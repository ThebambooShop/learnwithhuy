---
title: "Agent loop: state machine giữ log làm trạng thái duy nhất"
description: "Vì sao harness production reassemble prompt và rederive history trước mỗi step thay vì giữ message list trong bộ nhớ — turn/step state machine mà session log là durable state duy nhất, resume được bằng replay."
topic: "harness-engineer"
date: "2026-11-22"
cover: "/images/covers/posts/agent-loop-state-machine.jpg"
featured: false
views: 260
faq:
  - q: "Tại sao mỗi step phải derive lại history thay vì dùng lại list của step trước?"
    a: "Message list trong bộ nhớ là bản sao thứ hai của sự thật: compaction đổi surface sau lưng nó, replay không có nó, crash làm mất nó. Derive từ log mỗi step thì không có gì phải giữ đồng bộ — log là trạng thái duy nhất, mọi thứ khác là projection. Header đếm 1, 3, 2 sau compaction là bằng chứng đọc thẳng từ log."
  - q: "Turn và step khác nhau thế nào?"
    a: "Turn là một lượt người dùng vào: append user/message rồi chạy step cho tới khi một step báo end reason. Step là một lần gọi model: derive history, stream, append kết quả. Với tool, một turn có thể nhiều step; một step chết giữa đường không phá turn sau."
  - q: "Agent giữ gì để resume được?"
    a: "Không giữ gì durable: session, model seam, và status chỉ mang nghĩa 'đang giữa turn'. Replay log vào session mới cộng một Agent mới, turn tiếp theo sinh ra đúng từng row như Agent cũ — resume là replay, không phải khôi phục bộ nhớ."
  - q: "Khác gì agent loop 100 dòng của bài nền tảng?"
    a: "Bản chất vòng lặp giống nhau: model quyết định, code thực thi, kết quả quay về model. Khác ở chỗ loop này sống trên kernel như plugin, gắn session log làm trạng thái duy nhất, ghi turn/step boundary vào log, và có turn guard. Đó là shape production của cùng một ý tưởng."
---

Session log của bài trước đã biết derive history và compact được — nhưng chưa có gì lái nó. Mọi check đều hand-crank: tự append từng message như người điều khiển đứng nhồi tay. Thiếu cái máy: nhận text người dùng, gọi model, ghi lại, lặp cho tới khi xong. Cái máy đó là agent loop, và Mini-dsh gọi một lần chạy của nó là một **turn** — gồm một hoặc nhiều **step**.

Bài này dựng cái máy đó, và mổ xẻ quyết định thiết kế của nó: không giữ state riêng, dựa hẳn vào log.

> **Design question: tại sao reassemble prompt và rederive history trước mỗi step, thay vì giữ một message list trong bộ nhớ?**
>
> Vì một list live là **bản sao thứ hai của sự thật**. Compaction đổi surface sau lưng nó. Crash làm mất nó. Resume session nghĩa là dựng lại nó rồi hy vọng khớp với cái model thực sự đã thấy. Log đã là state durable duy nhất — loop nên dựa vào nó, không nên cạnh tranh với nó. Derive mỗi step nghĩa là không có gì cần giữ đồng bộ, bao giờ.

## Turn và step: state machine hai tầng

Một `Agent` cầm đúng ba thứ: một Session, một Model seam (callable nhận messages, stream trả chunk rồi message), và một `status` flag. `status` chỉ có hai giá trị `"idle"` và `"running"` — và nó **không bao giờ durable**: nó chỉ mang nghĩa "đang giữa turn ngay bây giờ", không phải lịch sử.

```python
# agent_loop.py — rút gọn từ Mini-dsh section 04
class Agent:
    """Lái một session qua Model seam, mỗi lần một turn."""

    def __init__(self, session, model):
        self.session = session
        self.model = model
        self.status = "idle"  # "idle" | "running" — không bao giờ durable

    def send(self, text):
        """Một turn: message người dùng vào, chạy step cho tới khi có end reason."""
        if self.status == "running":
            raise RuntimeError("agent đang giữa turn; một log chỉ kể một câu chuyện")
        self.status = "running"
        try:
            self.session.append("user/message", {"content": text})
            self.session.append("turn/start", {})
            while self._step() is None:
                pass
            self.session.append("turn/end", {})
        finally:
            self.status = "idle"

    def _step(self):
        """Một step: derive lại history, một lần gọi model, append lại tất cả."""
        self.session.append("step/start", {})
        messages = self.session.derive_messages()  # derive lại, không bao giờ cache
        self.session.append("request/header", {"messages": len(messages)})
        for kind, value in self.model(messages):
            if kind == "chunk":
                self.session.append("assistant/chunk", {"text": value})
            else:
                self.session.append("assistant/message", {"content": value.content})
        # Chưa có tool: mọi step đều completed. Bài sau thêm arm None —
        # tool đã chạy, quay vòng tiếp.
        reason = "completed"
        self.session.append("step/end", {"reason": reason})
        return reason
```

Cấu trúc hai tầng:

- **`send()` = một turn.** Append `user/message` và `turn/start`, chạy `while self._step() is None` cho tới khi một step trả về end reason, rồi append `turn/end`. Turn guard ở đầu hàm là bắt buộc: hai turn chạy song song trên một log sẽ đan xen hai bộ marker vào một chuỗi — một log chỉ kể một câu chuyện. Real dsh xếp message mới vào inbox và nhấc nó lên ở step boundary; cơ chế đó nằm ở bài scheduler.
- **`_step()` = một step.** Derive history từ log **fresh**, ghi `request/header` niêm yết cái sắp gửi, stream một lần gọi model qua seam, append lại từng chunk và message cuối, kết thúc bằng `step/end` với reason.

Vòng lặp nhìn như thế này:

```
send(text)
  │
  ├─ append("user/message")            ← model thấy
  ├─ append("turn/start")              ← log-only
  │
  ▼
┌───────────── một step ─────────────────────┐
│ append("step/start")                       │
│ messages = derive_messages()  ◄── đọc log  │
│ append("request/header", {messages: n})    │
│ model(messages): chunk … chunk … message   │
│ append("assistant/chunk" / "message")      │
│ append("step/end", {reason})               │
└──────────────────┬─────────────────────────┘
                   │
     reason == None ──► còn việc (tool đã chạy) ──► step tiếp theo
     reason != None ──► append("turn/end") ──► status về "idle"
```

Chú ý một điều: ngày hôm nay loop chỉ chạy đúng một step mỗi turn — không có tool thì mọi step đều `completed`. Shape `while` + end reason chính là socket mà bài tools sẽ cắm vào: thêm arm `None` cho step có tool call, turn tự động thành nhiều step, và `send()` không đổi một chữ.

## Log là durable state duy nhất

Năm marker — `turn/start`, `step/start`, `step/end`, `turn/end`, `request/header` — đều là **log-only** (`surface_op` là `None`): model không bao giờ thấy, nhưng log kể được cả câu chuyện thực thi. Đây là ba cái giá đầu tiên trả về:

**Compaction tự do ghép vào.** Compact giữa các turn, và `request/header` của step sau tự ghi số nhỏ hơn — vì step derive từ log *như log đang là lúc đó*. Không có dòng code nào bảo loop biết về compaction. Không cần.

**Crash giữa step không cần sửa chữa.** Một model call chết giữa đường để lại `step/start`, một `request/header`, vài orphan chunk — rồi im. Chunk là log-only nên lần derive tiếp theo tự sạch; turn sau gửi đúng history đúng. Không bước "repair" nào tồn tại.

**Resume là replay.** Agent không cầm gì durable. Replay log vào session mới, đưa cho một Agent mới, turn tiếp theo append ra từng row giống hệt như Agent cũ sẽ append. Kiểm chứng ở đây là byte-for-byte, không phải "tương tự".

`request/header` đáng một đoạn riêng: nó là dòng niêm yết **model đã thấy gì**. Không có nó, "model đã thấy X" chỉ là phỏng đoán — list trong bộ nhớ đã đổi nhiều lần rồi. Có nó, bằng chứng nằm ngay trong log: compaction giữa các turn, đọc counts thẳng từ log là `[1, 3, 2]` — 1 message đầu, 3 message turn hai, 2 message sau compaction (summary + message mới). Không đụng internals của stand-in, chỉ đọc record.

## Khác gì agent loop 100 dòng

Vòng lặp bạn viết trong bài [Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop) và vòng lặp này cùng một bản chất: model quyết định, code thực thi, kết quả quay về model. Khác nhau là nơi loop sống và state nào được thừa nhận:

| Tiêu chí | Agent loop 100 dòng | Loop trong harness |
| --- | --- | --- |
| Trạng thái hội thoại | `messages` list trong bộ nhớ | Session log append-only, mọi thứ khác derive từ nó |
| Prompt mỗi lượt | Ghép từ list đang cầm | `derive_messages()` mỗi step, không cache |
| Ranh giới thực thi | `for turn in range(max_turns)` — chỉ có trong code | `turn/start` + `step/start` + `step/end` + `turn/end` ghi vào log |
| Crash giữa đường | Mất list, không biết dừng ở đâu | Log ghi đúng chỗ chết; turn sau derive sạch, không cần repair |
| Resume | Không có | Replay log + Agent mới = byte-for-byte cùng tương lai |
| Nơi sống | Script độc lập, import SDK | Plugin trên kernel, service `agents` qua `AgentRegistry` |
| Guard | `max_turns` là nút an toàn duy nhất | Turn guard theo state machine, mỗi step có end reason |

Cột phải không "tốt hơn" một cách trừu tượng — nó đánh đổi thêm vài lớp code để mua lại những thứ script demo không có: audit, resume, compose. Khi agent chạy vài ngày trên một tác vụ, những thứ đó không phải nice-to-have.

## Chạy được ngay

Ghép hai bài: paste code Session của bài [session log và compaction](/bai-viet/session-log-va-compaction) vào trước, rồi thêm block này:

```python
# loop_demo.py — chỉ stdlib. Ghép code Session + Message của bài trước vào
# đầu file, rồi chạy: python3 loop_demo.py — không cần API key.


class ScriptedModel:
    """Queue trả lời canned, stream thành vài chunk rồi message cuối."""

    def __init__(self, responses):
        self._queue = list(responses)

    def __call__(self, messages):
        text = self._queue.pop(0)
        for i in range(0, len(text), 3):
            yield ("chunk", text[i:i+3])
        yield ("message", Message(role="assistant", content=text))


session = Session("s1")
agent = Agent(session, ScriptedModel(["Hello.", "Now this.", "The summary says 42."]))
agent.send("hi")
agent.send("and now?")


def header_counts(sess):
    return [e["payload"]["messages"] for e in sess.log if e["type"] == "request/header"]


print(header_counts(session))  # [1, 3] — mỗi step derive lại từ log

# Compaction giữa các turn (bài trước): nén mọi thứ thành một summary
session.append(
    "user/message",
    {"content": "Summary: greeted twice."},
    surface_op={"op": "replace", "start": 0, "end": len(session.log)},
)
agent.send("what did we say?")
print(header_counts(session))  # [1, 3, 2] — step sau compaction derive đúng 2 message
```

Số `[1, 3, 2]` là bằng chứng sống của cả hai bài: loop không cache (turn hai gửi 3, không phải nối dồn 4), và compaction đổi view mà không đụng log (turn ba gửi 2 — summary cộng message mới).

## Failure modes

Sáu lỗi nguồn đã liệt kê cho cái loop này:

- **Message list cache là bản sao thứ hai của sự thật.** Giữ history live trong list thì mọi cơ chế khác thành bài toán đồng bộ: compaction đổi surface sau lưng nó, replay dựng session không có nó. Derive từ log mỗi step — không có gì để đồng bộ, bao giờ.
- **Crash giữa step không cần repair.** `step/start` không có `step/end`, vài orphan chunk. Chunk là log-only nên lần derive kế tự sạch; check offline giết một model giữa dòng để chứng minh điều đó.
- **Turn không phải một lần gọi model.** Hard-wire "gửi, nhận, xong" thì không có chỗ nào cho tool execution quay vòng vào. Shape while-step với end reason tường minh chính là chỗ để bài tools gắn vào mà không đụng turn.
- **Không có `request/header` thì "model đã thấy X" là phỏng đoán.** Header niêm yết cái mỗi step gửi thẳng vào log. Compaction giữa các turn đọc counts từ log: 1, 3, 2.
- **Hai turn trên một log đan xen events.** `send()` trong khi turn đang chạy raise thay vì dệt hai bộ marker vào một chuỗi. Real dsh xếp message vào inbox và nhấc lên ở step boundary — cơ chế của bài scheduler.
- **Thiếu marker là replay mơ hồ.** Không có `turn/start` và `step/end`, replayer không phân biệt được turn xong đàng hoàng với turn chết giữa đường. Boundary là dữ liệu, không phải printf debugging: chúng biến một đống message thành execution record replay được.

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| `RuntimeError: agent đang giữa turn` | Gọi `send()` trong khi turn đang chạy (thường từ trong model seam) | Một log một câu chuyện. Message mới phải chờ ở step boundary — cơ chế inbox của bài scheduler |
| `request/header` đếm không đúng kỳ vọng | Bạn so nó với một list cache ở đâu đó | Đọc thẳng từ log: `e["payload"]["messages"]` của event `request/header` |
| Orphan chunk xuất hiện trong model view | Nhầm chunks là surface type | Chunk là log-only theo thiết kế; `derive_messages()` tự sạch — kiểm tra lại `SURFACE_TYPES` |
| Resume ra kết quả lệch | Append thủ công nhưng lộn thứ tự, hoặc sửa event trong log | Replay đúng thứ tự log, giữ nguyên `surface_op`; hoặc để `Agent.send()` tự làm mọi thứ |
| Turn chỉ chạy 1 step dù đã thêm tool | Quên arm `None`: step trả `"completed"` cho cả lượt có tool | Step có tool call phải trả `None` để while-loop quay lại |

> 📍 Bài này là bài 4 của lộ trình [Xây dựng Agent Harness từ số 0 với Mini-dsh](/lo-trinh/xay-dung-agent-harness). Source đầy đủ của section nằm ở [repo learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness) — `test.py` chạy offline, `demo.py` là bản đầu tiên cắm API thật vào Model seam.

## Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: chạy demo trên, rồi in toàn bộ log sau hai turn: `for e in session.log: print(e["seq"], e["type"], e.get("payload"))`. Đọc từng row theo thứ tự — bạn đang nhìn execution record của hai turn: user message, markers, header, chunks, message, end reason.

**Mức 2 — Tự sửa**: thêm giới hạn step mỗi turn. Cho `send()` nhận `max_steps=3`; `while self._step() is None` phải thoát nếu số step vượt mốc — append `step/end` với `reason="max-steps"` rồi `turn/end`, tương tự max_turns của bài nền tảng nhưng ở cấp step và ghi vào log. Test bằng một model seam luôn trả `None`.

**Mức 3 — Mở rộng**: hai việc. Một — mô phỏng tool: cho model seam trả `("tool_call", {"name": "search", "query": "..."})` trước message cuối; sửa `_step` để append `tool/result` và trả `None` khi gặp tool call, thây cái arm `None` hoạt động — một turn ba step, counts `[1, 2, 2]` kiểu đấy. Hai — viết resume harness: dump `session.log` ra JSON (thaw `surface_op` và payload), load lại, chạy tiếp với Agent mới, assert các row mới byte-for-byte trùng với Agent cũ trên session gốc.

## Tài liệu gốc

- [hardness1020/learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness) — repo gốc của lộ trình; cơ chế trong bài là section 04, đối chiếu trực tiếp với `packages/core/agent-loop` của DeepSeek Harness thật (pinned `99f6f02`).
- [Session log và compaction](/bai-viet/session-log-va-compaction) — bài trước: log, surface, `derive_messages()` và replace op mà loop này tiêu thụ mỗi step.
- [Tools và permission pipeline](/bai-viet/tools-permission-pipeline) — bài kế tiếp: arm `None` của step được lấp, turn thành nhiều step thật.
- [Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop) — agent loop 100 dòng, bản chất mà bài này đưa lên shape production.
- [Lộ trình: Xây dựng Agent Harness từ số 0 với Mini-dsh](/lo-trinh/xay-dung-agent-harness) — tổng quan 8 bài của lộ trình.

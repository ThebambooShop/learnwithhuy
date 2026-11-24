---
title: "Session log và compaction: nhớ của agent mà không phình context"
description: "Tại sao harness production derive lịch sử hội thoại từ một append-only log thay vì lưu message list, và compaction lấy bớt context bằng replace op mà không xóa dấu vết nào."
topic: "harness-engineer"
date: "2026-11-22"
cover: "/images/covers/posts/session-log-va-compaction.jpg"
featured: false
views: 180
faq:
  - q: "Tại sao không lưu trực tiếp list message của model?"
    a: "Message list là trạng thái đã 'hình thành' — không biết ai đổi gì, không khôi phục được, không compaction được. Append-only log ghi lại mọi sự kiện; lịch sử model chỉ là một mặt (surface) derive từ log. Muốn compact hay replay, chỉ thay đổi cách derive — dữ liệu gốc luôn còn nguyên."
  - q: "Compaction có xóa dữ liệu không?"
    a: "Không xóa gì trong log. Compaction chỉ thêm một replace op vào surface để lịch sử mà model nhìn thấy được nén lại. Log vẫn chứa đủ mọi sự kiện từ đầu — có thể replay lại phiên hội thoại bất kỳ lúc nào."
  - q: "Cái này khác memory dài hạn thế nào?"
    a: "Session log là trí nhớ ngắn hạn trong một phiên — sống trong harness, chết khi phiên kết thúc. Memory dài hạn (vector store, graph) là kiến trúc khác, nằm ngoài harness; bài 'agent-memory-va-context-engineering' trên site nói riêng về nó."
  - q: "Khi nào context mới thực sự phình?"
    a: "Khi message list phình do tool result lớn lặp lại nhiều lần mà không compact. Harness production theo dõi token mỗi step và chủ động replace các đoạn cũ — đó là lý do compaction là một cơ chế của harness, không phải trách nhiệm của model."
---

Cùng một lượt hội thoại của agent được đọc theo ba cách khác nhau: model cần history sạch để gọi tiếp, việc lưu đĩa cần từng row kể cả streamed chunk, và compaction cần nén cái model nhìn thấy mà không mất dấu vết. Một list `messages` dùng chung không thể phục vụ cả ba — chunk làm bẩn nó, compaction phải sửa nó một cách phá hủy, và sau một crash bạn chỉ cầm được cái list đúng lúc đó, không cách nào dựng lại nó đã đi qua những gì.

Harness production đi đường khác. Bài này mổ xẻ cơ chế đó từ Mini-dsh — bản rebuild nhỏ của DeepSeek Harness bằng Python thuần: append-only log, surface, và `derive_messages()`. Code chỉ dùng stdlib, chạy được ngay, không cần API key.

> **Design question: tại sao derive history từ log thay vì lưu message list trực tiếp?**
>
> Vì một list message là trạng thái đã *hình thành*: không ghi lại cách nó được tạo ra, không biết ai đổi gì, và không chỉnh được mà không phá hủy. Log ghi **mọi sự kiện xảy ra** một lần duy nhất, append-only; lịch sử model chỉ là một *surface* — danh sách các row được chọn để chiếu thành message. Compaction, replay, audit: tất cả chỉ là cách derive khác trên cùng một dữ liệu gốc.

## Append-only log: ghi một lần, đọc ba cách

Một turn của agent sinh ra nhiều hơn message: streamed chunk, tool call và kết quả, turn marker, request header. Toàn bộ trở thành event.

Event có shape `{seq, type, payload}` — và quan trọng nhất: **seq của event chính là index của nó trong log, mãi mãi**. Không event nào bị sửa, bị xóa, bị đẩy chỗ khác. Mọi thứ trỏ về seq — surface, event feed, dữ liệu đã lưu đĩa — nên thứ tự này là hằng số của toàn hệ thống.

Ba thành phần chuyển động:

- **Log**: list append-only của frozen events.
- **Surface**: list các seq có thứ tự, được duy trì lúc append — đúng và chỉ đúng 3 event type sinh message: `user/message`, `assistant/message`, `tool/result`.
- **`derive_messages()`**: chiếu surface thành `Message` objects, tính lại mỗi lần gọi. Không lưu đâu cả.

Việc append là phép ghi duy nhất, và nó làm hết phần canh gác:

```python
# session_log.py — rút gọn từ Mini-dsh section 02, chỉ stdlib
import json
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class Message:
    role: str  # "user" | "assistant" | "tool"
    content: str


# Ba event type duy nhất model nhìn thấy. Mọi thứ khác
# (assistant/chunk, turn marker, header) chỉ nằm trong log.
SURFACE_TYPES = {
    "user/message": "user",
    "assistant/message": "assistant",
    "tool/result": "tool",
}


def _freeze(value):
    """Đóng băng đệ quy: dict -> MappingProxyType, list -> tuple."""
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


class Session:
    """Append-only log của frozen events, cộng surface chiếu trên nó."""

    def __init__(self, session_id, on_event=None):
        self.id = session_id
        self.log = []      # frozen events; seq của event chính là index, mãi mãi
        self.surface = []  # các seq của event sinh message, theo thứ tự hội thoại
        self._on_event = on_event

    def append(self, event_type, payload):
        # Validate-and-copy tại biên: payload phải là JSON thuần,
        # log giữ bản sao riêng nên không caller nào sửa được history.
        payload = json.loads(json.dumps(payload))
        seq = len(self.log)
        event = _freeze({"seq": seq, "type": event_type, "payload": payload})
        self.log.append(event)
        if event_type in SURFACE_TYPES:
            self.surface.append(seq)
        if self._on_event is not None:
            self._on_event(self, event)
        return event

    def derive_messages(self):
        """Chiếu surface thành history của model. Không lưu, luôn derive."""
        return [
            Message(role=SURFACE_TYPES[e["type"]], content=e["payload"]["content"])
            for e in (self.log[seq] for seq in self.surface)
        ]
```

Hai chi tiết nhỏ mà giữ toàn bộ đảm bảo:

- `json.loads(json.dumps(payload))` — validate-and-copy tại biên. Payload không phải JSON thuần sẽ raise; payload hợp lệ được **sao chép**, nên caller đổi object gốc sau đó cũng không ảnh hưởng gì log.
- `_freeze` đóng băng đệ quy: dict thành `MappingProxyType`, list thành tuple. Event sau khi vào log không thể bị sửa — cố gắng gán là `TypeError`.

Trên kernel của bài trước, session log được mount như một service thông qua plugin: `ctx.provide("sessions", SessionStore(ctx))`. Mount được thì gỡ được — một `dispose()` là sạch.

## Lưu message list trực tiếp vs derive từ log

| Tiêu chí | Lưu message list trực tiếp | Derive từ log |
| --- | --- | --- |
| Streamed chunk | Làm bẩn list hoặc phải bỏ đi — mất dấu vết | Là event thật trong log, replay được; model không thấy vì không phải surface type |
| Compaction | Phải sửa list tại chỗ — phá hủy, mất dữ liệu gốc | Chỉ đổi cách derive; log giữ nguyên mọi row |
| Crash | Còn lại gì dùng nấy, không dựng lại được | Replay log từ đầu, dựng lại chính xác |
| Audit "model đã thấy gì" | Phỏng đoán — list đã đổi nhiều lần | Derive lại bất kỳ lúc nào, từ cùng một log |
| Sự thật nằm ở đâu | Trải trong list và trong đầu caller | Một chỗ duy nhất: log. Mọi thứ khác là projection |
| Cost mỗi step | Đọc list có sẵn | Tính lại projection — rẻ, chỉ là duyệt surface |

Cột phải đắt thêm một phép duyệt list seq mỗi step — chi phí không đáng kể so với cái mua được: không có state nào cần giữ đồng bộ.

## Liên hệ context engineering

Bài [Memory và Context Engineering](/bai-viet/agent-memory-va-context-engineering) đã nói compaction ở tầng kỹ thuật: nén lịch sử cũ thành tóm tắt trước khi hết window, kèm nguyên tắc *own your context window*. Mini-dsh đưa nguyên tắc đó xuống tầng dữ liệu: compaction ở đây là một **cơ chế của harness**, không phải một hàm tiện ích gọi trước khi gửi request.

Điểm khác then chốt: bản compaction kiểu context engineering **thay thế** list cũ bằng list mới — dữ liệu chi tiết biến mất khỏi hệ thống. Trong session log, cái bị thay chỉ là projection. Cái log giữ: mọi message gốc, mọi chunk, mọi marker. Khi tóm tắt viết sai — mất con số, gộp nhầm hai yêu cầu — dữ liệu gốc vẫn còn để kiểm tra và để replay. ⚠️ Trách nhiệm về chất lượng tóm tắt vẫn như cũ: instruction tóm tắt phải ghi rõ giữ nguyên con số và tên riêng; không cơ chế nào cứu được một summary kém.

## Compaction: replace op trên surface

Câu hỏi tưởng khó: log append-only thì compaction lấy cái gì đi? Câu trả lời nằm trong thiết kế: **model không bao giờ đọc log.** Model đọc message derive từ surface — và surface chỉ là một list seq. Nén view = sửa surface, không phải sửa log.

Cụ thể: mỗi append mang một **surface op**. Không truyền → mặc định theo type (`"append"` cho 3 surface type, `None` cho phần còn lại). Truyền tường minh → dạng `{"op": "replace", "start": s, "end": e}`: event mới che một run surface entry có seq nằm trong khoảng nửa đóng `[start, end)`.

Hai phương thức thay thế trong `Session` — toàn bộ phần diff so với code trên:

```python
def append(self, event_type, payload, surface_op=None):
    payload = json.loads(json.dumps(payload))
    if surface_op is None and event_type in SURFACE_TYPES:
        surface_op = "append"
    seq = len(self.log)
    # Validate transition TRƯỚC khi commit: op hỏng thì cả log lẫn
    # surface phải nguyên vẹn — không có row ghi một op chưa từng chạy.
    surface = self._surface_after(event_type, seq, surface_op)
    event = _freeze(
        {"seq": seq, "type": event_type, "payload": payload, "surface_op": surface_op}
    )
    self.log.append(event)
    self.surface = surface
    if self._on_event is not None:
        self._on_event(self, event)
    return event


def _surface_after(self, event_type, seq, surface_op):
    """Surface sẽ trông thế nào sau khi append này commit. Raise nếu op hỏng."""
    if surface_op is None:
        return self.surface
    if event_type not in SURFACE_TYPES:
        raise ValueError(f"'{event_type}' không derive message; không thể lên surface")
    if surface_op == "append":
        return self.surface + [seq]
    if not isinstance(surface_op, dict) or surface_op.get("op") != "replace":
        raise ValueError(f"surface op không rõ: {surface_op!r}")
    # {"op": "replace", "start": s, "end": e}: nửa đóng [start, end)
    start, end = surface_op["start"], surface_op["end"]
    covered = [i for i, s in enumerate(self.surface) if start <= s < end]
    if not covered:
        raise ValueError(f"replace [{start}, {end}) không phủ surface entry nào")
    if covered != list(range(covered[0], covered[-1] + 1)):
        raise ValueError(f"replace [{start}, {end}) phủ một run surface không liền kề")
    return self.surface[: covered[0]] + [seq] + self.surface[covered[-1] + 1 :]
```

Ba quy ước làm cái replace op này đứng vững:

- **Validate rồi mới commit.** `_surface_after()` chạy trước `self.log.append`. Op bị từ chối raise ra ngoài với log và surface y nguyên — không để lại row ghi một op chưa từng có hiệu lực (sai chỗ này là replay dựng ra surface khác với surface đang chạy).
- **Op nằm trên record.** Mỗi event mang `surface_op` của mình, đóng băng cùng event. Surface vì thế là hàm thuần của log: append lại toàn bộ log là dựng lại đúng surface. Đây là điều kiện để log đơn lẻ kể được cả câu chuyện.
- **Sự thay thế phải tự là message.** Chỉ surface type được phép mang op — `assistant/chunk` mang replace op bị từ chối. Cái đặt vào chỗ của message phải là message.

Và một quirk đáng nhìn kỹ: sau compaction, surface **không còn sort theo seq**. Nó là thứ tự hội thoại, không phải thứ tự log:

```
log      0:user   1:chunk  2:assistant  3:tool  4:user  5:assistant
surface  [0, 2, 3, 4, 5]

append("user/message", {"content": "Summary: ..."},
       surface_op={"op": "replace", "start": 0, "end": 4})

log      0:user  1:chunk  2:assistant  3:tool  4:user  5:assistant  6:user
surface  [6, 4, 5]

derive_messages() ──► "Summary: ..."   "and now?"   "Now this."
```

Summary (seq 6, mới nhất trong log) đứng **trước** các seq cũ trong surface — vì model đọc theo trình tự hội thoại. Đây cũng là lý do replace bị từ chối khi khoảng seq phủ một run có lỗ hổng: range `[5, 7)` trên surface `[6, 4, 5]` lấy được seq 6 và 5 nhưng bỏ sót 4 — commit nó là cắt summary đè lên những message nó không hề phủ.

## Chạy được ngay

Lưu phần code trên vào một file, thêm demo này vào cuối rồi chạy `python3 session_demo.py` — không key, không network:

```python
model_text = "Xin chào, mình đã đọc dữ liệu."

session = Session("demo")
session.append("user/message", {"content": "tổng hợp số liệu Q3"})   # seq 0
for i in range(0, len(model_text), 10):                              # streaming thật
    session.append("assistant/chunk", {"text": model_text[i:i+10]})
session.append("assistant/message", {"content": model_text})          # seq 2
session.append("tool/result", {"content": "42"})                      # seq 3

print("surface:", session.surface)              # [0, 4, 5] — chunk không lên surface
for m in session.derive_messages():
    print("  ", m.role, "→", m.content)

# Compaction: một append thường, mang replace op [0, 6) — nén mọi message
# trông thấy (seq 0, 4, 5), dù chunk row ở giữa chỉ nằm trong log
session.append(
    "user/message",
    {"content": "Summary: người dùng hỏi Q3; tool trả 42."},
    surface_op={"op": "replace", "start": 0, "end": 6},
)
print("log:", len(session.log), "events — không xóa row nào")
for m in session.derive_messages():
    print("  ", m.role, "→", m.content)         # chỉ còn summary
```

Kết quả: trước compaction model thấy 3 message (`user → assistant → tool`); sau compaction chỉ còn summary. Log tăng từ 6 lên 7 events, row seq 0 vẫn nằm nguyên tại chỗ với payload `"tổng hợp số liệu Q3"`.

## Failure modes

Năm lỗi thiết kế nguồn đã chỉ đích danh, chuyển thẳng sang đây:

- **Event sinh message mà surface bỏ sót là vô hình.** Thêm event type mới muốn model thấy mà quên đăng ký vào `SURFACE_TYPES` — `derive_messages()` âm thầm bỏ qua nó, không báo lỗi. Real dsh tập trung mapping vào một chỗ (`deriveEventMessage`) vì cùng lý do.
- **Subscriber ném exception chặn append.** Feed `session/event` là synchronous: một listener hỏng raise xuyên qua `append()` làm kẹt cả log. Persistence coordinator của real dsh bọc exception theo từng listener vì vậy.
- **Validate-and-copy là JSON-shaped, không phải meaning-shaped.** Round trip `json` lặng lẽ biến tuple thành list và chấp nhận `NaN`. Payload đi qua được là đảm bảo là dữ liệu thuần — không đảm bảo là dữ liệu bạn muốn.
- **Seq reference khiến cắt log tại chỗ bất khả thi — chủ đích.** Surface, feed, dữ liệu đã lưu đều trỏ seq. Xóa hay xếp lại row là phá tất cả; "xóa" chỉ được phép thực hiện như thay đổi projection, không bao giờ là phẫu thuật log.
- **State ngoài log sẽ không replay được.** Bất kỳ consumer nào cache message list hay giữ aggregate mutable đều lệch ngay khi history được derive lại. Log chỉ là sự thật durable duy nhất nếu mọi ghi đều đi qua `append()`.

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| `ValueError: replace [s, e) không phủ surface entry nào` | Khoảng đó đã bị replace trước đó, hoặc start/end tính sai | Tính range từ surface hiện tại, không cache seq đã bị thay |
| Summary nằm cạnh message nó nói đã thay | `end` là nửa đóng — off-by-one | `[0, 4)` thay seq 0–3 và giữ seq 4. `end` = seq cuối muốn nén + 1 |
| `ValueError: ... run không liền kề` | Sau compaction surface không sort theo seq; range seq lấy hụt entry nằm giữa | Replace phải phủ một run liền của surface theo thứ tự hội thoại, không phải range seq nào cũng được |
| `TypeError` khi sửa event trong log | Event đã frozen (`MappingProxyType`/tuple) | Không sửa log. Muốn đổi view → append một replace op |
| Event type mới biến mất khỏi `derive_messages()` | Không đăng ký vào `SURFACE_TYPES` | Mỗi type muốn model thấy phải vào `SURFACE_TYPES`; type log-only thì để ngoài một cách chủ ý |

> 📍 Bài này là bài 3 của lộ trình [Xây dựng Agent Harness từ số 0 với Mini-dsh](/lo-trinh/xay-dung-agent-harness) — rebuild DeepSeek Harness bằng Python stdlib, mỗi cơ chế một bài. Toàn bộ source nằm ở [repo learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness), check offline không cần API key.

## Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: chạy demo trên, rồi thêm event type mới `turn/start` (payload rỗng) bằng `session.append("turn/start", {})`. Chứng minh `derive_messages()` không đổi — type ngoài `SURFACE_TYPES` là log-only. Mục đích: thấy ranh giới log/surface là code, không phải quy ước.

**Mức 2 — Tự sửa**: viết helper `compact_recent(session, keep_recent=2)` tự tính `start`/`end` từ surface hiện tại để nén mọi message trừ 2 lượt gần nhất, rồi gọi replace op. Cẩn thận hai cái bẫy: run phải liền kề và `end` là nửa đóng. Test trên hội thoại 8 lượt — kiểm tra derive sau khi nén đúng còn `keep_recent` message cộng summary.

**Mức 3 — Mở rộng**: viết `replay(session)` — dựng Session mới bằng cách append lại từng event của log cũ (cần `thaw` payload và `surface_op` về JSON thuần trước), assert surface và `derive_messages()` của hai session identical. Sau đó thêm compaction thứ hai phủ cả summary cũ — thấy log vẫn giữ nguyên row đầu tiên "tổng hợp số liệu Q3".

## Tài liệu gốc

- [hardness1020/learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness) — repo gốc của lộ trình Mini-dsh; cơ chế trong bài là section 02 và 03, kèm đối chiếu từng file với DeepSeek Harness thật (pinned `99f6f02`).
- [Kernel và plugin: thiết kế harness](/bai-viet/kernel-plugin-thiet-ke-harness) — nền tảng trước đó: session log được mount như service `sessions` trên kernel này.
- [Agent loop: state machine giữ log làm trạng thái duy nhất](/bai-viet/agent-loop-state-machine) — bài kế tiếp: loop nào tiêu thụ cái log này mỗi step.
- [Memory và Context Engineering](/bai-viet/agent-memory-va-context-engineering) — compaction nhìn từ tầng kỹ thuật context, và nguyên tắc own your context window.
- [Lộ trình: Xây dựng Agent Harness từ số 0 với Mini-dsh](/lo-trinh/xay-dung-agent-harness) — tổng quan 8 bài của lộ trình.

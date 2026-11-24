---
title: "Agent Harness là gì: tại sao model cần một lớp điều phối"
description: "Hiểu agent harness khác gì agent loop, tại sao mọi agent production cần một lớp điều phối plugin, và chạy được cơ chế Message provider-agnostic đầu tiên của Mini-dsh — không cần API key."
topic: "harness-engineer"
date: "2026-11-22"
cover: "/images/covers/posts/agent-harness-la-gi.jpg"
featured: true
views: 320
faq:
  - q: "Agent harness khác agent loop như thế nào?"
    a: "Agent loop là vòng lặp model-decide-code-execute. Agent harness là toàn bộ lớp điều phối bao quanh loop: kernel quản lý plugin, session log, tool registry, permission, sandbox, skills, subagent. Loop chỉ là một cơ chế trong harness — harness production của DeepSeek (dsh) built trên nguyên tắc 'everything is a plugin'."
  - q: "Bài này có cần API key để chạy code không?"
    a: "Không. Toàn bộ Mini-dsh dùng Python stdlib, cơ chế model được thay bằng scripted stand-in (giả lập model theo kịch bản). Chạy offline check với python sections/00-setup/src/test.py không cần mạng hay API key."
  - q: "Message format tự định nghĩa có phải reinvent the wheel?"
    a: "Không. Provider-agnostic Message là ranh giới cho phép swap model provider mà không sửa logic harness — đúng cách dsh làm thật: mô hình chỉ là một plugin có thể thay thế."
  - q: "Học Mini-dsh có dùng được cho harness thật không?"
    a: "Mini-dsh là bản giáo dục rút gọn nhưng giữ đúng các design question và seam của dsh 0.1.0-rc.7. Học xong bạn đọc source dsh thật dễ hơn nhiều vì đã biết cơ chế đứng sau từng phần."
---

Bài trước bạn đã tự dựng được agent loop — model quyết định, code thực thi, kết quả quay về model ([Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop)). Nhưng loop chỉ là một cơ chế. Đưa agent đó ra production: bạn cần ghi log từng lượt, quản lý tool registry, permission, sandbox, skills, subagent — và một cách thay model mà không đụng lại toàn bộ code. Toàn bộ lớp điều phối bao quanh loop đó có tên riêng: **agent harness**.

Bài này mở lộ trình 8 bài **Xây dựng Agent Harness từ số 0 với Mini-dsh** — rebuild bản rút gọn của dsh, agent harness production của DeepSeek, chỉ bằng Python stdlib. Bài đầu tiên dựng cơ chế sơ khai nhất mà cả harness đứng trên đó: cách gọi model mà không để format của provider nào chảy vào core. Không API key, không mạng — chạy được ngay sau khi clone.

## Agent harness là gì?

> **Agent harness là toàn bộ lớp điều phối chạy quanh model call: kernel quản lý plugin, session log, tool registry, permission, sandbox, skills, subagent. Model chỉ là một plugin cắm vào lớp điều phối.**

dsh — harness mà DeepSeek dùng thật — là một codebase TypeScript lớn, trong đó tools, prompts và cả những subsystem nguyên vẹn đều là plugin mounted onto a running kernel. Ẩn sau tất cả chỉ là một thao tác lặp đi lặp lại: hỏi model một response. Mỗi lần như vậy, harness derive history, expose tools, assemble prompt, rồi gọi.

Vì mọi cơ chế đều phục vụ đúng một model call, câu hỏi thiết kế đầu tiên không phải "loop viết thế nào" — mà là "gọi model theo cách nào để không một bộ phận nào của harness dính vào một provider cụ thể".

## Harness khác agent loop ở đâu?

Loop là trái tim — nhưng tim không chạy một mình.

| | Agent loop | Agent harness |
| --- | --- | --- |
| Bản chất | Một cơ chế: model → tool call → execute → append context | Toàn bộ lớp điều phối chứa cơ chế đó |
| Quy mô | ~100 dòng Python là đủ | Codebase lớn, tách package rõ |
| Biết gì về thế giới | Chỉ biết messages và tool schema | Quản lý plugin, session log, tool registry, permission, sandbox, skills, subagent |
| Đổi model | Sửa trực tiếp vòng lặp | Thay một plugin — loop không đổi |
| Có thể thiếu không? | Không — không loop thì không có agent | Không — không harness thì production không có log, teardown sạch, swap model |

dsh xây trên nguyên tắc "everything is a plugin": tools, prompts, cả subsystems đều cắm vào kernel đang chạy. Agent loop trong dsh cũng chỉ là một plugin có đặc quyền điều phối. Tách loop ra khỏi lớp điều phối là quyết định kiến trúc đầu tiên bạn phải hiểu trước khi đọc source harness thật.

## Bản đồ Mini-dsh: 4 phase lõi

Mini-dsh dựng harness theo 4 phase, mỗi phase đúng một cơ chế, mỗi phase đứng trên phase trước:

```
Mini-dsh — 4 phase lõi, mỗi phase một cơ chế, dựng theo thứ tự

PHASE 1 · SEAM                     (bài này, section 00-setup)
┌────────────────────────────────────────────────────────────────┐
│  Message(role, content) — frozen, provider-agnostic            │
│  model(messages) → ("chunk", ...)... → ("message", Message)    │
└────────────────────────────────────────────────────────────────┘
                │ seam chờ người dùng đầu tiên
                ▼
PHASE 2 · KERNEL                   (bài kế, section 01-kernel)
┌────────────────────────────────────────────────────────────────┐
│  ctx.plugin(p) → Fiber gom undo của mọi registration           │
│  fiber.dispose() → undo chạy ngược — mount/unmount đối xứng    │
└────────────────────────────────────────────────────────────────┘
                │ log mount lên kernel như một service
                ▼
PHASE 3 · SESSION LOG              (bài session log và compaction)
┌────────────────────────────────────────────────────────────────┐
│  chunk / message / tool result → event types → file            │
│  compaction đọc log, nén view chứ không sửa record             │
└────────────────────────────────────────────────────────────────┘
                │ loop là consumer đầu tiên dùng cả ba phase trên
                ▼
PHASE 4 · AGENT LOOP               (bài agent loop state machine)
┌────────────────────────────────────────────────────────────────┐
│  model → tool call → execute → append → lặp                    │
│  forward chunks ngay từ byte đầu tiên, không buffer            │
└────────────────────────────────────────────────────────────────┘
```

Nguyên tắc dựng của cả lộ trình: mỗi section copy nguyên `src/` của section trước rồi thêm đúng một cơ chế. Diff giữa hai section liên tiếp chỉ là một cơ chế, không hơn — sau 8 bài bạn đọc lịch sử thiết kế harness như đọc một chuỗi commit.

## Phase 1: Message và Model seam

Cách làm đầu tiên ai cũng nghĩ tới: nơi nào cần gọi model thì import SDK của provider đó vào.

Cách làm đó làm provider lan khắp harness: format request của provider chạm vào prompt builder, response object của nó chạm vào log, tên role của nó chạm vào compaction. Đổi provider nghĩa là sửa ở cả ba nơi.

Phase 1 đặt ra 4 yêu cầu để chặn điều đó:

1. Mini-dsh có **Message shape riêng**, provider-agnostic — không vendor format nào vào core.
2. **Model seam** là một calling convention: callable nhận message list, stream các chunk event rồi kết thúc bằng đúng một final message.
3. **Scripted stand-in** nói đúng contract đó — seam có implementation chạy được ngay khi nó tồn tại.
4. Mỗi response được chunk hóa deterministic — streaming thật từ ngày đầu.

Code rút gọn chạy được, trích từ `src/` thật của section 00:

```python
# mini_seam.py — Phase 1 của Mini-dsh: Message + Model seam + ScriptedModel
# Chỉ Python stdlib — không API key, không mạng.

from dataclasses import dataclass

# 1. Message: vocabulary duy nhất của toàn bộ harness

@dataclass(frozen=True)
class Message:
    role: str      # "user" | "assistant" | "tool"
    content: str

# 2. ScriptedModel: implementation đầu tiên của Model seam

def _chunks(text, n=3):
    # chia chuỗi thành n đoạn gần bằng nhau, deterministic
    size = max(1, -(-len(text) // n))
    return [text[i : i + size] for i in range(0, len(text), size)]

class ScriptedModel:
    """Queue trả lời theo kịch bản — không bao giờ đọc request."""

    def __init__(self, responses):
        self._queue = list(responses)

    def __call__(self, messages):
        # Contract Model seam: ("chunk", str)... rồi một ("message", Message)
        text = self._queue.pop(0)
        for piece in _chunks(text):
            yield ("chunk", piece)
        yield ("message", Message(role="assistant", content=text))

# 3. drain: tiện ích tiêu thụ một stream để kiểm tra

def drain(stream):
    events = list(stream)
    chunks = [text for kind, text in events[:-1] if kind == "chunk"]
    kind, final = events[-1]
    assert kind == "message"
    return chunks, final

if __name__ == "__main__":
    model = ScriptedModel(["Hello, reader.", "Second answer."])

    chunks, final = drain(model([Message("user", "hi")]))
    assert final == Message("assistant", "Hello, reader.")
    assert "".join(chunks) == final.content, "chunks phải ghép đúng nội dung cuối"
    assert len(chunks) > 1, "streaming phải thật, không phải một blob"

    _, final = drain(model([Message("user", "again")]))
    assert final.content == "Second answer.", "queue trả lời đúng thứ tự"

    print("seam OK:", final.content)
```

Một lượt gọi qua seam chạy đúng hình này:

```text
caller                          ScriptedModel(["Hello, reader."])
  │
  │  model([Message("user", "hi")])
  ├─────────────────────────────►  pop response kế tiếp
  │                                (request không bao giờ bị đọc)
  │   ("chunk", "Hello")   ◄──┐
  │   ("chunk", ", rea")   ◄──┼──── chia thành n đoạn cố định
  │   ("chunk", "der.")    ◄──┘
  │   ("message", Message("assistant", "Hello, reader."))
  │◄─────────────────────────────
```

Bốn điểm kỹ thuật đáng nhớ:

- **Frozen, vì message là record của cái đã nói, không phải draft mutable.** Các section sau coi một message đã ghi là sự kiện đã xảy ra; một message cho phép gán lại field sẽ phá cả record lẫn view mà không để lại dấu vết.
- **Provider-agnostic, vì core không được quan tâm model của ai trả lời.** Dịch Message sang wire format của provider là việc của adapter — và adapter không nằm trong core.
- **Ba role đủ cho mọi trao đổi của harness**: user nói gì, model nói gì, tool trả về gì. Các cơ chế sau thêm event types *quanh* message chứ không thêm field *vào trong* message.
- **Seam là calling convention, không phải class.** Một hàm, một closure, một object — cái gì callable, nhận message list và yield đúng hai loại event đều là model hợp lệ. Đổi model là passing một callable khác, thế là model thành một part cắm vào.

Hai phase của stream quan trọng hơn cả stand-in: các chunk là live stream — thứ caller forward đi ngay để người dùng thấy tiến độ; final `Message` là durable record — bản ghi chính thức, luôn đọc lại được toàn văn.

## Chạy thử: clone và chạy offline check

Ba lệnh, không key:

```bash
git clone https://github.com/hardness1020/learn-deepseek-harness
cd learn-deepseek-harness
python sections/00-setup/src/test.py
```

Output:

```
section 00: all checks passed
```

Dòng duy nhất đó đứng trên ba assertion trong `test.py`:

1. **Chunks ghép lại đúng bằng content của final message** — stream và record không lệch nhau một ký tự.
2. **Số chunk lớn hơn 1** — streaming thật, không phải một blob nén lại.
3. **Lần gọi thứ hai nhận đúng "Second answer."** — queue trả lời theo đúng thứ tự kịch bản, không bao giờ đảo.

Tại sao chạy không cần key: stand-in trả lời từ queue có sẵn và **không bao giờ đọc request** — mọi check của tutorial đều offline, không mạng, và trả cùng một bytes mỗi lần chạy. Đây là convention check định chuẩn cho cả lộ trình: bạn sửa code, chạy lại, và biết ngay mình phá gì mà không tốn một xu API.

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'message'` | Đổi tên file hoặc copy `test.py` ra nơi khác một mình | Chạy đúng `python sections/00-setup/src/test.py` từ root repo — Python tự thêm thư mục chứa script vào `sys.path` |
| `IndexError: pop from empty list` | Gọi model nhiều lần hơn số response đã nạp vào queue | Nạp đủ kịch bản: mỗi lần gọi model "tiêu" một response |
| `FrozenInstanceError` khi gán `msg.content = ...` | Message là frozen dataclass — đúng thiết kế | Muốn đổi lịch sử thì thêm message mới hoặc đi qua session log, không sửa record cũ |
| Ghép chunks tay ở nhiều nơi và lệch | Mỗi caller tự nối chunk một kiểu | Tin final `("message", Message)` làm bản ghi duy nhất; chunks chỉ dùng để hiển thị |

> 📍 **Nguyên tắc carry-forward:** mọi section của lộ trình copy nguyên `src/` section trước rồi thêm đúng một cơ chế. Sau khi đọc hết 8 bài, `diff` giữa hai section liên tiếp cho bạn đúng một quyết định thiết kế mỗi lần.

## Gọi model trực tiếp vs qua harness

| Tiêu chí | Gọi model trực tiếp (import SDK ở mỗi chỗ cần gọi) | Qua harness (Message + Model seam) |
| --- | --- | --- |
| Định dạng dữ liệu | Wire format của provider chảy vào prompt, log, compaction | Một Message shape duy nhất; adapter lo dịch |
| Đổi provider | Sửa mọi nơi import SDK | Thay một callable — model là một plugin |
| Streaming | Chờ chuỗi hoàn chỉnh, không gì để hiển thị giữa chừng | Chunks + một final message ngay từ ngày đầu |
| Log | Lưu JSON của provider | Lưu event type riêng, không dính vendor |
| Test | Cần key, cần mạng, output không xác định | Scripted stand-in: offline, không key, deterministic |
| Bọc thêm behavior (retry, timing) | Phải sửa mỗi call site | Viết một closure bọc model — vẫn đúng contract |

Quy tắc ngắn: **một shape vào, một shape ra, provider thành một part cắm vào.** Chủ thể thật của harness là mọi thứ quanh model call — không bộ phận nào trong đó được phụ thuộc vào model của ai trả lời.

## Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: chạy `python sections/00-setup/src/test.py`, rồi sửa test thêm lần gọi thứ ba bằng `Message(role="tool", content="tool result")` — chứng minh seam nhận đủ cả ba role mà không cần đổi gì trong `ScriptedModel`.

**Mức 2 — Tự sửa**: viết hai hàm `to_vendor(msg)` và `from_vendor(d)` dịch Message sang dict kiểu wire format một provider (ví dụ `{"role": ..., "content": ...}`) và ngược lại. Chạy trên vài Message. Điểm cần thấy: harness core không đổi một chữ khi có thêm adapter mới.

**Mức 3 — Mở rộng**: viết `logged_model(model)` — một closure nhận model, trả về model mới vẫn nói đúng contract (chunks rồi message) nhưng in từng chunk ra stdout trước khi forward. Đây là kiểm tra cho tính chất calling convention của seam: một closure bọc model vẫn là model hợp lệ — nếu seam là base class thì cái này không viết nổi.

## Tài liệu gốc

Bài này viết từ source thật của lộ trình:

- [hardness1020/learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness) — repo tutorial; section `00-setup` là nguồn code, và bảng "In real dsh" map từng chi tiết vào dsh pinned commit `99f6f02`.
- [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) — harness production của DeepSeek; seam này map vào `packages/llm` (`types.ts` với `ToolSchema`, `index.ts` với `LlmAdapter`).

Đọc tiếp lộ trình [Xây dựng Agent Harness từ số 0 với Mini-dsh](/lo-trinh/xay-dung-agent-harness):

- [Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop) — loop là một cơ chế nằm trong harness.
- [Agent loop state machine](/bai-viet/agent-loop-state-machine) — phase 4 của bản đồ: loop dựng như một state machine.
- Bài kế: [Kernel và nguyên tắc 'mọi thứ là plugin'](/bai-viet/kernel-plugin-thiet-ke-harness) — phase 2: chỗ để cắm mọi thứ khác của harness.

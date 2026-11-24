---
title: "Scheduler song song và steering inbox: chạy nhanh mà không giẫm chân"
description: "Scheduler 4 giai đoạn prepare-dispatch-finalize-finish của Mini-dsh: parallel-safe overlap, exclusive barrier, synthetic result khi hủy — và steering inbox hai target next-turn/next-step với claim chỉ ở step boundary, để agent chạy nhanh mà transcript vẫn tái dựng được."
topic: "harness-engineer"
date: "2026-11-22"
cover: "/images/covers/posts/scheduler-va-steering-inbox.jpg"
featured: false
views: 120
faq:
  - q: "Chạy tool song song có làm transcript sai thứ tự không?"
    a: "Không. Worker threads chỉ tính result, không đụng log; hàng tool/call ghi hết trước khi dispatch, còn tool/result được append theo đúng thứ tự model xuất ra ở giai đoạn finish. Concurrency chỉ rút ngắn thời gian, không đổi thứ tự sự kiện — chạy lại cùng turn cho cùng transcript, replay vẫn tái dựng được."
  - q: "Tại sao tool mặc định là exclusive thay vì song song?"
    a: "Chỉ tác giả tool biết body của nó đụng vào state gì, nên khai báo an toàn là opt-in: is_concurrency_safe=True mới được chồng. Người quên khai ở chế độ exclusive chỉ mất tốc độ; ở chế độ ngược lại, người quên khai corrupt dữ liệu — đánh đổi đúng chiều."
  - q: "Cancel có giết tool đang chạy không?"
    a: "Không. Cancel chỉ ngừng mở batch mới ở biên giới giữa các batch; work đã được dispatch chạy đến cùng và báo kết quả. Call chưa kịp chạy nhận synthetic result 'aborted before dispatch'. Nhờ vậy không còn nửa file ghi dở, và mọi call đã ghi tool/call đều có câu trả lời cho replay."
  - q: "Steering đổ vào khi step vừa completed thì sao?"
    a: "Turn không đóng ngay. Trước khi kết thúc turn, loop re-check hàng next-step một lần cuối: còn steering thì ăn thêm một step trong cùng turn. Input bị kẹt chờ đánh thức là lỗi kinh điển nếu thiếu re-check này."
---

Bài trước, pipeline permission đã chốt được call nào được phép chạy. Nhưng còn một giả định ngầm phải bỏ: mỗi reply chỉ gom một call. Thực tế model được bảo "đọc ba ghi chú" sẽ xin cả ba trong một lượt — và vòng for tuần tự biến ba giây đọc thành ba giây chờ. Bài này xử lý hai vấn đề nằm cạnh nhau trong Mini-dsh: **chạy nhanh** (scheduler 4 giai đoạn) và **nói chuyện với agent trong khi nó đang bận** (steering inbox). Cả hai chung một ràng buộc từ các bài trước: nhanh cỡ nào cũng không được phá hợp đồng transcript. Nguồn là [tutorial learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness), section 06-scheduler và 07-inbox — link đầy đủ ở cuối bài.

## Câu hỏi thiết kế của scheduler

> **Tại sao parallel-safe được chạy chồng nhau, exclusive tạo barrier, còn call chưa kịp chạy nhận synthetic result khi hủy?** Vì concurrency chỉ được phép trả giá bằng thời gian, không được trả bằng transcript: cùng một turn phải sinh cùng một thứ tự sự kiện mỗi lần chạy để replay tái dựng được, và mọi call đã ghi `tool/call` phải có `tool/result` — kể cả call chưa từng được dispatch.

Sáu ràng buộc scheduler phải giữ:

1. **Log trước, chạy sau** — hàng `tool/call` append đủ trước khi dispatch bất kỳ gì.
2. **An toàn là khai báo** — tool tự nhận `is_concurrency_safe`; mặc định exclusive, vì chỉ tác giả biết body đụng vào state gì.
3. **Chỉ chồng trong batch** — call safe liên tiếp gom một batch; exclusive là batch một phần tử, một barrier.
4. **Không bỏ rơi work đã chạy** — cancel chỉ hiệu lực giữa các batch; body đã dispatch chạy đến cùng.
5. **Call bị bỏ qua vẫn được trả lời** — synthetic result, vì replay phải tái dựng transcript không lủng.
6. **Một writer duy nhất** — chỉ thread loop append log; worker chỉ tính result và trả về.

## Scheduler 4 giai đoạn: prepare → dispatch → finalize → finish

Bản rút gọn giữ đúng 4 giai đoạn và quy tắc gom batch, chỉ dùng stdlib:

```python
# scheduler.py — 4 giai đoạn: prepare, dispatch, finalize, finish
# Chỉ stdlib: chạy ngay, không cần API key.
from concurrent.futures import ThreadPoolExecutor

ABORTED_BEFORE_DISPATCH = "aborted before dispatch"


def execute_tool_calls(session, tools, calls, aborted):
    """Đưa calls của một reply qua 4 giai đoạn; log luôn theo thứ tự model."""
    # prepare: mỗi call một hàng tool/call (log-only) + verdict an toàn
    plan = [(i, call, tools.is_safe(call)) for i, call in enumerate(calls)]
    for _i, call, _safe in plan:
        session.append("tool/call", call)
    outcomes = {}  # index -> result, đầy dần theo từng batch finalize
    with ThreadPoolExecutor(max_workers=max(1, len(plan))) as pool:
        for batch in _batches(plan):
            # dispatch: batch mới chỉ bắt đầu khi turn chưa bị hủy
            if aborted.is_set():
                break
            futures = [
                (i, pool.submit(tools.execute, call))
                for i, call, _safe in batch
            ]
            # finalize: barrier — work đã chạy không bị bỏ rơi
            for i, future in futures:
                outcomes[i] = future.result()
    # finish: một tool/result mỗi call, thứ tự model; bị skip vẫn được trả lời
    for i, call, _safe in plan:
        if i not in outcomes:
            outcomes[i] = {
                "call_id": call["id"],
                "name": call["name"],
                "is_error": True,
                "content": ABORTED_BEFORE_DISPATCH,
            }
        session.append("tool/result", outcomes[i])


def _batches(plan):
    """Call safe liên tiếp gom một batch; exclusive là batch một phần tử."""
    safe_run = []
    for entry in plan:
        if entry[2]:  # safe
            safe_run.append(entry)
            continue
        if safe_run:
            yield safe_run
            safe_run = []
        yield [entry]  # exclusive: barrier hai bên
    if safe_run:
        yield safe_run
```

Timeline cho một reply bốn call:

```
reply: a (safe)   b (safe)   c (exclusive)   d (safe)

prepare   tool/call a, b, c, d   ◄ đủ 4 hàng, thứ tự model, chưa chạy gì
dispatch  batch [a b]    a ═════╗
                         b ═════╬═╗   safe: chạy chồng nhau
finalize                 ── barrier ─┘
dispatch  batch [c]      c ═════╗      exclusive: batch một phần tử
finalize                 ── barrier
dispatch  batch [d]      d ═══╗
finalize                 ── barrier
finish    tool/result a, b, c, d ◄ thứ tự model, dù b xong trước a
```

| Giai đoạn | Làm gì |
| --- | --- |
| **prepare** | Mỗi call một hàng `tool/call` (log-only) + verdict an toàn từ `is_safe()`; tên lạ tính exclusive |
| **dispatch** | Batch lên worker thread; trước mỗi batch hỏi một câu: turn đã bị hủy chưa? Có thì ngừng dispatch |
| **finalize** | Barrier — chờ cả batch xong; work đã chạy không bị bỏ rơi, kể cả sau cancel |
| **finish** | Một `tool/result` mỗi call, theo thứ tự model; call chưa dispatch nhận synthetic result |

Demo đo được trên đồng hồ — 2 đọc song song + 1 save exclusive, kèm một kịch bản hủy:

```python
if __name__ == "__main__":
    import threading
    import time

    class Log:
        def __init__(self):
            self.rows = []

        def append(self, kind, payload):
            self.rows.append((kind, payload))

    def _ok(call, content):
        return {"call_id": call["id"], "name": call["name"],
                "is_error": False, "content": content}

    # ---- 1. Overlap và barrier: 2 đọc song song + 1 save exclusive ----
    class Tools:
        def is_safe(self, call):
            return call["name"] != "save"  # mặc định exclusive nếu không khai

        def execute(self, call):
            if call["name"] == "read":
                time.sleep(0.4)
                return _ok(call, "nội dung ghi chú")
            time.sleep(0.4)
            return _ok(call, "đã ghi file")

    calls = [
        {"id": "c1", "name": "read", "args": {}},
        {"id": "c2", "name": "read", "args": {}},
        {"id": "c3", "name": "save", "args": {}},
    ]
    log = Log()
    t0 = time.perf_counter()
    execute_tool_calls(log, Tools(), calls, threading.Event())
    print(f"2 đọc + 1 save: {time.perf_counter() - t0:.2f}s (tuần tự sẽ là 1.20s)")
    for kind, payload in log.rows:
        print(kind, payload["name"])

    # ---- 2. Cancel: call chưa dispatch nhận synthetic result ----
    ev = threading.Event()

    class Tools2:
        def is_safe(self, call):
            return call["name"] != "late"  # late exclusive => batch riêng

        def execute(self, call):
            if call["name"] == "stop":
                ev.set()  # hủy từ trong body, chạy trên worker thread
                time.sleep(0.2)
                return _ok(call, "stopping")
            time.sleep(0.4)
            return _ok(call, "đã dispatch nên chạy hết")

    calls2 = [
        {"id": "c1", "name": "stop", "args": {}},
        {"id": "c2", "name": "sibling", "args": {}},
        {"id": "c3", "name": "late", "args": {}},
    ]
    log2 = Log()
    execute_tool_calls(log2, Tools2(), calls2, ev)
    for kind, payload in log2.rows:
        print(kind, payload["name"], payload.get("content", ""))
```

Kết quả chạy thật:

> 2 đọc + 1 save: 0.81s (tuần tự sẽ là 1.20s)
> tool/call read
> tool/call read
> tool/call save
> tool/result read
> tool/result read
> tool/result save
> tool/call stop
> tool/call sibling
> tool/call late
> tool/result stop stopping
> tool/result sibling đã dispatch nên chạy hết
> tool/result late aborted before dispatch

Đọc kết quả: hai `read` chạy chồng nhau nên tổng thời gian xấp xỉ 0.8s chứ không phải 1.2s — concurrency rút ngắn thời gian thật. Nhưng thứ tự log không đổi: đủ 3 hàng `tool/call` trước bất kỳ `tool/result` nào, và results ra theo đúng thứ tự model. Trong kịch bản hủy, `sibling` đã được dispatch nên chạy đến cùng; `late` đứng sau barrier, chưa kịp chạy, và vẫn được trả lời bằng synthetic result — [pipeline permission của bài trước](/bai-viet/tools-permission-pipeline) không hề bị động vào: mọi call có câu trả lời như bình thường.

## Ba khái niệm đặt cạnh nhau

| Khái niệm | Nghĩa là gì | Ai quyết định | Hệ quả trên log |
| --- | --- | --- | --- |
| **parallel-safe** | body không đụng state chung, chồng được | tác giả tool khai `is_concurrency_safe: True` | call safe liên tiếp gom một batch |
| **exclusive** | phải chạy một mình | mặc định — không khai là exclusive | batch một phần tử = barrier hai bên |
| **synthetic result** | câu trả lời cho call chưa kịp dispatch | scheduler sinh khi turn bị hủy | `tool/result` với `is_error: true` và "aborted before dispatch" |

Một chi tiết đáng chú ý: verdict an toàn được chốt ngay ở prepare. Tool bị unload giữa chừng vẫn giữ slot của nó — body đã chạy hoặc result nói ra chuyện gì xảy ra. Re-resolve giữa chừng nghĩa là plan có thể đổi dưới barrier — điều pipeline dùng để nói "call này không được chạy" thì scheduler không cho phép xảy ra ngược lại.

## Steering inbox: input không được gửi thẳng vào log

Scheduler giải quyết tốc độ; nhưng agent chạy nhanh tạo ra vấn đề mới. Người xem tool results stream qua muốn đổi hướng ngay, không đợi machine rảnh. Cách làm hiển nhiên — append text đến thẳng vào log thành `user/message` — phá transcript theo hai đường:

- Request đang bay đã derive history rồi: hàng mới khẳng định model đọc những từ nó chưa từng nhận, và replay tái dựng một request không hề được gửi.
- Sender thường là tool body trên worker thread — và bài trước vừa chốt log single-writer, worker không được append.

> **Tại sao cần 2 inbox target, và tại sao message chỉ được claim ở step boundary?** Vì input phải được **route, không được apply**, và routing phải mang ý định của người gửi. Text đến nằm trong pending list — insert có lock, hợp lệ từ thread nào cũng được, không sinh log row. Pending chỉ biến thành hàng `user/message` ở step boundary — chính là nơi request kế được re-derive từ log, nên transcript không bao giờ khẳng định model thấy điều nó không thấy. Hai target cho hai ý định: một prompt đáng có turn riêng (`next-turn`) khác một dòng steer cho việc đang chạy dở (`next-step`) — chỉ người gửi mới biết đó là cái nào.

Ba preset của `send()` — chỉ khác target và wakeup:

```python
# Ba preset của send() — rút gọn từ agent_loop.py, chỉ khác target và wakeup
def followup(self, text):
    self.send(text, "next-turn", True)   # prompt riêng, đáng có một turn


def steer(self, text):
    self.send(text, "next-step", True)   # input cho việc đang chạy dở


def inject(self, text):
    self.send(text, "next-step", False)  # đỗ context cho step sau, không đánh thức
```

Claim ở boundary — đúng chỗ request kế được re-derive:

```python
def claim_at_boundary(session, inbox, target):
    """Đúng chỗ request kế được re-derive: claim biến pending thành log row."""
    session.append("step/start", {})
    for message in inbox.claim(target):
        session.append("user/message", message)
    messages = session.derive_messages()  # re-derive, không cache
```

Vòng turn — turn không đóng sớm khi có steering mới:

```python
def _turn(self):
    self.session.append("turn/start", {})
    target = "next-turn"  # chỉ step đầu của turn mới tiêu thụ một prompt
    while True:
        reason = self._step(target)
        target = "next-step"
        if reason == "aborted":
            break  # cancel: inbox đã bị dọn trước đó
        if reason is not None and not self.inbox.has("next-step"):
            break  # steering mới đổ vào: đi thêm một step, cùng turn
    self.session.append("turn/end", {})
```

Claim đồ — insert từ thread nào cũng được, claim chỉ ở boundary:

```
insert: thread nào cũng được, lúc nào cũng được    claim: loop thread, chỉ ở boundary

steer("s")     → next-step [s]        mỗi step:   ăn toàn bộ next-step
followup("B")  → next-turn [B]        mở turn:    thêm đúng 1 prompt

turn A   step1             step2             step3
         claim [A, s]      claim []          claim []
         model gọi tool    model trả lời     completed, next-step rỗng
              ▲                             → turn đóng
              s được steer giữa step: đợi ở inbox
turn B   step1 claim [B]                   1 prompt = 1 turn
```

## next-turn vs next-step

| | **next-turn** | **next-step** |
| --- | --- | --- |
| Ý định của người gửi | prompt đáng có một turn riêng | input cho công việc đang chạy dở |
| Gửi lúc nào | user hỏi follow-up khi agent đang bận | user steer, tool body nộp kết quả, `inject()` đỗ context |
| Claim ở boundary nào | chỉ boundary mở turn — đúng 1 tin | mọi boundary — toàn bộ hàng đợi |
| Hệ quả trên transcript | 3 prompt xếp hàng = 3 turn, không merge | turn không đóng sớm: steering mới ăn thêm một step |

Code inbox và demo claim:

```python
# inbox.py — route, không apply: insert từ thread nào cũng được, claim ở boundary
import threading

TARGETS = ("next-turn", "next-step")


class Inbox:
    """Hai pending list sau một lock; insert từ thread nào cũng được,
    claim chỉ từ loop thread ở step boundary."""

    def __init__(self):
        self._lock = threading.Lock()  # tool body insert từ worker thread
        self._pending = {t: [] for t in TARGETS}

    def insert(self, target, message):
        """File một message theo target. Không log row: được route, không apply."""
        if target not in TARGETS:
            raise ValueError(f"unknown inbox target: {target!r}")
        with self._lock:
            self._pending[target].append(message)

    def claim(self, target):
        """Toàn bộ next-step; nếu boundary này mở turn thì thêm đúng 1 prompt."""
        with self._lock:
            claimed = self._pending["next-step"]
            self._pending["next-step"] = []
            if target == "next-turn" and self._pending["next-turn"]:
                claimed.append(self._pending["next-turn"].pop(0))
            return claimed

    def has(self, target):
        with self._lock:
            return bool(self._pending[target])

    def clear(self):
        """Dọn toàn bộ pending: next-step trước, next-turn sau."""
        with self._lock:
            self._pending["next-step"] = []
            self._pending["next-turn"] = []


if __name__ == "__main__":
    box = Inbox()
    # Ba nguồn gửi lúc machine đang bận — insert là thread-safe, không đụng log
    box.insert("next-step", "steer: kiểm tra thêm ngày tháng")
    box.insert("next-turn", "followup: tóm tắt lại")
    box.insert("next-turn", "followup: chào tạm biệt")

    print("turn A step 1 (mở turn):", box.claim("next-turn"))
    print("turn A step 2:", box.claim("next-step"))
    print("turn A step 3:", box.claim("next-step"))
    print("turn B step 1 (mở turn):", box.claim("next-turn"))
    print("turn C step 1 (mở turn):", box.claim("next-turn"))
```

Kết quả chạy thật:

> turn A step 1 (mở turn): ['steer: kiểm tra thêm ngày tháng', 'followup: tóm tắt lại']
> turn A step 2: []
> turn A step 3: []
> turn B step 1 (mở turn): ['followup: chào tạm biệt']
> turn C step 1 (mở turn): []

Đọc kết quả: boundary mở turn ăn toàn bộ `next-step` **cộng đúng một** `next-turn` prompt — hai followup xếp hàng không merge thành một mega-prompt; mỗi prompt một turn với một câu trả lời riêng. Turn A bước 3 kết thúc với reason "completed", nhưng turn chỉ được khép khi `next-step` rỗng lúc đó — nếu giữa chừng còn có steering đổ vào, nó đi thêm một bước nữa trong cùng turn. Turn C rỗng chứng minh không sinh turn ma. Một run thật khi tool body tự steer, log ghi thế này:

```
send("read my note")
  │   2  user/message   "read my note"                        ◄ claim ở boundary mở turn
  │   4  assistant/message {"tool_calls": [read]}
  │   5  tool/call     read
  │        ...body steer + queue 2 prompt từ worker thread...
  │   6  tool/result   read
  │   7  step/end      {"reason": null}                       ◄ còn call: quay lại
  │   9  user/message   "while reading: also check the dates"  ◄ steer ăn step kế
  │  15  step/end      {"reason": "completed"}
  │  16  turn/end                                             ◄ next-step rỗng: đóng
  │  17  turn/start                                           ◄ prompt 1 có turn riêng
  │  27  turn/start                                           ◄ prompt 2 có turn riêng
```

Steer vào turn đang chạy đúng một boundary sau khi nó được gửi — không giữa chừng, không muộn hơn. Và dòng `user/message` giờ nằm **sau** `step/start`: input vào transcript bằng cách được claim, không bằng cách append. Trong real dsh, steering thường đến từ UI; Mini-dsh nhấn nó từ tool body và bus listener — cùng một seam, cùng một quy tắc. `cancel()` còn dọn inbox trước khi hủy turn: input xếp hàng trước cancel bị bỏ cùng turn đó, không hồi sinh công việc đã hủy.

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Workers tự append khi xong → log là race | để concurrency rò ra ngoài batch | chỉ loop thread append; finish theo thứ tự model |
| Safe-by-default → corrupt state | tác giả quên khai | exclusive-by-default: quên khai mất tốc độ, không mất dữ liệu |
| Giết work đã dispatch khi cancel | coi abort là viên đạn | abort là quyết định barrier: chỉ ngừng mở batch mới |
| Call bị skip không có row | coi abort là xoá call | synthetic result "aborted before dispatch" |
| Apply input ngay giữa step | nghĩ input là message | route vào inbox, claim ở boundary re-derive |
| Một hàng đợi chung cho 2 intent | flatten prompts và steering | 2 target, người gửi khai báo |
| Claim cả hàng prompt một lượt | merge hội thoại | boundary mở turn ăn đúng 1 prompt |
| Đóng turn quên re-check next-step | steering tới sát cuối step | re-check trước `turn/end`: steering mới ăn thêm step |

## Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: chạy demo scheduler, tăng sleep của `read` lên 0.8s và xác nhận tổng thời gian vẫn xấp xỉ 0.8 + 0.4 chứ không phải 2.0s. Mục đích: thấy overlap là thật, đo được trên đồng hồ, trong khi thứ tự log không đổi.

**Mức 2 — Tự sửa**: trong demo hủy, đổi `is_safe` của `late` thành `True` để nó join batch 1. Chạy lại — `late` được dispatch trước khi cờ abort bật, chạy đến cùng và không còn synthetic result. Mục đích: thấy barrier do exclusive tạo ra chính là điểm kiểm tra cancel.

**Mức 3 — Mở rộng**: ghép inbox vào agent loop của bạn — một tool body gọi `steer()` giữa step; xác nhận log có `user/message` ngay sau `step/start` của step kế, và turn chỉ khép khi `next-step` rỗng. Đây là đường ray nền cho các bài sau, khi agent cần nhận thêm ngữ cảnh giữa chừng mà không phá session.

## Tài liệu gốc

- [hardness1020/learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness) — tutorial rebuild DeepSeek Harness bằng Python stdlib. Bài này từ **section 06-scheduler** (`src/scheduler.py`, check offline: `python sections/06-scheduler/src/test.py`) và **section 07-inbox** (`src/inbox.py`, check offline: `python sections/07-inbox/src/test.py`) — cả hai chạy không cần API key.
- Trong real dsh: `packages/core/agent-loop/src/tool-calls.ts` — `executeToolCalls` với cùng 4 giai đoạn prepare/dispatch/finalize/finish; `TOOL_ABORTED_BEFORE_DISPATCH` là mã riêng, phân biệt call bị skip với call bị gián đoạn; `packages/core/agent/src/inbox.ts` — `Inbox` hai list, `InboxTarget = 'next-turn' | 'next-step'`; `Agent.send` với ba preset giống hệt Mini-dsh; hook `agent/turn-stopping` được chốt một cơ hội steer cuối trước khi turn đóng.
- Docs của dsh: `docs/tool-execution-pipeline.md` (pipeline mà scheduler drives), `docs/agent-lifecycle.md` (vị trí tool execution trong một turn, cancellation gồm claim points và inbox events), `docs/subsystems/core.md`.

Đọc tiếp trong series:

- [Tools và permission pipeline](/bai-viet/tools-permission-pipeline) — bài trước: pipeline 5 giai đoạn mà scheduler dispatch vào.
- [System prompt và skills](/bai-viet/system-prompt-va-skills) — bài kế.
- [Lộ trình: Xây dựng Agent Harness từ số 0](/lo-trinh/xay-dung-agent-harness) — toàn bộ 8 bài của series.

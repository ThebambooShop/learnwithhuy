---
title: "Kernel và nguyên tắc 'mọi thứ là plugin'"
description: "Design question của kernel harness: vì sao framework phải sở hữu cleanup của plugin thay vì plugin tự dọn — cơ chế Fiber, effect() và reversible registration khiến mount/unmount đối xứng theo thiết kế, kèm code chạy được không API key."
topic: "harness-engineer"
date: "2026-11-22"
cover: "/images/covers/posts/kernel-plugin-thiet-ke-harness.jpg"
featured: false
views: 150
faq:
  - q: "Tại sao plugin không tự viết cleanup() cho mình?"
    a: "Convention cleanup dễ vỡ: plugin thêm một listener trong code path mới và quên unregister tương ứng là leak callback vĩnh viễn — không có gì kiểm tra được. Kernel đảo ngược quyền sở hữu: đăng ký là trao undo cho framework, mọi API như on hay provide đều trả disposer và gom vào Fiber của plugin, unmount là một thao tác duy nhất của framework."
  - q: "Fiber khác một event emitter thông thường thế nào?"
    a: "Event emitter lo phát sự kiện; Fiber lo vòng đời: một danh sách undo theo thứ tự đăng ký cộng trạng thái loading, active, disposed. Mọi đăng ký đi qua effect() nên unmount chạy ngược tự động, và đăng ký trên fiber đã disposed raise InactiveEffectError thay vì leak âm thầm."
  - q: "Vì sao undo phải chạy theo thứ tự ngược đăng ký?"
    a: "Plugin đăng ký nền móng trước và thứ phụ thuộc sau, nên teardown phải dỡ cái phụ thuộc trước cái nền — cùng lý do destructor và defer stack unwound ngược. Trong một fiber, thứ tự ngược bảo vệ phụ thuộc tự động; giữa các fiber, dsh thật dùng inject để fiber phụ thuộc unload trước provider."
  - q: "Kernel Mini-dsh dùng được cho production không?"
    a: "Đây là bản giáo dục của Cordis — kernel thật mà dsh vendored trong dsh 0.1.0-rc.7. Cordis có 6 state fiber, effect nhận Promise và AsyncIterable, inject-driven reload và 5 chế độ dispatch event; Mini-dsh giữ đúng một primitive effect() và emit. Nắm kernel nhỏ này là đọc source Cordis dễ hơn nhiều."
---

Bài trước kết thúc ở một seam chưa ai cắm vào: Message và contract `model(messages)` đang chờ người dùng đầu tiên ([Agent harness là gì](/bai-viet/chuong-trinh-harness-engineer)). Người dùng đó không phải agent loop — mà là kernel: phần sở hữu vòng đời của mọi thứ cắm vào harness.

Bài này trả lời đúng một design question: **ai phải sở hữu cleanup của plugin?** Câu trả lời của dsh — kernel thật mà DeepSeek dùng — là framework giữ hết, và nó đắt giá hơn bạn nghĩ: cùng một cơ chế này chặn được leak, và mở đường cho hot reload, test teardown, subagent shutdown.

## Design question: ai phải sở hữu cleanup?

Slogan của dsh là "everything is a plugin": tools, session stores, prompt sections, cả subsystem nguyên vẹn — tất cả mount và unmount khi harness đang chạy: đổi profile, hot reload, test teardown, subagent shutdown.

Cách quản cleanup mà ai cũng viết trước: convention. Mỗi plugin tự viết một `cleanup()` unregister những gì nó đăng ký.

Convention đó dễ vỡ một cách âm thầm: plugin thêm một listener trong một code path mới, quên dòng unregister tương ứng — và từ giờ unloading nó leak một callback bắn vào một plugin đã chết, mãi mãi. Không có gì trong cấu trúc code bắt người viết nhớ điều đó; chỉ có review và may mắn.

Kernel đảo quyền sở hữu:

> **Everything is a plugin, and every registration is reversible.**

Đăng ký một thứ *là* trao framework cái undo. Bốn yêu cầu để nguyên tắc đứng vững:

1. Mọi registration — listener, service, bất cứ gì — phải sản xuất một undo (**disposer**).
2. Disposer gom trên **fiber** sở hữu plugin: unmount là một thao tác framework duy nhất — chạy ngược toàn bộ.
3. Mỗi disposer chạy tối đa một lần, bất kể ai gọi trước.
4. Registration trên fiber đã disposed là một error, không phải silent leak.

## Fiber: đơn vị lifetime của một plugin

Fiber là danh sách undo có thứ tự cộng một state gate. Code trích từ `src/kernel.py`:

```python
class InactiveEffectError(RuntimeError):
    """Đăng ký effect trên fiber đã disposed."""


class Fiber:
    """Đơn vị lifetime của một plugin: danh sách undo có thứ tự."""

    def __init__(self, label):
        self.label = label
        self.state = "loading"  # loading -> active -> disposed
        self._disposers = []

    def collect(self, dispose, label=""):
        if self.state == "disposed":
            raise InactiveEffectError(
                f"cannot register {label or 'effect'} on disposed fiber '{self.label}'"
            )
        entry = {"dispose": dispose, "done": False}

        def run():
            if not entry["done"]:
                entry["done"] = True
                entry["dispose"]()

        self._disposers.append(run)
        return run  # single-shot: gọi sớm cũng an toàn, fiber không chạy lại

    def dispose(self):
        if self.state == "disposed":
            return
        self.state = "disposed"
        for run in reversed(self._disposers):
            run()
        self._disposers.clear()
```

Ba chi tiết nắm trọn cơ chế:

- **`collect` là điểm chặn duy nhất.** Mọi undo đi qua đây: fiber disposed thì raise, còn lại thì nhận vào danh sách và trả lại disposer.
- **Single-shot là phần chống lỗi dễ bị bỏ qua.** Caller gọi disposer sớm, rồi fiber dispose chạy lại — entry `done` đảm bảo undo chỉ chạy đúng một lần.
- **`reversed` là toàn bộ semantic của teardown.** Không plugin nào tự xếp thứ tự dỡ — framework làm hộ.

## Hình dạng của một plugin

Một plugin chỉ là một hàm nhận context của nó:

```python
def echo_plugin(ctx):
    ctx.on("say", heard.append)                    # đăng ký #1
    ctx.provide("echo", lambda t: f"echo: {t}")    # đăng ký #2
    # không một dòng cleanup nào: undo đã nằm trên fiber của plugin

fiber = ctx.plugin(echo_plugin)   # mount
fiber.dispose()                   # unmount: cả listener lẫn service biến mất
```

Và mỗi registration API của context chỉ dài ba dòng: làm việc thật, rồi trao `effect()` cái undo. Hai API nền của Mini-dsh:

```python
def on(self, event, callback):
    listeners = self._root._listeners.setdefault(event, [])
    listeners.append(callback)
    return self.effect(lambda: listeners.remove(callback), f"on({event})")

def provide(self, name, value):
    services = self._root._services
    if name in services:
        raise ValueError(f"service '{name}' already provided")
    services[name] = value
    return self.effect(lambda: services.pop(name), f"provide({name})")
```

`on` đăng ký listener cho một event; `provide` đăng ký một service mà plugin khác lấy qua `ctx.get()`. Cả hai xây trên đúng một primitive — `effect()`:

```python
def effect(self, dispose, label=""):
    return self.fiber.collect(dispose, label)
```

Mount và unmount đối xứng by construction:

```text
mount:    plugin(apply) ──► new Fiber ──► apply(child ctx)
                                         mỗi ctx.on / ctx.provide / ctx.effect
                                         đẩy một undo lên fiber
unmount:  fiber.dispose() ──► undo chạy ngược ──► registration biến mất
```

Thứ tự ngược có lý do: plugin đăng ký nền móng trước và thứ phụ thuộc sau, nên teardown phải dỡ phụ thuộc trước nền — cùng lý do destructor và defer stack unwound ngược.

## Code đầy đủ chạy được

Ghép lại thành một file chạy được — đây là kernel đủ dùng của Mini-dsh:

```python
# mini_kernel.py — Phase 2 của Mini-dsh: Fiber, effect(), Context
# Chỉ Python stdlib — không API key, không mạng.

class InactiveEffectError(RuntimeError):
    """Đăng ký effect trên fiber đã disposed."""


class Fiber:
    def __init__(self, label):
        self.label = label
        self.state = "loading"  # loading -> active -> disposed
        self._disposers = []

    def collect(self, dispose, label=""):
        if self.state == "disposed":
            raise InactiveEffectError(
                f"cannot register {label or 'effect'} on disposed fiber '{self.label}'"
            )
        entry = {"dispose": dispose, "done": False}

        def run():
            if not entry["done"]:
                entry["done"] = True
                entry["dispose"]()

        self._disposers.append(run)
        return run

    def dispose(self):
        if self.state == "disposed":
            return
        self.state = "disposed"
        for run in reversed(self._disposers):
            run()
        self._disposers.clear()


class Context:
    """View của một plugin lên toàn app. Mọi registration gom trên fiber của view."""

    def __init__(self, root=None, fiber=None):
        self._root = root if root is not None else self
        self.fiber = fiber if fiber is not None else Fiber("root")
        if self._root is self:
            self.fiber.state = "active"
            self._services = {}
            self._listeners = {}  # event name -> list of callbacks

    def effect(self, dispose, label=""):
        return self.fiber.collect(dispose, label)

    def plugin(self, apply):
        """Mount: chạy plugin với một child view. Trả về fiber của nó."""
        fiber = Fiber(getattr(apply, "__name__", "plugin"))
        apply(Context(self._root, fiber))
        fiber.state = "active"
        return fiber

    def on(self, event, callback):
        listeners = self._root._listeners.setdefault(event, [])
        listeners.append(callback)
        return self.effect(lambda: listeners.remove(callback), f"on({event})")

    def emit(self, event, *args):
        for callback in list(self._root._listeners.get(event, [])):
            callback(*args)

    def provide(self, name, value):
        services = self._root._services
        if name in services:
            raise ValueError(f"service '{name}' already provided")
        services[name] = value
        return self.effect(lambda: services.pop(name), f"provide({name})")

    def get(self, name):
        return self._root._services.get(name)


if __name__ == "__main__":
    ctx = Context()
    heard = []

    def echo_plugin(ctx):
        ctx.on("say", heard.append)
        ctx.provide("echo", lambda t: f"echo: {t}")

    fiber = ctx.plugin(echo_plugin)
    ctx.emit("say", "one")
    assert heard == ["one"]
    assert ctx.get("echo")("hi") == "echo: hi"

    fiber.dispose()                      # unmount: undo chạy ngược
    ctx.emit("say", "two")
    assert heard == ["one"], "listener phải biến mất sau dispose"
    assert ctx.get("echo") is None, "service phải biến mất sau dispose"

    # unmount một plugin không đụng hàng xóm
    ctx.plugin(lambda c: c.provide("a", 1))
    b_fiber = ctx.plugin(lambda c: c.provide("b", 2))
    b_fiber.dispose()
    assert ctx.get("a") == 1 and ctx.get("b") is None

    print("kernel OK: mount/unmount đối xứng, hàng xóm còn nguyên")
```

Chạy file này (lưu thành `mini_kernel.py`, `python3 mini_kernel.py`) cho ra dòng cuối: `kernel OK: mount/unmount đối xứng, hàng xóm còn nguyên` — plugin viết đúng một hình: đăng ký, không cleanup, framework dọn.

## Chạy thử trên repo

Ba lệnh, không key:

```bash
git clone https://github.com/hardness1020/learn-deepseek-harness
cd learn-deepseek-harness
python sections/01-kernel/src/test.py
```

Output:

```
section 01: all checks passed
```

Test này đứng trên 6 nhận định, mỗi nhận định chặn một loại lỗi:

1. **Mount-then-unmount reversibility** — hai registration, zero dòng cleanup trong plugin; sau dispose cả listener lẫn service biến mất.
2. **Reverse-order unwind** — plugin đăng ký a, b, c; dispose dừng ra c, b, a.
3. **Single-shot disposer** — caller gọi undo sớm, rồi fiber dispose vẫn chỉ chạy đúng một lần.
4. **Double dispose là no-op** — dispose lần hai không nổ, không chạy lại gì.
5. **Registration trên fiber đã disposed** — raise `InactiveEffectError`, không phải silent leak.
6. **Neighbor isolation** — unmount plugin a, service của plugin b còn nguyên.

Section này chưa gọi model nên không có demo API-key — kernel thuần quy luật vòng đời.

> 📍 Section kế copy nguyên `src/` của section này rồi thêm đúng một cơ chế: session log sẽ mount lên kernel như một service — lần đầu tiên bạn thấy một plugin thật cắm vào lớp điều phối vừa dựng.

## Registration một chiều vs reversible

| Khía cạnh | Convention `cleanup()` (plugin tự dọn) | Reversible registration (framework sở hữu undo) |
| --- | --- | --- |
| Ai giữ undo | Plugin tự nhớ viết ở mỗi nơi | Fiber gom tự động qua `effect()` |
| Code path mới thêm listener | Dễ quên unregister → leak | API trả disposer sẵn, không có chỗ để quên |
| Thứ tự teardown | Plugin tự lo, dễ sai | Ngược thứ tự đăng ký, mặc định |
| Cleanup gọi hai lần | Phụ thuộc kỷ luật plugin | Single-shot, gọi sớm cũng an toàn |
| Đăng ký sau khi unmount | Silent leak | `InactiveEffectError` |
| HMR / reload / test teardown | Phải viết riêng cho từng case | Cùng một code path: dispose-then-mount |

Cột phải không thông minh hơn cột trái — nó chỉ đẩy mọi quyết định về undo về đúng một điểm: `collect()`. Một điểm chặn thì test được; convention rải rác thì không.

## Failure modes thật của kernel

Năm cách thiết kế này hỏng khi dùng sai — ghi chú trực tiếp từ nguồn:

1. **Cleanup ngoài `effect()` là vô hình.** Plugin mở file, spawn thread mà không bọc undo vào `ctx.effect()` thì leak khi unmount, và framework không nhìn thấy gì để cứu. Kỷ luật phải toàn phần: *mọi* side effect đi qua `effect()`.
2. **Một disposer throw dừng cả unwind.** Một undo hỏng dừng phần còn lại của cleanup fiber. Mini-dsh chấp nhận để giữ kích thước; Cordis thật isolate lỗi từng disposer để bug của một plugin không kẹt teardown của plugin khác.
3. **Undo phụ thuộc state đã undone.** Reverse order bảo vệ phụ thuộc *trong một fiber*, nhưng giữa các fiber không có thứ tự ở đây. dsh thật xếp lớp `inject` bên trên để fiber phụ thuộc unload trước provider của nó.
4. **Đăng ký trong teardown.** Callback phát giữa dispose mà đăng ký effect mới sẽ leak âm thầm — vì vậy fiber disposed raise thay vì nhận.
5. **Giữ tham chiếu service qua unmount.** `ctx.get("echo")` trả một object sống; caller cache nó là giữ nó chạy sau khi provider đã chết. Quy tắc: resolve at use time, never cache.

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| `InactiveEffectError` khi `fiber.collect(...)` | Đăng ký trên fiber đã disposed — đúng thiết kế | Tạo fiber mới qua `ctx.plugin()`; không cố hồi sinh fiber cũ |
| `ValueError: service 'x' already provided` | `provide` trùng tên service đang sống | Đổi tên, hoặc unmount plugin đang giữ service trước |
| Service vẫn chạy sau unmount | Caller giữ tham chiếu lấy trước dispose | Resolve tại thời điểm dùng qua `ctx.get()`, không cache |
| Listener hàng xóm mất theo unmount | Các plugin đăng ký trên cùng một context gốc | Mỗi plugin mount qua `ctx.plugin()` — registration nằm trên fiber riêng |
| `emit` không đến ai | Không listener cho event đó | Không phải lỗi — kiểm tra tên event chính xác trước khi debug |

## Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: chạy `python sections/01-kernel/src/test.py`, rồi tự viết plugin thứ hai đăng ký listener riêng, unmount plugin thứ nhất qua fiber của nó và chứng minh listener của plugin hai vẫn nhận `emit` — neighbor isolation bằng tay của bạn.

**Mức 2 — Tự sửa**: thêm API `ctx.on_once(event, callback)` — listener tự gỡ sau lần phát đầu. Gợi ý: dùng chính disposer trả về từ `ctx.on()` để tự gỡ bên trong callback. Điểm cần thấy: bạn viết được API mới mà không đụng vào Fiber — mọi thứ đã reversible sẵn.

**Mức 3 — Mở rộng**: mount một `logging_plugin` đăng ký `ctx.on("log", ...)` ghi mọi sự kiện vào list, rồi unmount và chứng minh list dừng đúng lúc — lớp điều phối cho bài session log. Bonus: viết mini-HMR — unmount rồi mount lại cùng plugin và chứng minh service quay lại nguyên trạng: reload chỉ là dispose-then-mount.

## Tài liệu gốc

- [hardness1020/learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness) — section `01-kernel` là nguồn code bài này; bảng "In real dsh" map từng chi tiết vào Cordis vendored trong dsh pinned commit `99f6f02`.
- [cordiverse/cordis](https://github.com/cordiverse/cordis) — upstream framework mà dsh vendored và patch 18 chỗ; `Fiber`, `effect()`, `inject` đều đến từ đây.

Đọc tiếp lộ trình [Xây dựng Agent Harness từ số 0 với Mini-dsh](/bai-viet/chuong-trinh-harness-engineer):

- [Agent harness là gì](/bai-viet/chuong-trinh-harness-engineer) — bài trước: Message và Model seam, cái kernel này cắm vào.
- [Session log và compaction](/bai-viet/chuong-trinh-harness-engineer) — service đầu tiên mount lên kernel này.
- [Agent loop state machine](/bai-viet/chuong-trinh-harness-engineer) — phase cuối của bản đồ 4 phase.

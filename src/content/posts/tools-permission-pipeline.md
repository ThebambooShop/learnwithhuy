---
title: "Tools và permission pipeline: quyết định call nào được phép chạy"
description: "Registry tool scoped và pipeline 5 giai đoạn pre-ask-guard-execute-post của Mini-dsh: vì sao tool call bị từ chối vẫn phải trả về tool/result, và permission nằm ở đâu trong harness."
topic: "harness-engineer"
date: "2026-11-22"
cover: "/images/covers/posts/tools-permission-pipeline.jpg"
featured: false
views: 140
faq:
  - q: "Tại sao tool call bị từ chối vẫn trả về tool/result?"
    a: "Nếu bị từ chối mà im lặng, model tưởng lệnh đã chạy và tiếp tục dựa trên giả định sai. Trả về tool/result với nội dung 'denied: lý do' là tín hiệu rõ ràng để model chọn hướng khác hoặc tổng hợp câu trả lời — đây là pattern của dsh thật."
  - q: "Permission và guard khác nhau ở điểm nào?"
    a: "Guard là quy tắc code tự chặn (cấm ghi file ngoài thư mục X). Ask là quyết định của con người (xin duyệt trước khi chạy). Hai lớp này độc lập: một call có thể qua guard nhưng vẫn cần ask, hoặc bị guard chặn không cần hỏi ai."
  - q: "Nên check permission ở model hay ở harness?"
    a: "Ở harness. Model có thể bị prompt injection khiến nó muốn gọi tool nguy hiểm; chỉ harness — code thật sự chạy tool — mới có quyền nói không. Đó là lý do pipeline nằm trong registry của harness, không phải trong prompt."
  - q: "Registry scoped nghĩa là gì?"
    a: "Tool được đăng ký trong một scope (phiên, subagent, plugin) và tự mất hiệu lực khi scope đó đóng — đúng nguyên tắc reversible registration của kernel. Không có registry toàn cục không dọn được."
---

Bài trước, agent loop của bạn đã chạy được tool đầu tiên: model xuất call, code chạy, kết quả append vào context. Nhưng vẫn còn một khoảng trống to đùng nằm giữa model và code: ai quyết định call nào được phép chạy? Và khi quyết định là không — ai trả lời câu hỏi mà model vừa đặt ra?

Bài này xây đúng lớp đó của Mini-dsh: một **scoped registry** quản lý tool theo phạm vi, và một **pipeline 5 giai đoạn** — pre → ask → guard → execute → post — quyết định số phận từng call. Nguyên tắc xuyên suốt chỉ có một: mọi call đều kết thúc bằng một `tool/result` bình thường, kể cả khi nó bị từ chối, sai tham số, hoặc tên không tồn tại. Nguồn là [tutorial learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness), section 05-tools — link đầy đủ ở cuối bài.

## Tại sao call bị từ chối vẫn phải có câu trả lời

Cách làm hiển nhiên cho tools là một dict hàm: tìm tên, gọi, append những gì nó trả về. Tên lạ? Raise. Tham số sai? Raise. Policy không cho? Raise trước khi gọi. Vấn đề: mỗi raise ấy đều nổ **giữa turn** — message assistant chứa call đã nằm trong log từ trước, exception làm `send()` unwind, và hội thoại giữ lại một câu hỏi không có ai trả lời.

Ba đường dẫn lỗi khác nhau, cùng một hậu quả:

- **Tên tool không tồn tại** — raise "unknown tool".
- **Tham số sai** — raise khi unpack args.
- **Policy chặn** — raise trước khi body chạy.

> **Tại sao call bị từ chối hay lỗi vẫn phải trả về `tool/result` bình thường? Vì transcript là hợp đồng.** Model phải đọc được tín hiệu rõ ràng để tự sửa: im lặng là model tưởng lệnh đã chạy và tiếp tục dựa trên giả định sai, hoặc reissue lệnh đó vô hạn; raise là turn chết với một câu hỏi không có câu trả lời, và replay tái dựng đúng cái lỗ hổng đó. `{"is_error": true, "content": "denied: <lý do>"}` — cùng shape với kết quả thành công — là tín hiệu xấu nhưng rõ ràng: model đọc nó như một tool result bình thường rồi đổi hướng, hoặc tổng hợp câu trả lời từ dữ liệu đã có.

Muốn giữ đúng hợp đồng đó, tools layer phải bảo đảm một điều duy nhất: **mọi lối ra qua cùng một cửa**. Một denial, một crash, tham số sai hay tên lạ đều rời pipeline bằng cùng một result dict `{call_id, name, is_error, content}`. Body tool là phần không đáng tin — nó có thể raise bất cứ lúc nào — nhưng pipeline thì không được.

## Scoped registry: tool tồn tại theo phạm vi

Trước khi chạy được, call phải resolve được tên. Registry của Mini-dsh không phải một dict phẳng mà là các layer:

- Một layer **global** chứa tool dùng chung.
- Mỗi agent scope có một layer riêng, **shadow** tên global: cùng tên thì layer scope thắng.
- **Restriction** là danh sách tên được phép còn lại của một scope — và mọi restriction áp dụng cho scope phải **intersect**: một name chỉ visible khi nó nằm trong tất cả các restriction đó. Shadowing chỉ có thể thêm hoặc thay thế; restriction mới là thứ siết lại.

Hai chi tiết thiết kế dễ bỏ sót:

- **Tool bị restrict không phải bị "denied"** — nó đơn giản không tồn tại với scope đó. Gọi nó trả về `unknown tool`, một result bình thường như mọi result khác. Model không cần biết khái niệm permission để hiểu transcript của mình.
- **Mọi đăng ký đều trả về undo.** `register`, `restrict`, `pre`, `guard`, `post` đều trả về một callable gỡ chính nó — đúng nguyên tắc reversible registration mà [kernel và plugin](/bai-viet/kernel-plugin-thiet-ke-harness) đã chốt từ bài trước: plugin chết thì tool của plugin phải mất theo. Không có registration toàn cục không dọn được.

Nhờ vậy `request/header` giờ ghi danh sách tool mỗi request được offer: log tự minh chứng scope nhìn thấy gì. Scope B bị restrict còn `["where"]` thì transcript của B chỉ thấy `where`, trong khi scope A vẫn thấy hết — và sự khác biệt ấy nằm ngay trong log, không cần đoán.

## Pipeline 5 giai đoạn: pre → ask → guard → execute → post

Pipeline là một cái phễu. Mỗi giai đoạn có quyền quay call lại, và mọi lối thoát đều cùng một cửa:

```
call {"id", "name", "args"}
  │ resolve    tên lạ ──────────────────────────────────────┐
  │ pre        vote allow / ask / deny, chỉ siết không nới ─┤
  │ ask        không asker, không duyệt ─────────────────────┤
  │ guard      lý do chặn (deny-only) ───────────────────────┤
  │ execute    sai tham số, body raise ──────────────────────┤
  ▼                                                           ▼
{"is_error": false, "content"}           {"is_error": true, "content"}
        └────────────────────┬───────────────────────────────┘
                           post (review, có thể thay result)
                             ▼
                  một shape duy nhất, append làm tool/result
```

| Giai đoạn | Nhận gì | Làm gì | Câu trả lời khi từ chối |
| --- | --- | --- | --- |
| **pre** | call | Vote `allow` / `ask` / `deny` theo chính sách; vote chỉ siết, không nới | `denied before execution` |
| **ask** | vote `ask` từ pre | Xin phép con người qua seam `asker`; không có asker = deny (fail closed) | `approval was asked and not given` |
| **guard** | call đã qua chốt duyệt | Chặn theo quy tắc code — deny-only, không có quyền cho phép | `denied: <lý do>` |
| **execute** | call qua hết chốt | Validate tham số (thiếu/thừa) rồi chạy body; body raise thì bắt lại | `invalid args: ...` hoặc `TypeError: ...` |
| **post** | (call, result) | Review hậu xử lý — có thể thay result bằng result khác | đổi nội dung result, không sinh row mới |

Ba quy tắc giữ pipeline không tự cãi nhau:

1. **Vote chỉ siết**: `_RANK = {"allow": 0, "ask": 1, "deny": 2}` — hook sau không thể nới quyết định của hook trước. Nhiều chính sách cùng áp dụng thì đường nghiêm nhất thắng.
2. **Ask fail closed**: mặc định cho phép biến một harness chưa cấu hình thành harness permissions nhất. Gate này phải tắt đúng hướng: `ask` mà không ai duyệt là `deny`.
3. **Guard deny-only và đơn điệu**: bất kỳ guard nào cũng chỉ thu nhỏ những gì được chạy, nên thứ tự đăng ký không đổi kết quả. Guard có quyền approve sẽ ghi đè deny của guard khác tuỳ thứ tự — nên nó không được tồn tại.

⚠️ Phân biệt hai lớp này trước khi nhầm: **guard là quy tắc code tự chặn** (cấm ghi file ngoài thư mục X), **ask là quyết định của con người** (xin duyệt trước khi chạy). Một call có thể qua guard mà vẫn cần ask, hoặc bị guard chặn cứng không cần hỏi ai.

## Permission nằm ở harness, không nằm ở model

Vì sao không ghi chính sách vào system prompt kiểu "đừng gọi tool nguy hiểm"? Vì model chỉ **đề xuất** call — nó có thể bị prompt injection đẩy sang gọi thứ không nên gọi. Chỉ harness — code thật sự chạy tool — mới có quyền nói không. Pipeline nằm trong registry của harness, không nằm trong prompt.

Câu hỏi phân loại nhanh khi debug:

| Triệu chứng | Sửa ở đâu | Lớp |
| --- | --- | --- |
| Model chọn sai tool, điền sai tham số | Tên, description, schema trong `ToolDefinition` | prompt |
| Model muốn gọi thứ nguy hiểm | pre / guard / ask trong registry | code |
| Tool chậm hoặc đụng state chung | khai báo an toàn + scheduler | code — bài kế |

Nếu bạn đã đọc bài [Tool use và Routing](/bai-viet/agent-routing-va-tool-design), đây là cùng một kết luận mở rộng thêm một tầng: schema và mô tả là prompt — model đọc để chọn đúng; registry và pipeline là code — harness dùng để chặn đúng. Model chọn sai tool thì sửa mô tả; model muốn chạy thứ nguy hiểm thì sửa pipeline. Hai công cụ, hai lớp, không thay thế nhau.

## Code rút gọn, chạy được ngay

Bản Mini-dsh đầy đủ nằm trong repo kèm test offline. Bản rút gọn dưới đây giữ đúng pipeline và scoped registry, chỉ dùng stdlib — lưu thành `pipeline.py`, chạy `python3 pipeline.py`, không cần API key:

```python
# pipeline.py — scoped registry + pipeline pre/ask/guard/execute/post
# Chỉ stdlib: python3 pipeline.py chạy ngay, không cần API key.

_RANK = {"allow": 0, "ask": 1, "deny": 2}


class ToolRegistry:
    """Layer tool theo scope, các hook chính sách, và pipeline 5 giai đoạn.

    Mọi lối ra của execute() đều là result dict {call_id, name, is_error,
    content}: deny, crash, sai tham số hay tên lạ không bao giờ raise qua
    biên giới này, vì model phải đọc được một transcript trọn vẹn.
    """

    def __init__(self):
        self._layers = {None: {}}  # scope None = global; scope khác = layer riêng
        self._restrictions = []    # (scope, frozenset tên được phép còn lại)
        self._pre = []             # call -> "allow" | "ask" | "deny" | None
        self._guards = []          # call -> lý do chặn (string) | None
        self._post = []            # (call, result) -> result thay thế | None
        self.asker = None          # call -> bool; không có asker thì "ask" = deny

    # -- đăng ký: mỗi hàm trả về một undo, registration luôn hồi được -----
    def register(self, tool, scope=None):
        layer = self._layers.setdefault(scope, {})
        layer[tool["name"]] = tool
        return lambda: layer.pop(tool["name"])

    def restrict(self, names, scope=None):
        entry = (scope, frozenset(names))
        self._restrictions.append(entry)
        return lambda: self._restrictions.remove(entry)

    def pre(self, hook):
        self._pre.append(hook)
        return lambda: self._pre.remove(hook)

    def guard(self, check):
        self._guards.append(check)
        return lambda: self._guards.remove(check)

    def post(self, hook):
        self._post.append(hook)
        return lambda: self._post.remove(hook)

    # -- resolution: layer scope shadow global, restriction intersect -----
    def _visible(self, scope):
        merged = dict(self._layers.get(None, {}))
        merged.update(self._layers.get(scope, {}))
        return {
            name: tool
            for name, tool in merged.items()
            if all(
                name in allowed
                for for_scope, allowed in self._restrictions
                if for_scope is None or for_scope == scope
            )
        }

    # -- pipeline: pre -> ask -> guard -> execute -> post -----------------
    def execute(self, call, scope=None):
        return self._review(call, self._run(call, scope))

    def _run(self, call, scope):
        name = call["name"]
        tool = self._visible(scope).get(name)
        if tool is None:
            return self._result(call, True, f"unknown tool '{name}'")
        decision = "allow"
        for hook in list(self._pre):
            vote = hook(call)
            if vote is not None and _RANK[vote] > _RANK[decision]:
                decision = vote  # vote chỉ siết, không bao giờ nới
        if decision == "deny":
            return self._result(call, True, "denied before execution")
        if decision == "ask":
            approved = self.asker is not None and self.asker(call)
            if not approved:
                return self._result(call, True, "approval was asked and not given")
        for check in list(self._guards):
            reason = check(call)
            if reason:
                return self._result(call, True, f"denied: {reason}")
        args = dict(call.get("args", {}))
        missing = sorted(set(tool["params"]) - set(args))
        unknown = sorted(set(args) - set(tool["params"]))
        if missing or unknown:
            return self._result(
                call, True, f"invalid args: missing {missing}, unknown {unknown}"
            )
        try:
            return self._result(call, False, str(tool["execute"](args)))
        except Exception as exc:  # body có thể lỗi; pipeline thì không
            return self._result(call, True, f"{type(exc).__name__}: {exc}")

    def _review(self, call, result):
        for hook in list(self._post):
            result = hook(call, result) or result
        return result

    @staticmethod
    def _result(call, is_error, content):
        return {
            "call_id": call.get("id"),
            "name": call["name"],
            "is_error": is_error,
            "content": content,
        }


if __name__ == "__main__":
    reg = ToolRegistry()

    reg.register({
        "name": "read_note",
        "params": {"key": "khoá cần đọc"},
        "execute": lambda a: {"wifi": "hunter2"}.get(a["key"], "không có ghi chú"),
    })
    reg.register({
        "name": "write_note",
        "params": {"key": "khoá cần ghi", "value": "nội dung"},
        "execute": lambda a: f"đã ghi '{a['key']}'",
    })
    reg.register({
        "name": "delete_all",
        "params": {},
        "execute": lambda a: "XOÁ TOÀN BỘ",  # sẽ không bao giờ được chạy tới
    })

    # Chính sách 1: ghi dữ liệu phải xin phép (pre vote "ask") — nhưng
    # chưa cắm asker: ask mà không ai duyệt là deny, fail closed.
    reg.pre(lambda c: "ask" if c["name"] == "write_note" else None)
    # Chính sách 2: delete_all là tool phá hoại, guard chặn cứng.
    reg.guard(lambda c: "delete_all chặn cứng" if c["name"] == "delete_all" else None)
    # Post: review mọi result, kể cả result lỗi, gắn một nhãn cuối.
    reg.post(lambda c, r: {**r, "content": r["content"] + " [đã review]"})

    calls = [
        {"id": "c1", "name": "read_note", "args": {"key": "wifi"}},
        {"id": "c2", "name": "write_note", "args": {"key": "note", "value": "x"}},
        {"id": "c3", "name": "delete_all", "args": {}},
        {"id": "c4", "name": "read_note", "args": {"sai": 1}},
        {"id": "c5", "name": "no_such_tool", "args": {}},
    ]
    for call in calls:
        r = reg.execute(call)
        print(f"{r['call_id']} {r['name']}: is_error={r['is_error']} -> {r['content']}")
```

Kết quả chạy thật — năm call, năm lối ra, một shape:

> c1 read_note: is_error=False -> hunter2 [đã review]
> c2 write_note: is_error=True -> approval was asked and not given [đã review]
> c3 delete_all: is_error=True -> denied: delete_all chặn cứng [đã review]
> c4 read_note: is_error=True -> invalid args: missing ['key'], unknown ['sai'] [đã review]
> c5 no_such_tool: is_error=True -> unknown tool 'no_such_tool' [đã review]

Cái vòng loop cắm pipeline vào đâu? Đúng vào socket mà [agent loop state machine](/bai-viet/agent-loop-state-machine) để trống ở bài trước:

```python
def run_tool_arm(session, tools, reply):
    """Rút gọn từ agent_loop.py: socket reason None của bài trước."""
    for call in reply.tool_calls:
        session.append("tool/call", call)      # log-only: ghi trước khi chạy
        result = tools.execute(call)           # 5 giai đoạn, mọi lối ra là result
        session.append("tool/result", result)  # surface: model đọc ở lượt derive kế
    session.append("step/end", {"reason": None})
    return None  # còn tool call chưa được trả lời: quay lại một step nữa
```

Hai loại row, hai vai trò: `tool/call` **log-only** — ghi trước khi dispatch để replay có thứ tự gọi; `tool/result` **surface** — append sau khi có kết quả để lượt derive kế model đọc được. Reply có calls thì step kết thúc với `reason: None` → quay lại một step nữa. Model nhận cả call và result như lịch sử thường, không có nhánh đặc biệt nào cho "lệnh bị từ chối".

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Raise khi bị deny → transcript rách | coi từ chối là lỗi ngôn ngữ | trả result `is_error: true` kèm lý do |
| Bỏ qua call denied một cách im lặng | nghĩ "không chạy thì thôi" | model đợi hoặc reissue vô hạn — luôn phải trả lời |
| `ask` mà default allow | muốn "tiện" khi chưa có UI duyệt | fail closed: không asker là deny |
| Guard có nhánh approve | muốn linh hoạt hơn | deny-only, đơn điệu — thứ tự không đổi kết quả |
| Body raise làm chết cả loop | thiếu try/except ở biên pipeline | bắt mọi exception trong `execute`, trả thành result |
| Plugin chết mà tool còn nguyên | registration không undo | mọi đăng ký trả về undo, người đăng ký thu gom |
| Scope chỉ nới không siết | chỉ shadow, không restrict | intersect mọi restriction áp dụng cho scope |

## Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: chạy file trên, đọc kỹ 5 result. Rồi gắn `reg.asker = lambda call: True` và chạy lại — `write_note` giờ qua chốt ask. Mục đích: thấy seam `asker` là điểm duy nhất cần cắm UI duyệt thật vào.

**Mức 2 — Tự sửa**: thêm một pre hook vote `deny` cho mọi tool có tên bắt đầu bằng `delete`, rồi kiểm chứng call bị pre-deny **không** chạm tới guard cũng không chạm tới body (thêm một biến đếm số lần body chạy). Mục đích: hiểu vote chỉ siết và pipeline dừng sớm ngay giai đoạn vi phạm.

**Mức 3 — Mở rộng**: dựng `ToolScope` cho một subagent — register một layer riêng shadow tên global, rồi `restrict(["read_note"])` cho scope đó; gọi một tool bị restrict từ scope này và xác nhận trả về `unknown tool` như một result bình thường. Đây chính là tiền đề mà bài [capabilities và subagents](/bai-viet/capabilities-subagents-composition) dựa vào khi subagent chỉ nhận một tập con tool của cha.

## Tài liệu gốc

- [hardness1020/learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness) — tutorial rebuild DeepSeek Harness từ số 0 bằng Python stdlib. Bài này từ **section 05-tools**: `src/tools.py` là registry + pipeline đầy đủ, `src/test.py` là check offline không cần API key — `python sections/05-tools/src/test.py`.
- Trong real dsh (packages/core/tools): `ToolRuntime` là registry scoped layers; `tools/pre-execute` là waterfall trả `PreToolDecision = allow | deny | ask`; `ToolGuard` deny-only chạy sau approval; `tools/post-execute` là waterfall `accept | block` kèm enrichment; result thật cũng tách `isError: false | true` giống hệt Mini-dsh.
- Docs của dsh: `docs/tool-execution-pipeline.md` (pipeline từng giai đoạn) và `docs/subsystems/scope.md` (scoped layers, shadowing, restrictions).

Đọc tiếp trong series:

- [Agent loop state machine](/bai-viet/agent-loop-state-machine) — bài trước: vòng turn/step và socket `reason None` mà pipeline cắm vào.
- [Scheduler song song và steering inbox](/bai-viet/scheduler-va-steering-inbox) — bài kế: pipeline chạy thế nào khi model xuất 4 call một lượt, và nói chuyện với agent đang bận ra sao.
- [Lộ trình: Xây dựng Agent Harness từ số 0](/lo-trinh/xay-dung-agent-harness) — toàn bộ 8 bài của series.

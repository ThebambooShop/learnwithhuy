---
title: "System prompt động và Skills: nạp đúng thứ tự, đúng lúc"
description: "System prompt của agent production không phải chuỗi tĩnh: ordered providers sinh system text + tool list + runtime context mỗi step, và skill chỉ inject catalog — body nạp on-demand qua tool call."
topic: "ai-agent"
date: "2026-11-22"
cover: "/images/covers/posts/system-prompt-va-skills.jpg"
featured: false
views: 110
faq:
  - q: "Tại sao dynamic state là user message thay vì system text?"
    a: "System text được cache và coi như cố định trong phiên — ghi trạng thái runtime vào đó phá cache và làm model nhầm nó là quy tắc. Re-emitted user message là 'tình huống mới cho turn này', đúng ngữ nghĩa và giữ cache của phần system."
  - q: "Skill catalog và skill body khác nhau thế nào?"
    a: "Catalog là dòng mô tả ngắn của mọi skill (tên + khi nào dùng) được inject sẵn vào context. Body là nội dung đầy đủ, chỉ nạp khi model gọi tool load skill. Vốn context cho catalog là hằng số, không tăng theo số skill."
  - q: "Số skill nhiều có làm context phình không?"
    a: "Chỉ phình nếu bạn inject full body. Thiết kế catalog-inject + on-demand-load giữ mức tiêu thụ cố định — đây là lý do dsh làm layered provider registry thay vì paste hết vào system prompt."
  - q: "Thứ tự provider có quan trọng không?"
    a: "Có. Ordered providers quyết định phần nào đứng trước (quy tắc cứng) phần nào sau (bối cảnh mềm). Đổi thứ tự là đổi hành vi model — nên composition cần patch layers thay vì deep-merge."
---

Bài [Scheduler và steering inbox](/bai-viet/scheduler-va-steering-inbox) đã chốt điều kiện vào cửa: mọi thứ vào phiên qua boundary, mọi call trả lời trước khi step đóng. Nhưng nhìn lại request mà bài đó gửi model thì còn một khoảng trống to: không có system text nào. Model chưa từng được biết nó là ai, phải cư xử thế nào, hay thế giới ngoài đang trông ra sao.

Đây không phải lỗi quên viết prompt — mà là không ai có quyền viết một mình. Nhiều bộ phận của harness cùng sở hữu một mẩu: Mini-dsh viết dòng identity của chính nó, một plugin persona viết giọng điệu, tầng tool viết danh sách schema. Mỗi bên muốn góp phần của mình mà không phối hợp với bên khác, và mẩu đó phải rơi vào đúng chỗ trong mọi request. Nhiệm vụ thứ hai còn khó hơn: một đống instruction text cho công việc chuyên môn (skill) — quá lớn để ship mỗi step, quá hữu ích để bỏ ra ngoài.

Bài này trả lời hai design question của section 08 và 09 trong Mini-dsh, rồi đưa ra một registry chạy được bằng Python stdlib, không API key.

## Design question 1: trạng thái động để đâu?

> **Tại sao dynamic state là user message re-emitted thay vì system text?** Vì system text phải byte-identical giữa các step — provider cache trên một stable prompt prefix, và system text đứng đầu prefix đó. Một dòng timestamp render lại mỗi step là không request nào được dùng lại cache. Và vì log phải giữ trọn request history để replay xây lại đúng những gì model đã nhìn thấy. Re-emitted user message là "tình huống mới cho turn này": đúng ngữ nghĩa, giữ cache, và là một row thường trong log.

Ba lý do chồng lên nhau:

- **Cache**: provider cache theo prompt prefix ổn định. System text là phần đầu của prefix, nên nó phải ra nguyên vẹn từng byte mỗi step — bao gồm cả những step mà một provider vừa mount vào giữa phiên.
- **Ngữ nghĩa**: system text là quy tắc — "bạn là ai, bạn phải làm gì". Trạng thái runtime — bây giờ là mấy giờ, cwd là đâu — không phải quy tắc, là hoàn cảnh của turn hiện tại. Nhét hoàn cảnh vào quy tắc là làm model đọc hoàn cảnh thành luật.
- **Replay**: text patch vào request ngoài pipeline thông thường không bao giờ đến log, nên replay không thể xây lại những gì model thực sự thấy — vi phạm trọn vẹn điểm của [session log](/bai-viet/session-log-va-compaction).

## Cơ chế: ordered providers, ba artifact mỗi step

Một file mới, `system_prompt.py`, và luồng request bị kéo qua nó. Registry `SystemPrompt` giữ bốn loại provider:

- **sections** — static system text: identity, persona, quy tắc.
- **contexts** — dynamic runtime state: đồng hồ, cwd, catalog skill.
- **variables** — giá trị cho `{{name}}`.
- **tool-schema providers** — schema tool của request, qua một bridge: tool list cũng là một prompt output.

Mỗi registration trả về undo của nó — mọi thứ đều có thể đảo ngược, đúng tinh thần kernel/plugin của bài [Kernel và plugin: thiết kế harness](/bai-viet/kernel-plugin-thiet-ke-harness). Hàm `assemble()` resolve mọi provider theo `(order, registration order)` và trả về đúng ba artifact:

```python
def assemble(self, assemble_context):
    """Resolve mọi provider theo order: ba artifact của request."""
    sections = [self._render(e["text"], assemble_context)
                for e in _ordered(self._sections)]
    contexts = [e["provider"](assemble_context) for e in _ordered(self._contexts)]
    return {
        "system": "\n\n".join(text for text in sections if text),
        "tools": [s for provider in self._tools for s in provider(assemble_context)],
        "runtime_context": "\n".join(text for text in contexts if text),
    }
```

Ba quy tắc vận hành assembly:

1. **Order là một số, tiebreak theo registration order.** Đăng ký giống nhau luôn render text giống nhau. Dict order hay thread timing là cách chắc chắn miss prefix cache.
2. **Interpolation nghiêm ngặt.** Một `{{name}}` unknown hoặc unset refuse-to-ship — raise, và step dừng trước `request/header`. Không ship prompt có lỗ hổng cho model.
3. **Snapshot dedupe lấy sự thật từ log.** Snapshot giữ lại là row `user/message` mang `"kind": "runtime-context"` cuối cùng trong log — một projection của log, không phải state riêng. Sau resume, memory rỗng nhưng log còn; đạo snapshot từ log là dedupe và replay khớp nhau by construction.

Trong `_step()`, assembly xảy ra ngay sau inbox claim — đúng boundary nơi [agent loop state machine](/bai-viet/agent-loop-state-machine) đã re-derive mọi thứ. Snapshot chỉ append khi khác snapshot cuối:

```python
assembly = self.prompt.assemble({"tools": self.tools})
snapshot = assembly["runtime_context"]
if snapshot and snapshot != latest_snapshot(self.session):
    self.session.append("user/message",
                        {"content": snapshot, "kind": "runtime-context"})
```

Toàn bộ luồng, từ đăng ký đến request:

```text
registered, ordered              assemble(...), mỗi step

sections  -100 harness:identity ─┐
             0 persona           ├─► system text ────► request, byte-identical
variables  {{user}} = "Ada"     ─┘                     mỗi step
tool providers  bridge ──────────► tool list ─────────► request
contexts     0 time: 10:01      ─┐
            10 cwd: /home/ada    ├─► snapshot ─► khác snapshot cuối?
                                 ┘               ├─ có: user/message row
                                                 └─ không: không append gì
```

Một run thật như log ghi lại: tool `tick` đẩy đồng hồ giữa turn; system text 61 ký tự trong cả hai request, từng byte giống nhau, còn snapshot re-emit đúng một lần:

```text
  │   3  user/message   "time: 10:00"         ◄ snapshot, lần đọc đầu
  │   4  request/header system 61 chars, tools ["tick"]
  │   7  tool/result   "ticked"               ◄ đồng hồ giờ là 10:01
  │  10  user/message   "time: 10:01"         ◄ đã đổi: re-emit
  │  11  request/header system 61 chars       ◄ byte-identical
```

## System text và runtime-context snapshot: so sánh

| Tiêu chí | System text (sections) | Runtime-context snapshot (contexts) |
| --- | --- | --- |
| Loại nội dung | Identity, persona, quy tắc — không đổi giữa các step | Đồng hồ, cwd, catalog skill — thay đổi theo runtime |
| Cam kết cache | Byte-identical mỗi step, giữ prefix cache | Không nằm trong system text — không động vào prefix |
| Nơi vào request | Phần đầu, ghi trên `request/header` | Row `user/message`, `"kind": "runtime-context"` |
| Khi thay đổi | Không bao giờ — đây là design constraint | Re-emit đúng một row khi khác snapshot cuối |
| Nguồn sự thật | Registry provider | Log projection — row snapshot cuối trong log |
| Replay | Ghi trên `request/header` | Là row user thường trong derived history |

## Design question 2: catalog hay body?

> **Tại sao inject catalog làm context nhưng load full skill body qua tool call?** Vì "cái gì tồn tại" phải rẻ và luôn hiển thị, còn "nó nói gì" chỉ trả giá khi dùng. Catalog — tên và một dòng mô tả — đi vào mỗi request với chi phí hằng số; body chỉ đi qua một tool call khi model hỏi.

Cả hai vị trí quen thuộc đều không dùng được. Bake mọi instruction vào system text: mỗi request trả tiền cho toàn bộ, dùng hay không. Bỏ hẳn: model không thể dùng cái nó chưa từng nghe nói tới. Instruction text không vừa với ngân sách đó — một harness tích lũy how-to text cho công việc chuyên môn, và một turn dùng gần như không tới phần nào.

Khó hơn nữa: bộ skill không cố định. Skill text đến từ nhiều nguồn cùng lúc — built-in, workspace, plugin — mỗi nguồn mount, unmount hoặc override tên giữa phiên chạy, và không bên nào được sửa text của bên khác.

## Cơ chế: layered provider registry

Registry không giữ skills; giữ providers. Mỗi provider có hai verb: `list()` trả summaries `{name, description}`, `get(name)` trả một body. Providers xếp thành layers theo registration order; layer sau đè tên của layer trước — workspace override built-in mà không chạm vào nó — và `get()` đi ngược từ layer gần nhất. Mỗi registration trả undo.

```python
def catalog(self):
    """Một summary cho mỗi tên hiện thấy; dòng của layer sau thắng."""
    merged = {}
    for provider in self._providers:
        for summary in provider.list():
            merged[summary["name"]] = summary
    return list(merged.values())

def get(self, name):
    """Một body đầy đủ, layer gần nhất trước; None nếu không ai biết tên này."""
    for provider in reversed(self._providers):
        body = provider.get(name)
        if body is not None:
            return body
    return None
```

Catalog không cần cơ chế giao hàng mới. Nó là một context provider của section 08 (order=100), nên snapshot dedupe đã quyết định giúp: catalog đổi → re-emit một row; catalog yên → miễn phí. Body đi chiều ngược lại, qua [tool pipeline và permission](/bai-viet/tools-permission-pipeline) của section 05: model gọi tool `skill {"name": ...}` → `get(name)` → `tool/result`. Tên lạ raise trong body, pipeline trả về `is_error` result bình thường — turn tiếp tục, không sập loop. Catalog rỗng thì không ship gì cả.

Một run thật như log ghi lại:

```text
send("hi")
  │   3  user/message  "skills, load with ..."   ◄ catalog: tên + 1 dòng mỗi skill
  │   4  request/header tools ["skill"]
  │   5  assistant/message {"tool_calls": [skill "haiku"]}
  │   7  tool/result   "Answer with one haiku: ..."  ◄ body, on demand
  │   9  step/start    ◄ catalog không đổi: không row snapshot mới
```

Body ở seq 7 là derived history từ giờ: model trả giá cho nó trong mọi request sau của phiên — nhưng vì nó đã hỏi. Body của `greet` chưa từng được hỏi và chưa tốn một token nào.

## Inject catalog vs load body on-demand

| Tiêu chí | Inject catalog (context) | Load body (tool call) |
| --- | --- | --- |
| Nội dung | Tên + một dòng mô tả mỗi skill | Body đầy đủ của đúng một skill |
| Ai quyết định | Registry render mỗi assembly | Model gọi tool `skill {"name": ...}` |
| Chi phí token | Hằng số theo số skill, mỗi step | Một lần, đúng số skill được hỏi |
| Nơi vào request | runtime-context snapshot | `tool/result` row |
| Khi thay đổi | Catalog đổi → re-emit một row | Mỗi load là một row mới, catalog không đổi |
| Tên lạ | Không thể — catalog luôn khớp registry | `is_error` result, turn tiếp tục |

## Skills trong dsh thật

| Mini-dsh | dsh thật | Ghi chú |
| --- | --- | --- |
| `SkillRegistry`, layers global theo registration order | `packages/skill`: `SkillRegistry` scope-aware | Real dùng `SkillLayer implements ScopeLayer` — subagent có thể thấy catalog khác parent |
| `MemorySkillProvider` (dict) | `FileSystemSkillProvider` | Real đi thư mục skill trên disk, đọc summary không nạp body — token economy giữ tới tận I/O boundary |
| Catalog qua section 08 context provider | Catalog publish qua `agent/pre-step` listeners | Cùng một plane log rows, hai đường khác nhau |
| Re-resolve mỗi assembly | Bus event `skills/change` + cache invalidation | Mini không có cache để invalidate |

Điểm quan trọng nhất để mang về: cả hai đều giữ đúng một đường ra cho body — tool call. Không chữ skill nào lọt vào system text, nên provider mount giữa phiên không bao giờ phá prefix cache.

## Code thực hành: registry mini chạy được

Toàn bộ chỉ dùng stdlib (`re`), không API key — rút gọn từ sections 08 + 09 của Mini-dsh. Lưu thành `system_prompt_skills_mini.py` rồi `python3 system_prompt_skills_mini.py`.

```python
# system_prompt_skills_mini.py — rút gọn từ sections 08 + 09 của Mini-dsh
# Chỉ stdlib, không API key. Chạy: python3 system_prompt_skills_mini.py

import re

_VARIABLE = re.compile(r"\{\{(\w+)\}\}")
IDENTITY = "You are mini-dsh, a small agent harness."


# ------------------------------------------------------------------
# 1. SystemPrompt: bốn loại provider, assemble() ra ba artifact
# ------------------------------------------------------------------
class SystemPrompt:
    def __init__(self):
        self._count = 0        # registration counter: tiebreak tất định
        self._sections = []    # static system text
        self._contexts = []    # dynamic runtime state
        self._variables = {}   # {{name}} -> value
        self._tools = []       # tool-schema providers

    def section(self, name, text, order=0):
        return self._add(self._sections, {"name": name, "text": text, "order": order})

    def context(self, name, provider, order=0):
        return self._add(self._contexts, {"name": name, "provider": provider, "order": order})

    def variable(self, name, value):
        if name in self._variables:
            raise ValueError(f"prompt variable '{name}' already set")
        self._variables[name] = value
        return lambda: self._variables.pop(name)

    def tools(self, provider):
        self._tools.append(provider)
        return lambda: self._tools.remove(provider)

    def _add(self, entries, entry):
        entry["seq"] = self._count
        self._count += 1
        entries.append(entry)
        return lambda: entries.remove(entry)  # mỗi registration trả undo

    def assemble(self, assemble_context):
        """Resolve mọi provider theo (order, seq): ba artifact của request."""
        sections = [self._render(e["text"], assemble_context)
                    for e in _ordered(self._sections)]
        contexts = [e["provider"](assemble_context) for e in _ordered(self._contexts)]
        return {
            "system": "\n\n".join(t for t in sections if t),
            "tools": [s for p in self._tools for s in p(assemble_context)],
            "runtime_context": "\n".join(t for t in contexts if t),
        }

    def _render(self, text, ctx):
        if callable(text):
            text = text(ctx)
        return _VARIABLE.sub(self._value_of, text)

    def _value_of(self, match):
        name = match.group(1)
        value = self._variables.get(name)
        if value is None:  # unknown hoặc unset: refuse-to-ship
            raise ValueError(f"prompt variable '{name}' is unknown or unset")
        return str(value)


def _ordered(entries):
    return sorted(entries, key=lambda e: (e["order"], e["seq"]))


# ------------------------------------------------------------------
# 2. Snapshot dedupe: sự thật nằm trong log, không nằm trong memory
# ------------------------------------------------------------------
def latest_snapshot(log):
    """Snapshot giữ lại = row 'kind: runtime-context' cuối cùng trong log."""
    for event in reversed(log):
        if (event["type"] == "user/message"
                and event["payload"].get("kind") == "runtime-context"):
            return event["payload"]["content"]
    return None


def append_snapshot(log, snapshot):
    """Dedupe: chỉ append khi khác snapshot cuối — không thì không tốn gì."""
    if snapshot and snapshot != latest_snapshot(log):
        log.append({"type": "user/message",
                    "payload": {"content": snapshot, "kind": "runtime-context"}})


# ------------------------------------------------------------------
# 3. SkillRegistry: layered providers; catalog inject, body on-demand
# ------------------------------------------------------------------
class SkillRegistry:
    def __init__(self):
        self._providers = []  # layers theo registration order; layer sau đè layer trước

    def register(self, provider):
        self._providers.append(provider)
        return lambda: self._providers.remove(provider)

    def catalog(self):
        merged = {}
        for provider in self._providers:
            for summary in provider.list():
                merged[summary["name"]] = summary
        return list(merged.values())

    def get(self, name):
        for provider in reversed(self._providers):
            body = provider.get(name)
            if body is not None:
                return body
        return None

    def catalog_text(self):
        summaries = self.catalog()
        if not summaries:  # catalog rỗng: không ship gì
            return ""
        lines = [f"- {s['name']}: {s['description']}" for s in summaries]
        return "skills, load with the skill tool before use:\n" + "\n".join(lines)


class MemorySkillProvider:
    """Provider đơn giản nhất: dict name -> {"description", "body"}."""

    def __init__(self, skills):
        self._skills = dict(skills)

    def list(self):
        # summaries only: provider không bao giờ tự ngỏ body
        return [{"name": n, "description": s["description"]}
                for n, s in self._skills.items()]

    def get(self, name):
        skill = self._skills.get(name)
        return skill["body"] if skill else None


# ------------------------------------------------------------------
# 4. Demo: system text đứng yên, snapshot re-emit đúng lúc
# ------------------------------------------------------------------
if __name__ == "__main__":
    log = []
    prompt = SystemPrompt()

    prompt.section("harness:identity", IDENTITY, order=-100)
    prompt.section("persona", "Answer {{user}} briefly.", order=0)
    undo_var = prompt.variable("user", "Ada")  # đăng ký trước khi render

    clock = {"now": "10:00"}
    prompt.context("time", lambda ac: f"time: {clock['now']}", order=0)
    prompt.tools(lambda ac: [{"name": "tick"}])

    first = prompt.assemble({"tools": []})
    append_snapshot(log, first["runtime_context"])
    print("step 1 | system:", repr(first["system"]))
    print("step 1 | tools:", first["tools"])

    clock["now"] = "10:01"  # một tool giữa turn đã đổi trạng thái runtime
    second = prompt.assemble({"tools": []})
    append_snapshot(log, second["runtime_context"])
    print("step 2 | system byte-identical:", first["system"] == second["system"])
    print("step 2 | snapshot rows trong log:", sum(
        1 for e in log if e["payload"].get("kind") == "runtime-context"))

    append_snapshot(log, prompt.assemble({"tools": []})["runtime_context"])
    print("step 3 | clock đứng yên -> log vẫn", len(log), "row")

    # Skills: layer workspace đè layer built-in, body chỉ qua get()
    skills = SkillRegistry()
    skills.register(MemorySkillProvider({
        "greet": {"description": "greet the user", "body": "Say hello."},
        "haiku": {"description": "answer as a haiku", "body": "Answer with one haiku."},
    }))
    undo_workspace = skills.register(MemorySkillProvider({
        "greet": {"description": "greet the user (workspace)", "body": "Proclaim a hello."},
    }))

    print("---")
    print(skills.catalog_text())
    print("body greet (layer workspace thắng):", skills.get("greet"))
    print("body haiku (không ai đè):", skills.get("haiku"))
    print("tên không tồn tại:", skills.get("nope"))
    undo_workspace()  # undo gỡ đúng layer này thôi
    print("sau undo workspace, greet về built-in:", skills.get("greet"))

    # Strict interpolation: gỡ biến là refuse-to-ship, không ship prompt có lỗ
    print("---")
    undo_var()
    try:
        prompt.assemble({})
    except ValueError as exc:
        print("refuse-to-ship:", exc)
```

Kết quả chạy:

```text
step 1 | system: 'You are mini-dsh, a small agent harness.\n\nAnswer Ada briefly.'
step 1 | tools: [{'name': 'tick'}]
step 2 | system byte-identical: True
step 2 | snapshot rows trong log: 2
step 3 | clock đứng yên -> log vẫn 2 row
---
skills, load with the skill tool before use:
- greet: greet the user (workspace)
- haiku: answer as a haiku
body greet (layer workspace thắng): Proclaim a hello.
body haiku (không ai đè): Answer with one haiku.
tên không tồn tại: None
sau undo workspace, greet về built-in: Say hello.
---
refuse-to-ship: prompt variable 'user' is unknown or unset
```

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Prompt cache miss ở mọi step | Timestamp hoặc cwd render trong system text | Đưa state sang context provider — section/context split giữ mọi byte đổi khỏi system text |
| Snapshot re-emit dù không đổi | So sánh với state giữ trong memory | Đạo snapshot từ log (`latest_snapshot`) — dedupe và replay khớp by construction |
| Model nhận chuỗi `{{typo}}` nguyên văn | Interpolation lỏng | Strict interpolation raise; log cho thấy step dừng trước `request/header` |
| Catalog vẫn advertise skill đã gỡ | Cache kết quả render catalog | Re-resolve mỗi assembly; dedupe giữ quiet steps miễn phí |
| Unknown skill làm crash loop | Raise thoát khỏi tool pipeline | Raise trong body → pipeline → `is_error` result; turn tiếp tục |
| Cùng đăng ký nhưng render khác nhau mỗi run | Order theo dict hoặc thread timing | Một numeric order, tiebreak registration order |

## Failure modes — những thất bại thiết kế lặp lại

- **Đồng hồ trong system text phá cache mỗi step.** Providers cache trên stable prompt prefix và system text đứng đầu nó — một timestamp regenerate mỗi step là không request nào dùng lại prefix. Section/context split giữ mọi byte đổi ra khỏi system text by construction.
- **Text ra ngoài pipeline biến mất khỏi record.** State patch vào request không có log row là replay không thể xây lại những gì model thấy. Snapshot là `user/message` row; thậm chí system text cũng ghi trên `request/header` — log giữ trọn request record.
- **Re-emit snapshot không đổi làm phình history.** Append mỗi step là thêm một row cho không một bit thông tin mới, và mọi request sau trả giá. Boundary so với row snapshot cuối và chỉ append khi đổi.
- **Snapshot giữ trong memory drift khỏi log.** Sau resume memory rỗng, log không rỗng — step đầu re-emit thứ model đã thấy rồi. Đạo snapshot từ log là dedupe và replay luôn khớp.
- **Bodies trong catalog trả tiền cho mọi thứ luôn.** Inline mọi instruction là mỗi request mang toàn bộ trong khi một turn dùng tối đa một. `list()` chỉ yielding tên và một dòng; `get(name)` là cánh cửa duy nhất body lọt qua.
- **Catalog nằm trong system text làm prefix chạy.** Provider mount giữa phiên sẽ rewrite system text và bust cache. Là context thì một provider đổi chỉ tốn một `user/message` row và prefix giữ nguyên.

> 📍 **Lộ trình xuyên suốt — Mini-dsh:** bài này là bài 7 của 8 trong lộ trình [Xây dựng Agent Harness từ số 0 với Mini-dsh](/lo-trinh/xay-dung-agent-harness). Section 08 + 09 của repo gốc là nguồn; bài 8 đóng lộ trình với capability seams, jobs, subagent và composition.

## Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: thêm context provider `cwd` (dùng `os.getcwd()`) vào demo, rồi `os.chdir()` giữa hai step. Xác nhận system text byte-identical và cwd re-emit đúng một row — rồi đổi lại thư mục cũ, xác nhận nó re-emit lần thứ hai.

**Mức 2 — Tự sửa**: implement template có default: `{{name|fallback}}` — fallback dùng khi biến unset, nhưng vẫn raise cho tên hoàn toàn lạ. Trả lời bằng test: default có làm prefix cache bớt dự đoán được không? (Gợi ý: biến unset ở step 1 mà set ở step 2 vẫn đổi system text.)

**Mức 3 — Mở rộng**: viết `FileSystemSkillProvider` đọc thư mục skill — mỗi skill một file, dòng đầu là description, phần còn lại là body. `list()` chỉ đọc dòng đầu của mỗi file, `get(name)` mới đọc cả file. Đây chính là cách `FileSystemSkillProvider` của dsh giữ token economy tới tận I/O boundary.

## Tài liệu gốc

Bài này dựng lại từ hai section của tutorial rebuild DeepSeek Harness:

- [hardness1020/learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness) — full rebuild Mini-dsh bằng Python stdlib; nguồn của bài này là `sections/08-system-prompt` và `sections/09-skills`.
- [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) — dsh thật; registry nằm ở `packages/core/system-prompt` và `packages/skill`.

Đọc tiếp trong lộ trình:

- [Scheduler và steering inbox](/bai-viet/scheduler-va-steering-inbox) — bài trước: mọi thứ vào phiên qua boundary; catalog và snapshot cũng đi qua cùng cánh cửa đó.
- [Capabilities, subagent và composition](/bai-viet/capabilities-subagents-composition) — bài kế: ba seam cuối và cách ghép cả harness thành data.
- [Lộ trình Xây dựng Agent Harness từ số 0 với Mini-dsh](/lo-trinh/xay-dung-agent-harness) — toàn bộ lộ trình 8 bài.

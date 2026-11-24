---
title: "Capabilities, subagent và composition: ghép Mini-dsh thành hệ thống hoàn chỉnh"
description: "Ba seam cuối của Mini-dsh: capability tách Definition/Provider/Consumer cho fs/shell/sandbox/llm, jobs fence quyền hủy công việc nền, subagent đi qua provider interface thay vì kế thừa Agent, và composition biến cả harness thành data — patch layer, replace whole config, không deep-merge."
topic: "harness-engineer"
date: "2026-11-22"
cover: "/images/covers/posts/capabilities-subagents-composition.jpg"
featured: false
views: 90
faq:
  - q: "Khi nào một capability đáng trả giá tách ba lớp?"
    a: "Khi có code không được biết machine nào trả lời: một consumer hướng model cần schema ổn định qua backend swap, hoặc một backend thứ hai đang chờ lên ngôi. Nếu chỉ có một provider và một consumer và không ai swap, để nguyên một package — tách sớm là dead weight; llm là ngoại lệ đứng sẵn vì consumer của nó chính là agent loop."
  - q: "Subagent background và shell_job khác nhau thế nào?"
    a: "Ở tầng protocol: không khác. Cả hai là producer trả cùng protocol triple (cancel, done, read_output) cho cùng JobRegistry — một cái kind 'bash', một cái kind 'subagent'. job_output, job_kill, job_list được viết một lần và phục vụ cả hai producer mà không thêm dòng code nào."
  - q: "Tại sao patch replace cả config thay vì deep-merge?"
    a: "Merge làm config hiệu dụng trở thành kết quả gộp của mọi layer từng chạm row — debug một key sai phải replay cả stack. Replace giữ chân lý của mỗi row ở đúng một nơi: layer cuối cùng chạm nó chứa config hoàn chỉnh. Chi phí rơi vào bundle author phải restate row, và đó là lựa chọn chủ ý."
  - q: "Mini-dsh này có thay được dsh thật?"
    a: "Không, và không phải mục đích. Mini-dsh giữ đúng shape của từng seam và từng protocol để học cơ chế bằng Python stdlib; sandbox thật (bwrap/landlock/seatbelt), continuable subagent, HMR và bundle 78 row của dsh nằm ngoài Ceiling của tutorial và được link về repo gốc để đọc tiếp."
---

Chín bài trước đã dựng Mini-dsh từ một kernel rỗng tới một agent có inbox, có system prompt động, có skill catalog ([bài trước](/bai-viet/system-prompt-va-skills)). Nhưng đến đây harness vẫn chưa chạm vào thế giới ngoài log của chính nó: không đọc được file, không chạy được lệnh, không trao được công việc chậm cho ai, không trao được nhiệm vụ lớn cho context window nào khác. Và thứ quyết định tất cả những mảnh đó được mount vào sản phẩm nào vẫn là một hàm Python ai đó sửa tay.

Bài này đi qua bốn design question của sections 10–13. Mỗi câu hỏi đều có một câu trả lời phá trực giác: tách seam không phải vì đẹp, background không phải chỉ là thread, delegation không cần class, và patch không merge. Cuối bài, cả Mini-dsh đóng lại thành một hình và một danh sách 16 row data.

## Capability seams: một capability, ba vai trò

> **Định nghĩa.** Một capability là bất cứ thứ harness làm với thế giới ngoài log — đọc file, chạy lệnh, giới hạn quyền, gọi model.

Capability đầu tiên phải để đâu? Đáp án trực tiếp nhất: trong tool body. Nhưng chọn đó là ghép ba quyết định vào một hàm: model nhìn thấy gì (schema), contract là gì (đọc file trả về text), machine nào làm (disk thật, memory, host khóa). Offline check cần file trong memory; laptop cần disk thật; host khóa cần cả hai trừ đi. Phục vụ cả ba từ một tool body là viết body đó ba lần — và schema mà model lập kế hoạch theo đổi mỗi lần sửa.

Câu hỏi ngược lại cũng thật: tách mọi capability thành interface + backend package + tool package ngay ngày một là tích lũy abstraction chưa từng có implementation thứ hai.

> **Khi nào một capability đáng trả giá tách ba lớp?** Khi có code không được biết machine nào trả lời: một consumer hướng model cần giữ schema ổn định qua backend swap, hoặc một backend thứ hai đang chờ lên ngôi. Không có ai trong hai đằng ấy thì giữ một package — tách sớm là dead weight, không phải kỹ thuật tốt.

Ba vai trò, mỗi vai một nhiệm vụ:

- **Definition** — một ABC, một ctx key, và vocabulary của seam. Nó sở hữu contract và không gì khác; một Definition không ship code nào làm việc cả.
- **Provider** — plugin mount một implementation cụ thể dưới key. Kernel đã làm phần kế toán: `provide()` trả undo và refuse duplicate key, nên exclusive seam fail loud ngay tại mount. Bookkeeping này là của bài [Kernel và plugin: thiết kế harness](/bai-viet/kernel-plugin-thiet-ke-harness).
- **Consumer** — code resolve key qua `ctx.get()` tại execute time và chỉ nói verb của ABC — thường là tool hướng model. Không tool nào import provider. Kỷ luật import đó chính là seam.

Bốn seam của Mini-dsh: **fs** (read, write), **shell** (run), **sandbox** (confine), **llm**. Hai seam bend hình dạng, và mỗi bend là một design question được trả lời theo một hướng khác.

**Sandbox bend — fence, không phải tool.** Sandbox có provider nhưng không có tool. Một verb duy nhất, fail closed:

```python
def confine(self, argv, policy):
    if policy not in self._policies:  # fail closed: không bao giờ chạy unfenced
        raise ValueError(f"unknown sandbox policy '{policy}'")
    return ["mini-sandbox", "--policy", policy, "--", *argv]
```

Không ai offer `confine` cho model. Consumer của sandbox là provider của seam khác — fence bọc công việc model đã xin qua schema khác, dưới schema, nơi không ai có thể xin nó đừng bọc:

```python
class SandboxedShellExecutor(ShellExecutor):
    """Provider dựng trên seam khác: mọi run đi qua fence."""

    def run(self, argv):
        return self._inner.run(self._sandbox.confine(argv, self._policy))
```

**llm bend — Definition và Consumer gộp một.** Consumer của llm chính là agent loop — tham số `model` mà mọi Agent nhận từ section 04. Một Consumer home riêng sẽ vẽ ranh giới không swap nào đi qua. Model seam đã là contract: một plain callable stream chunks rồi một Message cuối, không cần ABC. Điều còn thiếu là tính plural — registry các adapter theo tên, resolved per call:

```python
def model(self, name):
    """Model seam gắn tên adapter, resolved per call."""
    def seam(messages, tools=(), system=""):
        adapter = self._adapters.get(name)
        if adapter is None:
            raise LookupError(f"no llm adapter registered under '{name}'")
        return adapter(messages, tools, system)
    return seam
```

Bằng chứng của seam nằm ở log: đổi backend giữa hai turn, mọi `request/header` row byte-identical, chỉ `tool/result` row cho biết máy nào đã trả lời.

## Hai lớp hay ba lớp?

| Tiêu chí | 2 lớp — viết thẳng vào tool body | 3 lớp — Definition / Provider / Consumer |
| --- | --- | --- |
| Ai biết machine nào chạy | Tool body — contract và machine dính một mảnh | Consumer không biết, chỉ nói verb của ABC |
| Đổi backend | Sửa tool body — schema model nhìn thấy đổi theo | Đổi provider mount, request byte-identical |
| Nhiều môi trường (offline, laptop, host khóa) | Viết body cho từng môi trường | Một consumer, mount provider theo môi trường |
| Provider thứ hai chưa tồn tại | Không phí gì | Dead weight — tách sớm là tích lũy abstraction |
| Consumer không phải tool (sandbox) | Không có chỗ để bọc fence | Provider của seam khác consume fence, dưới schema |
| Consumer là chính loop (llm) | Ranh giới không swap nào đi qua | Gộp: một service, adapter là callable thuần |

Quy tắc của dsh thật ghi rõ trong architecture note: capability không tách phòng ngừa; một provider + một consumer ở lại một package cho tới khi backend thứ hai xuất hiện. `dsh-llm` là ngoại lệ đứng sẵn vì consumer của nó là loop.

## Jobs: công việc nền thuộc về ai

Scheduler contract từ section 06 nghiêm ngặt: started work never abandoned, every call answers before the step closes. Hỏi shell seam chạy lệnh chậm là block cả turn — model, inbox và user cùng chờ một lệnh echo.

Workaround quen thuộc: tool body spawn một thread rồi trả về. Backgrounding dễ. Nhưng work đó thuộc về không ai: abort signal của turn chỉ vào call đã return; output của thread không có địa chỉ; session nào đoán được id đều đọc được, được kill được, được chờ được.

> **Ai sở hữu cancellation sau khi job ID được publish?** Registry — fenced cho owner, và handoff phải trọn vẹn. Tại thời điểm `start()` trả về id, protocol triple `(cancel, done, read_output)` chuyển tay sang JobRegistry; abort signal của turn sản xuất từ đó không còn chạm được job. Cửa kill duy nhất còn lại là `job_kill`, và mọi accessor kiểm tra fence trước.

Handoff gồm sáu điều:

1. **Publish id ngay** — `start()` trả id trong khi work chạy trên thread riêng; producing call trả lời bằng result bình thường không mang gì ngoài id.
2. **Nhận trọn protocol** — producer `run()` trả `(cancel, done, read_output)`; từ đó registry sở hữu ids, snapshots, settlement, delivery.
3. **Fence mọi accessor** — read, kill, list chỉ trả lời session sở hữu job; caller identity baked tại mount, ambient, không bao giờ là model argument.
4. **Settle first-wins, đúng một lần** — `completed`, `failed` hoặc `killed`, cái nào tới trước, mãi mãi.
5. **Delivery qua inbox** — `wakeup`: owner idle → `followup()` mở turn riêng; owner busy → `inject()` park tới step boundary (hai preset của bài [scheduler và inbox](/bai-viet/scheduler-va-steering-inbox)). `quiet`: chờ được poll. Background work không bao giờ tự append log row.
6. **Controls viết một lần** — `job_output`, `job_kill`, `job_list` phục vụ mọi producer.

Hai mảnh code là trái tim của thiết kế:

```python
def _fenced(self, job_id, caller_id):
    with self._lock:
        job = self._jobs.get(job_id)
    if job is None or job.owner.id != caller_id:
        # Một message cho id lạ và id giả mạo: người lạ không học được gì,
        # kể cả việc id đó có tồn tại.
        raise PermissionError(f"no job '{job_id}' owned by this session")
    return job

def _settle(self, job, status, detail=None):
    with self._lock:
        if job.outcome is not None:
            return  # race đã chốt; tiếng nói sau không đổi kết quả
        job.outcome = {"status": status, "detail": detail}
    self._notify(job)  # ngoài lock: delivery có thể lái cả một turn
```

`caller_id` không bao giờ đến từ model: `job_tools(owner)` bake identity vào khi mount tools vào scope của owner. Agent B gõ id gì thì tool của B vẫn tự xưng tên B trước registry — job của A vô hình. Hủy turn sản xuất cũng không chạm job: signal của turn kết thúc tại scheduler; call mà abort bắt trước dispatch vẫn trả lời bằng synthetic error result.

## Subagent: provider interface thay vì kế thừa

Delegation trao task cho child có session, tool scope và context window riêng, thu về một câu trả lời. Gửi agent đi errand — summarize package, chase failing test — và toàn bộ transcript của errand không đè lên context parent.

Điều đầu tiên hiện ra trong đầu là subclass: `class Subagent(Agent)` nghe như một lợi thế sẵn có. Nhưng cái trả lời delegation không phải lúc nào cũng là một agent trong process này. Dsh thật ship provider fork process, provider lái sản phẩm khác qua wire protocol, provider bọc cả một harness khác — base class là bắt mọi provider fake ruột của Agent chỉ để mount.

> **Tại sao subagent dùng provider interface thay vì kế thừa Agent?** Vì parent-side contract chỉ là bốn verb, còn class là commitment với mọi thứ khác. Registry giữ tên, không giữ class: một provider là callable nhận resolved request và trả một run — registry không nhìn qua nó.

Run là toàn bộ parent-side contract, và nó chủ đích là protocol triple của section 11:

```python
@dataclass(frozen=True)
class SubagentRun:
    cancel: callable        # yêu cầu child dừng; cooperative, best effort
    done: callable          # block tới khi kết thúc: ("completed", None) | ("failed", detail)
    read_output: callable   # câu trả lời của child tính đến hiện tại
```

Đó chính là payoff: foreground — tool call chờ `done()` và trả câu trả lời của child; background — trao cùng triple cho jobs registry unchanged, subagent thành producer thứ hai, peer với shell, và fence, settlement, controls của section 11 phục vụ nó với không một dòng code mới. Parent log chỉ mang hai row của errand — một `tool/call` và một `tool/result`; errand là một session hoàn chỉnh ở nơi khác, đúng như mọi thứ trong [session log](/bai-viet/session-log-va-compaction) vốn thuộc về session của nó.

## Inheritance vs provider interface

| Tiêu chí | Kế thừa Agent | Provider interface |
| --- | --- | --- |
| Provider bắt buộc là gì | Một Agent trong process này | Bất kỳ callable nào trả SubagentRun |
| Provider ngoài process | Phải fake ruột của Agent để mount | Tự nhiên — triple là đủ |
| Contract | Mọi thứ class bộc lộ | Bốn verb: resolve, cancel, done, read_output |
| Thêm provider mới (cache, subprocess, sản phẩm khác) | Fork logic hoặc thêm subclass | Register thêm một tên |
| Chạy background | Phải tự bọc vào jobs | Triple trao thẳng jobs — producer peer với shell |
| Child session | Dễ bị viết lẫn vào parent log | Hai log, một câu trả lời đi qua |

## Composition: harness là data

Sau mười hai sections, thứ quyết định sản phẩm mount gì vẫn là một hàm Python ai đó sửa. Products không ship được kiểu đó: web build và headless build là cùng những plugin trong list khác nhau; user muốn đổi một row của build người khác mà không fork. Mô tả harness phải thành data: một entry list phẳng, dựng bằng patch layers, mỗi layer thuộc về người nói hộ nó — base vendor trước, user sau.

> **Tại sao patch replace toàn bộ config thay vì deep-merge?** Vì merge làm config hiệu dụng trở thành emergent: muốn biết một row nghĩa là gì phải replay mọi layer từng chạm nó, và default của base rò rỉ vào mode không hề xin. Replace giữ chân lý của mỗi row ở đúng một nơi — layer cuối cùng chạm nó chứa config hoàn chỉnh. Chi phí rơi vào bundle author, và đó là chủ ý: row có giá trị khác nhau theo mode không được nằm ở base, mỗi mode restate config trọn vẹn.

Ba verb, tất cả keyed theo id: id lạ → insert; id đã có → replace whole config; `disabled` → remove. Nhánh replace là một assignment:

```python
row = next((r for r in entries if r["id"] == patch["id"]), None)
if patch.get("disabled"):
    if row is not None:
        entries.remove(row)
elif row is None:
    entries.append({"id": patch["id"], "name": patch["name"],
                    "config": dict(patch.get("config", {}))})
else:
    row["config"] = dict(patch.get("config", {}))  # whole, never a merge
```

Không có walk key-by-key để viết, vì một patch không bao giờ gặp config cũ: layer sau chạm row nói tất cả.

Một nửa khác là loader. Row là data nên không thể tự nói "load mình sau row sessions"; thay vào đó mỗi factory khai báo services nó cần, loader mount thứ gì vừa mount được cho tới khi list settles, và audit refuse boot khi row còn chờ — nêu tên từng row và service nó chờ. Vị trí row vì thế không mang ngữ nghĩa load: MINI_BASE đảo ngược thứ tự vẫn boot y hệt.

`MINI_BASE` — toàn bộ sections 00–12 — là 16 row data. Model row nằm ở base vì mọi mode đều cần một model, nhưng giá trị khác nhau theo mode: base ship stand-in không nói gì, và mọi profile restate whole config rồi insert adapter row riêng bên cạnh.

## Kiến trúc hoàn chỉnh: cả Mini-dsh trong một hình

```text
MINI_BASE (16 row data) + profile patch + user patch
        │ apply_layers() → 1 entry list phẳng → mount_entries() (availability-driven)
        ▼
┌────────────────────────────── kernel ctx ───────────────────────────────┐
│ sessions  tools  system_prompt  skills  fs  sandbox  shell  llm         │
│ agents  subagents  jobs  owner(a1)                                      │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ▼
 1  inbox claim tại boundary ─► 2 _step() assemble: system + tools + snapshot
                                ▼
 3  scheduler dispatch call (abort signal riêng cho từng call)
                                ▼
 4  pipeline: permission + tool scope
                                ▼
 5  tools: read/write/shell (qua seam) · skill (get body) · shell_job · subagent
                                ▼
 6  JobRegistry: publish id → owner fence → settle first-wins
                                ▼
 7  notice: followup() (idle) / inject() (busy) ─► quay về inbox, mở turn mới
```

Đọc hình từ trên xuống: sản phẩm là một diff over nothing — 16 row dựng lên từ một list rỗng, mount theo service availability, và một turn đi qua đúng chuỗi cửa đã học từ section 04: claim tại boundary, assemble, dispatch có abort signal, pipeline permission, tools, rồi công việc nền quay về inbox. Disable một row — skills chẳng hạn — và cùng harness trả lời cùng script bằng `unknown tool 'skill'`: một subsystem bị gỡ bằng data, không sửa một dòng code nào.

> 📍 **Lộ trình xuyên suốt — Mini-dsh:** bài cuối của lộ trình [Xây dựng Agent Harness từ số 0 với Mini-dsh](/lo-trinh/xay-dung-agent-harness). Section 10–13 của repo gốc là nguồn; bài tổng hợp trong lộ trình gắn toàn bộ kiến trúc lại thành hình này — mỗi bài trước là một tầng của nó.

## Code thực hành: bốn seam chạy được

Môi trường: chỉ stdlib (`abc`, `dataclasses`, `threading`), không API key. Code rút gọn bốn mảnh: capability seams, jobs fence, subagent run, composition patch. Lưu thành `seams_jobs_composition_mini.py` rồi `python3 seams_jobs_composition_mini.py`.

```python
# seams_jobs_composition_mini.py — rút gọn từ sections 10 + 11 + 12 + 13
# Chỉ stdlib, không API key. Chạy: python3 seams_jobs_composition_mini.py

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass


# ------------------------------------------------------------------
# 1. Capability seams: Definition / Provider / Consumer
# ------------------------------------------------------------------
class FileSystem(ABC):
    """Definition của fs seam, ctx key "fs". Exclusive: một provider."""

    @abstractmethod
    def read(self, path): ...

    @abstractmethod
    def write(self, path, text): ...


class MemoryFileSystem(FileSystem):
    def __init__(self, files=None):
        self._files = dict(files or {})

    def read(self, path):
        if path not in self._files:
            raise FileNotFoundError(path)
        return self._files[path]

    def write(self, path, text):
        self._files[path] = str(text)


class ShellExecutor(ABC):
    """Definition của shell seam: một verb, một ctx key "shell"."""

    @abstractmethod
    def run(self, argv):
        """Chạy một argv list; output của lệnh dưới dạng text."""


class EchoShellExecutor(ShellExecutor):
    """Provider stand-in: không chạy gì, trả lời bằng chính argv được xin."""

    def run(self, argv):
        return " ".join(argv)


class SandboxProvider(ABC):
    """Definition của sandbox seam: một verb, KHÔNG tool."""

    @abstractmethod
    def confine(self, argv, policy):
        """argv mới, fenced theo policy. Fail closed."""


class ArgvRewriteSandbox(SandboxProvider):
    """Provider stub: rewrite argv, enforce không gì — nhưng fail closed."""

    def __init__(self, policies):
        self._policies = frozenset(policies)

    def confine(self, argv, policy):
        if policy not in self._policies:  # fail closed: không chạy unfenced
            raise ValueError(f"unknown sandbox policy '{policy}'")
        return ["mini-sandbox", "--policy", policy, "--", *argv]


class SandboxedShellExecutor(ShellExecutor):
    """Provider dựng trên seam khác: consumer của sandbox là provider shell."""

    def __init__(self, inner, sandbox, policy):
        self._inner, self._sandbox, self._policy = inner, sandbox, policy

    def run(self, argv):
        return self._inner.run(self._sandbox.confine(argv, self._policy))


class LlmRuntime:
    """llm seam: Definition và Consumer gộp một; adapter là callable thuần."""

    def __init__(self):
        self._adapters = {}

    def register(self, name, adapter):
        if name in self._adapters:
            raise ValueError(f"llm adapter '{name}' already registered")
        self._adapters[name] = adapter
        return lambda: self._adapters.pop(name)

    def model(self, name):
        """Model seam gắn tên adapter, resolved per call."""
        def seam(messages, tools=(), system=""):
            adapter = self._adapters.get(name)
            if adapter is None:
                raise LookupError(f"no llm adapter registered under '{name}'")
            return adapter(messages, tools, system)
        return seam


def read_tool_body(ctx, path):
    """Consumer: resolve seam tại execute time, chỉ nói verb của ABC."""
    fs = ctx.get("fs")
    if fs is None:
        raise RuntimeError("no provider mounted under 'fs'")
    return fs.read(path)


# ------------------------------------------------------------------
# 2. Jobs: handoff ownership, owner fence, first-wins settlement
# ------------------------------------------------------------------
@dataclass(frozen=True)
class JobOwner:
    id: str


@dataclass
class Job:
    id: str
    kind: str
    owner: JobOwner
    cancel: callable
    read_output: callable
    outcome: dict = None


class JobRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs = {}
        self._count = 0

    def start(self, kind, owner, run, delivery="quiet"):
        """run() trả protocol triple (cancel, done, read_output); registry nhận id.

        delivery "wakeup" gửi notice qua inbox của owner — followup() nếu idle,
        inject() nếu busy (section 07); "quiet" chờ được poll bằng job_output.
        """
        if delivery not in ("quiet", "wakeup"):
            raise ValueError(f"unknown delivery '{delivery}'")
        cancel, done, read_output = run()
        with self._lock:
            self._count += 1
            job = Job(f"job-{self._count}", kind, owner, cancel, read_output)
            self._jobs[job.id] = job
        threading.Thread(target=lambda: self._settle(job, *done()),
                         daemon=True).start()
        return job.id

    def _fenced(self, job_id, caller_id):
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None or job.owner.id != caller_id:
            # Một message cho id lạ và id giả: người lạ không học được gì.
            raise PermissionError(f"no job '{job_id}' owned by this session")
        return job

    def status(self, job_id, caller_id):
        job = self._fenced(job_id, caller_id)
        return job.outcome["status"] if job.outcome else "running"

    def kill(self, job_id, caller_id):
        job = self._fenced(job_id, caller_id)
        job.cancel()
        self._settle(job, "killed")
        return self.status(job_id, caller_id)

    def _settle(self, job, status, detail=None):
        with self._lock:
            if job.outcome is not None:
                return  # race đã chốt; tiếng nói sau không đổi kết quả
            job.outcome = {"status": status, "detail": detail}


# ------------------------------------------------------------------
# 3. Subagent: provider interface, run là toàn bộ contract
# ------------------------------------------------------------------
@dataclass(frozen=True)
class SubagentRun:
    cancel: callable
    done: callable
    read_output: callable


class SubagentRuntime:
    def __init__(self):
        self._providers = {}
        self._count = 0

    def register(self, name, provider):
        if name in self._providers:
            raise ValueError(f"subagent provider '{name}' already registered")
        self._providers[name] = provider
        return lambda: self._providers.pop(name)

    def start(self, name, task):
        provider = self._providers.get(name)
        if provider is None:
            raise LookupError(f"no subagent provider registered under '{name}'")
        self._count += 1
        return provider({"id": f"sub-{self._count}", "task": task})


def cached_provider(answer):
    """Một provider không phải agent nào cả — và không ai phân biệt được."""
    def start(request):
        return SubagentRun(cancel=lambda: None,
                           done=lambda: ("completed", None),
                           read_output=lambda: answer)
    return start


# ------------------------------------------------------------------
# 4. Composition: patch layers; replace whole config, never a merge
# ------------------------------------------------------------------
def apply_layers(layers):
    entries = []
    for layer in layers:
        for patch in layer:
            row = next((r for r in entries if r["id"] == patch["id"]), None)
            if patch.get("disabled"):
                if row is not None:
                    entries.remove(row)
            elif row is None:
                entries.append({"id": patch["id"], "name": patch["name"],
                                "config": dict(patch.get("config", {}))})
            else:
                row["config"] = dict(patch.get("config", {}))  # whole, never a merge
    return entries


# ------------------------------------------------------------------
# 5. Demo
# ------------------------------------------------------------------
if __name__ == "__main__":
    # fs seam: swap backend, consumer và contract không đổi
    ctx = {"fs": MemoryFileSystem({"notes.txt": "alpha"})}
    print("read qua seam:", read_tool_body(ctx, "notes.txt"))
    ctx["fs"] = MemoryFileSystem({"notes.txt": "beta"})  # swap backend
    print("sau swap, cùng body, máy khác:", read_tool_body(ctx, "notes.txt"))

    # sandbox fence qua shell provider; policy lạ fail closed
    shell = SandboxedShellExecutor(EchoShellExecutor(),
                                   ArgvRewriteSandbox(["read-only"]), "read-only")
    print("fenced run:", shell.run(["echo", "hi"]))
    try:
        SandboxedShellExecutor(EchoShellExecutor(),
                               ArgvRewriteSandbox(["read-only"]),
                               "network").run(["echo", "hi"])
    except ValueError as exc:
        print("fail closed:", exc)

    # llm: adapters plural, late bound
    llm = LlmRuntime()
    undo = llm.register("main", lambda m, t=(), s="": iter(["from the first backend"]))
    undo()  # gỡ adapter: swap tới nơi mà không đụng agent
    llm.register("main", lambda m, t=(), s="": iter(["from the second backend"]))
    print("llm main trả:", next(llm.model("main")([])))

    # jobs: id sống qua turn; fence chặn session lạ; kill settle một lần
    jobs = JobRegistry()
    owner = JobOwner("a1")
    stop = threading.Event()      # cancel: work tự kiểm tra cờ này
    finished = threading.Event()  # done-gate: chưa set, work chưa kết thúc

    def run():
        def done():
            finished.wait()
            return ("completed", None)
        return (stop.set, done, lambda: "echo hi")

    job_id = jobs.start("shell", owner, run)
    print("job published:", job_id)
    try:
        jobs.status(job_id, "b1")  # session B soi job của A
    except PermissionError as exc:
        print("fence:", exc)
    print("kill chốt:", jobs.kill(job_id, owner.id))
    print("status sau kill:", jobs.status(job_id, owner.id))

    # subagent: provider không phải agent vẫn mount — registry không nhìn qua nó
    subs = SubagentRuntime()
    subs.register("cached", cached_provider("the log has 12 rows"))
    reply = subs.start("cached", "summarize the log")
    print("subagent reply:", reply.read_output())

    # composition: replace whole config, disable, insert — không merge
    base = [
        {"id": "model", "name": "scripted-llm",
         "config": {"name": "scripted", "responses": []}},
        {"id": "agent", "name": "agent",
         "config": {"agent": "a1", "session": "s1",
                    "model": "scripted", "prompt": "shared"}},
        {"id": "skills", "name": "skills"},
    ]
    profile = [
        # replace whole: chỉ config mới đi vào — key "prompt" của base không sống sót
        {"id": "agent", "config": {"agent": "a1", "session": "s1", "model": "live"}},
        # đổi plugin thì disable row cũ + insert row mới: patch không đổi name
        {"id": "model", "disabled": True},
        {"id": "model-live", "name": "live-llm", "config": {"name": "live"}},
        {"id": "skills", "disabled": True},          # remove subsystem bằng data
        {"id": "worker", "name": "subagent-tools"},  # insert
    ]
    print("entries sau patch:", apply_layers([base, profile]))
```

Kết quả chạy:

```text
read qua seam: alpha
sau swap, cùng body, máy khác: beta
fenced run: mini-sandbox --policy read-only -- echo hi
fail closed: unknown sandbox policy 'network'
llm main trả: from the second backend
job published: job-1
fence: no job 'job-1' owned by this session
kill chốt: killed
status sau kill: killed
subagent reply: the log has 12 rows
entries sau patch: [{'id': 'agent', 'name': 'agent', 'config': {'agent': 'a1', 'session': 's1', 'model': 'live'}}, {'id': 'model-live', 'name': 'live-llm', 'config': {'name': 'live'}}, {'id': 'worker', 'name': 'subagent-tools', 'config': {}}]
```

Chú ý dòng cuối: config của row `agent` bị thay toàn bộ — key `prompt` của base không sống sót qua patch, đó là replace whole config, không merge. Còn đổi plugin model thì disable row cũ rồi insert row mới, vì patch trên id đã có chỉ thay `config`, không đổi `name` (plugin factory).

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Đổi backend mà schema model đổi theo | Tool body import hoặc tự tạo provider | Body resolve ctx key per call, chỉ nói verb ABC — kỷ luật import là seam |
| Hai provider mount cùng key êm ru | Không refuse duplicate | Exclusive key refuse tại mount qua kernel `provide()` — fail loud trước khi ai gọi nhầm |
| Sandbox policy lạ vẫn chạy | `confine()` trả argv nguyên vẹn | Fail closed: raise → pipeline → `is_error` result; không gì chạy unfenced |
| `job_kill` báo killed mà work vẫn chạy | Triple thiếu cancel thật | `cancel` phải gắn với máy thật (process group, cờ mà work kiểm tra); settlement first-wins chốt kết quả |
| Job output đọc được từ session khác | Registry trả lời mọi người hỏi | Fence mọi accessor; identity baked tại mount, không bao giờ là model argument |
| Background âm thầm chạy foreground | Không có jobs registry mà fallback | Optional lookup `ctx.get("jobs")`; không registry thì refuse loudly |
| Config row "dính" key của base | Patch dạng deep-merge | Replace whole; row có giá trị khác theo mode không nằm ở base |

## Failure modes — những thất bại thiết kế lặp lại

- **Tool import provider là bypass interface.** Body tự mở disk hay tự tạo backend là đổi máy thành sửa tool, và mỗi môi trường fork schema. Kỷ luật import — resolve key per call, chỉ nói verb ABC — chính là seam.
- **Provider thứ hai mount êm là config bug.** Hai shell cùng mount thì ai chạy lệnh phụ thuộc mount order không ai đọc. Exclusive key refuse ở mount time, trước khi bất kỳ call nào chọn sai.
- **Sandbox fail open còn tệ hơn không có.** Trả argv nguyên vẹn cho policy không biết là mọi misconfig chạy unfenced, invisibly. `confine()` raise, pipeline trả `is_error`, không gì chạy.
- **Fence model-facing sandbox tool là fence sai cửa.** Offer `confine` trong schema là fencing thành lựa chọn của model. Fence bọc công việc đã được authorize, dưới schema.
- **Thread nền không registry là orphaned work.** Output không có địa chỉ, kill switch nối vào hư không; lệnh chậm kế tiếp background cùng kiểu và không ai list được cái gì đang chạy. `start()` nhỏ, nhưng id, fence và settlement là khoảng cách giữa background work và một leak.
- **Settlement lần hai viết lại history.** Late completion ghi đè `killed` là owner đọc kết quả sai sau đó. First-wins trong registry chốt race một lần, cho mọi consumer.
- **Notice append giữa step làm transcript mâu thuẫn.** Thread settlement không sở hữu boundary; notice phải đi qua inbox và vào ở boundary kế tiếp như mọi thứ khác.
- **Subclass làm contract là cap cho provider list.** Fork, remote, other-product provider hoặc không tồn tại hoặc phải fake Agent. Bốn verb hỏi đúng những gì parent làm: start, stop, wait, read.
- **Child dùng chung session parent là không phải delegation.** Transcript errand đè lên context parent — đúng cái chi phí delegation tồn tại để tránh. Hai log, một câu trả lời đi qua.
- **Deep merge làm mọi layer thành nghi phạm.** Debug một key sai là replay cả stack. Replace giữ câu trả lời ở một row trong một layer: patch cuối là toàn bộ sự thật.

## Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: viết một `SubprocessShellExecutor(ShellExecutor)` chạy `sh -c` qua `subprocess.run` (stdlib) và mount nó thay `EchoShellExecutor` trong demo. Xác nhận tool concept không đổi — chỉ máy thay đổi, schema và consumer giữ nguyên.

**Mức 2 — Tự sửa**: mount `JobRegistry` từ demo và viết background mode cho delegation: nếu jobs registry có mặt, trao triple vào `jobs.start("subagent", ...)`; nếu không có, refuse loudly. Xác nhận `job_list` liệt kê kind `subagent` và `job_kill`/`job_output` phục vụ nó mà không viết thêm controls.

**Mức 3 — Mở rộng**: viết `mount_entries` theo availability-driven (mỗi factory khai báo `requires`) kèm audit refuse boot và nêu tên row đang chờ. Chứng minh MINI_BASE đảo ngược thứ tự vẫn boot y hệt, rồi thêm profile layer của bạn với đủ ba verb: insert một provider row, replace model row whole, disable skills row.

## Tài liệu gốc

Bài này dựng lại từ bốn section cuối của tutorial rebuild DeepSeek Harness:

- [hardness1020/learn-deepseek-harness](https://github.com/hardness1020/learn-deepseek-harness) — full rebuild Mini-dsh bằng Python stdlib; nguồn của bài này là `sections/10-capability-seams`, `sections/11-jobs`, `sections/12-subagent` và `sections/13-composition`.
- [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) — dsh thật (pinned 99f6f02): `packages/fs`, `packages/shell`, `packages/sandbox`, `packages/llm`, `packages/jobs`, `packages/subagent`, và boot plane `packages/boot` + `packages/bundle`.

Trên LearnWithHuy:

- [System prompt động và Skills](/bai-viet/system-prompt-va-skills) — bài trước: catalog và snapshot của bài này đi qua đúng registry đó.
- [Agent harness là gì?](/bai-viet/agent-harness-la-gi) — mở đầu series: harness là gì và vì sao phải tự dựng.
- [12 nguyên tắc agent production](/bai-viet/12-nguyen-ly-agent-production) — các nguyên tắc mà từng seam trong bài này hiện thực hóa.
- [Lộ trình Xây dựng Agent Harness từ số 0 với Mini-dsh](/lo-trinh/xay-dung-agent-harness) — toàn bộ lộ trình 8 bài, kết thúc ở bài tổng hợp này.

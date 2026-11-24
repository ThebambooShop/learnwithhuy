---
title: "12 nguyên lý đưa AI Agent vào production"
description: "Bản dịch + triển khai 12 nguyên lý của 12-Factor Agents — từ natural language to tool calls, own your prompts và context window, đến stateless reducer — kèm evals, guardrails, human-in-the-loop và code thực hành."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-22"
cover: "/images/covers/posts/12-nguyen-ly-agent-production.jpg"
featured: false
views: 300
faq:
  - q: "Có phải áp dụng đủ cả 12 nguyên lý mới được đưa agent vào production?"
    a: "Không. Bốn nguyên lý đầu (natural language to tool calls, own your prompts, own your context window, tools are structured outputs) là tối thiểu để agent chạy ổn. Các nguyên lý còn lại thêm dần theo mức độ rủi ro: agent đụng tiền thì cần Factor 7 (ask_human), chạy nhiều người dùng và nhiều lần thì cần Factor 12 (stateless reducer). Đo bằng evals, không áp máy móc."
  - q: "Stateless reducer khác gì lưu lịch sử hội thoại trong database?"
    a: "Lưu database chỉ là giữ dữ liệu; stateless reducer là cách cấu trúc dữ liệu đó thành danh sách events, và state mới luôn tính được bằng một hàm thuần. Muốn resume agent, bạn chỉ cần load events và chạy lại reducer — không process nào giữ trạng thái trong RAM. Nhờ vậy restart, migrate hay chạy nhiều worker đều không làm mất trạng thái của agent."
  - q: "Eval trace-based khi nào đủ dùng, khi nào cần LLM judge?"
    a: "Trace-based đủ khi bạn chấm được chuỗi step bằng so khớp: agent có gọi đúng tool không, thứ tự step có khớp ground truth không, câu trả lời cuối có chứa thông tin bắt buộc không. Cần LLM judge khi tiêu chí là chất lượng văn phong hoặc phản hồi mở — thứ không so khớp được. Nguyên tắc: dùng trace-based hết mức vì gần như miễn phí và chạy trong CI được; LLM judge chỉ cho phần không chấm quy tắc được."
  - q: "Thinking budget nên đặt thế nào cho agent nhiều bước?"
    a: "Bắt đầu với reasoning effort thấp cho mọi step, chỉ nâng khi thất bại. Với model hỗ trợ tham số reasoning effort, viết cascade retry: chạy level thấp, nếu eval hoặc tool call fail thì chạy lại level cao hơn. Phần lớn step của agent thật chỉ cần level thấp — cách này cắt chi phí và độ trễ rõ rệt mà không ảnh hưởng chất lượng những tác vụ dễ."
---

Sáu bài trước trong lộ trình, bạn đã nắm từng pattern: agent loop, routing, planning, memory, multi-agent, RAG. Bài này là trụ cột vận hành — những nguyên tắc giữ cho agent không sập khi chạy thật. Nó đi cùng bài [Hướng dẫn xây dựng agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te): guide của OpenAI trả lời câu hỏi *thiết kế* — ca sử dụng nào, orchestration mẫu nào; bài này trả lời câu hỏi *production* — những quyết định kiến trúc nào quyết định agent của bạn sống hay chết sau vài tuần chạy.

## 12-Factor Agents: nguyên lý rút từ production thật

[12-Factor Agents](https://github.com/humanlayer/12-factor-agents) của HumanLayer đã vượt 27.000 sao trên GitHub. Cái tên mượn từ *The Twelve-Factor App* — bộ 12 nguyên lý dựng app SaaS bền vững — nhưng nội dung là 12 nguyên lý được rút ra từ agent production thật: agent hoàn tiền, agent support, agent chạy hàng nghìn task mỗi ngày.

> **Agent vào production không cần framework to. Nó cần một vòng lặp bạn kiểm soát được.**

Tài liệu viết cho team không muốn ôm framework nặng: mỗi nguyên lý là một quyết định kiến trúc có thể thử trong 1-2 giờ, không phải migration một tuần. Sau đây là bản dịch + triển khai của cả 12 nguyên lý.

## 12 nguyên lý

### 1. Natural Language to Tool Calls

LLM không chạy logic — nó xuất JSON tool call, code của bạn thực thi tool đó, append kết quả vào context rồi lặp. Agent thực chất chỉ là một vòng lặp `while` + gọi LLM + switch theo tool call. Đây là nguyên lý số 1 vì nó phá vỡ illusion "agent là sản phẩm đặc biệt": chính là code thường. Ví dụ áp dụng: agent đổi tên file chạy trên khoảng 100 dòng Python không framework — cùng kiến trúc với agent loop bạn đã xây ở [bài 1](/bai-viet/kien-truc-ai-agent-cam-nang).

### 2. Own your prompts

Prompt là tài sản quan trọng nhất của agent — đừng delegate việc viết nó cho framework. Khi framework giữ prompt trong template ngầm, một bản update có thể đổi hành vi agent mà bạn không biết. Giữ prompt trong code của bạn, review qua git, eval được như code thật. Ví dụ: system prompt của agent hỗ trợ khách hàng nằm trong một file riêng, mỗi thay đổi đi qua PR kèm eval regression trước khi merge.

### 3. Own your context window

Context quyết định chất lượng agent hơn cả model — nên kiểm soát trực tiếp cái gì được đưa vào và cái gì bị cắt. Framework tự truncate khi context đầy theo cách nó chọn, bạn mất quyền quyết định tin nào quan trọng. Ví dụ: agent xử lý ticket support giữ nguyên ticket gốc, nén chuỗi email dài thành tóm tắt ba câu, đặt history tool call ở cuối context để gần vị trí generation.

### 4. Tools are just structured outputs

Tool call không phải magic — chỉ là JSON có cấu trúc mà model sinh ra theo schema, code parse rồi dispatch. Hiểu thế này, thêm tool mới chỉ là thêm một schema + một handler, không cần học cơ chế riêng của framework nào. Ví dụ: schema `transfer_money(from, to, amount)` kèm handler gọi API ngân hàng — schema là hợp đồng, handler là code Python thường.

### 5. Unify execution state and business state

Đừng giữ hai nguồn sự thật: một cho agent loop (đang ở step nào) và một cho app domain (đơn hàng xử lý tới đâu). Gom vào một representation — state của agent chính là state nghiệp vụ. Ví dụ: state của agent hoàn tiền chính là bản ghi refund trong DB; process chết giữa chừng thì bạn phục hồi đúng chỗ, không lệch giữa "agent nghĩ đã xong" và "hệ thống chưa ghi".

### 6. Launch/Pause/Resume with simple APIs

Agent chạy dài hàng phút tới hàng giờ; người dùng cần pause, server cần restart, approval cần chờ qua đêm. Đó là nghiệp vụ, không phải chi tiết framework — nên có API đơn giản: start, pause, resume. Ví dụ: người quản trị bấm pause trong thread Slack, agent dừng ngay approval gate, resume sáng hôm sau khi được duyệt — không mất gì.

### 7. Contact humans with tool calls

"Hỏi con người" chỉ là một tool call nữa — giống gọi API bên ngoài. Định nghĩa tool `ask_human`, code chờ response, agent nhận câu trả lời như một tool result bình thường. Đây là cách gọn nhất để làm human-in-the-loop mà không cần cơ chế đặc biệt nào. Ví dụ: agent hoàn tiền vượt ngưỡng 5 triệu gọi `ask_human("Duyệt hoàn 7 triệu cho khách X?")`, người quản trị nhận thông báo và trả lời ngay trong UI.

### 8. Own your control flow

While loop, retry, escalation — giữ trong code của bạn, không giao cho abstraction của framework. Khi control flow nằm trong framework, debug hành vi khó như debug hộp đen. Ví dụ: quy tắc "thử tool tối đa 3 lần, sau đó escalate cho con người" viết bằng 10 dòng Python, đọc được trong 10 giây — thay vì tìm trong docs framework cách cấu hình đúng.

### 9. Compact errors into context window

Lỗi là dữ liệu, không phải exception cần nuốt. Nén lỗi ngắn gọn (status code, message một dòng) rồi append vào context để agent tự đọc và tự sửa lần gọi tiếp theo. Ví dụ: API trả 429, context thêm dòng `error: rate limit, retry after 30s` — model hiểu tình trạng và dừng gọi tiếp trong lúc bị rate limit; phần backoff là việc của code. Hai ranh giới cần giữ: không đưa nguyên văn stack trace, credentials hay dữ liệu nhạy cảm vào context — nén thành mã lỗi + message một dòng đã sanitize; lỗi 429 phải được code xử lý theo `Retry-After` và backoff ở tầng ứng dụng, không để model tự quyết định gọi lại trong loop.

### 10. Small, focused agents

Agent hẹp, một việc, ít tool luôn dễ eval, dễ debug, dễ tin hơn agent tổng quát to bự. Agent "làm được mọi thứ" thường làm được mọi thứ theo cách không dự đoán được. Ví dụ: tách agent đọc invoice, agent ghi sổ, agent báo cáo — ba agent nhỏ nối chuỗi, mỗi cái eval độc lập, lỗi dễ khoanh vùng trong một agent.

### 11. Trigger from anywhere

Agent mạnh lên khi có thể chạy từ Slack, email, webhook, cron — không bị nhốt trong một chat UI. Trigger chỉ là cách đưa task đầu vào; phần còn lại của agent không đổi. Ví dụ: cùng một agent tổng hợp báo cáo chạy lúc 8h sáng qua cron, và chạy on-demand qua webhook từ CRM khi đơn hàng bị hủy.

### 12. Make your agent a stateless reducer

Agent là một hàm stateless: events vào → state mới ra, giống reducer trong Redux. Không giữ state trong RAM, không có process "sống" cần bảo vệ; muốn resume thì load events và chạy lại reducer. Đây là nguyên lý nền cho scale: nhiều worker, restart, migrate đều không phá agent. Ví dụ: mỗi tool call và kết quả của nó là một event trong danh sách.

Lưu ý giới hạn: reducer như trình bày là **mô hình khái niệm**, chưa phải bản triển khai event-sourcing hoàn chỉnh. Phát lại event để dựng lại state khác với thực thi lại tool: nếu chạy lại event gây action ngoài đời thật — gửi email, hoàn tiền — phát sinh tác dụng phụ lặp. Tool có side effect cần **idempotency key**: reducer đánh dấu event đã processed, tool kiểm tra trước khi execute.

### Bonus: Factor 13 — Pre-fetch all the context you might need

Mọi context mà agent có khả năng cần thì lấy trước khi vòng lặp bắt đầu, đừng để agent tự mò từng mảnh qua nhiều vòng tool call. Ví dụ: agent xử lý ticket support, trước khi chạy pre-fetch sẵn lịch sử đơn hàng, cấu hình tenant và log gần nhất trong một truy vấn — rẻ hơn nhiều so với 6 vòng tool call chỉ để dọn đủ thông tin.

## Nhóm hóa: 3 tầng dễ nhớ

12 nguyên lý đứng rời dễ quên. Gom thành 3 tầng thì dùng được như checklist:

| Tầng | Nguyên lý | Câu hỏi nó trả lời |
| --- | --- | --- |
| **Tầng lõi loop** | 1, 2, 3, 4, 8 | Agent chạy bằng gì và ai kiểm soát logic? |
| **Tầng vận hành** | 5, 6, 9, 12 | Agent sống sót qua restart, lỗi và scale thế nào? |
| **Tầng con người & kênh** | 7, 10, 11 | Con người tham gia đâu, agent kích hoạt từ đâu, scope ra sao? |

Làm xong tầng lõi là agent chạy được; tầng vận hành là production-ready; tầng con người & kênh là sản phẩm thực sự dùng được. Đây là heuristic, không phải checklist cứng — agent nào "đủ production" phụ thuộc tiêu chí của bài toán: mức độ biến thiên của tác vụ, hậu quả khi sai, khả năng kiểm tra đầu ra, yêu cầu độ trễ, chi phí chịu được, nhu cầu phê duyệt và phương án fallback khi fail.

## Code thực hành: hai nguyên lý đắt giá nhất

### Factor 7 — `ask_human` chèn approval vào loop

> **Bản chạy được:** file Python hoàn chỉnh cho bài này nằm trong [starter kit](/starter/ai-agent-architecture/) — kèm mock mode và self-test (replay reducer không API), hướng dẫn cài đặt trong [README](/starter/ai-agent-architecture/README.md).

```python
import os, json
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()  # API key đọc từ biến môi trường OPENAI_API_KEY

TOOLS = [{
    "type": "function",
    "function": {
        "name": "ask_human",
        "description": "Hỏi con người duyệt hoặc làm rõ trước khi hành động",
        "parameters": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
}]

def ask_human(question: str) -> str:
    # Production: đẩy notification + chờ approval qua queue, không dùng input()
    print(f"[CHỜ DUYỆT] {question}")
    return input("Trả lời (approve / từ chối + lý do): ").strip()

# Dispatch qua dict: thêm tool mới chỉ là thêm một entry, không đụng run_agent
TOOL_HANDLERS = {
    "ask_human": lambda args: ask_human(args["question"]),
}

def execute_tool_call(call) -> str:
    """Mọi tool call — kể cả tool lạ — đều trả một tool result chuỗi.
    dispatch không raise: lỗi là dữ liệu (Factor 9), không phải exception."""
    try:
        args = json.loads(call.function.arguments or "{}")
    except json.JSONDecodeError as exc:
        return f"Lỗi: arguments của '{call.function.name}' không parse được JSON ({exc})."
    handler = TOOL_HANDLERS.get(call.function.name)
    if handler is None:
        return f"Lỗi: tool '{call.function.name}' không có handler trong TOOL_HANDLERS."
    try:
        return str(handler(args))
    except Exception as exc:  # handler lỗi vẫn sinh tool result để loop tiếp
        return f"Lỗi: handler '{call.function.name}' raise {type(exc).__name__}: {exc}"

def run_agent(task: str, max_steps: int = 12) -> str:
    context = [{"role": "user", "content": task}]
    for _ in range(max_steps):
        resp = client.chat.completions.create(
            model=MODEL, messages=context, tools=TOOLS,
        )
        msg = resp.choices[0].message
        context.append(msg)
        for call in msg.tool_calls or []:
            # Luôn append tool result cho MỌI tool call — kể cả tool lạ
            context.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": execute_tool_call(call),
            })
        if not msg.tool_calls:
            return msg.content  # agent trả lời xong
    return "Dừng do vượt số step cho phép"
```

Điểm khác biệt so với bản demo tối thiểu: mọi tool call — kể cả tool lạ — đều sinh ra một tool result đúng cấu trúc append vào context; thiếu nó là protocol error ở lượt sau. Test cả trường hợp model gọi nhiều tool trong một lượt trước khi chạy thật.

Mấu chốt: `ask_human` không làm gì đặc biệt — nó chỉ là một tool như mọi tool khác. Agent tự quyết khi nào cần hỏi, và câu trả lời của con người chảy vào context như một tool result. Approval gate ra đời từ một dòng định nghĩa tool.

`input()` chỉ hợp minh họa chạy trong terminal. Ứng dụng thật: trạng thái chờ duyệt phải lưu bền vững — ghi event `approval_requested` vào store, đánh dấu state `awaiting_approval`; process chết vẫn resume được khi duyệt xong. Đó chính là Factor 6 (Launch/Pause/Resume) và Factor 12 (reducer) ghép lại.

### Factor 12 — stateless reducer

```python
def reducer(state: dict, event: dict) -> dict:
    """Hàm thuần + idempotency: event đã xử lý thì bỏ qua khi replay.
    Không đụng biến ngoài, không side effect."""
    if event.get("id") in state.get("seen_ids", []):
        return state  # replay không tạo tác dụng phụ lần hai
    new = dict(state)
    new["events"] = state["events"] + [event]
    new["seen_ids"] = state.get("seen_ids", []) + [event["id"]]
    new["step"] = state["step"] + 1
    kind = event.get("kind")
    if kind == "tool_call":
        new["status"] = "running"
    elif kind == "approval":
        new["status"] = "approved" if event["approved"] else "rejected"
    elif kind == "done":
        new["status"] = "completed"
    return new

def drive(events: list, target: str = "completed") -> dict:
    """Driver: load events từ DB, chạy reducer tới trạng thái mục tiêu.
    Resume = gọi lại đúng hàm này với đúng danh sách events."""
    state = {"events": [], "seen_ids": [], "step": 0, "status": "idle"}
    for ev in events:
        state = reducer(state, ev)
        if state["status"] == target:
            break
    return state

# state = drive([
#     {"id": "ev1", "kind": "tool_call", "name": "lookup_order", "result": "order_42"},
#     {"id": "ev2", "kind": "approval", "approved": True},
#     {"id": "ev3", "kind": "done"},
# ])  # -> {"step": 3, "status": "completed", ...}
```

Mỗi tool call và kết quả là một event; state luôn tính lại được từ đầu danh sách. Server chết, worker đổi, chạy lại reducer với cùng events — kết quả như cũ. Event trùng `id` bị bỏ qua khi replay — lớp chống tác dụng phụ lặp nằm trong reducer, không phải trong tool.

## Evals: chấm trace không cần LLM judge

Notebook **Evals** trong kho [GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) của Nir Diamant chỉ ra một điểm quan trọng: phần lớn eval agent không cần LLM judge — chỉ cần so khớp trace (chuỗi step) với ground truth. Agent có gọi đúng tool không, thứ tự step có đúng không, kết quả cuối có chứa thông tin bắt buộc không — hết loại này chấm được bằng Python thuần.

```python
def eval_trace(actual_steps: list, expected_steps: list) -> dict:
    hits = sum(1 for a, e in zip(actual_steps, expected_steps) if a == e)
    return {
        "score": hits / max(len(expected_steps), 1),
        "order_ok": actual_steps[:len(expected_steps)] == expected_steps,
    }

# Trong CI: fail build khi score < 0.8 trên test case bắt buộc
```

| Tiêu chí | Trace-based eval | LLM judge |
| --- | --- | --- |
| Cách chấm | So khớp chuỗi step với ground truth | Model khác đọc trace rồi cho điểm |
| Chi phí | Gần bằng 0, chỉ Python | Mỗi lần eval một lần gọi LLM |
| Chạy trong CI | ✓ Ổn định, cùng input cùng kết quả | Chạy được nhưng flaky hơn |
| Phù hợp | Tool call đúng, thứ tự step, kết quả bắt buộc | Văn phong, câu trả lời mở |

Quy tắc dùng chung cho cả lộ trình: trace-based trước, LLM judge chỉ cho phần không chấm quy tắc được. Eval rẻ thì chạy được mọi commit — đây là điều kiện để agent không chạy lùi dần.

## Guardrails và Dry-Run: propose → simulate → approval

Bài 6 của khóa [Microsoft AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) (Trustworthy AI Agents) dựng bộ guardrail chuẩn, và trong [all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures) có hẳn một architecture mang tên **Dry-Run** cho cùng bài toán: trước hành động rủi ro, agent chạy theo trình tự **propose → simulate → approval gate** — đề xuất thay đổi, mô phỏng kết quả, chờ con người duyệt rồi mới execute. Lệnh DELETE không chạy ngay, nó chạy sau khi bảng so sánh before/after được duyệt.

Bộ guardrail tối thiểu cho agent production:

| Guardrail | Chặn cái gì | Đặt ở đâu |
| --- | --- | --- |
| **PII filter** | Thẻ, CCCD, email lộ vào log hoặc model | Trước khi gửi context |
| **Moderation** | Nội dung độc hại, yêu cầu vi phạm | Trước và sau lời gọi LLM |
| **Prompt injection classifier** | Payload nhét vào dữ liệu để chiếm điều khiển | Trước khi context vào model |
| **Approval gate** | Action rủi ro (chuyển tiền, xóa data, gửi ngoài) | Sau propose, trước execute |

⚠️ Approval gate chỉ hoạt động nếu có con người thật trong vòng — nối trực tiếp với Factor 7: gate là tool `ask_human`, không phải một toggle config trong framework.

⚠️ Approval gate và kiểm tra quyền phải nằm **ở phía server** trước hành động có tác dụng phụ — prompt injection classifier chỉ là một lớp, không phải biện pháp bảo vệ duy nhất.

## Thinking budgets: reasoning effort là chi phí

Một notebook trong GenAI_Agents xử lý đúng bài toán này: kiểm soát **thinking budget** — bao nhiêu reasoning model được phép chi cho một step. Tác vụ dễ không cần suy luận sâu; tiêu tốn budget ở đó là trả tiền cho cái không tạo giá trị. Pattern dùng được ngay: cascade retry — chạy reasoning effort thấp trước, fail thì nâng.

```python
def run_with_budget(task: str, levels=("low", "medium", "high")) -> str:
    out = None
    for level in levels:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": task}],
            reasoning_effort=level,
        )
        out = resp.choices[0].message.content
        if eval_trace(out, REQUIRED_STEPS)["order_ok"]:
            return out  # đạt rồi thì dừng, không đốt budget cao hơn
    return out
```

Cascade này thống nhất với nguyên lý 9 và 12: lỗi được nén lại để lần gọi kế tốt hơn, và toàn bộ vòng chạy vẫn là code của bạn.

> 📍 **Dự án xuyên suốt — DocMind:** sau bài này DocMind có approval gate cho action xóa tài liệu, eval trace chạy trong CI, và có thể pause/resume không mất trạng thái — đủ dùng cho một team thật.

### Lỗi thường gặp

| Lỗi | Vì sao nguy hiểm | Cách sửa |
| --- | --- | --- |
| Model gọi tool không có handler trong dispatch | Loop không append tool result cho tool lạ — protocol error ở lượt sau | Dispatch trả lỗi chuỗi cho MỌI tool call, kể cả tool lạ |
| Replay reducer phát lại event hoàn tiền | Tool side effect không idempotent — hoàn tiền hai lần | Idempotency key + đánh dấu event processed trước khi execute |
| Dùng LLM judge cho tiêu chí chấm được bằng quy tắc | Eval flaky — build đỏ không do regression thật | Chuyển sang trace-based cho phần so khớp được |

## Bài tập tự làm

**Mức 1 — làm theo:** viết agent hoàn tiền mini dùng tool `ask_human`: transaction dưới 5 triệu agent tự duyệt, từ 5 triệu trở lên bắt buộc hỏi. Log toàn bộ events ra file JSON.

**Mức 2 — tự sửa:** chuyển agent loop ở [bài 1](/bai-viet/kien-truc-ai-agent-cam-nang) thành stateless reducer — giữ nguyên hành vi, chạy lại từ danh sách events cũ và so khớp state cuối.

**Mức 3 — mở rộng:** viết eval trace-based với 5 test case, đưa vào CI (GitHub Actions), fail build khi score dưới 0.8. Thêm một bài test idempotency thật: chạy replay reducer với danh sách events chứa event trùng `id` — assert state không đổi sau lần phát lại thứ hai.

## Tài liệu gốc

- [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) — nguồn chính của 12 nguyên lý trong bài này.
- [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) — bài 6 về guardrails và agentic RAG.
- [NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) — notebook Evals và notebook thinking budgets.

Bài này là trụ cột của lộ trình **Kiến trúc AI Agent** — link cố định: `/bai-viet/12-nguyen-ly-agent-production`. Bài tiếp theo, [Chọn architecture cho agent: bản đồ 36 mẫu](/bai-viet/chon-agent-architecture-36-mau), là bản đồ tổng hợp mọi pattern đã học. Nếu bạn mới vào lộ trình, bắt đầu từ [Hướng dẫn xây dựng agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te) để có nền thiết kế.

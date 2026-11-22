---
title: "Nền tảng AI Agent: xây agent loop đầu tiên từ con số 0"
description: "Phân biệt workflow và agent, hiểu vòng lặp agent loop là cốt lõi của mọi hệ thống agent, và tự tay dựng một agent ~100 dòng Python không framework — nền tảng cho toàn bộ kiến trúc AI Agent."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-22"
cover: "/images/covers/posts/nen-tang-agent-va-agent-loop.jpg"
featured: true
views: 500
faq:
  - q: "Agent khác chatbot như thế nào?"
    a: "Chatbot nhận câu hỏi, sinh một câu trả lời và dừng — LLM không kiểm soát việc thực thi. Agent tự quản lý workflow: LLM ra quyết định bước tiếp theo, gọi tool khi cần, đọc kết quả rồi quyết định tiếp cho tới khi hoàn thành mục tiêu. Một LLM trả lời một lượt không phải agent."
  - q: "Agent loop hoạt động theo cơ chế nào?"
    a: "Một vòng lặp gồm 4 bước: model xuất tool call dạng JSON, code của bạn thực thi tool đó, kết quả được append vào context, rồi model nhận context mới để quyết định bước tiếp. Vòng lặp dừng khi model ngừng gọi tool hoặc chạm max_turns."
  - q: "Có cần framework như LangChain hay Agents SDK để xây agent không?"
    a: "Không bắt buộc. Một agent loop hoàn chỉnh chỉ cần OpenAI SDK và khoảng 100 dòng Python. Framework giúp orchestration đa agent, guardrail và quản lý state khi hệ thống phức tạp hơn — nhưng hiểu agent loop bằng code thuần trước là điều kiện để dùng framework đúng."
  - q: "Làm sao để agent không chạy vô hạn?"
    a: "Luôn đặt hai lớp điều kiện dừng: điều kiện tự nhiên (model ngừng gọi tool, hoặc chủ động gọi tool done để báo xong) và max_turns làm nút an toàn. Vượt max_turns thì ép model tổng hợp câu trả lời từ dữ liệu đã thu thập thay vì tiếp tục lặp."
---

Xây agent nghe phức tạp, nhưng trái tim của nó chỉ là một vòng lặp: model quyết định, code thực thi, kết quả quay về model, lặp cho tới khi xong. Hiểu và tự tay viết được vòng lặp đó — agent loop — là bước nền quan trọng nhất trước khi bạn chạm tới framework hay kiến trúc multi-agent.

Bài này đi từ con số 0: phân biệt workflow với agent, xác định khi nào KHÔNG nên dùng agent, rồi tự tay dựng một agent ~100 dòng Python chạy được ngay — không framework. Hiểu vòng lặp ở tầng thấp nhất, mọi abstraction phía sau đều dễ đọc.

## Agent là gì?

> **Agent là hệ thống có thể độc lập hoàn thành workflow thay cho bạn.**

Workflow là chuỗi bước cần thực hiện để đạt mục tiêu của người dùng — xử lý ticket hỗ trợ, review hợp đồng, tạo báo cáo. Phần mềm thông thường giúp bạn tinh gọn và tự động hóa workflow đó; agent thì **thực hiện chính workflow đó thay mặt bạn**, với mức độ độc lập cao.

Một agent có hai đặc điểm cốt lõi:

1. **LLM tự quản lý thực thi và ra quyết định** — LLM là cái não điều phối. Nó nhận biết khi nào workflow hoàn tất, chủ động sửa hành động khi gặp lỗi, và biết dừng lại chuyển quyền kiểm soát cho người dùng khi cần.
2. **Truy cập tools và tự chọn tool** — agent có quyền gọi nhiều tool để đọc ngữ cảnh và thực hiện hành động, tự chọn tool phù hợp theo trạng thái hiện tại của workflow, luôn hoạt động trong guardrail xác định rõ.

Ranh giới quan trọng: những ứng dụng tích hợp LLM nhưng **không dùng LLM để kiểm soát việc thực thi** — chatbot hỏi-đáp đơn giản, một LLM call sinh văn bản, bộ phân loại cảm xúc — không phải agent. Không có vòng quyết định thì không có agent.

Bản dịch đầy đủ guide chính thức của OpenAI về định nghĩa này nằm ở bài [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te). Bài này tập trung vào phần bạn phải tự viết code.

## Workflow vs Agent: hai pattern phải phân biệt trước khi viết code

Kho [GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) đặt hai pattern này cạnh nhau ngay từ đầu, vì gần như mọi hệ thống dùng LLM đều rơi vào một trong hai:

- **Workflow** là flow tất định: code của bạn gọi LLM theo thứ tự viết sẵn, có gate (điểm dừng chờ con người duyệt) ở những bước quan trọng. LLM làm từng bước, nhưng ai quyết định trình tự là code.
- **Agent** là hệ thống để LLM tự quyết định bước tiếp: gọi tool nào, gọi mấy lần, khi nào dừng.

Xét một tác vụ cụ thể: review hợp đồng.

Làm dạng **workflow có gate**:

1. Code gọi LLM dịch hợp đồng.
2. Code gọi LLM trích các điều khoản rủi ro.
3. Code gọi LLM chấm điểm risk cho từng điều khoản.
4. Gate: kết quả đẩy cho luật sư duyệt trước khi trả kết quả cuối.

Mỗi bước là một LLM call cố định. Dữ liệu truyền qua biến. Ai soạn prompt và quyết định thứ tự là lập trình viên.

Cùng tác vụ làm dạng **agent**: bạn khai báo các tool `translate_contract`, `extract_clauses`, `assess_risk`, rồi giao cho model yêu cầu "review hợp đồng này giúp tôi". Model tự quyết định gọi gì, theo thứ tự nào, có cần đọc lại phần nào không, và khi nào đủ thông tin để trả lời. Bạn chỉ giữ gate cuối — agent không được ký duyệt thay con người.

| Tiêu chí | Workflow | Agent |
| --- | --- | --- |
| Ai quyết định trình tự | Code viết sẵn | LLM tự quyết định |
| Tính dự đoán | Cao — chạy 100 lần giống nhau | Thấp hơn — cần guardrail |
| Audit | Dễ — mỗi bước một điểm kiểm tra | Khó hơn — phải log từng lượt loop |
| Chi phí token | Thấp — số lượt gọi cố định | Cao hơn — số lượt gọi không biết trước |
| Phù hợp khi | Bước cố định, cần kiểm soát | Nhiệm vụ mơ hồ, phụ thuộc ngữ cảnh |

Quy tắc chọn đơn giản: đã biết chính xác từng bước → workflow. Không biết trước trình tự các bước → agent.

## Khi nào KHÔNG nên dùng agent

Guide của OpenAI chỉ định dùng agent cho đúng 3 nhóm workflow:

1. **Ra quyết định phức tạp phụ thuộc ngữ cảnh** — phê duyệt hoàn tiền, đánh giá gian lận: không có bộ quy tắc cứng bọc được mọi ngoại lệ.
2. **Bộ quy tắc lớn khó bảo trì** — rules engine phình to, cập nhật tốn kém, dễ lỗi.
3. **Phụ thuộc dữ liệu phi cấu trúc** — phải diễn giải ngôn ngữ tự nhiên, trích xuất ý nghĩa từ tài liệu, hội thoại.

Ngoài 3 nhóm này, giải pháp tất định — if-else, rules engine, một API call — rẻ hơn, nhanh hơn và ổn định hơn. ⚠️ Cảm giác "nên làm agent cho cool" là sai lầm phổ biến nhất của người mới: phần lớn tác vụ thực tế trong công ty là workflow, không phải agent.

## Agent loop — trái tim của kiến trúc

Repo [12-factor-agents](https://github.com/humanlayer/12-factor-agents) mở đầu ngay bằng vòng lặp này, trước cả 12 nguyên tắc chi tiết, vì mọi factor sau đều quay quanh nó. Vòng lặp gồm các bước:

1. Model nhận context hiện tại: system prompt, hội thoại, kết quả tool trước đó.
2. Model xuất **tool call dạng JSON**: gọi tool nào, tham số gì.
3. Code của bạn thực thi tool thật.
4. Kết quả được **append vào context**.
5. Quay lại bước 1 — cho tới khi model quyết định dừng và xuất câu trả lời cuối.

Sơ đồ:

```
[User request]
     │
     ▼
┌─────────┐   tool call (JSON)    ┌────────────────────┐
│   LLM   │ ────────────────────> │ Code executes tool │
│         │ <──────────────────── │ (code của bạn)     │
└─────────┘   result được append    └────────────────────┘
     │           vào context
     │
     ├── còn tool call? ── có ──> quay lại LLM (lặp)
     │
     └── không còn ──> [final response]
```

Hai chi tiết người mới hay bỏ sót:

- Phải append **cả** message chứa tool_calls **và** kết quả tool vào context. Thiếu một trong hai là protocol error ở lượt tiếp theo.
- Model không biết tool trả về gì cho tới khi đọc kết quả trong context — mọi "hiểu biết" của agent về thế giới ngoài đều đi qua context. Quản lý context vì vậy là kỹ năng cốt lõi (factor #3 của 12-factor-agents).

## Code thực hành: agent ~100 dòng, không framework

Cài dependency: `pip install openai`. Toàn bộ agent nằm trong một file duy nhất, gồm 3 phần: tools thật, tool schema, và vòng lặp.

> **Ghi chú phiên bản**: code dùng Chat Completions API qua `openai` SDK 1.x, kiểm tra với `gpt-4o-mini`. Kiến trúc agent loop — tool call JSON → execute → append context → lặp — là kiến thức ổn định theo thời gian; tên API và model thì không. OpenAI đã ngừng Assistants API từ 26/8/2026 và hướng dự án mới sang Responses API: chuyển API không làm đổi vòng lặp bạn học ở đây.

```python
# agent_loop.py — agent đầu tiên, ~100 dòng, không framework
# Chạy: export OPENAI_API_KEY=<your-key-here> && python agent_loop.py

import json
import os

from openai import OpenAI

client = OpenAI()  # SDK tự đọc OPENAI_API_KEY từ environment
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ------------------------------------------------------------------
# 1. Tools thật: code của bạn thực thi, model chỉ "yêu cầu" gọi
# ------------------------------------------------------------------

def get_weather(city: str) -> str:
    # Demo: dữ liệu cứng. Thực tế: gọi API thật — đổi vài dòng return, vòng lặp KHÔNG đổi.
    data = {"Hà Nội": "22°C", "Đà Nẵng": "30°C", "TP.HCM": "31°C"}
    return data.get(city, f"Không có dữ liệu thời tiết cho {city}")

def calculate(expression: str) -> str:
    # Guardrail nhỏ: chỉ cho phép số và toán tử, chặn thực thi code tùy ý
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "Lỗi: biểu thức chứa ký tự không hợp lệ"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Lỗi tính toán: {e}"

# ------------------------------------------------------------------
# 2. Tool schema: mô tả tool bằng JSON để model biết cái gì tồn tại
# ------------------------------------------------------------------

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Lấy nhiệt độ hiện tại của một thành phố Việt Nam. "
                "Dùng khi cần số liệu thời tiết thật, không đoán.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Tên thành phố, ví dụ: 'Hà Nội'",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Tính một biểu thức số học (cộng, trừ, nhân, chia). "
                "Dùng cho so sánh số liệu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Biểu thức, ví dụ: '22 - 30'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]

# Registry: map tên tool -> hàm thật. Phần code duy nhất phải giữ đồng bộ với schema.
TOOL_REGISTRY = {
    "get_weather": get_weather,
    "calculate": calculate,
}

# ------------------------------------------------------------------
# 3. Agent loop: vòng lặp duy nhất làm nên "agent"
# ------------------------------------------------------------------

def run_agent(user_question: str, max_turns: int = 8) -> str:
    messages = [
        {"role": "system", "content": "Bạn là trợ lý thời tiết. Dùng tools khi cần số liệu thật. Không đoán."},
        {"role": "user", "content": user_question},
    ]

    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS_SCHEMA
        )
        msg = response.choices[0].message

        # Điều kiện dừng tự nhiên: model không gọi tool nữa -> câu trả lời cuối
        if not msg.tool_calls:
            return msg.content

        # Bắt buộc: append message chứa tool_calls vào context,
        # thiếu là protocol error ở lượt sau
        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in msg.tool_calls
            ],
        })

        # Thực thi TẤT CẢ tool calls model yêu cầu trong lượt này
        # (model có thể gọi nhiều tool song song trong một response)
        for call in msg.tool_calls:
            fn = TOOL_REGISTRY.get(call.function.name)
            if fn is None:
                result = f"Lỗi: tool '{call.function.name}' không tồn tại"
            else:
                args = json.loads(call.function.arguments)
                result = fn(**args)

            # Append kết quả vào context, gắn đúng tool_call_id
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result),
            })

    # Nút an toàn: hết max_turns -> ép model tổng hợp từ dữ liệu đã có
    messages.append({
        "role": "system",
        "content": "Hết lượt. Trả lời người dùng dựa trên thông tin đã thu thập.",
    })
    final = client.chat.completions.create(model=MODEL, messages=messages)
    return final.choices[0].message.content

if __name__ == "__main__":
    print(run_agent("Hà Nội nay bao nhiêu độ, nóng hơn Đà Nẵng không?"))
```

## Chạy code thế nào

Bốn bước, hai phút:

1. Tạo virtual environment và activate: `python3 -m venv .venv && source .venv/bin/activate`
2. Cài dependency: `pip install openai`
3. Lưu code phía trên thành file `agent_loop.py`
4. Đặt API key rồi chạy: `export OPENAI_API_KEY=sk-... && python agent_loop.py`

Chưa có API key vẫn học được bài này: file trong starter kit đi kèm có mock mode — chạy không cần key, in lại đúng luồng output mẫu bên dưới và tự chạy self-test kiểm tra hành vi agent.

Kết quả mẫu với câu hỏi trong code:

> Lượt 1: tool call get_weather(city="Hà Nội"), get_weather(city="Đà Nẵng")
> Lượt 2: tool call calculate(expression="22 - 30")
> Lượt 3: "Hà Nội 22°C, Đà Nẵng 30°C — Hà Nội mát hơn Đà Nẵng 8 độ."
> Số lượt có thể khác nhẹ tùy model.

> **Bản chạy được:** file Python hoàn chỉnh cho bài này nằm trong [starter kit](/starter/ai-agent-architecture/) — kèm mock mode và self-test, hướng dẫn cài đặt từ đầu trong [README](/starter/ai-agent-architecture/README.md).

Chạy với câu hỏi trên, luồng thực tế diễn ra thế này:

- **Lượt 1**: model xuất 2 tool calls trong cùng một response — `get_weather(city="Hà Nội")` và `get_weather(city="Đà Nẵng")`. Đây là parallel tool calls.
- Code thực thi cả hai, append 2 kết quả vào context.
- **Lượt 2**: model thấy "22°C" và "30°C" — đủ để trả lời trực tiếp; muốn chắc số chênh lệch thì gọi `calculate(expression="22 - 30")` trước. Cả hai đường hợp lệ, model tự quyết.
- **Lượt 3**: model không gọi tool nữa → câu trả lời cuối: "Hà Nội 22°C, Đà Nẵng 30°C — Hà Nội mát hơn Đà Nẵng 8 độ."

Dữ liệu thời tiết ở đây là demo cứng. Thay bằng API thật thì bạn chỉ đổi vài dòng trong `get_weather` — vòng lặp không đổi. Đó chính là lý do thiết kế: agent loop tách rời khỏi tool.

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'openai'` | Chưa cài package hoặc quên activate venv | Activate venv rồi `pip install openai` |
| `AuthenticationError 401` | API key chưa export hoặc key sai | `export OPENAI_API_KEY=...` trong cùng terminal chạy code |
| `invalid_request_error` về model | Tên model sai hoặc tài khoản hết quyền model đó | Đổi `OPENAI_MODEL` hoặc chọn model khác |
| `protocol error` ở lượt 2 | Thiếu append message chứa tool_calls hoặc thiếu tool result | Cả hai đều bắt buộc trong loop — append đủ rồi mới gọi model lại |

## Ba quyết định thiết kế đầu tiên

### 1. Chọn model nào?

Cần model hỗ trợ tool call. `gpt-4o-mini` đủ cho agent đầu tiên của bạn. Nếu model chọn tool sai liên tục, nâng model mạnh hơn trước khi mổ xẻ prompt — nguyên tắc guide OpenAI: prototype với model mạnh nhất, rồi hạ dần và đo lại.

### 2. Chọn tool nào?

Ít, rõ. Mỗi tool làm đúng một việc. Mỗi tham số có description riêng. Registry map tên tool → hàm là phần code duy nhất bạn phải giữ đồng bộ với schema — quy tắc thiết kế tool chi tiết nằm ở bài kế tiếp của series.

### 3. Đặt điều kiện dừng nào?

Ba lớp, chồng lên nhau:

- **Dừng tự nhiên**: model ngừng gọi tool và xuất câu trả lời cuối. Đây là điều kiện chính.
- **max_turns**: nút an toàn bắt buộc. Hết lượt thì ép model tổng hợp từ dữ liệu đã có, không cho lặp tiếp.
- **done flag**: khai báo một tool `done(report)` mà model phải gọi khi coi là xong. Kiểu này kiểm soát rõ nhất ở môi trường production — bạn viết loop như sau:

```python
# Variant: điều kiện dừng bằng done flag
DONE_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Gọi khi đã hoàn thành nhiệm vụ. 'report' là câu trả lời cuối cho người dùng.",
            "parameters": {
                "type": "object",
                "properties": {"report": {"type": "string"}},
                "required": ["report"],
            },
        },
    }
]

def run_agent_v2(user_question: str, max_turns: int = 8) -> str:
    messages = [
        {"role": "system", "content": "Hoàn thành nhiệm vụ bằng các tool. Khi xong, GỌI TOOL done với câu trả lời cuối."},
        {"role": "user", "content": user_question},
    ]
    for _ in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS_SCHEMA + DONE_SCHEMA
        )
        msg = response.choices[0].message
        if not msg.tool_calls:
            return msg.content

        messages.append({"role": "assistant", "content": msg.content,
                         "tool_calls": [c.model_dump() for c in msg.tool_calls]})

        for call in msg.tool_calls:
            if call.function.name == "done":  # điều kiện dừng mới
                return json.loads(call.function.arguments)["report"]

            args = json.loads(call.function.arguments)
            fn = TOOL_REGISTRY.get(call.function.name)
            result = fn(**args) if fn else f"Lỗi: tool '{call.function.name}' không tồn tại"
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})

    return "Hết max_turns, agent chưa báo done."
```

> 📍 **Dự án xuyên suốt — DocMind:** lộ trình đóng trên một dự án: trợ lý tra cứu tài liệu nội bộ. Sau bài này DocMind trả lời được một câu hỏi bằng tool `search_docs` — bạn tự dựng ở bài tập mức 3.

## Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: thêm tool thứ 4 `get_current_time()` trả giờ hiện tại. Chỉ cần hàm + schema + registry — vòng loop không đổi. Mục đích: thấy tool mới "cắm vào" hệ thống mà không đụng logic.

**Mức 2 — Tự sửa**: đổi điều kiện dừng — chạy `run_agent_v2` ở trên với câu hỏi cũ. Mục đích: thấy rõ bạn sở hữu control flow của agent, không phải framework.

**Mức 3 — Mở rộng**: agent hỏi-đáp tài liệu nội bộ — thay `get_weather` bằng `search_docs(query)`, mock tìm từ khóa trong vài đoạn văn bản công ty. Thêm system prompt: "trả lời chỉ dựa trên kết quả search_docs, trích dẫn đoạn nguồn". Đây là hình dáng đầu tiên của DocMind — trợ lý tài liệu nội bộ là dự án xuyên suốt của lộ trình.

## Tài liệu gốc

Bài này tổng hợp từ 3 nguồn tôi dùng khi tự học agent:

- [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) — khóa 18 bài của Microsoft; bài 4 đi sâu tool use.
- [NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) — kho notebook pattern: workflow, agent, routing.
- [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) — 12 nguyên tắc xây agent production-grade; vòng lặp agent loop nằm ngay phần mở đầu.

Đọc tiếp trong series:

- [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te) — bản dịch guide OpenAI: khi nào dùng agent, orchestration, guardrail.
- [AI Engineer Roadmap 2026](/bai-viet/ai-engineer-roadmap-2026) — lộ trình tổng thể nếu bạn đang định hướng career AI.
- [Tool use và Routing: hai pattern nền tảng của agent](/bai-viet/agent-routing-va-tool-design) — bài kế tiếp: routing pattern và thiết kế tool đúng cách.

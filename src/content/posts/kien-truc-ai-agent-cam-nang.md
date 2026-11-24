---
title: "Kiến trúc AI Agent: cẩm nang từ agent loop đến multi-agent"
description: "Cẩm nang gộp trọn 6 bài kiến trúc AI Agent trong một trang: agent loop từ con số 0, tool use và routing, memory và context engineering, planning và reflection, multi-agent orchestration, Agentic RAG đến GraphRAG."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-24"
cover: "/images/covers/posts/nen-tang-agent-va-agent-loop.jpg"
featured: false
views: 180
faq:
  - q: "Cẩm nang này gồm những gì?"
    a: "Toàn bộ 6 bài trước đây đăng riêng giờ gộp trong một trang, chia thành 6 phần đánh số — đọc tuần tự hoặc nhảy tới phần cần đều được."
  - q: "Nên đọc theo thứ tự không?"
    a: "Các phần được xếp theo thứ tự học gợi ý. Đọc lộn vẫn hiểu vì mỗi phần đứng độc lập, nhưng lần đầu học thì nên theo thứ tự. Tổng thời gian đọc khoảng 79 phút."
---

## 01. Nền tảng AI Agent: xây agent loop đầu tiên từ con số 0

Xây agent nghe phức tạp, nhưng trái tim của nó chỉ là một vòng lặp: model quyết định, code thực thi, kết quả quay về model, lặp cho tới khi xong. Hiểu và tự tay viết được vòng lặp đó — agent loop — là bước nền quan trọng nhất trước khi bạn chạm tới framework hay kiến trúc multi-agent.

Bài này đi từ con số 0: phân biệt workflow với agent, xác định khi nào KHÔNG nên dùng agent, rồi tự tay dựng một agent ~100 dòng Python chạy được ngay — không framework. Hiểu vòng lặp ở tầng thấp nhất, mọi abstraction phía sau đều dễ đọc.

### Agent là gì?

> **Agent là hệ thống có thể độc lập hoàn thành workflow thay cho bạn.**

Workflow là chuỗi bước cần thực hiện để đạt mục tiêu của người dùng — xử lý ticket hỗ trợ, review hợp đồng, tạo báo cáo. Phần mềm thông thường giúp bạn tinh gọn và tự động hóa workflow đó; agent thì **thực hiện chính workflow đó thay mặt bạn**, với mức độ độc lập cao.

Một agent có hai đặc điểm cốt lõi:

1. **LLM tự quản lý thực thi và ra quyết định** — LLM là cái não điều phối. Nó nhận biết khi nào workflow hoàn tất, chủ động sửa hành động khi gặp lỗi, và biết dừng lại chuyển quyền kiểm soát cho người dùng khi cần.
2. **Truy cập tools và tự chọn tool** — agent có quyền gọi nhiều tool để đọc ngữ cảnh và thực hiện hành động, tự chọn tool phù hợp theo trạng thái hiện tại của workflow, luôn hoạt động trong guardrail xác định rõ.

Ranh giới quan trọng: những ứng dụng tích hợp LLM nhưng **không dùng LLM để kiểm soát việc thực thi** — chatbot hỏi-đáp đơn giản, một LLM call sinh văn bản, bộ phân loại cảm xúc — không phải agent. Không có vòng quyết định thì không có agent.

Bản dịch đầy đủ guide chính thức của OpenAI về định nghĩa này nằm ở bài [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te). Bài này tập trung vào phần bạn phải tự viết code.

### Workflow vs Agent: hai pattern phải phân biệt trước khi viết code

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

### Khi nào KHÔNG nên dùng agent

Guide của OpenAI chỉ định dùng agent cho đúng 3 nhóm workflow:

1. **Ra quyết định phức tạp phụ thuộc ngữ cảnh** — phê duyệt hoàn tiền, đánh giá gian lận: không có bộ quy tắc cứng bọc được mọi ngoại lệ.
2. **Bộ quy tắc lớn khó bảo trì** — rules engine phình to, cập nhật tốn kém, dễ lỗi.
3. **Phụ thuộc dữ liệu phi cấu trúc** — phải diễn giải ngôn ngữ tự nhiên, trích xuất ý nghĩa từ tài liệu, hội thoại.

Ngoài 3 nhóm này, giải pháp tất định — if-else, rules engine, một API call — rẻ hơn, nhanh hơn và ổn định hơn. ⚠️ Cảm giác "nên làm agent cho cool" là sai lầm phổ biến nhất của người mới: phần lớn tác vụ thực tế trong công ty là workflow, không phải agent.

### Agent loop — trái tim của kiến trúc

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

### Code thực hành: agent ~100 dòng, không framework

Cài dependency: `pip install openai`. Toàn bộ agent nằm trong một file duy nhất, gồm 3 phần: tools thật, tool schema, và vòng lặp.

> **Ghi chú phiên bản**: code dùng Chat Completions API qua `openai` SDK 1.x, kiểm tra với `gpt-4o-mini`. Kiến trúc agent loop — tool call JSON → execute → append context → lặp — là kiến thức ổn định theo thời gian; tên API và model thì không. OpenAI đã ngừng Assistants API từ 26/8/2026 và hướng dự án mới sang Responses API: chuyển API không làm đổi vòng lặp bạn học ở đây.

```python
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

### Chạy code thế nào

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

#### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'openai'` | Chưa cài package hoặc quên activate venv | Activate venv rồi `pip install openai` |
| `AuthenticationError 401` | API key chưa export hoặc key sai | `export OPENAI_API_KEY=...` trong cùng terminal chạy code |
| `invalid_request_error` về model | Tên model sai hoặc tài khoản hết quyền model đó | Đổi `OPENAI_MODEL` hoặc chọn model khác |
| `protocol error` ở lượt 2 | Thiếu append message chứa tool_calls hoặc thiếu tool result | Cả hai đều bắt buộc trong loop — append đủ rồi mới gọi model lại |

### Ba quyết định thiết kế đầu tiên

#### 1. Chọn model nào?

Cần model hỗ trợ tool call. `gpt-4o-mini` đủ cho agent đầu tiên của bạn. Nếu model chọn tool sai liên tục, nâng model mạnh hơn trước khi mổ xẻ prompt — nguyên tắc guide OpenAI: prototype với model mạnh nhất, rồi hạ dần và đo lại.

#### 2. Chọn tool nào?

Ít, rõ. Mỗi tool làm đúng một việc. Mỗi tham số có description riêng. Registry map tên tool → hàm là phần code duy nhất bạn phải giữ đồng bộ với schema — quy tắc thiết kế tool chi tiết nằm ở bài kế tiếp của series.

#### 3. Đặt điều kiện dừng nào?

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

### Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: thêm tool thứ 4 `get_current_time()` trả giờ hiện tại. Chỉ cần hàm + schema + registry — vòng loop không đổi. Mục đích: thấy tool mới "cắm vào" hệ thống mà không đụng logic.

**Mức 2 — Tự sửa**: đổi điều kiện dừng — chạy `run_agent_v2` ở trên với câu hỏi cũ. Mục đích: thấy rõ bạn sở hữu control flow của agent, không phải framework.

**Mức 3 — Mở rộng**: agent hỏi-đáp tài liệu nội bộ — thay `get_weather` bằng `search_docs(query)`, mock tìm từ khóa trong vài đoạn văn bản công ty. Thêm system prompt: "trả lời chỉ dựa trên kết quả search_docs, trích dẫn đoạn nguồn". Đây là hình dáng đầu tiên của DocMind — trợ lý tài liệu nội bộ là dự án xuyên suốt của lộ trình.

### Tài liệu gốc

Bài này tổng hợp từ 3 nguồn tôi dùng khi tự học agent:

- [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) — khóa 18 bài của Microsoft; bài 4 đi sâu tool use.
- [NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) — kho notebook pattern: workflow, agent, routing.
- [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) — 12 nguyên tắc xây agent production-grade; vòng lặp agent loop nằm ngay phần mở đầu.

Đọc tiếp trong series:

- [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te) — bản dịch guide OpenAI: khi nào dùng agent, orchestration, guardrail.
- [AI Engineer Roadmap 2026](/bai-viet/ai-engineer-roadmap-2026) — lộ trình tổng thể nếu bạn đang định hướng career AI.
- [Tool use và Routing: hai pattern nền tảng của agent](/bai-viet/kien-truc-ai-agent-cam-nang) — bài kế tiếp: routing pattern và thiết kế tool đúng cách.

---

## 02. Tool use và Routing: hai pattern nền tảng của agent

Bài trước bạn đã tự tay viết agent loop khoảng 100 dòng không framework. Bài này đi vào hai pattern bạn sẽ gặp gần như trong mọi hệ thống agent: **routing** để điều hướng request một cách rẻ, và **tool use** để agent đọc dữ liệu và hành động. Cả hai đều có code chạy được ngay trong bài.

Đây là hai pattern nằm trong notebook của kho [GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) và bài 4 của khóa [Microsoft ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) — chọn đúng nguồn vì đây là hai pattern lặp lại nhiều nhất khi tôi đọc hệ thống agent thật.

### Routing pattern

> **Routing là một lượt forward pass duy nhất: model đọc request, chọn 1 trong các route định sẵn và trả về route kèm confidence. Không gọi tool, không lặp, không nhiều lượt.**

Notebook "Routing" trong GenAI_Agents xây đúng vậy. Sự khác biệt với agent: agent có vòng lặp và tool calls, số lượt gọi LLM không biết trước; routing chỉ một lần gọi rồi trả kết quả, chi phí và độ trễ biết trước.

Ba tình huống nên dùng routing thay vì full agent:

- **Phân loại intent**: ticket khách hàng → support / billing / technical. Model làm một việc duy nhất: chọn nhãn.
- **Gateway rẻ trước model đắt**: model nhỏ chốt route; chỉ request khó mới lên model lớn hoặc agent đầy đủ. Đây là cách tiết kiệm chi phí phổ biến nhất trong production.
- **Điều hướng multi-agent**: quyết định agent nào tiếp nhận trước khi handoff — routing là bước tiền xử lý của kiến trúc đa agent.

Quy tắc gọn: routing là tầng rẻ nhất trong stack. Phần lớn request đi qua router để bị loại sớm; chỉ phần nhỏ khó mới xuống tới model đắt hay agent đầy đủ.

Code thực hành — router trả enum + confidence bằng structured output:

> **Bản chạy được:** file Python hoàn chỉnh cho bài này nằm trong [starter kit](/starter/ai-agent-architecture/) — kèm mock mode và self-test, hướng dẫn cài đặt từ đầu trong [README](/starter/ai-agent-architecture/README.md).

```python
import json
import os

from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ROUTES = ["support", "billing", "technical", "other"]

SYSTEM_PROMPT = """Bạn là router phân loại intent của ticket khách hàng.
Chọn đúng MỘT route và trả về JSON.
Nếu không chắc chắn (confidence dưới 0.7) thì chọn 'other'."""

def route_ticket(message: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},  # structured output
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Ticket: {message}\n"
                    f"Routes khả dụng: {', '.join(ROUTES)}\n"
                    'Trả về JSON: {"route": "<tên route>", "confidence": <0..1>}'
                ),
            },
        ],
    )
    result = json.loads(response.choices[0].message.content)

    # Guardrail: model trả route ngoài enum thì ép về 'other'
    if result.get("route") not in ROUTES:
        result = {"route": "other", "confidence": float(result.get("confidence", 0.0))}
    return result

if __name__ == "__main__":
    print(route_ticket("Tôi bị trừ tiền 2 lần cho cùng một đơn hàng"))
    # -> {'route': 'billing', 'confidence': 0.95}
```

`response_format={"type": "json_object"}` ép model luôn trả JSON đúng schema bạn khai trong prompt. Vẫn validate ở code: giá trị model xuất là dữ liệu, không phải lời hứa.

Sơ đồ luồng:

```
[User request]
      │
      ▼
┌──────────────────┐  1 lượt forward pass  ┌───────────────────────────┐
│     Router       │ ────────────────────> │ route + confidence (JSON) │
│ (model nhỏ, rẻ)  │                       └─────────────┬─────────────┘
└──────────────────┘                                     │
                                            confidence >= ngưỡng?
                                  ┌─── có ───────────────┴───────── no ───┐
                                  ▼                                       ▼
                 [Xử lý theo route: workflow/model nhỏ]     [Escalate: model đắt /
                                                             agent đầy đủ / human]
```

Biến thể đáng biết: dùng `logprobs` thay vì để model tự khai confidence. Model trả đúng tên route, bạn lấy xác suất của token route làm confidence — khách quan hơn việc model tự chấm điểm:

```python
# Biến thể đo confidence bằng logprobs
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    max_tokens=12,
    logprobs=True,
    top_logprobs=5,
)
# response.choices[0].logprobs chứa xác suất từng token — dùng nó làm confidence
```

### Tool use pattern

Bài 4 của Microsoft course và notebook "Tool design" trong GenAI_Agents cùng đi vào một ý:

> **Tool là một hàm bạn khai báo schema để model có thể yêu cầu gọi. Model không thực thi tool — code của bạn thực thi, rồi trả kết quả về context.**

Câu cuối là kiến trúc quan trọng nhất của pattern này: model chỉ xuất JSON mô tả ý định gọi tool. Việc gọi hàm thật, xử lý lỗi, đưa kết quả vào context là trách nhiệm của code bạn — chính là agent loop trong bài trước.

Ba loại tool thường dùng trong hệ thống agent:

| Loại | Vai trò | Ví dụ |
| --- | --- | --- |
| **Data** | Truy xuất ngữ cảnh và thông tin | `search_orders`, `get_order_status`, tìm kiếm trên web |
| **Action** | Thực hiện hành động ra hệ thống ngoài | `refund_order`, `send_email`, cập nhật CRM |
| **Orchestration** | Agent khác đóng vai trò tool | Handoff tới refund agent, research agent |

Kiến trúc tổng thể — tất cả dữ liệu đi qua context, không có đường tắt:

```
[Model] ── tool call JSON ──> [Code của bạn] ── execute ──> [Tool result]
   ▲                                                         │
   └────────────────── append vào context ────────────────────┘
```

Code thực hành — agent với 3 tool, xử lý song song tool calls, trả lỗi mềm:

```python
# cs_agent.py — agent chăm sóc khách hàng với 3 tool
import json
import os

from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ---- 1. Ba tool thật: data, data, action ----

def search_orders(email: str) -> str:
    db = {
        "an@example.com": ["DH-101", "DH-102"],
        "binh@example.com": ["DH-201"],
    }
    found = db.get(email, [])
    # Lỗi mềm: trả chuỗi đọc được, không throw
    return json.dumps(found, ensure_ascii=False) if found else f"Không tìm thấy đơn nào cho {email}"

def get_order_status(order_id: str) -> str:
    status = {"DH-101": "đã giao", "DH-102": "đang vận chuyển", "DH-201": "đã hủy"}
    return status.get(order_id, f"Lỗi: đơn {order_id} không tồn tại")

def refund_order(order_id: str, reason: str) -> str:
    status = {"DH-101": "đã giao", "DH-102": "đang vận chuyển", "DH-201": "đã hủy"}
    if order_id not in status:
        return f"Lỗi: đơn {order_id} không tồn tại, không thể hoàn tiền"
    return f"Đã tạo yêu cầu hoàn tiền cho {order_id}. Lý do ghi nhận: {reason}"

# ---- 2. Schema cho từng tool: tên là động từ + đối tượng ----

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_orders",
            "description": "Tìm danh sách mã đơn hàng của khách theo email. "
                "Trả về 'Không tìm thấy đơn nào' nếu email không có trong hệ thống.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email của khách hàng"}
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Xem trạng thái hiện tại của một đơn hàng: đã giao, đang vận chuyển, hoặc đã hủy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Mã đơn hàng, ví dụ: 'DH-101'"}
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "refund_order",
            "description": "Tạo yêu cầu hoàn tiền cho một đơn hàng. "
                "Trả lỗi nếu đơn không tồn tại.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Mã đơn hàng cần hoàn tiền"},
                    "reason": {"type": "string", "description": "Lý do hoàn tiền do khách cung cấp"},
                },
                "required": ["order_id", "reason"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "search_orders": search_orders,
    "get_order_status": get_order_status,
    "refund_order": refund_order,
}

# ---- 3. Agent loop — giống hệt bài trước, tool mới không đổi loop ----

def run_agent(user_message: str, max_turns: int = 8) -> str:
    messages = [
        {"role": "system", "content": "Bạn là trợ lý chăm sóc khách hàng. Không đoán dữ liệu — luôn dùng tool."},
        {"role": "user", "content": user_message},
    ]
    for _ in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS_SCHEMA
        )
        msg = response.choices[0].message
        if not msg.tool_calls:
            return msg.content

        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [c.model_dump() for c in msg.tool_calls],
        })

        # Song song: thực thi TẤT CẢ tool calls của lượt này trước khi gọi model lại
        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments)
                fn = TOOL_REGISTRY.get(call.function.name)
                result = fn(**args) if fn else f"Lỗi: tool '{call.function.name}' không tồn tại"
            except Exception as e:
                result = f"Lỗi khi chạy tool: {e}"  # lỗi mềm -> model tự sửa lượt sau

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result),
            })

    messages.append({"role": "system", "content": "Hết lượt. Trả lời dựa trên thông tin đã có."})
    final = client.chat.completions.create(model=MODEL, messages=messages)
    return final.choices[0].message.content

if __name__ == "__main__":
    print(run_agent(
        "Đơn DH-101 của tôi tới đâu rồi? Cho luôn danh sách đơn của an@example.com"
    ))
```

Hai tình huống thử để hiểu pattern:

- Câu hỏi ở trên có **hai request độc lập** — model thường xuất 2 tool calls trong cùng một lượt (`get_order_status("DH-101")` và `search_orders("an@example.com")`), code thực thi cả hai rồi mới gọi model. Vòng `for call in msg.tool_calls` chính là chỗ xử lý song song: không gọi model sau từng tool, gom đủ kết quả rồi mới tiếp.
- Câu hỏi "hoàn tiền giúp tôi đơn DH-999" → `refund_order` trả lỗi mềm "đơn DH-999 không tồn tại" → model đọc lỗi trong context, xin lỗi và hỏi lại mã đúng. Không exception, loop không chết — đây là lợi thế lớn nhất của trả lỗi có thể đọc được.

### Thiết kế tool tốt

Model chọn tool bằng cách đọc tên và mô tả. Nghĩa là tên và description không phải comment — chúng là một phần của prompt. Notebook "Tool design" trong GenAI_Agents tóm được 5 quy tắc:

1. **Tên là động từ + đối tượng**: `get_weather`, `refund_order`. Không `api_call_1`, không `do_stuff`. Tên sai thì model chọn sai.
2. **Mô tả đầy đủ edge case**: "Trả về 'Không tìm thấy đơn nào' nếu email không có trong hệ thống" — model biết có nhánh thay thế sẽ xử lý gọn hơn nhiều so với đoán mò.
3. **Ít tham số, mỗi tham số có description**: mỗi tham số là thêm một chỗ model điền sai. Thiết kế lại tool cho ít tham số trước khi đổ lỗi cho model.
4. **Trả lỗi đọc được, không throw**: lỗi mềm đưa vào context để model tự sửa. Throw làm chết loop và model mất cơ hội phục hồi.
5. **Tool hẹp > tool ôm đồm**: tách `get_order_status` và `refund_order` thay vì gộp thành `manage_order(action="status"|"refund")`. Model ghép các tool hẹp theo ngữ cảnh tốt hơn nhiều so với điều khiển một tool đa năng.

Một quyết định thiết kế thường bị bỏ qua: tool của bạn bám sát API có sẵn (thin API wrapper) hay được thiết kế riêng cho việc của model (model-designed tool)?

| Tiêu chí | Thin API wrapper | Model-designed tool |
| --- | --- | --- |
| Định nghĩa | Bám 1-1 endpoint API có sẵn | Thiết kế riêng cho việc model cần làm |
| Debug | Dễ — lỗi map trực tiếp với API | Khó hơn — abstraction thêm lớp |
| Linh hoạt | Thấp — model phải ghép các wrapper thô | Cao — ngữ cảnh chuyên biệt cho model |
| Rủi ro | API quá rộng làm model lúng túng chọn | Tool tự chế nhiều, khó bảo trì |

Khuyến nghị của tôi: bắt đầu bằng wrapper mỏng bám API thật, đo agent chọn tool đúng thế nào trên một eval set nhỏ, rồi mới thiết kế lại tool theo lỗi thật. Đổi thiết kế tool trước khi đổi model — rẻ hơn nhiều và lặp nhanh hơn.

#### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Model trả route ngoài enum | Route list chưa khai rõ trong prompt | Guardrail ép về `other` như trong code |
| `json.loads` fail | Model trả text kèm JSON | Thêm `response_format={"type": "json_object"}` + retry một lần |
| Model gọi tool không tồn tại | Tên tool lệch giữa schema và registry | Registry trả lỗi mềm để model tự chỉnh |

### 12-factor #4 — tools are just structured outputs

Đây là factor #4 của [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) và là điểm nhiều người bỏ qua lần đầu đọc: **tool call không có gì ma thuật — nó chỉ là JSON có cấu trúc model xuất ra**, giống hệt structured output của router ở đầu bài. Cùng một cơ chế, hai cách dùng: một lượt (routing) hay nhiều lượt (agent loop).

Hệ quả debug cực mạnh:

- Model chọn sai tool → sửa tên hoặc mô tả tool (đó là sửa prompt), không phải "fix model".
- Model điền sai tham số → schema chưa rõ: thêm description tham số, dùng enum cho giá trị cố định, đánh dấu `required`.
- Model gọi tool không tồn tại → registry trả lỗi mềm, model tự chỉnh ở lượt sau.
- Tool trả kết quả vô nghĩa → model phải đoán; thêm mô tả format kết quả vào description.

Ví dụ thực tế: model gọi `get_weather` nhưng thành phố không có dữ liệu — tool trả `{'error': 'city_not_found'}`. Model đọc chuỗi này như một tool result bình thường, rồi tự quyết định xin lỗi người dùng hay đổi cách hỏi. Không exception, không restart, loop vẫn chạy.

Nhìn tool call như structured output, mọi lỗi model-điểm-tool đều quy về một thứ duy nhất bạn có thể sửa: schema và mô tả.

### Pattern nào dùng khi nào

Ba pattern đã học qua 2 bài, đặt cạnh nhau để chọn nhanh:

| Pattern | Số lượt LLM | Chi phí | Dùng khi |
| --- | --- | --- | --- |
| **Routing** | 1 lượt, không tool | Rất thấp | Phân loại intent, gateway rẻ, điều hướng multi-agent |
| **Tool use agent** | Nhiều lượt lặp | Cao hơn | Cần tra dữ liệu + hành động, trình tự không biết trước |
| **Workflow** | 1 call mỗi bước, cố định | Tất định, audit được | Bước cố định, cần kiểm soát từng điểm |

Ba pattern không loại trừ nhau. Hệ thống production thường layered: router chặn ở cổng → route đơn giản đi workflow tất định → route khó mới vào agent đầy đủ. Chi phí giảm, độ dự đoán tăng, và phần mơ hồ chỉ dành phần mềm agent cho đúng chỗ nó cần.

Thứ tự khuyến nghị khi mới bắt đầu: dựng router trước (một buổi chiều là xong), thêm workflow cho route phổ biến, và chỉ viết agent cho route mà workflow không bọc nổi.

> 📍 **Dự án xuyên suốt — DocMind:** sau bài này DocMind có cổng routing phân loại câu hỏi, và các tool của nó có tên + mô tả chuẩn để model chọn đúng — nền cho mọi bài sau.

### Bài tập tự làm (3 mức)

**Mức 1 — Làm theo**: thay `order_id` trong schema của `get_order_status` bằng enum `["DH-101", "DH-102", "DH-201"]`. Thử gọi agent với mã đơn sai và xem model hành xử thế nào trước và sau khi thêm enum.

**Mức 2 — Tự sửa**: thêm tool `cancel_order(order_id)` với mô tả "chỉ hủy được đơn đang vận chuyển; đơn đã giao trả lỗi mềm". Kiểm tra model có tự chặn việc hủy đơn đã giao không. Nếu không, sửa mô tả tool — không phải system prompt — rồi so sánh kết quả trước và sau khi sửa description.

**Mức 3 — Mở rộng**: dùng routing + tool cho DocMind — router phân loại câu hỏi thành `tra_cuu` / `tong_hop` / `khong_lien_quan`; route `tra_cuu` chạy agent với tool `search_docs` từ bài trước. Mục đích: ghép hai pattern của bài này thành cổng vào cho dự án xuyên suốt.

### Tài liệu gốc

- [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) — Lesson 4: Tool Use Design Pattern.
- [NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) — notebooks "Routing" và "Tool design".
- [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) — Factor #4: Tools are just structured outputs.

Đọc tiếp trong series:

- [Nền tảng AI Agent: xây agent loop đầu tiên từ con số 0](/bai-viet/kien-truc-ai-agent-cam-nang) — bài mở đầu series: agent loop ~100 dòng không framework.
- [Claude connectors, MCP và sub-agents](/bai-viet/claude-cho-doanh-nghiep) — mở rộng kiến trúc tool ra ngoài một process: MCP protocol và sub-agents.

---

## 03. Memory và Context Engineering: agent nhớ được gì, bỏ quên gì

Vấn đề lớn nhất của agent production không phải suy luận — model ngày càng giỏi — mà là quản lý cái model nhìn thấy. Mọi thứ vào context window: system prompt, lịch sử hội thoại, kết quả tool, memory được nạp vào, tài liệu vừa truy xuất — đều chiếm cùng một ngân sách hữu hạn và đắt. Agent chạy vài chục vòng sẽ nạp đầy window trước khi hoàn thành tác vụ: hoặc cắt bớt mà mất thông tin quan trọng, hoặc vượt limit mà chết giữa đường.

Bài này gom hai lớp giải pháp: **context engineering** — kỹ thuật quản lý cái gì nằm trong window tại từng lượt — và **memory phân tầng** — kiến trúc để lưu ngoài window rồi nạp lại khi cần.

### Context engineering: cái gì được vào window

> **Context engineering là bộ kỹ thuật quyết định nội dung context window tại mỗi lượt gọi model — không phải chỉ viết prompt đẹp.**

Bài 12 của khóa [Microsoft AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) có riêng một bài về chủ đề này; notebook **Context engineering** trong repo [GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) triển khai các kỹ thuật thành code chạy được. Prompt engineering lo cách diễn đạt một thông điệp; context engineering lo toàn bộ pipeline dữ liệu vào window — bao gồm cắt cái thừa và lấy cái thiếu.

Ba kỹ thuật thực hành, theo thứ tự rẻ đến đắt:

1. **Clear used context** — sau khi dùng xong kết quả tool, xóa nó khỏi context. Ví dụ agent đọc file 5.000 token để sửa một hàm; sửa xong, nội dung file không còn giá trị cho lượt sau. Giữ lại nghĩa là trả tiền token cho mỗi lượt tiếp theo mà model không dùng tới.
2. **Compaction** — tóm tắt lịch sử cũ thành vài gạch đầu dòng giữ bản chất, thay thế các lượt chi tiết. Khác clear ở chỗ nội dung cũ vẫn có giá trị (quyết định người dùng đã đưa, ràng buộc dự án) — chỉ là có thể nén lại.
3. **Pre-fetch** — lấy trước context có thể cần thay vì để agent tự đi lấy giữa chừng (factor 13 của [12-factor-agents](https://github.com/humanlayer/12-factor-agents)). Ví dụ nạp sẵn tài liệu dự án ngay khi agent start thay vì để agent trả một vòng gọi tool + một vòng gọi LLM chỉ để biết mình đang làm gì.

Code thực hành đầu tiên: trim + compaction cho một lịch sử hội thoại.

> **Bản chạy được:** file Python hoàn chỉnh cho bài này nằm trong [starter kit](/starter/ai-agent-architecture/) — kèm mock mode (chạy không cần API key) và self-test, hướng dẫn cài đặt từ đầu trong [README](/starter/ai-agent-architecture/README.md).

```python
import os
from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

RECENT_KEEP = 6          # số lượt gần nhất giữ nguyên
COMPACT_TRIGGER = 16     # tổng lượt chạm mốc này thì nén

def estimate_tokens(messages: list[dict]) -> int:
    return sum(len(m["content"]) // 4 + 8 for m in messages)  # xấp xỉ ~4 ký tự/token

def compact(messages: list[dict]) -> list[dict]:
    """Tách phần lịch sử cũ thành bản tóm tắt, giữ nguyên lượt gần nhất."""
    old, recent = messages[:-RECENT_KEEP], messages[-RECENT_KEEP:]
    summary = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": (
                "Tóm tắt hội thoại dưới đây thành tối đa 10 gạch đầu dòng. "
                "Giữ NGUYÊN: con số, tên riêng, mã đơn, ràng buộc người dùng đã đưa."
            )},
            {"role": "user", "content": "\n".join(f"{m['role']}: {m['content']}" for m in old)},
        ],
    ).choices[0].message.content
    return [
        {"role": "system", "content": f"[Tóm tắt hội thoại trước đó]\n{summary}"},
        *recent,
    ]

def send(messages: list[dict]) -> str:
    if len(messages) >= COMPACT_TRIGGER:
        messages = compact(messages)
    resp = client.chat.completions.create(model=MODEL, messages=messages)
    return resp.choices[0].message.content
```

Ba điểm kỹ thuật:

- **Compaction là một lần gọi model** — nó nhân chi phí, nên chỉ bật khi tổng lượt vượt ngưỡng, không nén mỗi lượt.
- **Instruction giữ nguyên con số và tên riêng** là phần quan trọng nhất của prompt tóm tắt. Mất "giá 12 triệu" hay "hạn 30/12" là mất thông tin người dùng, không phải tiết kiệm.
- `estimate_tokens` chỉ là xấp xỉ; production cần dùng tokenizer thật hoặc giá trị `usage` trả về trong response.

#### Own your context window

Đây là nguyên tắc số 3 trong [12-factor-agents](https://github.com/humanlayer/12-factor-agents): **đừng để framework quyết định cái gì vào context — bạn phải kiểm soát.**

Framework chat tự động ghép toàn bộ history vào mỗi lượt gọi. Tiện cho demo, hại cho production: bạn không cắt được tool output dài, không compaction được giữa đường, không pre-fetch được dữ liệu mà agent sắp cần. Trước mỗi lần gọi model, messages phải là thứ bạn chủ động lắp ráp — từ API thô hoặc framework cho phép can thiệp trước khi gửi.

### Phân tầng memory

Context window là short-term memory. Để nhớ qua phiên và qua ngày, agent cần tầng ngoài window — nạp lại khi cần. Bài 13 của khóa Microsoft và family **"Memory"** trong [all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures) gom các kiến trúc chính:

| Kiến trúc | Nguồn | Cơ chế | Điểm mạnh |
| --- | --- | --- | --- |
| **Short-term** | mặc định | chính context window | đơn giản, tức thời; hết token là quên |
| **Episodic + Semantic** (Park 2023) | Generative Agents | episodic: log từng sự kiện; semantic: triplet kiến thức | chia hai loại nhớ như con người; semantic tính toán được |
| **Graph Memory** | family "Memory" | triples subject/predicate/object thành đồ thị, truy vấn theo quan hệ | trả lời câu hỏi quan hệ giữa nhiều thực thể tốt |
| **MemGPT** (Packer 2023) | mô hình OS | main context + archival storage; agent tự swap trang khi đầy | cần ít can thiệp code; agent tự quản lý window của mình |
| **Voyager** (Wang 2023) | skill library | code Python đã chạy đúng được lưu và tái dùng trong subprocess thật | chất lượng tăng theo thời gian vận hành |
| **Agent Workflow Memory** (Wang 2024) | recipe quy trình | rút từ history các quy trình dùng lại cho tác vụ tương tự | ổn định pipeline khi gặp lại pattern quen |

Sơ đồ mô hình MemGPT — agent xem window như RAM và storage như disk:

```
┌───────────────────────────────────────────────────────┐
│            MAIN CONTEXT (context window — đắt)        │
│ ┌──────────┐ ┌────────────────┐ ┌───────────────────┐ │
│ │ system   │ │ working        │ │ recent messages   │ │
│ │ prompt   │ │ context        │ │ + tool results    │ │
│ └──────────┘ └────────────────┘ └───────────────────┘ │
└───────────────────────────────────────────────────────┘
      ▲                                     │
      │ page in: retrieve khi cần           │ page out:
      │                                     │ compact / archive
      ▼                                     ▼
┌───────────────────────────────────────────────────────┐
│     EXTERNAL STORAGE (rẻ, không giới hạn)             │
│  episodic log │ semantic facts │ skills │ recipes     │
└───────────────────────────────────────────────────────┘
```

#### Tầng nào cho bài toán nào

| Bài toán | Memory tier gợi ý | Lý do |
| --- | --- | --- |
| Chatbot CSKH nhiều phiên | Episodic (log phiên) | cần nhớ ticket cũ của cùng khách hàng giữa các phiên |
| Trợ lý cá nhân dài hạn | Episodic + Semantic | nhớ sự kiện đã qua lẫn sở thích và ràng buộc người dùng |
| Agent lập trình | Skill library kiểu Voyager | code đã chạy đúng là tài sản dùng lại được, rẻ hơn viết lại |
| Agent làm quy trình lặp (upload, deploy, báo cáo) | Agent Workflow Memory | recipe ổn định dùng lại cho tác vụ cùng hình dáng |
| Kiến thức tổ chức nhiều thực thể và quan hệ | Graph Memory | câu hỏi "ai làm gì với ai" truy vấn theo quan hệ tự nhiên hơn vector |

Quy tắc chọn: bắt đầu từ short-term; thêm tầng khi agent thực sự cần thông tin ngoài phiên hiện tại; thêm tầng phức tạp (graph, skill library) chỉ khi bài toán có cấu trúc khớp.

### Code thực hành: MemoryManager không framework

Lớp đơn giản gom cả add, retrieve và compact — keyword scoring thay embedding để không phụ thuộc framework nào:

```python
import time
from dataclasses import dataclass, field

@dataclass
class MemoryItem:
    text: str
    kind: str  # "event" | "fact"
    created: float = field(default_factory=time.time)

class MemoryManager:
    """Memory trong bộ nhớ, không framework: add / retrieve / compact."""

    def __init__(self, max_items: int = 50):
        self.items: list[MemoryItem] = []
        self.max_items = max_items

    # --- ghi: event là lượt xảy ra, fact là kiến thức bền ---
    def add(self, text: str, kind: str = "event") -> None:
        self.items.append(MemoryItem(text=text, kind=kind))
        if len(self.items) > self.max_items:
            self.compact()

    # --- đọc: keyword scoring cộng recency decay ---
    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        terms = {t for t in query.lower().split() if len(t) > 2}
        scored = []
        for item in self.items:
            words = item.text.lower().split()
            overlap = sum(1 for t in terms if t in words)
            if overlap == 0:
                continue
            recency = 1.0 / (time.time() - item.created + 1)
            scored.append((overlap + recency, item))
        scored.sort(key=lambda pair: -pair[0])
        return [i.text for _, i in scored[:top_k]]

    # --- nén: gộp nửa event cũ thành một fact ---
    def compact(self) -> None:
        events = [i for i in self.items if i.kind == "event"]
        if len(events) < 2:
            return
        old, kept = events[:len(events) // 2], events[len(events) // 2:]
        others = [i for i in self.items if i.kind != "event"]
        fact = MemoryItem(text=" | ".join(i.text for i in old), kind="fact")
        self.items = [fact, *kept, *others]

memory = MemoryManager()
memory.add("Người dùng đặt gói Cloud Pro ngày 20/11")
memory.add("Hạn thanh toán là 30/12/2026", kind="fact")
print(memory.retrieve("hạn thanh toán"))
```

Ba phương thức tương ứng ba vai trò:

- **add** ghi event (lượt hội thoại, hành động) hoặc fact (kiến thức bền) — phân kind ngay lúc ghi để compaction biết gộp gì.
- **retrieve** dùng keyword overlap cộng recency decay: item có từ trùng nhiều hơn và mới hơn được nạp trước. Đây là bản nhíp của vector search thật — nâng cấp tự nhiên là thay keyword bằng embedding cosine similarity, đúng kiến trúc đã nói trong bài [Hybrid Search](/bai-viet/rag-nang-cao-cam-nang).
- **compact** ép nửa event cũ thành một fact, giữ nguyên các fact có sẵn — cùng tinh thần compaction của context engineering nhưng ở tầng memory.

#### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Compaction làm mất con số quan trọng | Tóm tắt không có instruction giữ nguyên | Instruction tóm tắt phải ghi rõ "giữ NGUYÊN con số, tên riêng, mã đơn" |
| Retrieve trả kết quả không liên quan | Keyword overlap thấp vẫn vào top_k | Đặt ngưỡng overlap tối thiểu — dưới ngưỡng trả rỗng thay vì ép top_k |
| Đếm token lệch thực tế | `estimate_tokens` là xấp xỉ | Dùng `usage` trả về trong response hoặc tokenizer thật khi tính chi phí |

### Cạm bẫy

Ba cạm bẫy phổ biến khi thêm memory cho agent:

1. **Cho model mọi thứ vào context.** Đắt hơn là rõ hơn: token dài hơn nghĩa là chậm và đắt hơn; nội dung thừa còn làm model phân tán — chất lượng context quan trọng hơn số lượng. Cắt những gì lượt hiện tại không dùng.
2. **Nhầm memory với nền tảng RAG.** RAG truy xuất tài liệu ngoài cho câu hỏi tại chỗ; memory lưu trạng thái liên cá thể và diễn tiến theo thời gian. Cùng dùng vector search nhưng giải bài toán khác — nếu chưa rõ phần truy xuất, đọc bài [Hybrid Search BM25 + Dense + RRF](/bai-viet/rag-nang-cao-cam-nang) trước.
3. **Không log memory.** Khi agent trả lời sai vì "quên", không có log bạn không biết nó đã retrieve gì, đã compact mất gì. Log mỗi lệnh add/retrieve/compact cùng top_k kết quả — đây là câu trả lời cho phần lớn bug memory.

> 📍 **Dự án xuyên suốt — DocMind:** sau bài này DocMind nhớ phiên làm việc trước và giữ context gọn: lịch sử cũ nén thành tóm tắt, kết quả tool đã dùng bị xóa — token giảm, chất lượng không đổi.

### Bài tập tự làm (3 mức)

**Mức 1 — Làm theo:** thêm hàm `trim_tool_results()` bỏ kết quả tool đã tiêu hóa khỏi context. Chạy một hội thoại 20 lượt và so `estimate_tokens` trước/sau — ghi lại số token tiết kiệm thực tế.

**Mức 2 — Tự sửa:** nâng `retrieve()` từ keyword scoring sang embedding cosine similarity. So kết quả trên 10 câu hỏi thực tế của bạn — đếm mỗi bên trả đúng bao nhiêu kết quả liên quan.

**Mức 3 — Mở rộng:** viết instruction compaction giữ nguyên con số và tên riêng, rồi test: nạp hội thoại có "giá 12 triệu, hạn 30/12", nén, và hỏi lại agent xem nó còn nhớ đúng hai giá trị đó không. Ghép vào DocMind — trợ lý phải nhớ được "hạn thanh toán 30/12/2026" mà người dùng nói ở phiên trước.

### Tài liệu gốc

- [Microsoft AI Agents for Beginners — lesson 12 (Context engineering) và lesson 13 (Memory)](https://github.com/microsoft/ai-agents-for-beginners)
- [all-agentic-architectures — family "Memory"](https://github.com/FareedKhan-dev/all-agentic-architectures)
- [GenAI_Agents — notebook Context engineering](https://github.com/NirDiamant/GenAI_Agents)
- [12-factor-agents — factor 3 "Own your context window", pre-fetch context](https://github.com/humanlayer/12-factor-agents)
- Paper nền: MemGPT (Packer 2023), Generative Agents (Park 2023), Voyager (Wang 2023), Agent Workflow Memory (Wang 2024)
- Đọc liên quan trong series: [Hybrid Search BM25 + Dense + RRF](/bai-viet/rag-nang-cao-cam-nang) — nền truy xuất cho retrieve; [GraphRAG và Knowledge Graph](/bai-viet/rag-nang-cao-cam-nang) — nền cho Graph Memory; [Nền tảng agent và agent loop](/bai-viet/kien-truc-ai-agent-cam-nang) — agent loop mà memory gắn vào.

---

## 04. Planning và Reflection: agent tự lập kế hoạch và tự sửa lỗi

Một agent chạy agent loop cơ bản xử lý tốt tác vụ một đến vài vòng: nhận yêu cầu, gọi tool, trả kết quả. Đổi sang tác vụ phức tạp gồm nhiều bước phụ thuộc nhau, loop trần thường thất bại theo ba cách dễ đoán: bỏ sót bước, làm sai thứ tự, và chết ở bước đầu khi tool fail mà không quay lại. Hai pattern trong bài vá đúng ba lỗi đó: **planning** tự lập kế hoạch trước khi chạy, **reflection** tự chấm điểm và tự sửa sau khi chạy.

Nguyên lý chung: cả hai đều thêm lần gọi model bổ sung để kiểm soát lần gọi chính — luôn đổi chi phí lấy chất lượng. Bài này đi qua cơ chế, code chạy được và chi phí thật của mỗi lựa chọn.

### Planning: phân rã, thực thi, replan

> **Planning là pattern agent phân rã mục tiêu thành danh sách bước rõ ràng, thực thi từng bước và lập kế hoạch lại khi thực tế lệch khỏi dự đoán.**

Bài 7 của khóa [Microsoft AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) dành riêng cho pattern này; trong repo [all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures), planning nằm trong họ **"Tools & Actions"** cùng tool use và routing — bản chất nó cũng chỉ là cách tổ chức việc gọi tool có hệ thống.

Vòng đời chuẩn gồm ba pha:

1. **Decompose** — planner nhận mục tiêu, trả danh sách bước, mỗi bước có action và expected.
2. **Execute** — executor chạy từng bước, kết quả bước trước làm context cho bước sau.
3. **Replan** — bước fail thì planner viết lại phần kế hoạch còn lại dựa trên đã làm và lỗi vừa gặp.

```
              ┌───────────────┐
 Mục tiêu ──→ │    PLANNER    │ ──→ kế hoạch: [bước 1, bước 2, bước 3]
              └───────────────┘
                        │
                        ▼
              ┌───────────────┐  bước fail     ┌───────────────┐
              │   EXECUTOR    │ ─────────────→ │    REPLAN     │
              │ (chạy từng    │                │ (viết lại phần│
              │    bước)      │ ←───────────── │  kế hoạch)    │
              └───────────────┘  kế hoạch mới  └───────────────┘
                        │
                        ▼  bước OK → chạy tiếp đến hết kế hoạch
                 Kết quả cuối
```

#### Plan-then-execute hay interleave?

Hai phong cách lập kế hoạch, chọn theo hình dáng tác vụ:

| Tiêu chí | Plan-then-execute | Interleave (lập bước chạy bước) |
| --- | --- | --- |
| Cách làm | Planner viết ra toàn bộ kế hoạch, executor chạy lần lượt | Model chỉ quyết định bước tiếp theo mỗi vòng, không có bản kế hoạch tổng |
| Ưu điểm | Kế hoạch rõ, dễ review và debug trước khi đốt chi phí thực thi | Linh hoạt với bài toán không nhìn trước được hết; không lãng phí lập kế hoạch rồi vứt |
| Nhược điểm | Sai ở đầu thì cả chuỗi sai theo; chậm thích ứng với tín hiệu mới giữa đường | Dễ lạc đề sau nhiều vòng; khó audit tiến trình tổng thể |
| Hợp với | Tác vụ có cấu trúc rõ: deploy, migrate dữ liệu, tổng hợp báo cáo nhiều nguồn | Tác vụ khám phá: research web, debug hệ thống lạ, tìm kiếm đa nhánh |

ReAct trong bài [nền tảng agent](/bai-viet/kien-truc-ai-agent-cam-nang) là interleave thuần túy — planning thêm bản kế hoạch trên đó. Nhiều agent production dùng cả hai: kế hoạch thô trước, rồi cho phép một bước sinh bước con khi cần.

#### PEV: thêm verify sau mỗi bước

Plan-Execute-Verify (PEV) là biến thể đáng nhớ của họ "Tools & Actions": sau mỗi bước execute thêm một bước **verify độc lập** — tool có trả về dữ liệu đúng dạng không, kết quả có hợp lý không, bước này có làm tiến gần mục tiêu không. Verify pass mới sang bước kế; fail thì mới đụng đến replan.

Không verify, executor chỉ biết bước "chạy xong" chứ không biết bước "chạy đúng" — kết quả lỗi ở bước 2 được bước 3 dùng làm đầu vào và lan cả chuỗi. Verify mỗi bước cắt lỗi ngay tại chỗ sinh ra, đổi lấy một lần gọi model cho mỗi bước.

Code thực hành đầu tiên: plan-then-execute có replan khi bước fail.

> **Bản chạy được:** file Python hoàn chỉnh cho bài này nằm trong [starter kit](/starter/ai-agent-architecture/) — kèm mock mode (chạy không cần API key) và self-test, hướng dẫn cài đặt từ đầu trong [README](/starter/ai-agent-architecture/README.md).

```python
import os
import json
from openai import OpenAI

client = OpenAI()  # đọc OPENAI_API_KEY từ env
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def llm(messages: list[dict]) -> str:
    resp = client.chat.completions.create(model=MODEL, messages=messages)
    return resp.choices[0].message.content

def make_plan(goal: str) -> list[dict]:
    raw = llm([
        {"role": "system", "content": (
            "Bạn là planner. Phân rã mục tiêu thành tối đa 5 bước, mỗi bước có "
            "action và expected. Chỉ trả JSON: "
            '{"steps": [{"id": 1, "action": "...", "expected": "..."}]}'
        )},
        {"role": "user", "content": f"Mục tiêu: {goal}"},
    ])
    return json.loads(raw)["steps"]

def execute_step(step: dict, context: list[str]) -> str:
    return llm([
        {"role": "system", "content": "Thực thi bước dưới đây dựa trên kết quả đã có. Trả kết quả ngắn gọn."},
        {"role": "user", "content": f"Bước: {step['action']}\nKết quả trước đó: {context}"},
    ])

def replan(goal, failed_step, error, done, remaining) -> list[dict]:
    raw = llm([
        {"role": "system", "content": (
            "Bước dưới đây đã fail. Viết lại CHỈ phần kế hoạch còn lại để "
            "tránh nguyên nhân fail. Chỉ trả JSON đúng định dạng steps."
        )},
        {"role": "user", "content": (
            f"Mục tiêu: {goal}\nĐã làm xong: {done}\n"
            f"Bước lỗi: {failed_step['action']}\nLỗi: {error}\n"
            f"Bước chưa chạy: {remaining}"
        )},
    ])
    return json.loads(raw)["steps"]

def run_plan(goal: str, max_replans: int = 2) -> list[str]:
    steps, results, done, replans = make_plan(goal), [], [], 0
    while steps:
        step = steps.pop(0)
        try:
            outcome = execute_step(step, results)
            results.append(outcome)
            done.append(step)
        except Exception as e:
            replans += 1
            if replans > max_replans:
                raise RuntimeError(f"Replan vượt {max_replans} lần: {e}")
            steps = replan(goal, step, str(e), done, [s["action"] for s in steps])
    return results
```

Ba chi tiết đáng chú ý hơn phần thân code:

- **JSON thay vì free text** làm planner và replan nối vào executor không đổi giao diện. Model hay trả lệch format thì thêm `response_format={"type": "json_object"}` và retry một lần khi parse lỗi.
- **Replan chỉ viết phần còn lại**: phần đã pass không bị model viết lại thành khác, tránh regression ở những bước đã chạy đúng.
- **max_replans là van an toàn** — không có nó, một bước fail lặp vô tận sẽ đốt hóa đơn trong lúc bạn đi ăn trưa.

### Reflection: generate → critique → refine

> **Reflection là pattern agent tự đánh giá kết quả của chính mình và sửa lại trước khi giao cho người dùng.**

Nền lý thuyết: bài 9 "Metacognition" của khóa Microsoft — cho agent khả năng suy nghĩ về việc mình đang làm — và notebook **Reflection** trong repo [GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents). Công trình gốc là Self-Refine (Madaan 2023), vòng ba bước:

1. **Generate** — tạo bản nháp đầu tiên.
2. **Critique** — chính model chấm bản nháp theo rubric và liệt kê issues cụ thể.
3. **Refine** — sửa bản nháp theo issues, quay lại critique.

Lặp đến khi pass hoặc hết vòng. Rubric quyết định chất lượng cả vòng: "hay hơn" là critique vô dụng vì model không biết sửa đâu; "mỗi khẳng định phải có căn cứ, thiếu thì ghi rõ chỗ nào" mới dùng được.

#### Ba biến thể critique

Notebook Reflection triển khai ba biến thể thực hành, tăng dần độ chắc:

| Biến thể | Cách làm | Hợp với |
| --- | --- | --- |
| **Self-review** | Agent tự chấm theo rubric viết sẵn | Mọi tác vụ văn bản; rẻ nhất, dễ thêm nhất |
| **Skeptical reviewer** | Cùng model nhưng reviewer được hướng dẫn đọc hoài nghi, nghi ngờ từng khẳng định, tìm chỗ lý luận hụt | Nội dung có khẳng định mạnh, lý luận, bản dịch |
| **Fail-tests-as-feedback** | Chạy test thật, dùng assertion fail làm feedback cho vòng refine tiếp | Code: chắc chắn nhất vì feedback đến từ runtime |

Biến thể thứ hai đáng dừng một chút: cùng một model, chỉ đổi system prompt sang "bạn là reviewer hoài nghi..." là critique bắt được lớp lỗi mà self-review tử tế bỏ sót. Không cần model thứ hai — cần một góc nhìn khác.

Code thực hành thứ hai: vòng refine với rubric chấm điểm và stop condition rõ.

```python
import os
import json
from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def llm(messages: list[dict]) -> str:
    resp = client.chat.completions.create(model=MODEL, messages=messages)
    return resp.choices[0].message.content

RUBRIC = """Chấm bản nháp theo 3 tiêu chí, mỗi tiêu chí 1-5 điểm:
1. Factuality: mỗi khẳng định có căn cứ trong yêu cầu.
2. Completeness: trả lời đủ mọi phần của yêu cầu.
3. Clarity: người đọc hiểu ngay, không vòng vo.
Trả JSON: {"scores": {"factuality": int, "completeness": int, "clarity": int},
"total": int, "issues": ["..."], "pass": true|false} — pass khi total >= 12/15."""

def generate(task: str) -> str:
    return llm([
        {"role": "system", "content": "Viết câu trả lời chất lượng cao cho yêu cầu."},
        {"role": "user", "content": task},
    ])

def critique(task: str, draft: str) -> dict:
    raw = llm([
        {"role": "system", "content": RUBRIC},
        {"role": "user", "content": f"Yêu cầu: {task}\n\nBản nháp:\n{draft}"},
    ])
    return json.loads(raw)

def refine(task: str, draft: str, issues: list[str]) -> str:
    return llm([
        {"role": "system", "content": "Sửa bản nháp theo từng issue. Giữ phần đạt, chỉ thay phần bị chê."},
        {"role": "user", "content": f"Yêu cầu: {task}\n\nBản nháp:\n{draft}\n\nIssues:\n" + "\n".join(issues)},
    ])

def reflect_loop(task: str, max_rounds: int = 3) -> tuple[str, int]:
    draft = generate(task)
    prev_total = 0
    for round_no in range(1, max_rounds + 1):
        fb = critique(task, draft)
        if fb["pass"]:
            return draft, round_no
        if prev_total and fb["total"] <= prev_total:
            break  # điểm không tăng nữa — thêm vòng chỉ đốt tiền
        prev_total = fb["total"]
        draft = refine(task, draft, fb["issues"])
    return draft, round_no
```

Hai stop condition đều cần: pass theo rubric là chính; **điểm không tăng giữa hai vòng** là phụ — điểm đi ngang thì vòng sau gần như chắc chắn không cải thiện, và từ vòng ba reflection chỉ còn sửa lỗi rất nhỏ.

#### Reflexion: lưu lỗi để không lặp

Reflexion (Shinn 2023) là bước nâng cấp của reflection thường, khác biệt nằm ở nơi lưu lời tự phản tư:

- **Reflection thường**: critique và refine diễn ra trong một phiên; hết phiên là hết — lần chạy sau không biết gì về lần trước.
- **Reflexion**: sau khi thất bại, agent viết lời tự phản tư dạng chữ ("lần trước fail vì thiếu kiểm tra dữ liệu đầu vào; lần sau kiểm tra trước khi xử lý") lưu vào **episodic memory**; lần thử kế đọc lại trước khi làm, không lặp cùng lỗi.

Triển khai tối giản: một list hoặc file, mỗi lần thử push một note, lần thử sau nạp các note cũ vào system prompt. Ba lời phản tư là đủ để tránh lớp lỗi lặp — pattern rẻ nhất trong bài nhưng tăng chất lượng qua các phiên, không chỉ một phiên.

#### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Planner trả JSON lệch, parse fail | Prompt chưa chốt format cứng | Thêm `response_format={"type": "json_object"}` + retry một lần khi parse lỗi |
| Replan lặp vô tận | Bước fail lặp lại cùng nguyên nhân | Van an toàn `max_replans` — vượt ngưỡng thì raise |
| Critique chấm mọi thứ pass | Rubric mơ hồ kiểu "hay hơn" | Rubric phải có số đo và định nghĩa rõ từng tiêu chí |

### Sampling & Search: chạy nhiều phương án rồi chọn

Nhóm pattern thứ ba không tự sửa theo vòng lặp mà **chạy nhiều phương án rồi chọn phương án tốt nhất**. Đầu ra model một lần chỉ là một sample và sample có thể rơi vào trạng thái kém; sinh nhiều sample rồi tìm kiếm giữa chúng tăng xác suất có phương án tốt.

| Pattern | Ý tưởng | Chi phí (số lần gọi LLM) | Khi nào đáng dùng |
| --- | --- | --- | --- |
| **Self-Consistency** (Wang 2022) | Sample N lần cùng prompt, chọn đáp án chiếm đa số (majority vote) | ~x5-x7 với N=5 | Câu hỏi có đáp án đúng duy nhất (toán, trắc nghiệm); không hợp output tự do vì vote không định nghĩa được |
| **Tree of Thoughts** (Yao 2023) | Beam search trên "thoughts": mỗi bước sinh nhiều nhánh, đánh giá và chỉ giữ nhánh tốt | ~x10+, tăng theo depth × beam | Bài toán xây dựng từng bước, biết đánh giá trạng thái giữa chừng (lập kế hoạch phức tạp, chơi cờ) |
| **LATS** (Zhou 2024) | MCTS trên không gian action, reward từ tín hiệu thực (test pass/fail) backup ngược lên cha | ~x10+ mỗi iteration | Tác vụ code/debug có verifier tự động; đáng đổi chi phí khi có tín hiệu runtime |
| **Chain-of-Verification** (Dhuliawala 2023) | Sinh câu trả lời, tự đặt câu verify từng khẳng định, trả lời các câu verify đó độc lập rồi ghép lại | ~x3 | Nội dung fact-dense: bản dịch kỹ thuật, tổng hợp tài liệu — nơi hallucination nguy hiểm nhất |

Chain-of-Verification đáng chú ý vì các câu verify được trả lời trong những lần gọi riêng, không nhìn thấy câu trả lời gốc — tránh việc model "tự xác nhận" chính sai lầm của mình.

### Chi phí thật: đếm số lần gọi trước khi bật pattern

Mọi pattern trong bài đều **nhân số lần gọi model** — và số lần gọi nhân trực tiếp cả hóa đơn lẫn độ trễ. Quy tắc nhanh:

- **Reflection rẻ**: ~x2 (generate + critique); mỗi vòng refine thêm x1.
- **Self-Consistency trung**: ~x5-x7 với N=5.
- **ToT / LATS đắt**: ~x10+ và tăng theo beam width; thực tế có thể nhiều hơn nếu phải đánh giá mỗi node.
- **PEV**: thêm x1 cho mỗi bước — pipeline 5 bước thành ~10 lần gọi, không phải x2 toàn pipeline.

Bật pattern khi **accuracy đáng giá hơn chi phí**: tác vụ production có hậu quả thật — email khách hàng, commit lên main, báo cáo tài chính — đáng đổi x2-x5; tác vụ nội bộ dùng thử hoặc baseline đã pass 95% thì không đáng.

⚠️ Đo baseline trước khi bật: không có eval đo accuracy trước/sau, bạn chỉ đốt tiền theo niềm tin — cùng nguyên tắc chọn model trong bài nền tảng.

> 📍 **Dự án xuyên suốt — DocMind:** sau bài này DocMind xử lý được câu hỏi nhiều bước: planner tách câu hỏi phức tạp thành các lần truy xuất, executor chạy theo thứ tự, bước fail thì replan — thay vì để loop trần mò từng bước.

### Bài tập tự làm (3 mức)

**Mức 1 — Làm theo:** chạy `run_plan` với mục tiêu "tổng hợp 3 bài báo thành brief 5 gạch đầu dòng". In danh sách bước planner trả về và để ý bước nào model tưởng có tool nhưng thực tế không có — đó là chỗ cần thêm verify trước executor.

**Mức 2 — Tự sửa:** thêm verify vào pipeline: sau mỗi `execute_step`, verifier chấm 1-5 theo expected; dưới 3 thì replan. Đếm tổng lần gọi LLM thực tế — so với dự đoán của bạn trước khi chạy.

**Mức 3 — Mở rộng:** áp Reflexion cho một tác vụ viết: lần thử 1 fail theo rubric, lưu lời tự phản tư; lần thử 2 nạp nó vào system prompt. So `total` điểm rubric giữa hai lần — không tăng nghĩa là lời phản tư vô dụng, chỉnh rubric trước khi thử thêm. Ghép vào DocMind — khi câu hỏi tài liệu là "so sánh chính sách A và B", plan tách thành 2 nhánh truy xuất rồi tổng hợp.

### Tài liệu gốc

- [Microsoft AI Agents for Beginners — lesson 7 (Planning) và lesson 9 (Metacognition)](https://github.com/microsoft/ai-agents-for-beginners)
- [all-agentic-architectures — family "Tools & Actions"](https://github.com/FareedKhan-dev/all-agentic-architectures)
- [GenAI_Agents — notebook Reflection](https://github.com/NirDiamant/GenAI_Agents)
- Paper nền: Self-Refine (Madaan 2023), Reflexion (Shinn 2023), Self-Consistency (Wang 2022), Tree of Thoughts (Yao 2023), LATS (Zhou 2024), Chain-of-Verification (Dhuliawala 2023)
- Đọc trước trong series: [Nền tảng agent và agent loop](/bai-viet/kien-truc-ai-agent-cam-nang) — vòng agent loop và ReAct mà planning, reflection dựa trên; [Agent routing và tool design](/bai-viet/kien-truc-ai-agent-cam-nang) — tool mà executor gọi, routing mà planner điều hướng.

---

## 05. Multi-agent orchestration: điều phối đội agent như một hệ thống

Bài [Nền tảng agent và agent loop](/bai-viet/kien-truc-ai-agent-cam-nang) đã dựng một agent hoàn chỉnh: model, tools và vòng lặp quyết định. Câu hỏi tiếp theo rất tự nhiên khi agent bắt đầu làm việc thật: một agent có đủ không? Nguyên tắc của bài này khó chịu nhưng đúng: **thường là đủ — và khi không đủ, multi-agent phải trả giá**. Không có nâng cấp miễn phí nào ở đây.

Bài đi qua bốn phần: thời điểm nên tách nhiều agent, hai mẫu orchestration gốc (supervisor và handoff), các kiến trúc multi-agent đáng nhớ, rồi bảng so sánh framework và một bản dựng supervisor bằng OpenAI SDK chạy được ngay.

### Khi nào cần nhiều agent

Bài 8 của Microsoft AI Agents for Beginners đặt nguyên tắc theo đúng thứ tự: **tối đa hóa single-agent trước, tách multi-agent là phương án cuối**. Trước khi nghĩ đến "đội agent", còn ba mỏ vàng chưa khai: thêm tools từng bước, dùng prompt template với biến chính sách thay vì nhiều prompt riêng, và cải thiện tên với mô tả tools — model chọn nhầm tool phần lớn là do mô tả mơ hồ.

Chỉ khi ba cách trên đã dùng hết mà agent vẫn sai, mới xét dấu hiệu chạm trần:

- **Quá nhiều tools chồng lấn** — model chọn nhầm dù mô tả đã tốt, và bảng danh sách tools chiếm chỗ trong context.
- **Nhánh if-else chồng chéo** — thêm một ca sử dụng là phải sửa prompt cũ và chờ nó không phá ca cũ.
- **Các phần công việc cần system prompt khác hẳn nhau** — nhét mọi vai trò vào một prompt làm ngữ cảnh dài và loãng.
- **Các phần độc lập có thể chạy song song** — ví dụ tra ba nguồn dữ liệu cùng lúc.

> **Bắt đầu single-agent. Multi-agent là chi phí — thêm token, thêm độ trễ, thêm điểm lỗi — không phải nâng cấp miễn phí.**

| Tình huống | Nên làm |
| --- | --- |
| Agent chưa đủ tools, prompt còn sơ sài | Ở lại single-agent |
| Đã tối ưu tools và prompt nhưng vẫn chọn nhầm tool | Cân nhắc tách theo nhóm tools |
| Một prompt gánh nhiều vai trò mâu thuẫn | Tách theo vai trò |
| Tác vụ độc lập, chạy song song được | Tách + fan-out từ một điểm điều phối |
| Chỉ muốn hệ thống "trông chuyên nghiệp hơn" | Ở lại single-agent |

### Hai mẫu orchestration gốc

Guide *A Practical Guide to Building Agents* của OpenAI (đã dịch trong bài [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te)) chỉ nêu đúng hai mẫu orchestration; mọi framework về sau đều là biến thể của hai mẫu này. Ở đây chỉ chốt bản chất, không lặp lại chi tiết cú pháp.

**Manager/supervisor pattern** — một agent trung tâm giữ toàn quyền điều phối. Specialist được bọc thành tool (trong Agents SDK là `as_tool`): supervisor gọi khi cần, nhận kết quả về, tự quyết bước tiếp. Specialist không nói chuyện với người dùng, cũng không nói chuyện với nhau.

**Handoff phi tập trung** — quyền thực thi và toàn bộ trạng thái hội thoại được chuyển hẳn cho agent kế tiếp, không quay lại. Kiểu quen nhất là pipeline chăm sóc khách hàng: agent ngôn ngữ nhận tin nhắn, chuyển quyền cho agent bán hàng, agent bán hàng chuyển cho agent hoàn tất thanh toán.

| Tiêu chí | Manager/supervisor | Handoff phi tập trung |
| --- | --- | --- |
| Ai giữ context | Supervisor giữ trọn hội thoại | Agent đang giữ quyền thực thi |
| Điểm tương tác | Một, tại supervisor | Nhiều, theo lượt chuyển quyền |
| Kiểm soát chất lượng | Tập trung: mọi kết quả đi qua supervisor | Phân tán: mỗi agent tự chịu phần mình |
| Chi phí context | Cao dần ở supervisor (tích lũy) | Thấp hơn mỗi agent, nhưng mất nhìn tổng thể |
| Khi nào chọn | Pipeline cần tổng hợp, quyết định cuối | Mỗi chuyên gia tiếp quản trọn vẹn một pha |

Hai mẫu khác nhau trong code thế nào? Vài dòng dưới đây đủ để thấy — bản supervisor đầy đủ nằm ở phần cuối bài:

```python
def handoff_pipeline(topic: str) -> str:
    research = researcher(topic)      # specialist 1 chạy xong
    return writer(topic, research)    # specialist 2 tiếp quản, không quay lại
```

Quy tắc chọn gọn như sau: cần **một đầu ra cuối cùng có người chịu trách nhiệm** → supervisor. Workflow tự nhiên tách thành các pha rời rạc, mỗi pha một chủ nhân → handoff.

### Các kiến trúc multi-agent khác

Họ "Multi-Agent" trong [all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures) có thêm bốn kiến trúc đáng nhớ. Điểm chung: chúng là cách **cấu trúc lại quyền ra quyết định** — ai được nói gì, khi nào, và ai nghe.

**Debate** (Du et al., 2023). N agent trả lời độc lập, rồi K vòng phản biện lẫn nhau; một judge (hoặc bỏ phiếu đa số) chọn câu cuối. Paper gốc cho thấy debate tăng accuracy trên tác vụ suy luận toán học và chiến lược. Cái giá: một câu hỏi tốn N × K lần gọi LLM trở lên.

**Blackboard** — tư tưởng từ hệ AI cổ điển (Hearsay-II, thập niên 1970). Một workspace chung: agent nào xong phần mình ghi kết quả lên đó, agent khác đọc và tiếp nối. Không ai điều phối ai. Phù hợp khi không biết trước thứ tự công việc.

**STORM** (Shao et al., 2024). Mô phỏng nhóm nghiên cứu viết bài Wikipedia: nhiều perspective đặt câu hỏi khác nhau, khảo sát nguồn, tổng hợp thành bài có trích dẫn. Chọn kiến trúc này khi cần nội dung dài, đa góc nhìn, có căn cứ nguồn.

**Mixture of Agents** (Wang et al., 2024). Nhiều LLM xếp thành tầng proposer: tầng sau nhìn thấy output tầng trước, tầng cuối một aggregator tổng hợp. Trên benchmark, tập hợp model trung bình vượt cả model mạnh hơn từng cái một — cùng tinh thần với ensemble trong machine learning.

#### Sơ đồ supervisor

Kiến trúc supervisor — mẫu mà phần code dưới đây dựng — trông như sau:

```
                     ┌────────────────────────────────┐
  Người dùng ──────► │           Supervisor           │
                     │   giữ context, quyết định cuối  │
                     └────────┬──────────────┬────────┘
                              │              │
                  gọi như tool│              │gọi như tool
                              ▼              ▼
                      ┌────────────┐   ┌────────────┐
                      │ Researcher │   │   Writer   │
                      │ thu số liệu│   │ viết bài   │
                      └──────┬─────┘   └──────┬─────┘
                             │                │
                             └────────┬───────┘
                                      ▼
                         kết quả về lại Supervisor
```

Hai mũi tên xuống là hai lời gọi tool; hai đường về là hai kết quả trả về. Không có cạnh nối Researcher với Writer — mọi luồng dữ liệu đi qua supervisor. Đây là lý do supervisor dễ debug hơn handoff: toàn bộ lịch sử nằm ở một chỗ.

### Chọn framework

| Framework | Mô hình thiết kế | Điểm mạnh | Đánh đổi |
| --- | --- | --- | --- |
| LangGraph | Graph + state machine | Kiểm soát flow tốt nhất; checkpoint, replay, human-in-the-loop | Học dốc hơn; code dài hơn |
| AutoGen | Conversational multi-agent | Demo hội thoại giữa các agent nhanh nhất | Khó kiểm soát hội thoại dài; token khó đoán |
| CrewAI | Role-based crews | Map tự nhiên với business flow (PM, dev, QA) | Ít linh hoạt với flow phức tạp |
| OpenAI Swarm/Agents SDK | Handoff + as_tool mỏng | API nhỏ, dễ hiểu cơ chế gốc | Ecosystem ít hơn; pattern có hạn |

Đây là heuristic theo kinh nghiệm, không phải quy tắc cứng — nếu team bạn đã quen một framework và nó đủ kiểm soát flow, dùng tiếp là lựa chọn hợp lý.

Khuyến nghị của bài này: **tự dựng supervisor bằng OpenAI SDK thuần trước, rồi mới sang framework**. Lý do nằm ở chỗ debug: framework giấu vòng lặp tool-call bên trong API của nó. Khi pipeline hỏng, người sửa cần biết vòng lặp đó chạy thế nào — state nằm ở đâu, tool-call hỏng chỗ nào, vòng lặp dừng khi nào. Bản dựng ~120 dòng dưới đây chính là vòng lặp mà LangGraph hay CrewAI bọc lại theo cách riêng của chúng.

### Cạm bẫy multi-agent

Bốn thất bại lặp lại nhiều nhất khi đội agent vận hành thật:

1. **Giao tiếp gây nhiễu.** Mỗi agent thêm output vào context chung; sau vài vòng, model bị nhiễu bởi chính văn bản do agent sinh ra.
2. **Chi phí nhân.** N agent × K vòng — một debate N=3, K=2 là ít nhất sáu lần gọi model cho một câu hỏi.
3. **Debugging khó.** State phân tán giữa các agent, model có tính ngẫu nhiên — lỗi không tái hiện được bằng chạy lại.
4. **Lỗi lan truyền.** Researcher sai một số liệu, writer viết cả bài trên số liệu sai, không ai phát hiện.

Giảm thiểu bằng bốn nguyên tắc, áp dụng được cho mọi kiến trúc phía trên:

| Nguyên tắc | Cách làm cụ thể |
| --- | --- |
| Mỗi agent một vai trò hẹp | Một system prompt một nhiệm vụ; writer không kiêm fact-check |
| Contract đầu-ra rõ | JSON schema cố định: field nào, kiểu gì, bắt buộc gì |
| Supervisor là nơi duy nhất ra quyết định | Specialist chỉ trả dữ liệu; nhánh if-else nằm ở supervisor |
| Giới hạn vòng, log từng bước | max_rounds cứng; log mỗi tool-call để tái hiện lỗi |

Nguyên tắc thứ ba quan trọng nhất: quyền ra quyết định ở một điểm duy nhất thì hệ thống có một nơi để đặt guardrail, một nơi để audit, một nơi để sửa khi sai.

#### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Specialist trả text không phải JSON | Prompt chưa chốt "CHỈ trả JSON" đủ cứng | Thêm `response_format={"type": "json_object"}` ở cả specialist; supervisor validate JSON nhận về trước khi dùng |
| Supervisor tự viết bài thay vì gọi specialist | System prompt chưa cấm tự viết | Thêm "TUYỆT ĐỐI không tự viết bài" vào SYSTEM; soát log để chắc supervisor có gọi tool thật |
| Vòng không dừng — specialist trả lỗi, supervisor gọi lại mãi | Không có giới hạn vòng cứng | Đặt `max_rounds` cứng; khi hết vòng supervisor phải báo lỗi rõ cho người dùng thay vì dừng im lặng |

### Code thực hành: supervisor pattern với OpenAI SDK

Môi trường: `pip install openai`, hai biến môi trường `OPENAI_API_KEY` và `OPENAI_MODEL` (ví dụ `gpt-4.1`). Supervisor chỉ điều phối qua hai tool (`call_researcher`, `call_writer`); mỗi specialist là một function gọi LLM riêng với system prompt riêng. Specialist không biết nhau tồn tại — đúng theo sơ đồ ở trên.

> **Bản chạy được:** file Python hoàn chỉnh cho bài này nằm trong [starter kit](/starter/ai-agent-architecture/) — kèm mock mode (chạy không cần API key) và self-test, hướng dẫn cài đặt trong [README](/starter/ai-agent-architecture/README.md).

```python
import json
import os

from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ---------- Specialist 1: Researcher ----------
def researcher(topic: str) -> str:
    """Thu thập điểm chính, số liệu, rủi ro — trả JSON theo contract."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là researcher. Với chủ đề được cho, trả về JSON gồm: "
                    "key_points (5 điểm chính), numbers (3 số liệu đáng chú ý), "
                    "risks (2 rủi ro). CHỈ trả JSON, không thêm chữ nào khác."
                ),
            },
            {"role": "user", "content": f"Chủ đề: {topic}"},
        ],
    )
    return resp.choices[0].message.content


# ---------- Specialist 2: Writer ----------
def writer(topic: str, research_json: str) -> str:
    """Biến kết quả nghiên cứu thành bài phân tích hoàn chỉnh."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là writer. Dùng dữ liệu JSON từ researcher, viết bài "
                    "phân tích khoảng 300 từ: mở đầu nêu bối cảnh, thân bài dẫn "
                    "số liệu cụ thể, kết bài nêu rủi ro. Không bịa số liệu ngoài JSON."
                ),
            },
            {"role": "user", "content": f"Chủ đề: {topic}\nDữ liệu: {research_json}"},
        ],
    )
    return resp.choices[0].message.content


# ---------- Supervisor: chỉ điều phối qua tool ----------
SUPERVISOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_researcher",
            "description": "Gọi agent researcher thu thập điểm chính, số liệu, rủi ro cho một chủ đề.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_writer",
            "description": "Gọi agent writer viết bài phân tích từ dữ liệu JSON đã có.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "research_json": {"type": "string"},
                },
                "required": ["topic", "research_json"],
            },
        },
    },
]

SYSTEM = (
    "Bạn là supervisor điều phối đội specialist. Quy trình bắt buộc: "
    "1) call_researcher để lấy dữ liệu. "
    "2) call_writer để viết bài từ dữ liệu. "
    "3) Trả bài viết cho người dùng. Tuyệt đối không tự viết bài."
)


def run_supervisor(task: str, max_rounds: int = 6) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": task},
    ]
    for _ in range(max_rounds):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=SUPERVISOR_TOOLS
        )
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:  # supervisor đã trả lời xong
            return msg.content

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            if call.function.name == "call_researcher":
                result = researcher(args["topic"])
            else:
                result = writer(args["topic"], args["research_json"])
            print(f"[supervisor] gọi {call.function.name}")
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )
    return "Supervisor dừng: vượt số vòng cho phép."


if __name__ == "__main__":
    print(
        run_supervisor(
            "Viết bài phân tích thị trường GPU cloud cho ngành logistics tại Việt Nam"
        )
    )
```

Chạy ví dụ trên, supervisor làm đúng ba bước: gọi researcher, nhận JSON về, gọi writer với dữ liệu đó, trả bài viết. Ba điểm cần nhìn khi đọc log: mọi quyết định (gọi ai, khi nào, gọi thêm không) nằm ở supervisor; specialist có contract đầu ra cố định — researcher trả JSON ba field, writer bị cấm bịa số liệu ngoài JSON nhận vào; vòng lặp có điểm dừng cứng qua `max_rounds`. Khi bản dựng này chạy ổn, chuyển sang LangGraph hay CrewAI chỉ là đổi cách viết state và flow, không đổi cách nghĩ.

> 📍 **Dự án xuyên suốt — DocMind:** multi-agent là phần mở rộng của DocMind, không phải mặc định. DocMind chạy supervisor chỉ khi task đòi research nhiều nguồn rồi viết dài — phần lớn truy vấn tài liệu vẫn đi qua agent đơn của bài 1-2, rẻ và dễ debug hơn.

### Bài tập tự làm (3 mức)

- **Mức 1 — Làm theo:** thêm specialist thứ ba `fact_checker` nhận `research_json`, trả JSON đã sửa; sửa `SYSTEM` để supervisor buộc gọi researcher → fact_checker → writer đúng thứ tự đó.
- **Mức 2 — Tự sửa:** thay supervisor bằng handoff — researcher chuyển quyền thẳng cho writer khi xong; chạy cùng một task, so output cuối và số token của hai cách.
- **Mức 3 — Mở rộng:** đặt `max_rounds = 2` trên task đòi ba bước, viết fallback — khi hết vòng, supervisor trả message rõ ràng cho người dùng ("chưa hoàn thành vì X") thay vì dừng im lặng. Chỉ thêm tầng này vào DocMind khi bài viết cần research dài — một agent đơn giản đủ cho phần lớn truy vấn.

### Tài liệu gốc

- Microsoft — AI Agents for Beginners, bài 8 (Agentic Design Patterns): [github.com/microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners)
- all-agentic-architectures (Debate, Blackboard, STORM, Mixture of Agents): [github.com/FareedKhan-dev/all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures)
- Nir Diamant — GenAI Agents (notebook multi-agent từng kiến trúc): [github.com/NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents)
- Trên LearnWithHuy: [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te) — bản dịch guide OpenAI, có chi tiết `as_tool` và handoff; [Nền tảng agent và agent loop](/bai-viet/kien-truc-ai-agent-cam-nang) — vòng lặp single-agent là nền của mọi thứ trong bài này.

---

## 06. RAG trong agent: từ Agentic RAG đến GraphRAG

Bài [Nền tảng agent và agent loop](/bai-viet/kien-truc-ai-agent-cam-nang) đã dựng agent với vòng lặp tools; bài [Multi-agent orchestration](/bai-viet/kien-truc-ai-agent-cam-nang) đã tách đội agent. Bài này quay về một tool mà gần như mọi hệ agent đều phải có: retrieve dữ liệu. Câu hỏi không phải "RAG là gì" — mà là **ai ra quyết định trong RAG**: pipeline hay agent. Hệ agent hiện đại trả lời: agent. Retrieve chỉ là một tool, và chất lượng câu trả lời phụ thuộc vào việc agent quyết định tool đó thế nào.

### Vấn đề của RAG cổ điển trong agent

RAG cổ điển là pipeline cố định: chunk tài liệu → embed → retrieve top-k → nhét context → generate. Pipeline này chạy như thế nào thì chạy như vậy, cho dù query có cần retrieve hay không. Ba mù điểm lặp lại trong mọi hệ RAG theo pipeline:

1. **Không hỏi query có cần retrieve hay không.** Câu chào hỏi, câu hỏi kiến thức chung, câu hỏi về chính cuộc hội thoại — vẫn bị dọn top-k chunk tốn token mà không giúp gì.
2. **Không kiểm tra tài liệu tốt không.** Top-k là top theo similarity, không phải theo chất lượng; đoạn văn sai lệch nhưng tương đồng cao vẫn được dùng nguyên xi.
3. **Retrieve một lần là đủ hay chưa.** Câu hỏi multi-hop — "giám đốc công ty sở hữu nhà máy X đang làm gì" — cần retrieve hai lần trở lên; pipeline cố định chỉ fetch một đợt rồi chịu.

> **Trong hệ agent, RAG không phải pipeline mà là một chuỗi quyết định: có retrieve hay không, dùng tài liệu nào, có retrieve lại không, đủ dữ liệu để trả lời chưa.**

Năm kiến trúc dưới đây trả lời năm câu hỏi đó, mỗi cái một cách.

### Năm kiến trúc RAG trong hệ agent

Cả năm thuộc family "Retrieval (RAG)" trong [all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures).

#### 1. Agentic RAG

Agent tự quyết định khi nào retrieve và lấy gì. Retrieve trở thành tool `search_docs` trong vòng lặp: agent đọc câu hỏi, quyết gọi hay không, đọc kết quả, quyết dùng hay gọi tiếp. Không có paper riêng — đây là sự kết hợp tự nhiên giữa agent loop và RAG, và là nền của bốn kiến trúc còn lại. Quyết định dừng nằm trong tay model, không phải trong code.

#### 2. Corrective RAG (CRAG) — Yan et al., 2024

Chấm điểm tài liệu, kém thì sửa. Một retriever evaluator (paper gốc là T5-based) chấm từng tài liệu retrieved vào ba mức: Correct, Incorrect, Ambiguous. Tài liệu Correct đi thẳng vào sinh câu trả lời; Incorrect bị bỏ, query được viết lại rồi gọi **web search** lấy nguồn ngoài; Ambiguous được tinh chỉnh bằng cách tách và lọc. Điểm khác biệt lớn nhất: CRAG có đường fallback ra ngoài knowledge base — tài liệu nội bộ kém thì lấy web, thay vì sinh câu trả lời trên nền tài liệu rác.

#### 3. Self-RAG — Asai et al., 2024

Model tự phản tư từng bước bằng reflection token. Self-RAG huấn luyện model sinh các token đặc biệt: `Retrieve?` (có cần retrieve không), rồi sau mỗi đoạn retrieved là `ISREL` (relevance), `ISSUP` (câu trả lời có dựa trên tài liệu không), `ISUSE` (đoạn trả lời có hữu ích không). Từng tài liệu được đánh giá riêng: dùng, bỏ, hoặc đánh giá lại. Khác CRAG ở chỗ việc đánh giá không phải một component ngoài pipeline mà nằm trong chính model — sát hơn nhưng đắt hơn vì phải huấn luyện. Không huấn luyện model riêng, người ta xấp xỉ bằng một LLM chấm từng tài liệu và một LLM phản tư bản nháp.

#### 4. Adaptive RAG — Jeong et al., 2024

Route theo độ phức tạp của query. Một classifier đánh giá query rồi điều hướng: query đơn giản mà model biết sẵn → không retrieve; query cần dữ liệu → retrieve một lần; query multi-hop phức tạp → retrieve lặp nhiều nhịp. Trong hệ agent, classifier có thể chính là agent: nó đọc câu hỏi và chọn tool phù hợp — trả lời trực tiếp, `search_docs` một lần, hay chuỗi retrieve-giữa-các-bước.

#### 5. GraphRAG — Microsoft Research, 2024

Thay chunk thuần bằng knowledge graph và community summary. Vector RAG trả lời tốt câu hỏi tìm một fact ("mức phí X là bao nhiêu") nhưng kém với câu hỏi tổng hợp ("so sánh các đối thủ theo khía cạnh giá, công nghệ và đối tác") — dữ kiện cần nằm rải rác ở nhiều chunk mà top-k không gom đủ để tổng hợp. GraphRAG index tài liệu thành graph thực thể + quan hệ, chia cụm và tóm tắt từng cụm; câu hỏi tổng hợp được trả lời bằng cách đi qua các summary. Chi tiết ở phần "Cấu trúc GraphRAG" bên dưới.

Bảng gộp năm kiến trúc trước khi chuyển sang phần chọn:

| Kiến trúc | Nguồn | Ai đánh giá tài liệu | Điểm khác biệt chính |
| --- | --- | --- | --- |
| Agentic RAG | Pattern, không paper | Agent tự quyết dùng/bỏ/gọi lại | Retrieve là tool, điểm dừng do model |
| Corrective RAG | Yan et al. 2024 | Retriever evaluator ngoài pipeline | Kém → rewrite query + web search |
| Self-RAG | Asai et al. 2024 | Model tự sinh reflection token | Đánh giá nằm trong model, cần huấn luyện |
| Adaptive RAG | Jeong et al. 2024 | Classifier route theo độ phức tạp | Không retrieve / một lần / multi-hop tùy query |
| GraphRAG | Microsoft 2024 | Community summaries | Index là graph, mạnh cho câu hỏi tổng hợp |

#### Bảng chọn theo loại câu hỏi

| Loại câu hỏi | Kiến trúc phù hợp | Lý do |
| --- | --- | --- |
| Fact đơn giản, tài liệu nội bộ rõ | Plain RAG hoặc Agentic RAG | Retrieve một lần là đủ; thêm cơ chế chỉ tốn phí |
| Cần kiểm soát đúng/sai, nguồn thiếu tin cậy | CRAG hoặc Self-RAG | Chấm điểm tài liệu + đường fallback khi tài liệu kém |
| Query trộn lẫn độ khó, chitchat đến multi-hop | Adaptive RAG | Route theo độ phức tạp, không retrieve thứ không cần |
| Hỏi quan hệ, tổng hợp nhiều thực thể | GraphRAG | Community summary gom nổi quan hệ mà chunk rời rạc không gom được |

Hai kiến trúc có thể xếp chồng: hệ thực tế thường là Agentic RAG làm nền, CRAG cài làm phần chấm điểm bên trong, Adaptive RAG ở tầng routing đầu vào.

### Code thực hành: Agentic RAG với fallback web (mini-CRAG)

Bản dựng dưới đây là Agentic RAG đúng nghĩa: hai tool — `search_kb` tìm trong knowledge base nội bộ, `web_search` lấy nguồn ngoài. System prompt bắt buộc agent chấm relevance; điểm thấp thì fallback ra web. Đó chính là tinh thần CRAG, thu gọn trong ~100 dòng. Môi trường: `pip install openai`, `export OPENAI_API_KEY=...` (model mặc định `gpt-4o-mini`, đổi qua `OPENAI_MODEL`).

> **Bản chạy được:** file Python hoàn chỉnh cho bài này nằm trong [starter kit](/starter/ai-agent-architecture/) — kèm mock mode (chạy không cần API key) và self-test, hướng dẫn cài đặt trong [README](/starter/ai-agent-architecture/README.md).

```python
import json
import os

from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

KB = [
    {
        "id": "kb-001",
        "title": "Agentic RAG là gì",
        "text": "Agentic RAG là kiến trúc trong đó agent tự quyết định khi nào gọi "
        "tool retrieve, lấy dữ liệu từ nguồn nào, và có retrieve lại hay không. "
        "Retrieve chỉ là một tool trong vòng lặp agent.",
    },
    {
        "id": "kb-002",
        "title": "Corrective RAG (CRAG)",
        "text": "CRAG (Yan et al. 2024) chấm điểm từng tài liệu retrieved vào ba "
        "mức Correct, Incorrect, Ambiguous. Tài liệu điểm kém bị thay bằng web "
        "search sau khi rewrite query. Tài liệu điểm tốt đi thẳng vào sinh câu trả lời.",
    },
    {
        "id": "kb-003",
        "title": "GraphRAG của Microsoft",
        "text": "GraphRAG (Microsoft 2024) xây knowledge graph từ tài liệu: extract "
        "entities và relations, chia cụm bằng community detection, tóm tắt mỗi cụm "
        "thành summaries nhiều tầng để trả lời câu hỏi tổng hợp quan hệ.",
    },
    {
        "id": "kb-004",
        "title": "Chính sách hoàn tiền nội bộ",
        "text": "Khách hàng được hoàn tiền trong 30 ngày kể từ ngày thanh toán. "
        "Yêu cầu hoàn tiền qua email kèm mã đơn hàng. Bộ phận tài chính xử lý "
        "trong 5 ngày làm việc.",
    },
]


def search_kb(query: str) -> str:
    """Giả lập vector search: điểm = tỉ lệ từ khớp. Thực tế dùng embedding."""
    q = set(query.lower().split())
    scored = []
    for doc in KB:
        words = set((doc["title"] + " " + doc["text"]).lower().split())
        score = len(q & words) / max(len(q), 1)
        scored.append((round(score, 2), doc))
    scored.sort(key=lambda x: -x[0])
    return json.dumps(
        [
            {"id": d["id"], "title": d["title"], "text": d["text"], "relevance": s}
            for s, d in scored[:2]
        ],
        ensure_ascii=False,
    )


def web_search(query: str) -> str:
    """Fallback ngoài KB. Thực tế: gọi API search thật (Tavily, SerpAPI...)."""
    return json.dumps({"source": "web", "result": f"(giả lập) kết quả web cho: {query}"})


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Tìm tài liệu trong knowledge base nội bộ. Trả về 2 doc kèm relevance score.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Tìm trên web. CHỈ dùng khi mọi tài liệu trong KB có relevance thấp.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]

SYSTEM = (
    "Bạn là agent RAG. Quy trình bắt buộc:\n"
    "1) Nếu câu hỏi cần dữ liệu ngoài, gọi search_kb.\n"
    "2) Chấm relevance của tài liệu: dưới 0.2 coi là kém.\n"
    "3) Nếu mọi tài liệu kém, gọi web_search với query đã viết lại rõ ràng hơn.\n"
    "4) Trả lời chỉ dựa trên dữ liệu đã lấy. Nếu vẫn không đủ, nói rõ "
    "'không đủ dữ liệu' — tuyệt đối không đoán."
)


def run_rag_agent(question: str, max_rounds: int = 5) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    for _ in range(max_rounds):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS
        )
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:  # agent đã có câu trả lời
            return msg.content

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            if call.function.name == "search_kb":
                result = search_kb(args["query"])
            else:
                result = web_search(args["query"])
            print(f"[tool] {call.function.name}({args['query']!r})")
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )
    return "Dừng: vượt số vòng cho phép."


if __name__ == "__main__":
    # Trúng KB: agent gọi search_kb, relevance cao, trả lời luôn.
    print(run_rag_agent("CRAG xử lý thế nào khi tài liệu retrieved kém?"))
    # Hỏng KB: relevance thấp → agent phải rơi xuống web_search. Đây là mini-CRAG.
    print(run_rag_agent("Thủ tướng Singapore hiện tại là ai?"))
```

Chạy hai câu hỏi mẫu sẽ thấy hai hành vi khác nhau. Câu đầu trúng KB: một lần `search_kb` với relevance cao là agent trả lời, không gọi web. Câu thứ hai không có gì trong KB: relevance về 0, agent viết lại query và gọi `web_search` — đúng đường fallback của CRAG, chỉ khác là chấm điểm và quyết định nằm trong tay model thay vì một component cố định. Relevance score đi cùng mỗi doc để agent chấm bằng số chứ không cảm tính; `max_rounds` chặn agent retrieve vô hạn.

Để thấy agent khác gì pipeline, đối chiếu với bản RAG cổ điển đúng nghĩa — luôn retrieve, không hỏi, không chấm (dùng cho bài tập 3):

```python
def plain_rag(question: str) -> str:
    """RAG cổ điển: retrieve luôn, không quyết định gì cả."""
    docs = json.loads(search_kb(question))  # luôn gọi, dù có cần hay không
    context = "\n".join(f"- {d['text']}" for d in docs)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Trả lời dựa trên context sau."},
            {"role": "user", "content": f"Context:\n{context}\n\nCâu hỏi: {question}"},
        ],
    )
    return resp.choices[0].message.content
```

#### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Relevance score lệch khi demo | Mock dùng keyword overlap, không phải embedding | Hiểu đây là giả lập; thay bằng vector search thật khi lên production |
| Agent retrieve vô hạn | Không có điều kiện dừng khi dữ liệu kém | Đặt `max_rounds` cứng + rule "sau N lần vẫn kém thì trả 'không đủ dữ liệu'" |
| Agent trả lời ngoài tài liệu | System prompt chưa cấm đoán | Prompt phải có "trả lời chỉ dựa trên dữ liệu đã lấy, không đoán"; thêm eval test câu hỏi ngoài KB |

### Cấu trúc GraphRAG

GraphRAG đáng một bài riêng (đã có: [GraphRAG — knowledge graph cho RAG](/bai-viet/rag-nang-cao-cam-nang)), nhưng cấu trúc index cần nằm trong đầu khi chọn kiến trúc. Bốn bước:

1. **Extract entities và edges.** Mỗi chunk được LLM đọc để trích thực thể (công ty, con người, sản phẩm, sự kiện) và quan hệ giữa chúng, kèm mô tả và độ mạnh.
2. **Build graph.** Thực thể trùng hợp nhất thành node, quan hệ thành cạnh — kết quả là knowledge graph thay cho danh sách chunk.
3. **Community detection.** Thuật toán Leiden chia graph thành các cụm thực thể liên kết chặt, mỗi cụm đại diện một chủ đề tự nhiên.
4. **Community summaries.** Mỗi cụm được LLM tóm tắt; cụm của cụm cũng được tóm tắt, tạo thành các tầng summary từ nhỏ đến to.

```
  Tài liệu gốc
       │
       ▼
  chunk văn bản
       │
       ▼
  LLM extract: entities + relations (edges)
       │
       ▼
  Knowledge graph (node = thực thể, edge = quan hệ)
       │
       ▼
  Community detection (Leiden) → cụm thực thể liên quan
       │
       ▼
  Community summaries nhiều tầng (tóm tắt cụm, tóm tắt cụm của cụm)
       │
       ├─ Local search: hỏi về thực thể cụ thể → node + cạnh kề + doc gốc
       └─ Global search: câu hỏi tổng hợp → map-reduce qua summaries
```

Trade-off nằm rõ ở hai đầu. **Đầu index:** mỗi chunk cần ít nhất một lần gọi LLM để extract, cộng thêm tóm tắt mỗi cụm — đắt hơn vector index nhiều lần, và phải chạy lại mỗi khi tài liệu thay đổi. **Đầu query:** global search đi qua toàn bộ summaries bằng map-reduce, đắt hơn một lần vector search. Đổi lại là khả năng trả lời câu hỏi tổng hợp quan hệ mà vector RAG trả lời sai hoặc hụt — các dữ kiện rải rác được gom vào summary trước khi gặp câu hỏi, không phải lúc gặp câu hỏi.

Quy tắc thực dụng: bắt đầu bằng Agentic RAG trên vector index; chỉ thêm GraphRAG cho phần câu hỏi tổng hợp, hoặc cho toàn hệ thống nếu nghiệp vụ sống bằng những câu hỏi "so sánh" và "liên hệ giữa".

> 📍 **Dự án xuyên suốt — DocMind:** sau bài này DocMind trả lời trên knowledge base thật: tự quyết khi nào retrieve, chấm relevance, fallback ra web khi KB hụt, và nói "không đủ dữ liệu" thay vì bịa — đây là phần khiến DocMind dùng được thực tế.

### Bài tập tự làm (3 mức)

- **Mức 1 — Làm theo:** tách `grade_docs` thành tool thật — thêm tool `grade_docs(docs)` trả về danh sách doc kèm điểm từ một LLM chấm riêng, sửa `SYSTEM` để agent bắt buộc gọi trước khi dùng tài liệu; mini-CRAG thành thật thay vì chỉ dựa vào relevance score.
- **Mức 2 — Tự sửa:** đếm số lần `search_kb`; sau hai lần vẫn không có tài liệu đạt thì agent trả "không đủ dữ liệu" kèm những gì đã thử. Chạy lại câu hỏi hỏng KB và so hành vi.
- **Mức 3 — Mở rộng:** chạy ba query (fact trong KB, fact ngoài KB, câu hỏi tổng hợp "liên hệ giữa CRAG và web search trong tài liệu"), ghi agent gọi tool nào mấy lần, so với plain RAG retrieve-luôn. Cài vào DocMind — KB nội bộ hiện là mock, thay bằng tài liệu công ty thật của bạn.

### Tài liệu gốc

- all-agentic-architectures (family Retrieval: Agentic, Corrective, Self, Adaptive, GraphRAG): [github.com/FareedKhan-dev/all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures)
- Nir Diamant — GenAI Agents (notebook CRAG, Self-RAG, Adaptive RAG từng cái một): [github.com/NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents)
- Microsoft AI Agents for Beginners: [github.com/microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners)
- Papers: Corrective RAG (Yan et al. 2024, arXiv 2401.15884) — Self-RAG (Asai et al. 2024, arXiv 2310.11511) — Adaptive RAG (Jeong et al. 2024, arXiv 2403.14403) — GraphRAG (Microsoft Research 2024, arXiv 2404.16130)
- Trên LearnWithHuy: [GraphRAG — knowledge graph cho RAG](/bai-viet/rag-nang-cao-cam-nang), [Hybrid search: BM25 + dense + RRF](/bai-viet/rag-nang-cao-cam-nang) — tầng retrieval mà mọi kiến trúc trên đều đứng trên, [Đánh giá chất lượng RAG với RAGAS](/bai-viet/rag-nang-cao-cam-nang) — đo được mới biết kiến trúc nào đáng chuyển, và [Nền tảng agent và agent loop](/bai-viet/kien-truc-ai-agent-cam-nang).

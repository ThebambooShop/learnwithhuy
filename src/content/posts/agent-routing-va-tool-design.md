---
title: "Tool use và Routing: hai pattern nền tảng của agent"
description: "Hai pattern phổ biến nhất trong kiến trúc agent: routing một lượt để điều hướng request, và tool use đúng cách — từ thiết kế schema đến quy tắc naming — kèm code thực hành chạy được."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-22"
cover: "/images/covers/posts/agent-routing-va-tool-design.jpg"
featured: false
views: 300
faq:
  - q: "Routing khác một agent đầy đủ như thế nào?"
    a: "Routing là một lượt forward pass duy nhất: model chọn 1 route và trả kèm confidence, không gọi tool, không lặp. Agent chạy vòng lặp nhiều lượt với tool calls. Vì vậy routing rẻ, nhanh, dễ kiểm soát — phù hợp làm gateway phân loại trước khi quyết định gọi model đắt hay agent nào xử lý."
  - q: "Tool call có gì ma thuật không?"
    a: "Không. Tool call chỉ là structured output: model xuất JSON đúng schema bạn mô tả. Code của bạn đọc JSON đó, thực thi hàm thật, trả kết quả về context. Hiểu vậy giúp debug hiệu quả: model chọn sai tool là lỗi mô tả tool, không phải lỗi model."
  - q: "Đặt tên tool thế nào là tốt?"
    a: "Động từ rõ + đối tượng cụ thể: get_weather, refund_order — không dùng api_call_1 hay do_stuff. Mô tả phải nói rõ tool làm gì, khi nào dùng, và edge case nào (không tìm thấy dữ liệu, trạng thái không hợp lệ). Một tool chỉ nên làm đúng một việc."
  - q: "Tool gặp lỗi nên throw exception hay trả chuỗi lỗi?"
    a: "Trả chuỗi lỗi đọc được về context để model tự sửa: thử lại, đổi tham số, hoặc xin lỗi người dùng. Throw exception làm chết cả agent loop. Chỉ throw khi lỗi nghiêm trọng (thiếu quyền, lỗi hệ thống) và bạn muốn chặn ngay."
---

Bài trước bạn đã tự tay viết agent loop khoảng 100 dòng không framework. Bài này đi vào hai pattern bạn sẽ gặp gần như trong mọi hệ thống agent: **routing** để điều hướng request một cách rẻ, và **tool use** để agent đọc dữ liệu và hành động. Cả hai đều có code chạy được ngay trong bài.

Đây là hai pattern nằm trong notebook của kho [GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) và bài 4 của khóa [Microsoft ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) — chọn đúng nguồn vì đây là hai pattern lặp lại nhiều nhất khi tôi đọc hệ thống agent thật.

## Routing pattern

> **Routing là một lượt forward pass duy nhất: model đọc request, chọn 1 trong các route định sẵn và trả về route kèm confidence. Không gọi tool, không lặp, không nhiều lượt.**

Notebook "Routing" trong GenAI_Agents xây đúng vậy. Sự khác biệt với agent: agent có vòng lặp và tool calls, số lượt gọi LLM không biết trước; routing chỉ một lần gọi rồi trả kết quả, chi phí và độ trễ biết trước.

Ba tình huống nên dùng routing thay vì full agent:

- **Phân loại intent**: ticket khách hàng → support / billing / technical. Model làm một việc duy nhất: chọn nhãn.
- **Gateway rẻ trước model đắt**: model nhỏ chốt route; chỉ request khó mới lên model lớn hoặc agent đầy đủ. Đây là cách tiết kiệm chi phí phổ biến nhất trong production.
- **Điều hướng multi-agent**: quyết định agent nào tiếp nhận trước khi handoff — routing là bước tiền xử lý của kiến trúc đa agent.

Quy tắc gọn: routing là tầng rẻ nhất trong stack. Phần lớn request đi qua router để bị loại sớm; chỉ phần nhỏ khó mới xuống tới model đắt hay agent đầy đủ.

Code thực hành — router trả enum + confidence bằng structured output:

```python
# router.py — phân loại intent, một lượt gọi LLM
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

## Tool use pattern

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

## Thiết kế tool tốt

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

## 12-factor #4 — tools are just structured outputs

Đây là factor #4 của [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) và là điểm nhiều người bỏ qua lần đầu đọc: **tool call không có gì ma thuật — nó chỉ là JSON có cấu trúc model xuất ra**, giống hệt structured output của router ở đầu bài. Cùng một cơ chế, hai cách dùng: một lượt (routing) hay nhiều lượt (agent loop).

Hệ quả debug cực mạnh:

- Model chọn sai tool → sửa tên hoặc mô tả tool (đó là sửa prompt), không phải "fix model".
- Model điền sai tham số → schema chưa rõ: thêm description tham số, dùng enum cho giá trị cố định, đánh dấu `required`.
- Model gọi tool không tồn tại → registry trả lỗi mềm, model tự chỉnh ở lượt sau.
- Tool trả kết quả vô nghĩa → model phải đoán; thêm mô tả format kết quả vào description.

Ví dụ thực tế: model gọi `get_weather` nhưng thành phố không có dữ liệu — tool trả `{'error': 'city_not_found'}`. Model đọc chuỗi này như một tool result bình thường, rồi tự quyết định xin lỗi người dùng hay đổi cách hỏi. Không exception, không restart, loop vẫn chạy.

Nhìn tool call như structured output, mọi lỗi model-điểm-tool đều quy về một thứ duy nhất bạn có thể sửa: schema và mô tả.

## Pattern nào dùng khi nào

Ba pattern đã học qua 2 bài, đặt cạnh nhau để chọn nhanh:

| Pattern | Số lượt LLM | Chi phí | Dùng khi |
| --- | --- | --- | --- |
| **Routing** | 1 lượt, không tool | Rất thấp | Phân loại intent, gateway rẻ, điều hướng multi-agent |
| **Tool use agent** | Nhiều lượt lặp | Cao hơn | Cần tra dữ liệu + hành động, trình tự không biết trước |
| **Workflow** | 1 call mỗi bước, cố định | Tất định, audit được | Bước cố định, cần kiểm soát từng điểm |

Ba pattern không loại trừ nhau. Hệ thống production thường layered: router chặn ở cổng → route đơn giản đi workflow tất định → route khó mới vào agent đầy đủ. Chi phí giảm, độ dự đoán tăng, và phần mơ hồ chỉ dành phần mềm agent cho đúng chỗ nó cần.

Thứ tự khuyến nghị khi mới bắt đầu: dựng router trước (một buổi chiều là xong), thêm workflow cho route phổ biến, và chỉ viết agent cho route mà workflow không bọc nổi.

## Bài tập tự làm

1. **Router theo ngưỡng**: thêm logic `confidence < 0.7 → escalate_to_human` vào `route_ticket`. Viết 10 ticket test, đếm router chọn đúng bao nhiêu — đây là eval set đầu tiên của bạn.
2. **Schema chặt hơn**: thay `order_id` trong schema của `get_order_status` bằng enum `["DH-101", "DH-102", "DH-201"]`. Thử gọi agent với mã đơn sai và xem model hành xử thế nào trước và sau khi thêm enum.
3. **Tool có business rule**: thêm tool `cancel_order(order_id)` với mô tả "chỉ hủy được đơn đang vận chuyển; đơn đã giao trả lỗi mềm". Kiểm tra model có tự chặn việc hủy đơn đã giao không. Nếu không, sửa mô tả tool — không phải system prompt — rồi so sánh kết quả.

## Tài liệu gốc

- [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) — Lesson 4: Tool Use Design Pattern.
- [NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) — notebooks "Routing" và "Tool design".
- [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) — Factor #4: Tools are just structured outputs.

Đọc tiếp trong series:

- [Nền tảng AI Agent: xây agent loop đầu tiên từ con số 0](/bai-viet/nen-tang-agent-va-agent-loop) — bài mở đầu series: agent loop ~100 dòng không framework.
- [Claude connectors, MCP và sub-agents](/bai-viet/claude-connectors-mcp-sub-agents) — mở rộng kiến trúc tool ra ngoài một process: MCP protocol và sub-agents.

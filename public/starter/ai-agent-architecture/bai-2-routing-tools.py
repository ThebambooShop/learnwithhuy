"""Bài 2 — Tool use và Routing: hai pattern nền tảng của agent | LearnWithHuy — Kiến trúc AI Agent

Chạy mock (KHÔNG cần API key):  python bai-2-routing-tools.py
Chạy live:  export OPENAI_API_KEY=... && python bai-2-routing-tools.py
Giải thích đầy đủ: /bai-viet/agent-routing-va-tool-design
"""
import json
import os
import types

MOCK = not os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# --- Routing: một lượt forward pass — model chọn 1 route, không gọi tool ---

ROUTES = ["support", "billing", "technical", "other"]

SYSTEM_PROMPT = """Bạn là router phân loại intent của ticket khách hàng.
Chọn đúng MỘT route và trả về JSON.
Nếu không chắc chắn (confidence dưới 0.7) thì chọn 'other'."""


def normalize_route(result: dict) -> dict:
    """Guardrail thuần (tách hàm để self_test không cần API)."""
    if result.get("route") not in ROUTES:
        return {"route": "other", "confidence": float(result.get("confidence", 0.0))}
    return result


def get_client():
    from openai import OpenAI  # import muộn: mock mode không cần cài openai

    return OpenAI()  # SDK tự đọc OPENAI_API_KEY từ environment


def route_ticket(message: str, _client=None) -> dict:
    """Router: một lượt gọi LLM với structured output, trả route + confidence."""
    client = _client if _client is not None else get_client()
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},  # ép model luôn trả JSON
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Ticket: {message}\nRoutes khả dụng: {', '.join(ROUTES)}\n"
                    'Trả về JSON: {"route": "<tên route>", "confidence": <0..1>}'
                ),
            },
        ],
    )
    result = json.loads(response.choices[0].message.content)
    # Giá trị model xuất là dữ liệu, không phải lời hứa — vẫn validate ở code
    return normalize_route(result)


# --- 1. Ba tool thật: data, data, action — trả lỗi mềm, không throw ---


def search_orders(email: str) -> str:
    db = {"an@example.com": ["DH-101", "DH-102"], "binh@example.com": ["DH-201"]}
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


# --- 2. Schema cho từng tool: tên là động từ + đối tượng ---

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
            "description": "Xem trạng thái hiện tại của một đơn hàng: đã giao, "
            "đang vận chuyển, hoặc đã hủy.",
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


# --- 3. Dispatch thuần + agent loop — tool mới không đổi loop ---


def execute_tool(name: str, args_json: str) -> str:
    """Tool không tồn tại hoặc args sai -> chuỗi lỗi mềm để model tự chỉnh."""
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return f"Lỗi: tool '{name}' không tồn tại"
    try:
        args = json.loads(args_json)
        return str(fn(**args))
    except Exception as e:  # lỗi mềm -> model tự sửa lượt sau
        return f"Lỗi khi chạy tool: {e}"


def run_agent(user_message: str, max_turns: int = 8, _client=None) -> str:
    """_client chỉ dùng để inject model giả trong self_test — live không đụng."""
    client = _client if _client is not None else get_client()
    messages = [
        {
            "role": "system",
            "content": "Bạn là trợ lý chăm sóc khách hàng. Không đoán dữ liệu — luôn dùng tool.",
        },
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

        # Song song: thực thi TẤT CẢ tool calls của lượt này trước khi gọi model lại
        for call in msg.tool_calls:
            result = execute_tool(call.function.name, call.function.arguments)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    messages.append({"role": "system", "content": "Hết lượt. Trả lời dựa trên thông tin đã có."})
    final = client.chat.completions.create(model=MODEL, messages=messages)
    return final.choices[0].message.content


# --- 4. self_test — assert hành vi cốt lõi, KHÔNG gọi API ---


class _StubModel:
    """Client giả: có tools -> luôn trả tool call; không tools -> trả câu tổng hợp."""

    def __init__(self):
        self.create_calls = 0
        completions = types.SimpleNamespace()
        completions.create = self._create
        self.chat = types.SimpleNamespace(completions=completions)

    def _create(self, model, messages, tools=None):
        self.create_calls += 1
        if tools:
            call = types.SimpleNamespace(
                id="call-1",
                function=types.SimpleNamespace(
                    name="get_order_status", arguments='{"order_id": "DH-101"}'
                ),
            )
            msg = types.SimpleNamespace(content=None, tool_calls=[call])
        else:
            msg = types.SimpleNamespace(
                content="Trả lời từ thông tin đã thu thập.", tool_calls=None
            )
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


def self_test() -> None:
    """Assert hành vi cốt lõi, không gọi API."""
    # (1) Route ngoài enum bị ép về 'other'; route trong enum đi qua nguyên vẹn
    odd = normalize_route({"route": "hoan_tien_gap", "confidence": 0.9})
    assert odd == {"route": "other", "confidence": 0.9}, odd
    ok = normalize_route({"route": "billing", "confidence": 0.95})
    assert ok == {"route": "billing", "confidence": 0.95}, ok

    # (2) search_orders với email lạ: trả chuỗi lỗi mềm, KHÔNG raise
    result = search_orders("khong-ton-tai@example.com")
    assert result.startswith("Không tìm thấy đơn nào cho"), result
    assert "không tồn tại" in execute_tool("tool_lac", '{"email": "a@b.c"}')

    # (3) Agent loop dừng đúng max_turns: model giả LUÔN yêu cầu gọi tool,
    # max_turns=1 phải thoát qua nhánh tổng hợp — không treo, không gọi API
    stub = _StubModel()
    final = run_agent("test", max_turns=1, _client=stub)
    assert final == "Trả lời từ thông tin đã thu thập.", final
    assert stub.create_calls == 2, stub.create_calls  # 1 lượt loop + 1 lượt tổng hợp
    print("self_test: PASS")


def mock_run() -> None:
    """Mock mode: in luồng 2 lượt của ví dụ CSKH trong bài, không gọi API."""
    print(
        "MOCK MODE — chưa có OPENAI_API_KEY. "
        "Chạy live: export OPENAI_API_KEY=sk-... && python bai-2-routing-tools.py"
    )
    print("Luồng 2 lượt của ví dụ CSKH:")
    print(
        'Lượt 1: tool call get_order_status(order_id="DH-101"), '
        'search_orders(email="an@example.com")'
    )
    print("  ->", execute_tool("get_order_status", '{"order_id": "DH-101"}'))
    print("  ->", execute_tool("search_orders", '{"email": "an@example.com"}'))
    print(
        'Lượt 2: "Đơn DH-101 của bạn đã giao. Danh sách đơn của '
        'an@example.com: DH-101, DH-102."'
    )
    print("Số lượt có thể khác nhẹ tùy model.")


if __name__ == "__main__":
    self_test()
    if MOCK:
        mock_run()
    else:
        print(run_agent(
            "Đơn DH-101 của tôi tới đâu rồi? Cho luôn danh sách đơn của an@example.com"
        ))

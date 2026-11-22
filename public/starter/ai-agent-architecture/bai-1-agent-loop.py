"""Bài 1 — Nền tảng AI Agent: agent loop đầu tiên | LearnWithHuy — Kiến trúc AI Agent

Chạy mock (KHÔNG cần API key):  python bai-1-agent-loop.py
Chạy live:  export OPENAI_API_KEY=... && python bai-1-agent-loop.py
Giải thích đầy đủ: /bai-viet/nen-tang-agent-va-agent-loop
"""
import json
import os
import types

MOCK = not os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ------------------------------------------------------------------
# 1. Tools thật: code của bạn thực thi, model chỉ "yêu cầu" gọi
# ------------------------------------------------------------------


def get_weather(city: str) -> str:
    # Demo: dữ liệu cứng. Thực tế: gọi API thật — đổi vài dòng return, loop KHÔNG đổi.
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
                    "city": {"type": "string", "description": "Tên thành phố, ví dụ: 'Hà Nội'"}
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
                    "expression": {"type": "string", "description": "Biểu thức, ví dụ: '22 - 30'"}
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
# 3. Dispatch thuần: tách hàm để self_test chạy được mà KHÔNG cần gọi API
# ------------------------------------------------------------------


def execute_tool(name: str, args_json: str) -> str:
    """Tool không tồn tại hoặc args sai -> chuỗi lỗi đọc được, KHÔNG raise."""
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return f"Lỗi: tool '{name}' không tồn tại"
    try:
        args = json.loads(args_json)
        return str(fn(**args))
    except Exception as e:  # lỗi mềm: đưa vào context để model tự chỉnh
        return f"Lỗi khi chạy tool: {e}"


def get_client():
    from openai import OpenAI  # import muộn: mock mode không cần cài openai

    return OpenAI()  # SDK tự đọc OPENAI_API_KEY từ environment


# ------------------------------------------------------------------
# 4. Agent loop: vòng lặp duy nhất làm nên "agent"
# ------------------------------------------------------------------


def run_agent(user_question: str, max_turns: int = 8, _client=None) -> str:
    """_client chỉ dùng để inject model giả trong self_test — live không đụng."""
    client = _client if _client is not None else get_client()
    messages = [
        {
            "role": "system",
            "content": "Bạn là trợ lý thời tiết. Dùng tools khi cần số liệu thật. Không đoán.",
        },
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

        # Thực thi TẤT CẢ tool calls của lượt này (parallel tool calls)
        for call in msg.tool_calls:
            result = execute_tool(call.function.name, call.function.arguments)
            # Append kết quả vào context, gắn đúng tool_call_id
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    # Nút an toàn: hết max_turns -> ép model tổng hợp từ dữ liệu đã có
    messages.append({
        "role": "system",
        "content": "Hết lượt. Trả lời người dùng dựa trên thông tin đã thu thập.",
    })
    final = client.chat.completions.create(model=MODEL, messages=messages)
    return final.choices[0].message.content


# Variant done flag (run_agent_v2, rút gọn — code đầy đủ trong bài viết):
# thêm DONE_SCHEMA với tool done(report); trong loop, model gọi done ->
# return report ngay làm câu trả lời cuối. Kiểm soát điều kiện dừng rõ nhất ở production.


# ------------------------------------------------------------------
# 5. self_test — assert hành vi cốt lõi, KHÔNG gọi API
# ------------------------------------------------------------------


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
                    name="get_weather", arguments='{"city": "Hà Nội"}'
                ),
            )
            msg = types.SimpleNamespace(content=None, tool_calls=[call])
        else:
            msg = types.SimpleNamespace(
                content="Trả lời từ dữ liệu đã thu thập.", tool_calls=None
            )
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


def self_test() -> None:
    """Assert hành vi cốt lõi của agent, không gọi API."""
    # (1) Tool không tồn tại: fake một call struct như model trả về
    # -> trả CHUỖI lỗi đọc được, không raise
    fake_call = types.SimpleNamespace(
        id="call-x",
        function=types.SimpleNamespace(
            name="tool_chua_dang_ky", arguments='{"city": "Hà Nội"}'
        ),
    )
    result = execute_tool(fake_call.function.name, fake_call.function.arguments)
    assert "không tồn tại" in result and "tool_chua_dang_ky" in result, result

    # (2) Dispatch tool thật trả đúng giá trị
    assert execute_tool("get_weather", '{"city": "Hà Nội"}') == "22°C"
    assert execute_tool("calculate", '{"expression": "22 - 30"}') == "-8"

    # (3) Loop dừng đúng max_turns: model giả LUÔN yêu cầu gọi tool,
    # max_turns=1 phải thoát qua nhánh tổng hợp — không treo, không gọi API
    stub = _StubModel()
    final = run_agent("test", max_turns=1, _client=stub)
    assert final == "Trả lời từ dữ liệu đã thu thập.", final
    assert stub.create_calls == 2, stub.create_calls  # 1 lượt loop + 1 lượt tổng hợp
    print("self_test: PASS")


def mock_run() -> None:
    """Mock mode: in luồng lượt + kết quả đã ghi sẵn trong bài, không gọi API."""
    print(
        "MOCK MODE — chưa có OPENAI_API_KEY. "
        "Chạy live: export OPENAI_API_KEY=sk-... && python bai-1-agent-loop.py"
    )
    print("Luồng thực tế với câu hỏi trong bài:")
    print('Lượt 1: tool call get_weather(city="Hà Nội"), get_weather(city="Đà Nẵng")')
    print("  ->", execute_tool("get_weather", '{"city": "Hà Nội"}'))
    print("  ->", execute_tool("get_weather", '{"city": "Đà Nẵng"}'))
    print('Lượt 2: tool call calculate(expression="22 - 30")')
    print("  ->", execute_tool("calculate", '{"expression": "22 - 30"}'))
    print('Lượt 3: "Hà Nội 22°C, Đà Nẵng 30°C — Hà Nội mát hơn Đà Nẵng 8 độ."')
    print("Số lượt có thể khác nhẹ tùy model.")


if __name__ == "__main__":
    self_test()
    if MOCK:
        mock_run()
    else:
        print(run_agent("Hà Nội nay bao nhiêu độ, nóng hơn Đà Nẵng không?"))

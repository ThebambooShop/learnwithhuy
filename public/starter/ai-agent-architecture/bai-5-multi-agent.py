"""Bài 5 — Multi-agent orchestration: supervisor pattern (starter kit LearnWithHuy).

- MOCK MODE (không cần API key): hai specialist và vòng supervisor chạy bằng
  kịch bản ghi đúng luồng trong bài (call_researcher → call_writer → trả bài). Kèm self_test.
- LIVE MODE (có OPENAI_API_KEY): gọi model thật như code trong bài viết.

Chạy: python bai-5-multi-agent.py
"""

import json
import os
from types import SimpleNamespace

MOCK = not os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not MOCK:
    from openai import OpenAI
    client = OpenAI()

# ---------- Supervisor: contract tool (giống bài viết) ----------
SUPERVISOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_researcher",
            "description": "Gọi agent researcher thu thập điểm chính, số liệu, rủi ro cho một chủ đề.",
            "parameters": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_writer",
            "description": "Gọi agent writer viết bài phân tích từ dữ liệu JSON đã có.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string"}, "research_json": {"type": "string"}},
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


# ---------- Specialist: live mode (gọi LLM thật, logic như bài viết) ----------
RESEARCHER_PROMPT = (
    "Bạn là researcher. Với chủ đề được cho, trả về JSON gồm: "
    "key_points (5 điểm chính), numbers (3 số liệu đáng chú ý), "
    "risks (2 rủi ro). CHỈ trả JSON, không thêm chữ nào khác."
)
WRITER_PROMPT = (
    "Bạn là writer. Dùng dữ liệu JSON từ researcher, viết bài phân tích khoảng "
    "300 từ: mở đầu nêu bối cảnh, thân bài dẫn số liệu cụ thể, kết bài nêu rủi "
    "ro. Không bịa số liệu ngoài JSON."
)


def _llm_text(system: str, user: str) -> str:
    """Một lượt gọi LLM trả text — dùng chung cho hai specialist ở live mode."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content


def _researcher_live(topic: str) -> str:
    return _llm_text(RESEARCHER_PROMPT, f"Chủ đề: {topic}")


def _writer_live(topic: str, research_json: str) -> str:
    return _llm_text(WRITER_PROMPT, f"Chủ đề: {topic}\nDữ liệu: {research_json}")


# ---------- Specialist: mock mode (không gọi API) ----------
def _researcher_mock(topic: str) -> str:
    """Mock researcher: trả đúng JSON contract — 5 điểm, 3 số liệu, 2 rủi ro."""
    return json.dumps(
        {
            "key_points": [
                "Nhu cầu GPU cloud tăng nhanh theo sóng AI nội địa",
                "Logistics cần AI cho tối ưu tuyến, dự báo nhu cầu, OCR chứng từ",
                "Dữ liệu logistics nhạy cảm, ưu tiên hosting trong nước",
                "Thuê GPU theo giờ vẫn đắt hơn server CPU truyền thống",
                "Nhà cung cấp nội địa cạnh tranh bằng VND pricing và hỗ trợ onsite",
            ],
            "numbers": [
                "AI tối ưu tuyến có thể giảm 10-15% chi phí vận hành kho",
                "Thị trường cloud Việt Nam tăng khoảng 25%/năm",
                "Xử lý chứng từ giảm từ 3 ngày xuống vài giờ với OCR + LLM",
            ],
            "risks": [
                "Số liệu lấy từ nguồn công khai, dễ lệch thời điểm",
                "Chưa có khảo sát khách hàng thực tế về mức giá chịu được",
            ],
        },
        ensure_ascii=False,
    )


def _writer_mock(topic: str, research_json: str) -> str:
    """Mock writer: bài phân tích ~150 từ, chỉ dẫn số liệu có trong JSON nhận vào."""
    data = json.loads(research_json)
    points = "; ".join(data["key_points"][:3])
    return (
        f"Bài phân tích: {topic}\n\n"
        "Bối cảnh: sóng AI lan sang logistics Việt Nam, nhu cầu GPU cloud tăng "
        "nhanh cho bài toán tối ưu tuyến, dự báo nhu cầu và số hóa chứng từ. "
        f"Ba điểm nổi bật của thị trường: {points}.\n\n"
        "Về số liệu: AI tối ưu tuyến có thể giảm 10-15% chi phí vận hành kho; "
        "thị trường cloud Việt Nam tăng khoảng 25%/năm; thời gian xử lý chứng từ "
        "rút từ 3 ngày xuống vài giờ khi kết hợp OCR với LLM.\n\n"
        "Rủi ro: số liệu từ nguồn công khai dễ lệch thời điểm; chưa có khảo sát "
        "khách hàng thực tế về mức giá chịu được. Năng lực cạnh tranh nằm ở dữ "
        "liệu trong nước, giá VND và hỗ trợ onsite."
    )


researcher = _researcher_mock if MOCK else _researcher_live
writer = _writer_mock if MOCK else _writer_live


# ---------- dispatch: hàm thuần, tách ra để self_test dùng được ----------
def dispatch(call_name: str, args: dict) -> str:
    """Thực thi tool của supervisor; tool lạ trả chuỗi lỗi, không raise."""
    if call_name == "call_researcher":
        return researcher(args["topic"])
    if call_name == "call_writer":
        return writer(args["topic"], args["research_json"])
    return f"Lỗi: tool {call_name} không tồn tại."


def _msg_with_tools(calls):
    """Dựng message tool-call giả cùng hình dạng message OpenAI cho mock/self-test."""
    return SimpleNamespace(
        tool_calls=[
            SimpleNamespace(id=f"call_{i}", function=SimpleNamespace(name=n, arguments=json.dumps(a, ensure_ascii=False)))
            for i, (n, a) in enumerate(calls)
        ],
        content=None,
    )


def _chat_live(messages):
    """Một lượt gọi LLM của supervisor ở live mode."""
    resp = client.chat.completions.create(model=MODEL, messages=messages, tools=SUPERVISOR_TOOLS)
    return resp.choices[0].message


def run_supervisor(task: str, max_rounds: int = 6, _llm=None) -> str:
    """Vòng lặp supervisor: gọi tool qua dispatch, dừng khi trả lời hoặc hết vòng.

    _llm chỉ dùng cho mock mode và self_test: hàm nhận messages, trả message
    có .tool_calls / .content — thay một lượt gọi model thật.
    """
    chat = _llm if _llm is not None else _chat_live
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
    for _ in range(max_rounds):
        msg = chat(messages)
        messages.append(msg)

        if not msg.tool_calls:  # supervisor đã trả lời xong
            return msg.content

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = dispatch(call.function.name, args)
            print(f"[supervisor] gọi {call.function.name}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return "Supervisor dừng: vượt số vòng cho phép."


# ---------- Mock mode: kịch bản ghi sẵn đúng luồng trong bài ----------
def _mock_supervisor_llm(topic: str):
    """Supervisor giả: lượt 1 gọi researcher, lượt 2 gọi writer, lượt 3 trả bài."""
    research = _researcher_mock(topic)
    article = _writer_mock(topic, research)
    turn = {"n": 0}

    def llm(_messages):
        turn["n"] += 1
        if turn["n"] == 1:
            return _msg_with_tools([("call_researcher", {"topic": topic})])
        if turn["n"] == 2:
            return _msg_with_tools(
                [("call_writer", {"topic": topic, "research_json": research})]
            )
        return SimpleNamespace(tool_calls=None, content=article)

    return llm


def mock_run() -> None:
    topic = "Thị trường GPU cloud cho ngành logistics tại Việt Nam"
    print("=== MOCK MODE BAI-5: supervisor pattern, kịch bản ghi sẵn ===")
    article = run_supervisor(topic, _llm=_mock_supervisor_llm(topic))
    print(f"[supervisor] trả bài ({len(article.split())} từ):\n")
    print(article)


# ---------- Self-test: không gọi API ----------
def self_test() -> None:
    global researcher, writer
    saved = (researcher, writer)  # ép specialist về bản mock để không gọi API
    researcher, writer = _researcher_mock, _writer_mock
    try:
        # 1. dispatch với tool lạ -> chuỗi lỗi, không raise
        out = dispatch("call_unknown", {})
        assert out.startswith("Lỗi: tool call_unknown không tồn tại"), out

        # 2. supervisor luôn gọi tool -> dừng đúng max_rounds, trả thông điệp vượt vòng
        rounds = {"n": 0}

        def always_tool(_messages):
            rounds["n"] += 1
            return _msg_with_tools([("call_researcher", {"topic": "kiểm tra"})])

        out = run_supervisor("task giả", max_rounds=3, _llm=always_tool)
        assert out == "Supervisor dừng: vượt số vòng cho phép.", out
        assert rounds["n"] == 3, rounds["n"]

        # 3. JSON của researcher mock parse được, đủ 3 field đúng độ dài
        data = json.loads(_researcher_mock("GPU cloud cho logistics"))
        assert set(data) == {"key_points", "numbers", "risks"}, set(data)
        assert len(data["key_points"]) == 5 and len(data["numbers"]) == 3 and len(data["risks"]) == 2
    finally:
        researcher, writer = saved

    print("SELF-TEST BAI-5: PASS (tool lạ, dừng max_rounds, JSON contract)")


if __name__ == "__main__":
    self_test()  # chạy ở cả hai chế độ, không gọi API
    if MOCK:
        mock_run()
    else:
        print("=== LIVE MODE BAI-5 ===")
        print(
            run_supervisor(
                "Viết bài phân tích thị trường GPU cloud cho ngành logistics tại Việt Nam"
            )
        )

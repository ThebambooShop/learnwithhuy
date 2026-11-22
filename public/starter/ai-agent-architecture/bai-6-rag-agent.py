"""Bài 6 — Agentic RAG với fallback web: mini-CRAG (starter kit LearnWithHuy).

Hai chế độ chạy:

- MOCK MODE (không cần API key): search_kb và web_search là hàm thuần không
  gọi API nên giữ nguyên như bài; chỉ vòng LLM của agent thay bằng kịch bản
  ghi hai ví dụ trong bài — trúng KB → trả lời, hỏng KB → fallback web →
  trả "không đủ dữ liệu". Kèm self_test (assert) không gọi API.
- LIVE MODE (có OPENAI_API_KEY): gọi model thật như code trong bài viết.

Chạy: python bai-6-rag-agent.py
"""

import json
import os
from types import SimpleNamespace

MOCK = not os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not MOCK:
    from openai import OpenAI

    client = OpenAI()

# ---------- KB giả lập: 4 doc cứng (giống bài viết) ----------
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


def needs_fallback(docs_json: str, threshold: float = 0.2) -> bool:
    """Hàm thuần: docs rỗng hoặc mọi doc relevance < threshold -> True."""
    try:
        docs = json.loads(docs_json)
    except (json.JSONDecodeError, TypeError):
        return True
    if not docs:
        return True
    return max(d["relevance"] for d in docs) < threshold


# ---------- Agent: contract tool và system prompt (giống bài viết) ----------
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


def dispatch(call_name: str, args: dict) -> str:
    """Thực thi tool của agent RAG; tool lạ trả chuỗi lỗi, không raise."""
    if call_name == "search_kb":
        return search_kb(args["query"])
    if call_name == "web_search":
        return web_search(args["query"])
    return f"Lỗi: tool {call_name} không tồn tại."


def _msg_with_tools(calls):
    """Dựng message tool-call giả cùng hình dạng message OpenAI cho mock mode."""
    return SimpleNamespace(
        tool_calls=[
            SimpleNamespace(
                id=f"call_{i}",
                function=SimpleNamespace(
                    name=name, arguments=json.dumps(args, ensure_ascii=False)
                ),
            )
            for i, (name, args) in enumerate(calls)
        ],
        content=None,
    )


def _chat_live(messages):
    """Một lượt gọi LLM của agent ở live mode."""
    resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
    return resp.choices[0].message


def run_rag_agent(question: str, max_rounds: int = 5, _llm=None) -> str:
    """Vòng lặp agent RAG: search_kb -> chấm relevance -> fallback web -> trả lời.

    _llm chỉ dùng cho mock mode: hàm nhận messages, trả message có
    .tool_calls / .content — thay một lượt gọi model thật.
    """
    chat = _llm if _llm is not None else _chat_live
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    for _ in range(max_rounds):
        msg = chat(messages)
        messages.append(msg)

        if not msg.tool_calls:  # agent đã có câu trả lời
            return msg.content

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = dispatch(call.function.name, args)
            print(f"[tool] {call.function.name}({args['query']!r})")
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )
    return "Dừng: vượt số vòng cho phép."


# ---------- Mock mode: hai kịch bản ghi đúng hai ví dụ trong bài ----------
def _mock_llm_hit_kb(question: str):
    """Ví dụ 1 trúng KB: lượt 1 search_kb, lượt 2 trả lời luôn, không gọi web."""
    turn = {"n": 0}

    def llm(_messages):
        turn["n"] += 1
        if turn["n"] == 1:
            return _msg_with_tools([("search_kb", {"query": question})])
        return SimpleNamespace(
            tool_calls=None,
            content=(
                "Khi tài liệu retrieved kém, CRAG bỏ tài liệu đó, viết lại query "
                "rồi gọi web search lấy nguồn ngoài; tài liệu đạt mức Correct "
                "đi thẳng vào sinh câu trả lời (kb-002)."
            ),
        )

    return llm


def _mock_llm_miss_kb(question: str):
    """Ví dụ 2 hỏng KB: search_kb kém -> needs_fallback -> web_search -> 'không đủ dữ liệu'."""
    turn = {"n": 0}

    def llm(_messages):
        turn["n"] += 1
        if turn["n"] == 1:
            return _msg_with_tools([("search_kb", {"query": question})])
        if turn["n"] == 2:
            # quy tắc mini-CRAG: relevance thấp thì mới rơi xuống web_search
            assert needs_fallback(search_kb(question)), "relevance thấp phải fallback"
            return _msg_with_tools([("web_search", {"query": question})])
        return SimpleNamespace(
            tool_calls=None,
            content=(
                "Không đủ dữ liệu: KB nội bộ không có thông tin về Thủ tướng "
                "Singapore, và kết quả web giả lập không chứa nội dung thật."
            ),
        )

    return llm


def mock_run() -> None:
    print("=== MOCK MODE BAI-6: hai ví dụ trong bài ===")
    q1 = "CRAG xử lý thế nào khi tài liệu retrieved kém?"
    print(f"\n--- Ví dụ 1 (trúng KB): {q1}")
    print(run_rag_agent(q1, _llm=_mock_llm_hit_kb(q1)))
    q2 = "Thủ tướng Singapore hiện tại là ai?"
    print(f"\n--- Ví dụ 2 (hỏng KB, fallback web): {q2}")
    print(run_rag_agent(q2, _llm=_mock_llm_miss_kb(q2)))


# ---------- Self-test: không gọi API ----------
def self_test() -> None:
    # 1. search_kb trả đúng doc có relevance cao nhất cho câu hỏi trong KB
    docs = json.loads(search_kb("chính sách hoàn tiền"))
    assert docs[0]["id"] == "kb-004", docs[0]["id"]
    assert docs[0]["relevance"] == max(d["relevance"] for d in docs)

    # 2. needs_fallback: docs relevance thấp -> True, cao -> False
    assert needs_fallback(json.dumps([{"relevance": 0.05}, {"relevance": 0.1}])) is True
    assert needs_fallback(json.dumps([{"relevance": 0.8}])) is False

    # 3. câu hỏi ngoài KB -> relevance ~0 -> needs_fallback True
    outside = json.loads(search_kb("Thủ tướng Singapore"))
    assert outside[0]["relevance"] <= 0.2, outside[0]
    assert needs_fallback(json.dumps(outside)) is True

    print("SELF-TEST BAI-6: PASS (search_kb đúng doc, needs_fallback, câu hỏi ngoài KB)")


if __name__ == "__main__":
    self_test()  # chạy ở cả hai chế độ, không gọi API
    if MOCK:
        mock_run()
    else:
        print("=== LIVE MODE BAI-6: hai câu hỏi mẫu trong bài ===")
        print(run_rag_agent("CRAG xử lý thế nào khi tài liệu retrieved kém?"))
        print(run_rag_agent("Thủ tướng Singapore hiện tại là ai?"))

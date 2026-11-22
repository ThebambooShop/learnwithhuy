---
title: "RAG trong agent: từ Agentic RAG đến GraphRAG"
description: "Năm kiến trúc RAG trong hệ agent — Agentic RAG, Corrective RAG, Self-RAG, Adaptive RAG, GraphRAG — agent quyết định lúc nào retrieve, đánh giá tài liệu thế nào và khi nào dùng knowledge graph, kèm code thực hành."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-22"
cover: "/images/covers/posts/agent-rag-va-graphrag.jpg"
featured: false
views: 300
faq:
  - q: "Agentic RAG khác RAG cổ điển ở chỗ nào?"
    a: "RAG cổ điển là pipeline cố định: luôn retrieve top-k rồi nhét vào context, không hỏi liệu query có cần retrieve hay không. Agentic RAG biến retrieve thành một tool trong vòng lặp agent — agent tự quyết định gọi hay không, gọi bao nhiêu lần, và dùng kết quả hay không."
  - q: "Nên chọn CRAG hay Self-RAG?"
    a: "CRAG chấm điểm tài liệu ở cấp pipeline: kém thì rewrite query và fallback web search, triển khai nhanh không cần model riêng. Self-RAG yêu cầu model được huấn luyện sinh reflection token (ISREL, ISSUP, ISUSE) cho từng đoạn, kiểm soát sát hơn nhưng đắt. Không tự huấn luyện model thì bắt đầu bằng CRAG — hoặc mô phỏng Self-RAG bằng LLM chấm từng doc."
  - q: "Khi nào GraphRAG đáng cái giá index đắt?"
    a: "Khi câu hỏi là tổng hợp quan hệ qua nhiều thực thể — so sánh các đối thủ theo nhiều khía cạnh, hay hỏi xu hướng rải rác khắp tài liệu. Vector RAG thu thập được những mảnh rời rạc nhưng không tổng hợp được quan hệ giữa chúng. Chỉ cần fact đơn giản thì plain RAG rẻ hơn nhiều."
  - q: "Agent gọi retrieve vô hạn thì làm sao?"
    a: "Giới hạn bằng max_rounds cứng trong vòng lặp, và thêm điều kiện dừng: sau N lần retrieve vẫn không đủ dữ liệu thì agent phải trả lời rõ 'không đủ dữ liệu' thay vì đoán. Lưu log mỗi lần retrieve để biết agent đã thử những query gì."
---

Bài [Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop) đã dựng agent với vòng lặp tools; bài [Multi-agent orchestration](/bai-viet/agent-multi-agent-orchestration) đã tách đội agent. Bài này quay về một tool mà gần như mọi hệ agent đều phải có: retrieve dữ liệu. Câu hỏi không phải "RAG là gì" — mà là **ai ra quyết định trong RAG**: pipeline hay agent. Hệ agent hiện đại trả lời: agent. Retrieve chỉ là một tool, và chất lượng câu trả lời phụ thuộc vào việc agent quyết định tool đó thế nào.

## Vấn đề của RAG cổ điển trong agent

RAG cổ điển là pipeline cố định: chunk tài liệu → embed → retrieve top-k → nhét context → generate. Pipeline này chạy như thế nào thì chạy như vậy, cho dù query có cần retrieve hay không. Ba mù điểm lặp lại trong mọi hệ RAG theo pipeline:

1. **Không hỏi query có cần retrieve hay không.** Câu chào hỏi, câu hỏi kiến thức chung, câu hỏi về chính cuộc hội thoại — vẫn bị dọn top-k chunk tốn token mà không giúp gì.
2. **Không kiểm tra tài liệu tốt không.** Top-k là top theo similarity, không phải theo chất lượng; đoạn văn sai lệch nhưng tương đồng cao vẫn được dùng nguyên xi.
3. **Retrieve một lần là đủ hay chưa.** Câu hỏi multi-hop — "giám đốc công ty sở hữu nhà máy X đang làm gì" — cần retrieve hai lần trở lên; pipeline cố định chỉ fetch một đợt rồi chịu.

> **Trong hệ agent, RAG không phải pipeline mà là một chuỗi quyết định: có retrieve hay không, dùng tài liệu nào, có retrieve lại không, đủ dữ liệu để trả lời chưa.**

Năm kiến trúc dưới đây trả lời năm câu hỏi đó, mỗi cái một cách.

## Năm kiến trúc RAG trong hệ agent

Cả năm thuộc family "Retrieval (RAG)" trong [all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures).

### 1. Agentic RAG

Agent tự quyết định khi nào retrieve và lấy gì. Retrieve trở thành tool `search_docs` trong vòng lặp: agent đọc câu hỏi, quyết gọi hay không, đọc kết quả, quyết dùng hay gọi tiếp. Không có paper riêng — đây là sự kết hợp tự nhiên giữa agent loop và RAG, và là nền của bốn kiến trúc còn lại. Quyết định dừng nằm trong tay model, không phải trong code.

### 2. Corrective RAG (CRAG) — Yan et al., 2024

Chấm điểm tài liệu, kém thì sửa. Một retriever evaluator (paper gốc là T5-based) chấm từng tài liệu retrieved vào ba mức: Correct, Incorrect, Ambiguous. Tài liệu Correct đi thẳng vào sinh câu trả lời; Incorrect bị bỏ, query được viết lại rồi gọi **web search** lấy nguồn ngoài; Ambiguous được tinh chỉnh bằng cách tách và lọc. Điểm khác biệt lớn nhất: CRAG có đường fallback ra ngoài knowledge base — tài liệu nội bộ kém thì lấy web, thay vì sinh câu trả lời trên nền tài liệu rác.

### 3. Self-RAG — Asai et al., 2024

Model tự phản tư từng bước bằng reflection token. Self-RAG huấn luyện model sinh các token đặc biệt: `Retrieve?` (có cần retrieve không), rồi sau mỗi đoạn retrieved là `ISREL` (relevance), `ISSUP` (câu trả lời có dựa trên tài liệu không), `ISUSE` (đoạn trả lời có hữu ích không). Từng tài liệu được đánh giá riêng: dùng, bỏ, hoặc đánh giá lại. Khác CRAG ở chỗ việc đánh giá không phải một component ngoài pipeline mà nằm trong chính model — sát hơn nhưng đắt hơn vì phải huấn luyện. Không huấn luyện model riêng, người ta xấp xỉ bằng một LLM chấm từng tài liệu và một LLM phản tư bản nháp.

### 4. Adaptive RAG — Jeong et al., 2024

Route theo độ phức tạp của query. Một classifier đánh giá query rồi điều hướng: query đơn giản mà model biết sẵn → không retrieve; query cần dữ liệu → retrieve một lần; query multi-hop phức tạp → retrieve lặp nhiều nhịp. Trong hệ agent, classifier có thể chính là agent: nó đọc câu hỏi và chọn tool phù hợp — trả lời trực tiếp, `search_docs` một lần, hay chuỗi retrieve-giữa-các-bước.

### 5. GraphRAG — Microsoft Research, 2024

Thay chunk thuần bằng knowledge graph và community summary. Vector RAG trả lời tốt câu hỏi tìm một fact ("mức phí X là bao nhiêu") nhưng kém với câu hỏi tổng hợp ("so sánh các đối thủ theo khía cạnh giá, công nghệ và đối tác") — dữ kiện cần nằm rải rác ở nhiều chunk mà top-k không gom đủ để tổng hợp. GraphRAG index tài liệu thành graph thực thể + quan hệ, chia cụm và tóm tắt từng cụm; câu hỏi tổng hợp được trả lời bằng cách đi qua các summary. Chi tiết ở phần "Cấu trúc GraphRAG" bên dưới.

Bảng gộp năm kiến trúc trước khi chuyển sang phần chọn:

| Kiến trúc | Nguồn | Ai đánh giá tài liệu | Điểm khác biệt chính |
| --- | --- | --- | --- |
| Agentic RAG | Pattern, không paper | Agent tự quyết dùng/bỏ/gọi lại | Retrieve là tool, điểm dừng do model |
| Corrective RAG | Yan et al. 2024 | Retriever evaluator ngoài pipeline | Kém → rewrite query + web search |
| Self-RAG | Asai et al. 2024 | Model tự sinh reflection token | Đánh giá nằm trong model, cần huấn luyện |
| Adaptive RAG | Jeong et al. 2024 | Classifier route theo độ phức tạp | Không retrieve / một lần / multi-hop tùy query |
| GraphRAG | Microsoft 2024 | Community summaries | Index là graph, mạnh cho câu hỏi tổng hợp |

### Bảng chọn theo loại câu hỏi

| Loại câu hỏi | Kiến trúc phù hợp | Lý do |
| --- | --- | --- |
| Fact đơn giản, tài liệu nội bộ rõ | Plain RAG hoặc Agentic RAG | Retrieve một lần là đủ; thêm cơ chế chỉ tốn phí |
| Cần kiểm soát đúng/sai, nguồn thiếu tin cậy | CRAG hoặc Self-RAG | Chấm điểm tài liệu + đường fallback khi tài liệu kém |
| Query trộn lẫn độ khó, chitchat đến multi-hop | Adaptive RAG | Route theo độ phức tạp, không retrieve thứ không cần |
| Hỏi quan hệ, tổng hợp nhiều thực thể | GraphRAG | Community summary gom nổi quan hệ mà chunk rời rạc không gom được |

Hai kiến trúc có thể xếp chồng: hệ thực tế thường là Agentic RAG làm nền, CRAG cài làm phần chấm điểm bên trong, Adaptive RAG ở tầng routing đầu vào.

## Code thực hành: Agentic RAG với fallback web (mini-CRAG)

Bản dựng dưới đây là Agentic RAG đúng nghĩa: hai tool — `search_kb` tìm trong knowledge base nội bộ, `web_search` lấy nguồn ngoài. System prompt bắt buộc agent chấm relevance; điểm thấp thì fallback ra web. Đó chính là tinh thần CRAG, thu gọn trong ~100 dòng. Môi trường: `pip install openai`, `export OPENAI_API_KEY=...` (model mặc định `gpt-4o-mini`, đổi qua `OPENAI_MODEL`).

> **Bản chạy được:** file Python hoàn chỉnh cho bài này nằm trong [starter kit](/starter/ai-agent-architecture/) — kèm mock mode (chạy không cần API key) và self-test, hướng dẫn cài đặt trong [README](/starter/ai-agent-architecture/README.md).

```python
import json
import os

from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ---------- KB giả lập: vài doc cứng ----------
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

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Relevance score lệch khi demo | Mock dùng keyword overlap, không phải embedding | Hiểu đây là giả lập; thay bằng vector search thật khi lên production |
| Agent retrieve vô hạn | Không có điều kiện dừng khi dữ liệu kém | Đặt `max_rounds` cứng + rule "sau N lần vẫn kém thì trả 'không đủ dữ liệu'" |
| Agent trả lời ngoài tài liệu | System prompt chưa cấm đoán | Prompt phải có "trả lời chỉ dựa trên dữ liệu đã lấy, không đoán"; thêm eval test câu hỏi ngoài KB |

## Cấu trúc GraphRAG

GraphRAG đáng một bài riêng (đã có: [GraphRAG — knowledge graph cho RAG](/bai-viet/graphrag-knowledge-graph)), nhưng cấu trúc index cần nằm trong đầu khi chọn kiến trúc. Bốn bước:

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

## Bài tập tự làm (3 mức)

- **Mức 1 — Làm theo:** tách `grade_docs` thành tool thật — thêm tool `grade_docs(docs)` trả về danh sách doc kèm điểm từ một LLM chấm riêng, sửa `SYSTEM` để agent bắt buộc gọi trước khi dùng tài liệu; mini-CRAG thành thật thay vì chỉ dựa vào relevance score.
- **Mức 2 — Tự sửa:** đếm số lần `search_kb`; sau hai lần vẫn không có tài liệu đạt thì agent trả "không đủ dữ liệu" kèm những gì đã thử. Chạy lại câu hỏi hỏng KB và so hành vi.
- **Mức 3 — Mở rộng:** chạy ba query (fact trong KB, fact ngoài KB, câu hỏi tổng hợp "liên hệ giữa CRAG và web search trong tài liệu"), ghi agent gọi tool nào mấy lần, so với plain RAG retrieve-luôn. Cài vào DocMind — KB nội bộ hiện là mock, thay bằng tài liệu công ty thật của bạn.

## Tài liệu gốc

- all-agentic-architectures (family Retrieval: Agentic, Corrective, Self, Adaptive, GraphRAG): [github.com/FareedKhan-dev/all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures)
- Nir Diamant — GenAI Agents (notebook CRAG, Self-RAG, Adaptive RAG từng cái một): [github.com/NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents)
- Microsoft AI Agents for Beginners: [github.com/microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners)
- Papers: Corrective RAG (Yan et al. 2024, arXiv 2401.15884) — Self-RAG (Asai et al. 2024, arXiv 2310.11511) — Adaptive RAG (Jeong et al. 2024, arXiv 2403.14403) — GraphRAG (Microsoft Research 2024, arXiv 2404.16130)
- Trên LearnWithHuy: [GraphRAG — knowledge graph cho RAG](/bai-viet/graphrag-knowledge-graph), [Hybrid search: BM25 + dense + RRF](/bai-viet/hybrid-search-bm25-dense-rrf) — tầng retrieval mà mọi kiến trúc trên đều đứng trên, [Đánh giá chất lượng RAG với RAGAS](/bai-viet/danh-gia-chat-luong-rag-ragas) — đo được mới biết kiến trúc nào đáng chuyển, và [Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop).

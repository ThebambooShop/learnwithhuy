---
title: "Chọn architecture cho agent: bản đồ 36 mẫu từ Reflexion đến BrowserAgent"
description: "Bản đồ 36 kiến trúc agent được dựng sẵn và benchmark trong kho all-agentic-architectures — xếp theo 8 gia đình, kèm decision matrix chọn architecture theo bài toán thật và pattern deterministic-picker."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-22"
cover: "/images/covers/posts/chon-agent-architecture-36-mau.jpg"
featured: false
views: 300
faq:
  - q: "Cần biết LangGraph trước khi chạy các notebook trong repo không?"
    a: "Không bắt buộc. Notebook dựng architecture bằng LangGraph nhưng đọc được như code Python thường: mỗi notebook là một architecture, trạng thái đi từ node tới node. Nếu chưa từng dùng LangGraph, hãy chạy nhóm Beginner trước — bạn sẽ học LangGraph đúng lúc cần nó, qua cách nhìn architecture thay vì API."
  - q: "36 architecture có nghĩa là hệ thống của tôi cần chọn đúng một?"
    a: "Không. Decision matrix là điểm bắt đầu: chọn architecture cho từng loại task, không cho toàn hệ thống. Nhiều hệ thống production chạy song song 2-3 architecture — ví dụ Self-RAG cho QA, Plan-Execute-Verify cho tác vụ dài — và Meta-Controller là pattern để ghép chúng vào một điểm vào duy nhất."
  - q: "Deterministic-picker khác gì để LLM tự quyết mọi thứ?"
    a: "Deterministic-picker giới hạn LLM ở việc phân loại: model chỉ trả nhãn hoặc điểm số, Python mới là người chọn pipeline, validate nhãn và fallback khi nhãn lạ. Kết quả vì vậy dự đoán được, dễ test, không phụ thuộc hành vi model — cùng nguyên tắc với Factor 8 (own your control flow) trong bài 12 nguyên lý production."
  - q: "Benchmark 17 task trong repo có thay thế eval riêng của tôi không?"
    a: "Không. Benchmark dùng để sàng lọc: loại architecture rõ ràng không hợp trước khi đầu tư thời gian. Sau khi còn lại 1-2 ứng viên, bạn vẫn phải viết eval trên dữ liệu và tiêu chí thật của mình — chuẩn là kết hợp trace-based như bài 12 nguyên lý đã nói, chạy trong CI cho mọi commit."
---

Bảy bài trước trong lộ trình, mỗi bài dạy một pattern riêng: agent loop ở [bài 1](/bai-viet/nen-tang-agent-va-agent-loop), routing và tool design ở [bài 2](/bai-viet/agent-routing-va-tool-design), planning và reflection ở [bài 3](/bai-viet/agent-planning-va-reflection), memory ở [bài 4](/bai-viet/agent-memory-va-context-engineering), multi-agent ở [bài 5](/bai-viet/agent-multi-agent-orchestration), RAG trong agent ở [bài 6](/bai-viet/agent-rag-va-graphrag), và 12 nguyên lý production ở [bài 7](/bai-viet/12-nguyen-ly-agent-production). Câu hỏi còn lại là câu khó nhất: đứng trước một bài toán thật, chọn pattern nào?

Bài này trả lời bằng một bản đồ. Kho [all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures) của Fareed Khan (4.8k sao) dựng **36 architecture agent chạy được trên LangGraph** — mỗi architecture một notebook, cùng một giao diện thống nhất, hỗ trợ 11 provider LLM, kèm benchmark trên 17 task. Thay vì đọc lý thuyết 36 papers, bạn chạy 36 notebook và so số.

## Bản đồ: 8 gia đình kiến trúc

Tôi xếp 36 mẫu thành 8 gia đình theo nhiệm vụ chính của chúng. Nhớ tên gia đình là đủ để thu hẹp lựa chọn; đọc bảng từng architecture khi cần chi tiết.

### 1. Reasoning & Reflection

| Architecture | Ý chính |
| --- | --- |
| Reflection | Model tự chấm bản nháp của mình rồi viết lại — một vòng tự phê bình |
| Reflexion | Reflection cộng bộ nhớ — lưu bài học từ lần fail để lần sau không lặp |
| Chain-of-Verification | Sinh câu hỏi kiểm chứng rồi trả lời từng câu để bẫy hallucination |
| Self-Discover | Agent tự thiết kế reasoning module cho chính tác vụ trước khi giải |
| Constitutional AI | Model chấm và sửa đáp án theo một bộ nguyên tắc viết trước |

### 2. Sampling & Search

| Architecture | Ý chính |
| --- | --- |
| Self-Consistency | Sinh nhiều nhánh trả lời độc lập, bỏ phiếu chọn đáp án đa số |
| Tree of Thoughts | Reasoning thành cây nhánh, đánh giá từng nhánh rồi chọn nhánh tốt |
| LATS | Tree of Thoughts cộng Monte Carlo tree search, reflection làm heuristic |
| Mental Loop | Mô phỏng kết quả hành động "trong đầu" trước khi chạy thật |
| Ensemble | Nhiều pipeline khác nhau chạy song song rồi hợp nhất kết quả |

### 3. Retrieval (RAG)

| Architecture | Ý chính |
| --- | --- |
| Agentic RAG | Agent tự quyết khi nào cần truy vấn và truy vấn gì |
| Corrective RAG (CRAG) | Chấm điểm chunk truy về — đạt thì dùng, kém thì rewrite query và tìm lại |
| Self-RAG | Model tự quyết lúc nào cần retrieve và tự đánh giá đoạn trích dẫn |
| Adaptive RAG | Phân loại độ khó câu hỏi rồi chọn pipeline RAG tương ứng |
| GraphRAG | Truy vấn trên knowledge graph thay vì các chunk phẳng |

### 4. Memory

| Architecture | Ý chính |
| --- | --- |
| Episodic + Semantic | Nhớ trải nghiệm cụ thể (episodic) song song với kiến thức khái quát (semantic) |
| Graph Memory | Lưu quan hệ giữa các fact thành graph, nhớ theo cấu trúc |
| MemGPT | Quản lý context như hệ điều hành — RAM ngắn hạn, disk dài hạn |
| Voyager | Agent trong Minecraft tự viết và lưu thư viện skill để tái dùng |
| Agent Workflow Memory | Nhớ "recipe" các bước thành công để áp cho tác vụ tương tự |

### 5. Tools & Actions

| Architecture | Ý chính |
| --- | --- |
| Tool Use | Schema function + dispatch code — nền tảng cho mọi agent |
| ReAct | Reason và Act xen kẽ: nghĩ một câu, gọi một tool |
| Planning | Tách task thành plan các bước trước khi thực thi |
| Plan-Execute-Verify | Plan, thực hiện từng bước, verify, sửa plan khi lệch |
| SWE-Agent | Sửa code thật trên repo, chạy test để tự kiểm chứng |
| BrowserAgent | Điều khiển trình duyệt: click, điền form, đọc DOM |

### 6. Multi-Agent (điều phối)

| Architecture | Ý chính |
| --- | --- |
| Multi-Agent (supervisor) | Một agent điều phối giao việc cho các agent chuyên trách |
| Blackboard | Các agent ghi kết quả lên bảng chung, đọc và bổ sung của nhau |
| Debate | Nhiều agent lập luận trái chiều cho tới khi đồng thuận đáp án |
| STORM | Hệ multi-agent viết bài nghiên cứu dài có trích dẫn |

### 7. Meta & Mixture

| Architecture | Ý chính |
| --- | --- |
| Meta-Controller | Router chọn architecture nào chạy cho từng task |
| Mixture of Agents | Nhiều LLM hợp tác lần lượt rồi hợp kết quả để nâng chất lượng |

Hai architecture của gia đình này đứng "tầng trên" các gia đình kia: chúng điều phối giữa các architecture thay vì tự thực hiện tác vụ.

### 8. Safety & Specialty

| Architecture | Ý chính |
| --- | --- |
| Dry-Run | Propose, simulate, approval gate trước hành động rủi ro |
| Reflexive Metacognitive | Agent tự nhận biết khi thiếu tự tin và chủ động xin trợ giúp |
| RLHF Self-Improvement | Dùng feedback để cải thiện prompt và policy qua nhiều vòng |
| Cellular Automata | Agent cập nhật trạng thái theo hàng xóm — pattern thí nghiệm |

## Decision matrix: chọn theo bài toán thật

Bản đồ trên trả lời "có gì"; bảng dưới trả lời "chọn gì". Mỗi dòng là một tình huống thật, architecture gợi ý, và bài trong lộ trình đã dạy pattern đó.

| Bài toán thật | Gia đình | Architecture gợi ý | Bài đã học |
| --- | --- | --- | --- |
| Trả lời QA cần chính xác cao, chấm được | Retrieval | Self-RAG, Corrective RAG | [bài 6](/bai-viet/agent-rag-va-graphrag) |
| QA trên tài liệu nội bộ có quan hệ chằng chịt | Retrieval | GraphRAG | [bài 6](/bai-viet/agent-rag-va-graphrag) |
| Câu hỏi mơ hồ, khó đoán pipeline nào hợp | Retrieval | Adaptive RAG | [bài 6](/bai-viet/agent-rag-va-graphrag) |
| Tác vụ nhiều bước hay fail giữa chừng | Tools & Actions | Plan-Execute-Verify | [bài 3](/bai-viet/agent-planning-va-reflection) |
| Lỗi logic lặp lại qua nhiều lần chạy | Reasoning & Reflection | Reflexion | [bài 3](/bai-viet/agent-planning-va-reflection) |
| Tác vụ lặp lại cần nhớ recipe | Memory | Agent Workflow Memory | [bài 4](/bai-viet/agent-memory-va-context-engineering) |
| Context dài cần quản lý chặt | Memory | MemGPT | [bài 4](/bai-viet/agent-memory-va-context-engineering) |
| Hành động rủi ro cần duyệt | Safety & Specialty | Dry-Run | [bài 7](/bai-viet/12-nguyen-ly-agent-production) |
| Độ khó vượt 1 agent | Multi-Agent | Supervisor | [bài 5](/bai-viet/agent-multi-agent-orchestration) |
| Agent cần thao tác web, điền form | Tools & Actions | BrowserAgent | [bài 2](/bai-viet/agent-routing-va-tool-design) |
| Task đầu vào đa dạng, khó đoán trước | Meta & Mixture | Meta-Controller | [bài 2](/bai-viet/agent-routing-va-tool-design) |

Cách dùng bảng: bắt đầu từ mô tả bài toán gần nhất với của bạn, mở notebook của architecture gợi ý, chạy trên dữ liệu thật trước khi chuyển code vào hệ thống. Đừng đọc dọc bảng theo thứ tự — bài toán của bạn quyết định hàng nào để đọc.

## Deterministic-picker: model lo ngôn ngữ, code lo logic

13/36 architecture trong repo dùng chung một pattern nhỏ mà đắt giá: **deterministic-picker**. LLM chỉ được gọi để làm một việc — phân loại hoặc chấm điểm; toàn bộ logic quyết định cuối nằm trong Python. Đây là ranh giới rõ giữa hai vai trò:

| Việc | Ai làm |
| --- | --- |
| Phân loại câu hỏi, gắn nhãn task | LLM |
| Chọn pipeline theo nhãn, validate, fallback khi nhãn lạ | Python |
| Chấm điểm chunk, cân nhắc nhánh | LLM |
| So ngưỡng điểm để quyết định retry hay dừng | Python |

Pattern này viết được trong ~20 dòng:

```python
import json, os
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()  # API key đọc từ biến môi trường OPENAI_API_KEY

# Cả 36 architecture trong repo chia sẻ cùng một interface: arch.run(task)
ARCHS = {
    "qa_chinh_xac": self_rag,            # notebook Self-RAG trong repo
    "nhanh_chi_phi": agentic_rag,        # notebook Agentic RAG
    "da_buoc_dai": plan_execute_verify,  # notebook Plan-Execute-Verify
}

PICK_PROMPT = (
    "Phân loại task thành đúng một nhãn: "
    "qa_chinh_xac | nhanh_chi_phi | da_buoc_dai. "
    "Chỉ trả JSON dạng {\"label\": \"...\"}."
)

def pick_architecture(task: str):
    resp = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PICK_PROMPT},
            {"role": "user", "content": task},
        ],
    )
    label = json.loads(resp.choices[0].message.content).get("label")
    # Python compose quyết định cuối: nhãn lạ -> rơi về kiến trúc mặc định
    return ARCHS.get(label, ARCHS["nhanh_chi_phi"])
```

Nguyên tắc đứng sau: giữ model lo ngôn ngữ, code lo logic. Đây chính là Factor 8 — own your control flow — mà [bài 7](/bai-viet/12-nguyen-ly-agent-production) đã bàn. LLM của bạn đáng tin ở phần hiểu ngôn ngữ, không đáng tin ở phần đưa ra quyết định có hậu quả; để quyết định trong code, bạn giữ được khả năng test và dự đoán.

## Meta-Controller: router chọn architecture

Gia đình Meta & Mixture là hướng kết hợp của cả lộ trình. **Meta-Controller** đứng ở tầng cao nhất: nhận task, phân loại (chính là một deterministic-picker), rồi gọi đúng architecture như gọi một tool. Không ngẫu nhiên mà nó cùng kiểu với routing trong [bài 2](/bai-viet/agent-routing-va-tool-design) — chỉ khác một cấp: thay vì route giữa các tool, nó route giữa các architecture.

Cách triển khai gọn nhất: mỗi architecture đóng gói thành một "tool" với mô tả rõ ràng, Meta-Controller là agent supervisor ở [bài 5](/bai-viet/agent-multi-agent-orchestration) với danh sách tool đó. Bạn chỉ cần một phần tử nữa — eval để biết từng architecture chạy tốt trên loại task nào — và hệ thống tự chọn đường đi hợp lý.

## Học tiếp thế nào

Đừng học 36 notebook theo thứ tự thư mục. Khuyến nghị path của repo, khớp với lộ trình này:

1. **Beginner** — Reflection, Tool Use, ReAct: nền đã có ở [bài 1](/bai-viet/nen-tang-agent-va-agent-loop) và [bài 2](/bai-viet/agent-routing-va-tool-design).
2. **RAG** — Agentic RAG, Corrective RAG, Self-RAG: nối tiếp [bài 6](/bai-viet/agent-rag-va-graphrag).
3. **Multi-agent** — supervisor, Debate, STORM: nối tiếp [bài 5](/bai-viet/agent-multi-agent-orchestration).
4. **Safety** — Dry-Run, Reflexive Metacognitive: nối tiếp [bài 7](/bai-viet/12-nguyen-ly-agent-production).

Hai nguyên tắc khi học:

- **Chạy notebook thật, đừng đọc.** Giao diện `.run(task)` thống nhất cho phép bọc cùng một task qua nhiều architecture và so trực tiếp kết quả. So trên task của bạn là cách học nhanh nhất.
- **Đọc benchmarks.md trước khi tin bất kỳ architecture nào.** Repo benchmark 36 architecture trên 17 task — chọn theo số đo trên task giống bài toán của bạn, không theo tên nghe "xịn".

## Bài tập tự làm

1. **Chạy 2 notebook trên cùng một task thật của bạn** (Agentic RAG và Self-RAG là cặp hợp lý nếu task là QA nội bộ). Ghi bảng: số lần gọi LLM, tổng token, chất lượng đáp án.
2. **Viết deterministic-picker** cho 3 architecture bạn chọn: LLM phân loại nhãn, Python compose quyết định cuối và fallback. Thêm 1 test case cho nhãn lạ để chứng minh fallback hoạt động.
3. **Mở benchmarks.md**, tìm architecture có điểm tốt nhất trên task giống bài toán của bạn. Viết 200 từ giải thích vì sao bạn chọn hoặc vì sao không chọn nó — có lý do rõ hơn có kiến trúc đúng.

## Tài liệu gốc

- [FareedKhan-dev/all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures) — nguồn chính: 36 architecture, notebook, benchmark.
- [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) — các lesson nền mà bài 1-7 của lộ trình đã đi qua.

Đây là bài cuối của lộ trình **Kiến trúc AI Agent: từ agent loop đến production** — [bài 1](/bai-viet/nen-tang-agent-va-agent-loop) đến [bài 7](/bai-viet/12-nguyen-ly-agent-production). Nếu bạn quay lại cần tra nhanh: bản đồ 8 gia đình ở trên là bảng tra cứu, decision matrix là bảng chọn, và deterministic-picker là cầu nối về code — thứ bài 7 đã dựng nền.

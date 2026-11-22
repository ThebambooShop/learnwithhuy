---
title: "Memory và Context Engineering: agent nhớ được gì, bỏ quên gì"
description: "Context window là nguyên liệu đắt nhất của agent: quản lý short-term/long-term memory theo mô hình MemGPT, các kỹ thuật compaction và context engineering, cùng các kiến trúc memory nâng cao — kèm code thực hành."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-22"
cover: "/images/covers/posts/agent-memory-va-context-engineering.jpg"
featured: false
views: 300
faq:
  - q: "Compaction có làm agent mất thông tin quan trọng?"
    a: "Có, nếu tóm tắt không có nguyên tắc. Ba thứ phải giữ nguyên trong bản tóm tắt: con số (giá, hạn, mã đơn), tên riêng và ràng buộc người dùng đã đưa. Viết instruction compaction ghi rõ những thứ cần giữ nguyên, và giữ episodic log để có thể khôi phục nội dung đã bị cắt khi cần."
  - q: "Memory và RAG khác nhau thế nào?"
    a: "RAG truy xuất tài liệu ngoài để trả lời câu hỏi tại chỗ — corpus không đổi theo hành vi người dùng. Memory lưu trạng thái liên cá thể và diễn tiến theo thời gian: lựa chọn, sự kiện, skill đã học. Cả hai dùng chung công nghệ vector nhưng giải bài toán khác; nhiều agent production dùng cả hai cùng lúc."
  - q: "Khi nào cần MemGPT-style archival thay vì chỉ compaction?"
    a: "Khi lịch sử cần dùng lại qua nhiều phiên dài hoặc vượt window nhiều lần: trợ lý cá nhân dài hạn, agent làm việc nhiều ngày trên một dự án. Với phiên ngắn, compaction và clear used context đủ và rẻ hơn nhiều — archival là tầng bậc cao, không phải bước đầu tiên."
  - q: "Dùng thư viện memory thay vì tự viết thì chọn gì?"
    a: "Tự viết như MemoryManager trong bài chỉ hợp giai đoạn hiểu bản chất. Khi đi production, thư viện như mem0 hay letta (tiến hóa từ MemGPT) cho sẵn retrieval, update và decay. Nhưng nguyên tắc own your context window vẫn đứng: framework phải cho bạn quyền xem và sửa cái gì vào context trước mỗi lần gọi model."
---

Vấn đề lớn nhất của agent production không phải suy luận — model ngày càng giỏi — mà là quản lý cái model nhìn thấy. Mọi thứ vào context window: system prompt, lịch sử hội thoại, kết quả tool, memory được nạp vào, tài liệu vừa truy xuất — đều chiếm cùng một ngân sách hữu hạn và đắt. Agent chạy vài chục vòng sẽ nạp đầy window trước khi hoàn thành tác vụ: hoặc cắt bớt mà mất thông tin quan trọng, hoặc vượt limit mà chết giữa đường.

Bài này gom hai lớp giải pháp: **context engineering** — kỹ thuật quản lý cái gì nằm trong window tại từng lượt — và **memory phân tầng** — kiến trúc để lưu ngoài window rồi nạp lại khi cần.

## Context engineering: cái gì được vào window

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

### Own your context window

Đây là nguyên tắc số 3 trong [12-factor-agents](https://github.com/humanlayer/12-factor-agents): **đừng để framework quyết định cái gì vào context — bạn phải kiểm soát.**

Framework chat tự động ghép toàn bộ history vào mỗi lượt gọi. Tiện cho demo, hại cho production: bạn không cắt được tool output dài, không compaction được giữa đường, không pre-fetch được dữ liệu mà agent sắp cần. Trước mỗi lần gọi model, messages phải là thứ bạn chủ động lắp ráp — từ API thô hoặc framework cho phép can thiệp trước khi gửi.

## Phân tầng memory

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

### Tầng nào cho bài toán nào

| Bài toán | Memory tier gợi ý | Lý do |
| --- | --- | --- |
| Chatbot CSKH nhiều phiên | Episodic (log phiên) | cần nhớ ticket cũ của cùng khách hàng giữa các phiên |
| Trợ lý cá nhân dài hạn | Episodic + Semantic | nhớ sự kiện đã qua lẫn sở thích và ràng buộc người dùng |
| Agent lập trình | Skill library kiểu Voyager | code đã chạy đúng là tài sản dùng lại được, rẻ hơn viết lại |
| Agent làm quy trình lặp (upload, deploy, báo cáo) | Agent Workflow Memory | recipe ổn định dùng lại cho tác vụ cùng hình dáng |
| Kiến thức tổ chức nhiều thực thể và quan hệ | Graph Memory | câu hỏi "ai làm gì với ai" truy vấn theo quan hệ tự nhiên hơn vector |

Quy tắc chọn: bắt đầu từ short-term; thêm tầng khi agent thực sự cần thông tin ngoài phiên hiện tại; thêm tầng phức tạp (graph, skill library) chỉ khi bài toán có cấu trúc khớp.

## Code thực hành: MemoryManager không framework

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
# → ['Hạn thanh toán là 30/12/2026']
```

Ba phương thức tương ứng ba vai trò:

- **add** ghi event (lượt hội thoại, hành động) hoặc fact (kiến thức bền) — phân kind ngay lúc ghi để compaction biết gộp gì.
- **retrieve** dùng keyword overlap cộng recency decay: item có từ trùng nhiều hơn và mới hơn được nạp trước. Đây là bản nhíp của vector search thật — nâng cấp tự nhiên là thay keyword bằng embedding cosine similarity, đúng kiến trúc đã nói trong bài [Hybrid Search](/bai-viet/hybrid-search-bm25-dense-rrf).
- **compact** ép nửa event cũ thành một fact, giữ nguyên các fact có sẵn — cùng tinh thần compaction của context engineering nhưng ở tầng memory.

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Compaction làm mất con số quan trọng | Tóm tắt không có instruction giữ nguyên | Instruction tóm tắt phải ghi rõ "giữ NGUYÊN con số, tên riêng, mã đơn" |
| Retrieve trả kết quả không liên quan | Keyword overlap thấp vẫn vào top_k | Đặt ngưỡng overlap tối thiểu — dưới ngưỡng trả rỗng thay vì ép top_k |
| Đếm token lệch thực tế | `estimate_tokens` là xấp xỉ | Dùng `usage` trả về trong response hoặc tokenizer thật khi tính chi phí |

## Cạm bẫy

Ba cạm bẫy phổ biến khi thêm memory cho agent:

1. **Cho model mọi thứ vào context.** Đắt hơn là rõ hơn: token dài hơn nghĩa là chậm và đắt hơn; nội dung thừa còn làm model phân tán — chất lượng context quan trọng hơn số lượng. Cắt những gì lượt hiện tại không dùng.
2. **Nhầm memory với nền tảng RAG.** RAG truy xuất tài liệu ngoài cho câu hỏi tại chỗ; memory lưu trạng thái liên cá thể và diễn tiến theo thời gian. Cùng dùng vector search nhưng giải bài toán khác — nếu chưa rõ phần truy xuất, đọc bài [Hybrid Search BM25 + Dense + RRF](/bai-viet/hybrid-search-bm25-dense-rrf) trước.
3. **Không log memory.** Khi agent trả lời sai vì "quên", không có log bạn không biết nó đã retrieve gì, đã compact mất gì. Log mỗi lệnh add/retrieve/compact cùng top_k kết quả — đây là câu trả lời cho phần lớn bug memory.

> 📍 **Dự án xuyên suốt — DocMind:** sau bài này DocMind nhớ phiên làm việc trước và giữ context gọn: lịch sử cũ nén thành tóm tắt, kết quả tool đã dùng bị xóa — token giảm, chất lượng không đổi.

## Bài tập tự làm (3 mức)

**Mức 1 — Làm theo:** thêm hàm `trim_tool_results()` bỏ kết quả tool đã tiêu hóa khỏi context. Chạy một hội thoại 20 lượt và so `estimate_tokens` trước/sau — ghi lại số token tiết kiệm thực tế.

**Mức 2 — Tự sửa:** nâng `retrieve()` từ keyword scoring sang embedding cosine similarity. So kết quả trên 10 câu hỏi thực tế của bạn — đếm mỗi bên trả đúng bao nhiêu kết quả liên quan.

**Mức 3 — Mở rộng:** viết instruction compaction giữ nguyên con số và tên riêng, rồi test: nạp hội thoại có "giá 12 triệu, hạn 30/12", nén, và hỏi lại agent xem nó còn nhớ đúng hai giá trị đó không. Ghép vào DocMind — trợ lý phải nhớ được "hạn thanh toán 30/12/2026" mà người dùng nói ở phiên trước.

## Tài liệu gốc

- [Microsoft AI Agents for Beginners — lesson 12 (Context engineering) và lesson 13 (Memory)](https://github.com/microsoft/ai-agents-for-beginners)
- [all-agentic-architectures — family "Memory"](https://github.com/FareedKhan-dev/all-agentic-architectures)
- [GenAI_Agents — notebook Context engineering](https://github.com/NirDiamant/GenAI_Agents)
- [12-factor-agents — factor 3 "Own your context window", pre-fetch context](https://github.com/humanlayer/12-factor-agents)
- Paper nền: MemGPT (Packer 2023), Generative Agents (Park 2023), Voyager (Wang 2023), Agent Workflow Memory (Wang 2024)
- Đọc liên quan trong series: [Hybrid Search BM25 + Dense + RRF](/bai-viet/hybrid-search-bm25-dense-rrf) — nền truy xuất cho retrieve; [GraphRAG và Knowledge Graph](/bai-viet/graphrag-knowledge-graph) — nền cho Graph Memory; [Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop) — agent loop mà memory gắn vào.

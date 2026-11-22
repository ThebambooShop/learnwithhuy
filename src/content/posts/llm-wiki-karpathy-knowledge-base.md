---
title: "LLM Wiki của Karpathy: biến tài liệu rải rác thành knowledge base cục bộ"
description: "Bản dịch bài 'LLM Wiki Setup: Karpathy's Knowledge Base' của Kunal Ganglani + framework gốc từ gist của Karpathy: kiến trúc 3 tầng, 3 operations Ingest/Query/Lint, schema CLAUDE.md mẫu, hướng dẫn chi tiết build LLM Wiki với Obsidian + AI, so sánh agent và 5 failure mode kèm cách khắc phục."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-21"
cover: "/images/covers/posts/llm-wiki-karpathy-knowledge-base.jpg"
faq:
  - q: "LLM Wiki của Karpathy là gì?"
    a: "Một prompt pattern do Andrej Karpathy công bố dạng GitHub gist (tháng 4/2026, hơn 5.000 stars): thay vì retrieve từng đoạn tài liệu mỗi lần hỏi như RAG, một LLM agent biên dịch nguồn của bạn thành các file markdown liên kết chéo thành wiki tồn tại lâu dài, lớn dần theo từng nguồn bạn thêm vào."
  - q: "LLM Wiki khác RAG chỗ nào?"
    a: "RAG là stateless — mỗi query đều retrieve raw chunk rồi tổng hợp lại từ đầu. LLM Wiki biên dịch ngay lúc ingestion: tri thức nằm sẵn trong các trang wiki có cross-link tường minh. RAG scale theo chiều rộng (hàng triệu tài liệu), LLM Wiki scale theo chiều sâu (hàng trăm trang, giới hạn bởi context window)."
  - q: "Chạy LLM Wiki bằng model local được không?"
    a: "Được nhưng có điều kiện: cần model instruction-following và sửa file tốt. Qwen3 32B và Llama 3 70B qua Ollama xử lý được cập nhật cơ bản nhưng yếu ở multi-page update. Thực tế cần Apple Silicon 64GB unified memory hoặc GPU 24GB VRAM mới đủ dùng."
  - q: "Wiki lớn hơn context window thì làm sao?"
    a: "Quá khoảng 150–200 trang, agent bắt đầu 'quên' trang tồn tại và tạo trùng lặp. Cách khắc phục: file _index/master-index.md liệt kê mọi trang kèm tóm tắt một dòng, bảo agent đọc index trước rồi chỉ mở đúng trang cần cập nhật — cách này kéo giới hạn lên 300+ trang."
  - q: "Bảo trì LLM Wiki tốn bao nhiêu công?"
    a: "Không phải 'zero maintenance'. Tác giả gốc mất 30–45 phút mỗi 2–3 tuần để chạy contradiction check, chuẩn hóa thuật ngữ và dọn trang cũ. Vẫn nhẹ hơn tự bảo trì wiki thủ công nhiều, nhưng pattern chỉ sống nếu bạn duy trì đều đặn."
  - q: "File schema (CLAUDE.md / AGENTS.md) cần chứa gì?"
    a: "Ba nhóm nội dung: (1) ranh giới tầng — sources/ read-only, wiki/ là nơi agent duy nhất được viết, mọi thao tác kết thúc bằng cập nhật index + log; (2) quy ước trang — đặt tên kebab-case, frontmatter bắt buộc (tags, last_updated, source_count), chỉ wikilink lần nhắc đầu, không link trang chưa tồn tại; (3) workflow chuẩn cho Ingest / Query / Lint kèm định dạng entry log. Đây là file biến agent thành wiki maintainer kỷ luật thay vì chatbot generic — bạn và agent cùng tiến hóa nó theo thời gian."
---

Một LLM Wiki là knowledge base tồn tại lâu dài, cấu trúc chặt, làm bằng các file markdown liên kết chéo — do một LLM agent xây và bảo trì thay bạn. Thay vì re-derive câu trả lời từ raw documents ở mỗi lần hỏi như RAG, nó **biên dịch tri thức một lần và giữ cho nó luôn cập nhật**.

Tháng 4/2026, Andrej Karpathy đăng một [GitHub gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) mô tả pattern này. Đến nay gist có hơn 5.000 stars và hơn 10.000 forks — cộng đồng đang "bỏ phiếu bằng bàn phím". Bản dịch này đi theo bài viết gốc của [Kunal Ganglani](https://www.kunalganglani.com/blog/llm-wiki-karpathy-local-knowledge-base): không chỉ giải thích gist, mà cho biết **cái gì chạy được trong thực tế và cái gì gãy**.

**Trả lời nhanh:** LLM Wiki đáng xây không? Đáng, nếu bạn thường xuyên tổng hợp từ nhiều nguồn — papers, tài liệu kỹ thuật, meeting notes — và sẽ tiếp tục nạp thêm. Nếu chỉ thỉnh thoảng tra cứu, upload file lên ChatGPT hoặc NotebookLM đơn giản hơn. Dù chọn hướng nào, hãy dành thời gian cho bảo trì: contradiction check, đặt tên nhất quán, làm mới trang cũ.

<div style="margin:1.6em 0;">
  <span class="level-badge level-badge--basic">🟢 Cơ bản</span>
  <span class="level-badge">🆓 Free (Obsidian core)</span>
  <span class="level-badge">⏱️ Setup 15 phút</span>
</div>

## Bạn sẽ học được gì

<div class="lesson-grid">
  <div class="lesson-card">
    <p class="lesson-card__title">Vì sao compile-once thắng retrieve-per-query</p>
    <p>Khác biệt kiến trúc giữa LLM Wiki và RAG — và ranh giới khi nào nên dùng cái nào.</p>
  </div>
  <div class="lesson-card">
    <p class="lesson-card__title">Setup wiki trong 15 phút</p>
    <p>Obsidian vault + coding agent + gist của Karpathy dán vào system prompt — 6 bước.</p>
  </div>
  <div class="lesson-card">
    <p class="lesson-card__title">Cập nhật tăng dần không viết lại</p>
    <p>Workflow killer feature: list trang bị ảnh hưởng TRƯỚC, rồi update surgical có scope.</p>
  </div>
  <div class="lesson-card">
    <p class="lesson-card__title">Chọn đúng agent</p>
    <p>Claude Code, OpenAI Codex, Gemini CLI và model local qua Ollama — ưu nhược điểm thật.</p>
  </div>
  <div class="lesson-card">
    <p class="lesson-card__title">5 failure mode + cách sửa</p>
    <p>Context overflow, wiki drift, contradiction tích tụ, trang stale, over-linking.</p>
  </div>
  <div class="lesson-card">
    <p class="lesson-card__title">Framework 3 tầng của gist gốc</p>
    <p>Raw sources (immutable) — wiki (LLM sở hữu) — schema (CLAUDE.md): ranh giới trách nhiệm rõ ràng.</p>
  </div>
  <div class="lesson-card">
    <p class="lesson-card__title">3 operations: Ingest / Query / Lint</p>
    <p>Vòng đời vận hành wiki, kèm prompt mẫu dùng ngay — và trick "file câu trả lời tốt vào wiki".</p>
  </div>
  <div class="lesson-card">
    <p class="lesson-card__title">Đánh giá thẳng thắn</p>
    <p>Cái gì giữ vững, cái gì gây thất vọng, và chi phí bảo trì thật của pattern.</p>
  </div>
</div>

## LLM Wiki của Karpathy là gì?

Hầu hết engineer đã từng upload tài liệu lên ChatGPT hoặc Google NotebookLM. Bạn thả 10 file PDF vào, đặt câu hỏi, nhận một câu trả lời được tổng hợp từ các chunk được retrieve. Nó hoạt động. Nhưng hỏi một câu khác vào ngày mai, model lại bắt đầu từ con số 0. Không tích lũy. Không đối chiếu chéo. Không hiểu biết cộng hưởng.

**LLM Wiki dùng prompt pattern của Karpathy để biên dịch nguồn thành một knowledge base markdown tồn tại lâu dài, liên kết chéo với nhau.** Trong thực tế, đó là một folder các file markdown mà LLM agent đọc, viết và bảo trì. Mỗi file là một entity, một chủ đề hoặc một theme. Agent tự tạo cross-link giữa các trang, flag mâu thuẫn giữa các nguồn, và cập nhật tóm tắt khi bạn nạp tài liệu mới. **Bạn không bao giờ tự viết wiki. Bạn chỉ cung cấp nguồn, khám phá và đặt câu hỏi. Phần việc nặng thuộc về LLM.**

Câu quan trọng nhất trong gist là phép ẩn dụ của Karpathy:

> "Obsidian là IDE; LLM là programmer; wiki là codebase."

Cách định vị này quan trọng vì nó cho bạn biết chính xác quan hệ giữa các công cụ: bạn không "chat với AI về ghi chú của mình" — bạn đang chạy một **build process** tạo ra một artifact có cấu trúc. Điểm then chốt theo chính Karpathy: "Tri thức được biên dịch một lần rồi giữ cập nhật, không re-derive ở mỗi query. Đây là khác biệt then chốt: wiki là một artifact tồn tại lâu dài và cộng hưởng dần."

### Trong gist có gì?

Gist (ID `442a6bf555914893e9891c11519de94f`) ngắn một cách bất ngờ. Không phải tool. Không phải package cài được. Không hẳn là script. Đó là một **prompt pattern** — thứ Karpathy gọi là "an idea file, designed to be copy pasted to your own LLM Agent":

1. **Ý tưởng cốt lõi** — giải thích bằng văn xuôi vì sao biên dịch tri thức thành wiki tốt hơn retrieval kiểu RAG cho personal knowledge management.
2. **Mô tả workflow** — setup màn hình đôi của Karpathy: agent ở một bên, Obsidian ở bên kia.
3. **Ba use case** — cá nhân (goals, health, journal), nghiên cứu (papers, bài viết, luận điểm tiến triển), đọc sách (tổng hợp từng chương với trang nhân vật và theme).
4. **Chỉ thị ngầm cho agent** — gist được viết sao cho khi dán vào context, agent hiểu xây wiki kiểu gì, cấu trúc trang thế nào, xử lý cross-reference ra sao.

Cái gist KHÔNG có: cấu trúc thư mục cụ thể, prompt template cho agent, logic xử lý mâu thuẫn, hay hướng dẫn khi wiki vượt context window. Chính những khoảng trống đó là nơi kinh nghiệm dùng hằng ngày dạy bạn nhiều nhất.

## "Karpathy method": biên dịch một lần, truy vấn mãi mãi

"Karpathy method" — thuật ngữ cộng đồng đặt, không phải Karpathy tự dùng — quy về một quyết định kiến trúc duy nhất: **coi quản lý tri thức là bước biên dịch (compilation), không phải bước retrieve (retrieval).**

Trong RAG truyền thống: bạn lưu raw documents, embed chunks vào vector database, và retrieve các đoạn liên quan lúc query. Model tổng hợp ngay tại chỗ. Đây là kiến trúc stateless — mỗi query trả trọn chi phí tổng hợp.

Karpathy method đảo ngược: bạn trả chi phí tổng hợp **một lần, trước**, khi nạp một nguồn mới. Agent đọc nguồn, trích entity và claim, viết vào cấu trúc trang wiki hiện có. Từ đó tri thức được pre-compile thành markdown liên kết chéo, browsable. Query lúc này chỉ là đọc.

Tác giả gốc dẫn kinh nghiệm xây RAG pipeline cho chatbot conversational commerce ở Walmart (qua Firework): ở quy mô hàng triệu query mỗi ngày, cái quyết định chất lượng câu trả lời là **chất lượng retrieval, không phải model**. LLM Wiki kéo bài học đó đến tận cùng logic: nếu chất lượng retrieval quan trọng nhất, tại sao không bỏ hẳn retrieval và pre-compile câu trả lời?

Nói công bằng: pre-compilation hiệu quả tuyệt vời cho knowledge base cá nhân nơi bạn kiểm soát mọi nguồn. Nó **không thay thế RAG** cho hệ production với hàng triệu tài liệu và cập nhật real-time. Nhưng với cá nhân engineer đang xây research wiki, architecture decision log hay reading tracker — Karpathy method thực sự tốt hơn.

## LLM Wiki khác RAG chỗ nào?

| Khía cạnh | RAG truyền thống | LLM Wiki (Karpathy method) |
| --- | --- | --- |
| **Khi nào tổng hợp** | Lúc query | Lúc ingestion |
| **Trạng thái tri thức** | Stateless — dựng lại mỗi query | Persistent — artifact cộng hưởng |
| **Đối chiếu chéo** | Ngầm định (embedding similarity) | Tường minh (markdown link giữa các trang) |
| **Xử lý mâu thuẫn** | Không — conflict nổi lên ngẫu nhiên | Chủ động — agent flag khi ingestion |
| **Hạ tầng cần** | Vector DB, embedding model, retrieval pipeline | Folder markdown + LLM agent |
| **Phù hợp nhất** | Hệ quy mô lớn, nhiều user, real-time | Knowledge base cá nhân/nhóm, nghiên cứu |
| **Scale đến** | Hàng triệu tài liệu | Hàng trăm trang (giới hạn context) |
| **Chạy offline** | Chỉ với local LLM + vector DB local | Có, với bất kỳ local agent nào |

Ranh giới quyết định: **RAG scale theo chiều ngang với nhiều tài liệu hơn. LLM Wiki scale theo chiều dọc với độ tổng hợp sâu hơn.** Cần search 100.000 ticket hỗ trợ → dùng RAG. Cần tổng hợp 50 research papers thành một sự hiểu biết mạch lạc → LLM Wiki thắng, và không phải thắng sát nút.

## Setup LLM Wiki của riêng bạn: từng bước

Quá trình setup đơn giản đến mức gây hiểu nhầm. Chạy được mất 15 phút. Chạy **tốt** mất vài tuần lặp lại. Workflow tác giả đã chốt:

**Bước 1 — Tạo Obsidian vault.** Vault mới (hoặc một subfolder riêng trong vault hiện có). Tạo ba thư mục top-level: `sources/` cho raw input, `wiki/` cho các trang đã biên dịch mà agent sẽ viết, `_index/` cho danh mục thư mục tự sinh.

**Bước 2 — Chọn agent.** Cần một coding agent đọc ghi được file local: Claude Code, OpenAI Codex, Gemini CLI đều chạy được.

**Bước 3 — Dán gist của Karpathy vào system prompt.** Copy toàn bộ văn bản từ [gist gốc](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) vào SYSTEM hoặc project instructions của agent. Điều này cho agent mental model về cách cấu trúc wiki.

**Bước 4 — Thêm nguồn đầu tiên.** Thả một tài liệu (PDF, markdown, plain text) vào `sources/`. Nói với agent: "Đọc sources/my-paper.pdf và tích hợp vào wiki. Tạo trang entity mới khi cần, cập nhật trang hiện có nếu bị ảnh hưởng, thêm cross-link."

**Bước 5 — Review trong Obsidian.** Mở graph view. Bạn sẽ thấy node mới xuất hiện với link giữa chúng. Đọc các trang được sinh ra. Cảnh báo: **lần ingestion đầu tiên là bừa nhất** — agent đang dựng bộ xương wiki từ con số 0 và sẽ có vài lựa chọn cấu trúc kỳ lạ mà bạn cần sửa.

**Bước 6 — Lặp lại.** Hỏi về tài liệu. Agent thỉnh thoảng sẽ cập nhật trang wiki khi phát hiện khoảng trống. Thêm nguồn. Wiki cộng hưởng dần.

Cấu trúc file đã chốt: `wiki/` chứa một file markdown mỗi entity hoặc chủ đề (ví dụ `wiki/transformer-architecture.md`, `wiki/attention-mechanisms.md`). Mỗi file có YAML frontmatter với tags và ngày cập nhật cuối. `_index/` chứa các listing tự sinh giúp agent điều hướng khi wiki lớn.

## Kiến trúc 3 tầng — framework gốc trong gist

Bài của Ganglani tập trung kinh nghiệm thực chiến; phần dưới đây dịch **framework gốc từ gist của Karpathy** — tài liệu mô tả pattern được thiết kế để "copy paste vào LLM Agent của bạn". Karpathy nhấn mạnh gist là *idea file*: nó truyền ý tưởng, còn agent sẽ cụ thể hóa chi tiết cùng bạn. Framework chia tri thức thành **3 tầng với ranh giới trách nhiệm tường minh**:

**Tầng 1 — Raw sources (nguồn gốc).** Bộ sưu tập tài liệu bạn tuyển chọn: bài viết, papers, ảnh, data files. Tầng này **immutable** — agent chỉ đọc, không bao giờ sửa. Đây là source of truth của bạn.

**Tầng 2 — Wiki.** Thư mục các file markdown do agent sinh ra: trang tóm tắt, trang entity, trang khái niệm, so sánh, overview, synthesis. **Agent sở hữu tầng này 100%** — nó tạo trang, cập nhật khi có nguồn mới, giữ cross-reference, giữ nhất quán. Bạn đọc; agent viết.

**Tầng 3 — Schema.** Một file tài liệu (`CLAUDE.md` cho Claude Code hoặc `AGENTS.md` cho Codex) nói cho agent biết: wiki cấu trúc thế nào, conventions là gì, workflow nào cần theo khi ingest, trả lời câu hỏi, hay bảo trì. Karpathy gọi đây là file cấu hình then chốt — **nó là thứ biến agent thành một wiki maintainer kỷ luật thay vì một chatbot generic**. Bạn và agent cùng tiến hóa file này theo thời gian khi hiểu rõ domain của mình.

Tương ứng với 3 tầng, cây thư mục thực chiến (kết hợp đặt tên của Ganglani với schema của gist) trông như sau:

```
my-wiki/
├── CLAUDE.md              # Tầng 3: schema — luật cho agent
├── sources/               # Tầng 1: nguồn gốc — read-only tuyệt đối
│   ├── papers/
│   ├── articles/
│   └── meeting-notes/
├── wiki/                  # Tầng 2: agent sở hữu 100%
│   ├── entities/          # trang entity: người, công ty, công cụ, mô hình
│   ├── concepts/          # trang khái niệm: attention, RAG, embedding
│   └── synthesis/         # tổng hợp, so sánh, luận điểm đang tiến triển
├── _index/
│   └── index.md           # danh mục mọi trang + tóm tắt 1 dòng
├── log.md                 # nhật ký append-only
└── assets/                # ảnh tải về local (từ Web Clipper)
```

## Ba operations cốt lõi: Ingest, Query, Lint

Cả vòng đời vận hành wiki quy về ba thao tác:

### 1. Ingest — nạp nguồn mới

Bạn thả nguồn vào `sources/` và bảo agent xử lý. Flow mẫu: agent đọc nguồn → thảo luận takeaways chính với bạn → viết trang tóm tắt trong wiki → cập nhật index → cập nhật các trang entity/concept liên quan → append một entry vào log. **Một nguồn duy nhất có thể đụng tới 10–15 trang wiki.** Karpathy khuyên nạp từng nguồn một và tham gia sát sao (stay involved) — đọc tóm tắt, check cập nhật, hướng dẫn agent nhấn mạnh gì. Nhưng batch-ingest nhiều nguồn một lần với ít giám sát hơn cũng được — miễn bạn ghi workflow đã chọn vào schema cho các session sau.

### 2. Query — hỏi đáp có trích dẫn

Bạn hỏi; agent tìm trang liên quan, đọc, tổng hợp câu trả lời kèm citation. Câu trả lời có thể ở nhiều dạng: trang markdown, bảng so sánh, slide deck (Marp), biểu đồ (matplotlib), canvas. Insight quan trọng nhất của gist ở đây: **câu trả lời tốt nên được file ngược vào wiki thành trang mới.** Một so sánh bạn yêu cầu, một phân tích, một kết nối bạn phát hiện ra — những thứ đó có giá trị và không nên biến mất trong chat history. Cách này giúp *kết quả khám phá của bạn* cộng hưởng vào knowledge base giống như nguồn đã ingest.

### 3. Lint — health check định kỳ

Định kỳ, yêu cầu agent kiểm tra sức khỏe wiki: mâu thuẫn giữa các trang, claim stale đã bị nguồn mới thay thế, orphan page không có inbound link, khái niệm quan trọng được nhắc đến nhưng chưa có trang riêng, cross-reference thiếu, data gap có thể lấp bằng web search. Agent cũng giỏi đề xuất câu hỏi mới đáng điều tra và nguồn mới đáng tìm. **Đây là thao tác giữ wiki sống khi nó lớn dần.**

## index.md và log.md — hai file điều hướng

Hai file đặc biệt giúp agent (và bạn) điều hướng wiki khi nó lớn — mỗi file một mục đích riêng:

**`index.md` — định hướng nội dung.** Danh mục mọi thứ trong wiki: mỗi trang kèm link, tóm tắt một dòng, và tùy chọn metadata (ngày, số nguồn). Sắp theo category (entities, concepts, sources...). Agent cập nhật sau MỌI lần ingest. Khi trả lời query, agent đọc index **trước** để tìm trang liên quan rồi mới drill down — cách này hoạt động tốt bất ngờ ở quy mô vừa (~100 nguồn, vài trăm trang) và **tránh hẳn hạ tầng RAG embedding**.

**`log.md` — định hướng thời gian.** Ghi chép append-only mọi việc đã xảy ra và khi nào: ingest, query, lint pass. Tip thực dụng: nếu mỗi entry mở đầu bằng prefix nhất quán, log trở nên parse được bằng unix tools:

```markdown
## [2026-11-21] ingest | Attention Is All You Need
## [2026-11-21] query | So sánh BM25 và dense retrieval
## [2026-11-22] lint | Sửa 2 mâu thuẫn, gộp 1 trang trùng
```

```bash
# 5 thao tác gần nhất:
grep "^## \[" log.md | tail -5
```

Log cho bạn timeline tiến hóa của wiki và giúp agent biết gần đây đã làm gì — tránh làm lại việc cũ hoặc mâu thuẫn với quyết định trước.

## Hướng dẫn chi tiết: build LLM Wiki với Obsidian + AI từ con số 0

Phần này gom framework của gist + kinh nghiệm của Ganglani thành **quy trình chạy được ngay**. Tổng thời gian: ~15 phút dựng khung, vài tuần lặp để wiki đạt chất lượng.

### Bước A — Dựng khung và viết schema

Tạo cây thư mục như trên trong Obsidian vault. Việc quan trọng nhất và thường bị bỏ qua: **viết schema trước khi nạp nguồn đầu tiên.** Đây là điểm khác biệt giữa "agent kỷ luật" và "agent tự do sáng tạo lung tung". Template tối giản để bắt đầu (đặt vào `CLAUDE.md`):

```markdown
# LLM Wiki Schema

## Ranh giới
- `sources/` là READ-ONLY. Không bao giờ sửa, đổi tên hoặc xóa file ở đây.
- `wiki/` là tầng duy nhất bạn (agent) được viết. Một entity/concept = một file.
- Mọi thay đổi phải kết thúc bằng: cập nhật `_index/index.md` + append `log.md`.

## Quy ước trang wiki
- Tên file: kebab-case (vd: attention-mechanisms.md)
- Frontmatter YAML bắt buộc: tags, last_updated, source_count
- Chỉ wikilink lần nhắc ĐẦU TIÊN của mỗi entity trong một trang
- KHÔNG tạo wikilink đến trang chưa tồn tại
- Trang mới phải được thêm vào index.md kèm tóm tắt 1 dòng

## Workflow Ingest
1. Đọc nguồn, tóm tắt takeaways chính — cho tôi xem TRƯỚC khi viết wiki
2. Liệt kê các trang wiki bị ảnh hưởng — liệt kê thôi, CHƯA sửa
3. Chờ tôi duyệt scope, rồi cập nhật surgical (giữ nội dung cũ, thêm mới, flag mâu thuẫn)
4. Cập nhật index.md, append log.md với prefix "## [YYYY-MM-DD] ingest | <tên nguồn>"

## Workflow Lint (chạy khi tôi yêu cầu "lint wiki")
- Scan contradiction giữa các trang, liệt kê kèm tham chiếu trang + nguồn
- Trang stale: frontmatter last_updated > 30 ngày
- Orphan pages, khái niệm được nhắc ≥3 lần nhưng chưa có trang riêng
- Đề xuất 3 câu hỏi mới đáng điều tra dựa trên khoảng trống hiện có
```

Điểm mấu chốt của schema: nó mã hóa ngay từ đầu những failure mode mà Ganglani phát hiện sau nhiều tuần (xem phần bên dưới) — scoped update, quy ước link, contradiction flag, freshness tracking.

### Bước B — Nạp nguồn đầu tiên và hiệu chỉnh

Dán gist của [Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) vào system prompt của agent (bên cạnh schema), thả 1–2 nguồn vào `sources/`, chạy workflow Ingest. **Lần đầu sẽ bừa nhất** — agent đang dựng bộ xương. Mở graph view của Obsidian, sửa các lựa chọn cấu trúc kỳ lạ ngay: đổi tên trang, gộp trang trùng, chỉnh phân tầng entities/concepts. Những sửa tay này chính là chỗ bạn và agent cùng tiến hóa schema.

### Bước C — Thiết lập thói quen vận hành

Nhịp vận hành bền vững theo gist: **Ingest** mỗi khi có nguồn (kèm duyệt scope) → **Query** thoải mái, và nhớ file câu trả lời tốt vào wiki → **Lint** định kỳ (mỗi 2–3 tuần). Kết hợp tool hỗ trợ:

- **Obsidian Web Clipper** (browser extension): chuyển bài web thành markdown — cách nhanh nhất đưa nguồn vào `sources/`.
- **Tải ảnh về local:** Obsidian Settings → Files and links → đặt "Attachment folder path" thành `assets/`; gán hotkey cho "Download attachments for current file". Agent đọc và tham chiếu được ảnh trực tiếp thay vì URL dễ hỏng.
- **Graph view:** cách nhìn hình dạng wiki nhanh nhất — trang nào là hub, trang nào là orphan.
- **Marp + Dataview (plugin Obsidian):** Marp sinh slide từ nội dung wiki; Dataview query frontmatter YAML để tạo bảng động (trang theo tag, trang stale nhất...).
- **Git:** wiki chỉ là một repo markdown — bạn được version history, branching và collaboration miễn phí. `git diff` là công cụ review thay đổi của agent.
- **Search engine khi lớn:** ở quy mô nhỏ index.md là đủ; khi wiki lớn, [qmd](https://github.com/tobiastom/qmd) — local search cho markdown với hybrid BM25/vector + LLM re-ranking, có cả CLI (agent shell ra dùng) và MCP server (agent dùng như native tool).

### Bước D — scale lên khi wiki lớn

Quá ~150–200 trang, áp dụng master index và các fix failure mode ở phần dưới. Về lâu dài, theo dự đoán của Ganglani: agent-native IDE sẽ có sẵn "wiki mode", và hướng đi production là hybrid wiki + RAG.

## Agent nào làm LLM Wiki tốt nhất?

**Claude Code — lựa chọn tốt nhất hiện tại.** Xử lý long file reads tốt, viết markdown sạch với cross-link chuẩn, và agentic loop của nó hỗ trợ tự nhiên workflow "đọc nguồn, cập nhật nhiều trang wiki". Context window 200K đủ giữ một wiki tương đối lớn trong bộ nhớ khi cập nhật. Nhược điểm rõ ràng: bạn trả tiền theo token cho mỗi phiên bảo trì wiki, và các phiên đó cộng dồn.

**OpenAI Codex — chạy được nhưng có thói quen khó chịu:** hay cấu trúc lại các trang hiện có. Claude Code sửa surgical, Codex thi thoảng viết lại cả trang khi chỉ cần cập nhật một đoạn. Điều này gây **wiki drift** theo thời gian. Đã tốt hơn từ bản cập nhật tháng 6/2026, nhưng diff từ Claude Code vẫn dự đoán được hơn.

**Gemini CLI — context window lớn nhất (1M+ token)**, trên lý thuyết lý tưởng cho wiki lớn. Thực tế chất lượng cross-referencing yếu hơn: tạo trang được nhưng bỏ sót link hiển nhiên giữa các entity liên quan. Wiki dưới 50 trang thì ổn; vượt qua đó, Claude Code tạo graph kết nối tốt hơn.

**Model local qua Ollama — câu hỏi được hỏi nhiều nhất.** Được, nhưng có caveat thật: cần model instruction-following và sửa file mạnh. Qwen3 32B và Llama 3 70B xử lý được bảo trì wiki cơ bản nhưng struggle với multi-page update phức tạp. Trên M4 Max 64GB unified memory là dùng được; dưới mức đó, giới hạn context khiến việc này bực bội.

## Cập nhật nội dung mới không cần viết lại toàn bộ

Đây là câu hỏi được hỏi nhiều nhất — và cái gist gốc hầu như không đề cập. **Workflow cập nhật tăng dần là killer feature của pattern** khi làm đúng:

1. **Thả nguồn mới vào `sources/`.** Bất kỳ định dạng nào agent đọc được.
2. **Bắt agent xác định các trang bị ảnh hưởng TRƯỚC.** Prompt: "Đọc sources/new-paper.pdf. Liệt kê các trang wiki hiện có cần cập nhật dựa trên thông tin mới này. Chưa sửa gì cả."
3. **Review danh sách.** Đôi khi agent liệt kê 15 trang; bạn có thể chỉ muốn cập nhật 5. Đây là cơ hội thu hẹp phạm vi.
4. **Ra lệnh update surgical.** Prompt: "Chỉ cập nhật wiki/transformer-architecture.md và wiki/attention-mechanisms.md với các phát hiện mới từ sources/new-paper.pdf. Giữ nguyên nội dung hiện có, thêm thông tin mới, flag mọi mâu thuẫn."
5. **Chạy contradiction check.** Prompt: "Quét wiki tìm mọi claim mâu thuẫn nhau sau lần cập nhật vừa rồi. Liệt kê kèm tham chiếu trang."
6. **Review diff trong Obsidian.** Nếu dùng git (và bạn nên dùng), `git diff` cho thấy chính xác cái gì đã thay đổi.

**Insight then chốt: không bao giờ bảo agent "cập nhật wiki" mà không scope trang.** Một unscoped update trên wiki 100+ trang sẽ đốt token, tạo rewrite không cần thiết, và đưa vào những mâu thuẫn tinh vi. Quy trình trên mất 2–5 phút mỗi nguồn mới với Claude Code — nhanh hơn đáng kể so với tự đọc paper và cập nhật ghi chú tay, và chất lượng cross-referencing thậm chí tốt hơn đa số người làm bằng tay.

## Có phải đã có "LLM Wiki v2"?

Nói thẳng: **không có "LLM Wiki v2" chính thức.** Gist của Karpathy chỉ có một lần sửa kể từ 4/4/2026 — nó là phiên bản 1 và vẫn là tham chiếu chuẩn. Người ta search "llm wiki v2" vì ba lý do:

- **Community forks** — với hơn 10.000 forks, các fork hữu ích nhất thêm contradiction-check prompt, script sinh auto-index, và template theo use case (engineering ADR, book notes, research synthesis). Đó là "v2" theo tinh thần, nhưng không cái nào được Karpathy xác nhận.
- **Agent cải tiến** — Claude Code, Codex, Gemini CLI đều cập nhật đáng kể từ tháng 4/2026. Pattern chạy tốt hơn hôm nay không phải vì pattern đổi, mà vì các agent thực thi nó thông minh hơn.
- **Kỳ vọng một tool chính thức** — một số người mong ứng dụng đóng gói có GUI. Nó không tồn tại, và lẽ ra không nên: sức mạnh của pattern nằm ở sự tối giản — markdown files, một agent, một text editor.

Nếu muốn thứ gần nhất với "v2": lấy gist gốc, thêm workflow scoped-update ở trên, và thêm file tự sinh `_index/master-index.md` liệt kê mọi trang wiki kèm tóm tắt một dòng. **File index này là cải tiến lớn nhất so với gist thô.**

## So với Notion AI và Obsidian plugins?

**Notion AI** query nội dung workspace để sinh câu trả lời. Tiện, nhưng đó là RAG under the hood — stateless retrieval, không có synthesis tồn tại lâu dài, và dữ liệu của bạn nằm trên server Notion. Cần local AI và data sovereignty → Notion AI bị loại ngay.

**Obsidian plugins** (Copilot, Smart Connections...) thêm LLM capability vào Obsidian: search vault, sinh tóm tắt, trả lời về ghi chú. Nhưng chúng **không xây và không bảo trì wiki có cấu trúc thay bạn** — bạn vẫn là người tạo trang, viết tóm tắt, quản cross-link. LLM hỗ trợ, không sở hữu cấu trúc tri thức.

**LLM Wiki đảo ngược hoàn toàn mô hình sở hữu:** LLM sở hữu cấu trúc và nội dung wiki. Bạn sở hữu các nguồn và các câu hỏi. Bạn trở thành curator và editor — không phải author.

## Wiki gãy ở đâu, và sửa thế nào?

Pattern này có vấn đề thật. Đây là thứ thực sự gãy trong thực tế:

**1. Context window overflow — vấn đề số 1.** Wiki vượt khoảng 150–200 trang, phần lớn agent không giữ được toàn bộ wiki trong context khi cập nhật. Agent bắt đầu "quên" trang tồn tại → tạo trùng lặp hoặc bỏ sót cross-link. **Fix:** dùng master index (`_index/master-index.md`) liệt kê mọi trang kèm tóm tắt một dòng; bảo agent đọc index trước rồi chỉ load trang cần thiết. Giữ context khả thi ngay ở 300+ trang.

**2. Wiki drift.** Theo thời gian văn phong agent lệch: trang đầu ngắn gọn, trang sau dài dòng; tên entity không nhất quán ("transformer" vs "Transformer architecture" vs "the attention model"). **Fix:** thêm style guide vào system prompt — quy ước đặt tên, độ dài trang, template cấu trúc; review và chuẩn hóa mỗi 20–30 nguồn mới.

**3. Contradiction tích tụ.** Agent chỉ flag mâu thuẫn khi bạn yêu cầu rõ; trong cập nhật thường nhật nó không phải lúc nào cũng bắt được. Các claim mâu thuẫn có thể cùng tồn tại nhiều tuần. **Fix:** chạy prompt contradiction-check định kỳ hàng tuần: "Đọc mọi trang trong wiki/, liệt kê các claim mâu thuẫn nhau, kèm tham chiếu trang và nguồn chứng minh mỗi claim."

**4. Trang stale.** Một số trang được tạo ở giai đoạn ingestion đầu và không bao giờ cập nhật dù nguồn sau có thông tin liên quan. **Fix:** theo dõi độ mới bằng YAML frontmatter (`last_updated: 2026-07-10`); định kỳ hỏi: "Liệt kê mọi trang wiki chưa cập nhật trong 30 ngày mà có thông tin mới liên quan trong sources đã thêm từ lần cập nhật cuối của chúng."

**5. Over-linking.** Agent thỉnh thoảng link đến trang chưa tồn tại, hoặc link mọi lần nhắc một thuật ngữ dù link không thêm giá trị. Ít hại nhất nhưng khó chịu nhất. **Fix:** bảo agent chỉ link lần nhắc đầu tiên của mỗi entity trong một trang, và không bao giờ tạo link đến trang không tồn tại.

## Đánh giá thẳng thắn

**Cái gì giữ vững:** insight cốt lõi — compile, don't retrieve — là đúng.

**Cái gì bất ngờ:** pattern hợp với tài liệu kỹ thuật hơn cả use case sách mà Karpathy nêu — architecture decision records, onboarding docs, competitive analysis. Ngược lại, **"đọc sách" là use case yếu nhất**: sách có cấu trúc narrative mà định dạng wiki làm phẳng, đánh mất bối cảnh quan trọng.

**Cái gì thất vọng:** gánh nặng bảo trì. Mỗi 2–3 tuần mất 30–45 phút chạy contradiction check, chuẩn hóa thuật ngữ, dọn trang stale. Không phải con số 0 — nhưng nhẹ hơn nhiều so với bảo trì wiki thủ công. **"Zero maintenance" thì không.**

**Kết luận thẳng:** nếu bạn thường xuyên tổng hợp từ nhiều nguồn — papers, technical docs, bài viết, meeting notes — LLM Wiki tiết kiệm cho bạn vài giờ mỗi tuần. Nếu thỉnh thoảng mới tra cứu, cứ dùng NotebookLM hoặc ChatGPT file upload. **LLM Wiki thưởng cho người dùng đều đặn và gãy dưới sự bỏ bê.** Tác giả gốc chốt bằng một nhận xét đáng ghi lại: knowledge artifact — wiki page, prompt template hay RAG index production — chỉ cộng hưởng giá trị khi được bảo trì; ngừng nạp nguồn và chạy quality check là wiki bắt đầu phân hủy. Đó không phải lỗi của pattern — đó là bản chất của bất kỳ hệ tri thức sống nào.

## Pattern này sẽ đi về đâu?

Ba dự đoán từ bài gốc:

**Agent-native IDE sẽ hấp thụ pattern.** Hiện tại bạn phải tự setup workflow Obsidian + agent. Claude Code, Cursor hay Windsurf sẽ sớm ship tính năng "wiki mode" tự động hóa bước biên dịch — pattern hữu ích và đơn giản quá nên không thể mãi ở dạng gist.

**Context window sẽ xóa bài toán scale.** Trần 150–200 trang tồn tại vì giới hạn context. Gemini 1M+ token đã đẩy nó lên cao hơn; khi window 10M token trở nên phổ biến, LLM Wiki sẽ scale đến hàng nghìn trang mà không cần index workaround.

**Pattern sẽ hợp nhất với RAG trong production.** Với doanh nghiệp, pure compilation không scale và pure retrieval thiếu chiều sâu. Hybrid — một lớp wiki có cấu trúc được biên dịch trên kho tài liệu RAG-searchable — là đích đến: wiki xử lý synthesis và cross-referencing, RAG xử lý độ rộng và độ tươi.

## Bài này liên quan gì đến second brain của bạn?

Nếu bạn đang theo phương pháp tự xây second brain từng tầng trong bài [Xây dựng second brain bằng Obsidian từ số không](/bai-viet/xay-dung-second-brain-obsidian/) — nơi bạn tự viết ghi chú atomic, wikilink và MOC bằng tay — thì LLM Wiki chính là **tầng tiếp theo**: giữ nguyên tư duy "biên dịch tri thức", nhưng chuyển phần việc "compiler" (tổ chức, index, liên kết) cho LLM agent. Hai bài bổ sung cho nhau: một cái dạy bạn hiểu từng tầng để có thể đánh giá output của agent, một cái tự động hóa việc duy trì tầng đó.

## Nguồn

Bài này là bản dịch tiếng Việt (giữ nguyên thuật ngữ kỹ thuật tiếng Anh) của hai nguồn:

- **Gist gốc — "LLM Wiki"**: [A pattern for building personal knowledge bases using LLMs](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — Andrej Karpathy, 4/4/2026. Phần kiến trúc 3 tầng, ba operations, index/log và các tips dịch trực tiếp từ gist.
- **"LLM Wiki Setup: Karpathy's Knowledge Base"** — Kunal Ganglani, đăng 15/4/2026, cập nhật 2/11/2026. [Đọc bản gốc](https://www.kunalganglani.com/blog/llm-wiki-karpathy-local-knowledge-base). Phần kinh nghiệm thực chiến, so sánh agent, workflow cập nhật tăng dần, failure modes và đánh giá dịch từ bài này; bản dịch có lược bỏ các đoạn quảng bá cá nhân và liên kết chéo nội bộ của blog gốc, giữ nguyên toàn bộ nội dung kỹ thuật.

---
title: "GraphRAG: từ văn bản tới Knowledge Graph — xây dựng đồ thị tri thức bằng Microsoft GraphRAG"
description: "Hướng dẫn thực hành GraphRAG trên văn bản pháp luật tiếng Việt: trích xuất entity và relationship, tạo community bằng Leiden, Local Search vs Global Search, và kết quả benchmark so với dense retrieval."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-17"
cover: "/images/covers/posts/graphrag-knowledge-graph.jpg"
views: 540
---

Trong RAG thông thường, câu hỏi được mã hóa thành vector để tìm các đoạn văn bản liên quan. Cách này phù hợp khi câu trả lời nằm trong một vài đoạn liên quan trực tiếp. Khó khăn xuất hiện khi câu hỏi cần thông tin nằm ở **nhiều phần khác nhau** của tài liệu — ví dụ để trả lời *"Người thuê nhà có được tự ý chấm dứt hợp đồng khi căn nhà bị hư hỏng nghiêm trọng hay không?"*, hệ thống cần đồng thời: quy định về nghĩa vụ sửa chữa của bên cho thuê, điều kiện đơn phương chấm dứt hợp đồng, và quyền yêu cầu bồi thường của bên thuê. Các thông tin này nằm ở những đoạn khác nhau và không nhất thiết đều có độ tương đồng ngữ nghĩa cao với câu hỏi.

GraphRAG giải quyết bằng cách **bổ sung cấu trúc đồ thị**: thay vì chỉ dựa vào đoạn văn bản và vector, hệ thống còn biểu diễn các đối tượng và mối quan hệ giữa chúng — hỗ trợ kết nối và tổng hợp thông tin phân tán trong tập tài liệu.

## Microsoft GraphRAG tạo ra những gì?

[Microsoft GraphRAG](https://microsoft.github.io/graphrag/get_started/) là một triển khai của GraphRAG do Microsoft phát triển. Trong quá trình lập chỉ mục, nó tạo ra các loại dữ liệu chính:

- **Entity** — các đối tượng hoặc khái niệm quan trọng được phát hiện trong văn bản
- **Relationship** — mối liên hệ giữa các entity
- **Community** — các nhóm entity có liên kết chặt chẽ với nhau trong knowledge graph
- **Community report** — nội dung tổng hợp thông tin của từng community
- **Embedding** — vector biểu diễn một số nội dung để phục vụ truy xuất theo độ tương đồng

## Chuẩn bị môi trường

| Thành phần | Cấu hình sử dụng |
| --- | --- |
| Python | 3.12.4 |
| Microsoft GraphRAG | 3.1.1 |
| Mô hình ngôn ngữ | DeepSeek-V4-Flash (qua OpenRouter) |
| Mô hình embedding | BGE-M3 (qua API tự host bằng FastAPI) |

```bash
python -m pip install -r requirements.txt
graphrag --version          # kết quả cần hiển thị 3.1.1

# Khởi động API embedding BGE-M3 (tương thích OpenAI)
python -m uvicorn scripts.bge_m3_api:app --host 0.0.0.0 --port 8000
```

Workspace của GraphRAG gồm `settings.yaml`, `.env`, input, prompt và output. Tạo từ hai file mẫu:

```bash
cp .env.example .env
cp settings.yaml.example settings.yaml
```

## Chuẩn bị dữ liệu

Thực hành dùng bộ `YuITC/Vietnamese-Legal-Documents` trên Hugging Face — mỗi câu hỏi đi kèm văn bản pháp luật được gắn nhãn liên quan. Từ tập test, chọn 38 câu hỏi chứa "thử việc" hoặc "hợp đồng lao động", hợp nhất các cid xuất hiện → **63 văn bản pháp luật duy nhất** để xây GraphRAG.

Mỗi tài liệu gồm 4 trường: `id` (mã định danh từ cid — giữ lại để đối chiếu đánh giá sau này), `title`, `text` (nội dung được chia chunk), `source`. Cấu hình đọc file CSV trong `settings.yaml`:

```yaml
input:
  type: csv
  storage:
    type: file
    base_dir: corpus
    id_column: id
    title_column: title
    text_column: text
    file_pattern: "legal_labor\\.csv$"
```

## Cấu hình GraphRAG — những phần quan trọng

```yaml
chunking:
  type: tokens
  size: 600
  overlap: 80

extract_graph:
  entity_types:
    - government_body
    - legal_document
    - organization
    - person
    - process
    - legal_concept
  max_gleanings: 1
  prompt: prompts/extract_graph.txt

vector_store:
  type: lancedb
  db_uri: output/lancedb
  index_schema:
    text_unit_text:
      vector_size: 1024
    entity_description:
      vector_size: 1024
    community_full_content:
      vector_size: 1024

local_search:
  top_k_entities: 10
  top_k_relationships: 10
```

Điểm cần hiểu: **vector_size = 1024** vì BGE-M3 có vector đầu ra 1024 chiều — dùng model khác thì thay giá trị này. Chunk 600 token với overlap 80. Danh sách `entity_types` **không xác định trước** những thực thể cụ thể sẽ xuất hiện — nó chỉ giới hạn các nhóm mà LLM cần tập trung tìm kiếm (cơ quan nhà nước, văn bản pháp luật, tổ chức, cá nhân, quy trình, khái niệm pháp lý).

GraphRAG tạo embedding cho ba loại nội dung: `text_unit_text`, `entity_description` và `community_full_content`, lưu trong LanceDB.

## Lập chỉ mục — văn bản thành đồ thị tri thức

### Bước 1: Trích xuất thực thể và mối quan hệ

Mỗi văn bản được chia thành chunk — đơn vị nội dung đưa vào LLM để trích xuất. Prompt mặc định được điều chỉnh để đầu ra dùng tiếng Việt và giữ nguyên tên chính thức của văn bản pháp luật, cơ quan, tổ chức.

Với mỗi thực thể phát hiện được, LLM trả về ba thông tin: tên thực thể, loại thực thể, và mô tả dựa trên nội dung đoạn văn. Ví dụ một đoạn về Điều 24 của Bộ luật Lao động đề cập "người lao động", "người sử dụng lao động", "thử việc", "hợp đồng lao động" — LLM nhận diện các đối tượng này thành thực thể trong đồ thị.

Tiếp theo LLM xem xét mối liên hệ: nếu một điều luật dẫn chiếu đến một điều luật khác, hai điều luật trở thành hai thực thể với một relationship mô tả việc dẫn chiếu giữa chúng.

Sau khi các chunk được xử lý, GraphRAG **gộp kết quả**: cùng một thực thể xuất hiện ở nhiều chunk với cùng tên và loại → gộp thành một thực thể duy nhất. Vì một thực thể có thể được mô tả khác nhau ở nhiều chunk, GraphRAG dùng LLM tổng hợp thành một mô tả chung.

> ⚠️ **Cảnh báo quan trọng:** thực thể và mối quan hệ trong graph là kết quả do LLM tạo ra, **không phải dữ liệu đã được xác minh**. Mô hình có thể sinh thực thể quá chung chung, tách cùng một đối tượng thành nhiều thực thể, gộp nhầm các đối tượng khác nhau, hoặc tạo quan hệ chỉ vì hai thực thể cùng xuất hiện trong một đoạn. Hãy kiểm chứng và chuẩn hóa đồ thị trước khi đưa vào sử dụng.

### Bước 2: Tạo Community bằng thuật toán Leiden

Microsoft GraphRAG dùng thuật toán **Hierarchical Leiden** để phát hiện community trực tiếp từ cấu trúc graph: tìm cách phân node thành các nhóm sao cho node trong cùng nhóm liên kết chặt hơn so với node ở nhóm khác. Quá trình tạo ra hệ thống community **theo nhiều cấp** — community lớn chứa nhiều community nhỏ.

Vì Leiden dùng cấu trúc graph thay vì nhãn chủ đề có sẵn, community **không nhất thiết tương ứng** với một document hay một chương: thực thể nằm ở nhiều văn bản khác nhau vẫn có thể thuộc cùng một community nếu chúng được kết nối với nhau trong graph.

### Bước 3: Community report

Với mỗi community, GraphRAG tập hợp thực thể, mối quan hệ và nội dung liên quan rồi yêu cầu LLM viết bản tổng hợp — **community report**. Phân biệt: community cho biết nhóm thông tin nào đang liên kết với nhau; community report diễn giải và tổng hợp nhóm đó thành văn bản. Community report đặc biệt quan trọng cho Global Search.

### Chạy lập chỉ mục

Ta tận dụng pipeline chuẩn sẵn có của Microsoft GraphRAG:

```python
from graphrag.config.load_config import load_config
from graphrag.index.run.run_pipeline import run_pipeline
from graphrag.index.workflows.factory import PipelineFactory

async def build(root):
    config = load_config(root_dir=root)
    # Lấy standard indexing pipeline của Microsoft GraphRAG
    pipeline = PipelineFactory.create_pipeline(config, "standard")
    async for result in run_pipeline(pipeline, config):
        if result.error:
            raise result.error
```

```bash
python scripts/run_index.py .
# Nếu bảng Parquet đã tồn tại, chỉ cần chạy lại embedding:
python scripts/run_index.py . --workflow generate_text_embeddings
```

GraphRAG dùng cache để tái sử dụng kết quả đã hoàn thành — chạy lại sau gián đoạn không gọi lại LLM cho phần không thay đổi.

### Kết quả lập chỉ mục

| Thành phần | Số lượng |
| --- | --- |
| Văn bản | 63 |
| Text unit | 68 |
| Thực thể | 508 |
| Mối quan hệ | 1.043 |
| Community | 37 |
| Community report | 37 |

Kết quả lưu trong `output/` dưới dạng bảng Parquet: `documents.parquet`, `text_units.parquet`, `entities.parquet`, `relationships.parquet`, `communities.parquet`, `community_reports.parquet` và `stats.json`.

> ℹ️ Số lượng thực thể, mối quan hệ và community **thay đổi giữa các lần chạy** vì phụ thuộc output của LLM — các giá trị trên là của một lần chạy cụ thể.

## Truy vấn: Local Search và Global Search

### Local Search — tìm quanh thực thể

Bắt đầu bằng việc tìm entity liên quan đến câu hỏi, rồi khai thác vùng lân cận trong graph: relationship, entity liên quan, chunk nguồn. Context cùng câu hỏi đưa vào LLM để sinh câu trả lời.

```bash
graphrag query \
  "Có được ghi thỏa thuận thử việc trong hợp đồng lao động không?" \
  --root . --method local
```

Phù hợp với câu hỏi tập trung vào **một đối tượng, khái niệm, quy định hoặc mối quan hệ cụ thể**.

### Global Search — tổng hợp toàn corpus

Không bắt đầu từ entity cụ thể. Global Search dùng các community report để tổng hợp trên phạm vi rộng, xử lý nhiều report theo cơ chế **map–reduce**: bước map đưa từng nhóm report cùng câu hỏi vào LLM để rút ra ý liên quan và đánh giá mức quan trọng; các ý được gom thành context mới; bước reduce đưa context vào LLM lần nữa để tổng hợp câu trả lời cuối.

```bash
graphrag query \
  "Các nhóm nghĩa vụ chính của doanh nghiệp trong quan hệ lao động là gì?" \
  --root . --method global \
  --community-level 0 \
  --response-type "List of 3-5 points with source names"
```

`--community-level` xác định cấp community được dùng, `--response-type` quy định dạng câu trả lời. Phù hợp với câu hỏi cần **tổng hợp thông tin từ nhiều phần** của corpus.

## Ba ví dụ khi GraphRAG có lợi thế

**Case 1 — Chữ ký điện tử và hợp đồng gửi qua mạng.** Câu hỏi: *"Ảnh chữ ký của giám đốc trên bảng lương và hợp đồng gửi qua mạng có giá trị như chữ ký tay không?"* Cần hai nhóm thông tin: giá trị pháp lý của hợp đồng dạng thông điệp dữ liệu **và** điều kiện để chữ ký điện tử hợp lệ. Dense retrieval lấy được nhóm đầu nhưng thiếu điều kiện xác thực chữ ký. Global Search tổng hợp từ nhiều community — câu trả lời không chỉ xác nhận hợp đồng điện tử có giá trị pháp lý mà còn chỉ ra giá trị chữ ký phụ thuộc vào điều kiện xác thực.

**Case 2 — Thử việc, BHXH và công đoàn.** Câu hỏi: *"Người thử việc theo thỏa thuận riêng, chưa ký hợp đồng chính thức, có phải đóng BHXH và có quyền vào công đoàn không?"* Ba nhóm thông tin: thỏa thuận thử việc, điều kiện tham gia BHXH bắt buộc, quyền gia nhập công đoàn. Dense tìm được thử việc và công đoàn nhưng thiếu quy định xác định đối tượng BHXH bắt buộc — mô hình có thể suy rộng từ nghĩa vụ BHXH nói chung và đưa kết luận sai. Global Search đặt cả ba quy định vào cùng ngữ cảnh: BHXH phụ thuộc loại và thời hạn hợp đồng, quyền công đoàn xét theo căn cứ khác.

**Case 3 — Hợp đồng mang tên "cộng tác viên".** Câu hỏi: *"Gọi giấy tờ là hợp đồng cộng tác viên nhưng vẫn trả lương và quản lý hằng ngày có làm mất nghĩa vụ đóng BHXH không?"* Cần hai bước suy luận liên tiếp: xác định bản chất quan hệ từ dấu hiệu trả lương và sự quản lý → đối chiếu với điều kiện tham gia BHXH. Global Search còn chỉ ra corpus không đề cập trực tiếp đến tên gọi này — không thể chỉ dựa vào tên giấy tờ để kết luận.

## Đánh giá khả năng truy xuất

So sánh hai phương pháp trên 26 câu hỏi tình huống: **Dense** (truy xuất trực tiếp bằng vector) và **Graph + RRF** (bổ sung nhánh truy xuất từ community, hợp nhất bằng Reciprocal Rank Fusion với trọng số Dense 1,0 và community 0,5).

| Phương pháp | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
| --- | --- | --- | --- | --- | --- |
| Dense | **0,3205** | 0,7532 | 0,9135 | **0,8333** | **0,7804** |
| Graph + RRF | 0,2949 | **0,8205** | 0,9135 | 0,7821 | 0,7650 |

Graph + RRF đạt Recall@5 cao hơn (0,8205 so với 0,7532) — bổ sung văn bản từ community giúp tìm được nhiều văn bản liên quan hơn trong 5 kết quả đầu. Tuy nhiên Dense đạt Recall@1, MRR và nDCG cao hơn: **Graph + RRF cải thiện độ bao phủ ở top-5 nhưng chưa cải thiện chất lượng xếp hạng tổng thể**.

## Tổng kết

Pipeline này chuyển 63 văn bản pháp luật tiếng Việt thành đồ thị tri thức với 508 thực thể, 1.043 mối quan hệ, 37 community và 37 community report — sẵn sàng cho Local Search và Global Search. Ba lưu ý khi áp dụng: đừng vội tin đồ thị ngay sau lập chỉ mục — mở vài thực thể, vài quan hệ ra đối chiếu với văn bản gốc; và nếu corpus của bạn lớn hơn nhiều, hãy thử nghiệm lại trên chính dữ liệu đó, vì lợi ích của GraphRAG thường chỉ rõ ràng khi corpus đủ lớn và đủ phức tạp.

## Bài liên quan

- Trước đó: [Hybrid Search với BM25, Dense Retrieval và RRF](/bai-viet/hybrid-search-bm25-dense-rrf/)
- Tiếp theo: [Multi-hop RAG trên văn bản pháp luật tiếng Việt](/bai-viet/multi-hop-rag-langgraph/)

## Nguồn

- Tài liệu chính thức: [GraphRAG Getting Started](https://microsoft.github.io/graphrag/get_started/), [CLI Reference](https://microsoft.github.io/graphrag/cli/), [Indexing Methods](https://microsoft.github.io/graphrag/index/methods/), [Global Search](https://microsoft.github.io/graphrag/query/global_search/)
- Mã nguồn: [microsoft/graphrag](https://github.com/microsoft/graphrag), [RAG_Advanced_GraphRAG (repo thực hành)](https://github.com/Hoanghung0603/RAG_Advanced_GraphRAG.git)
- Nội dung biên tập lại từ bài thực hành GraphRAG của AI Guru x TiniX theo phong cách LearnWithHuy; kết quả lập chỉ mục và benchmark là của một lần chạy cụ thể.

---
title: "RAG nâng cao: cẩm nang từ Hybrid Search đến đánh giá hệ thống"
description: "Cẩm nang gộp trọn 5 bài RAG nâng cao trong một trang: hybrid search BM25 + dense + RRF, GraphRAG knowledge graph, multi-hop RAG với LangGraph, multimodal RAG cho tài liệu tiếng Việt và đánh giá chất lượng bằng Ragas."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-24"
cover: "/images/covers/posts/hybrid-search-bm25-dense-rrf.jpg"
featured: false
views: 180
faq:
  - q: "Cẩm nang này gồm những gì?"
    a: "Toàn bộ 5 bài trước đây đăng riêng giờ gộp trong một trang, chia thành 5 phần đánh số — đọc tuần tự hoặc nhảy tới phần cần đều được."
  - q: "Nên đọc theo thứ tự không?"
    a: "Các phần được xếp theo thứ tự học gợi ý. Đọc lộn vẫn hiểu vì mỗi phần đứng độc lập, nhưng lần đầu học thì nên theo thứ tự. Tổng thời gian đọc khoảng 58 phút."
---

## 01. Hybrid Search với BM25, Dense Retrieval và RRF: xây dựng tìm kiếm tài liệu tiếng Việt từ con số 0

Bạn đang xây một ô tìm kiếm cho kho văn bản pháp luật. Người dùng hỏi "thành lập công ty cần thủ tục hồ sơ nào", trong khi corpus lại dùng cụm "đăng ký doanh nghiệp" — nếu chỉ so khớp từ khóa, hệ thống bỏ lỡ tài liệu đúng vì hai câu không dùng chung từ. Ngược lại, khi người dùng nhập chính xác `01/2021/NĐ-CP`, model ngữ nghĩa không giữ chuỗi số hiệu tốt bằng tìm kiếm từ khóa.

Vì vậy ta dùng **hai góc nhìn song song** và hợp nhất bằng **RRF**:

- **BM25 hỏi:** "Câu hỏi và tài liệu có dùng chung những từ quan trọng nào?"
- **Dense retrieval hỏi:** "Câu hỏi và tài liệu có nói về cùng một ý, dù cách diễn đạt khác nhau?"

Luồng xử lý: câu hỏi hội thoại → rewrite (giữ cả câu gốc) → BM25 và dense retrieval chạy song song → RRF hợp nhất → top-k kết quả kèm nguồn.

> ⚠️ **Ranh giới cần nhớ:** hệ thống chỉ làm nhiệm vụ *tìm tài liệu và hiển thị nguồn*. Retrieval giúp bạn tìm nơi cần đọc — nó không chứng minh văn bản còn hiệu lực hay cho biết văn bản áp dụng thế nào trong một vụ việc cụ thể. Không phải tư vấn pháp lý.

### Bốn thành phần trước khi viết code

#### BM25 — tìm kiếm từ khóa thông minh

BM25 ưu tiên tài liệu chứa các từ quan trọng xuất hiện trong câu hỏi, có điều chỉnh hai hiện tượng: một từ lặp lại nhiều lần trong cùng tài liệu không được phép làm điểm tăng mãi, và một tài liệu dài không tự động được lợi chỉ vì có nhiều từ hơn. Điểm mạnh: số hiệu, tên cơ quan, thuật ngữ pháp lý. Điểm yếu: không tự hiểu hai cách gọi cùng một chủ đề.

Lưu ý kỹ thuật: thư viện `rank-bm25` nhận danh sách token chứ không tự quyết định cách tách từ — corpus và câu hỏi phải đi qua **cùng một hàm tiền xử lý**. Hai tokenizer khác nhau → điểm BM25 sai dù code vẫn chạy.

#### Dense retrieval — tìm kiếm ngữ nghĩa

Embedding model biến mỗi câu thành một vector (trong bài này: 1.024 số). Những câu gần nghĩa tạo ra vector gần nhau — nhờ vậy câu hỏi đời thường vẫn tìm thấy đoạn ghi bằng thuật ngữ chính thức, dù không trùng từ khóa. Model đa ngôn ngữ chạy được trên CPU, nhưng **không được huấn luyện riêng cho pháp luật Việt Nam** — phải benchmark thay vì mặc định nó hiểu đúng.

#### RRF — hợp nhất theo thứ hạng

BM25 score (8) và cosine score (0.4) không cùng thang đo — cộng trực tiếp sẽ làm một retriever lấn át retriever còn lại. RRF bỏ qua score gốc, chỉ nhìn vị trí:

$$\text{RRF}(d) = \sum_{r \in R} \frac{w_r}{k + \text{rank}_r(d)}$$

Trong đó `d` là một tài liệu, `R` là tập retriever, `rank_r(d)` là vị trí của tài liệu trong retriever `r`, `w_r` là trọng số tin cậy, `k` làm chênh lệch giữa các vị trí đầu bớt cực đoan.

**Ví dụ:** tài liệu đứng hạng 1 ở BM25 và hạng 2 ở dense (hai trọng số đều 1) nhận `1/61 + 1/62 ≈ 0,0325`. Tài liệu chỉ đứng hạng 1 ở BM25 nhận khoảng `0,0164`. Tài liệu được cả hai retriever đồng thuận có lợi thế rõ rệt — đây là trực giác quan trọng nhất của RRF.

#### Query rewriting — viết lại câu hội thoại

Sau khi hỏi về đăng ký doanh nghiệp, người dùng hỏi tiếp "thủ tục này thực hiện ở đâu?" — cụm "thủ tục này" không cho biết thủ tục nào. Query rewriting dùng lịch sử để tạo câu độc lập: "thủ tục đăng ký doanh nghiệp qua mạng thực hiện ở đâu?". Nhưng rewriter cũng đoán sai được — hệ thống có trách nhiệm phải **giữ cả câu gốc lẫn câu đã viết lại** để kiểm tra, thay vì âm thầm thay đổi ý người dùng.

### Chuẩn bị môi trường và dự án

```bash
git clone https://github.com/lengocquanggit255/demo-hybrid-retrieval.git
cd demo-hybrid-retrieval

python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt

# Windows PowerShell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Cấu trúc dự án — mỗi file một nhiệm vụ, không cần database hay dịch vụ bên ngoài:

```
demo-hybrid-retrieval/
|-- corpus.jsonl          # tập tài liệu nguồn
|-- queries.jsonl         # câu hỏi có đáp án đúng đã biết
|-- hybrid_search.py      # pipeline chính
|-- prepare_subset.py     # tạo tập con có thể tái lập
|-- requirements.txt
`-- subset_manifest.json
```

Dữ liệu lấy từ split test của bộ `YuITC/Vietnamese-Legal-Documents` trên Hugging Face — mỗi câu hỏi có sẵn danh sách cid liên quan, nghĩa là **có ground truth retrieval** thay vì tự đặt câu hỏi rồi tự chọn đáp án. Tập con gồm 20 query một tài liệu đúng, 10 query nhiều tài liệu đúng và 120 văn bản thật.

Corpus lưu dạng JSONL — mỗi dòng là một đơn vị retrieval độc lập:

```json
{
  "id": "63171",
  "title": "CID 63171: Điều 5. Thời hiệu xử phạt...",
  "text": "Nội dung điều khoản trong bộ dữ liệu...",
  "source": "https://huggingface.co/datasets/YuITC/Vietnamese-Legal-Documents"
}
```

### Bước 1 — Đọc dữ liệu và tiền xử lý

Kiểm tra schema ngay khi nạp để lỗi corpus xuất hiện **trước khi** model bắt đầu tải hoặc encode:

```python
def load_corpus(path):
    with path.open(encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    required = {"id", "title", "text", "source"}
    if not rows or any(required - row.keys() for row in rows):
        raise ValueError("Invalid corpus schema")
    return rows
```

BM25 cần tách câu thành token. Baseline dùng biểu thức chính quy Unicode và chuyển chữ về dạng thường:

```python
TOKEN_RE = re.compile(r"\w+", re.UNICODE)

def tokenize(text):
    return TOKEN_RE.findall(text.lower())
```

Đây là phương pháp tách từ đơn giản nhất — câu "Đăng ký doanh nghiệp qua mạng" thành `["đăng", "ký", "doanh", "nghiệp", "qua", "mạng"]`. Đủ gọn để theo dõi.

### Bước 2 — Tạo hai retriever

**BM25:**

```python
texts = [f"{row['title']}. {row['text']}" for row in rows]
bm25 = BM25Okapi([tokenize(text) for text in texts])
bm25_scores = np.asarray(bm25.get_scores(tokenize(query)))
bm25_order = np.argsort(-bm25_scores, kind="stable").tolist()
```

Ghép title với text để tên và số hiệu cũng tham gia tìm kiếm; tokenize corpus một lần để tạo index; kiểu sort stable giữ thứ tự xác định khi hai tài liệu bằng điểm — giúp kết quả lặp lại được khi debug và benchmark.

**Dense retrieval:**

```python
MODEL_NAME = "BAAI/bge-m3"
model = SentenceTransformer(MODEL_NAME)
embeddings = model.encode(texts, batch_size=4, normalize_embeddings=True)
query_embedding = model.encode(query, normalize_embeddings=True)
dense_scores = np.asarray(embeddings @ query_embedding)
```

Vector corpus tạo một lần khi khởi động; mỗi câu hỏi mới chỉ cần encode câu hỏi rồi nhân với ma trận vector tài liệu. Cả hai phía đã chuẩn hóa độ dài 1, tích vô hướng tương đương cosine similarity. Vài chục bản ghi thì NumPy đủ nhanh — thêm vector database ở giai đoạn này chỉ thêm server, schema và kết nối mà không giúp hiểu retrieval rõ hơn.

### Bước 3 — Kết hợp hai bảng xếp hạng bằng RRF

```python
def rrf(rankings, weights, k=60):
    if len(rankings) != len(weights) or k < 1:
        raise ValueError("Invalid RRF inputs")
    size = max(max(order) for order in rankings) + 1
    scores = np.zeros(size, dtype=float)
    for order, weight in zip(rankings, weights, strict=True):
        for rank, doc_index in enumerate(order, start=1):
            scores[doc_index] += weight / (k + rank)
    return np.argsort(-scores, kind="stable").tolist(), scores
```

Không chuẩn hóa BM25 và cosine score trước khi fusion — RRF chỉ làm việc với rank. Hai trọng số mặc định đều bằng 1 để bắt đầu công bằng; chỉ thay đổi khi đã có tập câu hỏi với relevance label.

### Bước 4 (tùy chọn) — Viết lại câu hỏi bằng LLM

Gửi history và câu hỏi mới đến một LLM qua API tương thích OpenAI, với chỉ dẫn nghiêm ngặt: chỉ dùng thông tin có trong lịch sử, không tự thêm tên người/tổ chức/điều kiện mới, câu hỏi đã rõ nghĩa thì giữ nguyên. Lưu cả `original`, `rewritten`, `model`, phiên bản prompt và request ID trong cùng trace. Nếu lời gọi API thất bại hoặc kết quả rỗng, dùng lại câu gốc thay vì dừng toàn bộ retrieval.

```bash
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="your-api-key"
export LLM_MODEL="your-model-id"
```

### Bước 5 — Chạy truy vấn đầu tiên

```bash
python hybrid_search.py \
  --query "Phó Tổng Giám đốc Ngân hàng Chính sách xã hội được xếp lương theo bảng lương như thế nào?" \
  --top-k 3
```

Kết quả kiểm thử trên subset:

| Phương pháp | Hạng | Tài liệu |
| --- | --- | --- |
| BM25 | 1 | CID 140864: chế độ tiền lương và phụ cấp |
| Dense | 1 | CID 140864: chế độ tiền lương và phụ cấp |
| Dense | 2 | CID 117750: Phó Viện trưởng VKSND tối cao |
| Hybrid | 1 | CID 140864: chế độ tiền lương và phụ cấp |
| Hybrid | 2 | CID 124460: dự toán chi NSNN |

Cả BM25 và dense đều đưa tài liệu đúng lên đầu nên RRF giữ ở hạng 1. Các hạng sau khác nhau: BM25 nghiêng về từ khóa "phụ cấp", dense ưu tiên chức danh gần nghĩa. Độ trễ mẫu: 3,54 ms cho BM25, 123,73 ms cho dense query, 0,44 ms cho fusion (không gồm thời gian tải model lần đầu).

### Bước 6 — Đánh giá bằng benchmark

Một vài truy vấn trông đúng chưa đủ chứng minh hệ thống tốt — benchmark buộc dùng cùng tập câu hỏi, cùng tài liệu đúng và cùng cách tính điểm cho mọi cấu hình:

```bash
python hybrid_search.py --self-check   # kết quả mong đợi: OK
python hybrid_search.py --benchmark    # tạo evaluation/ với per_query.csv và metrics.json
```

| Retriever | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
| --- | --- | --- | --- | --- | --- |
| BM25 | 0,6611 | 0,9222 | 0,9389 | 0,8806 | 0,8658 |
| Dense | 0,7278 | **0,9389** | **0,9833** | 0,9311 | 0,9208 |
| Hybrid RRF | **0,7944** | 0,9222 | 0,9722 | **0,9708** | **0,9483** |

**Cách đọc:** Recall@k là tỷ lệ tài liệu ground truth xuất hiện trong k vị trí đầu; MRR@10 chỉ nhìn vị trí của tài liệu đúng đầu tiên (hạng 1, 2, 3 đóng góp 1, 1/2, 1/3); nDCG@10 thưởng việc đưa nhiều tài liệu đúng lên sớm.

Hybrid đứng đầu ở Recall@1, MRR@10 và nDCG@10; Dense thắng Recall@5/10. Kết quả cho thấy RRF đưa tài liệu đúng đầu tiên lên sớm hơn, nhưng **không thắng dense ở mọi cutoff** — có 3/30 query mà hybrid tốt hơn dense-only. Đừng kết luận từ một ví dụ thuận lợi.

Latency (150 mẫu sau warm-up): BM25 p50 = 0,48 ms, Dense p50 = 100,23 ms, Hybrid end-to-end p50 = 100,86 ms — phần tăng chủ yếu từ BM25 vì phép cộng RRF rất nhỏ.

### Bước 7 — Chọn top-k, trọng số và hằng số RRF

Không có đáp án đúng cho mọi project. Cách an toàn là bắt đầu từ baseline rồi thay **từng biến một**:

1. **Chọn retrieval top-k.** Kết quả hiển thị trực tiếp → top-3; còn bước rerank → bắt đầu từ 10–20 candidate.
2. **Giữ RRF k = 60 lần đầu**, sau đó thử lưới nhỏ 20, 40, 60, 100 trên validation set.
3. **Trọng số bắt đầu 1:1.** Câu hỏi thường chứa số hiệu và thuật ngữ chính xác → tăng BM25. Người dùng diễn đạt đời thường → tăng dense.
4. **Đo lại chất lượng và latency.** Không chọn tham số chỉ vì một câu hỏi mẫu có vẻ tốt hơn.

```bash
python hybrid_search.py --benchmark \
  --top-k 5 --rrf-k 60 \
  --bm25-weight 1.2 --dense-weight 1.0
```

Quy trình tối thiểu: cố định validation set → thử lưới nhỏ → chọn cấu hình theo MRR/Recall và latency → báo cáo cuối trên test set **chưa dùng để tuning**. Thay nhiều tham số cùng lúc thì bạn không biết thay đổi nào thực sự tạo ra cải thiện.

### Các lỗi thường gặp

| Biểu hiện | Nguyên nhân thường gặp | Cách kiểm tra và sửa |
| --- | --- | --- |
| Lỗi import module | Virtual environment chưa active hoặc pip khác interpreter | `python -m pip show ...` và `python --version` |
| Không tải được model | Mất mạng, cache chưa đủ, bật offline quá sớm | Bỏ `HF_HUB_OFFLINE`; tải một lần rồi mới thử offline |
| BM25 toàn điểm 0 | Query và corpus dùng tokenizer khác nhau | In `tokenize(query)` và một tài liệu; kiểm tra Unicode |
| Dense trả dữ liệu nhiễu | Model tổng quát chưa phù hợp miền hoặc chunk chứa nhiều ý | Thêm relevance label, giảm chunk, thử model phù hợp tiếng Việt |
| Hybrid kém dense | BM25 kéo tài liệu trùng từ nhưng sai ý lên cao | Giảm trọng số BM25, tăng candidate pool hoặc thêm reranker |
| Kết quả thay đổi sau update | Model, dependency hoặc corpus đã đổi | Pin phiên bản; ghi hash corpus và ngày benchmark |
| Rewrite đổi ý người dùng | History không đúng chủ đề | Log original/rewritten; cho phép tắt rewrite; không rewrite nhiều vòng |
| Out of memory | Encode quá nhiều văn bản một batch | Giảm batch size, encode theo lô, lưu embedding ra đĩa |

### Tổng kết

Giá trị của hybrid không nằm ở chỗ nó luôn thắng — mà ở việc BM25 và dense nhìn dữ liệu theo hai cách khác nhau, nhờ đó **bù lỗi cho nhau**. RRF là một phép fusion nhỏ và dễ kiểm tra, nhưng chất lượng cuối cùng phụ thuộc vào corpus có nguồn, tiền xử lý nhất quán, log query rewrite và bộ benchmark có cả failure case. Giữ được những yếu tố đó, bạn thay model hay hạ tầng mà vẫn biết hệ thống thực sự tốt hơn hay chỉ trông có vẻ phức tạp hơn.

### Bài liên quan

- [LLM hoạt động như thế nào?](/bai-viet/llm-hoat-dong-nhu-the-nao/) — nền tảng embedding
- Tiếp theo trong lộ trình RAG nâng cao: GraphRAG: từ văn bản tới Knowledge Graph

### Nguồn

- [Công thức RRF gốc — Cormack, Clarke & Büttcher, SIGIR 2009](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)
- [rank-bm25](https://github.com/dorianbrown/rank_bm25) · [Model BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) · [Sentence Transformers Semantic Search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
- Dataset: [YuITC/Vietnamese-Legal-Documents](https://huggingface.co/datasets/YuITC/Vietnamese-Legal-Documents) (chỉ dùng cho benchmark trong phạm vi demo, không phải URL chính thức của văn bản pháp luật)
- Nội dung biên tập lại từ bài thực hành Hybrid Search của AI Guru x TiniX theo phong cách LearnWithHuy; số liệu benchmark là kết quả quan sát trên máy cụ thể, không phải cam kết SLA.

---

## 02. GraphRAG: từ văn bản tới Knowledge Graph — xây dựng đồ thị tri thức bằng Microsoft GraphRAG

Trong RAG thông thường, câu hỏi được mã hóa thành vector để tìm các đoạn văn bản liên quan. Cách này phù hợp khi câu trả lời nằm trong một vài đoạn liên quan trực tiếp. Khó khăn xuất hiện khi câu hỏi cần thông tin nằm ở **nhiều phần khác nhau** của tài liệu — ví dụ để trả lời *"Người thuê nhà có được tự ý chấm dứt hợp đồng khi căn nhà bị hư hỏng nghiêm trọng hay không?"*, hệ thống cần đồng thời: quy định về nghĩa vụ sửa chữa của bên cho thuê, điều kiện đơn phương chấm dứt hợp đồng, và quyền yêu cầu bồi thường của bên thuê. Các thông tin này nằm ở những đoạn khác nhau và không nhất thiết đều có độ tương đồng ngữ nghĩa cao với câu hỏi.

GraphRAG giải quyết bằng cách **bổ sung cấu trúc đồ thị**: thay vì chỉ dựa vào đoạn văn bản và vector, hệ thống còn biểu diễn các đối tượng và mối quan hệ giữa chúng — hỗ trợ kết nối và tổng hợp thông tin phân tán trong tập tài liệu.

### Microsoft GraphRAG tạo ra những gì?

[Microsoft GraphRAG](https://microsoft.github.io/graphrag/get_started/) là một triển khai của GraphRAG do Microsoft phát triển. Trong quá trình lập chỉ mục, nó tạo ra các loại dữ liệu chính:

- **Entity** — các đối tượng hoặc khái niệm quan trọng được phát hiện trong văn bản
- **Relationship** — mối liên hệ giữa các entity
- **Community** — các nhóm entity có liên kết chặt chẽ với nhau trong knowledge graph
- **Community report** — nội dung tổng hợp thông tin của từng community
- **Embedding** — vector biểu diễn một số nội dung để phục vụ truy xuất theo độ tương đồng

### Chuẩn bị môi trường

| Thành phần | Cấu hình sử dụng |
| --- | --- |
| Python | 3.12.4 |
| Microsoft GraphRAG | 3.1.1 |
| Mô hình ngôn ngữ | DeepSeek-V4-Flash (qua OpenRouter) |
| Mô hình embedding | BGE-M3 (qua API tự host bằng FastAPI) |

```bash
python -m pip install -r requirements.txt
graphrag --version          # kết quả cần hiển thị 3.1.1

python -m uvicorn scripts.bge_m3_api:app --host 0.0.0.0 --port 8000
```

Workspace của GraphRAG gồm `settings.yaml`, `.env`, input, prompt và output. Tạo từ hai file mẫu:

```bash
cp .env.example .env
cp settings.yaml.example settings.yaml
```

### Chuẩn bị dữ liệu

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

### Cấu hình GraphRAG — những phần quan trọng

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

### Lập chỉ mục — văn bản thành đồ thị tri thức

#### Bước 1: Trích xuất thực thể và mối quan hệ

Mỗi văn bản được chia thành chunk — đơn vị nội dung đưa vào LLM để trích xuất. Prompt mặc định được điều chỉnh để đầu ra dùng tiếng Việt và giữ nguyên tên chính thức của văn bản pháp luật, cơ quan, tổ chức.

Với mỗi thực thể phát hiện được, LLM trả về ba thông tin: tên thực thể, loại thực thể, và mô tả dựa trên nội dung đoạn văn. Ví dụ một đoạn về Điều 24 của Bộ luật Lao động đề cập "người lao động", "người sử dụng lao động", "thử việc", "hợp đồng lao động" — LLM nhận diện các đối tượng này thành thực thể trong đồ thị.

Tiếp theo LLM xem xét mối liên hệ: nếu một điều luật dẫn chiếu đến một điều luật khác, hai điều luật trở thành hai thực thể với một relationship mô tả việc dẫn chiếu giữa chúng.

Sau khi các chunk được xử lý, GraphRAG **gộp kết quả**: cùng một thực thể xuất hiện ở nhiều chunk với cùng tên và loại → gộp thành một thực thể duy nhất. Vì một thực thể có thể được mô tả khác nhau ở nhiều chunk, GraphRAG dùng LLM tổng hợp thành một mô tả chung.

> ⚠️ **Cảnh báo quan trọng:** thực thể và mối quan hệ trong graph là kết quả do LLM tạo ra, **không phải dữ liệu đã được xác minh**. Mô hình có thể sinh thực thể quá chung chung, tách cùng một đối tượng thành nhiều thực thể, gộp nhầm các đối tượng khác nhau, hoặc tạo quan hệ chỉ vì hai thực thể cùng xuất hiện trong một đoạn. Hãy kiểm chứng và chuẩn hóa đồ thị trước khi đưa vào sử dụng.

#### Bước 2: Tạo Community bằng thuật toán Leiden

Microsoft GraphRAG dùng thuật toán **Hierarchical Leiden** để phát hiện community trực tiếp từ cấu trúc graph: tìm cách phân node thành các nhóm sao cho node trong cùng nhóm liên kết chặt hơn so với node ở nhóm khác. Quá trình tạo ra hệ thống community **theo nhiều cấp** — community lớn chứa nhiều community nhỏ.

Vì Leiden dùng cấu trúc graph thay vì nhãn chủ đề có sẵn, community **không nhất thiết tương ứng** với một document hay một chương: thực thể nằm ở nhiều văn bản khác nhau vẫn có thể thuộc cùng một community nếu chúng được kết nối với nhau trong graph.

#### Bước 3: Community report

Với mỗi community, GraphRAG tập hợp thực thể, mối quan hệ và nội dung liên quan rồi yêu cầu LLM viết bản tổng hợp — **community report**. Phân biệt: community cho biết nhóm thông tin nào đang liên kết với nhau; community report diễn giải và tổng hợp nhóm đó thành văn bản. Community report đặc biệt quan trọng cho Global Search.

#### Chạy lập chỉ mục

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

#### Kết quả lập chỉ mục

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

### Truy vấn: Local Search và Global Search

#### Local Search — tìm quanh thực thể

Bắt đầu bằng việc tìm entity liên quan đến câu hỏi, rồi khai thác vùng lân cận trong graph: relationship, entity liên quan, chunk nguồn. Context cùng câu hỏi đưa vào LLM để sinh câu trả lời.

```bash
graphrag query \
  "Có được ghi thỏa thuận thử việc trong hợp đồng lao động không?" \
  --root . --method local
```

Phù hợp với câu hỏi tập trung vào **một đối tượng, khái niệm, quy định hoặc mối quan hệ cụ thể**.

#### Global Search — tổng hợp toàn corpus

Không bắt đầu từ entity cụ thể. Global Search dùng các community report để tổng hợp trên phạm vi rộng, xử lý nhiều report theo cơ chế **map–reduce**: bước map đưa từng nhóm report cùng câu hỏi vào LLM để rút ra ý liên quan và đánh giá mức quan trọng; các ý được gom thành context mới; bước reduce đưa context vào LLM lần nữa để tổng hợp câu trả lời cuối.

```bash
graphrag query \
  "Các nhóm nghĩa vụ chính của doanh nghiệp trong quan hệ lao động là gì?" \
  --root . --method global \
  --community-level 0 \
  --response-type "List of 3-5 points with source names"
```

`--community-level` xác định cấp community được dùng, `--response-type` quy định dạng câu trả lời. Phù hợp với câu hỏi cần **tổng hợp thông tin từ nhiều phần** của corpus.

### Ba ví dụ khi GraphRAG có lợi thế

**Case 1 — Chữ ký điện tử và hợp đồng gửi qua mạng.** Câu hỏi: *"Ảnh chữ ký của giám đốc trên bảng lương và hợp đồng gửi qua mạng có giá trị như chữ ký tay không?"* Cần hai nhóm thông tin: giá trị pháp lý của hợp đồng dạng thông điệp dữ liệu **và** điều kiện để chữ ký điện tử hợp lệ. Dense retrieval lấy được nhóm đầu nhưng thiếu điều kiện xác thực chữ ký. Global Search tổng hợp từ nhiều community — câu trả lời không chỉ xác nhận hợp đồng điện tử có giá trị pháp lý mà còn chỉ ra giá trị chữ ký phụ thuộc vào điều kiện xác thực.

**Case 2 — Thử việc, BHXH và công đoàn.** Câu hỏi: *"Người thử việc theo thỏa thuận riêng, chưa ký hợp đồng chính thức, có phải đóng BHXH và có quyền vào công đoàn không?"* Ba nhóm thông tin: thỏa thuận thử việc, điều kiện tham gia BHXH bắt buộc, quyền gia nhập công đoàn. Dense tìm được thử việc và công đoàn nhưng thiếu quy định xác định đối tượng BHXH bắt buộc — mô hình có thể suy rộng từ nghĩa vụ BHXH nói chung và đưa kết luận sai. Global Search đặt cả ba quy định vào cùng ngữ cảnh: BHXH phụ thuộc loại và thời hạn hợp đồng, quyền công đoàn xét theo căn cứ khác.

**Case 3 — Hợp đồng mang tên "cộng tác viên".** Câu hỏi: *"Gọi giấy tờ là hợp đồng cộng tác viên nhưng vẫn trả lương và quản lý hằng ngày có làm mất nghĩa vụ đóng BHXH không?"* Cần hai bước suy luận liên tiếp: xác định bản chất quan hệ từ dấu hiệu trả lương và sự quản lý → đối chiếu với điều kiện tham gia BHXH. Global Search còn chỉ ra corpus không đề cập trực tiếp đến tên gọi này — không thể chỉ dựa vào tên giấy tờ để kết luận.

### Đánh giá khả năng truy xuất

So sánh hai phương pháp trên 26 câu hỏi tình huống: **Dense** (truy xuất trực tiếp bằng vector) và **Graph + RRF** (bổ sung nhánh truy xuất từ community, hợp nhất bằng Reciprocal Rank Fusion với trọng số Dense 1,0 và community 0,5).

| Phương pháp | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
| --- | --- | --- | --- | --- | --- |
| Dense | **0,3205** | 0,7532 | 0,9135 | **0,8333** | **0,7804** |
| Graph + RRF | 0,2949 | **0,8205** | 0,9135 | 0,7821 | 0,7650 |

Graph + RRF đạt Recall@5 cao hơn (0,8205 so với 0,7532) — bổ sung văn bản từ community giúp tìm được nhiều văn bản liên quan hơn trong 5 kết quả đầu. Tuy nhiên Dense đạt Recall@1, MRR và nDCG cao hơn: **Graph + RRF cải thiện độ bao phủ ở top-5 nhưng chưa cải thiện chất lượng xếp hạng tổng thể**.

### Tổng kết

Pipeline này chuyển 63 văn bản pháp luật tiếng Việt thành đồ thị tri thức với 508 thực thể, 1.043 mối quan hệ, 37 community và 37 community report — sẵn sàng cho Local Search và Global Search. Ba lưu ý khi áp dụng: đừng vội tin đồ thị ngay sau lập chỉ mục — mở vài thực thể, vài quan hệ ra đối chiếu với văn bản gốc; và nếu corpus của bạn lớn hơn nhiều, hãy thử nghiệm lại trên chính dữ liệu đó, vì lợi ích của GraphRAG thường chỉ rõ ràng khi corpus đủ lớn và đủ phức tạp.

### Bài liên quan

- Trước đó: Hybrid Search với BM25, Dense Retrieval và RRF
- Tiếp theo: Multi-hop RAG trên văn bản pháp luật tiếng Việt

### Nguồn

- Tài liệu chính thức: [GraphRAG Getting Started](https://microsoft.github.io/graphrag/get_started/), [CLI Reference](https://microsoft.github.io/graphrag/cli/), [Indexing Methods](https://microsoft.github.io/graphrag/index/methods/), [Global Search](https://microsoft.github.io/graphrag/query/global_search/)
- Mã nguồn: [microsoft/graphrag](https://github.com/microsoft/graphrag), [RAG_Advanced_GraphRAG (repo thực hành)](https://github.com/Hoanghung0603/RAG_Advanced_GraphRAG.git)
- Nội dung biên tập lại từ bài thực hành GraphRAG của AI Guru x TiniX theo phong cách LearnWithHuy; kết quả lập chỉ mục và benchmark là của một lần chạy cụ thể.

---

## 03. Multi-hop RAG: suy luận bắc cầu qua nhiều văn bản với LangGraph cho tài liệu tiếng Việt

Tìm kiếm đơn bước (Single-hop RAG) gặp hạn chế lớn khi xử lý truy vấn pháp lý đòi hỏi suy luận bắc cầu qua nhiều văn bản: *Thực thể X → thực thể trung gian Y → văn bản quy định Z*. Do hiện tượng đứt gãy liên kết ngữ nghĩa và khuyết ngữ cảnh đại từ chỉ định, mô hình khó thu hồi đủ văn bản đích — làm giảm tỷ lệ hồi tưởng chuỗi và tăng rủi ro sinh ảo giác pháp lý.

**Khi nào nên dùng Multi-hop RAG:**

- Ngữ liệu có cấu trúc phân mảnh và liên kết bắc cầu (pháp luật, y khoa, hồ sơ kỹ thuật)
- Câu hỏi chứa đại từ quy chiếu cần khử nhập nhằng và bóc tách thực thể cầu nối
- Hệ thống yêu cầu kiểm soát xung đột (Contradiction Check) và trích dẫn căn cứ minh bạch
- Cần kiểm soát chặt từng bước nhảy suy luận để phục vụ truy vết và giải trình

**Không nên dùng khi:** câu hỏi đơn giản, thông tin nằm trọn vẹn trong một điều khoản đơn lẻ; hoặc yêu cầu độ trễ dưới 1 giây trên kho tài liệu độc lập, phẳng.

### Bốn khái niệm nền tảng

| Khái niệm | Là gì |
| --- | --- |
| **Semantic gap** (đứt gãy liên kết ngữ nghĩa) | Single-hop RAG chỉ tìm một lượt: khi câu hỏi bắc cầu, công cụ tìm kiếm nhận diện được thực thể ban đầu nhưng chưa xác định được thực thể trung gian Y để thu hồi văn bản điều chỉnh Z |
| **Bridge entity extraction** | Kỹ thuật bóc tách danh từ hoặc cụm định nghĩa của thực thể trung gian từ văn bản thu hồi ở Hop 0 — dùng làm cầu nối logic cho truy vấn của Hop 1 |
| **Coreference resolution** | Phân tích mệnh đề phụ thuộc trong chuỗi câu hỏi con, nhận diện đại từ quy chiếu ("nhóm đó", "loại này") rồi thay bằng tên thực thể chuẩn xác đã trích xuất ở Hop 0 |
| **Contradiction detection** | Phân tích văn bản thu hồi để phát hiện xung đột giữa các quy định (một văn bản nghiêm cấm, một văn bản cho phép theo điều kiện) → kích hoạt cảnh báo thay vì tự động suy diễn |

### Kiến trúc luồng xử lý trên LangGraph

Hệ thống vận hành trên một đồ thị trạng thái `StateGraph` gồm 3 node chính và một router điều kiện:

1. **decompose_node** — tách câu hỏi phức hợp thành chuỗi câu hỏi con có quan hệ bắc cầu
2. **retrieve_node** — khối truy xuất đa chặng: Hybrid Retriever (BM25s + Dense BGE-M3, hợp nhất RRF k=60), module con Bridge & Coreference (bóc tách thực thể Hop 0, khử đại từ Hop 1), module con Evidence Assess (thẩm định độ phủ số liệu và phát hiện mâu thuẫn)
3. **router_edge** — kiểm tra điều kiện dừng: đủ bằng chứng → synthesize; chưa đủ và chưa hết số Hop → quay lại retrieve; mâu thuẫn hoặc thiếu chứng cứ → thoái lui an toàn kèm cảnh báo
4. **synthesize_node** — tổng hợp câu trả lời cuối cùng kèm trích dẫn căn cứ pháp lý

Trạng thái `MultiHopState` mang theo toàn bộ ngữ cảnh xuyên suốt:

| Trường dữ liệu | Kiểu | Vai trò |
| --- | --- | --- |
| `question` | str | Câu hỏi gốc từ người dùng |
| `sub_questions` | List[SubQuestion] | Danh sách câu hỏi con kèm bằng chứng thu hồi |
| `current_hop` | int | Chỉ số bước nhảy suy luận hiện tại (0, 1, 2...) |
| `max_hops` | int | Giới hạn số bước tối đa để chống lặp vô hạn |
| `retrieval_logs` | List[Dict] | Nhật ký truy vấn, danh sách đoạn văn bản và điểm số RRF |
| `stop_reason` | str | `all_answered`, `contradiction` hoặc `insufficient` |
| `final_answer` | str | Câu trả lời cuối cùng kèm trích dẫn văn bản hoặc thông báo thoái lui |

### Thiết lập môi trường

```bash
git clone https://github.com/tnt305/multi-hop-rag.git
cd multi-hop-rag

conda env create -f environment.yml
conda activate multi_hop_rag

# Hoặc cài qua pip
pip install -r requirements.txt
# (pyvi, scikit-learn, datasets, faiss-cpu, pandas, bm25s, sentence-transformers, langgraph)
```

Cấu trúc mã nguồn:

```
multi_hop_rag/
├── pipeline.py                  # Entrypoint thực thi End-to-End
├── run.py                       # Runner điều phối pipeline, benchmark, trace
├── indexing/
│   ├── parent_child_chunker.py  # Phân đoạn văn bản phân cấp cha-con
│   ├── sparse_indexer.py        # Chỉ mục từ khóa BM25Okapi / BM25s
│   └── faiss_indexer.py         # Chỉ mục vector Dense BGE-M3
├── retrieval/
│   ├── base.py                  # Lớp cơ sở trừu tượng Retriever
│   └── factory.py               # Hợp nhất thứ hạng lai (RRF k=60)
├── decomposition/
│   └── sub_question_decomposer.py  # Phân rã câu hỏi đa bước (Heuristic / LLM)
├── workflow/
│   ├── rag_workflow.py          # Khởi tạo và biên dịch StateGraph (3 node chính)
│   ├── bridge.py                # Trích xuất thực thể cầu nối và khử đại từ
│   └── evidence.py              # Thẩm định độ phủ và phát hiện mâu thuẫn
├── detector/
│   └── nlp_classifier.py        # Phân loại câu hỏi đơn bước vs đa bước
├── evaluator/
│   └── eval_pipeline.py         # Kịch bản kiểm thử và đo lường độ chính xác
└── data/small_corpus/           # Dữ liệu kiểm thử chức năng
```

### Các module cốt lõi

#### Module 1 — HybridRetriever

Tính điểm BM25 từ khóa thưa, tính cosine trên vector Dense BGE-M3, hợp nhất theo RRF k=60:

```python
class HybridRetriever:
    def __init__(self, corpus, embeddings, bge_model=None):
        self.corpus = corpus
        self.embeddings = embeddings
        self.bm25 = BM25Okapi([tokenize_vi(text) for text in corpus])
        self.bge_model = bge_model

    def retrieve(self, query: str, top_k: int = 10):
        bm25_scores = self.bm25.get_scores(tokenize_vi(query))
        bm25_rank = np.argsort(-bm25_scores)[:top_k]

        q_emb = self.bge_model.encode(query) if self.bge_model \
            else self._get_cached_emb(query)
        cos_scores = (self.embeddings @ q_emb) / (
            np.linalg.norm(self.embeddings, axis=1)
            * np.linalg.norm(q_emb) + 1e-9)
        dense_rank = np.argsort(-cos_scores)[:top_k]

        rrf_scores = {}
        for r, idx in enumerate(bm25_rank):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (60 + r + 1)
        for r, idx in enumerate(dense_rank):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (60 + r + 1)

        sorted_idx = sorted(rrf_scores, key=lambda i: -rrf_scores[i])[:top_k]
        return [{"chunk_id": int(i), "text": self.corpus[i],
                 "score": float(rrf_scores[i])} for i in sorted_idx]
```

#### Module 2 — Bridge & Anaphora

Quét mẫu định nghĩa "là <cụm thực thể>" trong văn bản thu hồi Hop 0, loại bỏ cụm từ thừa để giữ tên thực thể cốt lõi, rồi thay thế đại từ chỉ định trong câu hỏi Hop 1:

```python
def extract_bridge_entity(evidence_list):
    for doc in evidence_list:
        text = doc.get("text", "")
        match = re.search(r'là\s+(.+?)(?:[,;.]\s*|$)', text)
        if match:
            phrase = match.group(1).strip()
            # Loại bỏ cụm thừa sau các từ nối
            for tok in ["được", "có thể", "nhằm", "để"]:
                if tok in phrase and not any(m in phrase
                        for m in ["thuộc Bộ", "thuộc UBND"]):
                    phrase = phrase[:phrase.index(tok)].strip()
                    break
            if 5 < len(phrase) < 120:
                return phrase
    return ""

def resolve_anaphora(sub_query: str, bridge_entity: str) -> str:
    for p in ["nhóm đó", "loại đó", "đối tượng đó", "nhóm này", "loại này"]:
        if p in sub_query and bridge_entity:
            return sub_query.replace(p, bridge_entity)
    return sub_query
```

#### Module 3 — Evidence Assessment & Contradiction Detection

Thẩm định ngưỡng điểm tin cậy RRF, kiểm tra sự hiện diện của số liệu khi câu hỏi cần, và phát hiện mâu thuẫn **theo cặp** (pairwise): hai đoạn cùng chia sẻ chủ đề hẹp (2 đến 25 token chung — tránh hai đoạn quá giống hoặc không liên quan) nhưng một bên có từ khóa cấm ("cấm", "nghiêm cấm", "không cho phép") và bên kia có từ khóa cho phép ("được phép", "có quyền") trong cửa sổ ngữ cảnh ±5 từ quanh token chung.

```python
def assess_evidence(query: str, results, min_score: float = 0.025) -> bool:
    if not results or results[0].get("score", 0.0) < min_score:
        return False
    if any(k in query.lower() for k in ["bao nhiêu", "mức", "bao lâu", "số tiền"]):
        return any(re.search(r'\d', doc["text"]) for doc in results[:3])
    return True

def detect_contradiction(texts) -> bool:
    # token hóa từng đoạn, tìm cặp văn bản cùng chủ đề hẹp
    # mà từ khóa cấm đối đầu từ khóa cho phép trong cửa sổ ±5 từ
    negators = {"cấm", "không được", "nghiêm cấm", "không cho phép"}
    permissions = {"được phép", "cho phép", "có quyền", "được quyền"}
    # ... vòng lặp pairwise trên content_sets[i] & content_sets[j]
    ...
```

#### Module 4 — Lắp ráp StateGraph

```python
def build_multihop_graph(retriever: HybridRetriever):
    workflow = StateGraph(MultiHopState)
    workflow.add_node("decompose", decompose_node)
    workflow.add_node("retrieve", lambda s: retrieve_node(s, retriever))
    workflow.add_node("synthesize", synthesize_node)

    workflow.set_entry_point("decompose")
    workflow.add_edge("decompose", "retrieve")
    workflow.add_conditional_edges("retrieve", router_edge, {
        "retrieve": "retrieve",
        "synthesize": "synthesize",
    })
    workflow.add_edge("synthesize", END)
    return workflow.compile()
```

Trong `retrieve_node`, sau khi truy xuất Hop 0, module bridge được gọi để gán `bridged_query` cho câu hỏi con tiếp theo — chính là cơ chế khử đại từ tạo ra truy vấn tường minh cho Hop 1.

### Kết quả thực nghiệm

Benchmark chức năng dùng Heuristic Decomposer và Sparse BM25s trên 20 ca tổng hợp cố định — mỗi ca có 4 đoạn văn bản: bridge, answer và 2 distractor.

| Chỉ số đo lường | Plain RAG | Multi-hop RAG | Ghi chú |
| --- | --- | --- | --- |
| Plain top-1 đúng đáp án | 0/20 | — | `plain_top1_ok = false` ở cả 20 ca |
| Benchmark end-to-end | — | **19/20 (95%)** | Cấu hình Heuristic Decomposer |
| Contradiction: true positive | — | TP = 1 | Phát hiện đúng ca contradiction |
| Contradiction: false positive | — | FP = 2 | Báo nhầm 2 ca single-hop bình thường |
| Precision / Recall mâu thuẫn | — | 33,3% / 100% | TP=1, FP=2, FN=0 theo nhãn suite |
| Fallback thiếu dữ liệu | — | 1/1 | Chỉ có 1 ca, chưa đại diện thực tế |

Ghi chú trung thực của nhóm phát triển: không dùng các tỷ lệ Hit@1 Hop 0, Hit@3 Hop 1 hay độ chính xác trích dẫn khi chưa có script tính trực tiếp; detector phát hiện đúng ca contradiction nhưng **báo nhầm 2 ca single-hop là mâu thuẫn** — báo mâu thuẫn ở ca bình thường phải tính là FAIL. Độ tin cậy thống kê phụ thuộc vào việc gắn nhãn kỳ vọng cho từng ca.

**Phân tích scale-up:** trên suite nhỏ có kiểm soát, cơ chế bắc cầu giúp Multi-hop thắng Plain RAG. Khi bổ sung nhiễu từ 100 đoạn trở lên, kết quả giảm rõ: với Sparse, số ca đúng giảm từ 6 (scale 0) xuống 4 (scale 100), 3 (scale 500) và 2 (scale 2.000–20.000). Triển khai trên kho lớn cần bổ sung bộ lọc metadata theo lĩnh vực và Cross-Encoder Reranker sau tầng Hybrid RRF — và đánh giá bằng benchmark riêng trước khi công bố hiệu quả định lượng.

### Ba kịch bản ứng dụng thực tế

1. **Tra cứu quy định hành chính:** Hop 0 xác định văn bản ủy quyền là văn bản hành chính theo Nghị định 30/2020/NĐ-CP → Hop 1 thu hồi các điều khoản về thể thức và thẩm quyền ký ban hành.
2. **Thẩm định điều kiện cấp phép:** tra cứu định nghĩa hoạt động khảo nghiệm (Luật Thú y) trước khi xác định quy chuẩn kỹ thuật và thông tư điều chỉnh (Thông tư 13/2016/TT-BNNPTNT) — hệ thống xâu chuỗi hai nguồn để tạo căn cứ hoàn chỉnh.
3. **Phát hiện xung đột và hiệu lực văn bản:** hai văn bản thuộc thời kỳ hoặc cơ quan khác nhau trái ngược về cùng một hành vi → hệ thống phát hiện mệnh đề đối lập và cảnh báo, hỗ trợ chuyên viên pháp chế nắm điểm mâu thuẫn trước khi ban hành văn bản áp dụng.

### Lỗi thường gặp và cảnh báo biên

**Lỗi ghép cặp sai (SYNTHETIC_DATA_MISMATCH):** hai văn bản thuộc miền tri thức khác nhau (Du lịch vs Đấu giá) bị ghép cặp vì trùng ngữ pháp bề mặt "là việc tổ chức...". Router Edge phát hiện không có liên kết thực thể hợp lệ, ngắt luồng an toàn và kích hoạt fallback. Biện pháp khắc phục: bổ sung bộ lọc miền tri thức (Domain Filter) hoặc kiểm tra độ tương đồng vector giữa thực thể trích xuất và tiêu đề văn bản đích.

**Lỗi phát hiện mâu thuẫn (SAFETY_ROUTER_TRIGGERED):** một văn bản nghiêm cấm khai thác tài nguyên trong khu bảo tồn đối đầu với một văn bản cho phép khai thác theo giấy phép — hàm `detect_contradiction` phát hiện xung đột theo cặp, ngắt luồng và trả cảnh báo minh bạch thay vì tự suy diễn.

**Cảnh báo vận hành:**

- **Bẫy lặp vô hạn:** câu hỏi có cấu trúc vòng tròn khiến hệ thống liên tục tạo câu hỏi con không đạt điều kiện dừng. Luôn duy trì chốt chặn `max_hops = 2` và `recursion_limit` trong đồ thị LangGraph.
- **Câu hỏi nhiều mệnh đề:** hàm Regex trích xuất cầu nối có thể bắt nhầm cụm từ phụ — cần ưu tiên bóc tách theo thứ tự xuất hiện của cấu trúc vị ngữ chính.

Chẩn đoán nhanh:

```bash
python pipeline.py                       # kiểm thử toàn bộ luồng độc lập
python run.py --benchmark --top_k 10     # benchmark đối đầu 20 ca
python run.py --trace_case mh20_01_det_may  # xuất vết thực thi chi tiết một ca
```

### Bài liên quan

- Trước đó: GraphRAG: từ văn bản tới Knowledge Graph
- Cơ chế Hybrid Retriever chi tiết: Hybrid Search với BM25, Dense Retrieval và RRF

### Nguồn

- Mã nguồn: [multi-hop-rag (repo thực hành)](https://github.com/tnt305/multi-hop-rag)
- Nghiên cứu nền: HotpotQA (EMNLP 2018), Dense Passage Retrieval (EMNLP 2020), BGE M3-Embedding (arXiv:2402.03216), Query2Doc (EMNLP 2023), AutoGen (arXiv:2308.08155)
- Nội dung biên tập lại từ bài thực hành Multi-hop RAG của AI Guru x TiniX theo phong cách LearnWithHuy; kết quả benchmark trên bộ dữ liệu tổng hợp cố định, chưa đại diện cho dữ liệu pháp luật thực tế.

---

## 04. Multimodal RAG: xây dựng pipeline đa phương thức và benchmark cho tài liệu PDF tiếng Việt

Hệ thống hỏi đáp trên tài liệu PDF học thuật tiếng Việt — chứa bảng số liệu nhiều cột, chú thích và biểu đồ — thường gặp ba trở ngại với phương pháp bóc tách truyền thống: **lệch hàng cột** khi làm phẳng bảng nén, **xáo trộn thứ tự đọc** khi dàn trang phức tạp (trang hai cột, hộp chú thích xen giữa), và **mất mát thông tin đồ thị** do OCR thông thường không bóc tách được nhãn trục.

Bài này trình bày giải pháp RAG đa phương thức (Multimodal RAG) kết hợp trích xuất trực quan và mô hình ngôn ngữ thị giác, kèm bộ dữ liệu kiểm thử có căn cứ số trang đối soát.

**Khi nào nên dùng:** tài liệu chứa nhiều bảng biểu phức tạp, đồ thị và hình ảnh chú thích chuyên sâu; hệ thống đòi hỏi trích dẫn chính xác số trang; cần benchmark phân tách rõ lỗi truy xuất và lỗi đọc hiểu hình ảnh. **Không nên dùng khi:** ngữ liệu chủ yếu là văn bản thuần túy, ít bảng biểu; hoặc yêu cầu thời gian thực với chi phí tính toán tối thiểu — pipeline thị giác tốn tài nguyên hơn văn bản thuần.

### Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Multimodal RAG** | RAG mở rộng: không chỉ xử lý văn bản mà còn lập chỉ mục và truy xuất trực tiếp khối bảng biểu, hình ảnh, đồ thị |
| **Side-aware Embedding** | Cơ chế vector hóa bất đối xứng: gắn nhãn `side="document"` khi lập chỉ mục và `side="query"` khi tìm kiếm để không gian biểu diễn hội tụ |
| **Lexical vs Dense** | Truy xuất từ khóa (BM25) dựa tần suất khớp từ vựng; truy xuất vector so khớp cosine trong không gian ngữ nghĩa |
| **Text QA vs Vision QA** | Text QA đưa văn bản/bảng Markdown vào mô hình ngôn ngữ; Vision QA đưa ảnh biểu đồ độ phân giải cao kết hợp chú thích vào mô hình thị giác |
| **Page Citation** | Quy tắc phản hồi bắt buộc kèm trích dẫn `[PDF trang X]` để đối chiếu tài liệu gốc |
| **Recall@k / MRR** | Tỷ lệ câu hỏi tìm thấy trang đích trong top-k; thứ hạng nghịch đảo trung bình của trang đúng đầu tiên |

### Kiến trúc phân nhánh đa phương thức

Kiến trúc Dual-Branch tách biệt luồng xử lý giữa văn bản/bảng biểu và hình ảnh/đồ thị thống kê, gồm 4 khối chính:

**Khối 1 — Multi-Parser Engine (bóc tách đa thành phần):**

- *Văn bản và bố cục:* PyMuPDF4LLM đọc toàn bộ PDF giữ đúng thứ tự đọc
- *Bảng nén số liệu:* pdfplumber bóc tách lưới ô bảng; với bảng nhiều cột phức tạp, thuật toán heuristic quét dòng dữ liệu từ văn bản nguyên bản rồi ghép với tiêu đề cột để tái cấu trúc thành bảng Markdown 2D chuẩn
- *Hình ảnh:* tự động cắt và lưu nguyên bản ảnh biểu đồ dạng PNG độ phân giải cao (220 DPI) kèm chú thích phụ cận — phục vụ trực tiếp cho mô hình thị giác phân tích trục số liệu thay vì chuyển qua OCR gây mất mát cấu trúc
- *Fallback OCR:* pytesseract (ngôn ngữ `vie+eng`) tự kích hoạt khi lượng văn bản trích xuất trên trang dưới ngưỡng 80 ký tự

**Khối 2 — Embedding Gateway:** kết nối đến Triton Inference Server chạy mô hình nhúng đa phương thức (512 chiều, FP16). Áp dụng Side-Aware Asymmetric Prefixing: lập chỉ mục offline bắt buộc gán `side="document"`; truy vấn gán `side="query"`. Nhánh văn bản nhúng các bản ghi trang/đoạn đã tích hợp bảng Markdown; nhánh hình ảnh nhúng trực tiếp file PNG biểu đồ qua endpoint thị giác.

**Khối 3 — Multi-Vector Retrieval:** tính cosine giữa vector truy vấn và kho vector bản ghi trang/đoạn; truy xuất hình ảnh bằng so khớp vector đặc trưng ảnh (Image-to-Image) hoặc tìm kiếm kết hợp ngữ cảnh phụ cận để ánh xạ về mã trang PDF gốc (Gold Page Anchor).

**Khối 4 — Dual-Engine QA & Citation:** Text QA gửi ngữ cảnh Markdown cùng câu hỏi cho mô hình ngôn ngữ; Vision QA gửi ảnh PNG dạng base64 kết hợp chú thích phụ cận cho mô hình thị giác đọc trực tiếp xu hướng đường cột và số liệu. **Mọi câu trả lời bắt buộc kèm trích dẫn `[PDF trang X]`.**

### Thực nghiệm: bộ kiểm thử 12 câu hỏi

Nguồn ngữ liệu: báo cáo học thuật của Ngân hàng Thế giới *"Nâng cao Hiệu quả Giáo dục Đại học tại Việt Nam"* (110 trang). Sau khi xử lý qua Multi-Parser Engine: **168 chunks** (62 khối bảng Markdown nén + 106 đoạn văn bản), **25 trang chứa bảng phức tạp** (nhiều cột số, header gộp đa tầng), **17 ảnh biểu đồ thống kê** bóc tách độc lập.

Bộ kiểm thử 12 câu hỏi có gán nhãn trang chuẩn (Ground-Truth Page Anchor):

| Mã | Loại | Nội dung | Trang đúng | Mục tiêu kiểm nghiệm |
| --- | --- | --- | --- | --- |
| T1–T3 | Văn bản | Số liệu định lượng trong văn bản xuôi | 18, 55, 65 | Trích xuất thông tin trong đoạn văn phức tạp |
| B1–B6 | Bảng | Số trường top 1.000 của 6 quốc gia | 46 (Bảng 3) | Kiểm định hiện tượng trượt cột khi đọc bảng Markdown phẳng |
| F1–F3 | Biểu đồ | So sánh khu vực, tỷ lệ nhập học, việc làm và thu nhập | 16, 39, 48 | Đọc biểu đồ đường và biểu đồ cột |

#### Hiệu năng truy xuất

| Phương pháp | Recall@1 | Recall@5 | MRR | Đánh giá |
| --- | --- | --- | --- | --- |
| Lexical (BM25) | 0.833 | 0.917 | 0.854 | Phụ thuộc từ khóa khớp chính xác |
| **jina-v5 (mức trang)** | **1.000** | **1.000** | **1.000** | Độ chính xác tuyệt đối ở top-1 |
| jina-v5 (mức đoạn) | 1.000 | 1.000 | 1.000 | Duy trì cao khi phân rã nhỏ |
| BGE-M3 (mức trang) | 0.667 | 1.000 | 0.833 | Thấp hơn ở top-1 nếu thiếu tiền tố chỉ dẫn |
| BGE-M3 (mức đoạn) | 0.833 | 1.000 | 0.892 | Ổn định hơn khi chỉ mục ở mức đoạn |

Ghi chú về truy xuất hình ảnh: so khớp ảnh→ảnh đạt chuẩn trên mẫu đồ thị kiểm nghiệm, nhưng truy xuất chéo **chữ→ảnh** trực tiếp còn hạn chế. Trong kịch bản RAG khi người dùng nhập câu hỏi bằng văn bản, hệ thống dùng truy vấn văn bản tìm trang qua Text-to-Page trước, rồi nạp ảnh crop cho Vision LLM. Lưu ý cần chỉ định chính xác cờ `side="query"` / `side="document"` để tránh suy giảm độ chính xác vector.

#### Hiệu năng hỏi đáp và trích dẫn trang

| Phương pháp hỏi đáp | Độ chính xác | Tỷ lệ trích dẫn | Tỷ lệ từ chối | Mẫu |
| --- | --- | --- | --- | --- |
| Text-only Lexical (văn bản + bảng) | 0.556 | 0.889 | 0.111 | 9 câu |
| **Text-only jina-v5 (văn bản + bảng)** | **0.667** | **1.000** | **0.000** | 9 câu |
| Multimodal Vision QA (ảnh + ngữ cảnh) | 0.667 | 0.333 | 0.000 | 3 câu biểu đồ |

#### Phân tích theo nhóm câu hỏi

- **Văn bản (T1–T3):** đạt 3/3 (100%) với jina-v5. Tại câu T3, truy xuất vector lấy chính xác trang 65 (học phí chiếm 55%), trong khi BM25 trượt sang trang 25 dẫn đến mô hình từ chối trả lời (abstain).
- **Bảng biểu (B1–B6):** đạt 3/6 PASS. Trang 46 được truy xuất hoàn toàn chính xác ở top-1 (Recall@1 = 100%); cả 3 ca sai đều do **trượt cột phía mô hình ngôn ngữ** khi xử lý bảng Markdown phẳng — B2 đọc 32 thay vì 35, B4 đọc 45 thay vì 60, B5 đọc 51 thay vì 44.
- **Hình ảnh (F1–F3):** câu F2 bắt buộc dùng Vision LLM vì mốc tăng trưởng "9% lên 28%" không tồn tại trong văn bản xuôi.

> **Tóm tắt số liệu cốt lõi:** khâu truy xuất đạt Recall@1 = 12/12 trang chuẩn (100%). Cả ba ca thất bại ở nhóm bảng biểu đều do trượt cột của LLM — đối với biểu đồ thống kê thuần túy, kích hoạt nhánh Vision QA là điều kiện tiên quyết để trích xuất đúng dữ liệu.

#### Kiểm toán chất lượng bóc tách (Parse audit)

| Tiêu chí | Kết quả | Ý nghĩa |
| --- | --- | --- |
| Nhận diện bảng | P = 1.00, R = 0.75, F1 = 0.857 | Nhận diện chính xác trang chứa bảng, bỏ sót một số bảng phụ |
| Lệch cấu trúc liên công cụ | 6/8 trang lệch dòng | pdfplumber và pymupdf4llm xử lý ô gộp khác nhau |
| Độ bao phủ hình ảnh | 0.929 (13/14) | Bỏ qua 1 ảnh bìa không chứa chú thích |
| Thứ tự đọc văn bản | Kendall-tau ≈ 0.390 | Bị ảnh hưởng bởi nhãn trục xoay 90° trong biểu đồ |
| Chất lượng OCR | CER ≈ 3.2% | Lớp văn bản kỹ thuật số của PDF đạt chất lượng tốt |

### Phân tích lỗi và giới hạn vận hành

#### Lỗi 1 — Lệch cột khi LLM đọc bảng Markdown nén

Bảng xếp hạng nhiều cột số liền kề (Webometrics, QS, THE, ARWU) khi chuyển sang Markdown bị làm phẳng thành chuỗi — do các ký tự phân cách và chữ số nằm sát nhau, mô hình dễ trích xuất nhầm giá trị của **cột lân cận cùng hàng**:

```json
{
  "execution_diagnostic": {
    "query": "Trong Bảng 3, Pháp có bao nhiêu trường trong top 1.000 của bảng xếp hạng QS?",
    "input_chunk_B": "| Pháp | 40 (Webometrics) | 35 (QS) | 32 (THE) |",
    "error_cause": "COLUMN_SLIP: bảng PDF nhiều cột số bị flatten Markdown; LLM lấy nhầm ô kề 32 (THE) thay vì 35 (QS)"
  }
}
```

Khâu truy xuất đã lấy đúng trang (Recall@1 = 100%) — sai số hoàn toàn nằm ở khâu đọc hiểu bảng phẳng. **Giải pháp:** yêu cầu mô hình liệt kê rõ tên cột và hệ quy chiếu trước khi trích xuất giá trị số, hoặc bổ sung bước xác thực cặp khóa-giá trị.

#### Các lỗi còn lại

- **Dao động giữa các lần thực thi LLM:** cùng một prompt có thể cho kết quả lệch ±1 câu do sampling — cố định `temperature = 0.0` và ép kiểu đầu ra có cấu trúc (Structured Output Schema) trong môi trường sản xuất.
- **Lệch cấu trúc giữa hai công cụ phân tích bảng:** 6/8 trang chứa bảng phức tạp có chênh lệch số dòng giữa pdfplumber và pymupdf4llm, chủ yếu tại ô gộp — duy trì cơ chế fallback đối chiếu thay vì chỉ dựa một công cụ.
- **Thứ tự đọc bị xáo trộn:** nhãn trục xoay 90° khiến đoạn văn bản bị cắt rời trong trích xuất tuyến tính — với trang chứa đồ thị, dùng trực tiếp ảnh cắt nguyên bản kết hợp Vision LLM tin cậy hơn.

**Lưu ý vận hành:** tài liệu quét chất lượng thấp cần deskew và tăng độ tương phản; bảng lớn trải nhiều trang nên chia nhỏ vùng bảng và thẩm định tên cột trước khi trích xuất; xử lý đa phương thức tốn tài nguyên hơn — phân loại câu hỏi trước để chỉ kích hoạt nhánh thị giác khi thực sự cần thiết.

### Triển khai: hai luồng sử dụng

**Luồng A — xem kết quả bằng artifact có sẵn** (không cần hạ tầng):

```bash
git clone https://github.com/tnt305/multimodal_rag.git
cd multimodal_rag
python3 -m json.tool outputs/benchmark/qa.json
python3 -m json.tool outputs/benchmark/retrieval.json
```

**Luồng B — tái tạo toàn bộ benchmark từ PDF gốc** cần hạ tầng bên ngoài: Triton gateway, hai model nhúng text/image đã load, cùng API cho QA/Vision — repo chưa kèm tài nguyên triển khai gateway, nên không phải quickstart chạy được từ fresh clone.

Xử lý các tình huống chạy lệch: thứ tự đọc xáo trộn → ưu tiên ảnh crop kết hợp Vision LLM; cấu trúc bảng vỡ → kích hoạt chế độ Heuristic Rebuild Grid; OCR thấp → tăng DPI và chỉ định gói ngôn ngữ `vie`; lệch cột → yêu cầu mô hình xuất danh sách tên cột trước khi trích xuất.

### Bài liên quan

- Trước đó: Multi-hop RAG với LangGraph
- Tiếp theo: Đánh giá chất lượng hệ thống RAG với Ragas

### Nguồn

- Mã nguồn: [multimodal_rag (repo thực hành)](https://github.com/tnt305/multimodal_rag.git)
- Nghiên cứu nền: BGE M3-Embedding (arXiv:2402.03216), jina-embeddings-v5-omni (Jina AI, 2025), Qwen3-VL (Alibaba Cloud, 2025)
- Nội dung biên tập lại từ bài thực hành Multimodal RAG của AI Guru x TiniX theo phong cách LearnWithHuy; số liệu benchmark quan sát trên bộ kiểm thử cụ thể.

---

## 05. Đánh giá chất lượng hệ thống RAG với Ragas: 4 độ đo, Golden Dataset và 5 lỗi thường gặp

Bạn đã xây được một hệ thống RAG cơ bản. Nhưng làm sao biết nó thực sự "thông minh"? Việc chỉ thử nghiệm 3–5 câu hỏi bằng mắt thường là không đủ khi đưa ứng dụng vào môi trường thực tế. Cần một phương pháp đánh giá tự động và toàn diện: xây dựng **Golden Dataset** và dùng thư viện **Ragas** để đo lường các độ đo.

Toàn bộ quy trình trong bài chạy local, miễn phí, không cần API key trả phí (yêu cầu: RAM tối thiểu 8GB, Python 3.9+, Ollama với mô hình Gemma2, thư viện `ragas`).

### Thuật ngữ cơ bản

| Thuật ngữ | Định nghĩa |
| --- | --- |
| **Ground Truth** | Đáp án đúng chuẩn do con người viết sẵn — thước đo chuẩn mực cho hệ thống |
| **Golden Dataset** | Tập dữ liệu "vàng" gồm các cặp (Câu hỏi, Ground Truth) dùng để kiểm thử |
| **LLM-as-a-Judge** | Dùng một LLM mạnh làm giám khảo chấm điểm câu trả lời do chatbot sinh ra, thay con người |
| **Ragas** | Thư viện mã nguồn mở chuyên đo lường chất lượng hệ thống RAG dựa trên LLM-as-a-Judge |
| **NLI** | Natural Language Inference — bài toán xác định một giả thuyết có được suy ra từ một tiền đề hay không; Ragas dùng NLI để kiểm tra tính logic của câu trả lời |

### Lý thuyết: hai thành phần cần đánh giá

Đánh giá RAG phải tách thành hai thành phần độc lập: **Hệ thống truy xuất (Retrieval)** và **Khả năng sinh văn bản (Generation)**. Nếu Retrieval lấy về rác, Generation chắc chắn sinh ra rác (Garbage in, Garbage out). Ngược lại, Retrieval lấy về thông tin vàng nhưng Generation bị ảo giác — hệ thống vẫn thất bại.

Luồng đánh giá: Câu hỏi → Truy xuất → Ngữ cảnh → Sinh trả lời → Câu trả lời. **Context Precision** và **Context Recall** đánh giá tầng Retrieval; **Faithfulness** và **Answer Relevancy** đánh giá tầng Generation.

#### A. Context Precision — độ chính xác của ngữ cảnh

Câu hỏi trả lời: *trong các đoạn văn lấy về, đoạn chứa đáp án có được xếp ở vị trí ưu tiên cao nhất không?* Ragas tính dựa trên Mean Average Precision:

$$\text{Context Precision@K} = \frac{\sum_{k=1}^{K} \left(\text{Precision@}k \times v(k)\right)}{\text{Tổng số chunks có liên quan}}$$

**Ví dụ:** tìm "Điều kiện cấp sổ đỏ lần đầu theo Luật Đất đai 2024", hệ thống trả về 3 kết quả — hai kết quả đầu không liên quan, kết quả liên quan nằm tuốt vị trí cuối. Độ đo MAP phạt rất nặng cấu hình này: Context Precision rơi xuống khoảng 1/3. Để đạt 1.0 tuyệt đối, đoạn liên quan bắt buộc phải ở vị trí số 1.

#### B. Context Recall — độ bao phủ của ngữ cảnh

Câu hỏi trả lời: *các đoạn văn lấy về có đủ tất cả các ý cần thiết để trả lời y hệt đáp án chuẩn không?* Độ này tập trung vào độ đầy đủ hơn là thứ tự xếp hạng:

$$\text{Context Recall} = \frac{\text{Số câu trong Ground Truth có mặt trong Context}}{\text{Tổng số câu của Ground Truth}}$$

Cơ chế của Ragas: LLM-giám-khảo đọc Ground Truth, chia thành từng ý (statements), rồi dò xem từng ý có xuất hiện trong context hay không. Ví dụ: đáp án chuẩn liệt kê 7 loại đất, nhưng chunk_size quá nhỏ khiến hệ thống chỉ lấy về đoạn nói về 4 loại đầu — Ragas đếm được 4/7 ý, Context Recall ≈ 0.57.

#### C. Faithfulness — độ trung thành

Câu hỏi trả lời: *mô hình AI có "bịa" ra thông tin ngoài những gì được cung cấp trong tài liệu không?* Quá trình gồm 2 bước suy luận NLI: **trích xuất ý** (phân tách câu trả lời thành danh sách mệnh đề ngắn) → **xác thực** (đối chiếu từng mệnh đề với context xem có được suy ra hay không).

$$\text{Faithfulness} = \frac{\text{Số mệnh đề được suy ra từ Context}}{\text{Tổng số mệnh đề trong câu trả lời}}$$

**Ví dụ:** ngữ cảnh ghi "Thời hạn giao đất nông nghiệp là 50 năm", nhưng LLM trả lời thêm "và sau khi hết hạn sẽ phải nộp phí gia hạn 10 triệu đồng". Mệnh đề thứ hai không hề có trong ngữ cảnh — dù quy định thực tế có như vậy hay không, hệ thống RAG vẫn coi đây là Hallucination nghiêm trọng. Faithfulness giảm xuống 0.5.

#### D. Answer Relevancy — độ liên quan của câu trả lời

Đo xem câu trả lời có trực tiếp giải quyết vấn đề hay trả lời lan man. Thú vị là Ragas **không so sánh trực tiếp** — nó làm ngược lại: dùng LLM sinh ra các *câu hỏi dự đoán* dựa trên câu trả lời, rồi đo khoảng cách Cosine giữa câu hỏi gốc và các câu hỏi dự đoán.

**Ví dụ:** hỏi về "Quy định bồi thường đất" nhưng câu trả lời dài dòng giải thích "Lịch sử Luật đất đai từ 1993" — câu hỏi sinh ngược chứa từ khóa về lịch sử, khoảng cách Cosine với câu hỏi gốc giảm mạnh.

### Thực hành: đánh giá với 2 cấu hình

Chạy đánh giá thực tế trên 2 cấu hình để thấy rõ sự biến động của các độ đo:

- **Cấu hình 1:** chunk_size = 250, top_k = 2 (cắt nhỏ, lấy vừa phải)
- **Cấu hình 2:** chunk_size = 1000, top_k = 2 (cắt lớn, giữ nguyên top-k để kiểm soát biến)

#### Golden Dataset — có cả "bẫy"

Một Golden Dataset tốt không chỉ chứa câu hỏi thông thường mà còn phải chứa các **bẫy (traps)**: 20 câu hỏi về Luật Đất đai 2024, trong đó có những câu ngoài luồng như "Công ty SpaceX được thành lập vào năm nào?" với đáp án chuẩn là "Tài liệu không đề cập". Thiết kế bẫy giúp kiểm tra khả năng từ chối của chatbot — đo bằng metric riêng **Correct Rejection Rate** để xem chatbot có trung thực từ chối hay lại tự bịa kiến thức ngoài.

```json
{
  "question": "Sổ đỏ, sổ hồng được gọi chính thức trong Luật Đất đai 2024 là gì?",
  "ground_truth": "Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất."
}
```

#### Script đánh giá tự động

Kịch bản 3 bước: **Inference** (vòng lặp nạp 20 câu hỏi, gọi chatbot sinh câu trả lời và thu thập contexts) → **Evaluation** (chuyển thành Dataset HuggingFace, đẩy cho Ragas chấm điểm) → **tính Correct Rejection Rate** cho nhóm câu bẫy.

```python
from ragas import evaluate
from ragas.metrics import (context_precision, context_recall,
                           faithfulness, answer_relevancy)

def run_evaluation_for_config(chunk_size, top_k, test_data):
    bot = PDFChatbot("Luat_Dat_Dai_2024.pdf",
                     chunk_size=chunk_size, top_k=top_k)
    # ... (chạy vòng lặp sinh câu trả lời -> data_dict)
    result = evaluate(
        Dataset.from_dict(data_dict),
        metrics=[context_precision, context_recall,
                 faithfulness, answer_relevancy],
        llm=ragas_llm, embeddings=ragas_embeddings,
    )
    df = result.to_pandas()

    # Tính CRR (Correct Rejection Rate) cho nhóm câu bẫy
    ood = df["ground_truth"].str.contains("không đề cập", na=False)
    correct = df[ood]["answer"].str.contains(
        "không đề cập|không có", na=False)
    print(f"[{chunk_size}] CRR: {correct.sum()/ood.sum():.2f}")

    # Lọc câu hợp lệ để tính trung bình
    cols = ['context_precision', 'context_recall',
            'faithfulness', 'answer_relevancy']
    return df[~ood][cols].mean()
```

#### Bảng kết quả và nhận xét

| Độ đo | Cấu hình 1 (Chunk 250, k=2) | Cấu hình 2 (Chunk 1000, k=2) |
| --- | --- | --- |
| Context Precision | 0.950 (n=10) | **1.000** (n=4) |
| Context Recall | 0.750 (n=16) | **0.923** (n=13) |
| Faithfulness | **0.433** (n=10) | 0.333 (n=3) |
| Answer Relevancy | 0.118 (n=16) | **0.141** (n=14) |

**Nhận xét chuyên sâu:**

- **Cấu hình 1 (chunk nhỏ):** Context Precision rất cao (0.950) nhưng Recall ở mức vừa phải (0.750) — top_k=2 không đủ gom lân cận, LLM thiếu thông tin đầy đủ, kéo theo Answer Relevancy thấp.
- **Cấu hình 2 (chunk lớn):** Context Recall tăng đáng kể (0.923) — chunk dài bao phủ đoạn văn bản lớn, ít bị rớt ý. Nhưng Faithfulness và Answer Relevancy vẫn chưa cao, cho thấy mô hình Gemma2 còn khó khăn khi bám sát ngữ cảnh với văn bản pháp lý phức tạp.

**Lưu ý quan trọng về độ tin cậy:** số lượng mẫu hợp lệ (n) của cấu hình 2 thấp bất thường — mô hình local nhỏ (Gemma2-9B) đôi khi không tuân thủ định dạng JSON đầu ra khi xử lý chuỗi ngữ cảnh quá dài, Ragas trả về NaN và mẫu bị loại. Điểm của cấu hình 2 do đó có độ tin cậy thống kê kém hơn. Một đặc điểm nội tại khác của LLM-as-a-judge: trong một số trường hợp, LLM giám khảo gộp ý hoặc bỏ qua tiểu tiết khi chia tách statement — ví dụ ngữ cảnh thực tế thiếu 1/7 loại đất nhưng Recall vẫn bị chấm 1.0 thay vì ≈ 0.857.

> **Bài học rút ra:** ở hệ thống lớn và phức tạp hơn, trade-off giữa Precision và Recall thường xuyên xuất hiện. Chiến lược khắc phục triệt để: **Parent-Child Retrieval** — nhúng chunk nhỏ để lấy Precision, nhưng trả về chunk lớn để lấy Recall.

### Nâng cao: dùng OpenAI API làm giám khảo

Khi cần hệ quy chiếu ổn định hơn, thay mô hình local bằng GPT-4:

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

evaluator_llm = ChatOpenAI(model="gpt-4", temperature=0)
ragas_llm = LangchainLLMWrapper(evaluator_llm)
ragas_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
```

Chi phí API có thể tốn kém vài nghìn đến vài chục nghìn tokens mỗi lần chạy — kiểm tra hạn mức trước. Bù lại, model thương mại lớn ổn định hơn trong suy luận NLI, thích hợp làm mốc tham chiếu (baseline); vẫn cần đối chiếu ngẫu nhiên với đánh giá của con người.

### 5 lỗi thường gặp trong RAG và cách khắc phục

#### 1. Lỗi "Biết tuốt" (Fail ở Faithfulness)

**Triệu chứng:** người dùng hỏi câu ngoài luồng ("Thủ tục ly hôn được quy định như thế nào?") — đáng ra phải từ chối, hệ thống lại kể vanh vách về Luật Hôn nhân gia đình dựa vào kiến thức huấn luyện gốc. **Nguyên nhân:** LLM bị ảo giác và phớt lờ ngữ cảnh. **Khắc phục:** System Prompt cực kỳ khắt khe — "CHỈ được phép dùng ngữ cảnh được cung cấp. Nếu không có thông tin, hãy nói 'Tài liệu không đề cập'. TUYỆT ĐỐI không dùng kiến thức bên ngoài." Cài `temperature = 0`.

#### 2. Lỗi "Cụt ý" (Fail ở Context Recall)

**Triệu chứng:** hỏi về 4 điều kiện chuyển nhượng quyền sử dụng đất, bot chỉ trả lời được điều kiện đầu tiên rồi dừng. **Nguyên nhân:** chunking quá thô, danh sách liệt kê bị đứt làm đôi, phần đuôi không lọt vào top-k. **Khắc phục:** Semantic Chunking hoặc Parent-Child Document Retriever.

#### 3. Lỗi "Lạc đề" (Fail ở Context Precision)

**Triệu chứng:** hỏi "Giao đất **không thu tiền** sử dụng đất là gì?", bot ưu tiên đoạn "Giao đất **có thu** tiền" lên top 1 vì từ khóa gần như trùng hoàn toàn, chỉ khác mỗi chữ "không". **Nguyên nhân:** Dense Embedding yếu trong phân biệt từ khóa chuyên ngành tương đồng. **Khắc phục:** Hybrid Search (kết hợp Vector Search với Keyword Search như BM25) và Cross-Encoder Re-ranking để chấm điểm lại top 10 kết quả trước khi đưa cho LLM.

#### 4. Lỗi "Nhiễu loạn ngữ cảnh" (Lost in the middle)

**Triệu chứng:** nhồi nhét 20 chunks để kéo Recall lên; câu trả lời nằm ở chunk số 10 nhưng LLM bỏ qua và kết luận không có thông tin. **Nguyên nhân:** LLM mắc hội chứng "Lost in the middle" — chỉ tập trung chú ý vào đầu và cuối prompt, bỏ quên phần giữa. **Khắc phục:** giới hạn số lượng context hợp lý (top 3–5), hoặc dùng kỹ thuật nén ngữ cảnh (Context Compression / LLMLingua) để gạn lọc trước khi đẩy vào prompt.

#### 5. Lỗi "Lệch định dạng" (Format Error)

**Triệu chứng:** yêu cầu trả lời dạng JSON hoặc bảng Markdown, bot trả về đoạn văn xuôi. **Nguyên nhân:** prompt chưa đủ tốt hoặc model quá nhỏ không theo được cấu trúc. **Khắc phục:** ép buộc đầu ra (Structured Outputs) qua Pydantic, Instructor, hoặc tính năng JSON Mode của API.

### Kết luận

Cũng giống như phát triển phần mềm truyền thống cần Unit Test, phát triển ứng dụng RAG cần một **Evaluation Pipeline** chặt chẽ. Việc định lượng bằng Ragas không chỉ giúp so sánh các mô hình nhúng hay thuật toán cắt văn bản — mà còn là minh chứng rõ ràng với khách hàng về độ chính xác và tin cậy của sản phẩm.

### Bài liên quan

- Trước đó: Multimodal RAG cho tài liệu PDF tiếng Việt
- Nền tảng liên quan: Hybrid Search với BM25, Dense Retrieval và RRF

### Nguồn

- [RAGAS: Automated Evaluation of RAG (Shahul Es et al., 2023, arXiv:2309.15217)](https://arxiv.org/abs/2309.15217) · [Ragas Official Documentation](https://docs.ragas.io/)
- Mã nguồn thực hành: [rag-advanced-evaluate (repo)](https://github.com/thaiptit123/rag-advanced-evaluate)
- Nội dung biên tập lại từ bài thực hành RAG Advanced của AI Guru x TiniX theo phong cách LearnWithHuy; API của Ragas có thể thay đổi theo phiên bản — bài viết dựa trên ragas 0.1.20.

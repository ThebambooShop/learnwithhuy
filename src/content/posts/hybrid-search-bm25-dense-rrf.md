---
title: "Hybrid Search với BM25, Dense Retrieval và RRF: xây dựng tìm kiếm tài liệu tiếng Việt từ con số 0"
description: "Hướng dẫn xây dựng hệ thống hybrid search cho văn bản pháp luật Việt Nam: kết hợp BM25 và dense retrieval bằng Reciprocal Rank Fusion, kèm query rewriting, benchmark Recall/MRR và cách chọn tham số."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-17"
cover: "/images/covers/posts/hybrid-search-bm25-dense-rrf.jpg"
views: 610
faq:
  - q: "Tại sao phải kết hợp BM25 và dense retrieval thay vì chỉ dùng một?"
    a: "BM25 giỏi khớp chính xác số hiệu và thuật ngữ pháp lý (01/2021/NĐ-CP) nhưng không hiểu rằng 'lập công ty' và 'đăng ký doanh nghiệp' cùng một chủ đề. Dense retrieval ngược lại — hiểu ngữ nghĩa nhưng dễ bỏ sót chuỗi số hiệu đặc thù. Hai góc nhìn bù lỗi cho nhau, RRF hợp nhất hai danh sách xếp hạng thành một."
  - q: "RRF hoạt động thế nào?"
    a: "Reciprocal Rank Fusion bỏ qua score gốc (BM25 và cosine không cùng thang đo), chỉ nhìn vị trí xếp hạng: mỗi tài liệu nhận điểm w/(k+rank) từ mỗi retriever. Tài liệu được cả hai retriever đồng thuận có lợi thế hơn tài liệu chỉ nổi bật trong một danh sách."
  - q: "Hằng số k=60 trong RRF có tối ưu cho mọi corpus không?"
    a: "Không. k=60 là baseline phổ biến từ công trình gốc SIGIR 2009. Nên giữ 60 ở lần đầu, sau đó thử lưới nhỏ (20, 40, 60, 100) trên validation set — k nhỏ làm vị trí đầu có ảnh hưởng mạnh hơn."
---

Bạn đang xây một ô tìm kiếm cho kho văn bản pháp luật. Người dùng hỏi "thành lập công ty cần thủ tục hồ sơ nào", trong khi corpus lại dùng cụm "đăng ký doanh nghiệp" — nếu chỉ so khớp từ khóa, hệ thống bỏ lỡ tài liệu đúng vì hai câu không dùng chung từ. Ngược lại, khi người dùng nhập chính xác `01/2021/NĐ-CP`, model ngữ nghĩa không giữ chuỗi số hiệu tốt bằng tìm kiếm từ khóa.

Vì vậy ta dùng **hai góc nhìn song song** và hợp nhất bằng **RRF**:

- **BM25 hỏi:** "Câu hỏi và tài liệu có dùng chung những từ quan trọng nào?"
- **Dense retrieval hỏi:** "Câu hỏi và tài liệu có nói về cùng một ý, dù cách diễn đạt khác nhau?"

Luồng xử lý: câu hỏi hội thoại → rewrite (giữ cả câu gốc) → BM25 và dense retrieval chạy song song → RRF hợp nhất → top-k kết quả kèm nguồn.

> ⚠️ **Ranh giới cần nhớ:** hệ thống chỉ làm nhiệm vụ *tìm tài liệu và hiển thị nguồn*. Retrieval giúp bạn tìm nơi cần đọc — nó không chứng minh văn bản còn hiệu lực hay cho biết văn bản áp dụng thế nào trong một vụ việc cụ thể. Không phải tư vấn pháp lý.

## Bốn thành phần trước khi viết code

### BM25 — tìm kiếm từ khóa thông minh

BM25 ưu tiên tài liệu chứa các từ quan trọng xuất hiện trong câu hỏi, có điều chỉnh hai hiện tượng: một từ lặp lại nhiều lần trong cùng tài liệu không được phép làm điểm tăng mãi, và một tài liệu dài không tự động được lợi chỉ vì có nhiều từ hơn. Điểm mạnh: số hiệu, tên cơ quan, thuật ngữ pháp lý. Điểm yếu: không tự hiểu hai cách gọi cùng một chủ đề.

Lưu ý kỹ thuật: thư viện `rank-bm25` nhận danh sách token chứ không tự quyết định cách tách từ — corpus và câu hỏi phải đi qua **cùng một hàm tiền xử lý**. Hai tokenizer khác nhau → điểm BM25 sai dù code vẫn chạy.

### Dense retrieval — tìm kiếm ngữ nghĩa

Embedding model biến mỗi câu thành một vector (trong bài này: 1.024 số). Những câu gần nghĩa tạo ra vector gần nhau — nhờ vậy câu hỏi đời thường vẫn tìm thấy đoạn ghi bằng thuật ngữ chính thức, dù không trùng từ khóa. Model đa ngôn ngữ chạy được trên CPU, nhưng **không được huấn luyện riêng cho pháp luật Việt Nam** — phải benchmark thay vì mặc định nó hiểu đúng.

### RRF — hợp nhất theo thứ hạng

BM25 score (8) và cosine score (0.4) không cùng thang đo — cộng trực tiếp sẽ làm một retriever lấn át retriever còn lại. RRF bỏ qua score gốc, chỉ nhìn vị trí:

$$\text{RRF}(d) = \sum_{r \in R} \frac{w_r}{k + \text{rank}_r(d)}$$

Trong đó `d` là một tài liệu, `R` là tập retriever, `rank_r(d)` là vị trí của tài liệu trong retriever `r`, `w_r` là trọng số tin cậy, `k` làm chênh lệch giữa các vị trí đầu bớt cực đoan.

**Ví dụ:** tài liệu đứng hạng 1 ở BM25 và hạng 2 ở dense (hai trọng số đều 1) nhận `1/61 + 1/62 ≈ 0,0325`. Tài liệu chỉ đứng hạng 1 ở BM25 nhận khoảng `0,0164`. Tài liệu được cả hai retriever đồng thuận có lợi thế rõ rệt — đây là trực giác quan trọng nhất của RRF.

### Query rewriting — viết lại câu hội thoại

Sau khi hỏi về đăng ký doanh nghiệp, người dùng hỏi tiếp "thủ tục này thực hiện ở đâu?" — cụm "thủ tục này" không cho biết thủ tục nào. Query rewriting dùng lịch sử để tạo câu độc lập: "thủ tục đăng ký doanh nghiệp qua mạng thực hiện ở đâu?". Nhưng rewriter cũng đoán sai được — hệ thống có trách nhiệm phải **giữ cả câu gốc lẫn câu đã viết lại** để kiểm tra, thay vì âm thầm thay đổi ý người dùng.

## Chuẩn bị môi trường và dự án

```bash
git clone https://github.com/lengocquanggit255/demo-hybrid-retrieval.git
cd demo-hybrid-retrieval

# macOS / Linux
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

## Bước 1 — Đọc dữ liệu và tiền xử lý

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

## Bước 2 — Tạo hai retriever

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

## Bước 3 — Kết hợp hai bảng xếp hạng bằng RRF

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

## Bước 4 (tùy chọn) — Viết lại câu hỏi bằng LLM

Gửi history và câu hỏi mới đến một LLM qua API tương thích OpenAI, với chỉ dẫn nghiêm ngặt: chỉ dùng thông tin có trong lịch sử, không tự thêm tên người/tổ chức/điều kiện mới, câu hỏi đã rõ nghĩa thì giữ nguyên. Lưu cả `original`, `rewritten`, `model`, phiên bản prompt và request ID trong cùng trace. Nếu lời gọi API thất bại hoặc kết quả rỗng, dùng lại câu gốc thay vì dừng toàn bộ retrieval.

```bash
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="your-api-key"
export LLM_MODEL="your-model-id"
```

## Bước 5 — Chạy truy vấn đầu tiên

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

## Bước 6 — Đánh giá bằng benchmark

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

## Bước 7 — Chọn top-k, trọng số và hằng số RRF

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

## Các lỗi thường gặp

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

## Tổng kết

Giá trị của hybrid không nằm ở chỗ nó luôn thắng — mà ở việc BM25 và dense nhìn dữ liệu theo hai cách khác nhau, nhờ đó **bù lỗi cho nhau**. RRF là một phép fusion nhỏ và dễ kiểm tra, nhưng chất lượng cuối cùng phụ thuộc vào corpus có nguồn, tiền xử lý nhất quán, log query rewrite và bộ benchmark có cả failure case. Giữ được những yếu tố đó, bạn thay model hay hạ tầng mà vẫn biết hệ thống thực sự tốt hơn hay chỉ trông có vẻ phức tạp hơn.

## Bài liên quan

- [LLM hoạt động như thế nào?](/bai-viet/llm-hoat-dong-nhu-the-nao/) — nền tảng embedding
- Tiếp theo trong lộ trình RAG nâng cao: [GraphRAG: từ văn bản tới Knowledge Graph](/bai-viet/graphrag-knowledge-graph/)

## Nguồn

- [Công thức RRF gốc — Cormack, Clarke & Büttcher, SIGIR 2009](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)
- [rank-bm25](https://github.com/dorianbrown/rank_bm25) · [Model BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) · [Sentence Transformers Semantic Search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
- Dataset: [YuITC/Vietnamese-Legal-Documents](https://huggingface.co/datasets/YuITC/Vietnamese-Legal-Documents) (chỉ dùng cho benchmark trong phạm vi demo, không phải URL chính thức của văn bản pháp luật)
- Nội dung biên tập lại từ bài thực hành Hybrid Search của AI Guru x TiniX theo phong cách LearnWithHuy; số liệu benchmark là kết quả quan sát trên máy cụ thể, không phải cam kết SLA.

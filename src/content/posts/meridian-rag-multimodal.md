---
title: "Meridian: RAG multimodal cho tài liệu bảo trì công nghiệp — cẩm nang toàn tập"
description: "Cẩm nang gộp trọn 8 bài Meridian trong một trang: vì sao text-chunk RAG thất bại trên PDF công nghiệp, ingestion layout-aware, chart digitiser, hybrid retrieval 8 kênh, conflict resolution, CRAG grader, claim-level verifier và deploy Qdrant offline."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-24"
cover: "/images/covers/posts/meridian-rag-bao-tri-cong-nghiep.jpg"
featured: false
views: 180
faq:
  - q: "Cẩm nang này gồm những gì?"
    a: "Toàn bộ 8 bài trước đây đăng riêng giờ gộp trong một trang, chia thành 8 phần đánh số — đọc tuần tự hoặc nhảy tới phần cần đều được."
  - q: "Nên đọc theo thứ tự không?"
    a: "Các phần được xếp theo thứ tự học gợi ý. Đọc lộn vẫn hiểu vì mỗi phần đứng độc lập, nhưng lần đầu học thì nên theo thứ tự. Tổng thời gian đọc khoảng 90 phút."
---

## Bạn sẽ học được gì

- **Phần 01. Meridian: vì sao text-chunk RAG thất bại trên tài liệu bảo trì công nghiệp**
- **Phần 02. Ingestion layout-aware: biến PDF bảng biểu và scan thành evidence có citation**
- **Phần 03. Chart digitiser: đọc số liệu từ biểu đồ trong PDF — caption không đủ**
- **Phần 04. 8 kênh hybrid retrieval: từ BM25 đến graph — hợp nhất bằng weighted RRF**
- **Phần 05. Fact index và conflict resolution: khi manual và bulletin nói khác nhau**
- **Phần 06. CRAG grader và abstention: trả lời 'không biết' là tính năng, không phải lỗi**
- **Phần 07. Claim-level verifier: chặn hallucination trước khi câu trả lời ra tới người dùng**
- **Phần 08. Benchmark và deploy: đóng benchmark held-out, chạy Qdrant offline**

> **Ai nên đọc:** Kỹ sư xây RAG cho tài liệu thật: PDF, bảng biểu, scan, bảo trì công nghiệp.
> **Điều kiện đầu vào:** Python trung cấp; đã từng xây hoặc đọc pipeline RAG cơ bản.
> **Tổng thời gian đọc:** ≈91 phút — có thể đọc dần theo phần, thời lượng từng phần ghi ngay trên tiêu đề.

01. Meridian: vì sao text-chunk RAG thất bại trên tài liệu bảo trì công nghiệp — ≈11 phút

"Torque bulông cánh quạt HX-200 bao nhiêu Nm?" — một câu hỏi đơn giản của kỹ thuật viên bảo trì. Câu trả lời nằm rải rác trên sáu nguồn: giá trị nằm trong **một dòng của bảng** ở manual, công suất riêng tại 50% load chỉ có trong **ảnh biểu đồ**, quy tắc an toàn trong **warning box**, số torque mới hơn trong **service bulletin**, lịch sử lỗi trong **CSV log**, mã alarm ở hiện trường là **ảnh chụp panel**.

RAG chunk-text truyền thống — chunk, embed, top-k, đưa cho LLM — đi một con đường qua cả sáu nguồn này, và sai mỗi kiểu tài liệu một cách khác nhau:

| Nguồn | Text-chunk RAG sai thế nào |
| --- | --- |
| Table row | Bảng 40 dòng bị làm phẳng thành một chunk; LLM trượt cột, lấy nhầm ô kề |
| Chart image | Bị bỏ qua hoặc chỉ còn caption — giá trị "tại 50% load" không tồn tại trong text |
| Warning box | Call-out dính vào đoạn kề, biến mất khỏi evidence |
| Bulletin mới hơn | Hai giá trị 45 vs 52 Nm bị trộn lẫn, LLM chọn theo thứ tự xuất hiện |
| CSV log | Log thành text chunk; LLM "đếm" tần suất alarm bằng arithmetic và sai |
| Ảnh panel | Không OCR, không descriptor — vô hình với index |

Meridian — repo RAG đa modality cho tài liệu bảo trì — thiết kế để từng lỗi trên không xảy ra. Nguyên lý nằm trong một câu:

> **Treat every modality as structured, citable evidence, decide first whether an answer is possible, compute what can be computed, and verify what is written.**

Mỗi mệnh đề ứng với một lớp: ingestion tạo evidence có citation; controller quyết định trước answer có khả thi không; công cụ tính thay LLM khi cần số chính xác; verifier kiểm từng claim trước khi trả người dùng.

### Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Evidence-grounded RAG** | Bảng, biểu đồ, warning, log, ảnh là evidence có cấu trúc và citation được, không phải text phẳng |
| **Layout-aware parsing** | Bảng → table + per-row chunks + typed facts; call-out → WARNING chunk; figure crop; bbox |
| **Hybrid retrieval (8 kênh)** | BM25, LSA dense, char-n-gram, entity, fact, visual, PRF, graph → weighted RRF → rerank → MMR |
| **CRAG grader** | Chấm mức phủ evidence trước khi sinh; thiếu → corrective retry hoặc abstain |
| **Abstention** | Từ chối trả lời khi evidence không đủ hoặc premise sai, thay vì đoán |
| **Conflict resolution** | Cùng (model, subject, attribute) từ nhiều nguồn → precedence: revised > bulletin > manual > effective date |
| **Claim verifier** | Kiểm từng claim: số unit-aware, identifier, tham chiếu, phủ định; fail → repair hoặc fallback |

### Luồng 9 bước từ câu hỏi đến câu trả lời

| # | Bước | Việc làm |
| --- | --- | --- |
| 1 | Perception | OCR + visual descriptor + phát hiện alarm code/model trên ảnh đính kèm |
| 2 | Analyzer | Intent (spec / procedure / troubleshoot / figure / analytics / general), models, codes, quantities, yes/no premise, phát hiện model lạ |
| 3 | Hybrid retrieval | 8 kênh → weighted RRF → late-interaction rerank → MMR |
| 4 | CRAG grader | Chấm correct / ambiguous / incorrect; incorrect → retry (relaxed model filter, keyword rewrite) → hết lượt thì abstain |
| 5 | Evidence | top-k + follow "see Table 4" đến đúng row + attach WARNING cùng section |
| 6 | Tools | lookup_spec (+conflict resolution), check_premise, chart reader, unit conversion |
| 7 | Compose | Offline: extractive composer với citation `[n]`. LLM mode: model viết từ evidence đánh số + 2 tools |
| 8 | Verify | Kiểm từng claim: số unit-aware, identifier/date, tham chiếu, phủ định, lexical coverage |
| 9 | Finalise | Calibrated confidence (Platt scaling), faithfulness, citations kèm bbox |

Mỗi bước phát một `TraceEvent` stream qua SSE — khi Meridian từ chối, bạn thấy nó dừng ở bước nào. Lọc theo model áp ở mức document: passage HX-500 không bao giờ trả lời câu hỏi HX-200, dù lexical khớp.

### Typical RAG demo vs Meridian: bảy điểm khác biệt

| Typical RAG demo | Meridian |
| --- | --- |
| Chunk text, embed, top-k | Layout-aware parsing: bảng → table + per-row chunks + typed numeric facts, warning call-outs, figure crops, OCR cho scan, bounding boxes |
| Chart và image bị bỏ qua hoặc chỉ caption | Chart digitiser đọc giá trị trực tiếp từ biểu đồ bar/line (trục hiệu chuẩn, tick label OCR vote); image → figure retrieval qua visual descriptor |
| Một vector search | 8 kênh retrieval (BM25, LSA dense, char-n-gram, entity, fact, visual, PRF, graph) → weighted RRF → late-interaction rerank → MMR |
| Luôn trả lời | CRAG-style grader + corrective retries + abstention (model lạ, từ ngoài corpus) |
| Nguồn mâu thuẫn bị trộn lẫn | Provenance-aware conflict resolution (bulletin supersedes manual) + false-premise detection |
| "The LLM said so" | Claim-level hallucination verifier (số unit-aware, identifier, phủ định, tham chiếu) kèm tự repair |
| LLM tự tính toán | Tools: pandas analytics chính xác trên log, unit conversion, chart interpolation |

Verifier tách rời generator — cùng một bộ kiểm tra bảo vệ cả offline composer lẫn LLM được cấu hình; output LLM không được tin mặc định, không repair được thì fallback về composer extractive.

### Offline-first: LSA + BM25, không cần LLM

> **Offline-first (LSA + BM25, không LLM):** benchmark tái lập được, chạy mọi nơi, không data rời máy. Chi phí: hiểu paraphrase yếu hơn neural encoder — giảm nhẹ bằng synonym canonicalisation, char-n-grams, late interaction.

Dense index mặc định là LSA (TF-IDF → SVD) trên word + char n-grams, in-memory; Docker Compose dùng Qdrant làm vector database — backend, không phải model embedding. Learned ranker 17 features đã train nhưng **không được adopt** vì không thắng weights hand-tuned trên held-out split — quyết định theo số, không theo trend.

### Số liệu benchmark

Benchmark chính: 93 câu hỏi (43 held-out), corpus synthetic 6 documents, 157 chunks.

| Chỉ số | Kết quả |
| --- | --- |
| Truy xuất (held-out) | Hit@1 89.5% · Hit@5 100% · MRR 0.88 (BM25 đơn lẻ: Hit@1 84.2%, Hit@5 97.4%) |
| Correctness (unit-aware) | 93.1% tổng thể, 92.5% held-out |
| Từ chối câu hỏi không thể trả lời | 100% (false abstention trên câu trả lời được: 1.1%) |
| Faithfulness | 100% claims được evidence hỗ trợ |
| Calibration confidence (held-out) | ECE 0.027 → 0.008 sau Platt scaling |
| Hallucination injection | Phát hiện 91.7% (số 87.5, fabricated 94.4, phủ định 93.8, entity 91.5) |

Stress benchmark: 100 documents, 700 chunks, 700 câu (600 answerable, 100 unanswerable) — correctness 90%, false abstention 10%, Hit@1 65%, MRR 0.771; Hit@1 giảm sâu khi corpus lớn hơn vì lọc theo model và fusion phải làm việc nặng hơn. Ranh giới: corpus synthetic có noise kiểm soát, không phải claim production trên manual thật. 6/93 câu fail đã biết — multi-hop ghép hai document, một ca OCR data plate, vài câu procedure khác xa manual.

### Quickstart 5 phút

```bash
#    macOS: brew install tesseract   |   Ubuntu/Debian: sudo apt install tesseract-ocr
# 2. Code + môi trường (Python 3.10+)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 3. Start (lần đầu ingest demo corpus ~30 s)
python -m meridian --load-demo
# mở http://127.0.0.1:8000
```

Năm câu demo: torque HX-200 impeller bolt (conflict 45 vs 52 Nm, bulletin thắng) · HX-200 chịu dung dịch 150 °C không (false premise, từ chối) · công suất riêng HX-500 tại 50% load (chart image) · mã alarm phổ biến nhất trong log (pandas chính xác) · CEO của Helix Dynamics (abstain vì ngoài corpus).

### Sketch "decide first" bằng Python thuần

Sketch tái hiện logic route "decide first" của Meridian bằng if/else thuần, chạy offline:

```python
def route_intent(question: str, has_image: bool = False) -> str:
    """Bước 'decide first' của Meridian: chọn nhánh pipeline TRƯỚC khi retrieval."""
    q = question.lower().strip()
    unknown_models = ("hx-999", "zz-series")      # model không có trong corpus

    if any(m in q for m in unknown_models):
        return "abstain"          # không bao giờ trả lời thay model khác
    if has_image:
        return "perception"       # OCR + visual descriptor + phát hiện alarm code/model
    if any(k in q for k in ("phổ biến nhất", "thống kê", "số lần", "log")):
        return "tool_analytics"   # pandas tính chính xác trên CSV log
    if any(k in q for k in ("tại 50%", "derating", "biểu đồ", "đồ thị")):
        return "tool_chart"       # chart digitiser đọc giá trị
    if q.startswith(("hx-", "có ", "is ")):
        return "spec_check"       # lookup_spec + check_premise (câu yes/no)
    return "retrieval"            # 8 kênh -> RRF -> grader -> compose -> verify


def run_pipeline(branch: str) -> str:
    """Map nhánh về chuỗi bước trong luồng 9 bước (1..9)."""
    steps = {
        "abstain":        "1 bài -> 2 analyzer -> từ chối",
        "perception":     "1 perception -> 2 analyzer -> 3 retrieval -> 8 verify",
        "tool_analytics": "6 tools pandas -> 7 compose -> 8 verify",
        "tool_chart":     "6 chart reader -> 7 compose -> 8 verify",
        "spec_check":     "3 retrieval -> 6 lookup_spec -> 8 verify",
        "retrieval":      "3 retrieval -> 4 grader -> 5 evidence -> 6 tools -> 7 compose -> 8 verify",
    }
    return steps[branch]


if __name__ == "__main__":
    tests = [
        ("Torque của bulông cánh quạt HX-200 là bao nhiêu?", False),
        ("HX-200 chịu được dung dịch 150 °C không?", False),
        ("Công suất riêng của HX-500 tại 50% load?", False),
        ("Mã alarm nào xuất hiện nhiều nhất trong log?", False),
        ("CEO của Helix Dynamics là ai?", False),   # vẫn vào retrieval, grader sẽ abstain
        ("Mã alarm này là gì?", True),               # kèm ảnh chụp panel
    ]
    for question, has_image in tests:
        branch = route_intent(question, has_image)
        print(f"{branch:>14} | {run_pipeline(branch)}")
```

Chạy ngay, không thư viện ngoài. Keywords là demo-level; bản thật dùng regex entity `\b[A-Z]{1,4}-\d{2,5}...\b` và quantity parser có unit để nhận `150 °C` là một quantity.

### Bài tập

**Làm theo** — Chạy quickstart, hỏi lần lượt 5 demo questions. Mở trace SSE: ghi bước pipeline dừng (grader, premise hay verifier) và modality của citation — table_row, chart hay ocr_page.

**Tự sửa** — Sửa `route_intent` thêm nhánh `procedure` cho câu hỏi bắt đầu bằng "cách / làm thế nào / replace": route vào `retrieval` nhưng trả intent khác để Evidence stage attach các step chunks; chạy lại script và kiểm tra bảng nhánh đổi đúng.

**Mở rộng** — Viết hàm `weighted_rrf(rankings, weights, k=60)` theo công thức `score = Σ w_i / (k + rank_i)` cho 2 kênh BM25 + dense, test trên 5 câu demo và so Hit@1 trước/sau fusion; đối chiếu cách Meridian fuse 8 kênh trong `retrieval/pipeline.py`.

### Lỗi thường gặp

- ⚠️ `TesseractNotFoundError` hoặc trang scan trả về rỗng → Tesseract chưa cài → macOS `brew install tesseract`, Ubuntu `sudo apt install tesseract-ocr`; ngoài OCR, mọi path khác vẫn chạy.
- ⚠️ Hỏi giá trị trên chart nhưng hệ thống trả lời từ caption → câu hỏi thiếu mốc (tại 50% load) nên không route vào chart digitiser → đưa mốc vào câu hỏi; kiểm tra citation modality `chart`.
- ⚠️ Trả lời 45 Nm dù bulletin đã ra 52 Nm → system tự viết không có conflict resolution → gắn doc_type + effective_date vào mỗi fact và áp precedence; giá trị thua hiện ConflictNote, không bị giấu.
- ⚠️ Abstain sai trên câu hỏi hợp lệ → paraphrase mạnh khiến grader thấy query term thiếu trong corpus → synonym canonicalisation + char-n-gram; đọc trace xem grader chấm bước nào.
- ⚠️ Port 8000 bị chiếm khi start → service khác đang chạy → `python -m meridian --port 8010`.

### FAQ

**Meridian có cần API key, LLM hay GPU để chạy không?**
Không. Mặc định deterministic offline: LSA + BM25 chạy trên CPU, không API key, không GPU, không data rời máy. LLM (Anthropic hoặc server OpenAI-compatible như Ollama) là tùy chọn và vẫn phải đi qua cùng một verifier.

**Con số 93.1% correctness đo trên dữ liệu gì?**
Benchmark synthetic 93 câu hỏi (43 held-out) sinh cùng corpus 6 documents, 157 chunks. Đây là bằng chứng cho thiết kế pipeline, không phải claim về manual thật của nhà máy.

**Vì sao hệ thống trả lời sai khi manual và service bulletin mâu thuẫn?**
Text-chunk RAG trộn lẫn hai nguồn rồi để LLM đoán. Meridian đưa giá trị về dạng Fact có provenance rồi áp precedence: cột revised trước, bulletin trên manual, rồi effective date mới nhất; giá trị thua thành ConflictNote.

**Khi nào Meridian từ chối trả lời thay vì đoán?**
Ba tình huống: grader chấm evidence chưa đủ sau corrective retry; câu hỏi nhắc model không có trong corpus hoặc premise sai; verifier không repair được claim unsupported nào.

### Tài liệu gốc

- [Meridian README](https://github.com/punit2911/meridian-multimodal-rag#readme) — bảng "Why it is different", quick start, measured results
- [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) — luồng 9 bước, decisions table, retrieval chi tiết
- Bài liền kề trong series: Ingestion layout-aware: biến PDF bảng biểu và scan thành evidence có citation · Hybrid retrieval 8 kênh · bài nền [Multimodal RAG PDF tiếng Việt](/bai-viet/rag-nang-cao-cam-nang/) — nơi phân tích hiện tượng COLUMN_SLIP khi bảng bị làm phẳng

---

02. Ingestion layout-aware: biến PDF bảng biểu và scan thành evidence có citation — ≈11 phút

Một manual PDF chứa bảng torque 40 dòng, một service bulletin DOCX, một CSV log 6 tháng và một trang scan mờ — nạp cả bốn vào hệ thống. Ingestion là nơi RAG thắng hoặc thua trước cả khi LLM xuất hiện. Chunk-text truyền thống làm phẳng toàn trang: bảng thành chuỗi ký tự, warning box dính vào đoạn kề, scan thành trang trắng, citation trỏ cả trang thay vì đúng vùng.

Meridian chọn hướng ngược lại: **layout-aware parsing** — đọc PDF theo bố cục thật, xuất chunks có cấu trúc, facts có kiểu dữ liệu, bbox có tọa độ. Bài này đi qua từng module ingestion.

### Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Layout-aware parsing** | Phân tích PDF theo bố cục: heading theo font-size, bảng qua pdfplumber, call-out box, figure crop — không làm phẳng toàn trang |
| **Per-row chunk** | Mỗi dòng bảng thành một chunk riêng, mang caption bảng + section làm context |
| **Typed fact** | Cặp (attribute, value, unit) khai thác từ dòng bảng, lưu kèm provenance để lookup chính xác |
| **Bounding box (bbox)** | Tọa độ vùng chứa chunk trên trang; UI highlight đúng vùng khi mở "View source page" |
| **Multi-pass OCR (`ocr_best`)** | Chạy Tesseract nhiều cấu hình (deskew, adaptive threshold) rồi chọn/ghép kết quả tốt nhất |
| **Immutable snapshot** | Index build hoàn chỉnh trong object mới rồi swap atomic; không có index dở dang |
| **Dedupe SHA-256** | Trước khi lưu, hash file; file trùng bị bỏ qua an toàn khi upload lại |

### PDF đi qua ingest/pdf.py

Sáu bước mỗi trang:

- **Heading detection theo font-size** — đoạn cỡ chữ lớn hơn thân bài là section heading; tên section gắn vào context của mọi chunk thuộc section đó.
- **Bảng qua pdfplumber** — lưới ô được bóc thành một **table chunk** (toàn bảng, giữ ngữ cảnh) + **per-row chunks** (mỗi dòng một chunk, để truy xuất) + **typed numeric facts** cho từng ô số.
- **Call-out box → WARNING chunk riêng** — box cảnh báo không trộn vào đoạn văn; Evidence stage attach các WARNING cùng section khi trả lời.
- **Figure crop + page render** — mỗi figure cắt riêng (phục vụ chart digitiser và visual retrieval), trang được render PNG để highlight evidence.
- **Per-chunk bounding boxes** — mọi chunk mang tọa độ vùng trên trang.
- **Auto OCR** — trang trích xuất được quá ít ký tự → render → chạy Tesseract.

> **Rows as chunks:** một câu hỏi khớp một dòng bảng, không phải cả bảng 40 dòng. Row chunk mang caption của bảng ("Table 2 — Fastening torques") làm context, nên retrieval vẫn biết dòng đó thuộc bảng nào.

Hệ quả trực tiếp: hỏi "Torque bulông cánh quạt HX-200?" khớp đúng dòng "Impeller bolt: 45 Nm" thay vì nạp cả bảng cho LLM — loại bỏ nguy cơ trượt cột (COLUMN_SLIP) đã phân tích trong bài nền Multimodal RAG PDF tiếng Việt.

### Facts as first-class index

> **Facts as first-class index:** mỗi fact là một tuple (model, subject, attribute, value, unit, provenance) — không phải text. Từ tuple này hệ thống làm được exact lookup, unit conversion (10 bar = 145 psi) và conflict resolution — việc bất khả thi với text chunk thuần.

Đây là quyết định kiến trúc quan trọng nhất của ingestion. Shape thật của `Fact` trong `meridian/schemas.py`:

| Field | Ý nghĩa |
| --- | --- |
| `model`, `subject`, `attribute` | Khóa tra cứu: "HX-200" + "impeller bolt" + "torque" |
| `value`, `unit`, `display` | 45.0, "nm", "45 Nm" — value là số thật, không phải string |
| `doc_id`, `doc_type`, `doc_title` | Provenance: manual \| bulletin \| log \| card |
| `effective_date` | Bản effective mới hơn thắng khi conflict |
| `revised`, `previous` | Cờ nhận từ header cột "revised/new" hay "previous/old" |
| `approximate` | Giá trị đọc từ chart digitiser — bị loại khỏi conflict resolution |

Khi hai document cùng khẳng định (HX-200, impeller bolt, torque) bằng hai giá trị khác nhau, `resolve_conflicts` trong `index/facts.py` áp precedence: cột revised trước, rồi bulletin trên manual, rồi effective date mới nhất. Giá trị thua không bị xóa — thành `ConflictNote` hiển thị trong UI. Dòng key-value ("Maximum starts per hour: 6") được khai thác qua `mine_kv_facts` thành fact cùng shape.

### Scan: ocr.py

Trang scan không phải fallback rẻ tiền mà là path có chất lượng kiểm soát:

- **Deskew** — chỉnh nghiêng trang trước khi OCR.
- **Adaptive threshold** — tăng tương phản cho ảnh chụp/scan kém.
- **Multi-pass `ocr_best`** — chạy Tesseract nhiều cấu hình, vote chọn kết quả tốt nhất thay vì tin một lần chạy.
- **Regex repair cho alarm code** — OCR đọc "HX2O0" được sửa về dạng mẫu `[A-Z]{1,4}-\d{3,4}`; cùng regex này rút entities cho channel entity retrieval.

### Formats khác: office.py, images.py

- **DOCX service bulletin** — parse thành chunks + facts; doc_type gắn "bulletin" để precedence đúng khi conflict với manual.
- **CSV/XLSX log** — log không bị chunk thành text mà trở thành **datasets + aggregate chunks**: analytics chạy pandas trên dataset gốc, đếm chính xác thay vì LLM đếm bằng văn.
- **TXT/MD** và ảnh — path đơn giản hơn; ảnh đi qua perception (OCR + visual descriptor + phát hiện model/alarm code).

### Persistence: SQLite + snapshot immutable

Document và chunks persist vào SQLite cùng các file dẫn xuất (page images, figure crops, table data). Mỗi file hash SHA-256 — upload lại file y hệt bị bỏ qua. Index gồm nhiều lớp: lexical + char-n-gram, entity + fact + visual + graph, dense (LSA in-memory mặc định, hoặc Qdrant trong Docker). Khi corpus thay đổi:

> **Immutable index snapshots:** mỗi thay đổi rebuild một object `Indexes` mới và swap atomic sau khi build xong — readers never see half-built state. **SQLite + files:** persistence zero-ops; index rebuild từ SQLite khi start.

### Schemas thật: Chunk và Citation

Hai text field của `Chunk` là điểm dễ bỏ sót nhất khi tự thiết kế:

| Field | Vai trò |
| --- | --- |
| `text` | Text được **index**: prefix "doc title \| section" + content — phục vụ retrieval |
| `content` | Text sạch cho **evidence** — answer chỉ được phép quote phần này |
| `modality` | text \| table \| table_row \| figure \| chart \| warning \| ocr_page \| image |
| `parent_id` | Trỏ về section root (`doc_id:sec:...`) — dùng khi expand evidence |
| `bbox` | `BBox(x0, y0, x1, y1, page_width, page_height)` theo convention pdfplumber, gốc top-left |
| `meta` | Chứa `refs` (tham chiếu "Table 4") và `facts` mined từ chunk |

`Citation` là contract trả về UI: `index`, `chunk_id`, `doc_title`, `page`, `modality`, `snippet`, `bbox` (list `[x0, y0, x1, y1]`), `via` (retrieval \| crossref \| warning \| tool \| calculator) và `score`. Nhờ bbox, "View source page" highlight đúng dòng bảng, không phải cả trang.

### Sketch Chunk + Fact chạy offline

```python
"""Sketch data contracts của Meridian (rút gọn từ schemas.py) + build_fact chạy offline."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float
    page_width: float
    page_height: float


@dataclass
class Chunk:
    id: str
    doc_id: str
    page: int = 1
    modality: str = "text"        # text | table | table_row | figure | chart | warning | ocr_page | image
    text: str = ""                # text được index: "title | section\ncontent"
    content: str = ""             # text sạch cho evidence — answer chỉ được quote phần này
    section: str = ""
    parent_id: Optional[str] = None
    bbox: Optional[BBox] = None
    entities: list = field(default_factory=list)   # alarm code, model name rút từ regex


@dataclass
class Fact:
    model: str
    subject: str
    attribute: str
    value: float
    unit: Optional[str]
    chunk_id: str
    doc_id: str
    doc_type: str = "manual"      # manual | bulletin | log | card | image | notes
    effective_date: Optional[str] = None
    revised: bool = False         # đến từ cột "revised/new"
    previous: bool = False        # đến từ cột "previous/old"
    approximate: bool = False     # đến từ chart digitiser — loại khỏi conflict resolution


UNIT_ALIASES = {"nm": "nm", "n·m": "nm", "bar": "bar", "psi": "psi"}


def build_fact(value, unit, model, subject, attribute, provenance):
    """provenance là dict nguồn gốc (chunk_id, doc_id, doc_type...) — Fact cần nó để giải conflict."""
    p = dict(provenance)
    return Fact(
        model=model.upper(),
        subject=subject,
        attribute=attribute.lower(),
        value=float(value),
        unit=UNIT_ALIASES.get((unit or "").lower(), unit),
        chunk_id=p["chunk_id"],
        doc_id=p["doc_id"],
        doc_type=p.get("doc_type", "manual"),
        effective_date=p.get("effective_date"),
        revised=bool(p.get("revised")),
        previous=bool(p.get("previous")),
        approximate=bool(p.get("approximate")),
    )


def resolve_conflicts(facts):
    """Thứ tự ưu tiên: revised > bulletin > manual > effective_date mới hơn."""
    def rank(f):
        return (1 if f.revised else 0,
                {"bulletin": 2, "manual": 1}.get(f.doc_type, 0),
                f.effective_date or "")
    winner = max(facts, key=rank)
    return winner, [f for f in facts if f is not winner]


if __name__ == "__main__":
    bbox = BBox(x0=72, y0=340, x1=520, y1=360, page_width=595, page_height=842)
    row = Chunk(id="hx_manual:0012", doc_id="hx_manual", page=4, modality="table_row",
                content="Impeller bolt: 45 Nm", bbox=bbox, entities=["HX-200"])
    facts = [
        build_fact(45, "Nm", "hx-200", "Impeller Bolt", "Torque",
                   {"chunk_id": row.id, "doc_id": row.doc_id,
                    "doc_type": "manual", "effective_date": "2024-03-01"}),
        build_fact(52, "Nm", "hx-200", "Impeller Bolt", "Torque",
                   {"chunk_id": "hx_sb7:0003", "doc_id": "hx_sb7",
                    "doc_type": "bulletin", "effective_date": "2025-06-15"}),
    ]
    winner, losers = resolve_conflicts(facts)
    print(f"winner: {winner.value} {winner.unit} ({winner.doc_type})")
    for f in losers:
        print(f"conflict: {f.value} {f.unit} ({f.doc_type}) -> ConflictNote")
```

Chạy thuần stdlib. Trong repo thật, `ChunkBuilder.add` tự sinh id tăng dần (`doc_id:0001`), nối context "title | section" vào `text` và `add_facts` đính fact vào `chunk.meta["facts"]` — toàn bộ hàm thuần, dễ unit-test.

### Bài tập

**Làm theo** — Chạy `python -m meridian --load-demo`, mở Knowledge base tab, upload một PDF có bảng. Đếm số chunk theo modality qua UI; click `[n]` trong câu trả lời, mở "View source page" và quan sát bbox highlight đúng dòng bảng.

**Tự sửa** — Thêm alias unit mới vào `UNIT_ALIASES` (ví dụ "n.m" → "nm"); thêm test `build_fact` cho header "Torque (N·m)". Sau đó sửa `resolve_conflicts` đảo ưu tiên: effective_date mới hơn thắng trước doc_type — ghi nhận kết quả demo đổi thế nào và vì sao precedence gốc an toàn hơn.

**Mở rộng** — Viết `table_to_records` mini: nhận bảng Markdown pipe (`| Model | Torque (Nm) |`) và trả list fact dict (subject, attribute, value, unit). Đối chiếu với hàm thật `table_to_records` trong `meridian/ingest/common.py` — pure function, xử lý thêm cột unit và cờ previous/revised.

### Lỗi thường gặp

- ⚠️ Trang scan ra chunk rỗng → Tesseract chưa cài hoặc trang quá mờ → cài Tesseract; pipeline có sẵn deskew + adaptive threshold trong `ocr_best`; nếu vẫn kém, tăng DPI khi render trang.
- ⚠️ Fact không có unit → header không chứa "(unit)" và bảng không có cột unit/uom → chuẩn hoá header nguồn hoặc đưa unit vào cột riêng; dòng "key: value" dùng `mine_kv_facts` vẫn ra fact.
- ⚠️ Row chunk tìm thấy nhưng "View source page" highlight sai chỗ → chunk thiếu bbox riêng → bbox bắt buộc per-chunk lấy từ pdfplumber; kiểm tra `Citation.bbox` khác None khi debug.
- ⚠️ Upload lại file tạo bản trùng → dedupe SHA-256 chỉ nhận đúng file y nguyên; file đã tự chỉnh một chút → hash khác → là document mới, không phải bug → muốn thay thế thì xóa bản cũ trước khi upload.
- ⚠️ Câu trả lời vẫn dùng giá trị cũ ngay sau upload → snapshot mới chưa build xong, swap atomic chưa xảy ra → đây là hành vi đúng (không index dở dang); chờ trace rebuild hoàn tất hoặc refresh.

### FAQ

**Một dòng bảng thành một chunk thì số chunk tăng nhiều, retrieval có chậm không?**
Có tăng (bảng 40 dòng → 41 chunks) nhưng đổi lại precision truy xuất: câu hỏi khớp một dòng thay vì cả bảng. RRF fuse và MMR lọc gần-trùng; chi phí build một lần khi upload, không phải mỗi câu hỏi.

**Tesseract có bắt buộc phải cài không?**
Chỉ cần cho trang scan. macOS: brew install tesseract; Ubuntu: sudo apt install tesseract-ocr. Không có Tesseract thì mọi path khác — PDF text, bảng, DOCX bulletin, CSV/XLSX log, TXT/MD — vẫn ingest bình thường.

**Unit nằm ở header bảng hay ở cột riêng thì fact gắn unit thế nào?**
Header kiểu 'Torque (Nm)' được regex tách '(Nm)' thành unit cho value; nếu bảng có cột unit/uom thì unit lấy theo từng dòng. Header chứa 'previous/old' hoặc 'revised/new' gắn cờ previous/revised phục vụ conflict resolution.

**Vì sao phải build snapshot mới rồi mới swap, không update index tại chỗ?**
Mỗi upload hoặc xóa rebuild một object Indexes mới và swap atomic sau khi build xong — người đọc không bao giờ thấy index dở dang. Start lại thì index rebuild từ SQLite nên không mất gì.

### Tài liệu gốc

- [Meridian README](https://github.com/punit2911/meridian-multimodal-rag#readme) — quick start, kiến trúc ingestion, measured results
- [docs/MODULES.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/MODULES.md) — bảng module và 15 kỹ thuật
- [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) — decisions table ("Rows as chunks", "Facts as first-class index", immutable snapshots)
- Mã nguồn đọc trong bài: [meridian/schemas.py](https://github.com/punit2911/meridian-multimodal-rag/blob/main/meridian/schemas.py) · [meridian/ingest/common.py](https://github.com/punit2911/meridian-multimodal-rag/blob/main/meridian/ingest/common.py)
- Bài liền kề trong series: Bài 1 — Meridian: vì sao text-chunk RAG thất bại trên tài liệu bảo trì công nghiệp · Bài 3 — Chart digitiser đọc biểu đồ · bài nền [Multimodal RAG PDF tiếng Việt](/bai-viet/rag-nang-cao-cam-nang/)

---

03. Chart digitiser: đọc số liệu từ biểu đồ trong PDF — caption không đủ — ≈10 phút

Caption của biểu đồ trong manual máy bơm thường chỉ viết vậy: *curve of head vs flow*. Người dùng hỏi: *head tại 70 m³/h là bao nhiêu?* Câu trả lời nằm trong các pixel của đường cong — captioning trả lời được "biểu đồ này vẽ cái gì", không trả lời được "giá trị là bao nhiêu tại điểm X".

Vì vậy Meridian có khối riêng — **chart digitiser** trong `ingest/figures.py` — biến ảnh bar/line chart thành bộ số (x → y): tìm hộp trục, calibration pixel → giá trị, OCR tick label bằng vote nhiều pass, tách series theo màu, nội suy tại điểm hỏi. Mọi giá trị đọc được gắn cờ approximate. Bài này đi qua từng bước với hằng số thật.

### Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Chart digitiser** | Biến ảnh bar/line chart thành bộ số (x → y): trục, calibration, series, interpolation |
| **Axis calibration** | Fit `value = a·pixel + b` từ cặp (vị trí tick, giá trị tick label) |
| **Tick label voting** | Đọc cùng nhãn qua nhiều scale OCR + binarisation, chọn nhãn phổ biến |
| **Visual descriptor** | Vector 264 chiều: HSV + HOG-like + ink-layout, image-to-figure retrieval |
| **Approximate fact** | Giá trị đọc từ chart, gắn `approximate: true` — evidence, không thi đấu khi resolve conflict |
| **Photo perception** | Hiểu ảnh truy vấn: OCR + alarm-code/model detection + cảnh báo khi khó đọc |

### Ba bước digitise

**Bước 0 — phân loại.** `classify_figure` phân ảnh chart / diagram / photo / document qua ImageStats: pixel trắng, màu bão hoà, nền tối, trục dài, tỷ lệ số OCR. Nền tối → photo; trục + nền trắng > 50% + màu hoặc nhiều số → chart; ≥ 60 từ → document; còn lại → diagram; chỉ ảnh `chart` được digitise.

**Bước 1 — tìm hộp trục.** `_axes_geometry` binarise ảnh (pixel tối dưới 90), morphology opening với kernel ngang/dọc dài 30% để giữ đường thẳng dài. Hộp phải chiếm tối thiểu 25% chiều rộng, 20% chiều cao ảnh — không đạt là không digitise.

**Bước 2 — calibration trục.** Đét tick marks ngoài trục, OCR từng nhãn, fit `value = a·pixel + b`; điểm lệch quá 4% span bị loại rồi fit lại. Trục y bắt buộc slope âm; trục x cần ≥ 3 cặp tick, slope dương, RMS ≤ 0.02 — không đạt thì refuse.

**Bước 3 — tách series theo màu.** Pixel bão hoà (S > 90, V > 60) gom theo hue histogram (18 bin, bin ≥ 120 pixel, tối đa 4 series, merge bin kề bù anti-aliasing). Connected components ≥ 40 pixel: rộng-phẳng cùng đáy (lấp đầy ≥ 0.85, baseline lệch ≤ 4 pixel) là bar — đọc đỉnh cột; còn lại là line — trung bình y theo cột.

> ⚠️ **Refuse over guess:** fit kém, slope sai chiều, tick quá ít → trả `None`. Giá trị sai còn tệ hơn không có gì.

### Tick label: vote nhiều pass OCR

Một pass Tesseract đọc sai chuỗi ngắn với độ tin cậy cao: "50%" thành "90%" và không có dấu hiệu để biết. `figures.py` xử lý bằng vote: crop nhãn đọc qua 5 scale phóng (3.0, 4.0, 2.0, 5.0, 6.0) và 2 biến thể (raw + Otsu) — tối đa 10 pass; kết quả hợp lệ bỏ vào `Counter`, dừng sớm khi kết quả thắng rõ (≥ 4 phiếu, gấp ≥ 3 lần runner-up); hết pass chấp nhận khi có ≥ 2 phiếu.

Nhãn thiếu được `_repair_labels` tái dựng từ cấp số cộng (25%, 50%, 75%, 100%), chỉ sửa khi ≥ 3 nhãn đồng thuận. Confidence = 0.35 + 0.2·(số tick y) + 0.2·(1 − RMS) + 0.15·(có title) + 0.1·(có x-labels); dưới 0.55 bị vứt, cap 0.99.

### Bốn cách đọc biểu đồ

| Cách đọc | Đầu vào | Cho được gì | Không cho được gì |
| --- | --- | --- | --- |
| Caption | Text chú thích | Loại chart, chủ đề | Giá trị tại điểm bất kỳ |
| OCR toàn ảnh | Text nhãn trục | Tick values, tên trục | Đường cong — không có (x → y) |
| **Chart digitiser** | Pixel + OCR vote | Bộ (x → y), interpolation tại điểm hỏi | Precision tuyệt đối — sai số ± vài % |
| Vision LLM | Ảnh + prompt | Mô tả xu hướng linh hoạt | Numeric-exact, reproducible, offline |

Bốn cách không thay thế nhau: caption và OCR cho ngữ cảnh, digitiser cho số kiểm soát sai số, Vision LLM cho mô tả tự do, kết quả vào fact index.

### Giá trị approximate: không được phép đè số chính xác

Chart digitised được convert thành **approximate facts** (`approximate: true`): mỗi điểm (x → y) một fact, gắn chunk và model. Câu hỏi *What is the HX-500 specific power at 50% load?* được trả lời — fact channel tìm fact HX-500 chủ đề specific power, rồi `interpolate_series` nội suy tại 50% giữa hai mốc gần nhất.

Nhưng cờ approximate quyết định ranh giới quan trọng hơn. Trong `resolve_conflicts` của `index/facts.py`, chỉ **exact facts** thi đấu: revised thắng previous, bulletin thắng manual, date mới nhất thắng; thua cuộc báo thành ConflictNote. Approximate facts không bao giờ tham gia — comment trong code: *they are evidence, not specifications*.

Vì sao? Sai số đọc ảnh là vô tránh; sai số bảng spec là 0. Cho approximate trả lời câu hỏi — không cho nó đè số manual.

### Visual descriptor và photo perception

Photo alarm panel, data plate không có trục — không digitise được nhưng vẫn cần tìm lại. `visual_descriptor` tạo vector 264 chiều: HSV histogram 8×3×3 = 72 bin (0.5), gradient grid 4×4×8 = 128 (1.0), ink-layout 8×8 = 64 (0.8); letterbox 256×256, sqrt-normalised rồi L2-normalise — robust với resize, nhiễu nhẹ, JPEG artefact.

Khi upload ảnh truy vấn, `retrieval/perception.py` OCR, trích alarm code và model name, tính descriptor. Descriptor vào kênh retrieval `visual`: cosine với index visual, top 10 score ≥ 0.5 — photo data plate tìm lại đúng trang chứa figure.

Photo perception còn biết nó đọc không được: OCR thiếu → "only visual similarity can be used"; rỗng → "relying on visual similarity only"; confidence < 55% → cảnh báo *Verify the alarm code*.

```python
"""Hai khối nhỏ của chart digitiser: interpolation và tick-label voting."""
from collections import Counter


def interpolate_value(x, points):
    """Nội suy tuyến tính trên danh sách (x, y); None khi x ngoài khoảng đã digitise."""
    pts = sorted((float(px), float(py)) for px, py in points)
    if len(pts) < 2 or x < pts[0][0] - 1e-9 or x > pts[-1][0] + 1e-9:
        return None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


def vote_tick_labels(reads):
    """Chọn nhãn tick xuất hiện nhiều nhất qua nhiều pass OCR.

    Một pass Tesseract đọc sai chuỗi ngắn với độ tin cậy cao (50% -> 90%);
    vote qua nhiều pass khôi phục chúng. Dừng sớm khi một kết quả thắng rõ
    (>= 4 phiếu và >= 3 lần runner-up); cuối cùng yêu cầu >= 2 phiếu.
    """
    votes = Counter(r.strip() for r in reads if r and r.strip())
    if not votes:
        return None
    (top, c1), *rest = votes.most_common(2)
    if c1 >= 4 and (not rest or c1 >= 3 * rest[0][1]):
        return top
    return top if c1 >= 2 else None


if __name__ == "__main__":
    # Đường cong specific power digitised từ chart HX-500 (load % -> kW/kg)
    curve = [(20, 3.1), (40, 4.6), (60, 6.0), (80, 7.2), (100, 8.0)]
    value = interpolate_value(50, curve)
    print(f"HX-500 specific power @ 50% load = {value:.2f} kW/kg")

    # 7 pass OCR trên cùng một tick label: 4 lần đọc 50, 2 lần 90, 1 lần rỗng
    print("tick label cuối cùng:", vote_tick_labels(["50", "50", "90", "50", "90", "50", ""]))

    assert interpolate_value(50, curve) == (4.6 + 6.0) / 2      # 5.3
    assert interpolate_value(150, curve) is None                # ngoài range
    assert vote_tick_labels(["50", "50", "50", "50"]) == "50"   # thắng sớm rõ ràng
    assert vote_tick_labels(["x", "y"]) is None                 # không đủ 2 phiếu
    print("OK")
```

### Bài tập

**Làm theo:** Copy code block vào `digitiser.py`, chạy. Thử `interpolate_value(0, curve)` và `interpolate_value(150, curve)` — ngoài range trả `None`.

**Tự sửa:** Thêm nhiễu vào tick-label reads (ví dụ `["50", "5O", "90", "50", "50", "90"]` — chữ O thay số 0), sửa dừng sớm thành `c1 >= 3`: case `["50", "90", "50", "90", "50"]` có đổi kết quả không?

**Mở rộng:** Viết `repair_arithmetic(labels)` mô phỏng `_repair_labels`: tìm cấp số cộng có ≥ 3 nhãn đồng thuận, tái dựng cả dãy, giữ `%` khi đa số nhãn gốc có.

### Lỗi thường gặp

| Biểu hiện | Nguyên nhân | Xử lý |
| --- | --- | --- |
| Digitiser trả `None` dù ảnh rõ là chart | Không tìm thấy hộp trục hoặc confidence < 0.55 | Tăng độ phân giải, trục đủ dài, nền trắng; xem từng thành phần confidence |
| Tick label đọc sai (50% thành 90%) | Một pass OCR không đáng tin | Vote nhiều scale + Otsu; repair chỉ sửa khi ≥ 3 nhãn đồng thuận |
| Giá trị chart đè số trong manual | Approximate fact lọt vào conflict resolution | Giữ `approximate: true`; conflict chỉ xét exact facts |
| Ảnh photo truy vấn đọc không được | OCR confidence thấp | Cảnh báo verify; fallback sang visual descriptor |
| Line chart cho số vô nghĩa | Trục x chưa calibration (dưới 3 cặp tick) | Refuse: trả `None`, không interpolate |

### FAQ

**Tại sao caption không đủ cho câu hỏi giá trị từ biểu đồ?**
Caption chỉ mô tả loại và chủ đề (curve of head vs flow), không chứa giá trị số. Hỏi giá trị tại 70 m³/h cần bộ số (x → y) — số chỉ nằm trong pixel của đường cong, nên phải digitiser đọc từ ảnh.

**Vì sao tick label phải vote nhiều pass OCR thay vì đọc một lần?**
Tesseract một pass đọc sai chuỗi ngắn với độ tin cậy cao (50% thành 90%). Digitiser vote qua 5 scale + 2 biến thể nhị phân bằng Counter — dừng sớm khi kết quả thắng rõ, cuối cùng yêu cầu ≥ 2 phiếu.

**Giá trị đọc từ chart có được dùng để trả lời câu hỏi spec không?**
Có, nhưng chỉ làm evidence: gắn `approximate: true`, tham gia fact retrieval và interpolation, nhưng bị loại khỏi conflict resolution — không đè số chính xác trong manual hay bulletin.

**Ảnh truy vấn không phải biểu đồ (photo data plate) thì xử lý thế nào?**
Dùng visual descriptor (HSV + HOG-like + ink-layout, 264 chiều) cho image-to-figure retrieval, kết hợp OCR và alarm-code/model detection. Confidence dưới 55% → cảnh báo verify mã trên thiết bị, không trình bày như chắc chắn.

### Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — README và [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md)
- Code: `meridian/ingest/figures.py` (digitiser, visual descriptor), `meridian/retrieval/perception.py`, `meridian/index/facts.py` (approximate)
- Bài liền kề: Ingest PDF, bảng biểu và trang scan · 8 kênh hybrid retrieval · Fact index và conflict resolution
- Từ blog cũ: [Multimodal RAG cho PDF tiếng Việt](/bai-viet/rag-nang-cao-cam-nang/) — nền Vision QA cho biểu đồ

---

04. 8 kênh hybrid retrieval: từ BM25 đến graph — hợp nhất bằng weighted RRF — ≈10 phút

Một vector search không đủ cho corpus bảo trì công nghiệp. Câu hỏi *What torque for the HX-200 impeller bolt?* cần khớp chính xác "HX-200" — dense retrieval bỏ sót số hiệu. Câu hỏi paraphrase *bơm quá nhiệt xử lý thế nào?* cần hiểu ngữ nghĩa — BM25 trượt nếu corpus dùng từ khác. Ảnh chụp panel có OCR typo "E4T" thay "E47" — cả hai đều trượt. Không có một kênh nào thắng mọi loại lỗi.

Vì vậy Meridian chạy **8 kênh song song**, hợp nhất bằng weighted RRF, rerank theo late interaction + 17 features, rồi MMR. Benchmark cho thấy full pipeline đạt **Hit@1 89.5%** trên held-out, BM25 alone 84.2%. Bài này đi qua từng kênh — nó giải quyết lỗi gì — với hằng số thật từ `retrieval/pipeline.py`.

### Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **BM25 field-boosted** | Lexical retrieval tự viết, boost title/section/content/entities |
| **LSA dense** | Embedding offline: TF-IDF → SVD, không cần model download |
| **Weighted RRF** | Reciprocal Rank Fusion có trọng số per-channel: chỉ dùng rank, bỏ score gốc |
| **Late interaction / MaxSim** | Rerank kiểu ColBERT: mỗi query token khớp token tốt nhất trong chunk |
| **MMR** | Maximal Marginal Relevance — khử near-duplicate sau khi xếp hạng |
| **Model filtering** | Mask document level theo model trong câu hỏi — không cho passage sai model lọt qua |

### 8 kênh — mỗi kênh bù một loại lỗi

| Kênh | Trọng số | Làm gì | Giải quyết lỗi gì của kênh khác |
| --- | --- | --- | --- |
| **bm25** | 1.0 | Lexical field-boosted title/section/content/entities | Paraphrase của dense bỏ sót thuật ngữ chính xác |
| **dense** | 0.55 | LSA word+char n-grams, TF-IDF → SVD | Từ khoá của BM25 không hiểu "quá nhiệt" ↔ "overheating" |
| **char** | 0.30 | char-n-gram TF-IDF | OCR typo: "E4T" vẫn match "E47" nhờ chuỗi ký tự con |
| **entity** | 0.9 | Exact match alarm code / model từ query analysis | Model confusion — HX-500 khác HX-200; code hit trong TABLE bị nhân 0.6 |
| **fact** | 1.0 | Structured value search trên typed (value, unit) facts, min_score 0.45 | Câu hỏi số liệu mà BM25 không hit từ khoá |
| **visual** | 1.0 | HSV + HOG-like + ink-layout descriptor cho ảnh truy vấn, top 10 score ≥ 0.5 | Câu hỏi bằng ảnh — photo panel tìm lại figure/page |
| **prf** | 0.45 | RM3-style pseudo-relevance feedback từ top-3 BM25 | Query ngắn thiếu thuật ngữ — thêm 6 terms weight 0.25 rồi rescore |
| **graph** | 0.5 | Personalized PageRank từ top-6 RRF seeds qua edges mention/row-of/adjacent/warns/refers-to | Context mà lexical miss: hàng bảng liền kề, cảnh báo cùng section |

Hai kênh cần chú ý cách chúng giới hạn chính mình. **PRF** chỉ nhận terms chưa có trong query, bỏ terms số và terms ≤ 2 ký tự. **Graph** chạy sau RRF: 6 chunk điểm cao nhất làm seeds, lan truyền qua knowledge graph, kéo về tối đa pool/2 = 30 chunk; chunk chỉ vào được nhờ graph được gắn `via="graph"`. Seed sai thì lan truyền sai — lý do weight graph chỉ 0.5.

### Fusion: weighted RRF → rerank → MMR

Mỗi kênh trả top **pool = 60**. Weighted RRF hợp nhất:

$$\text{RRF}(d) = \sum_{c} \frac{w_c}{k + \text{rank}_c(d)}, \quad k = 60$$

Chunk được nhiều kênh đồng thuận có lợi thế cấu trúc: hạng 3 ở 4 kênh thường thắng hạng 1 ở 1 kênh. Top **40** vào rerank theo ba tầng:

1. **Late interaction (MaxSim):** mỗi query token khớp token tốt nhất trong chunk — exact stem match 1.0, fuzzy match (cutoff 0.86) 0.75, cosine trên LSA term vectors scale `((cos − 0.55) / 0.45) · 0.7`; tổng hợp theo IDF weight. Matching fine-grained kiểu ColBERT mà hoàn toàn offline.
2. **Feature ranker 17 features:** ghép score từng kênh với tín hiệu cấu trúc. Default weights hand-tuned: `rrf 0.30, late 0.28, fact 0.18, bm25 0.15, entity 0.14, modality 0.14, q_cov 0.12, visual 0.12, dense 0.10, section_overlap 0.08, graph 0.05, model_match 0.06, char 0.04, prf 0.03, is_bulletin 0.02`, còn `is_row`, `is_warning` = 0. Learned logistic-regression ranker train qua `scripts/run_eval.py` nhưng **chỉ được adopt khi thắng default trên held-out** — trong benchmark nó không thắng.
3. **MMR λ = 0.82:** chỉ phạt near-duplicate cùng modality cùng document (cosine > 0.88) — giữ diversity khi bảng n chữ số đưa ra 30 hàng giống nhau.

> **Định nghĩa:** Weighted RRF tổng đóng góp theo vị trí — `w/(k+rank)` — không phải tổng score; hợp nhất được 8 kênh có thang đo không tương thích mà không cần chuẩn hoá.

### Model filtering: điều kiện cứng ở document level

Trước cả fusion: khi query analysis nhận diện model (HX-500), retrieval áp mask **ở document level** — chunk thuộc document của model khác bị loại khỏi mọi kênh. Passage HX-500 không bao giờ được trả lời câu hỏi HX-200, dù từ ngữ giống nhau đến mức nào.

Filter là điều kiện cứng: chunk "gần đúng" của model sai vẫn bị loại dù score cao. Nếu retrieval trả passage HX-500 với torque 52 Nm cho câu hỏi về HX-200 (spec 45 Nm), phần verify sửa được câu chữ nhưng không sửa được sai số liệu đã vào context.

### Ablation: hybrid thêm nhiều nhưng không phải ma thuật

Benchmark synthetic đi kèm repo: 93 câu hỏi, 43 held-out. Trên held-out:

| Cấu hình | Hit@1 | Hit@5 | MRR |
| --- | --- | --- | --- |
| BM25 alone | 84.2% | 97.4% | — |
| **Full pipeline (8 kênh + rerank + MMR)** | **89.5%** | **100%** | **0.88** |

Đọc đúng số: full pipeline chỉ hơn BM25 alone **+5.3 điểm Hit@1**. Kênh bổ sung không phải phép màu — phần lớn chất lượng đến từ lớp sau retrieval: CRAG grader, conflict resolution, verifier, abstention (100% declined unanswerable, faithfulness 100%).

Repo kèm sẵn **ablation preset** — `bm25`, `dense`, `hybrid_rrf`, `hybrid+entity+fact`, `+prf+graph`, `+late_rerank`, `full` — mỗi preset bật tắt một nhóm kênh; đo per-config thay vì đoán.

Chủ đề RRF này blog cũ đã có bài riêng: [Hybrid Search với BM25, Dense Retrieval và RRF](/bai-viet/rag-nang-cao-cam-nang/) — cùng công thức k=60 SIGIR 2009, nhưng chưa weighted per-channel và chưa có rerank phía sau.

```python
"""Weighted RRF thuần Python — khối hợp nhất giữa 8 kênh retrieval."""
from collections import defaultdict


def weighted_reciprocal_rank_fusion(rankings, weights, k=60):
    """rankings: dict kênh -> danh sách id theo thứ hạng; weights: dict kênh -> trọng số.

    score(d) = sum_k w_k / (k + rank_k(d)). Trả về danh sách id theo điểm giảm dần,
    tie-break theo id để kết quả xác định khi debug và benchmark.
    """
    if k < 1:
        raise ValueError("k phải >= 1")
    scores = defaultdict(float)
    for name, ranked in rankings.items():
        w = weights.get(name, 1.0)
        for rank, doc_id in enumerate(ranked, 1):
            scores[doc_id] += w / (k + rank)
    return sorted(scores, key=lambda d: (-scores[d], d))


if __name__ == "__main__":
    rankings = {
        "bm25":   ["hx500_power_row", "hx500_chart", "manual_intro"],
        "dense":  ["hx500_chart", "hx500_power_row"],
        "char":   ["hx500_power_row"],
        "entity": ["hx500_power_row"],
    }
    weights = {"bm25": 1.0, "dense": 0.55, "char": 0.30, "entity": 0.9}
    fused = weighted_reciprocal_rank_fusion(rankings, weights, k=60)
    print(fused)

    # Đối chiếu tay: hx500_power_row = 1.0/61 + 0.55/62 + 0.30/61 + 0.9/61
    #               hx500_chart    = 1.0/63 + 0.55/61
    scores = {
        "hx500_power_row": 1.0 / 61 + 0.55 / 62 + 0.30 / 61 + 0.9 / 61,
        "hx500_chart":     1.0 / 63 + 0.55 / 61,
    }
    assert fused[0] == "hx500_power_row"
    print(f"row={scores['hx500_power_row']:.5f}  chart={scores['hx500_chart']:.5f}")

    # Đồng thuận 2 kênh thắng kênh duy nhất — trực giác quan trọng nhất của RRF
    r = {"a": ["doc_x", "doc_y"], "b": ["doc_x", "doc_z"]}
    assert weighted_reciprocal_rank_fusion(r, {"a": 1.0, "b": 1.0})[0] == "doc_x"
    print("OK")
```

### Bài tập

**Làm theo:** Chạy code block, đối chiếu tay từng score trong comment. Đổi `k=60` thành `k=1` rồi `k=100`: k=1 cho hạng 1 áp đảo hoàn toàn; k lớn làm các hạng gần nhau hơn.

**Tự sửa:** Thêm kênh `fact` (weight 1.0) và `graph` (0.5) như Meridian; cho `hx500_chart` đứng hạng 1 ở `fact`. Tính tay score ba chunk, đối chiếu output, rồi trả lời: nâng weight kênh nào sẽ đưa `hx500_chart` lên hạng 1?

**Mở rộng:** Implement mini late-interaction: mỗi query token score exact match 1.0 / fuzzy (`difflib.get_close_matches`, cutoff 0.86) 0.75 / miss 0.0, cộng theo IDF weight. Ghép vào feature dict cùng RRF score và tính linear score với default weights — phiên bản thu gọn của tầng rerank trong `rerank.py`.

### Lỗi thường gặp

| Biểu hiện | Nguyên nhân | Xử lý |
| --- | --- | --- |
| Kết quả đổi khi bật/tắt kênh, không biết kênh nào gây nhiễu | Thay nhiều biến cùng lúc | Dùng ablation preset và đo per-config trên cùng bộ câu hỏi có ground truth |
| Chunk đúng nhưng model sai được trả về | Model filtering chưa bật hoặc query analysis không nhận diện model | Bật `model_filter` để mask document level; kiểm tra `analysis.models` trước |
| PRF làm kết quả trôi topic | Expansion terms quá nhiều hoặc trùng terms đã có | Giữ 6 terms, weight 0.25, loại terms đã có trong query và terms số — như pipeline.py làm |
| Rerank chậm trên corpus lớn | Late interaction chạy trên depth lớn | Giảm `rerank_depth` (40) trước khi giảm kênh — fusion RRF rẻ, rerank tốn |
| Learned ranker "tốt hơn" trên train nhưng tụt trên held-out | Overfit | Chỉ adopt khi thắng default trên held-out — Meridian train rồi vẫn không adopt |

### FAQ

**Vì sao RRF bỏ qua score gốc của từng kênh?**
BM25 score, cosine LSA và fact score không cùng thang đo — cộng trực tiếp sẽ làm một kênh lấn át. RRF chỉ dùng rank: mỗi chunk nhận `w_k/(60+rank_k)` từ mỗi kênh; chunk được nhiều kênh đồng thuận nhảy lên đầu, bất kể thang đo gốc.

**Trọng số 8 kênh chọn thế nào?**
Hand-tuned: bm25 1.0, fact 1.0, visual 1.0, entity 0.9, dense 0.55, graph 0.5, prf 0.45, char 0.30. Nguyên tắc: kênh chính xác cao (exact match code, fact có unit) nặng hơn kênh mềm. Learned LTR chỉ được adopt khi thắng default trên held-out — trong benchmark nó không thắng nên giữ weights tay.

**17 features của feature ranker gồm gì?**
rrf, bm25, dense, char, late, entity, fact, modality, model_match, q_cov, section_overlap, is_row, is_warning, is_bulletin, graph, visual, prf — kết hợp score từng kênh với tín hiệu cấu trúc: modality prior theo intent, chunk là table row hay warning hay bulletin.

**Hybrid retrieval có phải ma thuật không?**
Không. Trên benchmark 43 câu held-out, full pipeline đạt Hit@1 89.5% so với BM25 alone 84.2% (+5.3 điểm) và Hit@5 đều đạt 100%. Phần giá trị lớn còn lại nằm ở grader, verifier và abstention — retrieval chỉ là một lớp.

### Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — README (Measured results) và [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) mục 4
- Code: `meridian/retrieval/pipeline.py` (8 kênh, weighted RRF, MMR), `meridian/retrieval/rerank.py` (late interaction, 17 features)
- Bài liền kề trong series: Chart digitiser đọc số liệu từ biểu đồ · Fact index và conflict resolution · CRAG grader và abstention
- Từ blog cũ: [Hybrid Search với BM25, Dense Retrieval và RRF](/bai-viet/rag-nang-cao-cam-nang/) — cùng chủ đề RRF

---

05. Fact index và conflict resolution: khi manual và bulletin nói khác nhau — ≈11 phút

Hỏi "What torque should I use for the HX-200 impeller bolt?" và nhận câu trả lời nghe rất chắc: 45 Nm. Hoặc 52 Nm — tùy lúc chạy. Corpus của Meridian chứa cả hai số này: Maintenance Manual ghi 45 Nm, Service Bulletin SB-118 revision mới hơn ghi 52 Nm. Khi cả hai chunk cùng rơi vào top-k, RAG text trộn lẫn chúng hoặc chọn ngẫu nhiên theo thứ tự chunk. Không ai nói cho bạn biết bulletin mới hơn; cũng không ai nói 45 Nm đã bị supersede. Với lệnh torque sai 7 Nm trên máy móc công nghiệp, đó không phải lỗi demo — đó là sự cố.

Meridian giải bằng một quyết định kiến trúc: fact index tách khỏi vector search. Bài này đi qua cấu trúc Fact, precedence rules của `resolve_conflicts`, `check_premise` bắt giả định sai, và nhóm tool tính chính xác đi kèm.

### Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Fact** | Bản ghi có cấu trúc `(model, subject, attribute, value, unit, provenance)` khai thác từ bảng biểu và chart đã digitise — không phải chunk văn bản |
| **Provenance** | Nguồn gốc của fact: doc_type (manual/bulletin), cờ `revised`/`previous`, effective date, chunk_id để trích dẫn trang gốc |
| **Conflict resolution** | Nhiều nguồn cho cùng `(model, subject, attribute)` nhưng khác giá trị — precedence rules chọn người thắng và giải thích người thua |
| **ConflictNote** | Đối tượng ghi giá trị thắng/thua, tên cả hai tài liệu, quy tắc áp dụng — hiển thị trong UI, không bao giờ âm thầm |
| **lookup_spec** | Tool tìm fact đúng câu hỏi yêu cầu, có attribute-aware scoring và companion lookup để không sót conflict |

### Vì sao fact index là tài sản hạng nhất

> "Facts as first-class index (model, subject, attribute, value, unit, provenance) — lets the system do exact lookup, unit conversion and conflict resolution — impossible from text chunks alone."
> — docs/ARCHITECTURE.md §3, bảng Decisions and why

Câu "impossible from text chunks alone" không phải rhetoric: exact lookup, unit conversion và conflict resolution đòi hỏi biết thuộc tính nào, của chủ thể nào, đơn vị nào, từ tài liệu nào — thông tin chỉ tồn tại khi parse giữ được cấu trúc.

| Tiêu chí | RAG trên text chunk | Fact index trong Meridian |
| --- | --- | --- |
| Trả lời "torque của HX-200?" | Chunk giống câu hỏi nhất theo cosine — có thể là hàng khác của bảng | Fact đúng `(HX-200, impeller bolt, torque)` kèm value + unit |
| Đơn vị | Trộn vào văn bản, LLM tự đoán | Trường `unit` riêng; so sánh theo unit dimension |
| Xung đột nguồn | Cả hai chunk vào context, LLM tự xử lý | Precedence rules quyết định, ConflictNote ghi lại |
| Yes/no premise | Evidence không đủ → trả lời theo cảm tính | check_premise: confirmed / refuted / superseded / unknown |
| Giá trị từ chart | Caption mô tả "curve of head vs flow" | Giá trị nội suy, luôn đánh dấu `approximate` |

Facts được khai thác ở khâu ingest (bài Ingest PDF, bảng biểu, scan: mỗi table row trở thành một chunk và một fact). `FactIndex` nhóm theo `group_key` — `(model, subject_tokens, attribute, unit_dimension)` — để mọi nguồn nói về cùng đại lượng vật lý nằm chung một nhóm; giá trị approximate từ chart không bao giờ vào nhóm.

### resolve_conflicts: precedence rules rõ ràng, người thua được báo cáo

`index/facts.py` áp precedence theo thứ tự cố định:

| Thứ tự | Quy tắc | Ví dụ |
| --- | --- | --- |
| 1 | Giá trị cột `revised` bỏ giá trị `previous` cùng hàng | Row ghi "45 (previous) → 52 (revised)": chỉ 52 cạnh tranh |
| 2 | Bulletin đè manual khi cùng ngày hiệu lực | SB-118 đè Maintenance Manual |
| 3 | Effective date mới nhất thắng | Bulletin 2025-03-01 thắng manual 2024-01-15 |

Ba chi tiết trong code đáng chú ý hơn bảng rules:

- **So sánh giá trị đi qua unit conversion và tolerance**: `quantities_match` với tolerance tương đối 1e-3 — hai nguồn cùng giá trị khác đơn vị (bar vs psi) không bị đếm nhầm là conflict.
- **Người thua không bị xóa**: mỗi nhóm sinh một `ConflictNote` gồm subject, model, giá trị thắng/thua, tên cả hai tài liệu, quy tắc áp dụng và chunk_id hai bên. UI hiển thị "45 Nm từ HX-200 Maintenance Manual đã bị SB-118 (52 Nm) thay thế". Không mất dữ liệu, không âm thầm.
- **Một nhóm chỉ sinh một note** — đủ giải thích, không tràn màn hình.

Kết quả cho câu hỏi demo là duy nhất và có giải thích: **52 Nm** kèm ConflictNote cho 45 Nm — deterministic, cùng input cho cùng output, không phụ thuộc mô hình ngôn ngữ nào.

### check_premise: bắt giả định sai trước khi trả lời

Câu hỏi "Is the HX-200 rated for fluid at 150 °C?" là yes/no question chứa premise "HX-200 có rating 150 °C cho fluid". Analyzer trích quantity `150 °C`; `lookup_spec` tìm fact theo unit dimension tương ứng. Không có evidence phù hợp → premise không được xác nhận → hệ thống refuse rõ ràng, không bịa một câu "yes" trơn tru. Đó là false premise detection: giả định sai phải bị bắt trước khi câu trả lời được viết, không phải sau.

`check_premise` trả về bốn verdict:

| Verdict | Điều kiện | Hành vi |
| --- | --- | --- |
| confirmed | Premise khớp giá trị đã resolve (tolerance ~0.3%) | Trả lời yes kèm nguồn |
| refuted | Có giá trị resolve nhưng khác premise | Từ chối premise, chỉ ra giá trị đúng |
| superseded | Premise khớp giá trị đã bị supersede | Giải thích: giá trị cũ từ manual, giá trị mới từ bulletin |
| unknown | Premise dùng đơn vị khác dimension với fact | Không xác nhận cũng không phủ định — refuse |

Chi tiết đáng học nhất là `superseded`: premise khớp giá trị cũ 45 Nm không bị phán "sai" — hệ thống trả lời bằng giá trị mới kèm giải thích nguồn cũ và mới. Người dùng giữ câu hỏi của mình nhưng được cập nhật thông tin.

### lookup_spec và nhóm tool tính chính xác

Fact index là nền; agent dùng qua các tool deterministic — không cái nào gọi LLM, không cái nào đánh giá code người dùng:

- **lookup_spec** — attribute-aware scoring: hỏi về "torque" thì fact torque được cộng điểm, fact interval trông giống nhau nhưng khác thuộc tính bị trừ điểm. Nó nạp companion facts cùng `group_key` để conflict không bị bỏ sót, và lọc theo rare terms — fact không nhắc đến "baseplate" không được trả lời câu hỏi về baseplate.
- **Safe pandas analytics** — "Which alarm code occurs most often?" không qua LLM tính số: tool map vào vetted operations (count, sum, mean, argmax), chạy trên DataFrame và hiển thị biểu thức thật (`df[filter].error_code.value_counts().head(5)`) kèm số dòng đã dùng — không expression tự do nào được đánh giá.
- **Unit conversion** — "torque in lb-ft" → giá trị chuyển sang đơn vị yêu cầu trước khi trả lời; 10 bar = 145 psi là phép tính.
- **Chart interpolation** — "What is the HX-500 specific power at 50% load?" đọc điểm từ đường curve đã digitise, nội suy tại x=50, đánh dấu `interpolated=True` khi x không trùng điểm đo.

Nhóm này giải quyết phần "số học do LLM": mỗi số trong câu trả lời đến từ một phép tính hoặc một fact có nguồn, không từ xác suất sinh token.

### Mini implementation: resolve_conflicts bằng stdlib

Đoạn sau giữ precedence của `index/facts.py` thu về stdlib — chạy offline, không dependency:

```python
"""Mini conflict resolver: manual vs bulletin vs effective date (stdlib only)."""
from collections import defaultdict


def group_key(f):
    return (f["model"], f["subject"], f["attribute"])


def same_value(a, b):
    # cùng đơn vị và gần nhau theo tolerance tương đối thì coi là cùng giá trị
    if a["unit"] != b["unit"]:
        return False
    return abs(a["value"] - b["value"]) <= 1e-3 * max(1.0, abs(a["value"]))


def rank(f):
    # precedence: cột revised > bulletin > manual, rồi ngày hiệu lực mới nhất
    return (1 if f["revised"] else 0, 1 if f["doc_type"] == "bulletin" else 0, f["effective_date"])


def resolve_conflicts(facts):
    groups = defaultdict(list)
    for f in facts:
        groups[group_key(f)].append(f)
    selected, notes = [], []
    for key, members in groups.items():
        if any(m["revised"] for m in members):
            members = [m for m in members if not m["previous"]]
        distinct = []
        for m in members:
            if not any(same_value(m, d) for d in distinct):
                distinct.append(m)
        if len(distinct) == 1:
            selected.append(max(members, key=rank))
            continue
        ranked = sorted(members, key=rank, reverse=True)
        winner = ranked[0]
        selected.append(winner)
        loser = ranked[1]
        rule = ("bulletin đè manual" if winner["doc_type"] == "bulletin" and loser["doc_type"] != "bulletin"
                else "ngày hiệu lực mới nhất thắng")
        notes.append({"subject": winner["subject"], "model": winner["model"],
                      "winner": winner["doc_title"], "loser": loser["doc_title"],
                      "winner_value": f"{winner['value']} {winner['unit']}",
                      "loser_value": f"{loser['value']} {loser['unit']}", "rule": rule})
    return selected, notes


facts = [
    {"model": "HX-200", "subject": "impeller bolt", "attribute": "torque",
     "value": 45, "unit": "Nm", "revised": False, "previous": False,
     "doc_type": "manual", "doc_title": "HX-200 Maintenance Manual", "effective_date": "2024-01-15"},
    {"model": "HX-200", "subject": "impeller bolt", "attribute": "torque",
     "value": 52, "unit": "Nm", "revised": True, "previous": False,
     "doc_type": "bulletin", "doc_title": "Service Bulletin SB-118", "effective_date": "2025-03-01"},
]
selected, notes = resolve_conflicts(facts)
assert selected[0]["value"] == 52, "bulletin revised phải thắng"
assert notes[0]["rule"] == "bulletin đè manual"
assert notes[0]["winner_value"] == "52 Nm" and notes[0]["loser_value"] == "45 Nm"

facts2 = [dict(facts[0]), dict(facts[1])]
facts2[0]["effective_date"] = "2025-03-01"
facts2[1]["revised"] = False
selected2, notes2 = resolve_conflicts(facts2)
assert selected2[0]["doc_type"] == "bulletin", "cùng ngày: bulletin đè manual"
print("OK —", selected2[0]["value"], selected2[0]["unit"], "| note:", notes2[0]["rule"])
```

### Bài tập

**Làm theo:** Chạy code block trên. Thêm fact thứ ba — manual cũ cho giá trị 48 Nm, effective date 2023 — và kiểm tra note vẫn chỉ sinh một bản cho nhóm.

**Tự sửa:** Thay `same_value` bằng so sánh theo unit dimension với bảng quy đổi (bar↔psi, Nm↔lb-ft): hai fact cùng giá trị khác đơn vị là đồng thuận, không phải conflict.

**Mở rộng:** Kết nối với bài 8 kênh hybrid retrieval: fact channel gọi `FactIndex.search` với IDF nội bộ. Viết wrapper nhận output retrieval của bạn, dựng fact giả lập rồi chạy `resolve_conflicts` trước khi compose — conflict resolution chạy trước generation, không phải sửa sau.

### Lỗi thường gặp

- **LLM trộn lẫn hai giá trị trong một câu trả lời** → cả manual và bulletin cùng vào context qua top-k → đặt fact index + `resolve_conflicts` trước khâu compose; kiểm tra ConflictNote có được render trong UI không — note bị nuốt thì người thua "mất" âm thầm.
- **Conflict được đếm nhầm khi hai nguồn ghi cùng giá trị khác đơn vị** → so sánh số thô thay vì đi qua unit conversion → so sánh theo unit dimension kèm tolerance như `quantities_match`.
- **Premise sai được trả lời "yes"** → analyzer không trích premise quantity hoặc lookup_spec không lọc theo unit dimension → bật trace của analyzer (intent yes/no, quantities) trước khi debug tool.
- **Giá trị chart nội suy lọt vào conflict resolution** → quên loại approximate → `resolve_conflicts` loại approx ngay từ đầu; giữ nhãn approximate khi hiển thị — chúng vẫn là evidence hợp lệ.
- **lookup_spec trả về fact của model khác** → model filtering chỉ áp ở retrieval mà không áp ở fact search → lọc theo models của câu hỏi ngay trong `FactIndex.search` — một chunk HX-500 không bao giờ trả lời câu hỏi HX-200.

### FAQ

**Fact index khác gì vector search?**
Vector search trả về chunk giống câu hỏi nhất theo cosine — xác suất. Fact index trả về giá trị đúng theo (model, subject, attribute) kèm unit, nên có thể làm exact lookup, unit conversion và conflict resolution — những việc chunk văn bản làm không được.

**Ai thắng khi manual và bulletin cho giá trị khác nhau?**
Thứ tự precedence: giá trị cột revised bỏ giá trị previous của cùng hàng; bulletin đè manual khi cùng ngày; ngày hiệu lực mới nhất thắng. Người thua không bị xóa — ghi thành ConflictNote hiển thị trong UI.

**Giá trị đọc từ biểu đồ có tham gia conflict resolution không?**
Không. Chart digitiser đánh dấu giá trị nội suy là approximate — evidence, không phải specification, nên bị loại khỏi mọi nhóm conflict. Chúng vẫn dùng để trả lời nhưng luôn kèm nhãn approximate.

**check_premise xử lý giả định sai thế nào?**
Câu 'Is the HX-200 rated for fluid at 150 °C?' chứa premise 150 °C nhưng corpus không có evidence phù hợp → refuted → refuse rõ ràng thay vì bịa câu trả lời. Nếu premise khớp giá trị superseded cũ, verdict là superseded kèm giải thích giá trị mới.

### Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) mục 3 (bảng Decisions) và mục 5 (Conflict resolution), kèm [docs/MODULES.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/MODULES.md)
- Code trong bài: `meridian/index/facts.py` (FactIndex, resolve_conflicts, ConflictNote), `meridian/agent/tools.py` (lookup_spec, check_premise, run_analytics, convert_fact, read_chart_values)
- Bài liền kề trong series: 8 kênh hybrid retrieval · CRAG grader và abstention · Ingest PDF, bảng biểu, scan

---

06. CRAG grader và abstention: trả lời 'không biết' là tính năng, không phải lỗi — ≈12 phút

RAG demo luôn trả lời — kể cả khi evidence không đủ. Hỏi "Who is the CEO of Helix Dynamics?" trên corpus tài liệu bảo trì: không có CEO nào, không có Helix Dynamics nào, nhưng demo thông thường vẫn sinh ra một câu trông mượt với số liệu bịa. Hallucination sinh ra từ đúng chỗ này: pipeline cho phép generation chạy dù evidence không hỗ trợ. Lỗi không nằm ở mô hình ngôn ngữ; nó nằm ở quyết định thiết kế.

Meridian đặt grader TRƯỚC generation: đánh giá evidence có đủ hỗ trợ câu hỏi hay không bằng phép tính rẻ, deterministic; không đủ thì retry, vẫn không đủ thì abstain. Trích từ bảng Decisions trong ARCHITECTURE:

> "Grader before generation — cheap, deterministic abstention is safer than asking a generator to 'say I don't know'."

### Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **CRAG** | Corrective RAG — chấm điểm evidence trước generation, sửa lỗi truy xuất rồi mới quyết định trả lời hay từ chối |
| **Grader verdict** | correct / ambiguous / incorrect — evidence đủ / mập mờ / không đủ hỗ trợ |
| **IDF coverage** | Tỷ lệ thuật ngữ câu hỏi được evidence hỗ trợ, có trọng số IDF — từ hiếm quan trọng hơn từ phổ biến |
| **OOV** | Out-of-vocabulary — thuật ngữ không có trong corpus; được xử lý theo anchor logic, không mặc định là tin xấu |
| **Anchor term** | Thuật ngữ cụ thể của câu hỏi được tìm thấy trong evidence — chứng tỏ câu hỏi "đậu" vào đúng chủ đề |
| **Brand-term exclusion** | Tên hệ thống, tên model, từ branding trong tiêu đề tài liệu không tính vào coverage — chúng nói không gì về chủ đề |
| **Abstention** | Từ chối trả lời có kiểm soát, kèm lý do hiển thị trong trace |

### Grader chấm điểm evidence trước khi viết câu trả lời

`retrieval/grader.py` lấy top 4 candidates của retrieval (bài 8 kênh hybrid retrieval đã đi qua pipeline đó) và tính ba tín hiệu:

1. **IDF-weighted query-term coverage** — mỗi thuật ngữ câu hỏi được gán trọng số IDF theo BM25 của corpus; coverage bằng tổng trọng số thuật ngữ có trong evidence chia tổng trọng số. Từ hiếm có trọng số lớn.
2. **Late-interaction score** — MaxSim kiểu ColBERT trên term vectors, lấy giá trị cao nhất trên top evidence.
3. **Fused score truy xuất** — final score của pipeline 8 kênh cho candidate tốt nhất.

Công thức kết hợp và ngưỡng:

`score = 0.55 × coverage + 0.25 × late + 0.20 × min(1, top_final)` — correct ≥ 0.62, ambiguous ≥ 0.40, thấp hơn là incorrect.

| Verdict | Ngưỡng score | Hành vi pipeline |
| --- | --- | --- |
| correct | ≥ 0.62 | Expand evidence, chạy tool, compose |
| ambiguous | 0.40–0.62 | Vẫn compose nhưng confidence thấp, trình bày thận trọng |
| incorrect | < 0.40 | Corrective retry → vẫn sai → ABSTAIN |

Ngoài coverage, grader phạt trực tiếp: alarm code trong câu hỏi không thấy trong top evidence thì score nhân 0.5 — một mã lỗi khớp là điều kiện cứng của câu hỏi troubleshoot.

### OOV handling và brand-term exclusion

Hai chi tiết của grader quyết định chất lượng abstention nhiều hơn mọi ngưỡng.

**OOV không mặc định là tin xấu.** Thuật ngữ không có trong corpus được gán trọng số của từ hiếm nhất (`log(1 + n)`) — kéo coverage xuống nặng. Nhưng có ngoại lệ: nếu câu hỏi có ít nhất một anchor term cụ thể được tìm thấy trong evidence, thuật ngữ OOV được coi như paraphrase và chỉ tính như một từ hiếm bình thường. Nếu không có anchor nào và phần trọng số OOV vượt 30% tổng, grader tuyên bố incorrect ngay với lý do hiển thị rõ: "key term(s) that appear in no indexed document".

**Brand terms không nói gì về chủ đề.** Thuật ngữ trùng với tiêu đề tài liệu (branding, document-type words) và token tên model đang hỏi bị loại khỏi tính coverage. Nếu không loại, câu hỏi "What is the HX-200 torque?" được điểm mượt chỉ vì evidence chứa chuỗi "HX-200" — một tín hiệu giả về độ đủ evidence. Danh sách từ GENERIC ("give", "tell", "need"...) cũng bị loại — không mang tín hiệu answerability.

### Corrective loop và unknown-model refuse

Verdict incorrect không kết thúc ngay — CRAG-style corrective loop:

1. Retry truy xuất với **relaxed model filter** — evidence đúng có thể nằm ở tài liệu bị model filter loại lần đầu.
2. Rewrite câu hỏi **keyword-only** — bỏ cấu trúc câu, giữ thuật ngữ discriminative.
3. Vẫn incorrect → **ABSTAIN** kèm lý do trong trace.

Trước grader còn một lối thoát sớm hơn: **unknown-model refuse**. Analyzer trích model/entity từ câu hỏi; nếu câu hỏi nhắc model không tồn tại trong corpus, pipeline refuse NGAY — không bao giờ trả lời thay cho sản phẩm khác. Đây là lý do demo "Who is the CEO of Helix Dynamics?" abstain: "Helix Dynamics" là một entity không có documentation nào, và trích thông tin về nó từ corpus sai chủ đề là hành vi nguy hiểm nhất của một hệ thống hỏi đáp — nguy hiểm hơn cả refuse.

### Evidence selection: theo cross-reference, gắn WARNING

Grader quyết định "trả lời hay không"; lớp evidence selection quyết định "đưa cái gì vào generation" (`retrieval/context.py`):

- **Follow cross-reference**: chunk ghi "see Table 4" — hệ thống theo tham chiếu tới đúng ROW của bảng đó trong index, không dừng ở câu nói "see Table 4". Composer nhận giá trị thật của hàng, không nhận lời hứa tham chiếu.
- **Attach WARNING chunks cùng section**: nếu chunk chứa câu trả lời thuộc cùng section với warning box, warning được gắn vào context. Câu trả lời kỹ thuật không bao giờ thiếu cảnh báo an toàn chỉ vì warning nằm ở một chunk khác.

Hai cơ chế này trả lời câu hỏi mà top-k thuần không trả lời được: evidence đưa vào generation có phản ánh đúng nghĩa tài liệu gốc, hay chỉ phản ánh thứ tự rank của retrieval.

### Benchmark: cân bằng refuse và false abstention

Từ chối là con dao hai lưỡi — refuse quá nhiều là hệ thống vô dụng. Số liệu đo được:

| Chỉ số | Benchmark chính (93 câu) | Stress set (100 notes, 700 câu) |
| --- | --- | --- |
| Unanswerable declined | 100% | 100% |
| False abstention trên answerable | 1.1% | 10.0% |
| Answer correctness (unit-aware) | 93.1% overall, 92.5% held-out | 90.0% (held-out theo model) |

Stress set false abstention 10% cho thấy chi phí của ngưỡng hand-tuned khi corpus lớn và wording noise tăng. Hướng đối chiếu vẫn rõ: 100% unanswerable decline + faithfulness 100% claims supported là ưu tiên của hệ thống bảo trì công nghiệp — sai số nằm ở câu trả lời có kiểm soát, không ở câu bịa.

### Mini implementation: idf_coverage_grader

Sketch giữ đúng ý chính của `grader.py` — IDF coverage, OOV/anchor logic, brand exclusion — thu về stdlib:

```python
"""Grader IDF coverage: OOV handling, anchor logic, brand exclusion (stdlib only)."""
import math

THRESH_CORRECT, THRESH_AMBIGUOUS = 0.62, 0.40
GENERIC = {"give", "tell", "need", "use", "much", "many", "correct", "right"}
BRAND = {"hx", "meridian"}  # tên hệ thống/tài liệu không tính vào coverage


def idf_of(df_count, n_docs):
    return math.log(1.0 + (n_docs - df_count + 0.5) / (df_count + 0.5))


def oov_weight(n_docs):
    # từ ngoài vocabulary là từ hiếm nhất
    return math.log(1.0 + n_docs)


def build_index(chunks):
    n = len(chunks)
    df = {}
    for doc in chunks:
        for t in set(doc):
            df[t] = df.get(t, 0) + 1
    return n, df


def idf_coverage_grader(query_terms, evidence_chunks, n_docs, df):
    q = [t for t in dict.fromkeys(query_terms) if t not in GENERIC and t not in BRAND]
    covered = set()
    for doc in evidence_chunks:
        covered |= set(doc)
    anchored = any(t in covered for t in q)  # ít nhất một thuật ngữ cụ thể được tìm thấy
    total_w = got_w = 0.0
    missing = []
    for t in q:
        if t in df:
            w = idf_of(df[t], n_docs)
        else:
            w = idf_of(0.25 * n_docs, n_docs) if anchored else oov_weight(n_docs)
        total_w += w
        if t in covered:
            got_w += w
        else:
            missing.append(t)
    coverage = got_w / total_w if total_w else 0.5
    oov = [t for t in missing if t not in df]
    if oov and not anchored:
        oov_share = sum(oov_weight(n_docs) for _ in oov) / total_w
        if oov_share >= 0.3:
            return "incorrect", coverage, [f"key terms in no indexed document: {', '.join(oov)}"]
    # fused score: coverage 0.55 + late interaction 0.25 + retrieval score 0.20
    score = 0.55 * coverage + 0.25 * 0.8 + 0.20 * 0.9
    label = "correct" if score >= THRESH_CORRECT else "ambiguous" if score >= THRESH_AMBIGUOUS else "incorrect"
    reasons = ["no support in evidence: " + ", ".join(missing)] if missing else []
    return label, coverage, reasons


chunks_corpus = [
    ["hx-200", "impeller", "bolt", "torque", "52", "nm", "bulletin"],
    ["hx-200", "maintenance", "manual", "lubrication", "grease", "interval"],
    ["hx-500", "specific", "power", "chart", "curve", "head", "flow"],
    ["hx-500", "alarm", "e-47", "low", "suction", "pressure"],
]
n_docs, df = build_index(chunks_corpus)

label, cov, why = idf_coverage_grader(["torque", "impeller", "bolt", "hx-200"], chunks_corpus[:1], n_docs, df)
assert label == "correct" and cov >= 0.75, (label, cov, why)

# 2. hỏi về Helix Dynamics — không anchor, OOV chiếm >30% → incorrect
label2, cov2, why2 = idf_coverage_grader(["ceo", "helix", "dynamics"], chunks_corpus, n_docs, df)
assert label2 == "incorrect", (label2, why2)

# 3. paraphrase: "greasing" là OOV nhưng câu hỏi anchored → không chết vì OOV
label3, cov3, why3 = idf_coverage_grader(["greasing", "interval", "hx-200"], chunks_corpus[1:2], n_docs, df)
assert label3 in ("ambiguous", "correct"), (label3, why3)
print("OK —", label, round(cov, 2), "|", label2, "|", label3, round(cov3, 2))
```

### Bài tập

**Làm theo:** Chạy code block trên và đoán giá trị coverage trước khi xem output. Thay evidence của case 1 bằng `chunks_corpus[1:2]` (chunk lubrication) — coverage giảm thế nào, verdict đổi thành gì, và thuật ngữ nào xuất hiện trong `missing`.

**Tự sửa:** Thêm cấu trúc evidence để simulate brand-term exclusion: đọc tiêu đề tài liệu từ trường riêng của mỗi chunk và loại thuật ngữ trùng tiêu đề khỏi danh sách tính coverage thay vì dùng hằng số BRAND.

**Mở rộng:** Viết corrective loop: hàm nhận verdict incorrect, thực hiện một lần retry với rewritten query (bỏ stop words, giữ thuật ngữ IDF cao nhất) rồi gọi lại grader; cap hai vòng — vẫn incorrect thì trả về ABSTAIN kèm lý do. Nối với bài Fact index và conflict resolution để retry dùng fact channel trước khi fallback keyword-only.

### Lỗi thường gặp

- **Hệ thống abstain quá nhiều** → ngưỡng 0.62 đặt cho corpus có IDF floor cao hoặc evidence depth thấp → đo false abstention trên tập answerable của bạn, hạ THRESH_CORRECT hoặc tăng depth evidence trước khi đổi threshold.
- **OOV từ hiếm kéo coverage chết dù câu hỏi hợp lệ** → thiếu anchor logic → kiểm tra `anchored` có được tính trên thuật ngữ cụ thể (không phải GENERIC) hay không; paraphrase hợp lệ phải được nới lỏng như case 3 trong code.
- **Coverage mượt vì brand term** → chưa loại title_terms và token tên model → câu hỏi nhắc tên model được điểm cao từ tín hiệu giả; loại theo tiêu đề tài liệu, không theo hằng số cứng.
- **Câu trả lời thiếu cảnh báo an toàn** → evidence chỉ lấy top-k thuần → bật cross-reference following và warning expansion cùng section như `retrieval/context.py`; kiểm tra trong trace xem WARNING chunk có được attach không.
- **Retry vô hạn khi evidence trượt bền bỉ** → corrective loop không có cap → cap số vòng (relaxed filter rồi keyword rewrite rồi abstain); mỗi vòng retry phải ghi lý do vào trace để không restart ngầm.

### FAQ

**Vì sao grader đặt trước generation thay vì sau?**
Vì hallucination sinh ra khi generation chạy dù evidence không đủ. Grader rẻ, deterministic, chấm evidence trước — không đủ thì abstain; chi phí bỏ một câu trả lời nhỏ hơn nhiều chi phí một câu bịa. Chấm sau generation thì sai sót đã lọt qua composer.

**Từ khóa không có trong corpus bị xử lý thế nào?**
OOV được tính là từ hiếm nhất (log(1+n)) — kéo coverage xuống nặng. Nhưng nếu câu hỏi có anchor term cụ thể tìm thấy trong evidence, OOV coi như paraphrase và chỉ tính như từ hiếm bình thường; không anchor và OOV chiếm ≥30% trọng số → incorrect ngay.

**Vì sao 'Who is the CEO of Helix Dynamics?' bị từ chối?**
Analyzer trích entity 'Helix Dynamics' không có trong corpus — unknown-model refuse kích hoạt trước khi retrieval chạy. Trích thông tin về sản phẩm hay tổ chức không có documentation là hành vi nguy hiểm nhất của hệ thống hỏi đáp, nên pipeline refuse ngay thay vì trả lời thay.

**Abstention 10% trên stress set có quá nhiều không?**
Phụ thuộc nghiệp vụ. 100% unanswerable decline và faithfulness 100% là ưu tiên của hệ thống bảo trì công nghiệp; false abstention 10% trên corpus stress 700 câu có wording noise là chi phí của ngưỡng hand-tuned. Giám sát cả hai hướng và chỉnh ngưỡng theo tập answerable thực tế của bạn.

### Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) mục 2 (corrective retries trong flow diagram) và mục 5 (Grader); README bảng "Why it is different" và Measured results
- Code trong bài: `meridian/retrieval/grader.py` (grade, GENERIC, OOV/anchor logic, brand-term exclusion), `meridian/retrieval/context.py` (cross-reference following, warning expansion), `meridian/agent/agent.py` (corrective loop, unknown-model refuse)
- Bài liền kề trong series: Fact index và conflict resolution · Claim verifier bắt hallucination
- Từ blog cũ: [Đánh giá chất lượng RAG với Ragas](/bai-viet/rag-nang-cao-cam-nang/) — grader trong bài là đánh giá đặt trong pipeline trước generation; Ragas đánh giá sau khi hệ thống đã trả lời

---

07. Claim-level verifier: chặn hallucination trước khi câu trả lời ra tới người dùng — ≈13 phút

RAG demo đo chất lượng bằng "câu trả lời có mượt không". Nhưng hallucination không phải lỗi tổng thể của câu trả lời — nó lẩn vào từng claim: một con số sai, một mã lỗi không tồn tại, một câu phủ định evidence chưa bao giờ nói. Câu trả lời 90% đúng với 10% bịa nguy hiểm hơn câu từ chối. Bài trước chặn generation chạy khi evidence không đủ; bài này xử lý phần còn lại: kiểm từng claim trước khi ra tới người dùng.

Quyết định kiến trúc nằm ngay trong bảng Decisions của ARCHITECTURE.md:

> "Verifier is separate from the generator — same checks guard the offline composer and any LLM. Independent of what writes the text."

Bộ check viết **một lần**, bảo vệ **mọi nguồn sinh văn bản** — composer offline extractive lẫn LLM Anthropic/OpenAI/Ollama. Verifier không quan tâm ai viết câu trả lời, chỉ quan tâm câu trả lời có bám evidence hay không. Chất lượng trust vì thế không bị rewrite mỗi lần đổi generator hay nâng cấp model — trust layer sống ở chỗ không có model nào trong pipeline.

### Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Claim** | Từng câu/bullet atom của câu trả lời — verifier chấm từng claim, không chấm cả đoạn |
| **Verifier** | Bộ kiểm deterministic, không LLM — đối chiếu từng claim với evidence được cite |
| **Verdict** | supported / partial / unsupported / contradicted — bốn mức của một claim |
| **Unit-aware check** | So số theo kích thước vật lý: 10 bar = 145 psi là khớp, không phải khác |
| **Repair** | Drop câu claim không được support — xóa, không sửa lại câu |
| **CiteBook** | Sổ citation của composer: gán [n] theo thứ tự xuất hiện đầu tiên của evidence |
| **Faithfulness** | Tỷ trọng claim được support (partial tính nửa) của câu trả lời delivered |

### Bốn lớp kiểm tra trong verify/verifier.py

`split_claims` tách answer thành atomic claims: mỗi bullet là một claim, mỗi câu là một claim; heading kết thúc bằng hai chấm bị loại. Mỗi claim giữ danh sách citation [n] nó trích. Từng claim đi qua bốn lớp:

| Lớp | Kiểm tra gì | Ví dụ lỗi bị bắt |
| --- | --- | --- |
| **Numeric** | Mọi số phải tồn tại trong evidence, so theo unit conversion, tolerance 0.4% | "torque 60 Nm" khi evidence ghi 52 Nm → contradicted |
| **Identifier/reference** | Mã lỗi, model, ngày, tham chiếu "Table 3" phải nằm trong evidence **đã cite** — không phải toàn corpus | Mã SB-12 chỉ có trong [5] nhưng claim trích [2] → unsupported |
| **Negation** | Claim chứa phủ định khi không câu nào trong evidence phủ định → contradicted | "Valve is NOT auto-closing" khi evidence chỉ ghi mô tả khẳng định |
| **Lexical coverage** | IDF-weighted coverage của thuật ngữ claim so với evidence — từ hiếm có trọng số lớn | Paraphrase lố bịch làm coverage rơi dưới ngưỡng → unsupported |

Hai chi tiết quyết định chất lượng. **Số đối chiếu theo kích thước vật lý, không theo ký tự**: evidence "10 bar", claim "145 psi" — so chuỗi sai, so unit conversion khớp; "60 Nm" khi evidence "52 Nm" là lệch cùng kích thước torque → **contradicted**, nặng hơn unsupported; số có trong corpus nhưng ở evidence khác cái được cite cũng bị bắt. **Số người dùng trích lại trong correction được phép**: hệ thống phản bác false premise "Is the HX-200 rated for 150 degC?" bằng "rating is 140 degC, not 150 degC" — con số 150 do người dùng đưa; không có ngoại lệ này, mọi câu sửa false premise đều bị đánh chết.

Verdict cuối của mỗi claim:

| Verdict | Điều kiện | Score band |
| --- | --- | --- |
| supported | đủ coverage, không số lẻ, không identifier thiếu | ≥ 0.72 |
| partial | một phần số khớp, hoặc coverage trung bình | 0.48–0.72 |
| unsupported | số không có trong evidence, coverage thấp | < 0.48 |
| contradicted | lệch cùng kích thước vật lý, hoặc negation lật nghĩa | bị ép ≤ 0.2 |

### Composer offline: extractive là cách không thể bịa

Composer offline là **evidence-extractive**: mỗi câu ghép trực tiếp từ một row bảng, một step procedure, một chart reading hoặc kết quả tool — không sinh ngữ mới. `agent/compose.py` dùng **CiteBook** gán citation `[n]` theo thứ tự evidence xuất hiện lần đầu, và nhớ verifier-text của từng evidence để verifier đối chiếu đúng chỗ.

> "Composer is extractive in offline mode — cannot invent facts; fluency is traded for guaranteed faithfulness."

| Tiêu chí | Offline composer (extractive) | LLM mode (Anthropic / OpenAI-compatible) |
| --- | --- | --- |
| Nguồn câu chữ | Ghép từ row/step/chart/computed + template cố định | Viết tự do từ numbered evidence |
| Citation | CiteBook gán [n] theo thứ tự xuất hiện đầu tiên | Prompt bắt buộc trích [n], được gọi 2 tools |
| Risk bịa | Không thể bịa — chỉ trích và nối | Có thể bịa — bị verifier bắt |
| Fluency | Thấp — câu dạng bản ghi | Cao — văn xuôi tự nhiên |
| Offline / chi phí | Không key, không network | Cần server (Ollama local cũng được) |
| Vai trò | Default + fallback bắt buộc | Tùy chọn, output vẫn đi cùng verifier |

Điểm cần nhấn: offline composer là **fallback bắt buộc** của LLM mode. LLM chết (network, auth, malformed reply) hoặc output không qua verifier → pipeline quay về composer extractive — người dùng vẫn nhận câu trả lời có citation, chỉ kém mượt hơn.

### LLM mode: tùy chọn, viết từ numbered evidence

Default là offline thuần. Khi bật, LLM viết câu trả lời **từ numbered evidence** (chính là các [1], [2] CiteBook đã đánh số) và được gọi hai tool: `search_documents` và `lookup_spec` — tìm thêm tài liệu hoặc tra fact index với conflict resolution. LLM không được "tra google", chỉ được nhìn đúng kho evidence retrieval đã chọn.

Cấu hình với Ollama chạy local llama3.1 (miễn phí, không key):

```bash
MERIDIAN_LLM_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:11434/v1
MERIDIAN_LLM_MODEL=llama3.1
MERIDIAN_AGENT_MODE=auto
```

`MERIDIAN_AGENT_MODE=auto` — có LLM server thì dùng, không có thì offline; `policy` ép offline cứng. Với Docker Compose, base URL đổi thành `http://host.docker.internal:11434/v1` vì `localhost` trong container không trỏ về host.

⚠️ **Ghi chú API stability:** giao diện LLM và bộ env var của repo có thể đổi giữa các phiên bản — khi chạy thật, check README mới nhất trên repo trước khi copy cấu hình.

### Repair ladder: drop câu sai, không sửa câu sai

Câu trả lời có claim không được support thì repair ladder đi bốn nấc:

| Nấc | Hành động | Điều kiện |
| --- | --- | --- |
| 1 | **Pass-through** | Tất cả claim supported → delivered |
| 2 | **Repair** | Drop câu chứa claim unsupported/contradicted — câu còn lại giữ nguyên |
| 3 | **Fallback extractive** | Repair xong không còn đủ câu → quay về composer offline |
| 4 | **Abstain** | Cả hai fail → từ chối trả lời kèm lý do trong trace |

Nguyên tắc: **drop, không sửa**. Sửa câu sai bằng cách sinh câu mới là làm việc của generator — đưa vào repair là mở lỗ cho hallucination quay lại. Repair chỉ xóa. Nấc 3 và 4 là hai đường về an toàn: nấc 3 trả về câu có citation được đảm bảo, nấc 4 trả về "không trả lời được" — cả hai tốt hơn một câu bịa.

### Benchmark hallucination-injection: phát hiện 91.7%

Làm sao tin verifier không phải nơi trang trí? Benchmark injection lấy câu trả lời đã verify sạch, **tiêm lỗi có kiểm soát** — đổi số, thêm câu bịa, lật negation, đổi entity — rồi đo tỷ lệ phát hiện:

| Loại injection | Detection |
| --- | --- |
| Overall | 91.7% |
| Numeric | 87.5% |
| Fabricated sentence | 94.4% |
| Negation | 93.8% |
| Entity | 91.5% |
| False positive trên answer sạch | 12.3% |

False positive 12.3% là giá của độ nghiêm ngặt — câu sạch bị flag vì paraphrase mạnh làm coverage rơi; chấp nhận được vì repair chỉ drop câu. Kết quả cuối quan trọng nhất: faithfulness **100% claims supported** trên câu delivered — chưa có hallucination nào lọt tới người dùng trong benchmark này. Calibration đi cùng: confidence Platt-scaled trên train split, ECE held-out từ 0.027 → 0.008 — con số hiển thị cho người dùng đáng tin hơn gần 3.5 lần.

### Mini implementation: split_claims + check_number_claim

Sketch giữ ý chính của `verify/verifier.py` — tách claim, citation index, kiểm số unit-aware theo kích thước vật lý — thu về stdlib:

```python
"""Claim verifier sketch: split_claims + unit-aware number check (stdlib only)."""
import re

_CITE_RE = re.compile(r"\[(\d+)\]")
QTY_RE = re.compile(r"(\d+(?:\.\d+)?)\s*([a-z]+(?:-[a-z]+)?)")
_META_PREFIX = re.compile(r"\b(table|figure|fig\.?|section|step|page|rev(?:ision)?)\s*$")

UNIT_MAP = {
    "bar":   ("pressure", 100_000.0),
    "kpa":   ("pressure", 1_000.0),
    "psi":   ("pressure", 6_894.757),
    "nm":    ("torque", 1.0),
    "n-m":   ("torque", 1.0),
    "lb-ft": ("torque", 1.35582),
    "mm":    ("length", 0.001),
    "inch":  ("length", 0.0254),
}


def split_claims(answer):
    """Mỗi bullet/câu là một atomic claim → (text không citation, cites)."""
    claims = []
    for line in (answer or "").split("\n"):
        line = line.strip().lstrip("-*•> ").strip()
        if not line:
            continue
        cites = [int(m.group(1)) for m in _CITE_RE.finditer(line)]
        text = _CITE_RE.sub("", line).strip()
        text = re.sub(r"^\d{1,2}[.)]\s+", "", text)      # bỏ marker list
        if text.endswith(":"):                            # heading, không phải claim
            continue
        if len(re.findall(r"[A-Za-z0-9]+", text)) < 2:
            continue
        claims.append((text, cites))
    return claims


def _match(target, evidence_numbers, dim, rel_tol):
    for v, u in evidence_numbers:
        conv = UNIT_MAP.get(u)
        if conv and conv[0] == dim:
            if abs(v * conv[1] - target) <= rel_tol * max(abs(target), 1.0):
                return True
    return False


def check_number_claim(claim_text, evidence_numbers, rel_tol=0.004):
    """Số trong claim đối chiếu evidence theo kích thước vật lý:
    khớp hết → supported; lệch cùng kích thước → contradicted; thiếu hẳn → unsupported."""
    checks = []
    lower = claim_text.lower()
    for m in QTY_RE.finditer(lower):
        value, unit = float(m.group(1)), m.group(2)
        conv = UNIT_MAP.get(unit)
        if conv is None:
            continue                                      # identifier hoặc từ thường
        prefix = lower[max(0, m.start() - 14):m.start()]
        if _META_PREFIX.match(prefix):
            continue                                      # số bảng/trang/bước, không phải quantity
        dim, factor = conv
        target = value * factor
        checks.append((f"{value:g} {unit}", _match(target, evidence_numbers, dim, rel_tol), dim))
    if not checks:
        return "supported", []                            # không chứa số → fail ở bước khác
    reasons = [f"number {name} không được evidence hỗ trợ" for name, ok, _ in checks if not ok]
    if all(ok for _, ok, _ in checks):
        return "supported", []
    ev_dims = {UNIT_MAP[u][0] for _, u in evidence_numbers if u in UNIT_MAP}
    if any(not ok and dim in ev_dims for _, ok, dim in checks):
        reasons.append("same-dimension number differs → contradicted")
        return "contradicted", reasons
    if any(ok for _, ok, _ in checks):
        return "partial", reasons
    return "unsupported", reasons


answer = (
    "Impeller bolt torque is 52 Nm [1].\n"
    "Maximum inlet pressure is 145 psi [2].\n"
    "Shaft runout limit is 0.05 mm [3]."
)
claims = split_claims(answer)
assert len(claims) == 3, claims

ev = [(52.0, "nm"), (10.0, "bar")]          # evidence đã cite: torque + pressure
v1, r1 = check_number_claim(claims[0][0], ev)
assert v1 == "supported", (v1, r1)

v2, r2 = check_number_claim(claims[1][0], ev)   # 10 bar = 145 psi — khác đơn vị, cùng pressure
assert v2 == "supported", (v2, r2)

v3, r3 = check_number_claim("Impeller bolt torque is 60 Nm", ev)
assert v3 == "contradicted", (v3, r3)           # lệch cùng kích thước torque

v4, r4 = check_number_claim(claims[2][0], ev)
assert v4 == "unsupported", (v4, r4)            # length không có trong evidence

print("OK —", v1, "|", v2, "|", v3, "|", v4)
for text, cites in claims:
    print(f"  claim: {text!r}  cites={cites}")
```

### Bài tập

**Làm theo:** Chạy code block trên, rồi sửa `ev` thành `[(52.0, "lb-ft")]` — claim "52 Nm" giờ khớp không, vì sao? Ghi lại kết quả trước khi chạy.

**Tự sửa:** Thêm echo-refutation vào `check_number_claim`: nhận thêm `echo_numbers` (số người dùng đưa); số khớp echo được miễn trừ khi claim có từ phủ định. Test với "Rating is 140 degC, not 150 degC" và evidence chỉ có 140 — phải supported thay vì contradicted.

**Mở rộng:** Viết `repair_ladder(answer, verdicts)` mô phỏng repair của `verifier.py`: drop câu chứa claim unsupported/contradicted; nếu sau repair faithfulness dưới 0.6, trả về "FALLBACK_EXTRACTIVE". So sánh với prompt flow trong bài [Agent RAG và GraphRAG](/bai-viet/kien-truc-ai-agent-cam-nang/).

### Lỗi thường gặp

- **Verifier bắt claim đúng vì paraphrase mạnh** → lexical coverage rơi dưới ngưỡng 0.72 dù nghĩa đúng → nguồn false positive 12.3%; hạ ngưỡng hoặc so thêm câu evidence khác, không dùng coverage một mình.
- **Số correction của người dùng bị flag hallucination** → thiếu echo-refutation → truyền `echo_text` (câu hỏi gốc) vào `verify()` để số trích lại được miễn trừ trong phần correction.
- **Citation [n] chỉ vào evidence không tồn tại** → LLM tự sáng tạo số citation ngoài range → verifier bắt "cites non-existent evidence" ngay lớp đầu; composer offline không xảy ra vì CiteBook gán số theo thứ tự thật.
- **Số bảng/trang bị đếm là quantity** ("see Table 3" → 3 là số?) → thiếu lọc meta-prefix → số sau "table/figure/section/step/page" phải loại trước khi check numeric.
- **Verifier chậm trên request lớn** → evidence set không cache → `EvidenceDoc.prepare()` cache sẵn sentence windows, quantities, identifiers; verify chỉ chạy trên claims đã tách.

### FAQ

**Verifier khác grader ở bài trước chỗ nào?**
Grader chấm evidence TRƯỚC generation — quyết định trả lời hay abstain. Verifier chấm từng claim SAU generation — đối chiếu câu trả lời đã viết với evidence được cite. Grader chặn generation chạy thiếu evidence; verifier bắt những gì lọt qua trong lúc viết. Hai lớp cùng hoạt động, không thay thế nhau.

**Vì sao composer offline không thể bịa?**
Composer extractive ghép mỗi câu từ row bảng, step procedure, chart reading hoặc kết quả tool đã truy xuất, mỗi câu kèm citation [n] do CiteBook gán theo thứ tự xuất hiện đầu tiên. Không có bước sinh ngữ mới — chỉ trích và nối. Trade-off: fluency thấp hơn LLM, đổi lấy faithfulness được đảm bảo bằng cấu trúc.

**Số người dùng đưa vào câu hỏi bị flag là hallucination thì sao?**
Verifier có echo-refutation: số người dùng trích lại trong phần correction ('... is 140 degC, not 150 degC') được phép — đây là số đang bị bác bỏ, không phải số bịa. Không có cơ chế này, mọi câu phản bác false premise đều bị verifier đánh chết và repair xóa nhầm phần correction đúng.

**False positive 12.3% trên benchmark injection nghĩa là gì?**
Trên câu trả lời sạch, 12.3% claim bị flag không chính xác — chủ yếu paraphrase mạnh làm IDF-weighted lexical coverage rơi dưới ngưỡng. Chi phí chấp nhận được vì repair chỉ drop câu unsupported (không sửa câu), faithfulness của câu delivered vẫn 100%, và nó hiện rõ trong reports/eval_report.md chứ không được giấu.

### Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) mục 3 (Decisions: verifier separate from generator, composer extractive) và mục 5 (Trust layer); README mục "Optional: use an LLM" và Measured results
- Code trong bài: `meridian/verify/verifier.py` (split_claims, bốn lớp check, verdicts, repair), `meridian/agent/compose.py` (composer extractive, CiteBook gán [n]), `meridian/llm/base.py` (provider-neutral client, LLMError → fallback), `meridian/agent/llm_agent.py` (LLM writer, tools search_documents / lookup_spec)
- Bài liền kề trong series: CRAG grader và abstention · Benchmark và deploy
- Từ blog cũ: [Agent RAG và GraphRAG](/bai-viet/kien-truc-ai-agent-cam-nang/) — so sánh cách agent RAG thông thường xử lý output LLM với repair ladder trong bài

---

08. Benchmark và deploy: đóng benchmark held-out, chạy Qdrant offline — ≈13 phút

RAG không có benchmark đóng held-out là RAG chưa xong. Bạn có thể đổi retriever, thêm reranker, gắn LLM vào composer — không có tập câu hỏi đã đóng, mọi thay đổi được đánh giá bằng cảm giác "trông có vẻ tốt hơn". Bài này lấy Meridian làm case study cho hai việc còn lại của pipeline: **đóng benchmark held-out có số liệu trung thực** và **deploy ổn định với Qdrant tự host** — cả hai chạy offline, không key, không tài khoản vector database.

### Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Golden questions** | Bộ câu hỏi sinh cùng corpus, đi kèm answer facts (tolerance + unit) và gold evidence |
| **Held-out split** | Tách train/test (50/43) — model chỉ được học trên train, được chấm trên test |
| **nDCG** | Normalized Discounted Cumulative Gain — đo thứ hạng retrieval tính theo vị trí lãi suất |
| **ECE / Brier** | Expected Calibration Error và mean squared error của confidence so với nhãn đúng/sai |
| **Bootstrap CI** | Khoảng tin cậy 95% bằng resampling các câu hỏi — đo độ hẹp của số liệu |
| **Ablation** | Tắt từng retrieval channel để đo đóng góp riêng — bảng per-channel trong report |
| **Qdrant** | Vector database tự host cho ANN search; free, không API key |

### Eval design: golden questions sinh cùng corpus

Trích ARCHITECTURE.md mục 6:

> "Golden questions are generated *with* the corpus so ground truth is exact (answer facts with tolerance and units; gold evidence by document + required phrases)."

Quyết định này thay đổi tính chất của benchmark. Khi câu hỏi được sinh từ chính document nó hỏi về, ground truth không phải "ý kiến người gán nhãn" nữa — nó là phép trích xuất: giá trị đúng có tolerance, có unit; evidence đúng là document cụ thể + những cụm từ bắt buộc phải xuất hiện. So sánh với pipeline gán nhãn tay thường gặp:

| Tiêu chí | Golden questions sinh cùng corpus | Gán nhãn tay trên corpus thật |
| --- | --- | --- |
| Độ chính xác ground truth | Tuyệt đối — giá trị từ source của chính document | Phụ thuộc người gán, dễ lệch |
| Định dạng answer | Facts với tolerance + units — so unit-aware | Văn bản tự do — so fuzzy |
| Gold evidence | Document + required phrases — kiểm chứng được | Trích dẫn thủ công |
| Khớp corpus thật | Không — synthetic ≠ real manuals | Khớp |
| Chi phí sinh lại | Chạy lại script | Gán lại toàn bộ |

Split 50/43 train/test: model học chỉ trên train, chấm trên held-out. Bộ metrics đo mỗi run: Hit/Recall@k, MRR, nDCG cho retrieval; unit-aware answer correctness cho QA; abstention precision/recall; faithfulness; citation recall; ECE/Brier cho calibration; bootstrap CI cho độ hẹp của số liệu; latency. **Ablation per channel** — tắt từng kênh trong 8 kênh hybrid (bài 8 kênh hybrid retrieval) để đo đóng góp riêng, xuất thẳng vào report thay vì phỏng đoán.

Số liệu benchmark chính (93 câu, 43 held-out): retrieval Hit@1 89.5%, Hit@5 100%, MRR 0.88; answer correctness unit-aware 93.1% overall, 92.5% held-out; unanswerable declined 100%; faithfulness 100%; ECE 0.027 → 0.008 sau Platt scaling. Đây là số liệu đo được trên corpus synthetic — không phải claim về manual thật.

### Bài học trung thực: learned ranker được train nhưng KHÔNG adopt

Chi tiết này đáng đọc hơn mọi số liệu trong report. Meridian có một hook learned-to-rank: logistic-regression ranker 17 features có thể được train bằng `scripts/run_eval.py`. Nó được train thật. Và nó **không được adopt** — vì không thắng hand-tuned weights trên held-out split.

> "a logistic-regression ranker can be trained (`scripts/run_eval.py`) and is adopted only if it beats the default on held-out questions."

Quy tắc adoption một chiều: chỉ vào production khi beat default trên tập câu hỏi chưa từng thấy. Điểm cần ghi nhớ: eval có quyền nói **KHÔNG** với model "đẹp hơn" — đẹp hơn là tổng thể đẹp trên train, đẹp hơn là thuyết phục về mặt kỹ thuật; còn held-out là trọng tài duy nhất. Pipeline RAG nhiều dự án rơi vào vấn đề ngược lại: thêm model mới vào pipeline vì "nó mới hơn nó mạnh hơn", không có benchmark đóng để đối chiếu — mỗi quyết định kiến trúc là một cú bắn mù.

### Known failures: 6/93 hiện trong report, không giấu

Report ghi rõ 6 câu thất bại trên 93, chia theo loại — không phải footnote, mà là phần nội dung của `reports/eval_report.md`:

| Loại lỗi | Mô tả | Tỷ lệ trên loại đó |
| --- | --- | --- |
| Multi-hop | Cần ghép fact từ 2 documents khác nhau | ~40% câu multi-hop |
| Data-plate OCR | Ảnh low-contrast của data plate — OCR đọc sai | Câu cần data plate |
| Prose procedures | Câu hỏi diễn đạt khác manual quá nhiều | Vài câu procedure |
| Verifier false positive | Paraphrase mạnh làm lexical coverage rơi | ~12% trên answer sạch |

Mỗi lỗi được đối chiếu: multi-hop 40% thất bại là **giới hạn kiến trúc** của evidence selection hiện tại — nó theo cross-reference trong cùng document tốt, ghép hai document khác nhau chưa xử lý; data-plate OCR là **giới hạn OCR trên ảnh kém chất lượng**, không phải lỗi retrieval. Tách rõ từng loại là điều kiện để fix đúng chỗ — báo cáo giấu lỗi là báo cáo không dùng được để fix.

### Deployment: Docker Compose + Qdrant offline

`docker compose up --build` start hai service: Meridian và Qdrant. Qdrant là vector database **self-hosted** — free, không API key, không account. Vector index persist trong volume `qdrant-data`; documents và parsed chunks nằm trong volume `meridian-data`. Container chạy non-root user, expose `/api/health` cho health check. Qdrant không publish ra host network theo default.

Điểm kiến trúc cần hiểu rõ: **Qdrant collection được rebuild từ SQLite khi start và sau mỗi mutation**. Đây là ANN search cho vector — chưa phải incremental ingestion hay một ingestion service scale ngang. Lexical, graph, fact index vẫn in-process; multi-replica coordination và tenant isolation chưa được implement. Không giấu giới hạn này trong doc — nó nằm ngay trong DEPLOYMENT.md production notes.

Bảng env vars chính:

| Variable | Default | Nghĩa |
| --- | --- | --- |
| `MERIDIAN_VECTOR_STORE` | `memory` | `memory` (in-process LSA) hoặc `qdrant` (ANN qua Qdrant) |
| `MERIDIAN_QDRANT_URL` | `http://localhost:6333` | Địa chỉ Qdrant server |
| `MERIDIAN_LLM_PROVIDER` | `none` | `anthropic` hoặc `openai` (OpenAI-compatible) |
| `MERIDIAN_AGENT_MODE` | `auto` | `auto` dùng LLM khi có; `policy` ép offline |
| `MERIDIAN_OCR_LANG` | `eng` | Tesseract language packs, ví dụ `eng+deu` |
| `MERIDIAN_RENDER_DPI` | `170` | Độ phân giải render trang |
| `MERIDIAN_MAX_UPLOAD_MB` | `60` | Giới hạn upload mỗi file |

Production notes: đặt reverse proxy (nginx, Caddy) với TLS và authentication phía trước — app không có login riêng; **backup volume `data`** — index rebuild từ SQLite khi start, mất SQLite là mất corpus; sentence-transformers là tùy chọn (bật `MERIDIAN_EMBEDDINGS=st`, model `BAAI/bge-small-en-v1.5`) nhưng cần download model một lần nên default vẫn là LSA chạy offline thuần — phải re-ingest sau khi đổi.

### Lệnh benchmark và mở rộng pipeline

Ba lệnh làm xương sống của benchmark workflow:

```bash
python scripts/build_corpus.py            # sinh lại synthetic corpus + golden questions (cần reportlab)
python scripts/run_eval.py [--no-train]   # benchmark đầy đủ → reports/eval_report.{md,json} + charts
python scripts/build_stress_corpus.py [--docs 100]  # corpus stress riêng: 700 chunks, 700 questions
```

Mở rộng pipeline có ba đường chính, mỗi đường có một điểm ghi:

| Mở rộng | Cách làm | Điểm ghi |
| --- | --- | --- |
| Thêm parser document mới | Viết parser trả `(Document, [Chunk])` và register suffix trong `ingest/pipeline.py` | Contract là tuple — parser không biết retrieval tồn tại |
| Thêm retrieval channel | Thêm scorer trong `retrieval/pipeline.py`, weight trong `RetrievalConfig.channel_weights`, feature trong `rerank.FEATURES` | Channel mới phải đi qua ablation — đo đóng góp trên held-out |
| Đổi domain | Thay `resources/synonyms.json`, units, entity regexes trong `ingest/common.py` | Domain-agnostic nằm ở config, không phải rewrite pipeline |

Đây là phần ARCHITECTURE mục 8 — kiến trúc mở rộng được vì mỗi khối có contract rõ: parser không biết retrieval, channel mới không cần sửa composer, domain mới không cần sửa verifier.

### Mini implementation: bootstrap CI + ECE/Brier

Sketch thu về stdlib: bootstrap CI cho held-out correctness và ECE/Brier cho Platt scaling trước/sau:

```python
"""Bootstrap CI + ECE/Brier cho benchmark RAG (stdlib only)."""
import random


def bootstrap_ci(scores, n_boot=200, alpha=0.05, seed=7):
    """95% CI cho trung bình bằng bootstrap resampling (resample các câu hỏi)."""
    rng = random.Random(seed)
    n = len(scores)
    means = sorted(sum(scores[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot))
    lo = means[int((alpha / 2) * n_boot)]
    hi = means[int((1 - alpha / 2) * n_boot) - 1]
    return sum(scores) / n, lo, hi


def brier(scores, labels):
    """Mean squared error của confidence so với nhãn đúng/sai."""
    return sum((p - y) ** 2 for p, y in zip(scores, labels)) / len(scores)


def ece(scores, labels, n_bins=5):
    """Expected Calibration Error: |confidence trung bình - accuracy| có trọng số theo bin."""
    bins = [[] for _ in range(n_bins)]
    for p, y in zip(scores, labels):
        bins[min(int(p * n_bins), n_bins - 1)].append((p, y))
    total = len(scores)
    err = 0.0
    for b in bins:
        if b:
            conf = sum(p for p, _ in b) / len(b)
            acc = sum(y for _, y in b) / len(b)
            err += (len(b) / total) * abs(conf - acc)
    return err


held_out = [1] * 40 + [0] * 3                 # 43 câu held-out, 40 đúng → 93.0%
mean, lo, hi = bootstrap_ci(held_out, n_boot=200)
assert lo <= mean <= hi, (lo, mean, hi)
assert hi - lo < 0.25, (lo, hi)               # CI hẹp: đủ tin để so sánh pipeline

lab = [1] * 10 + [0, 0]                       # 12 câu: 10 đúng, 2 sai
conf_before = [0.75] * 10 + [0.85, 0.85]      # kém tự tin ở câu đúng, quá tự tin ở câu sai
conf_after = [0.95] * 10 + [0.25, 0.25]       # Platt scaling kéo lại
e_before, e_after = ece(conf_before, lab), ece(conf_after, lab)
assert e_after < e_before, (e_before, e_after)
assert brier(conf_after, lab) < brier(conf_before, lab)
print(f"OK — held-out {mean:.3f} CI [{lo:.3f}, {hi:.3f}] | "
      f"ECE {e_before:.3f} → {e_after:.3f} | Brier {brier(conf_before, lab):.3f} → {brier(conf_after, lab):.3f}")
```

### Bài tập

**Làm theo:** Chạy code block trên. Sửa `n_boot` thành 20 rồi 500 — bootstrap CI thay đổi thế nào, n_boot 20 còn đáng tin để so sánh pipeline không, và vì sao? Ghi lại giá trị lo/hi của ba lần chạy.

**Tự sửa:** Thêm hàm `mrr(ranked_lists)` tính MRR từ danh sách rank của gold document trên 43 câu held-out: mỗi câu là list index vị trí gold (1-based); MRR = mean(1/rank đầu tiên gold xuất hiện). So với giá trị MRR 0.88 trong README — viết thêm assert kiểm MRR >= 0.8 trên tập giả lập có 40/43 câu gold rank 1 và 3 câu gold rank 2.

**Mở rộng:** Viết ablation mini: giả sử bạn có 3 channel với score riêng từng câu — chạy hai config (full pipeline và tắt một channel), dùng `bootstrap_ci` trên hiệu số accuracy giữa hai config để trả lời "channel này có đáng giữ không" thay vì nhìn điểm trung bình trần. Thêm vào đó một adoption gate: chỉ adopt config mới khi biên giới dưới của CI của nó cao hơn biên giới trên của default.

### Lỗi thường gặp

- **Đánh giá RAG bằng cảm giác sau mỗi thay đổi** → không có benchmark held-out đóng → sinh corpus + golden questions, tách train/test, chỉ so config trên held-out; không thêm model mới vì "thuyết phục về lý thuyết" khi chưa qua ablation.
- **Số benchmark cao hơn số thật khi deploy** → benchmark đo trên synthetic corpus, không phải manual thật → đọc report như đo kiến trúc; synthetic stress corpus ≠ production accuracy — kiểm tra lại trên bộ tài liệu thật của bạn trước khi hứa chất lượng với khách.
- **Qdrant rebuild toàn bộ collection sau mỗi upload lớn** → ingestion chưa incremental, mutation lớn tốn thời gian → chấp nhận ở quy mô demo/cá nhân; nếu cần incremental ingestion thật thì phải tách ingestion service — ghi rõ trong doc chứ không ngụ ý.
- **Container không gọi được Ollama trên host** → trong Docker, `localhost` là container → set `OPENAI_BASE_URL=http://host.docker.internal:11434/v1` và recreate service sau khi đổi `.env` (`docker compose up -d --no-build --force-recreate meridian`).
- **Bootstrap CI quá rộng để so sánh config** → số câu held-out quá nhỏ (10–20 câu) → tăng số câu held-out (43 trong benchmark này) hoặc tăng n_boot; n_boot không thay đổi độ hẹp CI thật — nó chỉ ổn định ước lượng, n câu held-out mới quyết định độ hẹp.

### FAQ

**Vì sao golden questions sinh cùng corpus mà không phải gán nhãn tay?**
Vì generator sinh câu hỏi từ chính document nó vừa tạo — ground truth chính xác tuyệt đối: answer facts đi kèm tolerance và unit, gold evidence xác định theo document + required phrases. Gán nhãn tay trên corpus thật tốn công, lệch người và không kiểm chứng được 'đây là câu trả lời đúng'. Trade-off rõ ràng: synthetic corpus ≠ real manuals — benchmark đo kiến trúc, không đo production accuracy.

**Learned ranker đẹp hơn sao không adopt?**
Vì nó không thắng hand-tuned weights trên held-out split. Adoption gate là quy tắc một chiều: ranker học chỉ được vào production khi beat default trên tập câu hỏi nó chưa từng thấy. Eval có quyền nói KHÔNG với model 'đẹp hơn' — benchmark đóng held-out nghĩa là không có lối tắt nào qua mô hình dễ nhìn.

**Qdrant có cần API key hay account không?**
Không. Qdrant self-hosted là free — Docker Compose start nó cùng Meridian, persist vector index trong volume qdrant-data. MERIDIAN_VECTOR_STORE=qdrant, MERIDIAN_QDRANT_URL default http://localhost:6333. Điểm cần nhớ: collection rebuild từ SQLite khi start và sau mỗi mutation — đây là ANN search cho vector, chưa phải incremental ingestion.

**Stress corpus 700 câu dùng để làm gì?**
Kiểm hành vi retrieval khi quy mô tăng: 100 generated notes → 700 chunks → 700 questions (600 answerable, 100 unanswerable), held-out theo model. Kết quả cho thấy độ khó tăng thật: Hit@1 65% so với 89.5% trên benchmark chính — và false abstention 10%. Đây là công cụ đo độ nhạy của ngưỡng, không phải bằng chứng production accuracy.

### Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) mục 6 (Evaluation design), mục 7 (Failure modes), mục 8 (Extending); [docs/DEPLOYMENT.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/DEPLOYMENT.md) toàn bộ (Docker, env vars, production notes); README Measured results + Larger synthetic stress benchmark
- Code trong bài: `meridian/eval/` (metrics.py, runner.py, report.py), `scripts/run_eval.py` (benchmark + trained ranker hook), `scripts/build_corpus.py`, `scripts/build_stress_corpus.py`, `docker-compose.yml` (Meridian + Qdrant volumes)
- Bài liền kề trong series: Claim verifier bắt hallucination · Series bắt đầu: RAG bảo trì công nghiệp
- Từ blog cũ: [Đánh giá chất lượng RAG với Ragas](/bai-viet/rag-nang-cao-cam-nang/) — Ragas đánh giá sau khi hệ thống trả lời; benchmark trong bài đóng held-out và chấm cả retrieval lẫn calibration trước deploy

---
title: "Meridian: vì sao text-chunk RAG thất bại trên tài liệu bảo trì công nghiệp"
description: "Torque nằm trong table row, derating trong chart image, mã alarm trên ảnh panel — text-chunk RAG sai mỗi kiểu tài liệu một cách khác nhau. Meridian dùng 8 kênh hybrid retrieval, CRAG grader + abstention và claim verifier: Hit@1 89.5%, abstention 100% trên benchmark 93 câu."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-23"
cover: "/images/covers/posts/meridian-rag-bao-tri-cong-nghiep.jpg"
featured: false
views: 385
faq:
  - q: "Meridian có cần API key, LLM hay GPU để chạy không?"
    a: "Không. Mặc định deterministic offline: LSA + BM25 chạy trên CPU, không API key, không GPU, không data rời máy. LLM (Anthropic hoặc server OpenAI-compatible như Ollama) là tùy chọn và vẫn phải đi qua cùng một verifier."
  - q: "Con số 93.1% correctness đo trên dữ liệu gì?"
    a: "Benchmark synthetic 93 câu hỏi (43 held-out) sinh cùng corpus 6 documents, 157 chunks. Đây là bằng chứng cho thiết kế pipeline, không phải claim về manual thật của nhà máy."
  - q: "Vì sao hệ thống trả lời sai khi manual và service bulletin mâu thuẫn?"
    a: "Text-chunk RAG trộn lẫn hai nguồn rồi để LLM đoán. Meridian đưa giá trị về dạng Fact có provenance rồi áp precedence: cột revised trước, bulletin trên manual, rồi effective date mới nhất; giá trị thua thành ConflictNote."
  - q: "Khi nào Meridian từ chối trả lời thay vì đoán?"
    a: "Ba tình huống: grader chấm evidence chưa đủ sau corrective retry; câu hỏi nhắc model không có trong corpus hoặc premise sai; verifier không repair được claim unsupported nào."
---

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

## Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Evidence-grounded RAG** | Bảng, biểu đồ, warning, log, ảnh là evidence có cấu trúc và citation được, không phải text phẳng |
| **Layout-aware parsing** | Bảng → table + per-row chunks + typed facts; call-out → WARNING chunk; figure crop; bbox |
| **Hybrid retrieval (8 kênh)** | BM25, LSA dense, char-n-gram, entity, fact, visual, PRF, graph → weighted RRF → rerank → MMR |
| **CRAG grader** | Chấm mức phủ evidence trước khi sinh; thiếu → corrective retry hoặc abstain |
| **Abstention** | Từ chối trả lời khi evidence không đủ hoặc premise sai, thay vì đoán |
| **Conflict resolution** | Cùng (model, subject, attribute) từ nhiều nguồn → precedence: revised > bulletin > manual > effective date |
| **Claim verifier** | Kiểm từng claim: số unit-aware, identifier, tham chiếu, phủ định; fail → repair hoặc fallback |

## Luồng 9 bước từ câu hỏi đến câu trả lời

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

## Typical RAG demo vs Meridian: bảy điểm khác biệt

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

## Offline-first: LSA + BM25, không cần LLM

> **Offline-first (LSA + BM25, không LLM):** benchmark tái lập được, chạy mọi nơi, không data rời máy. Chi phí: hiểu paraphrase yếu hơn neural encoder — giảm nhẹ bằng synonym canonicalisation, char-n-grams, late interaction.

Dense index mặc định là LSA (TF-IDF → SVD) trên word + char n-grams, in-memory; Docker Compose dùng Qdrant làm vector database — backend, không phải model embedding. Learned ranker 17 features đã train nhưng **không được adopt** vì không thắng weights hand-tuned trên held-out split — quyết định theo số, không theo trend.

## Số liệu benchmark

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

## Quickstart 5 phút

```bash
# 1. OCR engine hệ thống (cài một lần)
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

## Sketch "decide first" bằng Python thuần

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

## Bài tập

**Làm theo** — Chạy quickstart, hỏi lần lượt 5 demo questions. Mở trace SSE: ghi bước pipeline dừng (grader, premise hay verifier) và modality của citation — table_row, chart hay ocr_page.

**Tự sửa** — Sửa `route_intent` thêm nhánh `procedure` cho câu hỏi bắt đầu bằng "cách / làm thế nào / replace": route vào `retrieval` nhưng trả intent khác để Evidence stage attach các step chunks; chạy lại script và kiểm tra bảng nhánh đổi đúng.

**Mở rộng** — Viết hàm `weighted_rrf(rankings, weights, k=60)` theo công thức `score = Σ w_i / (k + rank_i)` cho 2 kênh BM25 + dense, test trên 5 câu demo và so Hit@1 trước/sau fusion; đối chiếu cách Meridian fuse 8 kênh trong `retrieval/pipeline.py`.

## Lỗi thường gặp

- ⚠️ `TesseractNotFoundError` hoặc trang scan trả về rỗng → Tesseract chưa cài → macOS `brew install tesseract`, Ubuntu `sudo apt install tesseract-ocr`; ngoài OCR, mọi path khác vẫn chạy.
- ⚠️ Hỏi giá trị trên chart nhưng hệ thống trả lời từ caption → câu hỏi thiếu mốc (tại 50% load) nên không route vào chart digitiser → đưa mốc vào câu hỏi; kiểm tra citation modality `chart`.
- ⚠️ Trả lời 45 Nm dù bulletin đã ra 52 Nm → system tự viết không có conflict resolution → gắn doc_type + effective_date vào mỗi fact và áp precedence; giá trị thua hiện ConflictNote, không bị giấu.
- ⚠️ Abstain sai trên câu hỏi hợp lệ → paraphrase mạnh khiến grader thấy query term thiếu trong corpus → synonym canonicalisation + char-n-gram; đọc trace xem grader chấm bước nào.
- ⚠️ Port 8000 bị chiếm khi start → service khác đang chạy → `python -m meridian --port 8010`.

## FAQ

**Meridian có cần API key, LLM hay GPU để chạy không?**
Không. Mặc định deterministic offline: LSA + BM25 chạy trên CPU, không API key, không GPU, không data rời máy. LLM (Anthropic hoặc server OpenAI-compatible như Ollama) là tùy chọn và vẫn phải đi qua cùng một verifier.

**Con số 93.1% correctness đo trên dữ liệu gì?**
Benchmark synthetic 93 câu hỏi (43 held-out) sinh cùng corpus 6 documents, 157 chunks. Đây là bằng chứng cho thiết kế pipeline, không phải claim về manual thật của nhà máy.

**Vì sao hệ thống trả lời sai khi manual và service bulletin mâu thuẫn?**
Text-chunk RAG trộn lẫn hai nguồn rồi để LLM đoán. Meridian đưa giá trị về dạng Fact có provenance rồi áp precedence: cột revised trước, bulletin trên manual, rồi effective date mới nhất; giá trị thua thành ConflictNote.

**Khi nào Meridian từ chối trả lời thay vì đoán?**
Ba tình huống: grader chấm evidence chưa đủ sau corrective retry; câu hỏi nhắc model không có trong corpus hoặc premise sai; verifier không repair được claim unsupported nào.

## Tài liệu gốc

- [Meridian README](https://github.com/punit2911/meridian-multimodal-rag#readme) — bảng "Why it is different", quick start, measured results
- [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) — luồng 9 bước, decisions table, retrieval chi tiết
- Bài liền kề trong series: [Ingestion layout-aware: biến PDF bảng biểu và scan thành evidence có citation](/bai-viet/meridian-ingest-pdf-bang-bieu-scan/) · [Hybrid retrieval 8 kênh](/bai-viet/meridian-hybrid-retrieval-8-kenh/) · bài nền [Multimodal RAG PDF tiếng Việt](/bai-viet/multimodal-rag-pdf-tieng-viet/) — nơi phân tích hiện tượng COLUMN_SLIP khi bảng bị làm phẳng

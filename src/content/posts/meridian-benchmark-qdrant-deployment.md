---
title: "Benchmark và deploy: đóng benchmark held-out, chạy Qdrant offline"
description: "Eval design của Meridian: golden questions sinh cùng corpus nên ground truth chính xác tuyệt đối, 50/43 train/test, bootstrap CI và ablation per channel; learned ranker được train nhưng KHÔNG adopt vì không thắng hand-tuned trên held-out; deploy Docker Compose với Qdrant tự host, không API key."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-23"
cover: "/images/covers/posts/meridian-benchmark-qdrant-deployment.jpg"
featured: false
views: 296
faq:
  - q: "Vì sao golden questions sinh cùng corpus mà không phải gán nhãn tay?"
    a: "Vì generator sinh câu hỏi từ chính document nó vừa tạo — ground truth chính xác tuyệt đối: answer facts đi kèm tolerance và unit, gold evidence xác định theo document + required phrases. Gán nhãn tay trên corpus thật tốn công, lệch người và không kiểm chứng được 'đây là câu trả lời đúng'. Trade-off rõ ràng: synthetic corpus ≠ real manuals — benchmark đo kiến trúc, không đo production accuracy."
  - q: "Learned ranker đẹp hơn sao không adopt?"
    a: "Vì nó không thắng hand-tuned weights trên held-out split. Adoption gate là quy tắc một chiều: ranker học chỉ được vào production khi beat default trên tập câu hỏi nó chưa từng thấy. Eval có quyền nói KHÔNG với model 'đẹp hơn' — benchmark đóng held-out nghĩa là không có lối tắt nào qua mô hình dễ nhìn."
  - q: "Qdrant có cần API key hay account không?"
    a: "Không. Qdrant self-hosted là free — Docker Compose start nó cùng Meridian, persist vector index trong volume qdrant-data. MERIDIAN_VECTOR_STORE=qdrant, MERIDIAN_QDRANT_URL default http://localhost:6333. Điểm cần nhớ: collection rebuild từ SQLite khi start và sau mỗi mutation — đây là ANN search cho vector, chưa phải incremental ingestion."
  - q: "Stress corpus 700 câu dùng để làm gì?"
    a: "Kiểm hành vi retrieval khi quy mô tăng: 100 generated notes → 700 chunks → 700 questions (600 answerable, 100 unanswerable), held-out theo model. Kết quả cho thấy độ khó tăng thật: Hit@1 65% so với 89.5% trên benchmark chính — và false abstention 10%. Đây là công cụ đo độ nhạy của ngưỡng, không phải bằng chứng production accuracy."
---

RAG không có benchmark đóng held-out là RAG chưa xong. Bạn có thể đổi retriever, thêm reranker, gắn LLM vào composer — không có tập câu hỏi đã đóng, mọi thay đổi được đánh giá bằng cảm giác "trông có vẻ tốt hơn". Bài này lấy Meridian làm case study cho hai việc còn lại của pipeline: **đóng benchmark held-out có số liệu trung thực** và **deploy ổn định với Qdrant tự host** — cả hai chạy offline, không key, không tài khoản vector database.

## Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Golden questions** | Bộ câu hỏi sinh cùng corpus, đi kèm answer facts (tolerance + unit) và gold evidence |
| **Held-out split** | Tách train/test (50/43) — model chỉ được học trên train, được chấm trên test |
| **nDCG** | Normalized Discounted Cumulative Gain — đo thứ hạng retrieval tính theo vị trí lãi suất |
| **ECE / Brier** | Expected Calibration Error và mean squared error của confidence so với nhãn đúng/sai |
| **Bootstrap CI** | Khoảng tin cậy 95% bằng resampling các câu hỏi — đo độ hẹp của số liệu |
| **Ablation** | Tắt từng retrieval channel để đo đóng góp riêng — bảng per-channel trong report |
| **Qdrant** | Vector database tự host cho ANN search; free, không API key |

## Eval design: golden questions sinh cùng corpus

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

Split 50/43 train/test: model học chỉ trên train, chấm trên held-out. Bộ metrics đo mỗi run: Hit/Recall@k, MRR, nDCG cho retrieval; unit-aware answer correctness cho QA; abstention precision/recall; faithfulness; citation recall; ECE/Brier cho calibration; bootstrap CI cho độ hẹp của số liệu; latency. **Ablation per channel** — tắt từng kênh trong 8 kênh hybrid (bài [8 kênh hybrid retrieval](/bai-viet/meridian-hybrid-retrieval-8-kenh/)) để đo đóng góp riêng, xuất thẳng vào report thay vì phỏng đoán.

Số liệu benchmark chính (93 câu, 43 held-out): retrieval Hit@1 89.5%, Hit@5 100%, MRR 0.88; answer correctness unit-aware 93.1% overall, 92.5% held-out; unanswerable declined 100%; faithfulness 100%; ECE 0.027 → 0.008 sau Platt scaling. Đây là số liệu đo được trên corpus synthetic — không phải claim về manual thật.

## Bài học trung thực: learned ranker được train nhưng KHÔNG adopt

Chi tiết này đáng đọc hơn mọi số liệu trong report. Meridian có một hook learned-to-rank: logistic-regression ranker 17 features có thể được train bằng `scripts/run_eval.py`. Nó được train thật. Và nó **không được adopt** — vì không thắng hand-tuned weights trên held-out split.

> "a logistic-regression ranker can be trained (`scripts/run_eval.py`) and is adopted only if it beats the default on held-out questions."

Quy tắc adoption một chiều: chỉ vào production khi beat default trên tập câu hỏi chưa từng thấy. Điểm cần ghi nhớ: eval có quyền nói **KHÔNG** với model "đẹp hơn" — đẹp hơn là tổng thể đẹp trên train, đẹp hơn là thuyết phục về mặt kỹ thuật; còn held-out là trọng tài duy nhất. Pipeline RAG nhiều dự án rơi vào vấn đề ngược lại: thêm model mới vào pipeline vì "nó mới hơn nó mạnh hơn", không có benchmark đóng để đối chiếu — mỗi quyết định kiến trúc là một cú bắn mù.

## Known failures: 6/93 hiện trong report, không giấu

Report ghi rõ 6 câu thất bại trên 93, chia theo loại — không phải footnote, mà là phần nội dung của `reports/eval_report.md`:

| Loại lỗi | Mô tả | Tỷ lệ trên loại đó |
| --- | --- | --- |
| Multi-hop | Cần ghép fact từ 2 documents khác nhau | ~40% câu multi-hop |
| Data-plate OCR | Ảnh low-contrast của data plate — OCR đọc sai | Câu cần data plate |
| Prose procedures | Câu hỏi diễn đạt khác manual quá nhiều | Vài câu procedure |
| Verifier false positive | Paraphrase mạnh làm lexical coverage rơi | ~12% trên answer sạch |

Mỗi lỗi được đối chiếu: multi-hop 40% thất bại là **giới hạn kiến trúc** của evidence selection hiện tại — nó theo cross-reference trong cùng document tốt, ghép hai document khác nhau chưa xử lý; data-plate OCR là **giới hạn OCR trên ảnh kém chất lượng**, không phải lỗi retrieval. Tách rõ từng loại là điều kiện để fix đúng chỗ — báo cáo giấu lỗi là báo cáo không dùng được để fix.

## Deployment: Docker Compose + Qdrant offline

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

## Lệnh benchmark và mở rộng pipeline

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

## Mini implementation: bootstrap CI + ECE/Brier

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

## Bài tập

**Làm theo:** Chạy code block trên. Sửa `n_boot` thành 20 rồi 500 — bootstrap CI thay đổi thế nào, n_boot 20 còn đáng tin để so sánh pipeline không, và vì sao? Ghi lại giá trị lo/hi của ba lần chạy.

**Tự sửa:** Thêm hàm `mrr(ranked_lists)` tính MRR từ danh sách rank của gold document trên 43 câu held-out: mỗi câu là list index vị trí gold (1-based); MRR = mean(1/rank đầu tiên gold xuất hiện). So với giá trị MRR 0.88 trong README — viết thêm assert kiểm MRR >= 0.8 trên tập giả lập có 40/43 câu gold rank 1 và 3 câu gold rank 2.

**Mở rộng:** Viết ablation mini: giả sử bạn có 3 channel với score riêng từng câu — chạy hai config (full pipeline và tắt một channel), dùng `bootstrap_ci` trên hiệu số accuracy giữa hai config để trả lời "channel này có đáng giữ không" thay vì nhìn điểm trung bình trần. Thêm vào đó một adoption gate: chỉ adopt config mới khi biên giới dưới của CI của nó cao hơn biên giới trên của default.

## Lỗi thường gặp

- **Đánh giá RAG bằng cảm giác sau mỗi thay đổi** → không có benchmark held-out đóng → sinh corpus + golden questions, tách train/test, chỉ so config trên held-out; không thêm model mới vì "thuyết phục về lý thuyết" khi chưa qua ablation.
- **Số benchmark cao hơn số thật khi deploy** → benchmark đo trên synthetic corpus, không phải manual thật → đọc report như đo kiến trúc; synthetic stress corpus ≠ production accuracy — kiểm tra lại trên bộ tài liệu thật của bạn trước khi hứa chất lượng với khách.
- **Qdrant rebuild toàn bộ collection sau mỗi upload lớn** → ingestion chưa incremental, mutation lớn tốn thời gian → chấp nhận ở quy mô demo/cá nhân; nếu cần incremental ingestion thật thì phải tách ingestion service — ghi rõ trong doc chứ không ngụ ý.
- **Container không gọi được Ollama trên host** → trong Docker, `localhost` là container → set `OPENAI_BASE_URL=http://host.docker.internal:11434/v1` và recreate service sau khi đổi `.env` (`docker compose up -d --no-build --force-recreate meridian`).
- **Bootstrap CI quá rộng để so sánh config** → số câu held-out quá nhỏ (10–20 câu) → tăng số câu held-out (43 trong benchmark này) hoặc tăng n_boot; n_boot không thay đổi độ hẹp CI thật — nó chỉ ổn định ước lượng, n câu held-out mới quyết định độ hẹp.

## FAQ

**Vì sao golden questions sinh cùng corpus mà không phải gán nhãn tay?**
Vì generator sinh câu hỏi từ chính document nó vừa tạo — ground truth chính xác tuyệt đối: answer facts đi kèm tolerance và unit, gold evidence xác định theo document + required phrases. Gán nhãn tay trên corpus thật tốn công, lệch người và không kiểm chứng được 'đây là câu trả lời đúng'. Trade-off rõ ràng: synthetic corpus ≠ real manuals — benchmark đo kiến trúc, không đo production accuracy.

**Learned ranker đẹp hơn sao không adopt?**
Vì nó không thắng hand-tuned weights trên held-out split. Adoption gate là quy tắc một chiều: ranker học chỉ được vào production khi beat default trên tập câu hỏi nó chưa từng thấy. Eval có quyền nói KHÔNG với model 'đẹp hơn' — benchmark đóng held-out nghĩa là không có lối tắt nào qua mô hình dễ nhìn.

**Qdrant có cần API key hay account không?**
Không. Qdrant self-hosted là free — Docker Compose start nó cùng Meridian, persist vector index trong volume qdrant-data. MERIDIAN_VECTOR_STORE=qdrant, MERIDIAN_QDRANT_URL default http://localhost:6333. Điểm cần nhớ: collection rebuild từ SQLite khi start và sau mỗi mutation — đây là ANN search cho vector, chưa phải incremental ingestion.

**Stress corpus 700 câu dùng để làm gì?**
Kiểm hành vi retrieval khi quy mô tăng: 100 generated notes → 700 chunks → 700 questions (600 answerable, 100 unanswerable), held-out theo model. Kết quả cho thấy độ khó tăng thật: Hit@1 65% so với 89.5% trên benchmark chính — và false abstention 10%. Đây là công cụ đo độ nhạy của ngưỡng, không phải bằng chứng production accuracy.

## Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) mục 6 (Evaluation design), mục 7 (Failure modes), mục 8 (Extending); [docs/DEPLOYMENT.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/DEPLOYMENT.md) toàn bộ (Docker, env vars, production notes); README Measured results + Larger synthetic stress benchmark
- Code trong bài: `meridian/eval/` (metrics.py, runner.py, report.py), `scripts/run_eval.py` (benchmark + trained ranker hook), `scripts/build_corpus.py`, `scripts/build_stress_corpus.py`, `docker-compose.yml` (Meridian + Qdrant volumes)
- Bài liền kề trong series: [Claim verifier bắt hallucination](/bai-viet/meridian-claim-verifier-hallucination/) · [Series bắt đầu: RAG bảo trì công nghiệp](/bai-viet/meridian-rag-bao-tri-cong-nghiep/)
- Từ blog cũ: [Đánh giá chất lượng RAG với Ragas](/bai-viet/danh-gia-chat-luong-rag-ragas/) — Ragas đánh giá sau khi hệ thống trả lời; benchmark trong bài đóng held-out và chấm cả retrieval lẫn calibration trước deploy

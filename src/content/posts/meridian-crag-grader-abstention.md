---
title: "CRAG grader và abstention: trả lời 'không biết' là tính năng, không phải lỗi"
description: "Grader CRAG-style đặt trước generation: IDF-weighted query-term coverage + late interaction, OOV handling, brand-term exclusion, corrective retry rồi abstain — 100% câu không trả lời được bị decline, false abstention chỉ 1.1% trên benchmark 93 câu."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-23"
cover: "/images/covers/posts/meridian-crag-grader-abstention.jpg"
featured: false
views: 355
faq:
  - q: "Vì sao grader đặt trước generation thay vì sau?"
    a: "Vì hallucination sinh ra khi generation chạy dù evidence không đủ. Grader rẻ, deterministic, chấm evidence trước — không đủ thì abstain; chi phí bỏ một câu trả lời nhỏ hơn nhiều chi phí một câu bịa. Chấm sau generation thì sai sót đã lọt qua composer."
  - q: "Từ khóa không có trong corpus bị xử lý thế nào?"
    a: "OOV được tính là từ hiếm nhất (log(1+n)) — kéo coverage xuống nặng. Nhưng nếu câu hỏi có anchor term cụ thể tìm thấy trong evidence, OOV coi như paraphrase và chỉ tính như từ hiếm bình thường; không anchor và OOV chiếm ≥30% trọng số → incorrect ngay."
  - q: "Vì sao 'Who is the CEO of Helix Dynamics?' bị từ chối?"
    a: "Analyzer trích entity 'Helix Dynamics' không có trong corpus — unknown-model refuse kích hoạt trước khi retrieval chạy. Trích thông tin về sản phẩm hay tổ chức không có documentation là hành vi nguy hiểm nhất của hệ thống hỏi đáp, nên pipeline refuse ngay thay vì trả lời thay."
  - q: "Abstention 10% trên stress set có quá nhiều không?"
    a: "Phụ thuộc nghiệp vụ. 100% unanswerable decline và faithfulness 100% là ưu tiên của hệ thống bảo trì công nghiệp; false abstention 10% trên corpus stress 700 câu có wording noise là chi phí của ngưỡng hand-tuned. Giám sát cả hai hướng và chỉnh ngưỡng theo tập answerable thực tế của bạn."
---

RAG demo luôn trả lời — kể cả khi evidence không đủ. Hỏi "Who is the CEO of Helix Dynamics?" trên corpus tài liệu bảo trì: không có CEO nào, không có Helix Dynamics nào, nhưng demo thông thường vẫn sinh ra một câu trông mượt với số liệu bịa. Hallucination sinh ra từ đúng chỗ này: pipeline cho phép generation chạy dù evidence không hỗ trợ. Lỗi không nằm ở mô hình ngôn ngữ; nó nằm ở quyết định thiết kế.

Meridian đặt grader TRƯỚC generation: đánh giá evidence có đủ hỗ trợ câu hỏi hay không bằng phép tính rẻ, deterministic; không đủ thì retry, vẫn không đủ thì abstain. Trích từ bảng Decisions trong ARCHITECTURE:

> "Grader before generation — cheap, deterministic abstention is safer than asking a generator to 'say I don't know'."

## Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **CRAG** | Corrective RAG — chấm điểm evidence trước generation, sửa lỗi truy xuất rồi mới quyết định trả lời hay từ chối |
| **Grader verdict** | correct / ambiguous / incorrect — evidence đủ / mập mờ / không đủ hỗ trợ |
| **IDF coverage** | Tỷ lệ thuật ngữ câu hỏi được evidence hỗ trợ, có trọng số IDF — từ hiếm quan trọng hơn từ phổ biến |
| **OOV** | Out-of-vocabulary — thuật ngữ không có trong corpus; được xử lý theo anchor logic, không mặc định là tin xấu |
| **Anchor term** | Thuật ngữ cụ thể của câu hỏi được tìm thấy trong evidence — chứng tỏ câu hỏi "đậu" vào đúng chủ đề |
| **Brand-term exclusion** | Tên hệ thống, tên model, từ branding trong tiêu đề tài liệu không tính vào coverage — chúng nói không gì về chủ đề |
| **Abstention** | Từ chối trả lời có kiểm soát, kèm lý do hiển thị trong trace |

## Grader chấm điểm evidence trước khi viết câu trả lời

`retrieval/grader.py` lấy top 4 candidates của retrieval (bài [8 kênh hybrid retrieval](/bai-viet/meridian-hybrid-retrieval-8-kenh/) đã đi qua pipeline đó) và tính ba tín hiệu:

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

## OOV handling và brand-term exclusion

Hai chi tiết của grader quyết định chất lượng abstention nhiều hơn mọi ngưỡng.

**OOV không mặc định là tin xấu.** Thuật ngữ không có trong corpus được gán trọng số của từ hiếm nhất (`log(1 + n)`) — kéo coverage xuống nặng. Nhưng có ngoại lệ: nếu câu hỏi có ít nhất một anchor term cụ thể được tìm thấy trong evidence, thuật ngữ OOV được coi như paraphrase và chỉ tính như một từ hiếm bình thường. Nếu không có anchor nào và phần trọng số OOV vượt 30% tổng, grader tuyên bố incorrect ngay với lý do hiển thị rõ: "key term(s) that appear in no indexed document".

**Brand terms không nói gì về chủ đề.** Thuật ngữ trùng với tiêu đề tài liệu (branding, document-type words) và token tên model đang hỏi bị loại khỏi tính coverage. Nếu không loại, câu hỏi "What is the HX-200 torque?" được điểm mượt chỉ vì evidence chứa chuỗi "HX-200" — một tín hiệu giả về độ đủ evidence. Danh sách từ GENERIC ("give", "tell", "need"...) cũng bị loại — không mang tín hiệu answerability.

## Corrective loop và unknown-model refuse

Verdict incorrect không kết thúc ngay — CRAG-style corrective loop:

1. Retry truy xuất với **relaxed model filter** — evidence đúng có thể nằm ở tài liệu bị model filter loại lần đầu.
2. Rewrite câu hỏi **keyword-only** — bỏ cấu trúc câu, giữ thuật ngữ discriminative.
3. Vẫn incorrect → **ABSTAIN** kèm lý do trong trace.

Trước grader còn một lối thoát sớm hơn: **unknown-model refuse**. Analyzer trích model/entity từ câu hỏi; nếu câu hỏi nhắc model không tồn tại trong corpus, pipeline refuse NGAY — không bao giờ trả lời thay cho sản phẩm khác. Đây là lý do demo "Who is the CEO of Helix Dynamics?" abstain: "Helix Dynamics" là một entity không có documentation nào, và trích thông tin về nó từ corpus sai chủ đề là hành vi nguy hiểm nhất của một hệ thống hỏi đáp — nguy hiểm hơn cả refuse.

## Evidence selection: theo cross-reference, gắn WARNING

Grader quyết định "trả lời hay không"; lớp evidence selection quyết định "đưa cái gì vào generation" (`retrieval/context.py`):

- **Follow cross-reference**: chunk ghi "see Table 4" — hệ thống theo tham chiếu tới đúng ROW của bảng đó trong index, không dừng ở câu nói "see Table 4". Composer nhận giá trị thật của hàng, không nhận lời hứa tham chiếu.
- **Attach WARNING chunks cùng section**: nếu chunk chứa câu trả lời thuộc cùng section với warning box, warning được gắn vào context. Câu trả lời kỹ thuật không bao giờ thiếu cảnh báo an toàn chỉ vì warning nằm ở một chunk khác.

Hai cơ chế này trả lời câu hỏi mà top-k thuần không trả lời được: evidence đưa vào generation có phản ánh đúng nghĩa tài liệu gốc, hay chỉ phản ánh thứ tự rank của retrieval.

## Benchmark: cân bằng refuse và false abstention

Từ chối là con dao hai lưỡi — refuse quá nhiều là hệ thống vô dụng. Số liệu đo được:

| Chỉ số | Benchmark chính (93 câu) | Stress set (100 notes, 700 câu) |
| --- | --- | --- |
| Unanswerable declined | 100% | 100% |
| False abstention trên answerable | 1.1% | 10.0% |
| Answer correctness (unit-aware) | 93.1% overall, 92.5% held-out | 90.0% (held-out theo model) |

Stress set false abstention 10% cho thấy chi phí của ngưỡng hand-tuned khi corpus lớn và wording noise tăng. Hướng đối chiếu vẫn rõ: 100% unanswerable decline + faithfulness 100% claims supported là ưu tiên của hệ thống bảo trì công nghiệp — sai số nằm ở câu trả lời có kiểm soát, không ở câu bịa.

## Mini implementation: idf_coverage_grader

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

# 1. câu hỏi có thật, evidence khớp → correct
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

## Bài tập

**Làm theo:** Chạy code block trên và đoán giá trị coverage trước khi xem output. Thay evidence của case 1 bằng `chunks_corpus[1:2]` (chunk lubrication) — coverage giảm thế nào, verdict đổi thành gì, và thuật ngữ nào xuất hiện trong `missing`.

**Tự sửa:** Thêm cấu trúc evidence để simulate brand-term exclusion: đọc tiêu đề tài liệu từ trường riêng của mỗi chunk và loại thuật ngữ trùng tiêu đề khỏi danh sách tính coverage thay vì dùng hằng số BRAND.

**Mở rộng:** Viết corrective loop: hàm nhận verdict incorrect, thực hiện một lần retry với rewritten query (bỏ stop words, giữ thuật ngữ IDF cao nhất) rồi gọi lại grader; cap hai vòng — vẫn incorrect thì trả về ABSTAIN kèm lý do. Nối với bài [Fact index và conflict resolution](/bai-viet/meridian-fact-index-conflict-resolution/) để retry dùng fact channel trước khi fallback keyword-only.

## Lỗi thường gặp

- **Hệ thống abstain quá nhiều** → ngưỡng 0.62 đặt cho corpus có IDF floor cao hoặc evidence depth thấp → đo false abstention trên tập answerable của bạn, hạ THRESH_CORRECT hoặc tăng depth evidence trước khi đổi threshold.
- **OOV từ hiếm kéo coverage chết dù câu hỏi hợp lệ** → thiếu anchor logic → kiểm tra `anchored` có được tính trên thuật ngữ cụ thể (không phải GENERIC) hay không; paraphrase hợp lệ phải được nới lỏng như case 3 trong code.
- **Coverage mượt vì brand term** → chưa loại title_terms và token tên model → câu hỏi nhắc tên model được điểm cao từ tín hiệu giả; loại theo tiêu đề tài liệu, không theo hằng số cứng.
- **Câu trả lời thiếu cảnh báo an toàn** → evidence chỉ lấy top-k thuần → bật cross-reference following và warning expansion cùng section như `retrieval/context.py`; kiểm tra trong trace xem WARNING chunk có được attach không.
- **Retry vô hạn khi evidence trượt bền bỉ** → corrective loop không có cap → cap số vòng (relaxed filter rồi keyword rewrite rồi abstain); mỗi vòng retry phải ghi lý do vào trace để không restart ngầm.

## FAQ

**Vì sao grader đặt trước generation thay vì sau?**
Vì hallucination sinh ra khi generation chạy dù evidence không đủ. Grader rẻ, deterministic, chấm evidence trước — không đủ thì abstain; chi phí bỏ một câu trả lời nhỏ hơn nhiều chi phí một câu bịa. Chấm sau generation thì sai sót đã lọt qua composer.

**Từ khóa không có trong corpus bị xử lý thế nào?**
OOV được tính là từ hiếm nhất (log(1+n)) — kéo coverage xuống nặng. Nhưng nếu câu hỏi có anchor term cụ thể tìm thấy trong evidence, OOV coi như paraphrase và chỉ tính như từ hiếm bình thường; không anchor và OOV chiếm ≥30% trọng số → incorrect ngay.

**Vì sao 'Who is the CEO of Helix Dynamics?' bị từ chối?**
Analyzer trích entity 'Helix Dynamics' không có trong corpus — unknown-model refuse kích hoạt trước khi retrieval chạy. Trích thông tin về sản phẩm hay tổ chức không có documentation là hành vi nguy hiểm nhất của hệ thống hỏi đáp, nên pipeline refuse ngay thay vì trả lời thay.

**Abstention 10% trên stress set có quá nhiều không?**
Phụ thuộc nghiệp vụ. 100% unanswerable decline và faithfulness 100% là ưu tiên của hệ thống bảo trì công nghiệp; false abstention 10% trên corpus stress 700 câu có wording noise là chi phí của ngưỡng hand-tuned. Giám sát cả hai hướng và chỉnh ngưỡng theo tập answerable thực tế của bạn.

## Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) mục 2 (corrective retries trong flow diagram) và mục 5 (Grader); README bảng "Why it is different" và Measured results
- Code trong bài: `meridian/retrieval/grader.py` (grade, GENERIC, OOV/anchor logic, brand-term exclusion), `meridian/retrieval/context.py` (cross-reference following, warning expansion), `meridian/agent/agent.py` (corrective loop, unknown-model refuse)
- Bài liền kề trong series: [Fact index và conflict resolution](/bai-viet/meridian-fact-index-conflict-resolution/) · [Claim verifier bắt hallucination](/bai-viet/meridian-claim-verifier-hallucination/)
- Từ blog cũ: [Đánh giá chất lượng RAG với Ragas](/bai-viet/danh-gia-chat-luong-rag-ragas/) — grader trong bài là đánh giá đặt trong pipeline trước generation; Ragas đánh giá sau khi hệ thống đã trả lời

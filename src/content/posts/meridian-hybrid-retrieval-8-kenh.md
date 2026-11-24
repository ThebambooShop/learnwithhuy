---
title: "8 kênh hybrid retrieval: từ BM25 đến graph — hợp nhất bằng weighted RRF"
description: "8 kênh retrieval (BM25, LSA dense, char-n-gram, entity, fact, visual, PRF, graph) hợp nhất bằng weighted RRF rồi rerank MaxSim trên 17 features: full pipeline đạt Hit@1 89.5% trên held-out so với BM25 alone 84.2%."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-23"
cover: "/images/covers/posts/meridian-hybrid-retrieval-8-kenh.jpg"
featured: false
views: 340
faq:
  - q: "Vì sao RRF bỏ qua score gốc của từng kênh?"
    a: "BM25 score, cosine LSA và fact score không cùng thang đo — cộng trực tiếp sẽ làm một kênh lấn át. RRF chỉ dùng rank: mỗi chunk nhận w_k/(60+rank_k) từ mỗi kênh; chunk được nhiều kênh đồng thuận nhảy lên đầu, bất kể thang đo gốc."
  - q: "Trọng số 8 kênh chọn thế nào?"
    a: "Hand-tuned: bm25 1.0, fact 1.0, visual 1.0, entity 0.9, dense 0.55, graph 0.5, prf 0.45, char 0.30. Nguyên tắc: kênh chính xác cao (exact match code, fact có unit) nặng hơn kênh mềm. Learned LTR chỉ được adopt khi thắng default trên held-out — trong benchmark nó không thắng nên giữ weights tay."
  - q: "17 features của feature ranker gồm gì?"
    a: "rrf, bm25, dense, char, late, entity, fact, modality, model_match, q_cov, section_overlap, is_row, is_warning, is_bulletin, graph, visual, prf — kết hợp score từng kênh với tín hiệu cấu trúc: modality prior theo intent, chunk là table row hay warning hay bulletin."
  - q: "Hybrid retrieval có phải ma thuật không?"
    a: "Không. Trên benchmark 43 câu held-out, full pipeline đạt Hit@1 89.5% so với BM25 alone 84.2% (+5.3 điểm) và Hit@5 đều đạt 100%. Phần giá trị lớn còn lại nằm ở grader, verifier và abstention — retrieval chỉ là một lớp."
---

Một vector search không đủ cho corpus bảo trì công nghiệp. Câu hỏi *What torque for the HX-200 impeller bolt?* cần khớp chính xác "HX-200" — dense retrieval bỏ sót số hiệu. Câu hỏi paraphrase *bơm quá nhiệt xử lý thế nào?* cần hiểu ngữ nghĩa — BM25 trượt nếu corpus dùng từ khác. Ảnh chụp panel có OCR typo "E4T" thay "E47" — cả hai đều trượt. Không có một kênh nào thắng mọi loại lỗi.

Vì vậy Meridian chạy **8 kênh song song**, hợp nhất bằng weighted RRF, rerank theo late interaction + 17 features, rồi MMR. Benchmark cho thấy full pipeline đạt **Hit@1 89.5%** trên held-out, BM25 alone 84.2%. Bài này đi qua từng kênh — nó giải quyết lỗi gì — với hằng số thật từ `retrieval/pipeline.py`.

## Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **BM25 field-boosted** | Lexical retrieval tự viết, boost title/section/content/entities |
| **LSA dense** | Embedding offline: TF-IDF → SVD, không cần model download |
| **Weighted RRF** | Reciprocal Rank Fusion có trọng số per-channel: chỉ dùng rank, bỏ score gốc |
| **Late interaction / MaxSim** | Rerank kiểu ColBERT: mỗi query token khớp token tốt nhất trong chunk |
| **MMR** | Maximal Marginal Relevance — khử near-duplicate sau khi xếp hạng |
| **Model filtering** | Mask document level theo model trong câu hỏi — không cho passage sai model lọt qua |

## 8 kênh — mỗi kênh bù một loại lỗi

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

## Fusion: weighted RRF → rerank → MMR

Mỗi kênh trả top **pool = 60**. Weighted RRF hợp nhất:

$$\text{RRF}(d) = \sum_{c} \frac{w_c}{k + \text{rank}_c(d)}, \quad k = 60$$

Chunk được nhiều kênh đồng thuận có lợi thế cấu trúc: hạng 3 ở 4 kênh thường thắng hạng 1 ở 1 kênh. Top **40** vào rerank theo ba tầng:

1. **Late interaction (MaxSim):** mỗi query token khớp token tốt nhất trong chunk — exact stem match 1.0, fuzzy match (cutoff 0.86) 0.75, cosine trên LSA term vectors scale `((cos − 0.55) / 0.45) · 0.7`; tổng hợp theo IDF weight. Matching fine-grained kiểu ColBERT mà hoàn toàn offline.
2. **Feature ranker 17 features:** ghép score từng kênh với tín hiệu cấu trúc. Default weights hand-tuned: `rrf 0.30, late 0.28, fact 0.18, bm25 0.15, entity 0.14, modality 0.14, q_cov 0.12, visual 0.12, dense 0.10, section_overlap 0.08, graph 0.05, model_match 0.06, char 0.04, prf 0.03, is_bulletin 0.02`, còn `is_row`, `is_warning` = 0. Learned logistic-regression ranker train qua `scripts/run_eval.py` nhưng **chỉ được adopt khi thắng default trên held-out** — trong benchmark nó không thắng.
3. **MMR λ = 0.82:** chỉ phạt near-duplicate cùng modality cùng document (cosine > 0.88) — giữ diversity khi bảng n chữ số đưa ra 30 hàng giống nhau.

> **Định nghĩa:** Weighted RRF tổng đóng góp theo vị trí — `w/(k+rank)` — không phải tổng score; hợp nhất được 8 kênh có thang đo không tương thích mà không cần chuẩn hoá.

## Model filtering: điều kiện cứng ở document level

Trước cả fusion: khi query analysis nhận diện model (HX-500), retrieval áp mask **ở document level** — chunk thuộc document của model khác bị loại khỏi mọi kênh. Passage HX-500 không bao giờ được trả lời câu hỏi HX-200, dù từ ngữ giống nhau đến mức nào.

Filter là điều kiện cứng: chunk "gần đúng" của model sai vẫn bị loại dù score cao. Nếu retrieval trả passage HX-500 với torque 52 Nm cho câu hỏi về HX-200 (spec 45 Nm), phần verify sửa được câu chữ nhưng không sửa được sai số liệu đã vào context.

## Ablation: hybrid thêm nhiều nhưng không phải ma thuật

Benchmark synthetic đi kèm repo: 93 câu hỏi, 43 held-out. Trên held-out:

| Cấu hình | Hit@1 | Hit@5 | MRR |
| --- | --- | --- | --- |
| BM25 alone | 84.2% | 97.4% | — |
| **Full pipeline (8 kênh + rerank + MMR)** | **89.5%** | **100%** | **0.88** |

Đọc đúng số: full pipeline chỉ hơn BM25 alone **+5.3 điểm Hit@1**. Kênh bổ sung không phải phép màu — phần lớn chất lượng đến từ lớp sau retrieval: CRAG grader, conflict resolution, verifier, abstention (100% declined unanswerable, faithfulness 100%).

Repo kèm sẵn **ablation preset** — `bm25`, `dense`, `hybrid_rrf`, `hybrid+entity+fact`, `+prf+graph`, `+late_rerank`, `full` — mỗi preset bật tắt một nhóm kênh; đo per-config thay vì đoán.

Chủ đề RRF này blog cũ đã có bài riêng: [Hybrid Search với BM25, Dense Retrieval và RRF](/bai-viet/hybrid-search-bm25-dense-rrf/) — cùng công thức k=60 SIGIR 2009, nhưng chưa weighted per-channel và chưa có rerank phía sau.

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

## Bài tập

**Làm theo:** Chạy code block, đối chiếu tay từng score trong comment. Đổi `k=60` thành `k=1` rồi `k=100`: k=1 cho hạng 1 áp đảo hoàn toàn; k lớn làm các hạng gần nhau hơn.

**Tự sửa:** Thêm kênh `fact` (weight 1.0) và `graph` (0.5) như Meridian; cho `hx500_chart` đứng hạng 1 ở `fact`. Tính tay score ba chunk, đối chiếu output, rồi trả lời: nâng weight kênh nào sẽ đưa `hx500_chart` lên hạng 1?

**Mở rộng:** Implement mini late-interaction: mỗi query token score exact match 1.0 / fuzzy (`difflib.get_close_matches`, cutoff 0.86) 0.75 / miss 0.0, cộng theo IDF weight. Ghép vào feature dict cùng RRF score và tính linear score với default weights — phiên bản thu gọn của tầng rerank trong `rerank.py`.

## Lỗi thường gặp

| Biểu hiện | Nguyên nhân | Xử lý |
| --- | --- | --- |
| Kết quả đổi khi bật/tắt kênh, không biết kênh nào gây nhiễu | Thay nhiều biến cùng lúc | Dùng ablation preset và đo per-config trên cùng bộ câu hỏi có ground truth |
| Chunk đúng nhưng model sai được trả về | Model filtering chưa bật hoặc query analysis không nhận diện model | Bật `model_filter` để mask document level; kiểm tra `analysis.models` trước |
| PRF làm kết quả trôi topic | Expansion terms quá nhiều hoặc trùng terms đã có | Giữ 6 terms, weight 0.25, loại terms đã có trong query và terms số — như pipeline.py làm |
| Rerank chậm trên corpus lớn | Late interaction chạy trên depth lớn | Giảm `rerank_depth` (40) trước khi giảm kênh — fusion RRF rẻ, rerank tốn |
| Learned ranker "tốt hơn" trên train nhưng tụt trên held-out | Overfit | Chỉ adopt khi thắng default trên held-out — Meridian train rồi vẫn không adopt |

## FAQ

**Vì sao RRF bỏ qua score gốc của từng kênh?**
BM25 score, cosine LSA và fact score không cùng thang đo — cộng trực tiếp sẽ làm một kênh lấn át. RRF chỉ dùng rank: mỗi chunk nhận `w_k/(60+rank_k)` từ mỗi kênh; chunk được nhiều kênh đồng thuận nhảy lên đầu, bất kể thang đo gốc.

**Trọng số 8 kênh chọn thế nào?**
Hand-tuned: bm25 1.0, fact 1.0, visual 1.0, entity 0.9, dense 0.55, graph 0.5, prf 0.45, char 0.30. Nguyên tắc: kênh chính xác cao (exact match code, fact có unit) nặng hơn kênh mềm. Learned LTR chỉ được adopt khi thắng default trên held-out — trong benchmark nó không thắng nên giữ weights tay.

**17 features của feature ranker gồm gì?**
rrf, bm25, dense, char, late, entity, fact, modality, model_match, q_cov, section_overlap, is_row, is_warning, is_bulletin, graph, visual, prf — kết hợp score từng kênh với tín hiệu cấu trúc: modality prior theo intent, chunk là table row hay warning hay bulletin.

**Hybrid retrieval có phải ma thuật không?**
Không. Trên benchmark 43 câu held-out, full pipeline đạt Hit@1 89.5% so với BM25 alone 84.2% (+5.3 điểm) và Hit@5 đều đạt 100%. Phần giá trị lớn còn lại nằm ở grader, verifier và abstention — retrieval chỉ là một lớp.

## Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — README (Measured results) và [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) mục 4
- Code: `meridian/retrieval/pipeline.py` (8 kênh, weighted RRF, MMR), `meridian/retrieval/rerank.py` (late interaction, 17 features)
- Bài liền kề trong series: [Chart digitiser đọc số liệu từ biểu đồ](/bai-viet/meridian-chart-digitiser-doc-bieu-do/) · [Fact index và conflict resolution](/bai-viet/meridian-fact-index-conflict-resolution/) · [CRAG grader và abstention](/bai-viet/meridian-crag-grader-abstention/)
- Từ blog cũ: [Hybrid Search với BM25, Dense Retrieval và RRF](/bai-viet/hybrid-search-bm25-dense-rrf/) — cùng chủ đề RRF

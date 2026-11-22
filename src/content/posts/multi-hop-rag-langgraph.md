---
title: "Multi-hop RAG: suy luận bắc cầu qua nhiều văn bản với LangGraph cho tài liệu tiếng Việt"
description: "Thiết kế Multi-hop RAG lặp trên LangGraph: phân rã câu hỏi, trích xuất thực thể cầu nối, khử đại từ, phát hiện mâu thuẫn văn bản, và kết quả benchmark 19/20 ca so với Plain RAG."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-17"
cover: "/images/covers/posts/multi-hop-rag-langgraph.jpg"
views: 480
---

Tìm kiếm đơn bước (Single-hop RAG) gặp hạn chế lớn khi xử lý truy vấn pháp lý đòi hỏi suy luận bắc cầu qua nhiều văn bản: *Thực thể X → thực thể trung gian Y → văn bản quy định Z*. Do hiện tượng đứt gãy liên kết ngữ nghĩa và khuyết ngữ cảnh đại từ chỉ định, mô hình khó thu hồi đủ văn bản đích — làm giảm tỷ lệ hồi tưởng chuỗi và tăng rủi ro sinh ảo giác pháp lý.

**Khi nào nên dùng Multi-hop RAG:**

- Ngữ liệu có cấu trúc phân mảnh và liên kết bắc cầu (pháp luật, y khoa, hồ sơ kỹ thuật)
- Câu hỏi chứa đại từ quy chiếu cần khử nhập nhằng và bóc tách thực thể cầu nối
- Hệ thống yêu cầu kiểm soát xung đột (Contradiction Check) và trích dẫn căn cứ minh bạch
- Cần kiểm soát chặt từng bước nhảy suy luận để phục vụ truy vết và giải trình

**Không nên dùng khi:** câu hỏi đơn giản, thông tin nằm trọn vẹn trong một điều khoản đơn lẻ; hoặc yêu cầu độ trễ dưới 1 giây trên kho tài liệu độc lập, phẳng.

## Bốn khái niệm nền tảng

| Khái niệm | Là gì |
| --- | --- |
| **Semantic gap** (đứt gãy liên kết ngữ nghĩa) | Single-hop RAG chỉ tìm một lượt: khi câu hỏi bắc cầu, công cụ tìm kiếm nhận diện được thực thể ban đầu nhưng chưa xác định được thực thể trung gian Y để thu hồi văn bản điều chỉnh Z |
| **Bridge entity extraction** | Kỹ thuật bóc tách danh từ hoặc cụm định nghĩa của thực thể trung gian từ văn bản thu hồi ở Hop 0 — dùng làm cầu nối logic cho truy vấn của Hop 1 |
| **Coreference resolution** | Phân tích mệnh đề phụ thuộc trong chuỗi câu hỏi con, nhận diện đại từ quy chiếu ("nhóm đó", "loại này") rồi thay bằng tên thực thể chuẩn xác đã trích xuất ở Hop 0 |
| **Contradiction detection** | Phân tích văn bản thu hồi để phát hiện xung đột giữa các quy định (một văn bản nghiêm cấm, một văn bản cho phép theo điều kiện) → kích hoạt cảnh báo thay vì tự động suy diễn |

## Kiến trúc luồng xử lý trên LangGraph

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

## Thiết lập môi trường

```bash
git clone https://github.com/tnt305/multi-hop-rag.git
cd multi-hop-rag

# Khởi tạo môi trường Conda từ file cấu hình chuẩn
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

## Các module cốt lõi

### Module 1 — HybridRetriever

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

### Module 2 — Bridge & Anaphora

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

### Module 3 — Evidence Assessment & Contradiction Detection

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

### Module 4 — Lắp ráp StateGraph

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

## Kết quả thực nghiệm

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

## Ba kịch bản ứng dụng thực tế

1. **Tra cứu quy định hành chính:** Hop 0 xác định văn bản ủy quyền là văn bản hành chính theo Nghị định 30/2020/NĐ-CP → Hop 1 thu hồi các điều khoản về thể thức và thẩm quyền ký ban hành.
2. **Thẩm định điều kiện cấp phép:** tra cứu định nghĩa hoạt động khảo nghiệm (Luật Thú y) trước khi xác định quy chuẩn kỹ thuật và thông tư điều chỉnh (Thông tư 13/2016/TT-BNNPTNT) — hệ thống xâu chuỗi hai nguồn để tạo căn cứ hoàn chỉnh.
3. **Phát hiện xung đột và hiệu lực văn bản:** hai văn bản thuộc thời kỳ hoặc cơ quan khác nhau trái ngược về cùng một hành vi → hệ thống phát hiện mệnh đề đối lập và cảnh báo, hỗ trợ chuyên viên pháp chế nắm điểm mâu thuẫn trước khi ban hành văn bản áp dụng.

## Lỗi thường gặp và cảnh báo biên

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

## Bài liên quan

- Trước đó: [GraphRAG: từ văn bản tới Knowledge Graph](/bai-viet/graphrag-knowledge-graph/)
- Cơ chế Hybrid Retriever chi tiết: [Hybrid Search với BM25, Dense Retrieval và RRF](/bai-viet/hybrid-search-bm25-dense-rrf/)

## Nguồn

- Mã nguồn: [multi-hop-rag (repo thực hành)](https://github.com/tnt305/multi-hop-rag)
- Nghiên cứu nền: HotpotQA (EMNLP 2018), Dense Passage Retrieval (EMNLP 2020), BGE M3-Embedding (arXiv:2402.03216), Query2Doc (EMNLP 2023), AutoGen (arXiv:2308.08155)
- Nội dung biên tập lại từ bài thực hành Multi-hop RAG của AI Guru x TiniX theo phong cách LearnWithHuy; kết quả benchmark trên bộ dữ liệu tổng hợp cố định, chưa đại diện cho dữ liệu pháp luật thực tế.

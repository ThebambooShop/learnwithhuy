---
title: "Đánh giá chất lượng hệ thống RAG với Ragas: 4 độ đo, Golden Dataset và 5 lỗi thường gặp"
description: "Hướng dẫn đánh giá hệ thống RAG bằng Ragas: Context Precision, Context Recall, Faithfulness, Answer Relevancy — so sánh 2 cấu hình chunk size thực tế và phân tích 5 lỗi RAG phổ biến."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-17"
cover: "/images/covers/posts/danh-gia-chat-luong-rag-ragas.jpg"
views: 470
faq:
  - q: "Thử nghiệm vài câu hỏi bằng mắt có đủ để đánh giá RAG không?"
    a: "Không đủ khi đưa ứng dụng vào production. Cần phương pháp đánh giá tự động với Golden Dataset (tập cặp câu hỏi – đáp án chuẩn) và thư viện Ragas để đo 4 độ đo một cách nhất quán, so sánh được giữa các cấu hình."
  - q: "Chạy Ragas có cần API key trả phí không?"
    a: "Không bắt buộc. Có thể dùng mô hình local qua Ollama (ví dụ Gemma2) và HuggingFace Embeddings — miễn phí và dữ liệu không gửi ra ngoài. Khi cần hệ quy chiếu ổn định hơn để chấm điểm, có thể thay bằng GPT-4 làm giám khảo, nhưng chi phí API có thể đáng kể."
  - q: "Nên cắt văn bản thành chunk nhỏ hay lớn?"
    a: "Mỗi cách có trade-off: chunk nhỏ (250 ký tự) cho Context Precision cao nhưng Recall thấp do thiếu ngữ cảnh lân cận; chunk lớn (1000 ký tự) cho Recall cao hơn nhưng dễ trượt ý. Chiến lược khắc phục triệt để là Parent-Child Retrieval: nhúng chunk nhỏ để lấy Precision, trả về chunk lớn để lấy Recall."
---

Bạn đã xây được một hệ thống RAG cơ bản. Nhưng làm sao biết nó thực sự "thông minh"? Việc chỉ thử nghiệm 3–5 câu hỏi bằng mắt thường là không đủ khi đưa ứng dụng vào môi trường thực tế. Cần một phương pháp đánh giá tự động và toàn diện: xây dựng **Golden Dataset** và dùng thư viện **Ragas** để đo lường các độ đo.

Toàn bộ quy trình trong bài chạy local, miễn phí, không cần API key trả phí (yêu cầu: RAM tối thiểu 8GB, Python 3.9+, Ollama với mô hình Gemma2, thư viện `ragas`).

## Thuật ngữ cơ bản

| Thuật ngữ | Định nghĩa |
| --- | --- |
| **Ground Truth** | Đáp án đúng chuẩn do con người viết sẵn — thước đo chuẩn mực cho hệ thống |
| **Golden Dataset** | Tập dữ liệu "vàng" gồm các cặp (Câu hỏi, Ground Truth) dùng để kiểm thử |
| **LLM-as-a-Judge** | Dùng một LLM mạnh làm giám khảo chấm điểm câu trả lời do chatbot sinh ra, thay con người |
| **Ragas** | Thư viện mã nguồn mở chuyên đo lường chất lượng hệ thống RAG dựa trên LLM-as-a-Judge |
| **NLI** | Natural Language Inference — bài toán xác định một giả thuyết có được suy ra từ một tiền đề hay không; Ragas dùng NLI để kiểm tra tính logic của câu trả lời |

## Lý thuyết: hai thành phần cần đánh giá

Đánh giá RAG phải tách thành hai thành phần độc lập: **Hệ thống truy xuất (Retrieval)** và **Khả năng sinh văn bản (Generation)**. Nếu Retrieval lấy về rác, Generation chắc chắn sinh ra rác (Garbage in, Garbage out). Ngược lại, Retrieval lấy về thông tin vàng nhưng Generation bị ảo giác — hệ thống vẫn thất bại.

Luồng đánh giá: Câu hỏi → Truy xuất → Ngữ cảnh → Sinh trả lời → Câu trả lời. **Context Precision** và **Context Recall** đánh giá tầng Retrieval; **Faithfulness** và **Answer Relevancy** đánh giá tầng Generation.

### A. Context Precision — độ chính xác của ngữ cảnh

Câu hỏi trả lời: *trong các đoạn văn lấy về, đoạn chứa đáp án có được xếp ở vị trí ưu tiên cao nhất không?* Ragas tính dựa trên Mean Average Precision:

$$\text{Context Precision@K} = \frac{\sum_{k=1}^{K} \left(\text{Precision@}k \times v(k)\right)}{\text{Tổng số chunks có liên quan}}$$

**Ví dụ:** tìm "Điều kiện cấp sổ đỏ lần đầu theo Luật Đất đai 2024", hệ thống trả về 3 kết quả — hai kết quả đầu không liên quan, kết quả liên quan nằm tuốt vị trí cuối. Độ đo MAP phạt rất nặng cấu hình này: Context Precision rơi xuống khoảng 1/3. Để đạt 1.0 tuyệt đối, đoạn liên quan bắt buộc phải ở vị trí số 1.

### B. Context Recall — độ bao phủ của ngữ cảnh

Câu hỏi trả lời: *các đoạn văn lấy về có đủ tất cả các ý cần thiết để trả lời y hệt đáp án chuẩn không?* Độ này tập trung vào độ đầy đủ hơn là thứ tự xếp hạng:

$$\text{Context Recall} = \frac{\text{Số câu trong Ground Truth có mặt trong Context}}{\text{Tổng số câu của Ground Truth}}$$

Cơ chế của Ragas: LLM-giám-khảo đọc Ground Truth, chia thành từng ý (statements), rồi dò xem từng ý có xuất hiện trong context hay không. Ví dụ: đáp án chuẩn liệt kê 7 loại đất, nhưng chunk_size quá nhỏ khiến hệ thống chỉ lấy về đoạn nói về 4 loại đầu — Ragas đếm được 4/7 ý, Context Recall ≈ 0.57.

### C. Faithfulness — độ trung thành

Câu hỏi trả lời: *mô hình AI có "bịa" ra thông tin ngoài những gì được cung cấp trong tài liệu không?* Quá trình gồm 2 bước suy luận NLI: **trích xuất ý** (phân tách câu trả lời thành danh sách mệnh đề ngắn) → **xác thực** (đối chiếu từng mệnh đề với context xem có được suy ra hay không).

$$\text{Faithfulness} = \frac{\text{Số mệnh đề được suy ra từ Context}}{\text{Tổng số mệnh đề trong câu trả lời}}$$

**Ví dụ:** ngữ cảnh ghi "Thời hạn giao đất nông nghiệp là 50 năm", nhưng LLM trả lời thêm "và sau khi hết hạn sẽ phải nộp phí gia hạn 10 triệu đồng". Mệnh đề thứ hai không hề có trong ngữ cảnh — dù quy định thực tế có như vậy hay không, hệ thống RAG vẫn coi đây là Hallucination nghiêm trọng. Faithfulness giảm xuống 0.5.

### D. Answer Relevancy — độ liên quan của câu trả lời

Đo xem câu trả lời có trực tiếp giải quyết vấn đề hay trả lời lan man. Thú vị là Ragas **không so sánh trực tiếp** — nó làm ngược lại: dùng LLM sinh ra các *câu hỏi dự đoán* dựa trên câu trả lời, rồi đo khoảng cách Cosine giữa câu hỏi gốc và các câu hỏi dự đoán.

**Ví dụ:** hỏi về "Quy định bồi thường đất" nhưng câu trả lời dài dòng giải thích "Lịch sử Luật đất đai từ 1993" — câu hỏi sinh ngược chứa từ khóa về lịch sử, khoảng cách Cosine với câu hỏi gốc giảm mạnh.

## Thực hành: đánh giá với 2 cấu hình

Chạy đánh giá thực tế trên 2 cấu hình để thấy rõ sự biến động của các độ đo:

- **Cấu hình 1:** chunk_size = 250, top_k = 2 (cắt nhỏ, lấy vừa phải)
- **Cấu hình 2:** chunk_size = 1000, top_k = 2 (cắt lớn, giữ nguyên top-k để kiểm soát biến)

### Golden Dataset — có cả "bẫy"

Một Golden Dataset tốt không chỉ chứa câu hỏi thông thường mà còn phải chứa các **bẫy (traps)**: 20 câu hỏi về Luật Đất đai 2024, trong đó có những câu ngoài luồng như "Công ty SpaceX được thành lập vào năm nào?" với đáp án chuẩn là "Tài liệu không đề cập". Thiết kế bẫy giúp kiểm tra khả năng từ chối của chatbot — đo bằng metric riêng **Correct Rejection Rate** để xem chatbot có trung thực từ chối hay lại tự bịa kiến thức ngoài.

```json
{
  "question": "Sổ đỏ, sổ hồng được gọi chính thức trong Luật Đất đai 2024 là gì?",
  "ground_truth": "Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất."
}
```

### Script đánh giá tự động

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

### Bảng kết quả và nhận xét

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

## Nâng cao: dùng OpenAI API làm giám khảo

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

## 5 lỗi thường gặp trong RAG và cách khắc phục

### 1. Lỗi "Biết tuốt" (Fail ở Faithfulness)

**Triệu chứng:** người dùng hỏi câu ngoài luồng ("Thủ tục ly hôn được quy định như thế nào?") — đáng ra phải từ chối, hệ thống lại kể vanh vách về Luật Hôn nhân gia đình dựa vào kiến thức huấn luyện gốc. **Nguyên nhân:** LLM bị ảo giác và phớt lờ ngữ cảnh. **Khắc phục:** System Prompt cực kỳ khắt khe — "CHỈ được phép dùng ngữ cảnh được cung cấp. Nếu không có thông tin, hãy nói 'Tài liệu không đề cập'. TUYỆT ĐỐI không dùng kiến thức bên ngoài." Cài `temperature = 0`.

### 2. Lỗi "Cụt ý" (Fail ở Context Recall)

**Triệu chứng:** hỏi về 4 điều kiện chuyển nhượng quyền sử dụng đất, bot chỉ trả lời được điều kiện đầu tiên rồi dừng. **Nguyên nhân:** chunking quá thô, danh sách liệt kê bị đứt làm đôi, phần đuôi không lọt vào top-k. **Khắc phục:** Semantic Chunking hoặc Parent-Child Document Retriever.

### 3. Lỗi "Lạc đề" (Fail ở Context Precision)

**Triệu chứng:** hỏi "Giao đất **không thu tiền** sử dụng đất là gì?", bot ưu tiên đoạn "Giao đất **có thu** tiền" lên top 1 vì từ khóa gần như trùng hoàn toàn, chỉ khác mỗi chữ "không". **Nguyên nhân:** Dense Embedding yếu trong phân biệt từ khóa chuyên ngành tương đồng. **Khắc phục:** Hybrid Search (kết hợp Vector Search với Keyword Search như BM25) và Cross-Encoder Re-ranking để chấm điểm lại top 10 kết quả trước khi đưa cho LLM.

### 4. Lỗi "Nhiễu loạn ngữ cảnh" (Lost in the middle)

**Triệu chứng:** nhồi nhét 20 chunks để kéo Recall lên; câu trả lời nằm ở chunk số 10 nhưng LLM bỏ qua và kết luận không có thông tin. **Nguyên nhân:** LLM mắc hội chứng "Lost in the middle" — chỉ tập trung chú ý vào đầu và cuối prompt, bỏ quên phần giữa. **Khắc phục:** giới hạn số lượng context hợp lý (top 3–5), hoặc dùng kỹ thuật nén ngữ cảnh (Context Compression / LLMLingua) để gạn lọc trước khi đẩy vào prompt.

### 5. Lỗi "Lệch định dạng" (Format Error)

**Triệu chứng:** yêu cầu trả lời dạng JSON hoặc bảng Markdown, bot trả về đoạn văn xuôi. **Nguyên nhân:** prompt chưa đủ tốt hoặc model quá nhỏ không theo được cấu trúc. **Khắc phục:** ép buộc đầu ra (Structured Outputs) qua Pydantic, Instructor, hoặc tính năng JSON Mode của API.

## Kết luận

Cũng giống như phát triển phần mềm truyền thống cần Unit Test, phát triển ứng dụng RAG cần một **Evaluation Pipeline** chặt chẽ. Việc định lượng bằng Ragas không chỉ giúp so sánh các mô hình nhúng hay thuật toán cắt văn bản — mà còn là minh chứng rõ ràng với khách hàng về độ chính xác và tin cậy của sản phẩm.

## Bài liên quan

- Trước đó: [Multimodal RAG cho tài liệu PDF tiếng Việt](/bai-viet/multimodal-rag-pdf-tieng-viet/)
- Nền tảng liên quan: [Hybrid Search với BM25, Dense Retrieval và RRF](/bai-viet/hybrid-search-bm25-dense-rrf/)

## Nguồn

- [RAGAS: Automated Evaluation of RAG (Shahul Es et al., 2023, arXiv:2309.15217)](https://arxiv.org/abs/2309.15217) · [Ragas Official Documentation](https://docs.ragas.io/)
- Mã nguồn thực hành: [rag-advanced-evaluate (repo)](https://github.com/thaiptit123/rag-advanced-evaluate)
- Nội dung biên tập lại từ bài thực hành RAG Advanced của AI Guru x TiniX theo phong cách LearnWithHuy; API của Ragas có thể thay đổi theo phiên bản — bài viết dựa trên ragas 0.1.20.

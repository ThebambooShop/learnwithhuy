---
title: "Multimodal RAG: xây dựng pipeline đa phương thức và benchmark cho tài liệu PDF tiếng Việt"
description: "Pipeline RAG đa phương thức xử lý PDF chứa bảng số liệu và biểu đồ: Multi-Parser Engine, side-aware embedding, Text QA vs Vision QA, benchmark 12 câu hỏi và phân tích lỗi trượt cột."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-17"
cover: "/images/covers/posts/multimodal-rag-pdf-tieng-viet.jpg"
views: 430
---

Hệ thống hỏi đáp trên tài liệu PDF học thuật tiếng Việt — chứa bảng số liệu nhiều cột, chú thích và biểu đồ — thường gặp ba trở ngại với phương pháp bóc tách truyền thống: **lệch hàng cột** khi làm phẳng bảng nén, **xáo trộn thứ tự đọc** khi dàn trang phức tạp (trang hai cột, hộp chú thích xen giữa), và **mất mát thông tin đồ thị** do OCR thông thường không bóc tách được nhãn trục.

Bài này trình bày giải pháp RAG đa phương thức (Multimodal RAG) kết hợp trích xuất trực quan và mô hình ngôn ngữ thị giác, kèm bộ dữ liệu kiểm thử có căn cứ số trang đối soát.

**Khi nào nên dùng:** tài liệu chứa nhiều bảng biểu phức tạp, đồ thị và hình ảnh chú thích chuyên sâu; hệ thống đòi hỏi trích dẫn chính xác số trang; cần benchmark phân tách rõ lỗi truy xuất và lỗi đọc hiểu hình ảnh. **Không nên dùng khi:** ngữ liệu chủ yếu là văn bản thuần túy, ít bảng biểu; hoặc yêu cầu thời gian thực với chi phí tính toán tối thiểu — pipeline thị giác tốn tài nguyên hơn văn bản thuần.

## Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Multimodal RAG** | RAG mở rộng: không chỉ xử lý văn bản mà còn lập chỉ mục và truy xuất trực tiếp khối bảng biểu, hình ảnh, đồ thị |
| **Side-aware Embedding** | Cơ chế vector hóa bất đối xứng: gắn nhãn `side="document"` khi lập chỉ mục và `side="query"` khi tìm kiếm để không gian biểu diễn hội tụ |
| **Lexical vs Dense** | Truy xuất từ khóa (BM25) dựa tần suất khớp từ vựng; truy xuất vector so khớp cosine trong không gian ngữ nghĩa |
| **Text QA vs Vision QA** | Text QA đưa văn bản/bảng Markdown vào mô hình ngôn ngữ; Vision QA đưa ảnh biểu đồ độ phân giải cao kết hợp chú thích vào mô hình thị giác |
| **Page Citation** | Quy tắc phản hồi bắt buộc kèm trích dẫn `[PDF trang X]` để đối chiếu tài liệu gốc |
| **Recall@k / MRR** | Tỷ lệ câu hỏi tìm thấy trang đích trong top-k; thứ hạng nghịch đảo trung bình của trang đúng đầu tiên |

## Kiến trúc phân nhánh đa phương thức

Kiến trúc Dual-Branch tách biệt luồng xử lý giữa văn bản/bảng biểu và hình ảnh/đồ thị thống kê, gồm 4 khối chính:

**Khối 1 — Multi-Parser Engine (bóc tách đa thành phần):**

- *Văn bản và bố cục:* PyMuPDF4LLM đọc toàn bộ PDF giữ đúng thứ tự đọc
- *Bảng nén số liệu:* pdfplumber bóc tách lưới ô bảng; với bảng nhiều cột phức tạp, thuật toán heuristic quét dòng dữ liệu từ văn bản nguyên bản rồi ghép với tiêu đề cột để tái cấu trúc thành bảng Markdown 2D chuẩn
- *Hình ảnh:* tự động cắt và lưu nguyên bản ảnh biểu đồ dạng PNG độ phân giải cao (220 DPI) kèm chú thích phụ cận — phục vụ trực tiếp cho mô hình thị giác phân tích trục số liệu thay vì chuyển qua OCR gây mất mát cấu trúc
- *Fallback OCR:* pytesseract (ngôn ngữ `vie+eng`) tự kích hoạt khi lượng văn bản trích xuất trên trang dưới ngưỡng 80 ký tự

**Khối 2 — Embedding Gateway:** kết nối đến Triton Inference Server chạy mô hình nhúng đa phương thức (512 chiều, FP16). Áp dụng Side-Aware Asymmetric Prefixing: lập chỉ mục offline bắt buộc gán `side="document"`; truy vấn gán `side="query"`. Nhánh văn bản nhúng các bản ghi trang/đoạn đã tích hợp bảng Markdown; nhánh hình ảnh nhúng trực tiếp file PNG biểu đồ qua endpoint thị giác.

**Khối 3 — Multi-Vector Retrieval:** tính cosine giữa vector truy vấn và kho vector bản ghi trang/đoạn; truy xuất hình ảnh bằng so khớp vector đặc trưng ảnh (Image-to-Image) hoặc tìm kiếm kết hợp ngữ cảnh phụ cận để ánh xạ về mã trang PDF gốc (Gold Page Anchor).

**Khối 4 — Dual-Engine QA & Citation:** Text QA gửi ngữ cảnh Markdown cùng câu hỏi cho mô hình ngôn ngữ; Vision QA gửi ảnh PNG dạng base64 kết hợp chú thích phụ cận cho mô hình thị giác đọc trực tiếp xu hướng đường cột và số liệu. **Mọi câu trả lời bắt buộc kèm trích dẫn `[PDF trang X]`.**

## Thực nghiệm: bộ kiểm thử 12 câu hỏi

Nguồn ngữ liệu: báo cáo học thuật của Ngân hàng Thế giới *"Nâng cao Hiệu quả Giáo dục Đại học tại Việt Nam"* (110 trang). Sau khi xử lý qua Multi-Parser Engine: **168 chunks** (62 khối bảng Markdown nén + 106 đoạn văn bản), **25 trang chứa bảng phức tạp** (nhiều cột số, header gộp đa tầng), **17 ảnh biểu đồ thống kê** bóc tách độc lập.

Bộ kiểm thử 12 câu hỏi có gán nhãn trang chuẩn (Ground-Truth Page Anchor):

| Mã | Loại | Nội dung | Trang đúng | Mục tiêu kiểm nghiệm |
| --- | --- | --- | --- | --- |
| T1–T3 | Văn bản | Số liệu định lượng trong văn bản xuôi | 18, 55, 65 | Trích xuất thông tin trong đoạn văn phức tạp |
| B1–B6 | Bảng | Số trường top 1.000 của 6 quốc gia | 46 (Bảng 3) | Kiểm định hiện tượng trượt cột khi đọc bảng Markdown phẳng |
| F1–F3 | Biểu đồ | So sánh khu vực, tỷ lệ nhập học, việc làm và thu nhập | 16, 39, 48 | Đọc biểu đồ đường và biểu đồ cột |

### Hiệu năng truy xuất

| Phương pháp | Recall@1 | Recall@5 | MRR | Đánh giá |
| --- | --- | --- | --- | --- |
| Lexical (BM25) | 0.833 | 0.917 | 0.854 | Phụ thuộc từ khóa khớp chính xác |
| **jina-v5 (mức trang)** | **1.000** | **1.000** | **1.000** | Độ chính xác tuyệt đối ở top-1 |
| jina-v5 (mức đoạn) | 1.000 | 1.000 | 1.000 | Duy trì cao khi phân rã nhỏ |
| BGE-M3 (mức trang) | 0.667 | 1.000 | 0.833 | Thấp hơn ở top-1 nếu thiếu tiền tố chỉ dẫn |
| BGE-M3 (mức đoạn) | 0.833 | 1.000 | 0.892 | Ổn định hơn khi chỉ mục ở mức đoạn |

Ghi chú về truy xuất hình ảnh: so khớp ảnh→ảnh đạt chuẩn trên mẫu đồ thị kiểm nghiệm, nhưng truy xuất chéo **chữ→ảnh** trực tiếp còn hạn chế. Trong kịch bản RAG khi người dùng nhập câu hỏi bằng văn bản, hệ thống dùng truy vấn văn bản tìm trang qua Text-to-Page trước, rồi nạp ảnh crop cho Vision LLM. Lưu ý cần chỉ định chính xác cờ `side="query"` / `side="document"` để tránh suy giảm độ chính xác vector.

### Hiệu năng hỏi đáp và trích dẫn trang

| Phương pháp hỏi đáp | Độ chính xác | Tỷ lệ trích dẫn | Tỷ lệ từ chối | Mẫu |
| --- | --- | --- | --- | --- |
| Text-only Lexical (văn bản + bảng) | 0.556 | 0.889 | 0.111 | 9 câu |
| **Text-only jina-v5 (văn bản + bảng)** | **0.667** | **1.000** | **0.000** | 9 câu |
| Multimodal Vision QA (ảnh + ngữ cảnh) | 0.667 | 0.333 | 0.000 | 3 câu biểu đồ |

### Phân tích theo nhóm câu hỏi

- **Văn bản (T1–T3):** đạt 3/3 (100%) với jina-v5. Tại câu T3, truy xuất vector lấy chính xác trang 65 (học phí chiếm 55%), trong khi BM25 trượt sang trang 25 dẫn đến mô hình từ chối trả lời (abstain).
- **Bảng biểu (B1–B6):** đạt 3/6 PASS. Trang 46 được truy xuất hoàn toàn chính xác ở top-1 (Recall@1 = 100%); cả 3 ca sai đều do **trượt cột phía mô hình ngôn ngữ** khi xử lý bảng Markdown phẳng — B2 đọc 32 thay vì 35, B4 đọc 45 thay vì 60, B5 đọc 51 thay vì 44.
- **Hình ảnh (F1–F3):** câu F2 bắt buộc dùng Vision LLM vì mốc tăng trưởng "9% lên 28%" không tồn tại trong văn bản xuôi.

> **Tóm tắt số liệu cốt lõi:** khâu truy xuất đạt Recall@1 = 12/12 trang chuẩn (100%). Cả ba ca thất bại ở nhóm bảng biểu đều do trượt cột của LLM — đối với biểu đồ thống kê thuần túy, kích hoạt nhánh Vision QA là điều kiện tiên quyết để trích xuất đúng dữ liệu.

### Kiểm toán chất lượng bóc tách (Parse audit)

| Tiêu chí | Kết quả | Ý nghĩa |
| --- | --- | --- |
| Nhận diện bảng | P = 1.00, R = 0.75, F1 = 0.857 | Nhận diện chính xác trang chứa bảng, bỏ sót một số bảng phụ |
| Lệch cấu trúc liên công cụ | 6/8 trang lệch dòng | pdfplumber và pymupdf4llm xử lý ô gộp khác nhau |
| Độ bao phủ hình ảnh | 0.929 (13/14) | Bỏ qua 1 ảnh bìa không chứa chú thích |
| Thứ tự đọc văn bản | Kendall-tau ≈ 0.390 | Bị ảnh hưởng bởi nhãn trục xoay 90° trong biểu đồ |
| Chất lượng OCR | CER ≈ 3.2% | Lớp văn bản kỹ thuật số của PDF đạt chất lượng tốt |

## Phân tích lỗi và giới hạn vận hành

### Lỗi 1 — Lệch cột khi LLM đọc bảng Markdown nén

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

### Các lỗi còn lại

- **Dao động giữa các lần thực thi LLM:** cùng một prompt có thể cho kết quả lệch ±1 câu do sampling — cố định `temperature = 0.0` và ép kiểu đầu ra có cấu trúc (Structured Output Schema) trong môi trường sản xuất.
- **Lệch cấu trúc giữa hai công cụ phân tích bảng:** 6/8 trang chứa bảng phức tạp có chênh lệch số dòng giữa pdfplumber và pymupdf4llm, chủ yếu tại ô gộp — duy trì cơ chế fallback đối chiếu thay vì chỉ dựa một công cụ.
- **Thứ tự đọc bị xáo trộn:** nhãn trục xoay 90° khiến đoạn văn bản bị cắt rời trong trích xuất tuyến tính — với trang chứa đồ thị, dùng trực tiếp ảnh cắt nguyên bản kết hợp Vision LLM tin cậy hơn.

**Lưu ý vận hành:** tài liệu quét chất lượng thấp cần deskew và tăng độ tương phản; bảng lớn trải nhiều trang nên chia nhỏ vùng bảng và thẩm định tên cột trước khi trích xuất; xử lý đa phương thức tốn tài nguyên hơn — phân loại câu hỏi trước để chỉ kích hoạt nhánh thị giác khi thực sự cần thiết.

## Triển khai: hai luồng sử dụng

**Luồng A — xem kết quả bằng artifact có sẵn** (không cần hạ tầng):

```bash
git clone https://github.com/tnt305/multimodal_rag.git
cd multimodal_rag
python3 -m json.tool outputs/benchmark/qa.json
python3 -m json.tool outputs/benchmark/retrieval.json
```

**Luồng B — tái tạo toàn bộ benchmark từ PDF gốc** cần hạ tầng bên ngoài: Triton gateway, hai model nhúng text/image đã load, cùng API cho QA/Vision — repo chưa kèm tài nguyên triển khai gateway, nên không phải quickstart chạy được từ fresh clone.

Xử lý các tình huống chạy lệch: thứ tự đọc xáo trộn → ưu tiên ảnh crop kết hợp Vision LLM; cấu trúc bảng vỡ → kích hoạt chế độ Heuristic Rebuild Grid; OCR thấp → tăng DPI và chỉ định gói ngôn ngữ `vie`; lệch cột → yêu cầu mô hình xuất danh sách tên cột trước khi trích xuất.

## Bài liên quan

- Trước đó: [Multi-hop RAG với LangGraph](/bai-viet/multi-hop-rag-langgraph/)
- Tiếp theo: [Đánh giá chất lượng hệ thống RAG với Ragas](/bai-viet/danh-gia-chat-luong-rag-ragas/)

## Nguồn

- Mã nguồn: [multimodal_rag (repo thực hành)](https://github.com/tnt305/multimodal_rag.git)
- Nghiên cứu nền: BGE M3-Embedding (arXiv:2402.03216), jina-embeddings-v5-omni (Jina AI, 2025), Qwen3-VL (Alibaba Cloud, 2025)
- Nội dung biên tập lại từ bài thực hành Multimodal RAG của AI Guru x TiniX theo phong cách LearnWithHuy; số liệu benchmark quan sát trên bộ kiểm thử cụ thể.

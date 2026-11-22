---
title: "AI biết người học đang ở đâu? Knowledge tracing và học máy thích ứng"
description: "Giải thích knowledge tracing — công nghệ nền của adaptive learning (Khanmigo, Duolingo): máy đo mức thành thạo từng chủ đề từ dữ liệu làm bài, cách dùng để lập lộ trình ôn tập, và datasets để tự trải nghiệm."
topic: "ai-trong-giao-duc"
date: "2026-11-22"
cover: "/images/covers/posts/ai-biet-nguoi-hoc-dang-o-dau.jpg"
views: 0
faq:
  - q: "Knowledge tracing là gì, giải thích đơn giản?"
    a: "Là kỹ thuật máy học đo xác suất bạn đã thành thạo từng kỹ năng, dựa trên lịch sử làm bài (đúng/sai/thời gian). Hệ dùng kết quả đó để chọn bài tiếp theo — đó là lý do Duolingo biết nên nhắc bạn ôn từ nào."
  - q: "Có thể dùng knowledge tracing với lớp học bình thường không?"
    a: "Được ở mức đơn giản: bảng phân tích lỗi sai theo chủ đề bằng AI (prompt có trong bài). Muốn đúng kỹ thuật thật thì có thư viện pyBKT/pyKT open-source, cần chút kiến thức Python."
  - q: "Dữ liệu học sinh dùng cho nghiên cứu ở đâu ra?"
    a: "Có bộ mở như EdNet (387★, gần 800k người học) và ASSISTments — miễn phí cho nghiên cứu. Dữ liệu học sinh thật trong lớp thì phải xin phép và ẩn danh."
---

Khi Duolingo nhắc bạn ôn đúng những từ hay quên nhất, hoặc Khanmigo nâng độ khó bài tập đúng lúc bạn vừa nắm được bài cũ — đằng sau là cùng một công nghệ: **knowledge tracing** (KT), hay "theo dõi kiến thức". Đây là mảnh ghép ít nổi tiếng nhất nhưng tạo khác biệt lớn nhất giữa "AI giáo dục" và "ChatGPT kèm menu bài tập".

## Ý tưởng cốt lõi: lịch sử làm bài → xác suất thành thạo

Cách hoạt động đơn giản để hình dung:

1. Học sinh làm hàng loạt câu hỏi, mỗi câu gắn với một **kỹ năng** (skill/concept): "biến đổi lượng giác", "cộng phân số"...
2. Mô hình KT đọc chuỗi kết quả đúng/sai theo thời gian — **và cả thứ tự**: sai bài khó sau 3 bài đúng dễ có ý nghĩa khác sai liên tục 3 bài dễ.
3. Đầu ra: với mỗi kỹ năng, một con số 0–100% là **xác suất đã thành thạo**.

Đây chính là hệ thống trong bài 5 — thanh progress "Đại số 92%, Hàm số 18%". Mọi hệ adaptive đều chạy trên con số đó: **92% → chuyển chủ đề mới; 18% → quay lại luyện và giảm độ khó**.

Thế hệ mô hình ngày càng tinh: [Deep Knowledge Tracing (NeurIPS 2015)](https://arxiv.org/abs/1506.05908) dùng mạng nơ-ron đọc toàn chuỗi lịch sử; [AKT (KDD 2020)](https://dl.acm.org/doi/10.1145/3394486.3403282) dùng attention giống transformer; [simpleKT (ICLR 2023)](https://arxiv.org/abs/2302.06881) chứng minh baseline đơn giản vẫn rất khó bị vượt. Hướng mới 2025–2026: [Agent4Edu (AAAI 2025)](https://arxiv.org/abs/2501.10332) mô phỏng **học sinh ảo** bằng generative agents để dự đoán phản ứng của người học thật trước nội dung mới.

## Dùng ngay ở mức giáo viên: bảng phân tích lỗi sai

Bạn không cần mô hình để được 80% giá trị của ý tưởng này. Prompt sau biến AI thành công cụ chẩn đoán theo kỹ năng:

```text
Đây là danh sách câu sai của một học sinh trong 3 bài kiểm tra Toán.
Gom lỗi theo KỸ NĂNG (không theo bài kiểm tra), mỗi kỹ năng đánh giá:
- % đúng ước lượng từ dữ liệu
- Kiểu lỗi hay gặp (khái niệm sai / tính toán / đọc đề)
- 3 câu ôn tập phù hợp bắt đầu từ mức hiện tại
KHÔNG bịa thêm câu học sinh chưa làm.

[DÁN DANH SÁCH: câu số | chủ đề | đúng/sai | dạng lỗi nếu biết]
```

Cơ chế ẩn sau prompt này là **cognitive diagnosis** (chẩn đoán nhận thức) — họ mô hình của KT. Các hệ nghiên cứu như [NCD (AAAI 2020)](https://arxiv.org/abs/1908.08733) mở rộng thêm yếu tố tâm lý — thậm chí mô hình hóa cả trạng thái cảm xúc của học sinh khi làm bài ("Boosting Neural Cognitive Diagnosis with Student's Affective State Modeling", AAAI 2024) để chẩn đoán chính xác hơn.

## Muốn đi sâu kỹ thuật: 2 thư viện chuẩn

- **[pyBKT](https://github.com/CAHLR/pyBKT)** (293★, cập nhật 11/2026) — cài Bayesian Knowledge Tracing bằng `pip install pyBKT`, huấn luyện trên file CSV lịch sử làm bài, có notebook mẫu.
- **[pyKT](https://github.com/pykt-team/pykt-toolkit)** (462★) — benchmark các mô hình KT sâu (DKT, AKT, simpleKT...) trên dataset chuẩn, dành cho ai muốn nghiên cứu.

Và nếu bạn muốn dữ liệu thật để thử: [EdNet](https://github.com/riiid/ednet) của Riiid — gần 800 nghìn người học app Santa, dataset giáo dục công khai lớn nhất (387★; lưu ý repo ngừng cập nhật từ 2020, dùng làm data nghiên cứu vẫn tốt).

## Hạn chế cần biết

1. **Mô hình KT chỉ giỏi trong phạm vi dữ liệu nó thấy** — học sinh mới, đề kiểu lạ, hoặc môn tự do sáng tạo (viết văn) là vùng yếu của KT truyền thống.
2. **Con số "92% thành thạo" là dự đoán, không phải sự thật** — dùng để xếp hàng bài tập, đừng dùng để xếp loại học sinh.
3. Các hệ thực tế luôn ghép KT với con người: giáo viên thấy bảng phân tích, quyết định can thiệp.

Nguồn: mục Learner Modeling (50 entry KT + 35 cognitive diagnosis) trong [Awesome AI-LLM4Education](https://github.com/GeminiLight/awesome-ai-llm4education).

Tiếp theo là phần người đọc hay tò mò nhất: [**AI dạy từng môn học ra sao? Ngoại ngữ, Toán, Lập trình**](/bai-viet/ai-day-tung-mon-hoc/)

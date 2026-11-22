---
title: "AI thiết kế bài dạy: soạn giáo án 20 phút thay vì 2 tiếng"
description: "Quy trình 5 bước soạn giáo án và kế hoạch bài dạy bằng AI, học từ hệ thống multi-agent soạn bài nghiên cứu (Instructional Agents, COMA), kèm 3 prompt mẫu: giáo án, phân hoá theo trình độ, ngân hàng hoạt động."
topic: "ai-trong-giao-duc"
date: "2026-11-22"
cover: "/images/covers/posts/ai-thiet-ke-ke-hoach-bai-day.jpg"
views: 0
faq:
  - q: "Dùng AI soạn giáo án có bị mất vai trò của giáo viên không?"
    a: "Không, nếu quy trình đúng: AI sinh bản nháp theo chuẩn do bạn đưa, bạn đối chiếu và chỉnh. Các nghiên cứu (Instructional Agents, COMA) đều thiết kế AI ở vai trợ lý — giáo viên phê duyệt từng phần."
  - q: "AI soạn giáo án có tuân thủ chuẩn chương trình không?"
    a: "Chỉ khi bạn đưa chuẩn đó vào prompt. Đây là lý do bước 1 của quy trình là cung cấp mục tiêu theo chuẩn (VD: theo CT GDPT 2018), AI mới sinh nội dung khớp lớp và môn."
  - q: "Nên dùng ChatGPT, Claude hay Gemini để soạn bài?"
    a: "Về chất lượng soạn giáo án, cả ba đều đủ dùng. Ưu tiên công cụ hỗ trợ file/tài liệu dài (upload đề cương, SGK) để AI bám theo giáo trình thật thay vì đoán."
---

Phần công việc nặng nhất của một buổi dạy không phải là dạy — mà là **soạn**. Các nghiên cứu gần đây trong lĩnh vực soạn bài tự động (lesson plan generation) đã mô hình hóa được quy trình chuẩn, và phần lớn thầy cô có thể áp dụng ngay với ChatGPT/Claude/Gemini + một quy trình đúng.

## Cách các hệ nghiên cứu làm việc này

**[Instructional Agents](https://arxiv.org/abs/2508.19611)** (EACL 2026, [mã nguồn](https://github.com/DaRL-GenAI/instructional_agents)) mô phỏng cả tổ chuyên môn bằng 4 agent: *Lecture Designer* thiết kế nội dung, *Lecture Facilitator* chuyển thành hoạt động trên lớp, *Lecture Reviewer* đối chiếu với chuẩn chương trình, *Social Worker* đánh giá khả năng tiếp nhận của học sinh khó theo. Mỗi agent sinh một phần, phần sau bóc phần trước để chỉnh — kết quả thử nghiệm trên các lớp đại học: khối lượng công việc của giảng viên giảm rõ rệt mà chất lượng tài liệu vẫn được reviewer (giáo viên thật) xác nhận.

**COMA** (WWW 2026, [mã nguồn](https://github.com/ai4ed/COMA-LessonPlan)) đi xa hơn: các agent phối hợp **đa vòng** —Designer và Reviewer tranh luận đến khi thống nhất, thay vì một lượt sinh–một lượt chấm. Điểm học được từ COMA dùng cho prompt của bạn: đừng yêu cầu AI "soạn giáo án" một phát ăn ngay; hãy để nó **sinh → tự soi lại theo chuẩn → sửa**, hai lượt luôn cho bản tốt hơn hẳn một lượt.

## Quy trình 5 bước dùng được ngay

1. **Đưa chuẩn vào trước.** Dán mục tiêu bài học theo chương trình (CT GDPT 2018, yêu cầu cần đạt) — AI không tự biết chuẩn của lớp 8 môn Hoá.
2. **Yêu cầu sinh giáo án theo khung cố định** (mục tiêu, hoạt động khởi động, hình thành kiến thức, luyện tập, vận dụng, đánh giá). Khung cứng giúp AI không trôi.
3. **Yêu cầu AI tự soi theo chuẩn** — prompt thứ hai: "Đối chiếu giáo án trên với yêu cầu cần đạt, liệt kê chỗ thiếu hoặc sai lớp." (kỹ thuật từ COMA).
4. **Giáo viên chỉnh bản nháp** — đặc biệt các phần mang nghề thật: thời lượng, kiến thức nền của lớp mình, hoạt động phù hợp sĩ số.
5. **Lưu thành học liệu dùng lại** — giáo án đã chốt thành mẫu để lần sau chỉ thay phần thay đổi.

## 3 prompt mẫu

**Prompt 1 — giáo án hoàn chỉnh:**

```text
Bạn là tổ trưởng chuyên môn môn [MÔN], lớp [LỚP], theo CT GDPT 2018.

Soạn kế hoạch bài dạy chủ đề [CHỦ ĐỀ] với yêu cầu cần đạt sau:
[Y DÁN YÊU CẦU CẦN ĐẠT TÀI LIỆU CHÍNH THỨC]

Khung bắt buộc: (1) Mục tiêu theo 3 mức nhận thức; (2) Hoạt động khởi động
dưới 5 phút, gắn đời sống; (3) Hoạt động hình thành kiến thức chia tối đa
3 phần, mỗi phần có câu hỏi kiểm tra nhanh; (4) Luyện tập 2 bài từ dễ đến khó;
(5) Vận dụng mở; (6) Tiêu chí đánh giá có bảng rubric ngắn.
Sĩ số 45 học sinh, thời lượng 45 phút. Không bịa tài liệu tham khảo.
```

**Prompt 2 — phân hoá theo trình độ (khó nhất, giá trị nhất):**

```text
Từ giáo án trên, tạo 3 phiên bản hoạt động luyện tập cho 3 nhóm:
- Nhóm cần hỗ trợ: bài có gợi ý từng bước, số liệu đơn giản hơn.
- Nhóm trung bình: đúng chuẩn yêu cầu cần đạt.
- Nhóm phát triển: mở rộng hoặc bài thực tế, kèm 1 câu hỏi mở.
Mỗi nhóm kèm tiêu chí "xong bài" rõ ràng để em kiểm tra nhanh.
```

**Prompt 3 — ngân hàng câu hỏi:** dán đoạn SGK, yêu cầu "sinh 10 câu hỏi nhận biết–thông hiểu–vận dụng (4/3/3) kèm đáp án và lỗi hay gặp của học sinh khi làm sai". Cách này bám tài liệu thật — nền tảng của các hệ sinh câu hỏi có kiểm soát trong nghiên cứu (Math MCQ via human–LLM collaboration, EDM 2024): **người ra khung, AI lấp nội dung, người duyệt cuối**.

## Ba bẫy cần tránh

1. **Không đưa chuẩn vào prompt** → AI soạn theo hiểu biết chung chung, không khớp CT 2018 — đây là lỗi phổ biến nhất.
2. **Nhờ AI nghĩ luôn hoạt động "đổi mới sáng tạo"** → ra hoạt động hình thức. Cung cấp 1–2 hoạt động bạn thích làm làm ví dụ, AI bắt chước đúng khí chất hơn là tự bịa.
3. **Coi bản AI là bản cuối** → mọi nghiên cứu trong danh mục đều có bước reviewer là con người; bỏ bước này là mất đúng phần nghề của giáo viên.

Nguồn chính của bài này: [Instructional Agents](https://github.com/DaRL-GenAI/instructional_agents), [COMA](https://github.com/ai4ed/COMA-LessonPlan) trong bộ [Awesome AI-LLM4Education](https://github.com/GeminiLight/awesome-ai-llm4education).

Bài tiếp theo là phía kia của mặt trận: [**AI chấm bài và đánh giá tự động**](/bai-viet/ai-cham-diem-danh-gia-tu-dong/) — soạn xong bài thì đến chấm.

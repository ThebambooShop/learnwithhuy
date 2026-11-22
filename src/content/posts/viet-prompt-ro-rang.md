---
title: "Cách viết prompt rõ ràng để AI hiểu đúng yêu cầu"
description: "Cùng một câu hỏi, AI có thể trả lời hời hợt hoặc rất sát ý — khác biệt nằm ở cách bạn đặt yêu cầu. Bài viết hướng dẫn công thức viết prompt đơn giản, dễ áp dụng ngay."
topic: "prompt-engineering"
date: "2026-07-20"
cover: "/images/covers/posts/viet-prompt-ro-rang.jpg"
views: 1180
---

Nếu bạn từng cảm thấy "AI trả lời vô dụng quá" thì có thể vấn đề không nằm ở AI, mà ở **yêu cầu bạn đưa ra**. AI giống như một trợ lý giỏi nhưng mới quen việc: bạn nói càng rõ, kết quả càng sát ý.

Bài viết này chia sẻ cách viết prompt (yêu cầu gửi cho AI) mà mình dùng hằng ngày — không phải kỹ thuật cao siêu, chỉ là vài nguyên tắc cộng thêm ví dụ.

## Một prompt rõ ràng gồm những gì

Hãy tưởng tượng bạn nhờ đồng nghiệp soạn thư mời họp. Nếu bạn chỉ nói "viết thư mời họp giùm mình", kết quả sẽ chung chung. Nếu bạn nói rõ người nhận, thời gian, nội dung chính và giọng văn mong muốn, bạn sẽ nhận được bản dùng được ngay.

Với AI cũng vậy. Một prompt hiệu quả thường có 4 phần:

- **Bối cảnh**: bạn là ai, đang làm việc gì, thông tin liên quan.
- **Nhiệm vụ**: cụ thể bạn muốn AI làm gì.
- **Định dạng**: đầu ra mong muốn trông thế nào (độ dài, kiểu danh sách, giọng văn).
- **Ví dụ** (nếu có): một mẫu tốt để AI noi theo.

## Công thức dễ nhớ: Vai trò — Bối cảnh — Nhiệm vụ — Định dạng

Mình rút gọn thành bốn chữ V-B-N-Đ:

1. **Vai trò**: "Hãy đóng vai một chuyên viên tuyển dụng..."
2. **Bối cảnh**: "...mình đang tuyển vị trí bán hàng cho công ty phần mềm, ứng viên là sinh viên mới ra trường..."
3. **Nhiệm vụ**: "...hãy soạn 5 câu hỏi phỏng vấn để đánh giá khả năng giao tiếp..."
4. **Định dạng**: "...mỗi câu hỏi kèm một dòng giải thích muốn đánh giá điều gì, trình bày dạng danh sách."

Bạn không cần cả bốn phần trong mọi trường hợp — với câu hỏi ngắn thì chỉ cần nhiệm vụ rõ là đủ. Càng phức tạp thì càng nên đủ.

## Ví dụ: trước và sau

Đây là một prompt hay gặp:

```text
Viết bài giới thiệu sản phẩm giùm mình.
```

Và phiên bản cải tiến:

```text
Mình bán một ứng dụng ghi chú cho sinh viên, có tính năng tự tóm tắt bài giảng.
Hãy viết một đoạn giới thiệu khoảng 100 từ để đăng trong nhóm sinh viên trên
Facebook, giọng văn thân thiện, kèm một câu hỏi cuối bài để khuyến khích bình luận.
Tránh cam kết kiểu "tăng điểm số tuyệt đối".
```

Khác biệt rõ nhất: phiên bản sau nêu **đối tượng đọc**, **độ dài**, **giọng văn**, và cả **điều cần tránh** — những thứ AI không thể tự đoán.

## Bốn lỗi thường gặp

- **Prompt quá ngắn.** "Viết về AI" là ví dụ kinh điển — AI không biết bạn muốn viết cho ai, dài bao nhiêu, để làm gì.
- **Nhồi nhiều việc vào một prompt.** "Viết email, kèm lịch họp, kèm phân tích dữ liệu, kèm slide" — hãy tách thành các bước, hoặc yêu cầu AI làm từng phần rồi ghép.
- **Không nói định dạng đầu ra.** Nếu bạn cần danh sách gạch đầu dòng mà AI trả một đoạn văn dài, trách nhiệm thuộc về người đặt yêu cầu.
- **Bỏ qua thông tin AI không thể biết.** Tên công ty, dữ liệu nội bộ, quy cách riêng của bạn — AI không đoán được, hãy đưa vào prompt (trừ dữ liệu nhạy cảm, xem mục dưới).

## Về bảo mật khi viết prompt

Một lưu ý quan trọng: **đừng dán thông tin nhạy cảm vào công cụ AI công khai** — số liệu khách hàng, tài liệu mật, thông tin cá nhân của người khác. Nhiều công ty có quy định riêng về việc này; nếu bạn đi làm, hãy kiểm tra chính sách của công ty trước khi dùng công cụ AI cho công việc.

## Luyện tập thế nào

Cách tốt nhất để tiến bộ là **đối chiếu**: chạy prompt, đọc kết quả, tự hỏi "mình có thể diễn đạt lại yêu cầu nào để kết quả sát hơn?", rồi chạy lại. Thói quen cải tiến từng vòng như vậy giúp bạn tiến bộ nhanh hơn việc đọc mười bài "mẹo prompt".

Bạn có thể bắt đầu bằng cách áp dụng công thức V-B-N-Đ cho một việc thật trong tuần này — ví dụ soạn email trả lời khách hàng, hoặc lên dàn ý một bài thuyết trình. Chúc bạn "nói chuyện" với AI ngày càng thoải mái!

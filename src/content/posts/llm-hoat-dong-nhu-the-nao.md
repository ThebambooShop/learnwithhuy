---
title: "LLM hoạt động như thế nào? Giải thích bằng ví dụ đơn giản"
description: "Mô hình ngôn ngữ lớn (LLM) đứng sau ChatGPT, Gemini, Copilot... Bản chất cốt lõi của chúng đơn giản đến bất ngờ: đoán từ tiếp theo. Hiểu được điều này giúp bạn dùng AI khôn ngoan hơn."
topic: "generative-ai-llm"
date: "2026-08-18"
cover: "/images/covers/posts/llm-hoat-dong-nhu-the-nao.jpg"
featured: true
views: 1410
---

Bạn đang trò chuyện với một chatbot: nó trả lời mạch lạc, trích dẫn thơ, viết code, chuyển giọng văn theo yêu cầu. Có lúc bạn cảm thấy như đang nói chuyện với một người. Nhưng bên dưới tất cả, có một sự thật thú vị: **mô hình ngôn ngữ lớn (LLM — Large Language Model) về bản chất chỉ đang làm một việc — đoán từ tiếp theo.**

Hiểu được điều này không chỉ thú vị, mà còn giúp bạn dùng AI hiệu quả hơn hẳn. Cùng đi từng bước nhé.

## Bắt đầu từ trò chơi điền từ

Hãy hoàn thành câu sau:

> "Hà Nội là thủ đô của ___"

Bạn trả lời gần như ngay lập tức: "Việt Nam". Bạn làm được điều đó nhờ đã đọc rất nhiều câu tương tự trong đời. LLM cũng học theo cách đó — nhưng thay vì đọc suốt nhiều năm, nó được "đọc" một lượng văn bản khổng lồ (sách, bài báo, trang web...) và liên tục luyện trò điền từ:

- "Mùa thu Hà Nội thường ___" → đoán: "đẹp", "mát"
- "Công thức hoá học của nước là ___" → đoán: "H₂O"
- "Kính gửi Quý công ty, tôi viết email này để ___" → đoán: "trình bày", "tham vấn"

Mỗi lần đoán sai, mô hình được điều chỉnh một chút. Sau hàng tỷ lần lặp, mô hình trở nên giỏi đoán đến mức tạo ra văn bản tự nhiên.

## Từ đoán một từ đến viết cả đoạn văn

Vậy làm sao từ "đoán từ tiếp theo" lại ra được cả bài viết? Câu trả lời: **lặp lại liên tục**.

Mô hình viết từng từ một: đoán từ đầu tiên, thêm vào câu, rồi đoán từ tiếp theo dựa trên tất cả những gì đã viết, và cứ thế. Giống như người ta viết văn vậy — từng chữ một, mỗi chữ được chọn dựa trên ngữ cảnh phía trước.

Có một chi tiết thú vị: mô hình không chọn cứng một từ duy nhất, mà có một **phân phối xác suất**. Ví dụ sau "Hà Nội là thủ đô của", "Việt Nam" có xác suất cao nhất, nhưng các lựa chọn khác vẫn có khả năng. Chính vì vậy, cùng một câu hỏi có thể cho hai câu trả lời hơi khác nhau ở hai lần hỏi.

## "Token" — đơn vị mà LLM thực sự đọc

LLM không đọc từng ký tự, cũng không đọc từng từ hoàn chỉnh. Văn bản được chia thành các **token** — những mảnh nhỏ (thường là một phần từ hoặc một vài ký tự):

- "học máy" có thể thành `học` + `máy`
- "machinelearning" có thể thành `machine` + `learning`
- một số từ tiếng Việt có dấu có thể bị tách thành nhiều mảnh nhỏ

Đây là lý do đôi khi AI đếm chữ hoặc chơi trò chơi chữ chưa chuẩn xác — nó "nhìn" văn bản qua lăng kính token, không phải qua lăng kính con người. LLM cũng có **giới hạn ngữ cảnh** (context window): số token tối đa nó có thể "giữ trong đầu" cho một lần hội thoại. Tài liệu quá dài vượt giới hạn này thì những phần đầu có thể bị lược.

## Vì sao đôi khi AI "bịa" thông tin

Đây là phần quan trọng nhất của bài viết. LLM được tối ưu để **tạo ra văn bản trôi chảy, hợp ngữ cảnh** — không phải để **kiểm tra sự thật**. Khi được hỏi về thông tin nó chưa học kỹ, mô hình vẫn sẽ tạo một câu trả lời nghe rất thuyết phục... nhưng có thể sai hoàn toàn.

Hiện tượng này gọi là **ảo giác** (hallucination). Ví dụ kinh điển: nhờ AI trích dẫn nghiên cứu khoa học — nó có thể tạo ra tên tác giả, tên tạp chí nghe rất thật nhưng không tồn tại.

Vì vậy, quy tắc vàng khi dùng LLM:

- Với **thông tin có thể kiểm chứng** (số liệu, trích dẫn, quy định): luôn kiểm tra lại ở nguồn gốc.
- Với **nội dung sáng tạo** (dàn ý, bản nháp, giải thích khái niệm): thoải mái dùng, rồi chỉnh theo ý bạn.

## Điều này có ý nghĩa gì khi bạn dùng AI

Hiểu cơ chế "đoán từ tiếp theo" giúp giải thích nhiều kinh nghiệm thực tế:

- **Prompt càng rõ, ngữ cảnh càng tốt** → mô hình có nhiều "manh mối" để đoán đúng hướng.
- **Cho ví dụ mẫu trong prompt** → mô hình nắm được format và giọng văn bạn muốn.
- **Yêu cầu AI "suy nghĩ từng bước"** cho việc phức tạp → giúp nó xây dựng câu trả lời có logic hơn thay vì nhảy đến kết luận.
- **Đừng trông chờ AI tra cứu dữ liệu mới nhất** (trừ khi công cụ đó có tính năng tìm kiếm web) — kiến thức của mô hình dừng ở thời điểm dữ liệu huấn luyện.

LLM không phải "cỗ máy biết tất cả", mà là một "người học qua đọc rất nhiều, nói chuyện rất giỏi, nhưng cần bạn kiểm chứng". Khi nhìn nhận đúng vị trí của nó, bạn sẽ dùng nó hiệu quả và an toàn hơn nhiều.

Trong bài sau, mình sẽ so sánh LLM với "anh họ" Machine Learning truyền thống để bạn biết khi nào nên dùng loại công cụ nào. Hẹn gặp lại!

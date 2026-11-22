---
title: "Sổ tay ứng dụng AI cho ngành giáo dục: bản đồ để bắt đầu đúng cách"
description: "Sổ tay do RMIT Việt Nam phối hợp Bộ GD&ĐT xây dựng dành cho nhà giáo — tóm gọn điều đáng đọc nhất: công thức câu lệnh hiệu quả, quy trình soạn bài, cách dùng AI trong kiểm tra đánh giá và nguyên tắc dùng an toàn."
topic: "ai-trong-giao-duc"
date: "2026-11-21"
cover: "/images/covers/posts/so-tay-ung-dung-ai-nganh-giao-duc.jpg"
featured: true
views: 0
faq:
  - q: "Sổ tay hướng dẫn nhà giáo ứng dụng AI là của ai thực hiện?"
    a: "Sổ tay do Đại học RMIT Việt Nam phối hợp với Cục Nhà giáo và Cán bộ quản lý giáo dục (Bộ Giáo dục và Đào tạo) thực hiện, có hỗ trợ nguồn lực từ chương trình Aus4Skills. Nội dung viết theo bối cảnh giáo dục Việt Nam, gồm sáu chương đi từ nền tảng tư duy đến thực hành cụ thể."
  - q: "Giáo viên không rành công nghệ có dùng được AI không?"
    a: "Được. Sổ tay mở đầu bằng cách thiết lập ChatGPT/Gemini từng bước, kèm thư viện câu lệnh mẫu theo từng việc cụ thể: soạn kế hoạch bài dạy, tạo đề kiểm tra, phản hồi học sinh. Phần lớn thao tác chỉ là viết yêu cầu bằng tiếng Việt và kiểm duyệt lại kết quả."
  - q: "Dùng AI trong kiểm tra, đánh giá có hợp lệ không?"
    a: "Hợp lệ khi minh bạch. Sổ tay gợi ý thang AIAS chia các cấp độ được phép dùng AI khi làm bài, và nguyên tắc vàng: chất lượng đề phụ thuộc dữ liệu đầu vào bạn cung cấp. AI giúp tạo đề, đáp án, rubric — nhưng tuyệt đối không tải lên thông tin định danh học sinh."
---

Cuốn **"Sổ tay hướng dẫn nhà giáo ứng dụng AI trong giảng dạy và quản lý giáo dục"** (RMIT Việt Nam phối hợp Cục Nhà giáo và Cán bộ quản lý giáo dục — Bộ GD&ĐT, hỗ trợ bởi Aus4Skills) là tài liệu hiếm hoi viết cho giáo viên Việt Nam mà không dùng ngôn ngữ khái niệm: mọi chương đều đi kèm quy trình từng bước, câu lệnh mẫu và hình minh họa.

Bài này tóm lại những điều đáng đọc nhất — theo cách bất kỳ ai đang dạy học, quản trị trường học, hay đơn giản muốn xem AI "xuyên ngành" vào một nghề cụ thể, đều lấy được thứ dùng được ngay.

## Sổ tay gồm những gì?

Sáu chương, mỗi chương một mặt trận:

| Chương | Nội dung |
| --- | --- |
| 1 | Tổng quan AI tạo sinh, viết câu lệnh hiệu quả, dùng AI có trách nhiệm |
| 2 | Xây dựng kế hoạch bài dạy và bài giảng (Gamma, Canva, NotebookLM) |
| 3 | Thiết kế kiểm tra, đánh giá: đề trắc nghiệm, tự luận, đáp án, rubric |
| 4 | Học liệu số: ảnh, nhạc, truyện, video, mô phỏng và trò chơi học tập |
| 5 | Hỗ trợ và quản lý học tập, quản trị nhà trường với nền tảng tích hợp AI |
| 6 | Phát triển chuyên môn: NotebookLM, nghiên cứu sâu, khung năng lực số |

## Một câu lệnh tốt có năm yếu tố

Phần đáng áp dụng nhất cho mọi nghề nằm ở chương 1. Sổ tay định nghĩa công thức của một câu lệnh hiệu quả:

- **Nhân vật** (Persona): AI nhập vai ai? — "Đóng vai một gia sư giỏi…"
- **Mục tiêu** (Task): muốn AI làm gì? — "…giải thích quá trình quang hợp…"
- **Đối tượng** (Audience): nội dung cho ai? — "…cho một học sinh 14 tuổi…"
- **Bối cảnh** (Context): dùng vào việc gì? — "…để ôn thi môn Sinh học…"
- **Giới hạn** (Constraints): ràng buộc gì? — "…khoảng 300 từ, giọng thân thiện."

Ghép lại được một câu lệnh hoàn chỉnh:

> Đóng vai một gia sư giỏi, biết chia nhỏ và giải thích những vấn đề phức tạp một cách dễ hiểu. Giải thích quá trình quang hợp cho một học sinh 14 tuổi để em ôn thi môn Sinh học. Câu trả lời dài khoảng 300 từ, giọng điệu thân thiện và giàu tính giáo dục.

Đối chiếu với một câu lệnh yếu kiểu "tìm 3 nguyên nhân gây ô nhiễm không khí" — thiếu vai trò, thiếu đối tượng, thiếu định dạng — bạn sẽ thấy khác biệt không nằm ở công cụ AI, mà nằm ở yêu cầu bạn đưa vào. Khi kết quả kém, quay lại đếm xem thiếu yếu tố nào.

## Quy trình soạn bài: AI tạo bản nháp, người thầy là tác giả cuối cùng

Chương 2 đưa ra quy trình bốn bước để soạn kế hoạch bài dạy: **xác định mục tiêu và đầu vào** (kèm cả số công văn định hình khung kế hoạch bài dạy của Bộ), **viết câu lệnh theo cấu trúc chuẩn**, **tương tác và tinh chỉnh**, rồi **kiểm duyệt chuyên môn**.

Nguyên tắc xuyên suốt là đúng một dòng:

> AI tạo ra bản nháp, còn người thầy mới là tác giả cuối cùng. Mọi sản phẩm do AI gợi ý đều cần được thẩm định về tính chính xác, sự phù hợp với học sinh và mức độ bám sát chương trình trước khi đưa vào lớp.

Phần thực dụng nhất của chương này là cách neo câu lệnh vào một phương pháp sư phạm cụ thể và mô hình TPACK (công nghệ phục vụ mục tiêu dạy học, không ngược lại), thiết kế bài dạy bao trùm cho các nhóm học sinh khác nhau, và cả phương án "hai lối" cho lớp ít công nghệ — AI vẫn có thể hỗ trợ cả những hoàn cảnh chưa có thiết bị đầy đủ.

## Kiểm tra đánh giá: chất lượng đầu vào quyết định chất lượng đề

Chương 3 có một "nguyên tắc vàng" đáng nhớ: cùng một công cụ AI, câu lệnh sơ sài cho bộ đề chung chung, câu lệnh chuẩn bị kỹ với đủ **câu lệnh rõ ràng, nội dung cần kiểm tra, mô tả mức độ nhận thức và câu hỏi mẫu** sẽ cho bộ đề gần như dùng ngay. Số câu cho từng mức độ của thang Bloom nên được quy định rõ để kiểm soát độ khó.

Điểm đáng cẩn thận hơn cả là phân công: AI hỗ trợ tạo đề, đáp án, bảng tiêu chí đánh giá và phản hồi — nhưng **không tải lên AI thông tin định danh học sinh**. Và để tránh tranh cãi "đây có phải học sinh dùng AI không", sổ tay gợi ý thang AIAS chia rõ các cấp độ được phép dùng AI khi làm bài, kèm minh bạch hóa mức độ sử dụng.

Một lưu ý tôi muốn nhấn thêm từ tài liệu tham khảo của chính sổ tay: các công cụ phát hiện văn bản do AI viết (detector) có tỷ lệ báo nhầm cao, đặc biệt bất lợi cho người viết không phải bản ngữ — nên dựa vào detector để phán xét học sinh là con đường dở nhất. Đánh giá quá trình và tiêu chí minh bạch sẽ an toàn hơn nhiều.

## Học liệu số và lớp học số: nhiều hơn là tạo slide

Chương 4 và 5 mở rộng phạm vi AI từ "soạn văn bản" sang sáng tạo nội dung đa phương thức: hình minh họa, nhạc giáo dục, sách truyện, video, mô phỏng và trò chơi học tập (kể cả nhờ AI viết trò chơi mà không cần biết lập trình). Sổ tay nhắc cấu trúc câu lệnh tạo ảnh gồm bốn thành phần: chủ thể, bối cảnh, phong cách và chi tiết — và mọi sản phẩm đều cần kiểm duyệt nội dung trước khi dùng.

Phần quản lý học tập đưa ra ranh giới đáng nhớ: dữ liệu tiến độ học tập giúp phát hiện sớm học sinh cần hỗ trợ, nhưng **không được dùng để dán nhãn học sinh**. Học liệu tự học tạo bằng AI (như bài thuyết minh từ slide) nên nghe lại và kiểm tra trước khi giao.

## Dùng AI có trách nhiệm: nguyên tắc không phải đề xuất

Sổ tay liệt kê sáu nguyên tắc kiểm tra khi đưa AI vào lớp học: **công bằng, độ tin cậy và an toàn, quyền riêng tư, tính bao hàm, tính minh bạch, trách nhiệm giải trình**. Chọn nguyên tắc nền tảng nhất để bắt đầu:

- **Tối thiểu hóa dữ liệu**: chỉ đưa vào AI những gì không nhạy cảm, không định danh, không vượt mục đích sư phạm. Nhờ AI gợi ý phản hồi? Xóa tên và thông tin nhận diện học sinh trước.
- **Không suy đoán cảm xúc**: Đạo luật AI của EU cấm dùng AI nhận diện cảm xúc trong trường học — đừng dùng camera/micro để đo mức tập trung của học sinh.
- **Minh bạch với người học**: khi phù hợp, nói rõ phần nào được tạo bằng AI — qua chính trải nghiệm đó, học sinh học được cách dùng AI có phản biện.

## Bốn lỗi thường gặp và cách khắc phục

1. **Câu lệnh quá chung chung** — bổ sung đủ năm yếu tố: môn, lớp, thời lượng, phương pháp, định dạng.
2. **Chấp nhận ngay bản nháp đầu tiên** — bản nháp đầu là điểm khởi đầu để đối thoại, không phải sản phẩm để sao chép.
3. **Bỏ qua khâu kiểm chứng** — mọi con số, sự kiện, công thức đều phải thẩm định trước khi lên lớp.
4. **Đánh mất dấu ấn cá nhân** — bài giảng hoàn toàn do AI tạo thường thiếu kết nối với lớp cụ thể của bạn; hãy thêm ví dụ địa phương, câu chuyện riêng và phong cách của chính mình.

## Không dạy học thì lấy gì từ sổ tay này?

Đúng như danh mục mới của blog này theo dõi: **AI ứng dụng theo từng ngành** — cấu trúc của sổ tay khá chuẩn mực để áp vào bất kỳ nghề nào:

- Công thức năm yếu tố câu lệnh dùng được với mọi nghề, từ soạn báo giá đến viết đề xuất dự án.
- Quy trình "AI nháp — người làm chuyên môn chốt" là bản đồ an toàn cho cả kế toán, luật sư hay kỹ thuật viên.
- Nguyên tắc tối thiểu hóa dữ liệu và minh bạch hóa việc dùng AI không đặc thù riêng cho giáo dục.

Nếu bạn muốn đọc nguyên bản, sổ tay phân phối miễn phí qua RMIT Việt Nam và các kênh của Bộ Giáo dục và Đào tạo. Bài sau trong danh mục này, tôi sẽ đi sâu từng chương kèm bộ câu lệnh thực hành đầy đủ hơn.

---
title: "Chương trình Harness Engineer: toàn bộ 14 bài giảng trong một trang"
description: "Bản tổng hợp chương trình Harness Engineer: năm lớp phòng thủ của harness, 14 bài giảng từ \"tại sao agent mạnh vẫn thất bại\" đến graph engineering — kèm điểm cốt lõi của từng bài và lộ trình học trên learnwithhuy."
topic: "harness-engineer"
date: "2026-11-24"
cover: "/images/covers/posts/agent-harness-la-gi.jpg"
featured: true
views: 540
faq:
  - q: "Chương trình Harness Engineer dành cho ai?"
    a: "Ai đã dùng AI coding agent (Claude Code, Codex, Cursor...) và thấy agent mạnh nhưng kết quả không đáng tin cậy. Chương trình dạy cách biến kho lưu trữ của bạn thành một harness đầy đủ: đặc tả tác vụ, cung cấp ngữ cảnh, môi trường thực thi, phản hồi xác minh và quản lý trạng thái."
  - q: "Nên học 14 bài giảng theo thứ tự không?"
    a: "Có. Bài 1–2 dựng nền lý thuyết (năm lớp phòng thủ, định nghĩa harness), bài 3–12 đi từng lớp phòng thủ, bài 13–14 tổng hợp thành vòng lặp tự chủ rồi nâng cấp lên graph engineering. Đọc lộn lệch vẫn hiểu, nhưng thứ tự là đường nhanh nhất."
  - q: "Chuỗi Mini-dsh trong cùng chủ đề có liên quan gì?"
    a: "Chuỗi Mini-dsh (8 bài) là phần thực hành: tự tay dựng một agent harness thật theo nguyên tắc everything-is-a-plugin. Học lý thuyết xong thì vào chuỗi Mini-dsh để dựng hệ thống chạy được."
---

Agent của bạn chạy 20 phút rồi báo "xong" — nhưng code làm hỏng test, sửa một lỗi sinh ra hai lỗi. Trước khi mở ví nâng cấp model, hãy đọc chương trình này: **vấn đề phần lớn không nằm ở model, mà nằm ở harness** — toàn bộ hạ tầng bên ngoài trọng số model. Chương trình Harness Engineer gồm 14 bài giảng (dịch và tái sử dụng từ [Learn Harness Engineering — WalkingLab](https://github.com/walkinglabs/learn-harness-engineering), giấy phép MIT, bài gốc tiếng Việt), dưới đây là điểm cốt lõi của từng bài và link đọc đầy đủ — **cả chương trình đọc ngay trên learnwithhuy, không cần sang web ngoài**.

## Bản đồ chương trình

| Nhóm | Bài | Trọng tâm |
|------|-----|-----------|
| Nền tảng | 01–02 | Vì sao agent mạnh vẫn thất bại; harness thực sự là gì |
| Nguồn sự thật | 03–04 | Repo thành system of record; chia nhỏ file hướng dẫn |
| Chạy dài | 05–06 | Liên tục giữa các phiên; giai đoạn khởi tạo riêng |
| Ranh giới | 07–08 | WIP=1 chống làm quá; feature list ràng buộc "xong" |
| Xác minh | 09–10 | Chặn tuyên bố thành công sớm; end-to-end testing |
| Quan sát | 11–12 | Observability trong harness; bàn giao trạng thái sạch |
| Tổng hợp | 13–14 | Từ prompt thủ công đến vòng lặp tự chủ; graph engineering |

### Bài 01. Mô hình mạnh không có nghĩa là thực thi đáng tin cậy

- Năng lực mô hình và độ tin cậy thực thi là hai chuyện khác nhau. Ngay cả một con ngựa thuần chủng cũng cần bộ yên cương tốt.
- Khi sự cố xảy ra, kiểm tra harness trước, rồi mới đến mô hình. Đổi mô hình là lựa chọn tốn kém nhất, và phần lớn thời gian, đó thậm chí không phải là vấn đề mô hình.
- Mỗi lỗi là một tín hiệu: harness của bạn có khiếm khuyết cấu trúc. Hãy tìm và sửa nó.
- Đừng chỉ nói "mô hình không đủ tốt". Hãy rà qua có hệ thống năm lớp: tác vụ chưa định nghĩa rõ, ngữ cảnh thiếu, môi trường cấu hình sai, thiếu xác minh, mất trạng thái giữa các phiên. Cứ mười lần thì chín lần vấn đề nằm ở một trong các lớp đó.
- Một tệp `AGENTS.md` có thể hiệu quả hơn việc nâng cấp lên mô hình đắt tiền hơn.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-01-why-capable-agents-still-fail/](/bai-viet/lecture-01-why-capable-agents-still-fail/)

---

### Bài 02. Harness thực sự có nghĩa là gì

- Harness = Hướng dẫn + Công cụ + Môi trường + Trạng thái + Phản hồi. Cả năm hệ thống phụ đều cần thiết.
- Không phải trọng số mô hình, thì đó là harness. Harness của bạn quyết định bao nhiêu phần năng lực mô hình được hiện thực hóa.
- Trong năm hệ thống phụ, hệ thống phụ phản hồi thường có chi phí đầu tư thấp nhất mà lợi nhuận cao nhất. Hãy chuẩn hóa lệnh xác minh trước tiên.
- Dùng "thí nghiệm loại trừ biến có kiểm soát" để định lượng đóng góp biên của từng hệ thống phụ. Còn muốn xác định điểm nghẽn thật, hãy dựa vào nhật ký lỗi và quy kết nguyên nhân, không chỉ dựa vào ablation.
- Harness mục ruỗng giống như code vậy. Hãy kiểm tra định kỳ và trả nợ harness y như cách bạn trả nợ kỹ thuật.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-02-what-a-harness-actually-is/](/bai-viet/lecture-02-what-a-harness-actually-is/)

---

### Bài 03. Biến kho lưu trữ thành nguồn sự thật duy nhất

- Kiến thức không nằm trong repo thì không tồn tại với agent. Đưa thông tin quyết định quan trọng vào kho lưu trữ là khoản đầu tư harness nền tảng nhất, hãy vẽ bản đồ cho tốt để không lạc.
- Dùng "bài kiểm tra phiên mới" để đánh giá chất lượng repo: một phiên mới có trả lời được năm câu hỏi cơ bản khi chỉ nhìn vào nội dung repo không?
- Kiến thức phải nằm cạnh code, tối giản nhưng đầy đủ, và cập nhật song song với code. Vấn đề không phải viết thêm tài liệu, mà là đặt thông tin vào đúng chỗ.
- Vận dụng nguyên tắc ACID cho trạng thái agent: commit nguyên tử, xác minh nhất quán, cô lập đồng thời và bền vững hóa kiến thức quan trọng.
- Suy giảm kiến thức là kẻ thù lớn nhất. Tài liệu lỗi thời còn nguy hiểm hơn không có tài liệu, vì nó đẩy agent đi hướng sai trong khi agent vẫn nghĩ mình đang đi đúng hướng.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-03-why-the-repository-must-become-the-system-of-record/](/bai-viet/lecture-03-why-the-repository-must-become-the-system-of-record/)

---

### Bài 04. Chia hướng dẫn ra thành nhiều tệp

- "Thêm quy tắc" là giảm đau ngắn hạn, nhưng là thuốc độc dài hạn. Trước khi thêm quy tắc, hãy nghĩ xem nó có chỗ đứng tốt hơn trong một tài liệu chủ đề không.
- Tệp đầu vào là bộ định tuyến, không phải bách khoa toàn thư. 50-200 dòng chỉ gồm tổng quan, ràng buộc cứng và liên kết.
- Tận dụng hiệu ứng "lạc giữa chừng": thông tin quan trọng đặt ở đầu hoặc cuối, mục kém quan trọng chuyển sang tài liệu chủ đề.
- Quản lý sự phình hướng dẫn y như quản lý nợ kỹ thuật. Kiểm tra định kỳ, mỗi hướng dẫn cần có nguồn gốc, điều kiện áp dụng và điều kiện hết hạn.
- Sau khi chia, SNR tăng lên, agent dành nhiều ngân sách ngữ cảnh hơn cho tác vụ thật thay vì xử lý hướng dẫn lan man.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-04-why-one-giant-instruction-file-fails/](/bai-viet/lecture-04-why-one-giant-instruction-file-fails/)

---

### Bài 05. Duy trì ngữ cảnh xuyên suốt các phiên

- Cửa sổ ngữ cảnh là tài nguyên hữu hạn. Tác vụ dài sẽ trải qua nhiều phiên, và các phiên sẽ mất thông tin, đó là thực tế khách quan.
- Giải pháp không phải cửa sổ lớn hơn, mà là lưu trữ trạng thái tốt hơn. Tệp tiến độ, nhật ký quyết định và git checkpoint phối hợp với nhau, để phiên mới nối tiếp phiên cũ.
- Hãy đối xử với agent như một kỹ sư bị xóa trắng bộ nhớ ngắn hạn mỗi phiên: trước khi "tan ca", phải ghi lại đã làm gì, vì sao, và bước tiếp theo là gì.
- Chi phí tái thiết lập là chỉ số then chốt. Một harness tốt để lại tiến độ, kết quả xác minh và các bước kế tiếp trong tệp, để phiên mới phục hồi nhanh chóng.
- Chiến lược hỗn hợp: tác vụ ngắn xử lý trong phiên, tác vụ dài dùng artifact có cấu trúc để duy trì tính liên tục.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-05-why-long-running-tasks-lose-continuity/](/bai-viet/lecture-05-why-long-running-tasks-lose-continuity/)

---

### Bài 06. Khởi tạo trước mỗi phiên agent

- Khởi tạo và triển khai có mục tiêu tối ưu khác nhau, trộn lẫn chỉ kéo cả hai xuống.
- Đầu ra của khởi tạo không phải code nghiệp vụ, mà là hạ tầng: môi trường chạy được, test xác minh được, danh sách sẵn sàng, phân rã tác vụ.
- Xác nhận khởi tạo bằng bốn điều kiện trong danh sách sẵn sàng: chạy được, test được, thấy tiến độ được, chọn được bước tiếp theo.
- Khởi động từ mẫu tốt hơn từ đầu. Hãy dùng template dự án để dựng sẵn hạ tầng chuẩn hoá.
- Thời gian đầu tư cho khởi tạo được thu hồi hoàn toàn trong 3-4 phiên kế tiếp. Đây không phải chi phí thêm, mà là khoản đầu tư trả trước.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-06-why-initialization-needs-its-own-phase/](/bai-viet/lecture-06-why-initialization-needs-its-own-phase/)

---

### Bài 07. Vạch ranh giới tác vụ rõ ràng cho agent

- **WIP=1 là cài đặt mặc định an toàn cho harness agent**: xong một rồi mới sang cái tiếp theo, đừng cố song song hoá.
- **Bằng chứng hoàn thành phải có thể thực thi**: "code trông có vẻ ổn" không tính, "curl trả về 201" mới tính.
- **Bề mặt phạm vi phải được đưa ra thành một tệp**: không chỉ nhắc tới trong hội thoại, mà phải ghi vào repo ở định dạng máy đọc được.
- **Vượt phạm vi và dở dang là cộng sinh**: giải quyết được một là giải quyết luôn cái kia.
- **"Làm ít mà xong" luôn thắng "làm nhiều mà bỏ dở"**: số dòng code agent và tỷ lệ hoàn thành tính năng có tương quan âm. Chất lượng bao giờ cũng thắng số lượng.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-07-why-agents-overreach-and-under-finish/](/bai-viet/lecture-07-why-agents-overreach-and-under-finish/)

---

### Bài 08. Sử dụng feature list để ràng buộc những gì agent làm

- **Feature list là cấu trúc nền của harness**, không phải ghi chú cho người. Bộ lập lịch, bộ xác minh và trình báo cáo bàn giao đều dựa vào nó.
- **Mỗi mục tính năng phải có đủ bộ ba**: mô tả hành vi, lệnh xác minh và trạng thái hiện tại. Thiếu một yếu tố thì mục chưa hoàn chỉnh, cũng như ghế ba chân mà mất một chân.
- **Chuyển trạng thái do harness kiểm soát**, agent không tự ý đổi được. Pass xác minh là con đường nâng cấp duy nhất.
- **Feature list là nguồn sự thật duy nhất của dự án**, mọi thông tin dạng "cần làm gì" đều bắt nguồn từ đó.
- **Hiệu chỉnh độ hạt về mức "hoàn thành được trong một phiên"**, quá rộng thì không xong, quá hẹp thì không quản lý nổi.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-08-why-feature-lists-are-harness-primitives/](/bai-viet/lecture-08-why-feature-lists-are-harness-primitives/)

---

### Bài 09. Ngăn chặn agent tuyên bố thành công quá sớm

- **Agent tự tin thái quá một cách có hệ thống**, sai lệch hiệu chuẩn độ tự tin là thực tế khách quan. Code được viết ra không có nghĩa là viết đúng.
- **Phán đoán hoàn thành phải được đưa ra ngoài**, harness tự xác minh độc lập. Đừng tin "cảm giác" của agent.
- **Cả ba lớp xác nhận đều cần thiết**: cú pháp pass, hành vi pass, hệ thống pass, tiến từng lớp một, không cắt tắt.
- **Thông báo lỗi nên bao gồm bước sửa cụ thể**, giúp agent tự điều chỉnh thay vì chỉ biết "sai rồi".
- **Không tái cấu trúc khi chức năng cốt lõi chưa được xác minh**, ràng buộc ưu tiên hoàn thành chính là chìa khoá ngăn chặn tối ưu hoá sớm.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-09-why-agents-declare-victory-too-early/](/bai-viet/lecture-09-why-agents-declare-victory-too-early/)

---

### Bài 10. Chỉ chạy toàn bộ pipeline mới tính là xác minh thật sự

- **Unit test mù có hệ thống với khiếm khuyết ở ranh giới component**: thiết kế cô lập của chúng chính là điều ngăn chúng phát hiện vấn đề tương tác.
- **Test toàn bộ quy trình không chỉ phát hiện khiếm khuyết, mà thay đổi cả cách agent viết code**, giúp nó tập trung hơn vào tích hợp và ranh giới.
- **Quy tắc kiến trúc phải có thể thực thi**, không viết trong tài liệu để chờ người đọc, mà tự động kiểm tra trên mỗi commit.
- **Thông báo lỗi phải thiết kế cho agent**, kèm bước sửa cụ thể để hình thành vòng lặp tự sửa.
- **Thăng cấp phản hồi review khiến harness tự động mạnh lên**, mỗi loại khiếm khuyết bắt được trở thành một tuyến phòng thủ vĩnh viễn.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-10-why-end-to-end-testing-changes-results/](/bai-viet/lecture-10-why-end-to-end-testing-changes-results/)

---

### Bài 11. Làm cho runtime của agent có thể quan sát được

- **Khả năng quan sát là thuộc tính kiến trúc của harness.** Nó không phải tính năng thêm vào sau, mà là năng lực cốt lõi phải được thiết kế từ đầu.
- **Cả hai lớp quan sát đều cần thiết.** Tín hiệu runtime giải thích "chuyện gì đã xảy ra", artifact quá trình giải thích "vì sao lại làm thế này".
- **Sprint contract đẩy việc căn chỉnh lên đầu.** Chúng ngăn generator xây thứ mà evaluator sẽ lập tức từ chối vì lý do có thể dự đoán trước.
- **Rubric chấm điểm làm đánh giá có thể tái lập.** Evaluator khác nhau cho điểm tương tự với cùng một đầu ra.
- **Khả năng quan sát biến một lời từ chối mơ hồ thành một khiếm khuyết cụ thể, có thể sửa.**

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-11-why-observability-belongs-inside-the-harness/](/bai-viet/lecture-11-why-observability-belongs-inside-the-harness/)

---

### Bài 12. Bàn giao sạch ở cuối mỗi phiên

- **Trạng thái sạch là điều kiện cần để hoàn thành phiên**, không phải dọn dẹp tuỳ chọn, mà là một phần của "định nghĩa hoàn thành".
- **Cả năm chiều đều không thể thiếu**, build, test, tiến độ, artifact, khởi động, mỗi cái phải được kiểm tra tường minh.
- **Tài liệu chất lượng làm sức khoẻ codebase trở nên theo dõi được**, bạn chỉ có thể chủ động sửa thứ bạn biết đang tụt dốc.
- **Định kỳ đơn giản hoá harness**, khi năng lực mô hình cải thiện, gỡ các ràng buộc không còn cần thiết.
- **"Dọn sau" nghĩa là không bao giờ dọn.** Tăng trưởng entropy là trạng thái mặc định, chỉ có dọn chủ động mới chống lại được.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-12-why-every-session-must-leave-a-clean-state/](/bai-viet/lecture-12-why-every-session-must-leave-a-clean-state/)

---

### Bài 13. Từ Nhắc lệnh Thủ công đến Vòng lặp Tự chủ

- **Loop Engineering không thay thế Harness Engineering — nó xây dựng một tầng lên trên đó.** Harness làm cho các lần chạy đơn lẻ đáng tin cậy. Vòng lặp làm cho các lần chạy liên tục tự chủ.
- **`/goal` là vòng lặp đơn giản nhất:** mục tiêu + xác minh + điều kiện dừng. Ba thứ đó dịch chuyển bạn từ bên trong vòng lặp ra bên ngoài nó.
- **Sáu nguyên thủy (Automations / Worktrees / Skills / Connectors / Sub-agents / Trạng thái Bên ngoài) là các khối xây dựng của vòng lặp.** Không phải tất cả mọi lúc, nhưng bạn cần biết khi nào nên dùng cái nào.
- **Maker và checker phải được tách riêng.** Một mô hình chấm điểm công việc của chính mình là không đáng tin cậy. Một trình xác minh độc lập — đôi khi là một mô hình hoàn toàn khác — là đảm bảo độ tin cậy cơ bản của bất kỳ vòng lặp nào.
- **Các vòng lặp làm cho việc tạo ra gần như miễn phí và để lại phán đoán như là nguồn lực khan hiếm.** Thời gian bạn tiết kiệm không phải để nghỉ ngơi. Đó là để đưa ra nhiều phán đoán hơn.
- **Bốn chi phí thầm lặng trở nên gay gắt hơn khi vòng lặp chạy càng lâu:** nợ xác minh, sự thối rữa hiểu biết, sự đầu hàng nhận thức, bùng nổ token. Các vòng lặp tăng tốc đầu ra — và rủi ro.
- **Bắt đầu nhỏ.** Một `/goal`, một cron, một file bộ nhớ markdown. Nhận thấy lợi nhuận, sau đó xếp chồng lên nhau.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-13-loop-engineering/](/bai-viet/lecture-13-loop-engineering/)

---

### Bài 14. Từ Vòng lặp Đơn lẻ đến Kỹ thuật Đồ thị

- **Graph Engineering không thay thế Loop Engineering, mà xây dựng một lớp lên trên nó.** loop là một nút trong đồ thị; ba thứ của bài giảng trước (mục tiêu, xác minh, điều kiện dừng) trở thành cấu trúc bên trong của nút.
- **Đồ thị biến "quyết định trì hoãn" thành "quyết định trước".** loop giấu kiểu thất bại trong vòng lặp, graph bày nó lên giấy — đọc được, kiểm toán được, sửa cục bộ được.
- **Đồ thị và workflow khác nhau ở chỗ nút chứa gì.** Chứa hàm là workflow, chứa agent là đồ thị. Đây cũng là thứ rượu mới duy nhất trong "rượu cũ trong bình mới".
- **Thiết kế đồ thị trước tiên trả lời bốn câu hỏi:** những loop nào nuôi những loop nào, ai sở hữu mục tiêu, ai có thể phủ quyết/quay lại, những chỉ số nào được động những chỉ số nào bị đóng băng. Trả lời không được thì đừng vẽ.
- **Đừng vẽ đồ thị vì thích vẽ.** Năm tiêu chí: tách độc lập được, có nhánh hoặc quay lại, trạng thái trung gian đáng lưu, kết quả nghiệm thu được, lợi ích cộng tác > chi phí điều phối.
- **Băng thông đánh giá của bạn vẫn là trần nhà.** Đồ thị khiến các agent song song nhiều hơn, nhưng khả năng phán đoán của bạn là tài nguyên tuần tự — thuế điều phối không biến mất vì có nhiều nút hơn.
- **Hãy nhớ tiếng nói phản biện.** Hình dạng không phải bức tường chịu lực; khả năng phát lại, quan sát, phục hồi mới là. Danh từ sẽ đổi mỗi sáu tuần, năng lực kỹ thuật thì không.

**Đọc bài giảng đầy đủ →** [/bai-viet/lecture-14-graph-engineering/](/bai-viet/lecture-14-graph-engineering/)


## Học tiếp bằng thực hành: chuỗi Mini-dsh

Lý thuyết của 14 bài giảng ghép với phần thực hành trong cùng chủ đề **Harness Engineer** — chuỗi 8 bài tự tay dựng agent harness (Mini-dsh) theo nguyên tắc *everything is a plugin*:

1. [Agent Harness là gì: tại sao model cần một cái khung](/bai-viet/agent-harness-la-gi/) — ranh giới harness vs. loop, Message provider-agnostic
2. [Kernel và nguyên tắc "mọi thứ là plugin"](/bai-viet/kernel-plugin-thiet-ke-harness/) — Fiber, effect(), đăng ký đối xứng với unmount
3. [Agent loop: state machine giữ log làm trạng thái duy nhất](/bai-viet/agent-loop-state-machine/) — rebuild từ log, không có state riêng
4. [Tools và permission pipeline](/bai-viet/tools-permission-pipeline/) — quyết định call nào được phép chạy
5. [Session log và compaction](/bai-viet/session-log-va-compaction/) — nhớ của agent mà không phình context
6. [System prompt động và Skills](/bai-viet/system-prompt-va-skills/) — nạp đúng thứ tự, đúng lúc
7. [Scheduler song song và steering inbox](/bai-viet/scheduler-va-steering-inbox/) — chạy nhanh mà không giẫm chân
8. [Capabilities, subagent và composition](/bai-viet/capabilities-subagents-composition/) — ghép thành hệ thống hoàn chỉnh

> **Nguồn chương trình giảng:** [walkinglabs/learn-harness-engineering](https://github.com/walkinglabs/learn-harness-engineering) — WalkingLab, giấy phép MIT. Toàn bộ bài giảng và code ví dụ thuộc repo gốc.

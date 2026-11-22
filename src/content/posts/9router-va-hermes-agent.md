---
title: "9Router và Hermes Agent: 2 công cụ AI mà dev nào cũng nên biết"
description: "Một cổng định tuyến API thông minh và một Agent tự chủ đa năng — hai công cụ mã nguồn mở giải quyết hai tầng bài toán khác nhau khi xây hệ thống AI. Giải thích dễ hiểu kèm bảng so sánh và kịch bản thực tế."
topic: "cong-cu-ai"
date: "2026-11-17"
cover: "/images/covers/posts/9router-va-hermes-agent.jpg"
views: 950
---

Khi ứng dụng AI chuyển từ "ô hội thoại" sang hệ thống xử lý tác vụ phức tạp, bạn sẽ gặp hai thách thức ở hai tầng khác nhau:

- **Tầng hạ tầng mô hình:** gọi trực tiếp API của từng nhà cung cấp khiến mã nguồn bị khóa chặt vào cấu trúc của họ. Dịch vụ nào đó gặp sự cố, hết rate limit hoặc tăng giá là phải sửa code ở nhiều nơi.
- **Tầng thực thi tác vụ:** để hoàn thành công việc phức tạp (lập trình, phân tích dữ liệu, quản trị hệ thống), mô hình không thể hoạt động đơn độc — cần suy luận đa bước, tự chọn công cụ, ghi nhớ ngữ cảnh qua nhiều phiên.

Bài viết này giới thiệu hai công cụ mã nguồn mở giải quyết đúng hai tầng đó. **9Router** lo tầng cổng API, **Hermes Agent** lo tầng tác vụ tự chủ. Kết hợp lại, bạn được một hệ thống AI vừa suy luận mạnh, vừa linh hoạt hạ tầng — không khóa chặt vào nhà cung cấp nào.

## 9Router — cổng định tuyến API thông minh

**9Router là gì?** Một API Gateway mã nguồn mở chuẩn hóa và chuyển tiếp các yêu cầu gọi mô hình AI. Nó cung cấp giao diện tương thích chuẩn API OpenAI tại `http://localhost:20128/v1` — nghĩa là bất kỳ công cụ nào (Claude Code, Cursor, Codex, Cline hay Agent khác) đều có thể trỏ đến mà không cần sửa mã nguồn tích hợp.

### Tính năng cốt lõi

- **RTK Token Saver** — nén dữ liệu thô từ công cụ (git diff, grep, ls... vốn chiếm 30–50% dung lượng prompt nhưng chứa nhiều dòng trắng): tự động phân tích 1KB đầu tiên của kết quả và nén lại, tiết kiệm 20–40% input token mà vẫn giữ ngữ cảnh.
- **Chế độ Caveman / Ponytail** — tự động ép mô hình trả lời ngắn gọn, trực diện, bỏ câu chuyển tiếp rườm rà: tiết kiệm tới 65% output token.
- **3-Tier Fallback** — ghép nhóm mô hình theo thứ tự ưu tiên: tầng 1 mô hình cao cấp (Subscription), hết hạn mức thì chuyển tầng 2 giá rẻ, sự cố thì chuyển tầng 3 miễn phí.
- **Multi-account Round-robin** — tự động luân chuyển giữa nhiều tài khoản cùng nhà cung cấp khi một tài khoản chạm giới hạn.
- **Format Translation** — dịch định dạng API hai chiều giữa OpenAI, Claude, Gemini, Cursor, Kiro, Vertex AI và Ollama.

### Lưu ý quan trọng về chi phí

Một điểm cần phân biệt rõ: **9Router bản thân là phần mềm miễn phí, mã nguồn mở 100% (giấy phép MIT)** — dữ liệu cấu hình và nhật ký lưu cục bộ trong SQLite (`~/.9router/db/data.sqlite`), tự triển khai không tốn phí bản quyền. Chi phí (nếu có) nằm ở **mô hình phía sau**:

- **Local LLM** qua Ollama/vLLM: miễn phí hoàn toàn.
- **Gói API miễn phí** (Kiro AI, OpenCode Free...): có hạn mức trải nghiệm.
- **Dịch vụ thương mại** (OpenAI API, Anthropic API, Claude Code Pro...): tính phí theo token hoặc hạn mức đăng ký.

Nó cũng có Web Dashboard trực quan tại `http://localhost:20128` để quản lý nhà cung cấp và thiết lập quy tắc định tuyến thay vì chỉnh file cấu hình tay.

## Hermes Agent — Agent tự chủ đa năng

**Hermes Agent là gì?** Một khung làm việc Agent tự chủ mã nguồn mở do Nous Research phát triển. Khác với ứng dụng trò chuyện theo từng phiên, Hermes Agent chạy liên tục và độc lập — trên máy cục bộ, VPS chi phí thấp, GPU cluster hoặc môi trường serverless (Modal, Daytona).

### Vòng lặp tự học khép kín

Điểm đặc sắc nhất là **Closed Learning Loop** theo chu trình: *Quan sát → Thực thi → Phản ánh → Kết tinh → Tái sử dụng*. Sau mỗi tác vụ phức tạp, Agent tự phân tích lại quá trình làm việc và cô đọng thành kỹ năng tái sử dụng. Kỹ năng do Agent tự học được gắn nhãn `learned` trên giao diện danh mục, quản lý dưới dạng file Markdown theo chuẩn mở agentskills.io.

### Kiến trúc bộ nhớ 3 tầng

- **Working Memory** — bộ nhớ ngắn hạn: toàn bộ ngữ cảnh của phiên hiện tại.
- **Persistent Semantic Memory** — bộ nhớ ngữ nghĩa dài hạn: thói quen, hồ sơ người dùng, chuỗi công cụ đã dùng qua nhiều phiên.
- **Cross-Session Recall** — truy xuất lịch sử qua các phiên bằng tìm kiếm toàn văn SQLite FTS5 kết hợp tóm tắt AI, giảm hiện tượng trôi ngữ cảnh.

### Bộ công cụ và khả năng

Hơn 40 công cụ tích hợp sẵn: terminal đa môi trường (Local, Docker, SSH, Singularity, Modal, Daytona), thao tác tệp và mã nguồn, điều khiển trình duyệt, đa phương tiện (TTS, tạo ảnh) và mở rộng qua MCP. Đáng chú ý là **Subagents** — khi bạn giao nhiều việc cùng lúc, Agent chính tự tạo các tác vụ con chạy song song rồi tổng hợp kết quả, không tiêu tốn ngữ cảnh của phiên chính.

Tương tác đa kênh: Terminal TUI chuyên nghiệp, cùng Messaging Gateway tích hợp Telegram, Discord, Slack, WhatsApp, Signal và Email — bạn nhắn tin thoại cho Agent đang chạy trên server từ điện thoại. Kèm **Cron Scheduler** lập lịch bằng ngôn ngữ tự nhiên ("mỗi sáng gửi báo cáo vào Telegram") và backend serverless đóng băng khi rảnh để chi phí duy trì tiệm cận 0.

## Hai công cụ kết hợp như thế nào?

Hermes Agent không bị khóa vào nhà cung cấp nào: nó phát ra yêu cầu chuẩn API OpenAI. Trỏ endpoint về 9Router là bạn được cả hai lợi thế. Luồng xử lý gồm 6 bước:

1. **Khởi tạo:** bạn nhập mục tiêu qua TUI hoặc app nhắn tin.
2. **Lập kế hoạch:** Hermes Agent phân tích ngữ cảnh, đọc bộ nhớ dài hạn, đóng gói yêu cầu chuẩn OpenAI gửi đến `http://localhost:20128/v1`.
3. **Định tuyến:** 9Router nén token (RTK), kiểm tra hạn mức, chuyển tiếp đến nhà cung cấp tối ưu; sự cố thì kích hoạt fallback 3 tầng.
4. **Trả kết quả:** nhà cung cấp xử lý và phản hồi về 9Router.
5. **Chuẩn hóa:** 9Router đóng gói phản hồi chuẩn OpenAI trả lại Agent.
6. **Thực thi:** Hermes Agent chạy công cụ thật trên hệ thống, lưu bộ nhớ mới, trả đáp án cho bạn.

## So sánh vai trò

| Khía cạnh | 9Router | Hermes Agent |
| --- | --- | --- |
| Vai trò | Proxy/gateway định tuyến mô hình | Agent tự chủ thực thi tác vụ |
| Đầu vào | API request chuẩn OpenAI | Yêu cầu bằng ngôn ngữ tự nhiên |
| Bộ nhớ | Không (stateless) | Có (Memory + Skill bền vững) |
| Thực thi Tool | Không | Có (40+ tool) |
| Lập lịch (Cron) | Không | Có, bằng ngôn ngữ tự nhiên |
| Tối ưu token | RTK, Caveman/Ponytail | Conversation Compression |
| Dự phòng | Fallback 3 tầng | Fallback qua chuỗi cấu hình |
| Messaging | Không | Telegram, Discord, Slack, WhatsApp, Signal |
| Giấy phép | Mã nguồn mở MIT | Mã nguồn mở MIT |

Tóm gọn: **9Router** trả lời *"gửi yêu cầu này đến mô hình nào, định dạng gì, nén bao nhiêu token"*; **Hermes Agent** trả lời *"làm gì với kết quả, ghi nhớ gì cho lần sau, lập lịch thế nào"*.

## Kịch bản thực tế: "Phân tích dung lượng ổ đĩa"

Trong demo của tài liệu gốc, người dùng gõ yêu cầu phân tích dung lượng ổ đĩa vào Hermes Agent:

1. Agent đóng gói yêu cầu, gửi qua 9Router.
2. 9Router áp RTK Token Saver (giảm 20–40% token prompt) rồi định tuyến đến mô hình tối ưu.
3. Mô hình phản hồi danh sách lệnh cần chạy (`df`, `du`); Agent tự chạy trên hệ thống thật.
4. Agent tổng hợp số liệu thành báo cáo: tổng dung lượng, mức sử dụng từng phân vùng, các thư mục chiếm nhiều nhất, và gợi ý 3 khu vực nên dọn dẹp.

Toàn bộ quá trình suy luận phía sau được 9Router định tuyến và nén token âm thầm — người dùng chỉ thấy một báo cáo sạch.

## Nên bắt đầu từ đâu?

- Nếu bạn **đã dùng Cursor/Claude Code/Cline** và muốn tiết kiệm token + tránh đứt gãy khi nhà cung cấp sự cố: triển khai 9Router trước, trỏ công cụ hiện tại về `localhost:20128/v1` — không đổi thói quen làm việc.
- Nếu bạn cần **Agent chạy liên tục, tự học, tự động hóa**: dùng Hermes Agent, và cấu hình nó dùng 9Router làm điểm kết nối duy nhất để có cả hai lợi thế.

Vì cả hai đều là mã nguồn mở, cách an toàn nhất để đánh giá là đọc mã nguồn và thử trên môi trường của riêng bạn — đúng tinh thần "học thật, chia sẻ thật" của blog này.

## Nguồn tham khảo

Bài viết dựa trên tài liệu hướng dẫn "9Router và Hermes Agent" của AI Guru x TiniX (Mentor Đỗ Hoàng Hà). Nguồn chính thức của hai công cụ:

- [9Router trên GitHub](https://github.com/decolua/9router)
- [Hermes Agent trên GitHub](https://github.com/nousresearch/hermes-agent)
- [Hermes Agent Documentation](https://hermes-agent.nousresearch.com/docs/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

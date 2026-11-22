---
title: "OpenClaw là gì? AI Agent mã nguồn mở chạy trên máy tính của bạn"
description: "Bài 1 series OpenClaw: OpenClaw là gì, lịch sử phát triển, vì sao nó gây sốt với hơn 300,000 GitHub stars, và cách AI agent này hoạt động qua Gateway và vòng lặp OODA."
topic: "cong-cu-ai"
date: "2026-11-17"
cover: "/images/covers/posts/openclaw-la-gi.jpg"
views: 950
---

Đầu năm 2026, một project nhỏ trên GitHub bắt đầu lan truyền với tốc độ chưa từng có trong lịch sử phần mềm mã nguồn mở. Trong vòng chưa đầy 4 tháng, nó vượt qua React để trở thành project phi tổng hợp được star nhiều nhất mọi thời đại trên GitHub với hơn 300,000 stars. Project đó tên là **OpenClaw**.

Nhưng con số không phải điều quan trọng nhất. OpenClaw đại diện cho một cách tiếp cận hoàn toàn mới với AI: không phải chatbot bạn hỏi rồi đọc câu trả lời, mà là **một AI Agent thực sự làm việc cho bạn** — chạy ngay trên máy tính của bạn, kết nối với các ứng dụng bạn dùng hàng ngày.

Series này (6 bài) tổng hợp từ documentation chính thức và kinh nghiệm cộng đồng để bạn có thể hiểu, cài đặt và khai thác OpenClaw cho công việc thực tế — được thiết kế cho **người không chuyên kỹ thuật**: bạn cần kỹ thuật cơ bản (cài phần mềm, dùng terminal) nhưng không cần biết lập trình.

## OpenClaw là gì?

OpenClaw là một AI Agent mã nguồn mở chạy trực tiếp trên máy tính của bạn. Khác với Claude hay ChatGPT chỉ trả lời câu hỏi trong cửa sổ chat, OpenClaw có thể tự mình: mở ứng dụng, duyệt web, đọc/viết file, chạy lệnh terminal, và thực hiện chuỗi hành động phức tạp — giống như một nhân viên thực sự làm việc trên màn hình máy tính.

Điểm quan trọng cần hiểu ngay: **OpenClaw không thay thế Claude hay ChatGPT** — nó là lớp kết nối giúp LLM (Claude, GPT-5, DeepSeek...) thực sự làm việc trên máy tính của bạn.

### Lịch sử phát triển

| Thời gian | Sự kiện |
| --- | --- |
| Tháng 11/2025 | Peter Steinberger (lập trình viên Áo) ra mắt "Clawdbot" trên GitHub |
| Tháng 1/2026 | Đổi tên thành "Moltbot" sau tranh chấp nhãn hiệu với Anthropic |
| 28/01/2026 | Đổi tên lần cuối thành "OpenClaw" — tên chính thức hiện tại |
| 2/2026 | Vượt 300,000 GitHub stars, qua mặt React. Peter gia nhập OpenAI |
| 2/2026 | Dự án chuyển sang quản lý bởi Open-Source Foundation |
| 3/2026 | ClawHub đạt 47,000 Skills. Nvidia, Meta, Google đều tích hợp OpenClaw |

### Vì sao OpenClaw gây sốt?

1. **BYOM — Bring Your Own Model.** Bạn tự mang API key của mình (Claude, GPT-5, DeepSeek, hoặc model local qua Ollama). Dữ liệu không đi qua server của bên thứ ba, chi phí hoàn toàn trong tầm kiểm soát.
2. **Chạy cục bộ — dữ liệu không rời khỏi máy bạn.** Toàn bộ workspace, lịch sử, token xác thực đều được mã hóa và lưu tại máy của bạn. Đây là lý do các doanh nghiệp cần bảo mật dữ liệu chọn OpenClaw thay vì Manus AI hay các cloud agent khác.
3. **Hệ sinh thái Skills khổng lồ.** ClawHub có 47,000+ Skills do cộng đồng đóng góp. Mỗi Skill là một file hướng dẫn giúp Agent hiểu cách tích hợp với một dịch vụ cụ thể: từ Gmail, Google Calendar, Obsidian, GitHub, đến Zalo, Shopify, QuickBooks...
4. **Tương tác qua ứng dụng bạn đã dùng.** Không cần học giao diện mới. Nhắn tin với Agent qua Telegram, Discord, WhatsApp, hoặc Slack — mở Telegram, gõ lệnh, Agent làm việc.

## Kiến trúc & cơ chế hoạt động

Để dùng OpenClaw hiệu quả, bạn cần hiểu 2 khái niệm cốt lõi: **Gateway** (trung tâm điều khiển) và **vòng lặp OODA** (cách Agent "suy nghĩ" và hành động).

### Gateway — trái tim của hệ thống

Gateway là một dịch vụ Node.js chạy nền (background service) trên máy tính hoặc VPS của bạn. Nó đóng vai trò trung tâm điều phối, kết nối 3 thành phần:

- **LLM (Bộ não):** Claude, GPT-5, DeepSeek, hoặc Ollama (model local). Bạn cung cấp API key, Gateway gửi yêu cầu và nhận phản hồi.
- **Kênh giao tiếp (Giao diện):** Telegram, Discord, WhatsApp... Bạn nhắn tin từ đây, Agent nhận lệnh và gửi kết quả lại đây.
- **Tools & Skills (Cánh tay):** Các công cụ để Agent thực sự hành động trên máy tính và kết nối với dịch vụ ngoài.

### Vòng lặp OODA — cách Agent xử lý mọi việc

OODA (Observe — Orient — Decide — Act) là vòng lặp mà Agent lặp đi lặp lại cho đến khi hoàn thành nhiệm vụ. Hiểu vòng lặp này giúp bạn biết cách viết lệnh hiệu quả và tại sao đôi khi Agent cần nhiều bước để hoàn thành một việc:

| Giai đoạn | Agent làm gì |
| --- | --- |
| **OBSERVE (Quan sát)** | Chụp màn hình, đọc file, lấy dữ liệu từ hệ thống |
| **ORIENT (Định hướng)** | Gửi ảnh/dữ liệu lên LLM (Claude/GPT) để phân tích |
| **DECIDE (Quyết định)** | LLM xác định hành động phù hợp với yêu cầu người dùng |
| **ACT (Hành động)** | Thực thi: click chuột, gõ bàn phím, chạy lệnh, gửi tin |

Vòng lặp liên tục: sau mỗi hành động, Agent tiếp tục quan sát kết quả và lặp lại cho đến khi hoàn thành nhiệm vụ.

## Nên đọc OpenClaw như thế nào?

> OpenClaw về bản chất là "WordPress của AI Agent" — cực kỳ mạnh và linh hoạt, nhưng cần hiểu cách vận hành để tránh rủi ro bảo mật. Đừng cấp cho Agent nhiều quyền hơn mức cần thiết: bắt đầu với các tool cơ bản, mở rộng dần khi đã quen.

Sau bài này, bạn sẽ có thể: hiểu OpenClaw hoạt động ra sao và tại sao nó khác biệt với các AI tool khác; cài đặt và cấu hình trong 30 phút; tích hợp Telegram/Discord/Slack; cài Skills từ ClawHub; xây quy trình tự động hóa; và thiết lập Multi-Agent để có đội AI làm việc song song.

## Bài tiếp theo trong series

- **Bài 2:** [Cài đặt và cấu hình OpenClaw trong 30 phút](/bai-viet/cai-dat-va-cau-hinh-openclaw/) — 3 phương pháp cài, wizard thiết lập, và cách viết SOUL.md "linh hồn" của Agent
- Bài 3: Tools, Skills và tích hợp kênh giao tiếp
- Bài 4: 21 use case thực chiến cho công việc
- Bài 5: Multi-Agent, bảo mật và chạy 24/7 trên VPS
- Bài 6: OpenClaw hay Manus AI? Lộ trình 30 ngày làm chủ

## Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn cộng đồng và [documentation OpenClaw](https://openclaw.ai/) — có biên tập lại cấu trúc theo phong cách LearnWithHuy.
- Kho mã nguồn: [github.com/openclaw](https://github.com/openclaw)

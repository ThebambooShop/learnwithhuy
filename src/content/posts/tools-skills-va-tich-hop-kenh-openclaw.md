---
title: "Tools, Skills và tích hợp kênh của OpenClaw"
description: "Bài 3 series OpenClaw: 26 công cụ nội tại chia 8 nhóm, nguyên tắc tối thiểu quyền, 47,000+ Skills trên ClawHub, và cách kết nối Telegram, Zalo, Slack để ra lệnh cho Agent mọi lúc."
topic: "cong-cu-ai"
date: "2026-11-17"
cover: "/images/covers/posts/tools-skills-va-tich-hop-kenh-openclaw.jpg"
views: 820
---

Nếu Tools là "cơ quan", thì Skills là "sách giáo khoa" dạy Agent cách dùng cơ quan đó để thực hiện việc gì. Bài này đi qua ba lớp năng lực của OpenClaw: **Tools** (26 công cụ nội tại), **Skills** (mở rộng qua ClawHub) và **kênh giao tiếp** (Telegram, Zalo, Slack...).

## Tools — 26 công cụ nội tại

Tools là các "cơ quan" quyết định Agent **CÓ THỂ** làm gì. Mặc định OpenClaw bật 22 tool và tắt 4 tool. Hiểu từng nhóm tool giúp bạn cấu hình đúng quyền cho Agent và biết giới hạn của nó.

### 8 nhóm tool của OpenClaw

| Nhóm Tool | Tools | Chức năng |
| --- | --- | --- |
| group:runtime | exec, bash, process | Chạy lệnh hệ thống |
| group:fs | read, write, edit, apply_patch | Quản lý file |
| group:web | web_search, web_fetch | Tìm kiếm & duyệt web |
| group:ui | browser, canvas | Điều khiển trình duyệt |
| group:memory | memory_search, memory_get | Bộ nhớ lâu dài |
| group:automation | cron, gateway | Tự động hóa định kỳ |
| group:sessions | sessions_list, sessions_send... | Quản lý phiên |
| group:messaging | message | Gửi tin nhắn |

### Các nhóm quan trọng nhất

**group:fs — Làm việc với file.** Cho phép Agent đọc, tạo, chỉnh sửa file trên máy của bạn — tool nền tảng cho hầu hết mọi tác vụ. `read`: đọc file (an toàn nhất). `write`: tạo/ghi đè file (cẩn thận khi cấp quyền). `edit`: chỉnh sửa một phần file. `apply_patch`: áp dụng diff patch, dùng nhiều cho task dev.

**group:web — Tìm kiếm & duyệt web.** `web_search`: tìm kiếm như Google, Agent tự tìm thông tin mới nhất. `web_fetch`: đọc nội dung trang web, tóm tắt, trích xuất dữ liệu.

**group:ui — Điều khiển trình duyệt.** `browser`: mở Chrome/Firefox, click, điền form, chụp screenshot — tool mạnh nhất, Agent tự thao tác trình duyệt như người dùng thật. `canvas`: hiển thị nội dung HTML/UI tương tác (mặc định TẮT).

**group:runtime — Chạy lệnh hệ thống.** Cho phép Agent chạy lệnh shell, script Python, Node.js... Cực kỳ mạnh nhưng cũng cực kỳ nhạy cảm về bảo mật.

> ⚠️ **TRÁNH:** KHÔNG bật group:runtime nếu bạn chưa hiểu rõ tác hại. Agent có thể xóa file, thay đổi cài đặt hệ thống nếu nhận lệnh sai.

**group:automation — Lập lịch tác vụ.** `cron`: lập lịch tác vụ chạy định kỳ (hàng giờ, hàng ngày...), kết hợp với HEARTBEAT.md để tạo automation hoàn chỉnh. `gateway`: quản lý Gateway service từ trong chat — restart, check status...

### Nguyên tắc tối thiểu quyền

Cách bật/tắt tool được khai báo trong SOUL.md:

```text
# Tools Policy
ENABLED: read, write, edit, web_search, web_fetch, browser, cron, message, memory_search
DISABLED: exec, bash, process, canvas, nodes
```

Ví dụ trên tắt exec/bash vì đây là agent marketing — không cần chạy code. Nguyên tắc: **chỉ bật đúng những tool cần thiết cho công việc của agent đó**. Với người mới, bắt đầu với: `read, write, web_search, web_fetch, message`. Sau đó mở rộng dần khi cần.

## Skills & ClawHub — 47,000+ khả năng mở rộng

Một Skill là file SKILL.md chứa hướng dẫn ngôn ngữ tự nhiên kết hợp YAML metadata — **không phải code, không cần lập trình**. ClawHub là registry công khai chứa hơn 47,000 Skills do cộng đồng đóng góp; từ tháng 2/2026 tích hợp quét virus tự động bằng VirusTotal để lọc Skills độc hại.

### Các danh mục Skills nổi bật

| Danh mục | Số lượng Skills | Ví dụ nổi bật |
| --- | --- | --- |
| Productivity | 2,400+ | gog (Google Workspace), obsidian, notion, calendar |
| Development | 2,100+ | github, gitlab, docker, terminal, database |
| Business | 1,800+ | crm, shopify, quickbooks, hubspot, jira |
| AI/ML | 1,500+ | imagen, whisper, elevenlabs, replicate |
| Web | 1,200+ | scraper, screenshot, puppeteer, playwright |
| Social/Messaging | 900+ | telegram-bot, discord-bot, slack, zalo |
| Finance | 700+ | binance, stock-data, accounting |
| Media | 600+ | youtube, spotify, podcast, video-edit |

### Top 8 Skills được dùng nhiều nhất

1. **gog — Google Workspace toàn bộ.** Tích hợp Gmail, Calendar, Tasks, Drive, Docs, Sheets trong một Skill. Setup: chạy "gog auth" → OAuth browser window. Đây là Skill số 1 cho automation văn phòng.
2. **tavily — AI-Optimized Web Search.** Web search thiết kế riêng cho AI agents — kết quả structured, ít nhiễu hơn Google thông thường. Free: 1,000 credits/tháng. Dùng thay web_search mặc định cho research tasks.
3. **capability-evolver — Agent tự cải thiện bản thân.** 35,000+ lượt cài — Skill phổ biến nhất ClawHub. Agent tự monitor hiệu suất, phát hiện khoảng trống, tự đề xuất và cài Skill mới. Dùng sau khi đã setup ổn định 2–3 tuần.
4. **browser-automation — Làm bất cứ điều gì trên web.** Điều khiển Chrome để điền form, đăng nhập website, scrape dữ liệu, chụp screenshot tự động. Không cần API — Agent dùng như người thật.
5. **github — Quản lý code & dự án.** Đọc/tạo issues, pull requests, quản lý repository. Dùng cho báo cáo tiến độ sprint, tóm tắt code review, auto-changelog.
6. **obsidian — Quản lý kiến thức.** Đọc và viết vào Obsidian vault, tạo note tự động, link giữa khái niệm, xây knowledge base từ conversations.
7. **memory-logging — Ghi nhớ thông minh.** Tự động log lỗi phát sinh, bài học rút ra, sở thích người dùng vào MEMORY.md. Agent học từ kinh nghiệm và không lặp lại sai lầm cũ. Cài từ đầu ngay khi setup.
8. **telegram-bot — Điều khiển bot Telegram.** Gửi tin nhắn, hình ảnh, file vào nhóm/channel Telegram theo lịch hoặc sự kiện. Kết hợp với HEARTBEAT.md để auto-post. Đây là cầu nối quan trọng nhất giữa Agent và người dùng Việt Nam.

### Cách cài Skill từ ClawHub

Tìm Skill → Click Install trong UI → Điền config API key, token... → Restart & test.

Hoặc trong chat với Agent: "Cài skill gog cho tôi" — Agent tìm trên ClawHub, hướng dẫn từng bước lấy Google OAuth token, tự động cấu hình và test kết nối.

> ⚠️ Hãy đọc SKILL.md của bất kỳ Skill bên thứ ba nào **TRƯỚC KHI** cài. Một số Skill yêu cầu quyền truy cập rộng vào hệ thống — cần hiểu rõ trước khi chấp nhận. Với doanh nghiệp, nên dùng Skills từ ClawHub official (có dấu tick xanh) hoặc tự viết Skills riêng để đảm bảo an toàn. Chi tiết về cảnh báo Skills độc hại xem [bài 5 trong series](/bai-viet/multi-agent-bao-mat-vps-openclaw/).

## Tích hợp kênh giao tiếp

OpenClaw hỗ trợ 12+ kênh giao tiếp. Bạn ra lệnh cho Agent từ bất kỳ đâu — điện thoại, máy tính, thậm chí từ xe hơi — thông qua ứng dụng nhắn tin bạn đã quen dùng.

| Kênh | Phổ biến tại VN | Đặc điểm |
| --- | --- | --- |
| **Telegram** | Rất cao | Khuyến nghị #1. Bot API mạnh, miễn phí, hỗ trợ file lớn, nhóm |
| **Discord** | Cao (game/dev) | Tốt cho team dev. Hỗ trợ slash commands, embeds, reaction |
| **WhatsApp** | Rất cao | Quen thuộc nhất nhưng cần WhatsApp Business API (có phí) |
| **Slack** | Doanh nghiệp | Tốt nhất cho môi trường doanh nghiệp, tích hợp nhiều app |
| **Zalo** | Việt Nam | Phổ biến tại VN. Cần Zalo OA API. Tốt cho khách hàng VN |
| **Signal** | An toàn | Bảo mật cao nhất. Dùng khi cần riêng tư tuyệt đối |
| **iMessage** | iPhone/Mac | Chỉ hoạt động trên macOS. Tích hợp tự nhiên với Apple |
| **Google Chat** | Google Workspace | Tốt nếu công ty dùng Google Workspace toàn bộ |

### Thiết lập Telegram (khuyến nghị)

Telegram là kênh phổ biến nhất và dễ thiết lập nhất — 3 bước:

1. Mở Telegram, tìm @BotFather. Chạy lệnh /newbot, đặt tên cho bot (ví dụ: ArinaAIBot)
2. Sao chép Bot Token mà BotFather cung cấp (dạng: `123456:ABCDEF...`)
3. Trong wizard OpenClaw, chọn "Telegram", dán token vào. Agent sẽ tự kết nối

Sau khi kết nối, thử ngay: mở chat với bot Telegram của bạn, gõ "Xin chào! Cho tôi biết bạn có thể làm gì?" — Agent sẽ liệt kê các Skills đã cài và khả năng hiện có.

### Thiết lập Zalo (cho thị trường Việt Nam)

Nếu khách hàng hoặc đội nhóm của bạn dùng Zalo, đây là lựa chọn tốt. Cần: Zalo Official Account (OA) đã được duyệt và Zalo OA API key.

| Bước | Hành động | Ghi chú |
| --- | --- | --- |
| 1 | Tạo Zalo Official Account tại oa.zalo.me | Cần xác minh CMND/CCCD hoặc đăng ký doanh nghiệp |
| 2 | Tạo Zalo App tại developers.zalo.me | Lấy App ID và Secret Key |
| 3 | Cài Skill "zalo" từ ClawHub | Điền App ID, Secret, Access Token |
| 4 | Test qua Zalo OA của bạn | Gửi tin nhắn test cho OA |

> 💡 Một agent có thể kết nối đồng thời nhiều kênh — ví dụ nhận lệnh từ Telegram (cá nhân) VÀ trả kết quả vào Slack (team), tất cả từ cùng một Gateway. Nếu chạy trên VPS 24/7, agent sẽ phản hồi ngay cả khi máy tính cá nhân của bạn tắt (chi tiết ở [bài 5](/bai-viet/multi-agent-bao-mat-vps-openclaw/)).

## Bài tiếp theo trong series

- **Bài 4:** [21 use case OpenClaw thực chiến](/bai-viet/21-use-case-openclaw-thuc-chien/) — từ tiết kiệm 5 giờ/tuần đến tự động hóa kinh doanh
- Bài 5: Multi-Agent, bảo mật và chạy 24/7 trên VPS
- Bài 6: OpenClaw hay Manus AI? Lộ trình 30 ngày làm chủ
- [Bài 1](/bai-viet/openclaw-la-gi/) · [Bài 2](/bai-viet/cai-dat-va-cau-hinh-openclaw/)

## Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn cộng đồng và [OpenClaw](https://openclaw.ai/) + [ClawHub](https://clawhub.ai/) — có biên tập lại cấu trúc theo phong cách LearnWithHuy.

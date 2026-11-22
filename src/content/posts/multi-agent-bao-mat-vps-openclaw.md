---
title: "Multi-Agent, bảo mật và chạy OpenClaw 24/7 trên VPS"
description: "Bài 5 series OpenClaw: khi nào cần nhiều Agent trong cùng Gateway, cách các Agent giao tiếp qua sessions, 6 quy tắc bảo mật bắt buộc, và hướng dẫn triển khai VPS chi phí 3–5 USD/tháng."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-17"
cover: "/images/covers/posts/multi-agent-bao-mat-vps-openclaw.jpg"
views: 720
---

Sau khi đã quen với một Agent duy nhất ([bài 2](/bai-viet/cai-dat-va-cau-hinh-openclaw/)) và các use case thực chiến ([bài 4](/bai-viet/21-use-case-openclaw-thuc-chien/)), bài này đưa bạn lên hai cấp độ tiếp theo: **chạy nhiều Agent song song** và **triển khai vận hành 24/7 một cách an toàn**.

## Multi-Agent — xây dựng đội AI

Multi-Agent là tính năng cho phép chạy nhiều Agent độc lập trong cùng một Gateway. Mỗi Agent có workspace riêng, bộ nhớ riêng, và có thể "giao tiếp" với nhau thông qua sessions.

### Khi nào cần Multi-Agent?

- **Cần cách ly dữ liệu:** Agent Marketing không được thấy dữ liệu của Agent HR
- **Cần quyền truy cập khác nhau:** Agent Dev có quyền exec; Agent Content không có
- **Cần bộ nhớ riêng biệt:** mỗi dự án hoặc khách hàng có Agent riêng
- **Tăng throughput:** nhiều tác vụ song song không phải chờ nhau

### Đội AI 3 Agent tiêu biểu

Một cấu hình phổ biến: **Agent Content** (Marketing & viết lách) → **Agent Research** (Tìm kiếm & phân tích) → **Agent Ops** (Email & lịch trình).

Cách tạo Agent mới:

```bash
openclaw agent create --name 'content-agent' --workspace ./workspace-content
openclaw agent create --name 'research-agent' --workspace ./workspace-research
```

Mỗi workspace có SOUL.md riêng, TOOLS.md riêng. Kết nối kênh riêng: agent 1 dùng Telegram, agent 2 dùng Slack.

### Agent giao tiếp với nhau

Các Agent có thể nhận và gửi task cho nhau thông qua sessions. Ví dụ thực tế: Agent Marketing nhận yêu cầu từ bạn, chuyển Research Agent tìm dữ liệu, nhận kết quả về và viết nội dung.

```text
# Luồng multi-agent:
Bạn -> Agent Marketing: 'Viết bài về xu hướng AI tháng 3/2026'
Agent Marketing -> Agent Research: 'Tìm 10 nguồn tin uy tín về AI trends tháng 3/2026'
Agent Research: Tìm kiếm, tổng hợp, trả kết quả về
Agent Marketing: Dùng kết quả viết bài, trả bạn bài hoàn chỉnh
```

> 💡 Multi-Agent thực sự hữu ích khi bạn đã quen với single agent và muốn mở rộng quy mô. Bắt đầu với 1 agent, thêm dần khi cần. Đặt tên Agent rõ ràng theo chức năng: arina-marketing, arina-dev, arina-cs (customer support). Dễ quản lý và ít nhầm lẫn hơn.

## Bảo mật — phần quan trọng nhất

OpenClaw chạy cục bộ với dữ liệu được mã hóa trên máy của bạn — đây là ưu điểm bảo mật lớn nhất. Tuy nhiên, vẫn cần cấu hình đúng để tránh các rủi ro phổ biến.

### Cảnh báo: Skills độc hại trên ClawHub

⚠️ Phát hiện tháng 2/2026: trong 2,857 skills được audit trên ClawHub, có **341 skills độc hại** (chiến dịch "ClawHavoc"). Một skill độc hại có thể đọc file, gửi dữ liệu ra ngoài, hoặc thực thi lệnh nguy hiểm.

| Dấu hiệu Skill AN TOÀN | Dấu hiệu Skill NGHI NGỜ |
| --- | --- |
| 100+ stars, nhiều người dùng | Stars = 0, mới upload |
| Author có profile rõ ràng | Author ẩn danh, tên ngẫu nhiên |
| SKILL.md giải thích rõ code làm gì | SKILL.md mơ hồ, thiếu documentation |
| Được featured trên ClawHub official | Không có review nào |
| Source code ngắn, dễ đọc | Code obfuscated, nhiều base64 |

### 6 quy tắc bảo mật bắt buộc

1. **Chỉ cài Skills đã được verify:** Chọn skills có 100+ stars, đọc SKILL.md kỹ, ưu tiên skills được featured chính thức trên clawhub.ai.
2. **Nguyên tắc tối thiểu quyền:** Chỉ bật tool mà Agent thực sự cần. Không bao giờ bật exec/bash cho agent không cần chạy code.
3. **Không dùng số cá nhân cho WhatsApp automation:** Dùng số điện thoại doanh nghiệp riêng biệt. Nếu bị ban sẽ mất số luôn.
4. **Kiểm tra Canvas Host:** Mặc định Canvas bind 0.0.0.0 (mọi thiết bị trong mạng LAN có thể truy cập). Đổi sang 127.0.0.1 nếu không cần truy cập từ thiết bị khác.
5. **Không cấp quyền xóa file vĩnh viễn:** Cấu hình trong SOUL.md: Agent phải xin xác nhận trước khi xóa bất kỳ file nào.
6. **Dùng biến môi trường cho secret:** Không hardcode API key, token trong SOUL.md hay AGENTS.md. Lưu trong file .env.

## Triển khai trên VPS — hoạt động 24/7

Nếu muốn Agent hoạt động liên tục kể cả khi máy tính cá nhân tắt, hãy triển khai lên VPS (Virtual Private Server). Chi phí VPS tối thiểu khoảng 3–5 USD/tháng.

| Nhà cung cấp | Gói phù hợp | Chi phí/tháng | Ghi chú |
| --- | --- | --- | --- |
| DigitalOcean | Droplet 2GB RAM | $14 | Dễ dùng nhất, có tutorial chính thức OpenClaw |
| Vultr | 2GB RAM, SSD | $12 | Tốc độ cao, nhiều datacenter châu Á |
| Linode (Akamai) | 2GB RAM | $12 | Ổn định, hỗ trợ tốt |
| AWS Lightsail | 2GB RAM | $10 | Phù hợp nếu đã dùng AWS ecosystem |
| VPS Việt Nam | VinaHost, Hostinger | $5–10 | Latency thấp hơn cho user VN |

### Cài đặt OpenClaw trên VPS (Ubuntu)

```bash
# 1. Kết nối SSH vào VPS
ssh root@your-vps-ip

# 2. Cài Node.js 24
curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
apt-get install -y nodejs

# 3. Cài OpenClaw
npm install -g openclaw@latest

# 4. Chạy onboarding và cài daemon (tự khởi động)
openclaw onboard --install-daemon
```

> 💡 Khuyến nghị tối thiểu: VPS 2GB RAM, SSD, Ubuntu 22.04 LTS. Với 2–3 Agent chạy song song cần 4GB RAM.
>
> **Luôn backup thư mục workspace định kỳ.** SOUL.md, AGENTS.md, MEMORY.md là "não" của Agent — mất đi mất khá nhiều công thiết lập lại.

## Bài tiếp theo trong series

- **Bài 6:** [OpenClaw hay Manus AI? Chọn công cụ và lộ trình 30 ngày](/bai-viet/openclaw-vs-manus-lo-trinh-30-ngay/)
- [Bài 1](/bai-viet/openclaw-la-gi/) · [Bài 2](/bai-viet/cai-dat-va-cau-hinh-openclaw/) · [Bài 3](/bai-viet/tools-skills-va-tich-hop-kenh-openclaw/) · [Bài 4](/bai-viet/21-use-case-openclaw-thuc-chien/)

## Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn cộng đồng và [OpenClaw](https://openclaw.ai/) — có biên tập lại cấu trúc theo phong cách LearnWithHuy. Các số liệu bảo mật và giá VPS theo tài liệu gốc, nên kiểm tra lại tại thời điểm bạn đọc.

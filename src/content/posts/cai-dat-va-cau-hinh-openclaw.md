---
title: "Cài đặt và cấu hình OpenClaw trong 30 phút"
description: "Bài 2 series OpenClaw: 3 phương pháp cài đặt, wizard thiết lập 4 bước, cách chọn LLM, và hướng dẫn viết các file workspace quan trọng nhất — SOUL.md, AGENTS.md và HEARTBEAT.md."
topic: "cong-cu-ai"
date: "2026-11-17"
cover: "/images/covers/posts/cai-dat-va-cau-hinh-openclaw.jpg"
views: 880
---

Sau khi hiểu OpenClaw là gì ([bài 1](/bai-viet/openclaw-la-gi/)), bài này sẽ đưa bạn từ cài đặt đến có một Agent "hiểu mình" — thông qua các file cấu hình workspace.

## Yêu cầu hệ thống

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị |
| --- | --- | --- |
| Hệ điều hành | macOS, Linux, Windows (WSL) | macOS hoặc Ubuntu Linux |
| Node.js | v22.16 trở lên | v24 (LTS mới nhất) |
| RAM | 1 GB (chỉ Gateway) | 4 GB trở lên |
| Kết nối Internet | Bắt buộc | Ổn định, tốc độ cao |
| API Key | Anthropic, OpenAI, xAI, hoặc Ollama (local) | Claude API từ Anthropic |

## 3 phương pháp cài đặt

Có 3 phương pháp cài đặt OpenClaw. Với người mới, khuyến nghị dùng **One-Liner (phương pháp 1)** — nhanh nhất và ít gặp lỗi nhất.

### Phương pháp 1: One-Liner (khuyến nghị)

Dán lệnh sau vào Terminal (macOS/Linux) hoặc WSL (Windows) và nhấn Enter:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

Lệnh này tự động: kiểm tra và cài Node.js nếu chưa có, tải OpenClaw, và chạy wizard thiết lập ban đầu.

### Phương pháp 2: Cài qua npm

```bash
npm install -g openclaw@latest
# Hoặc dùng pnpm:
pnpm add -g openclaw@latest
```

### Phương pháp 3: Docker (cho VPS — hoạt động 24/7)

```bash
# Tạo file docker-compose.yml và file .env với API key
docker compose up -d
# OpenClaw sẽ chạy nền, tự khởi động lại nếu server reboot
```

## Chạy wizard thiết lập

Sau khi cài, chạy lệnh onboarding — wizard sẽ hướng dẫn từng bước:

```bash
openclaw onboard
# Hoặc cài daemon (tự khởi động cùng máy):
openclaw onboard --install-daemon
```

Wizard gồm 4 bước: **Kết nối LLM** (nhập API key) → **Tạo Gateway** (daemon service) → **Chọn kênh** (Telegram/Discord) → **Cài Skills** (ClawHub).

### Kết nối LLM — chọn bộ não cho Agent

| LLM | Ưu điểm | Nhược điểm | Phù hợp |
| --- | --- | --- | --- |
| Claude (Anthropic) | Phân tích sâu, an toàn, ngữ cảnh dài | Phí theo token | Công việc quan trọng, phức tạp |
| GPT-5 (OpenAI) | Đa năng, phổ biến, nhiều tích hợp sẵn | Phí cao hơn | Tổng quát, đa tác vụ |
| DeepSeek | Rẻ nhất, xử lý code tốt | Hạn chế một số chủ đề | Dev, code, chi phí thấp |
| Ollama (local) | Miễn phí 100%, riêng tư tuyệt đối | Cần máy mạnh, chậm hơn | Dữ liệu cực nhạy cảm |

> Nhiều người dùng cộng đồng chọn Claude (Anthropic) làm LLM chính cho OpenClaw vì xử lý ngữ cảnh dài và phân tích sâu tốt. Chi phí thực tế rất hợp lý — một Agent hoạt động cả tháng thường tốn 10–30 USD tùy mức độ sử dụng.
>
> Để tiết kiệm chi phí: cấu hình Agent dùng model nhẹ hơn (claude-haiku, gpt-4o-mini) cho các tác vụ đơn giản, chỉ dùng Opus/GPT-5 khi cần phân tích phức tạp.

## Cấu hình workspace — "não bộ" của Agent

Sau khi cài đặt, bước quan trọng nhất là viết các file cấu hình workspace. Đây là nơi bạn "dạy" Agent hiểu bạn là ai, công việc bạn làm gì, và Agent cần hoạt động theo phong cách nào:

| File | Vai trò | Ví dụ nội dung |
| --- | --- | --- |
| **SOUL.md** | Tính cách, giọng điệu, phạm vi hoạt động | Tên agent, ngôn ngữ phản hồi, lĩnh vực chuyên môn |
| **AGENTS.md** | Quy trình làm việc được lập trình sẵn | Workflow xử lý email, quy trình tạo báo cáo |
| **MEMORY.md** | Quy tắc ghi nhớ lâu dài | Thông tin về bạn, công ty, các sở thích |
| **TOOLS.md** | Cấu hình tool cụ thể cho môi trường | Đường dẫn file, API endpoint riêng |
| **USER.md** | Hồ sơ người dùng | Tên, vai trò, ngữ cảnh công việc |
| **HEARTBEAT.md** | Tác vụ chạy định kỳ | Kiểm tra email mỗi 30 phút, báo cáo hàng ngày 8h |
| **BOOT.md** | Script chạy khi khởi động | Lệnh chào hỏi, kiểm tra trạng thái hệ thống |

### SOUL.md — định nghĩa tính cách Agent

SOUL.md là file quan trọng nhất. Nó định nghĩa "linh hồn" của Agent — từ tên, giọng điệu, đến phạm vi hoạt động và các quy tắc cốt lõi. Mẫu cơ bản:

```text
# Identity
Tên tôi là Arina, trợ lý AI của công ty.
Tôi hoạt động dưới sự điều hành của Trần Văn A - Giám đốc.

# Ngôn ngữ
Luôn trả lời bằng tiếng Việt trừ khi được yêu cầu cụ thể dùng ngôn ngữ khác.

# Phong cách
- Ngắn gọn, súc tích. Không nói dài dòng.
- Chủ động, tự tin. Không hỏi lại nếu yêu cầu đã đủ rõ.
- Báo cáo tiến độ khi làm việc dài.

# Giới hạn
- Không xóa file mà không có xác nhận.
- Không gửi email ra ngoài công ty mà không được duyệt.
- Không truy cập tài khoản tài chính.
```

### AGENTS.md — quy trình làm việc

AGENTS.md chứa các workflow được lập trình sẵn. Khi bạn nói "xử lý email sáng", Agent sẽ theo đúng quy trình này:

**Workflow: Xử lý Email Buổi Sáng**

1. Dùng Skill "gog" để lấy email chưa đọc từ Gmail
2. Phân loại: khẩn cấp / cần phản hồi / chỉ đọc / spam
3. Soạn bản nháp trả lời cho email "cần phản hồi"
4. Gửi danh sách tóm tắt vào Telegram của chủ nhân
5. Đợi xác nhận trước khi gửi bất kỳ email nào

**Workflow: Tạo Báo Cáo Tuần**

1. Lấy dữ liệu từ Google Sheets (Skill "gog")
2. Phân tích xu hướng và điểm nổi bật
3. Tạo file Word báo cáo theo template
4. Gửi file vào kênh Slack #management

### HEARTBEAT.md — tự động hóa định kỳ

```text
# Mỗi ngày lúc 7:30 sáng
- Tóm tắt email chưa đọc, gửi vào Telegram
- Nhắc lịch họp trong ngày

# Mỗi thứ Hai lúc 9:00 sáng
- Tổng hợp task tuần trước, gửi báo cáo tiến độ

# Mỗi ngày cuối tháng lúc 17:00
- Nhắc hoàn thành các báo cáo tháng
```

> 💡 Hai kinh nghiệm đáng nhớ: bắt đầu với SOUL.md ngắn gọn (10–15 dòng), thêm dần theo thời gian khi bạn hiểu hơn về cách Agent phản hồi. Và HEARTBEAT.md cực kỳ hữu ích nhưng cần cẩn thận — chỉ cấu hình tác vụ bạn thực sự muốn chạy tự động và đã kiểm tra kỹ workflow.

### Ba mẫu Agent phổ biến

**Mẫu 1: Agent Marketing** — Identity: trợ lý AI marketing, tiếng Việt mặc định. Phong cách: ngắn gọn, sáng tạo nhưng chuyên nghiệp, hỏi "dùng cho kênh nào?" nếu chưa rõ. Tools được phép: `read, write, web_search, web_fetch, message`. Tools bị cấm: `exec, bash, process`. Không bao giờ: đăng bài trực tiếp lên mạng xã hội mà không có xác nhận; gửi email ra ngoài công ty mà không được duyệt.

**Mẫu 2: Agent Operations** — Identity: trợ lý vận hành. Phong cách: chính xác, ngắn gọn, hành động ngay. Tools được phép: `read, write, edit, web_search, web_fetch, browser, cron, message, memory_search`. Ưu tiên xử lý: yêu cầu khẩn cấp → tác vụ định kỳ → research. Bảo mật: không xóa file khi không có xác nhận "yes delete [tên file]"; không truy cập thư mục /finance/ trừ khi được yêu cầu rõ ràng.

**Mẫu 3: Agent Customer Support** (AGENTS.md workflow) — 1. Đọc câu hỏi, xác định loại: kỹ thuật / giá / chính sách / khiếu nại → 2. Tìm câu trả lời trong Knowledge Base (web_fetch từ docs.company.com) → 3. Nếu tìm thấy: trả lời và hỏi "Bạn cần thêm thông tin gì không?" → 4. Nếu không tìm thấy: "Câu hỏi của bạn đang được chuyển đến team [bộ phận], sẽ có người phản hồi trong [X] giờ làm việc" → 5. Ghi log vào Google Sheets (Skill: gog).

## Bài tiếp theo trong series

- **Bài 3:** [Tools, Skills và tích hợp kênh của OpenClaw](/bai-viet/tools-skills-va-tich-hop-kenh-openclaw/) — 26 công cụ nội tại, 47,000+ Skills trên ClawHub, và thiết lập Telegram/Zalo
- Bài 4: 21 use case thực chiến cho công việc
- Bài 5: Multi-Agent, bảo mật và chạy 24/7 trên VPS
- Bài 6: OpenClaw hay Manus AI? Lộ trình 30 ngày làm chủ
- [Bài 1: OpenClaw là gì?](/bai-viet/openclaw-la-gi/)

## Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn cộng đồng và [documentation OpenClaw](https://openclaw.ai/) — có biên tập lại cấu trúc theo phong cách LearnWithHuy.

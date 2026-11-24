---
title: "OpenClaw: cẩm nang từ cài đặt đến 21 use case thực chiến"
description: "Cẩm nang gộp trọn 6 bài OpenClaw trong một trang: OpenClaw là gì, cài đặt trong 30 phút, tools/skills/tích hợp kênh, chạy 24/7 trên VPS an toàn, 21 use case thực chiến và so sánh với Manus kèm lộ trình 30 ngày."
topic: "ai-agent-va-tu-dong-hoa"
date: "2026-11-24"
cover: "/images/covers/posts/openclaw-la-gi.jpg"
featured: false
views: 180
faq:
  - q: "Cẩm nang này gồm những gì?"
    a: "Toàn bộ 6 bài trước đây đăng riêng giờ gộp trong một trang, chia thành 6 phần đánh số — đọc tuần tự hoặc nhảy tới phần cần đều được."
  - q: "Nên đọc theo thứ tự không?"
    a: "Các phần được xếp theo thứ tự học gợi ý. Đọc lộn vẫn hiểu vì mỗi phần đứng độc lập, nhưng lần đầu học thì nên theo thứ tự. Tổng thời gian đọc khoảng 45 phút."
---

## 01. OpenClaw là gì? AI Agent mã nguồn mở chạy trên máy tính của bạn

Đầu năm 2026, một project nhỏ trên GitHub bắt đầu lan truyền với tốc độ chưa từng có trong lịch sử phần mềm mã nguồn mở. Trong vòng chưa đầy 4 tháng, nó vượt qua React để trở thành project phi tổng hợp được star nhiều nhất mọi thời đại trên GitHub với hơn 300,000 stars. Project đó tên là **OpenClaw**.

Nhưng con số không phải điều quan trọng nhất. OpenClaw đại diện cho một cách tiếp cận hoàn toàn mới với AI: không phải chatbot bạn hỏi rồi đọc câu trả lời, mà là **một AI Agent thực sự làm việc cho bạn** — chạy ngay trên máy tính của bạn, kết nối với các ứng dụng bạn dùng hàng ngày.

Series này (6 bài) tổng hợp từ documentation chính thức và kinh nghiệm cộng đồng để bạn có thể hiểu, cài đặt và khai thác OpenClaw cho công việc thực tế — được thiết kế cho **người không chuyên kỹ thuật**: bạn cần kỹ thuật cơ bản (cài phần mềm, dùng terminal) nhưng không cần biết lập trình.

### OpenClaw là gì?

OpenClaw là một AI Agent mã nguồn mở chạy trực tiếp trên máy tính của bạn. Khác với Claude hay ChatGPT chỉ trả lời câu hỏi trong cửa sổ chat, OpenClaw có thể tự mình: mở ứng dụng, duyệt web, đọc/viết file, chạy lệnh terminal, và thực hiện chuỗi hành động phức tạp — giống như một nhân viên thực sự làm việc trên màn hình máy tính.

Điểm quan trọng cần hiểu ngay: **OpenClaw không thay thế Claude hay ChatGPT** — nó là lớp kết nối giúp LLM (Claude, GPT-5, DeepSeek...) thực sự làm việc trên máy tính của bạn.

#### Lịch sử phát triển

| Thời gian | Sự kiện |
| --- | --- |
| Tháng 11/2025 | Peter Steinberger (lập trình viên Áo) ra mắt "Clawdbot" trên GitHub |
| Tháng 1/2026 | Đổi tên thành "Moltbot" sau tranh chấp nhãn hiệu với Anthropic |
| 28/01/2026 | Đổi tên lần cuối thành "OpenClaw" — tên chính thức hiện tại |
| 2/2026 | Vượt 300,000 GitHub stars, qua mặt React. Peter gia nhập OpenAI |
| 2/2026 | Dự án chuyển sang quản lý bởi Open-Source Foundation |
| 3/2026 | ClawHub đạt 47,000 Skills. Nvidia, Meta, Google đều tích hợp OpenClaw |

#### Vì sao OpenClaw gây sốt?

1. **BYOM — Bring Your Own Model.** Bạn tự mang API key của mình (Claude, GPT-5, DeepSeek, hoặc model local qua Ollama). Dữ liệu không đi qua server của bên thứ ba, chi phí hoàn toàn trong tầm kiểm soát.
2. **Chạy cục bộ — dữ liệu không rời khỏi máy bạn.** Toàn bộ workspace, lịch sử, token xác thực đều được mã hóa và lưu tại máy của bạn. Đây là lý do các doanh nghiệp cần bảo mật dữ liệu chọn OpenClaw thay vì Manus AI hay các cloud agent khác.
3. **Hệ sinh thái Skills khổng lồ.** ClawHub có 47,000+ Skills do cộng đồng đóng góp. Mỗi Skill là một file hướng dẫn giúp Agent hiểu cách tích hợp với một dịch vụ cụ thể: từ Gmail, Google Calendar, Obsidian, GitHub, đến Zalo, Shopify, QuickBooks...
4. **Tương tác qua ứng dụng bạn đã dùng.** Không cần học giao diện mới. Nhắn tin với Agent qua Telegram, Discord, WhatsApp, hoặc Slack — mở Telegram, gõ lệnh, Agent làm việc.

### Kiến trúc & cơ chế hoạt động

Để dùng OpenClaw hiệu quả, bạn cần hiểu 2 khái niệm cốt lõi: **Gateway** (trung tâm điều khiển) và **vòng lặp OODA** (cách Agent "suy nghĩ" và hành động).

#### Gateway — trái tim của hệ thống

Gateway là một dịch vụ Node.js chạy nền (background service) trên máy tính hoặc VPS của bạn. Nó đóng vai trò trung tâm điều phối, kết nối 3 thành phần:

- **LLM (Bộ não):** Claude, GPT-5, DeepSeek, hoặc Ollama (model local). Bạn cung cấp API key, Gateway gửi yêu cầu và nhận phản hồi.
- **Kênh giao tiếp (Giao diện):** Telegram, Discord, WhatsApp... Bạn nhắn tin từ đây, Agent nhận lệnh và gửi kết quả lại đây.
- **Tools & Skills (Cánh tay):** Các công cụ để Agent thực sự hành động trên máy tính và kết nối với dịch vụ ngoài.

#### Vòng lặp OODA — cách Agent xử lý mọi việc

OODA (Observe — Orient — Decide — Act) là vòng lặp mà Agent lặp đi lặp lại cho đến khi hoàn thành nhiệm vụ. Hiểu vòng lặp này giúp bạn biết cách viết lệnh hiệu quả và tại sao đôi khi Agent cần nhiều bước để hoàn thành một việc:

| Giai đoạn | Agent làm gì |
| --- | --- |
| **OBSERVE (Quan sát)** | Chụp màn hình, đọc file, lấy dữ liệu từ hệ thống |
| **ORIENT (Định hướng)** | Gửi ảnh/dữ liệu lên LLM (Claude/GPT) để phân tích |
| **DECIDE (Quyết định)** | LLM xác định hành động phù hợp với yêu cầu người dùng |
| **ACT (Hành động)** | Thực thi: click chuột, gõ bàn phím, chạy lệnh, gửi tin |

Vòng lặp liên tục: sau mỗi hành động, Agent tiếp tục quan sát kết quả và lặp lại cho đến khi hoàn thành nhiệm vụ.

### Nên đọc OpenClaw như thế nào?

> OpenClaw về bản chất là "WordPress của AI Agent" — cực kỳ mạnh và linh hoạt, nhưng cần hiểu cách vận hành để tránh rủi ro bảo mật. Đừng cấp cho Agent nhiều quyền hơn mức cần thiết: bắt đầu với các tool cơ bản, mở rộng dần khi đã quen.

Sau bài này, bạn sẽ có thể: hiểu OpenClaw hoạt động ra sao và tại sao nó khác biệt với các AI tool khác; cài đặt và cấu hình trong 30 phút; tích hợp Telegram/Discord/Slack; cài Skills từ ClawHub; xây quy trình tự động hóa; và thiết lập Multi-Agent để có đội AI làm việc song song.

### Bài tiếp theo trong series

- **Bài 2:** Cài đặt và cấu hình OpenClaw trong 30 phút — 3 phương pháp cài, wizard thiết lập, và cách viết SOUL.md "linh hồn" của Agent
- Bài 3: Tools, Skills và tích hợp kênh giao tiếp
- Bài 4: 21 use case thực chiến cho công việc
- Bài 5: Multi-Agent, bảo mật và chạy 24/7 trên VPS
- Bài 6: OpenClaw hay Manus AI? Lộ trình 30 ngày làm chủ

### Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn cộng đồng và [documentation OpenClaw](https://openclaw.ai/) — có biên tập lại cấu trúc theo phong cách LearnWithHuy.
- Kho mã nguồn: [github.com/openclaw](https://github.com/openclaw)

---

## 02. Cài đặt và cấu hình OpenClaw trong 30 phút

Sau khi hiểu OpenClaw là gì (bài 1), bài này sẽ đưa bạn từ cài đặt đến có một Agent "hiểu mình" — thông qua các file cấu hình workspace.

### Yêu cầu hệ thống

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị |
| --- | --- | --- |
| Hệ điều hành | macOS, Linux, Windows (WSL) | macOS hoặc Ubuntu Linux |
| Node.js | v22.16 trở lên | v24 (LTS mới nhất) |
| RAM | 1 GB (chỉ Gateway) | 4 GB trở lên |
| Kết nối Internet | Bắt buộc | Ổn định, tốc độ cao |
| API Key | Anthropic, OpenAI, xAI, hoặc Ollama (local) | Claude API từ Anthropic |

### 3 phương pháp cài đặt

Có 3 phương pháp cài đặt OpenClaw. Với người mới, khuyến nghị dùng **One-Liner (phương pháp 1)** — nhanh nhất và ít gặp lỗi nhất.

#### Phương pháp 1: One-Liner (khuyến nghị)

Dán lệnh sau vào Terminal (macOS/Linux) hoặc WSL (Windows) và nhấn Enter:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

Lệnh này tự động: kiểm tra và cài Node.js nếu chưa có, tải OpenClaw, và chạy wizard thiết lập ban đầu.

#### Phương pháp 2: Cài qua npm

```bash
npm install -g openclaw@latest
pnpm add -g openclaw@latest
```

#### Phương pháp 3: Docker (cho VPS — hoạt động 24/7)

```bash
# Tạo file docker-compose.yml và file .env với API key
docker compose up -d
# OpenClaw sẽ chạy nền, tự khởi động lại nếu server reboot
```

### Chạy wizard thiết lập

Sau khi cài, chạy lệnh onboarding — wizard sẽ hướng dẫn từng bước:

```bash
openclaw onboard
# Hoặc cài daemon (tự khởi động cùng máy):
openclaw onboard --install-daemon
```

Wizard gồm 4 bước: **Kết nối LLM** (nhập API key) → **Tạo Gateway** (daemon service) → **Chọn kênh** (Telegram/Discord) → **Cài Skills** (ClawHub).

#### Kết nối LLM — chọn bộ não cho Agent

| LLM | Ưu điểm | Nhược điểm | Phù hợp |
| --- | --- | --- | --- |
| Claude (Anthropic) | Phân tích sâu, an toàn, ngữ cảnh dài | Phí theo token | Công việc quan trọng, phức tạp |
| GPT-5 (OpenAI) | Đa năng, phổ biến, nhiều tích hợp sẵn | Phí cao hơn | Tổng quát, đa tác vụ |
| DeepSeek | Rẻ nhất, xử lý code tốt | Hạn chế một số chủ đề | Dev, code, chi phí thấp |
| Ollama (local) | Miễn phí 100%, riêng tư tuyệt đối | Cần máy mạnh, chậm hơn | Dữ liệu cực nhạy cảm |

> Nhiều người dùng cộng đồng chọn Claude (Anthropic) làm LLM chính cho OpenClaw vì xử lý ngữ cảnh dài và phân tích sâu tốt. Chi phí thực tế rất hợp lý — một Agent hoạt động cả tháng thường tốn 10–30 USD tùy mức độ sử dụng.
>
> Để tiết kiệm chi phí: cấu hình Agent dùng model nhẹ hơn (claude-haiku, gpt-4o-mini) cho các tác vụ đơn giản, chỉ dùng Opus/GPT-5 khi cần phân tích phức tạp.

### Cấu hình workspace — "não bộ" của Agent

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

#### SOUL.md — định nghĩa tính cách Agent

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

#### AGENTS.md — quy trình làm việc

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

#### HEARTBEAT.md — tự động hóa định kỳ

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

#### Ba mẫu Agent phổ biến

**Mẫu 1: Agent Marketing** — Identity: trợ lý AI marketing, tiếng Việt mặc định. Phong cách: ngắn gọn, sáng tạo nhưng chuyên nghiệp, hỏi "dùng cho kênh nào?" nếu chưa rõ. Tools được phép: `read, write, web_search, web_fetch, message`. Tools bị cấm: `exec, bash, process`. Không bao giờ: đăng bài trực tiếp lên mạng xã hội mà không có xác nhận; gửi email ra ngoài công ty mà không được duyệt.

**Mẫu 2: Agent Operations** — Identity: trợ lý vận hành. Phong cách: chính xác, ngắn gọn, hành động ngay. Tools được phép: `read, write, edit, web_search, web_fetch, browser, cron, message, memory_search`. Ưu tiên xử lý: yêu cầu khẩn cấp → tác vụ định kỳ → research. Bảo mật: không xóa file khi không có xác nhận "yes delete [tên file]"; không truy cập thư mục /finance/ trừ khi được yêu cầu rõ ràng.

**Mẫu 3: Agent Customer Support** (AGENTS.md workflow) — 1. Đọc câu hỏi, xác định loại: kỹ thuật / giá / chính sách / khiếu nại → 2. Tìm câu trả lời trong Knowledge Base (web_fetch từ docs.company.com) → 3. Nếu tìm thấy: trả lời và hỏi "Bạn cần thêm thông tin gì không?" → 4. Nếu không tìm thấy: "Câu hỏi của bạn đang được chuyển đến team [bộ phận], sẽ có người phản hồi trong [X] giờ làm việc" → 5. Ghi log vào Google Sheets (Skill: gog).

### Bài tiếp theo trong series

- **Bài 3:** Tools, Skills và tích hợp kênh của OpenClaw — 26 công cụ nội tại, 47,000+ Skills trên ClawHub, và thiết lập Telegram/Zalo
- Bài 4: 21 use case thực chiến cho công việc
- Bài 5: Multi-Agent, bảo mật và chạy 24/7 trên VPS
- Bài 6: OpenClaw hay Manus AI? Lộ trình 30 ngày làm chủ
- Bài 1: OpenClaw là gì?

### Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn cộng đồng và [documentation OpenClaw](https://openclaw.ai/) — có biên tập lại cấu trúc theo phong cách LearnWithHuy.

---

## 03. Tools, Skills và tích hợp kênh của OpenClaw

Nếu Tools là "cơ quan", thì Skills là "sách giáo khoa" dạy Agent cách dùng cơ quan đó để thực hiện việc gì. Bài này đi qua ba lớp năng lực của OpenClaw: **Tools** (26 công cụ nội tại), **Skills** (mở rộng qua ClawHub) và **kênh giao tiếp** (Telegram, Zalo, Slack...).

### Tools — 26 công cụ nội tại

Tools là các "cơ quan" quyết định Agent **CÓ THỂ** làm gì. Mặc định OpenClaw bật 22 tool và tắt 4 tool. Hiểu từng nhóm tool giúp bạn cấu hình đúng quyền cho Agent và biết giới hạn của nó.

#### 8 nhóm tool của OpenClaw

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

#### Các nhóm quan trọng nhất

**group:fs — Làm việc với file.** Cho phép Agent đọc, tạo, chỉnh sửa file trên máy của bạn — tool nền tảng cho hầu hết mọi tác vụ. `read`: đọc file (an toàn nhất). `write`: tạo/ghi đè file (cẩn thận khi cấp quyền). `edit`: chỉnh sửa một phần file. `apply_patch`: áp dụng diff patch, dùng nhiều cho task dev.

**group:web — Tìm kiếm & duyệt web.** `web_search`: tìm kiếm như Google, Agent tự tìm thông tin mới nhất. `web_fetch`: đọc nội dung trang web, tóm tắt, trích xuất dữ liệu.

**group:ui — Điều khiển trình duyệt.** `browser`: mở Chrome/Firefox, click, điền form, chụp screenshot — tool mạnh nhất, Agent tự thao tác trình duyệt như người dùng thật. `canvas`: hiển thị nội dung HTML/UI tương tác (mặc định TẮT).

**group:runtime — Chạy lệnh hệ thống.** Cho phép Agent chạy lệnh shell, script Python, Node.js... Cực kỳ mạnh nhưng cũng cực kỳ nhạy cảm về bảo mật.

> ⚠️ **TRÁNH:** KHÔNG bật group:runtime nếu bạn chưa hiểu rõ tác hại. Agent có thể xóa file, thay đổi cài đặt hệ thống nếu nhận lệnh sai.

**group:automation — Lập lịch tác vụ.** `cron`: lập lịch tác vụ chạy định kỳ (hàng giờ, hàng ngày...), kết hợp với HEARTBEAT.md để tạo automation hoàn chỉnh. `gateway`: quản lý Gateway service từ trong chat — restart, check status...

#### Nguyên tắc tối thiểu quyền

Cách bật/tắt tool được khai báo trong SOUL.md:

```text
ENABLED: read, write, edit, web_search, web_fetch, browser, cron, message, memory_search
DISABLED: exec, bash, process, canvas, nodes
```

Ví dụ trên tắt exec/bash vì đây là agent marketing — không cần chạy code. Nguyên tắc: **chỉ bật đúng những tool cần thiết cho công việc của agent đó**. Với người mới, bắt đầu với: `read, write, web_search, web_fetch, message`. Sau đó mở rộng dần khi cần.

### Skills & ClawHub — 47,000+ khả năng mở rộng

Một Skill là file SKILL.md chứa hướng dẫn ngôn ngữ tự nhiên kết hợp YAML metadata — **không phải code, không cần lập trình**. ClawHub là registry công khai chứa hơn 47,000 Skills do cộng đồng đóng góp; từ tháng 2/2026 tích hợp quét virus tự động bằng VirusTotal để lọc Skills độc hại.

#### Các danh mục Skills nổi bật

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

#### Top 8 Skills được dùng nhiều nhất

1. **gog — Google Workspace toàn bộ.** Tích hợp Gmail, Calendar, Tasks, Drive, Docs, Sheets trong một Skill. Setup: chạy "gog auth" → OAuth browser window. Đây là Skill số 1 cho automation văn phòng.
2. **tavily — AI-Optimized Web Search.** Web search thiết kế riêng cho AI agents — kết quả structured, ít nhiễu hơn Google thông thường. Free: 1,000 credits/tháng. Dùng thay web_search mặc định cho research tasks.
3. **capability-evolver — Agent tự cải thiện bản thân.** 35,000+ lượt cài — Skill phổ biến nhất ClawHub. Agent tự monitor hiệu suất, phát hiện khoảng trống, tự đề xuất và cài Skill mới. Dùng sau khi đã setup ổn định 2–3 tuần.
4. **browser-automation — Làm bất cứ điều gì trên web.** Điều khiển Chrome để điền form, đăng nhập website, scrape dữ liệu, chụp screenshot tự động. Không cần API — Agent dùng như người thật.
5. **github — Quản lý code & dự án.** Đọc/tạo issues, pull requests, quản lý repository. Dùng cho báo cáo tiến độ sprint, tóm tắt code review, auto-changelog.
6. **obsidian — Quản lý kiến thức.** Đọc và viết vào Obsidian vault, tạo note tự động, link giữa khái niệm, xây knowledge base từ conversations.
7. **memory-logging — Ghi nhớ thông minh.** Tự động log lỗi phát sinh, bài học rút ra, sở thích người dùng vào MEMORY.md. Agent học từ kinh nghiệm và không lặp lại sai lầm cũ. Cài từ đầu ngay khi setup.
8. **telegram-bot — Điều khiển bot Telegram.** Gửi tin nhắn, hình ảnh, file vào nhóm/channel Telegram theo lịch hoặc sự kiện. Kết hợp với HEARTBEAT.md để auto-post. Đây là cầu nối quan trọng nhất giữa Agent và người dùng Việt Nam.

#### Cách cài Skill từ ClawHub

Tìm Skill → Click Install trong UI → Điền config API key, token... → Restart & test.

Hoặc trong chat với Agent: "Cài skill gog cho tôi" — Agent tìm trên ClawHub, hướng dẫn từng bước lấy Google OAuth token, tự động cấu hình và test kết nối.

> ⚠️ Hãy đọc SKILL.md của bất kỳ Skill bên thứ ba nào **TRƯỚC KHI** cài. Một số Skill yêu cầu quyền truy cập rộng vào hệ thống — cần hiểu rõ trước khi chấp nhận. Với doanh nghiệp, nên dùng Skills từ ClawHub official (có dấu tick xanh) hoặc tự viết Skills riêng để đảm bảo an toàn. Chi tiết về cảnh báo Skills độc hại xem bài 5 trong series.

### Tích hợp kênh giao tiếp

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

#### Thiết lập Telegram (khuyến nghị)

Telegram là kênh phổ biến nhất và dễ thiết lập nhất — 3 bước:

1. Mở Telegram, tìm @BotFather. Chạy lệnh /newbot, đặt tên cho bot (ví dụ: ArinaAIBot)
2. Sao chép Bot Token mà BotFather cung cấp (dạng: `123456:ABCDEF...`)
3. Trong wizard OpenClaw, chọn "Telegram", dán token vào. Agent sẽ tự kết nối

Sau khi kết nối, thử ngay: mở chat với bot Telegram của bạn, gõ "Xin chào! Cho tôi biết bạn có thể làm gì?" — Agent sẽ liệt kê các Skills đã cài và khả năng hiện có.

#### Thiết lập Zalo (cho thị trường Việt Nam)

Nếu khách hàng hoặc đội nhóm của bạn dùng Zalo, đây là lựa chọn tốt. Cần: Zalo Official Account (OA) đã được duyệt và Zalo OA API key.

| Bước | Hành động | Ghi chú |
| --- | --- | --- |
| 1 | Tạo Zalo Official Account tại oa.zalo.me | Cần xác minh CMND/CCCD hoặc đăng ký doanh nghiệp |
| 2 | Tạo Zalo App tại developers.zalo.me | Lấy App ID và Secret Key |
| 3 | Cài Skill "zalo" từ ClawHub | Điền App ID, Secret, Access Token |
| 4 | Test qua Zalo OA của bạn | Gửi tin nhắn test cho OA |

> 💡 Một agent có thể kết nối đồng thời nhiều kênh — ví dụ nhận lệnh từ Telegram (cá nhân) VÀ trả kết quả vào Slack (team), tất cả từ cùng một Gateway. Nếu chạy trên VPS 24/7, agent sẽ phản hồi ngay cả khi máy tính cá nhân của bạn tắt (chi tiết ở bài 5).

### Bài tiếp theo trong series

- **Bài 4:** 21 use case OpenClaw thực chiến — từ tiết kiệm 5 giờ/tuần đến tự động hóa kinh doanh
- Bài 5: Multi-Agent, bảo mật và chạy 24/7 trên VPS
- Bài 6: OpenClaw hay Manus AI? Lộ trình 30 ngày làm chủ
- Bài 1 · Bài 2

### Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn cộng đồng và [OpenClaw](https://openclaw.ai/) + [ClawHub](https://clawhub.ai/) — có biên tập lại cấu trúc theo phong cách LearnWithHuy.

---

## 04. Multi-Agent, bảo mật và chạy OpenClaw 24/7 trên VPS

Sau khi đã quen với một Agent duy nhất (bài 2) và các use case thực chiến (bài 4), bài này đưa bạn lên hai cấp độ tiếp theo: **chạy nhiều Agent song song** và **triển khai vận hành 24/7 một cách an toàn**.

### Multi-Agent — xây dựng đội AI

Multi-Agent là tính năng cho phép chạy nhiều Agent độc lập trong cùng một Gateway. Mỗi Agent có workspace riêng, bộ nhớ riêng, và có thể "giao tiếp" với nhau thông qua sessions.

#### Khi nào cần Multi-Agent?

- **Cần cách ly dữ liệu:** Agent Marketing không được thấy dữ liệu của Agent HR
- **Cần quyền truy cập khác nhau:** Agent Dev có quyền exec; Agent Content không có
- **Cần bộ nhớ riêng biệt:** mỗi dự án hoặc khách hàng có Agent riêng
- **Tăng throughput:** nhiều tác vụ song song không phải chờ nhau

#### Đội AI 3 Agent tiêu biểu

Một cấu hình phổ biến: **Agent Content** (Marketing & viết lách) → **Agent Research** (Tìm kiếm & phân tích) → **Agent Ops** (Email & lịch trình).

Cách tạo Agent mới:

```bash
openclaw agent create --name 'content-agent' --workspace ./workspace-content
openclaw agent create --name 'research-agent' --workspace ./workspace-research
```

Mỗi workspace có SOUL.md riêng, TOOLS.md riêng. Kết nối kênh riêng: agent 1 dùng Telegram, agent 2 dùng Slack.

#### Agent giao tiếp với nhau

Các Agent có thể nhận và gửi task cho nhau thông qua sessions. Ví dụ thực tế: Agent Marketing nhận yêu cầu từ bạn, chuyển Research Agent tìm dữ liệu, nhận kết quả về và viết nội dung.

```text
Bạn -> Agent Marketing: 'Viết bài về xu hướng AI tháng 3/2026'
Agent Marketing -> Agent Research: 'Tìm 10 nguồn tin uy tín về AI trends tháng 3/2026'
Agent Research: Tìm kiếm, tổng hợp, trả kết quả về
Agent Marketing: Dùng kết quả viết bài, trả bạn bài hoàn chỉnh
```

> 💡 Multi-Agent thực sự hữu ích khi bạn đã quen với single agent và muốn mở rộng quy mô. Bắt đầu với 1 agent, thêm dần khi cần. Đặt tên Agent rõ ràng theo chức năng: arina-marketing, arina-dev, arina-cs (customer support). Dễ quản lý và ít nhầm lẫn hơn.

### Bảo mật — phần quan trọng nhất

OpenClaw chạy cục bộ với dữ liệu được mã hóa trên máy của bạn — đây là ưu điểm bảo mật lớn nhất. Tuy nhiên, vẫn cần cấu hình đúng để tránh các rủi ro phổ biến.

#### Cảnh báo: Skills độc hại trên ClawHub

⚠️ Phát hiện tháng 2/2026: trong 2,857 skills được audit trên ClawHub, có **341 skills độc hại** (chiến dịch "ClawHavoc"). Một skill độc hại có thể đọc file, gửi dữ liệu ra ngoài, hoặc thực thi lệnh nguy hiểm.

| Dấu hiệu Skill AN TOÀN | Dấu hiệu Skill NGHI NGỜ |
| --- | --- |
| 100+ stars, nhiều người dùng | Stars = 0, mới upload |
| Author có profile rõ ràng | Author ẩn danh, tên ngẫu nhiên |
| SKILL.md giải thích rõ code làm gì | SKILL.md mơ hồ, thiếu documentation |
| Được featured trên ClawHub official | Không có review nào |
| Source code ngắn, dễ đọc | Code obfuscated, nhiều base64 |

#### 6 quy tắc bảo mật bắt buộc

1. **Chỉ cài Skills đã được verify:** Chọn skills có 100+ stars, đọc SKILL.md kỹ, ưu tiên skills được featured chính thức trên clawhub.ai.
2. **Nguyên tắc tối thiểu quyền:** Chỉ bật tool mà Agent thực sự cần. Không bao giờ bật exec/bash cho agent không cần chạy code.
3. **Không dùng số cá nhân cho WhatsApp automation:** Dùng số điện thoại doanh nghiệp riêng biệt. Nếu bị ban sẽ mất số luôn.
4. **Kiểm tra Canvas Host:** Mặc định Canvas bind 0.0.0.0 (mọi thiết bị trong mạng LAN có thể truy cập). Đổi sang 127.0.0.1 nếu không cần truy cập từ thiết bị khác.
5. **Không cấp quyền xóa file vĩnh viễn:** Cấu hình trong SOUL.md: Agent phải xin xác nhận trước khi xóa bất kỳ file nào.
6. **Dùng biến môi trường cho secret:** Không hardcode API key, token trong SOUL.md hay AGENTS.md. Lưu trong file .env.

### Triển khai trên VPS — hoạt động 24/7

Nếu muốn Agent hoạt động liên tục kể cả khi máy tính cá nhân tắt, hãy triển khai lên VPS (Virtual Private Server). Chi phí VPS tối thiểu khoảng 3–5 USD/tháng.

| Nhà cung cấp | Gói phù hợp | Chi phí/tháng | Ghi chú |
| --- | --- | --- | --- |
| DigitalOcean | Droplet 2GB RAM | $14 | Dễ dùng nhất, có tutorial chính thức OpenClaw |
| Vultr | 2GB RAM, SSD | $12 | Tốc độ cao, nhiều datacenter châu Á |
| Linode (Akamai) | 2GB RAM | $12 | Ổn định, hỗ trợ tốt |
| AWS Lightsail | 2GB RAM | $10 | Phù hợp nếu đã dùng AWS ecosystem |
| VPS Việt Nam | VinaHost, Hostinger | $5–10 | Latency thấp hơn cho user VN |

#### Cài đặt OpenClaw trên VPS (Ubuntu)

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

### Bài tiếp theo trong series

- **Bài 6:** OpenClaw hay Manus AI? Chọn công cụ và lộ trình 30 ngày
- Bài 1 · Bài 2 · Bài 3 · Bài 4

### Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn cộng đồng và [OpenClaw](https://openclaw.ai/) — có biên tập lại cấu trúc theo phong cách LearnWithHuy. Các số liệu bảo mật và giá VPS theo tài liệu gốc, nên kiểm tra lại tại thời điểm bạn đọc.

---

## 05. 21 use case OpenClaw thực chiến cho công việc

Tổng hợp từ cộng đồng OpenClaw trên Discord, Reddit, Facebook và các diễn đàn công nghệ Việt Nam. Đây là những tình huống người dùng thực tế đã triển khai thành công — không phải lý thuyết. Nếu mới bắt đầu, hãy đọc bài 2 và bài 3 trong series trước.

### Tổng quan theo nhóm

| Nhóm Use Case | Số giờ tiết kiệm/tuần | Độ phức tạp | Thời gian setup |
| --- | --- | --- | --- |
| Năng suất cá nhân | 5–10 giờ | Thấp | 1–2 tiếng |
| Kinh doanh & bán hàng | 10–20 giờ | Trung bình | 3–6 tiếng |
| Nội dung & marketing | 8–15 giờ | Trung bình | 2–4 tiếng |
| Developer & kỹ thuật | 6–12 giờ | Cao | 4–8 tiếng |
| E-commerce & vận hành | 12–25 giờ | Cao | 6–12 tiếng |
| Cộng đồng Việt Nam | 8–18 giờ | Trung bình | 2–5 tiếng |

### Nhóm 1: Năng suất cá nhân

Những automation đơn giản nhất nhưng ROI cao nhất — bắt đầu từ đây nếu bạn mới dùng OpenClaw lần đầu.

**1. Morning Briefing Assistant** (Skills: gog, weather-api). Mỗi sáng 7h, Agent tự động tổng hợp gửi vào Telegram: thời tiết hôm nay + dự báo 3 ngày tới, 5 email quan trọng nhất chưa đọc (tóm tắt 1 câu mỗi cái), lịch họp trong ngày kèm link Meet/Zoom, 3 task ưu tiên cao nhất từ Todoist/Notion. Cộng đồng report: thay thế 5–6 lần mở app mỗi sáng thành 1 tin nhắn. Tiết kiệm: 20–30 phút/ngày = 2+ giờ/tuần.

**2. Email Triage & Smart Reply** (Skills: gog, tavily). Lệnh Telegram: "Xử lý hộp thư đến sáng nay" — Agent phân loại email theo 4 nhóm Urgent/Reply/FYI/Archive, soạn sẵn bản nháp cho 3–5 email cần trả lời chờ bạn review. Với email lặp lại (hỏi giá, hỏi tính năng), Agent trả lời tự động từ KB. Số liệu cộng đồng: 90% email phân loại đúng sau 2 tuần fine-tune, đạt 97%+ sau khi chỉnh SOUL.md thêm context về công ty và sản phẩm.

**3. Household Manager** (Skills: gog, iMessage, calendar). Agent tên "Zosia" quản lý hộ gia đình: theo dõi giờ công babysitter từ tin nhắn, order đồ ăn/tạp hóa qua app, book nhà hàng, nhắc cuộc hẹn gia đình qua iMessage. Đây là case thực tế Peter Steinberger (creator OpenClaw) tự chia sẻ. Bài học: SOUL.md cần viết rõ ngữ cảnh gia đình, không chỉ công việc.

**4. Expense Tracker & Budget Alert** (Skills: gog, banking-parser). Agent đọc sao kê ngân hàng/email receipt hàng ngày lúc 8pm, tự phân loại chi tiêu (ăn uống, mua sắm, giải trí, đầu tư...). Cộng đồng report: 90% accuracy phân loại ngay từ đầu, 97%+ sau 2 tuần dùng + feedback. Gửi cảnh báo Telegram khi chi tiêu vượt ngưỡng. Dữ liệu lưu local hoàn toàn — không upload lên cloud bên thứ ba.

### Nhóm 2: Kinh doanh & bán hàng

Những automation tạo ra doanh thu trực tiếp.

**5. Lead Generation & Scoring Pipeline** (Skills: tavily, browser-automation, gog). Multi-agent setup 3 agent phối hợp: Agent 1 — Scout (scan LinkedIn/Facebook Groups, detect leads phù hợp ICP) → Agent 2 — Researcher (tự động research company: website, size, funding, tech stack) → Agent 3 — Writer (tạo email tiếp cận cá nhân hóa cho từng lead trong <10 phút). Workflow: brief vào shared memory → research → viết email → queue review của bạn trên Telegram.

**6. Invoice Follow-Up Automation** (Skills: gog, stripe-cli). Agent monitor hóa đơn quá hạn, gửi follow-up theo lịch: ngày 3 sau hạn — nhắc nhẹ, thân thiện; ngày 7 — follow-up lần 2, đề xuất hỗ trợ; ngày 14 — escalate với formal notice. Agent viết đúng giọng văn của bạn (cấu hình SOUL.md) và cần xác nhận trước khi gửi mỗi email (cấu hình AGENTS.md).

**7. Client Onboarding Automation** (Skills: gog, slack; trigger webhook khi deal close). Khi deal close trên CRM → webhook trigger Agent: tạo folder Drive theo template dự án + copy tài liệu chuẩn, invite client vào Slack với welcome message cá nhân hóa, lên lịch kickoff meeting 3 ngày sau trên Google Calendar, tạo task checklist onboarding tuần đầu, thông báo nội bộ cho team qua Slack #project. Quy trình manual 3 ngày → tự động trong 8 phút.

**8. Research & Market Report** (Skills: tavily, browser-automation, write). Lệnh: "Nghiên cứu thị trường fintech Việt Nam Q1/2026, tổng hợp 5 điểm chính, tạo file Word theo template công ty" — Agent dùng Tavily tìm nguồn chất lượng cao, đọc 15–20 bài, cross-check dữ liệu, tạo Word hoàn chỉnh trong 8–12 phút thay vì 1–2 ngày nghiên cứu thủ công.

### Nhóm 3: Nội dung & marketing

Đặc biệt hiệu quả cho content creator, agency và SME.

**9. Multi-Platform Content Repurposing** (Skills: gog, write). Upload 1 bài blog/bài nói chuyện → Agent tự động tạo: 5 bài Facebook (dài, kể chuyện, engagement-focused), 3 post LinkedIn (professional, data-driven, có CTA), 10 caption Instagram (ngắn, punchy, hashtag research), 1 thread Twitter/X (7–10 tweet, hook mạnh), 1 đoạn newsletter 300 từ. Tất cả được điều chỉnh tone phù hợp từng platform dựa trên SOUL.md. Cộng đồng report: giảm 80% thời gian tạo nội dung đa kênh.

**10. AI News Aggregator & Daily Digest** (Skills: tavily, rss-reader). Agent monitor hàng trăm nguồn tin (RSS feeds + web) mỗi sáng — TechCrunch, Wired, HuggingFace blog, Arxiv daily, VnExpress Tech, CafeF... — tóm tắt 5–7 tin quan trọng nhất vào Telegram lúc 6h sáng. Có người setup cho 300+ sources, chỉ nhận 1 tin nhắn/ngày. Tip: cấu hình SOUL.md với danh sách nguồn ưu tiên và topic bạn quan tâm.

**11. Competitor Monitoring** (Skills: browser-automation, tavily). Mỗi thứ Hai 9h, Agent tự kiểm tra 3–5 đối thủ: theo dõi thay đổi pricing/landing page/tính năng mới, đọc review mới trên G2/Capterra/App Store, tóm tắt bài blog mới của đối thủ, so sánh với tháng trước. Gửi báo cáo Word vào Drive + ping vào Slack #competitive-intel. Setup một lần, tự chạy mãi mãi.

### Nhóm 4: Developer & kỹ thuật

Dành cho developer và technical lead — tiết kiệm nhiều giờ review và monitoring mỗi tuần.

**12. GitHub PR Review Assistant** (Skills: github-cli, tavily; trigger GitHub webhook → Telegram). Khi có PR mở → webhook trigger Agent: fetch diff, đọc code thay đổi, kiểm tra missing error handling/unused imports/naming convention, so sánh với coding standards trong workspace, gửi summary Telegram với actionable comments. Không thay thế human review — là pre-filter để human reviewer tập trung vào logic/architecture thay vì style issues. Một dev report: tiết kiệm 2–3 giờ review/tuần cho team 4 người.

**13. Remote Code via Telegram** (Skills: shell-executor). Case thực tế từ cộng đồng: nhắn Telegram "Update website FelixCraft AI thêm dòng Hi Every" → Agent SSH vào server, mở code, tìm đúng chỗ, sửa, deploy. Website update trong 1 phút — không cần mở laptop. Cấu hình AGENTS.md quan trọng: chỉ cho phép edit file trong thư mục /var/www/ — không bao giờ cho phép exec ngoài sandbox; luôn yêu cầu confirm trước khi deploy lên production.

**14. Server Monitoring & Auto-Alert** (Skills: shell-executor, telegram-bot). Agent check health server mỗi 5 phút: CPU > 80% liên tục 3 phút → alert Telegram ngay; RAM < 10% còn lại → cảnh báo + gợi ý process cần kill; Disk > 90% → gửi danh sách file lớn nhất có thể xóa; Service down → alert ngay + thử auto-restart. Gửi daily digest lúc 8pm: tổng quan sức khỏe hệ thống 24h qua. Setup trên VPS $5/tháng, chạy 24/7 không cần mở máy.

### Nhóm 5: E-commerce & vận hành

Cho shop online, doanh nghiệp vừa và nhỏ — giảm công việc lặp đi lặp lại trong vận hành hàng ngày.

**15. Shopify Inventory Management** (Skills: shopify-cli, gog). Mỗi sáng Agent kiểm tra tồn kho Shopify: sản phẩm sắp hết hàng → alert ngay; đọc file CSV từ nhà cung cấp, so sánh giá mới; cập nhật giá tự động theo rule (cost + 30% margin); đánh dấu out-of-stock nếu hết, unhide khi có hàng lại. Cộng đồng report: giảm 70% manual work trong order management, zero overselling case từ khi dùng Agent.

**16. Customer Support Bot 24/7** (Skills: telegram-bot hoặc zalo). Agent trực Telegram/Zalo 24/7: đọc FAQ từ file Google Docs (bạn tự cập nhật), trả lời tự động giá/chính sách đổi trả/thời gian ship/hướng dẫn dùng, hỏi thêm context nếu câu hỏi chưa rõ, case phức tạp tag @bạn vào conversation kèm tóm tắt context, ghi tất cả ticket vào Google Sheets CRM tự động. Phản hồi trong 5–30 giây bất kể 2h sáng hay ngày lễ.

**17. Automated Quoting & Contract** (Skills: gog, write). Lệnh: "Tạo báo giá cho khách [tên] gói [X]" — Agent đọc template trong Drive, điền thông tin, tính giá đúng công thức, tạo PDF chuyên nghiệp, upload vào Drive, gửi link vào Telegram của bạn. Thêm tính năng: gửi email cho khách kèm link ký điện tử. Tiết kiệm 45–60 phút/báo giá, không bao giờ quên điều khoản, luôn đúng giá.

### Nhóm 6: Ứng dụng nâng cao

**18. Điều khiển PC từ Zalo/Telegram** (Skills: shell-executor, screenshot). Nhắn Zalo từ điện thoại → Agent thực hiện trên PC → chụp màn hình → gửi lại. Ví dụ: "Mở file báo cáo tháng 3, điền tổng doanh thu vào ô B15" → Agent mở Excel, điền, chụp màn hình kết quả gửi cho bạn xác nhận. Cần cấu hình AGENTS.md cẩn thận: giới hạn thư mục và app được phép dùng.

**19. Bot tư vấn sản phẩm (Zalo OA)** (Skills: zalo, gog; Knowledge Base: Google Sheets). Phổ biến trong ngành bán hàng, bất động sản, bảo hiểm VN: Agent kết nối Zalo Official Account, trả lời tư vấn 24/7. Knowledge Base là file Google Sheets liệt kê sản phẩm, giá, ưu đãi — nhân viên update Sheets, Agent tự đọc data mới. Phân loại lead: hỏi giá (lạnh) vs hỏi chi tiết + thời gian (nóng) → lead nóng alert ngay cho sales team. Case thực tế: agency bất động sản giảm 60% thời gian phản hồi ban đầu.

**20. Tổng hợp báo cáo kinh doanh cuối ngày** (Skills: gog, browser-automation; Cron: 0 18 * * 1-6). 6pm mỗi ngày làm việc, Agent tự động: đọc Google Sheets doanh thu thực tế, so sánh với target, tính % hoàn thành, lấy số liệu đơn hàng từ phần mềm quản lý, tóm tắt 3 điểm nổi bật (tốt/cần chú ý/hành động ngay), gửi báo cáo vào Telegram nhóm ban lãnh đạo. Được dùng nhiều trong chuỗi cửa hàng, agency, SME Việt Nam.

**21. Research học thuật & tổng hợp tài liệu** (Skills: tavily, browser-automation, write). Dành cho sinh viên, researcher, giảng viên. Lệnh: "Tìm 10 paper về Retrieval Augmented Generation từ 2023–2025, tóm tắt methodology của mỗi paper, so sánh cách tiếp cận" — Agent dùng Tavily tìm Arxiv, Semantic Scholar, Google Scholar, tạo bảng so sánh Word hoàn chỉnh với citation đúng format APA/IEEE. Case từ cộng đồng Viblo: researcher dùng AutoResearchClaw skill từ idea → literature review → code thử nghiệm → paper draft. Lưu ý: luôn kiểm tra lại citation — AI có thể hallucinate source.

### Multi-Agent pipeline: Content Creator

Một trong những pattern phổ biến nhất cộng đồng chia sẻ — pipeline 3 Agent phối hợp:

**Agent Scout** (monitor RSS/web tìm topic hot) → **Agent Writer** (nhận brief viết draft) → **Agent Editor** (review format & polish).

Cách agents phối hợp qua shared memory:

```text
workspace/shared/briefs/2026-03-23.md
Topic: 'Top 5 AI tools cho SME Việt Nam Q1/2026'
Sources: [link1, link2, link3]
Keywords: AI, SME, Việt Nam, productivity

# Agent Writer đọc brief, viết draft:
workspace/shared/drafts/2026-03-23.md

# Agent Editor đọc draft, polish:
workspace/shared/final/2026-03-23.md
```

### Bắt đầu từ đâu?

> 💡 Bắt đầu với Use Case 1 (Morning Briefing) — đây là use case có tỉ lệ thành công cao nhất và không có rủi ro. Sau khi quen với cách Agent hoạt động, mở rộng sang business automation.
>
> Tip từ cộng đồng: trước khi để Agent tự gửi email/post, hãy chạy ở chế độ "draft mode" ít nhất 1 tuần. Chỉ confirm sau khi bạn tin tưởng 95%+ output của Agent.

### Bài tiếp theo trong series

- **Bài 5:** Multi-Agent, bảo mật và chạy OpenClaw 24/7 trên VPS
- Bài 6: OpenClaw hay Manus AI? Lộ trình 30 ngày làm chủ
- Bài 1 · Bài 2 · Bài 3

### Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn cộng đồng và [OpenClaw](https://openclaw.ai/) — có biên tập lại cấu trúc theo phong cách LearnWithHuy. Các số liệu "cộng đồng report" là kinh nghiệm chia sẻ từ người dùng, mang tính tham khảo.

---

## 06. OpenClaw hay Manus AI? Chọn công cụ agent và lộ trình 30 ngày làm chủ

Bài cuối series OpenClaw (bài 1 → bài 5): thị trường AI Agent 2026 đang rất sôi động. Hiểu rõ sự khác biệt giúp bạn chọn đúng công cụ cho từng nhu cầu — OpenClaw không phải lúc nào cũng là lựa chọn tốt nhất.

### So sánh OpenClaw và Manus AI

| Tiêu chí | OpenClaw | Manus AI |
| --- | --- | --- |
| **Loại** | Mã nguồn mở (Open Source) | Closed source (Meta) |
| **Chạy ở đâu** | Máy tính / VPS của bạn | Cloud (server của Meta) |
| **Chi phí** | Miễn phí + phí API key | $39 – $199/tháng |
| **Bảo mật dữ liệu** | Dữ liệu lưu cục bộ, riêng tư 100% | Dữ liệu trên server bên thứ 3 |
| **Độ tùy biến** | Tùy biến hoàn toàn (SOUL.md, AGENTS.md) | Giới hạn theo gói dịch vụ |
| **Skills / Plugin** | 47,000+ trên ClawHub | Tích hợp sẵn, ít hơn |
| **Cài đặt** | Cần kỹ thuật cơ bản | Không cần cài đặt |
| **Multi-Agent** | Có, tùy biến hoàn toàn | Hỗ trợ hạn chế |
| **Phù hợp với** | Dev, IT, doanh nghiệp cần bảo mật cao | Người dùng cá nhân, doanh nghiệp nhỏ |
| **GitHub Stars** | 300,000+ (kỷ lục lịch sử) | Không công khai |

#### Khi nào chọn OpenClaw?

- Cần bảo mật dữ liệu cao (dữ liệu tài chính, pháp lý, y tế)
- Muốn tùy biến hoàn toàn — từ LLM đến từng hành vi của Agent
- Chi phí dài hạn: không muốn trả subscription hàng tháng
- Có IT support: cần người cấu hình và maintain hệ thống
- Muốn tích hợp với hệ thống nội bộ phức tạp qua API/webhook

#### Khi nào chọn Manus AI?

- Cần triển khai ngay, không có thời gian/người cấu hình kỹ thuật
- Số lượng task không nhiều, chi phí subscription chấp nhận được
- Muốn trải nghiệm AI agent "plug and play" ngay lập tức
- Team không có ai có kỹ thuật để vận hành OpenClaw

**Kết hợp được không? Được!** Nhiều team dùng: OpenClaw cho dữ liệu nội bộ (HR, tài chính) + Manus cho research và tác vụ bên ngoài. Không phải chọn một.

Ngoài ra, Kimi Claw (cloud version của OpenClaw do Moonshot AI vận hành) là lựa chọn trung gian: giao diện OpenClaw nhưng không cần tự host. Phù hợp nếu muốn trải nghiệm trước khi self-host.

### Lộ trình 30 ngày làm chủ OpenClaw

Lộ trình này được thiết kế cho người không chuyên kỹ thuật, từng bước từ cài đặt đến vận hành thực tế. Mỗi tuần có chủ đề rõ ràng với nhiệm vụ hàng ngày cụ thể.

**Tổng quan:** TUẦN 1 — CÀI ĐẶT (Gateway + LLM) · TUẦN 2 — KHÁM PHÁ (Tools & Skills) · TUẦN 3 — TỰ ĐỘNG HÓA (Quy trình thực tế) · TUẦN 4 — TỐI ƯU (Multi-Agent + SOUL.md)

#### Tuần 1: Cài đặt & làm quen

Mục tiêu: thiết lập môi trường và tạo ra tương tác đầu tiên với Agent.

| Ngày | Nhiệm vụ trọng tâm | Thời lượng | Công cụ |
| --- | --- | --- | --- |
| Ngày 1 | Cài đặt Node.js + OpenClaw qua One-Liner. Chạy openclaw onboard | 45 phút | Terminal/Shell |
| Ngày 2 | Kết nối Telegram: tạo bot qua @BotFather và kiểm tra phản hồi | 30 phút | Telegram API |
| Ngày 3 | Thiết lập tâm hồn (SOUL.md): định nghĩa tên, ngôn ngữ, phong cách | 30 phút | Markdown Editor |
| Ngày 4 | Thử nghiệm 5 lệnh cơ bản: tìm kiếm web, đọc file, tóm tắt URL | 20 phút | Core Skills |
| Ngày 5 | Cài đặt Skill gog: kết nối và để Agent đọc email đầu tiên | 40 phút | Google Workspace |
| Cuối tuần | Review: đánh giá điều gì hoạt động tốt và cần điều chỉnh | 20 phút | Tự đánh giá |

#### Tuần 2: Khám phá Tools & Skills

Mục tiêu: mở rộng khả năng của Agent thông qua các công cụ lưu trữ và tự động hóa web.

| Ngày | Nhiệm vụ trọng tâm | Thời lượng | Công cụ/Skill |
| --- | --- | --- | --- |
| Ngày 8 | Cài Skill browser-automation: điều khiển Chrome qua chat | 30 phút | Playwright/Puppeteer |
| Ngày 9 | Cài Skill obsidian hoặc notion: tự động hóa ghi chép | 25 phút | Note-taking API |
| Ngày 10 | Viết file AGENTS.md đầu tiên: thiết lập workflow xử lý email sáng | 35 phút | Logic Workflow |
| Ngày 11 | Chạy thử nghiệm workflow email, thực hiện debug và hoàn thiện | 30 phút | Testing |
| Ngày 12 | Chọn và cài đặt Skill chuyên ngành từ ClawHub | 30 phút | Custom Skills |
| Cuối tuần | Lưu trữ: tạo thư viện các câu lệnh (prompts) hiệu quả nhất | 15 phút | Knowledge Base |

#### Tuần 3: Tự động hóa thực tế

Mục tiêu: đưa Agent vào vận hành thực tế và tối ưu hóa hiệu suất công việc.

| Ngày | Nhiệm vụ trọng tâm | Thời lượng | Công cụ/Skill |
| --- | --- | --- | --- |
| Ngày 15 | Thiết lập HEARTBEAT.md: tự động báo cáo email lúc 8h sáng | 30 phút | Cron/Schedule |
| Ngày 16 | Cấu hình Cron Job đầu tiên và kiểm tra tính ổn định | 25 phút | System Task |
| Ngày 17 | Chuyển đổi một quy trình thủ công (xem 21 use case) sang tự động hóa | 60 phút | Process Mapping |
| Ngày 18 | Triển khai lên VPS hoặc dùng --install-daemon để chạy 24/7 | 45 phút | Deployment |
| Ngày 19 | Cài Skill chuyên ngành thứ 2: kết nối công cụ làm việc của team | 30 phút | Collaboration |
| Cuối tuần | Tổng kết: tính toán thời gian tiết kiệm và tối ưu quy trình | 20 phút | Analytics |

#### Tuần 4: Tối ưu & mở rộng

Mục tiêu: hoàn thiện cá tính Agent, mở rộng quy mô và đánh giá hiệu quả thực tế.

| Ngày | Nhiệm vụ trọng tâm | Thời lượng | Tiêu chí hoàn thành |
| --- | --- | --- | --- |
| Ngày 22 | Tinh chỉnh SOUL.md: cập nhật phong cách dựa trên 3 tuần trải nghiệm | 20 phút | Agent phản hồi tự nhiên hơn |
| Ngày 23 | Viết 2–3 workflow mới vào AGENTS.md cho các quy trình lặp lại | 40 phút | Tăng số lượng tác vụ tự động |
| Ngày 24 | Thử nghiệm Multi-agent: tạo Agent thứ 2 cho mục đích chuyên biệt | 45 phút | Phân tách trách nhiệm công việc |
| Ngày 25 | Bảo mật hệ thống: kiểm tra cấu hình Canvas Host và quyền truy cập | 20 phút | Hệ thống an toàn, bảo mật |
| Ngày 28 | Kết nối: chia sẻ kinh nghiệm, workflow với đồng nghiệp hoặc cộng đồng | 30 phút | Lan tỏa giá trị công cụ |
| Ngày 30 | Tổng kết 30 ngày: xác định 3 thay đổi lớn và lập kế hoạch tháng tới | 20 phút | Có lộ trình nâng cấp dài hạn |

> 💡 Lộ trình này linh hoạt — không cần làm đúng thứ tự. Nếu ngày 3 gặp khó khăn, bỏ qua, tiếp tục ngày 4 và quay lại sau.

### Lời kết

OpenClaw không phải phép màu. Đó là **công cụ khuếch đại**.

Cũng như Claude AI hay bất kỳ công cụ mạnh nào khác — OpenClaw khuếch đại những gì bạn đã giỏi. Người giỏi quy trình dùng OpenClaw sẽ xây được hệ thống tự động hóa xuất sắc. Người chưa có quy trình rõ ràng dùng OpenClaw sẽ tự động hóa... sự hỗn loạn.

Điều đáng chú ý ở những người dùng OpenClaw thành công nhất không phải là họ biết kỹ thuật nhiều hơn. Mà là họ biết RÕ điều mình cần — và kiên nhẫn từng bước. Cài đặt xong, test thật kỹ một workflow nhỏ. Thành công rồi, mở rộng ra. Cứ thế.

Bước đầu tiên ngay hôm nay: cài OpenClaw, kết nối Telegram, viết SOUL.md đơn giản nhất có thể. Đừng nghĩ nhiều — hãy bắt đầu.

### Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn cộng đồng và [OpenClaw](https://openclaw.ai/) — có biên tập lại cấu trúc theo phong cách LearnWithHuy. Thông tin sản phẩm, giá và số liệu theo tài liệu gốc, nên kiểm tra lại trên trang chính thức trước khi quyết định.

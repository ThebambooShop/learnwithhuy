---
title: "9Router và Hermes Agent: giới thiệu và cài đặt từ con số 0"
description: "Cẩm nang gộp 2 bài về 9Router và Hermes Agent: hai công cụ AI mà dev nào cũng nên biết, kèm hướng dẫn cài đặt Hermes Agent chi tiết cho Windows, macOS và Linux."
topic: "ai-agent-va-tu-dong-hoa"
date: "2026-11-24"
cover: "/images/covers/posts/9router-va-hermes-agent.jpg"
featured: false
views: 180
faq:
  - q: "Cẩm nang này gồm những gì?"
    a: "Toàn bộ 2 bài trước đây đăng riêng giờ gộp trong một trang, chia thành 2 phần đánh số — đọc tuần tự hoặc nhảy tới phần cần đều được."
  - q: "Nên đọc theo thứ tự không?"
    a: "Các phần được xếp theo thứ tự học gợi ý. Đọc lộn vẫn hiểu vì mỗi phần đứng độc lập, nhưng lần đầu học thì nên theo thứ tự. Tổng thời gian đọc khoảng 20 phút."
---

## Bạn sẽ học được gì

- **Phần 01. 9Router và Hermes Agent: 2 công cụ AI mà dev nào cũng nên biết**
- **Phần 02. Cài đặt Hermes Agent từ con số 0: hướng dẫn chi tiết cho Windows, macOS và Linux**

> **Ai nên đọc:** Người mới tìm hiểu 9Router và Hermes Agent, muốn cài đặt nhanh theo từng hệ điều hành.
> **Điều kiện đầu vào:** Không cần nền tảng đặc biệt.
> **Tổng thời gian đọc:** ≈20 phút — có thể đọc dần theo phần, thời lượng từng phần ghi ngay trên tiêu đề.

01. 9Router và Hermes Agent: 2 công cụ AI mà dev nào cũng nên biết — ≈8 phút

Khi ứng dụng AI chuyển từ "ô hội thoại" sang hệ thống xử lý tác vụ phức tạp, bạn sẽ gặp hai thách thức ở hai tầng khác nhau:

- **Tầng hạ tầng mô hình:** gọi trực tiếp API của từng nhà cung cấp khiến mã nguồn bị khóa chặt vào cấu trúc của họ. Dịch vụ nào đó gặp sự cố, hết rate limit hoặc tăng giá là phải sửa code ở nhiều nơi.
- **Tầng thực thi tác vụ:** để hoàn thành công việc phức tạp (lập trình, phân tích dữ liệu, quản trị hệ thống), mô hình không thể hoạt động đơn độc — cần suy luận đa bước, tự chọn công cụ, ghi nhớ ngữ cảnh qua nhiều phiên.

Bài viết này giới thiệu hai công cụ mã nguồn mở giải quyết đúng hai tầng đó. **9Router** lo tầng cổng API, **Hermes Agent** lo tầng tác vụ tự chủ. Kết hợp lại, bạn được một hệ thống AI vừa suy luận mạnh, vừa linh hoạt hạ tầng — không khóa chặt vào nhà cung cấp nào.

### 9Router — cổng định tuyến API thông minh

**9Router là gì?** Một API Gateway mã nguồn mở chuẩn hóa và chuyển tiếp các yêu cầu gọi mô hình AI. Nó cung cấp giao diện tương thích chuẩn API OpenAI tại `http://localhost:20128/v1` — nghĩa là bất kỳ công cụ nào (Claude Code, Cursor, Codex, Cline hay Agent khác) đều có thể trỏ đến mà không cần sửa mã nguồn tích hợp.

#### Tính năng cốt lõi

- **RTK Token Saver** — nén dữ liệu thô từ công cụ (git diff, grep, ls... vốn chiếm 30–50% dung lượng prompt nhưng chứa nhiều dòng trắng): tự động phân tích 1KB đầu tiên của kết quả và nén lại, tiết kiệm 20–40% input token mà vẫn giữ ngữ cảnh.
- **Chế độ Caveman / Ponytail** — tự động ép mô hình trả lời ngắn gọn, trực diện, bỏ câu chuyển tiếp rườm rà: tiết kiệm tới 65% output token.
- **3-Tier Fallback** — ghép nhóm mô hình theo thứ tự ưu tiên: tầng 1 mô hình cao cấp (Subscription), hết hạn mức thì chuyển tầng 2 giá rẻ, sự cố thì chuyển tầng 3 miễn phí.
- **Multi-account Round-robin** — tự động luân chuyển giữa nhiều tài khoản cùng nhà cung cấp khi một tài khoản chạm giới hạn.
- **Format Translation** — dịch định dạng API hai chiều giữa OpenAI, Claude, Gemini, Cursor, Kiro, Vertex AI và Ollama.

#### Lưu ý quan trọng về chi phí

Một điểm cần phân biệt rõ: **9Router bản thân là phần mềm miễn phí, mã nguồn mở 100% (giấy phép MIT)** — dữ liệu cấu hình và nhật ký lưu cục bộ trong SQLite (`~/.9router/db/data.sqlite`), tự triển khai không tốn phí bản quyền. Chi phí (nếu có) nằm ở **mô hình phía sau**:

- **Local LLM** qua Ollama/vLLM: miễn phí hoàn toàn.
- **Gói API miễn phí** (Kiro AI, OpenCode Free...): có hạn mức trải nghiệm.
- **Dịch vụ thương mại** (OpenAI API, Anthropic API, Claude Code Pro...): tính phí theo token hoặc hạn mức đăng ký.

Nó cũng có Web Dashboard trực quan tại `http://localhost:20128` để quản lý nhà cung cấp và thiết lập quy tắc định tuyến thay vì chỉnh file cấu hình tay.

### Hermes Agent — Agent tự chủ đa năng

**Hermes Agent là gì?** Một khung làm việc Agent tự chủ mã nguồn mở do Nous Research phát triển. Khác với ứng dụng trò chuyện theo từng phiên, Hermes Agent chạy liên tục và độc lập — trên máy cục bộ, VPS chi phí thấp, GPU cluster hoặc môi trường serverless (Modal, Daytona).

#### Vòng lặp tự học khép kín

Điểm đặc sắc nhất là **Closed Learning Loop** theo chu trình: *Quan sát → Thực thi → Phản ánh → Kết tinh → Tái sử dụng*. Sau mỗi tác vụ phức tạp, Agent tự phân tích lại quá trình làm việc và cô đọng thành kỹ năng tái sử dụng. Kỹ năng do Agent tự học được gắn nhãn `learned` trên giao diện danh mục, quản lý dưới dạng file Markdown theo chuẩn mở agentskills.io.

#### Kiến trúc bộ nhớ 3 tầng

- **Working Memory** — bộ nhớ ngắn hạn: toàn bộ ngữ cảnh của phiên hiện tại.
- **Persistent Semantic Memory** — bộ nhớ ngữ nghĩa dài hạn: thói quen, hồ sơ người dùng, chuỗi công cụ đã dùng qua nhiều phiên.
- **Cross-Session Recall** — truy xuất lịch sử qua các phiên bằng tìm kiếm toàn văn SQLite FTS5 kết hợp tóm tắt AI, giảm hiện tượng trôi ngữ cảnh.

#### Bộ công cụ và khả năng

Hơn 40 công cụ tích hợp sẵn: terminal đa môi trường (Local, Docker, SSH, Singularity, Modal, Daytona), thao tác tệp và mã nguồn, điều khiển trình duyệt, đa phương tiện (TTS, tạo ảnh) và mở rộng qua MCP. Đáng chú ý là **Subagents** — khi bạn giao nhiều việc cùng lúc, Agent chính tự tạo các tác vụ con chạy song song rồi tổng hợp kết quả, không tiêu tốn ngữ cảnh của phiên chính.

Tương tác đa kênh: Terminal TUI chuyên nghiệp, cùng Messaging Gateway tích hợp Telegram, Discord, Slack, WhatsApp, Signal và Email — bạn nhắn tin thoại cho Agent đang chạy trên server từ điện thoại. Kèm **Cron Scheduler** lập lịch bằng ngôn ngữ tự nhiên ("mỗi sáng gửi báo cáo vào Telegram") và backend serverless đóng băng khi rảnh để chi phí duy trì tiệm cận 0.

### Hai công cụ kết hợp như thế nào?

Hermes Agent không bị khóa vào nhà cung cấp nào: nó phát ra yêu cầu chuẩn API OpenAI. Trỏ endpoint về 9Router là bạn được cả hai lợi thế. Luồng xử lý gồm 6 bước:

1. **Khởi tạo:** bạn nhập mục tiêu qua TUI hoặc app nhắn tin.
2. **Lập kế hoạch:** Hermes Agent phân tích ngữ cảnh, đọc bộ nhớ dài hạn, đóng gói yêu cầu chuẩn OpenAI gửi đến `http://localhost:20128/v1`.
3. **Định tuyến:** 9Router nén token (RTK), kiểm tra hạn mức, chuyển tiếp đến nhà cung cấp tối ưu; sự cố thì kích hoạt fallback 3 tầng.
4. **Trả kết quả:** nhà cung cấp xử lý và phản hồi về 9Router.
5. **Chuẩn hóa:** 9Router đóng gói phản hồi chuẩn OpenAI trả lại Agent.
6. **Thực thi:** Hermes Agent chạy công cụ thật trên hệ thống, lưu bộ nhớ mới, trả đáp án cho bạn.

### So sánh vai trò

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

### Kịch bản thực tế: "Phân tích dung lượng ổ đĩa"

Trong demo của tài liệu gốc, người dùng gõ yêu cầu phân tích dung lượng ổ đĩa vào Hermes Agent:

1. Agent đóng gói yêu cầu, gửi qua 9Router.
2. 9Router áp RTK Token Saver (giảm 20–40% token prompt) rồi định tuyến đến mô hình tối ưu.
3. Mô hình phản hồi danh sách lệnh cần chạy (`df`, `du`); Agent tự chạy trên hệ thống thật.
4. Agent tổng hợp số liệu thành báo cáo: tổng dung lượng, mức sử dụng từng phân vùng, các thư mục chiếm nhiều nhất, và gợi ý 3 khu vực nên dọn dẹp.

Toàn bộ quá trình suy luận phía sau được 9Router định tuyến và nén token âm thầm — người dùng chỉ thấy một báo cáo sạch.

### Nên bắt đầu từ đâu?

- Nếu bạn **đã dùng Cursor/Claude Code/Cline** và muốn tiết kiệm token + tránh đứt gãy khi nhà cung cấp sự cố: triển khai 9Router trước, trỏ công cụ hiện tại về `localhost:20128/v1` — không đổi thói quen làm việc.
- Nếu bạn cần **Agent chạy liên tục, tự học, tự động hóa**: dùng Hermes Agent, và cấu hình nó dùng 9Router làm điểm kết nối duy nhất để có cả hai lợi thế.

Vì cả hai đều là mã nguồn mở, cách an toàn nhất để đánh giá là đọc mã nguồn và thử trên môi trường của riêng bạn — đúng tinh thần "học thật, chia sẻ thật" của blog này.

### Nguồn tham khảo

Bài viết dựa trên tài liệu hướng dẫn "9Router và Hermes Agent" của AI Guru x TiniX (Mentor Đỗ Hoàng Hà). Nguồn chính thức của hai công cụ:

- [9Router trên GitHub](https://github.com/decolua/9router)
- [Hermes Agent trên GitHub](https://github.com/nousresearch/hermes-agent)
- [Hermes Agent Documentation](https://hermes-agent.nousresearch.com/docs/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

---

02. Cài đặt Hermes Agent từ con số 0: hướng dẫn chi tiết cho Windows, macOS và Linux — ≈12 phút

Hermes Agent là AI agent mã nguồn mở của Nous Research — không chỉ trả lời câu hỏi mà còn chủ động *hành động*: đọc ghi file, chạy lệnh terminal, điều khiển trình duyệt, gọi API. Bài này là hướng dẫn thực hành: từ con số 0 đến hội thoại AI đầu tiên trong khoảng 15 phút, trên cả ba hệ điều hành.

### Hai bản phân phối: CLI và Desktop

| Tiêu chí | Hermes CLI / TUI | Hermes Desktop |
| --- | --- | --- |
| **Giao diện** | Terminal, TUI đầy đủ | Cửa sổ đồ họa Electron |
| **Nền tảng** | Linux, macOS, Windows | macOS (Apple Silicon), Windows, Linux (qua CLI) |
| **Điểm mạnh** | Nhẹ, chạy remote qua SSH/VPS | Xem file, preview, trực quan |
| **Cài đặt** | One-liner curl / PowerShell | Tải bộ cài trực tiếp |

Chỉ muốn dùng terminal thì cài bản CLI là đủ. Thích giao diện cửa sổ thì đọc thêm phần Desktop ở cuối bài.

### Cài bản CLI: chuẩn bị gì trước

Installer được thiết kế tự động hóa tối đa, nhưng hệ thống cần có sẵn một số công cụ nền tảng:

- **Git** — clone mã nguồn Hermes và hỗ trợ cập nhật bằng `hermes update`
- **curl** — tải script cài đặt và các tệp nén môi trường
- **xz-utils** — giải nén `.tar.xz` khi cài Node.js trên Linux và WSL2
- **build-essential / g++** — biên dịch module native khi cài Desktop trên Linux
- **PowerShell 5.1+** — thực thi `install.ps1` trên Windows

> ✅ **Installer tự lo phần còn lại:** sau khi các công cụ trên sẵn sàng, Hermes sẽ tự phát hiện và cài uv, Python 3.11, Node.js v22, ripgrep và ffmpeg vào thư mục cách ly `~/.hermes/` — không ảnh hưởng hệ thống, không cần cài thủ công.

Kiểm tra nhanh:

```bash
git --version
curl --version
```

Chưa có thì cài theo hệ điều hành:

```bash
sudo apt update && sudo apt install -y git curl xz-utils build-essential

# Fedora / RHEL / CentOS
sudo dnf install -y git curl xz gcc-c++ make

# Arch Linux / Manjaro
sudo pacman -S --noconfirm git curl xz base-devel
```

```bash
# macOS — nhanh nhất là Xcode Command Line Tools (đã gồm Git, curl, make)
xcode-select --install
```

```powershell
# Windows native (PowerShell với quyền Administrator)
winget install Git.Git
# Windows qua WSL2 (khuyên dùng cho dev Windows)
wsl --install
```

### Cài đặt một dòng lệnh

**Linux, macOS và WSL2:**

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Trong quá trình cài, installer sẽ: phát hiện hệ điều hành và kiến trúc → cài uv (trình quản lý Python viết bằng Rust) → xác nhận Python 3.11, Git, Node.js → cài ripgrep và ffmpeg nếu chưa có → clone mã nguồn về `~/.hermes/hermes-agent`.

Tải lại cấu hình shell rồi kiểm tra:

```bash
source ~/.bashrc   # hoặc source ~/.zshrc trên macOS
hermes --version
```

**Windows (PowerShell, không dùng WSL2):**

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

Installer sẽ tự cài thêm bản Git Bash nhỏ gọn (MinGit, khoảng 45MB) vào `%LOCALAPPDATA%\hermes\git` nếu máy chưa có Git.

> ⚠️ **Cảnh báo antivirus trên Windows:** một số phần mềm diệt virus có thể gắn cờ false positive với file `uv.exe`. Đây là binary hợp lệ của Astral viết bằng Rust — trước khi thêm ngoại lệ, hãy xác minh nguồn gốc file (xem mục lỗi thường gặp). Máy công ty thì liên hệ quản trị viên hệ thống theo chính sách bảo mật nội bộ.

### Setup Wizard — cấu hình lần đầu

Ngay sau khi cài xong, wizard tự mở và hỏi bạn muốn thiết lập theo cách nào:

| Lựa chọn | Ý nghĩa |
| --- | --- |
| **Quick Setup (Nous Portal)** | Đăng nhập OAuth miễn phí, không cần API key — phù hợp người mới |
| **Full Setup** | Tự cấu hình từng provider, tool và option — dùng khi muốn kiểm soát toàn bộ, bao gồm cả việc dùng 9Router |
| **Blank Slate** | Tắt tất cả trừ mức tối thiểu, tự opt-in từng tính năng |

Khuyến nghị: **chọn Full Setup** — cho phép kiểm soát hoàn toàn và không khó hơn Quick Setup là mấy, vì wizard dẫn dắt từng bước.

#### Bảy bước trong wizard

1. **Chọn kiểu thiết lập** — Full Setup.
2. **Chọn provider** — Hermes hỗ trợ rất nhiều: Nous Portal, OpenAI, Anthropic, OpenRouter, AWS Bedrock, Azure, Ollama, LM Studio... Khi dùng 9Router, chọn **Custom endpoint** ở cuối danh sách.
3. **Nhập Base URL và API Key** — với 9Router: `http://localhost:20128/v1` và key do 9Router cấp.

> ℹ️ Cảnh báo `could not verify this endpoint supports /v1/models` là **bình thường** với custom endpoint — một số endpoint không expose route đó, Hermes vẫn kết nối và hoạt động đúng; chỉ là bạn cần nhập tên model thủ công ở bước sau.

4. **Chọn API compatibility mode** — chọn **Chat Completions** vì 9Router dùng chuẩn `/chat/completions` của OpenAI. Tên model điền **tên combo** đã tạo trong giao diện 9Router (ví dụ `my-first-combo`) — mỗi combo gom nhiều model và rule định tuyến lại, nhưng về phía Hermes nó chỉ là một tên model để chọn.
5. **Chọn terminal backend** — đa số chọn **Local** (chạy trực tiếp trên máy hiện tại). Còn có Docker, SSH, Modal, Daytona cho trường hợp remote/cloud.
6. **Bật/tắt Tool** — hơn 20 nhóm tool: Web Search, Browser Automation, Terminal, File Operations, Vision, Image Generation, TTS, Skills, Memory, Cron Jobs... Mặc định bật tất cả, dùng phím SPACE để toggle, ENTER xác nhận.
7. **Image Generation và Gateway** — nếu chưa cần tạo ảnh thì Skip. Gateway nhắn tin (Telegram, Discord, Slack, WhatsApp) cho phép chat từ điện thoại khi Agent chạy trên máy chủ — chỉ dùng CLI thì bỏ qua.

Hoàn tất, cấu hình được lưu tại: `~/.hermes/config.yaml` (config), `~/.hermes/.env` (API keys), `~/.hermes/` (cron, sessions, logs).

#### Đổi provider và model sau khi cài

```bash
hermes model                                     # menu chọn model tương tác
hermes config set provider.base_url "http://localhost:20128/v1"
hermes config set model "ten-combo-moi"
hermes config get                                # xem cấu hình hiện tại
```

### Cài bản Desktop

Hermes Desktop hỗ trợ chính thức trên **macOS Apple Silicon** và **Windows** — macOS chip Intel (x86) chưa được hỗ trợ. Trên macOS và Windows, bộ cài đã gồm sẵn phần lớn runtime, không cần cài thêm Python hay Node.js.

1. Tải bộ cài từ trang chính thức `https://hermes-agent.nousresearch.com/` (.dmg cho macOS, .exe cho Windows). Linux dùng lại lệnh CLI ở trên.
2. Mở file cài → kéo biểu tượng vào Applications (macOS) → nhấn **Install Hermes** → đợi 11 bước cài tự chạy xong → **Launch Hermes**.
3. Ở màn hình chọn provider lần đầu, có thể nhấn *"I'll choose a provider later"* để cấu hình sau qua Settings.
4. **Thêm 9Router:** Settings → Providers → **Custom Endpoints** → chọn "Local / custom endpoint" → điền `http://localhost:20128/v1` và API key → **Connect**.
5. **Chọn combo làm model:** Settings → Model → Provider/Server chọn `Local (localhost:20128)` → chọn combo từ dropdown → **Apply**. Từ giờ mọi hội thoại được định tuyến qua 9Router theo đúng combo đã chọn.

Gỡ cài đặt:

```bash
hermes uninstall            # gỡ toàn bộ CLI (giữ config và data)
hermes uninstall --full     # gỡ sạch config, data, session
hermes uninstall --gui      # chỉ gỡ Desktop GUI, giữ nguyên CLI agent
```

### Sáu khái niệm cốt lõi

| Khái niệm | Nghĩa | Vai trò |
| --- | --- | --- |
| **CLI** | Giao diện dòng lệnh | Hai mục đích: lệnh quản trị ngoài terminal (setup, update) và lệnh slash trong hội thoại (`/model`, `/skills`) |
| **Session** | Phiên làm việc | Mỗi lượt tương tác là một session; lịch sử lưu vết trong SQLite, tự nén khi tiến sát giới hạn ngữ cảnh |
| **Tools** | Công cụ | Hàm chức năng cụ thể: đọc file, chạy terminal, tìm kiếm web, điều khiển trình duyệt |
| **Skills** | Kỹ năng | Tài liệu hướng dẫn dạng Markdown dạy agent cách phối hợp nhiều công cụ cho một loại tác vụ |
| **Memory** | Bộ nhớ | Lưu bền vững thông tin về người dùng và môi trường, tự nạp lại ở mọi session sau |
| **MCP** | Model Context Protocol | Chuẩn giao tiếp mở để kết nối MCP Server bên ngoài: SQL, GitHub API, quản lý dự án |

### Nâng cao: Skills, Tools và MCP

#### Quản lý Skills

```bash
hermes skills list            # xem danh sách skill đã cài
hermes skills search QUERY    # tìm skill trong kho
hermes skills install ID      # cài skill theo ID hoặc URL
hermes skills inspect ID      # xem trước nội dung skill
hermes skills opt-out         # tắt tự động seed bundled skills
```

Trong hội thoại: `/excalidraw` gọi một skill cụ thể; ghép nhiều skill trong cùng lệnh `/github-pr-workflow /test-driven-development fix issue #123`; `/learn` tự đóng gói workflow hiện tại thành skill mới.

#### Tra cứu bộ Tools tích hợp

| Nhóm Tool | Công cụ tiêu biểu |
| --- | --- |
| Web & Search | `web_search`, `web_extract`, `x_search` |
| Terminal & Files | `terminal`, `process`, `read_file`, `patch` |
| Browser | `browser_navigate`, `browser_snapshot`, `browser_vision` |
| Media | `vision_analyze`, `image_generate`, `text_to_speech` |
| Orchestration | `todo`, `clarify`, `execute_code`, `delegate_task` |
| Memory | `memory`, `session_search` |
| Automation | `cronjob` |

```bash
hermes tools                          # giao diện bật/tắt Tool tương tác
hermes chat --toolsets "web,terminal" # chỉ định nhóm Tool khi khởi chạy
```

#### Tự viết Custom Tool

Tiêu chí chọn: dùng **Skill** cho quy trình kết hợp lệnh CLI và hướng dẫn text; tạo **Tool** khi cần gọi API trực tiếp, xử lý dữ liệu nhị phân hoặc tích hợp mã nguồn Python riêng.

```python
# tools/custom_tool.py
import json
from tools.registry import registry

def custom_handler(args, **kwargs):
    try:
        res = {"result": "success", "data": args.get("input_val")}
        return json.dumps(res)  # bắt buộc trả về JSON string
    except Exception as e:
        return json.dumps({"error": str(e)})

registry.register(
    name="custom_tool",
    toolset="custom",
    schema={
        "name": "custom_tool",
        "description": "Mô tả chức năng của custom tool",
        "parameters": {
            "type": "object",
            "properties": {"input_val": {"type": "string"}},
            "required": ["input_val"],
        },
    },
)
```

Ngoài ra có thể đặt custom tool độc lập dạng Plugin tại `~/.hermes/plugins/` mà không cần chỉnh sửa mã gốc.

#### Tích hợp MCP

```bash
hermes mcp              # duyệt và cài MCP Server tương tác
hermes mcp catalog      # xem danh sách catalog dạng text
hermes mcp install github
```

Hoặc cấu hình thủ công trong `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "/path/to/projects"
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your_github_token"
```

### Hội thoại đầu tiên — thử thật

Demo tác vụ 1: *"Tìm kiếm thông tin về thần Hermes trên Wikipedia, tạo thư mục docs tại ~/, ghi nội dung tìm được vào một file trong thư mục này."* Hermes tự phân tích mục tiêu, lập kế hoạch và tự điều phối 4 công cụ liên tiếp: `browser_navigate` mở trang Wikipedia → `terminal` tạo thư mục và file rỗng → `browser_console` trích xuất nội dung trang → `write_file` ghi vào `~/docs/hermes_wikipedia.txt`.

Demo tác vụ 2: *"Hãy xoá file vừa tạo rồi sau đó xoá thư mục docs."* Hermes chạy 2 lệnh terminal liên tiếp để dọn dẹp.

> ⚠️ Nếu tool browser không hoạt động, kiểm tra Node.js đã cài chưa bằng `node --version` — browser tools cần Node.js để chạy Playwright. Thiếu thì cài từ nodejs.org rồi chạy lại `hermes setup`.

Sau khi xác nhận hoạt động, thử thêm: `/skills` xem danh sách skill, `/model` đổi model nhanh trong chat, dán một đoạn code bất kỳ để yêu cầu giải thích, chạy `hermes doctor` khi gặp vấn đề.

### 8 lỗi thường gặp và cách xử lý

| Biểu hiện | Nguyên nhân thường gặp | Cách xử lý |
| --- | --- | --- |
| Cài xong nhưng lệnh `hermes` chưa chạy | Shell chưa nạp lại PATH | `source ~/.bashrc` (hoặc `.zshrc`); kiểm tra `echo $PATH \| tr ':' '\n' \| grep hermes`; đóng và mở lại terminal |
| Installer báo lỗi Python hoặc uv | Mạng chập chờn hoặc môi trường chặn tải | Chạy lại installer một lần nữa — nó tự cài uv, Python, Node.js, ripgrep, ffmpeg |
| Không cài được Desktop trên macOS 12+ | Máy chạy chip Intel (x86) | Desktop chỉ hỗ trợ Apple Silicon; kiểm tra ở About This Mac, chuyển sang dùng CLI |
| `uv.exe` bị antivirus xóa trên Windows | False positive của Defender/Bitdefender | Xác minh bằng GitHub attestation; nếu whitelist thì thêm cả thư mục Hermes (nâng cấp uv thay hash, whitelist theo file sẽ báo tiếp) |
| Cài được nhưng báo lỗi quyền truy cập | Quyền máy không ổn | Kiểm tra `ls -la ~`; không dùng sudo với cách cài mặc định; Windows kiểm tra policy máy công ty |
| Model hoặc provider chưa hoạt động | Cấu hình chưa khớp | Chạy theo thứ tự: `hermes doctor` → `hermes model` → `hermes auth`; restart session sau khi đổi cấu hình |
| Chạy nhưng không phản hồi như mong đợi | Model, quota hoặc provider sai | Chọn lại model bằng `hermes model`, kiểm tra `hermes doctor`; gateway thì restart dịch vụ |
| Đang xử lý muốn dừng | — | Nhấn Ctrl+C trên CLI; trên Desktop nhấn nút Stop trong khung chat |

> 💡 Khi hỏi hỗ trợ, gửi kèm `hermes --version`, `hermes doctor`, hệ điều hành đang dùng và mô tả các bước đã làm trước khi lỗi — team hỗ trợ khoanh vùng nhanh hơn nhiều.

### Bài tiếp theo trong lộ trình

- Bài trước: 9Router và Hermes Agent: 2 công cụ AI mà dev nào cũng nên biết
- Cùng chủ đề: [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te/)

### Nguồn

- Nguồn chính thức: [Hermes Agent documentation](https://hermes-agent.nousresearch.com/docs/), [GitHub Repository](https://github.com/NousResearch/hermes-agent), [Cộng đồng Discord của Nous Research](https://discord.gg/NousResearch)
- Nội dung biên tập lại từ tài liệu hướng dẫn cài đặt Hermes Agent của AI Guru x TiniX theo phong cách LearnWithHuy; đường dẫn và lệnh nên đối chiếu lại với tài liệu chính thức tại thời điểm đọc.

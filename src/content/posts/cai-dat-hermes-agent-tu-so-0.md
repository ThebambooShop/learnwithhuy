---
title: "Cài đặt Hermes Agent từ con số 0: hướng dẫn chi tiết cho Windows, macOS và Linux"
description: "Hướng dẫn cài Hermes Agent trên CLI và Desktop cho cả ba hệ điều hành, cấu hình provider qua 9Router, giải thích 6 khái niệm cốt lõi và bảng 8 lỗi thường gặp kèm cách xử lý."
topic: "cong-cu-ai"
date: "2026-11-17"
cover: "/images/covers/posts/cai-dat-hermes-agent-tu-so-0.jpg"
views: 720
faq:
  - q: "Cài Hermes Agent mất bao lâu?"
    a: "Khoảng 15 phút từ con số 0 đến hội thoại AI đầu tiên. Installer tự động cài uv, Python 3.11, Node.js, ripgrep và ffmpeg vào thư mục ~/.hermes/ — bạn chỉ cần Git và curl (hoặc PowerShell 5.1+ trên Windows) có sẵn."
  - q: "Nên dùng bản CLI hay bản Desktop?"
    a: "Dùng CLI nếu bạn làm việc chủ yếu trong terminal, cần chạy remote qua SSH/VPS — bản này nhẹ nhất. Dùng Desktop nếu thích giao diện cửa sổ có preview file. Lưu ý bản Desktop chỉ hỗ trợ macOS Apple Silicon và Windows, không hỗ trợ Mac chip Intel."
  - q: "Hermes Agent có phải trả phí không?"
    a: "Hermes Agent là mã nguồn mở miễn phí (MIT). Nhưng mô hình phía sau mới phát sinh chi phí: chạy local qua Ollama thì miễn phí, còn provider thương mại như OpenAI hay Anthropic tính phí theo token."
  - q: "Kết nối Hermes với 9Router bằng cách nào?"
    a: "Trong Setup Wizard chọn Custom endpoint, nhập Base URL http://localhost:20128/v1 và API key do 9Router cấp, chọn chế độ Chat Completions, rồi điền tên combo đã tạo trong 9Router vào ô model name."
---

[Hermes Agent](/bai-viet/9router-va-hermes-agent/) là AI agent mã nguồn mở của Nous Research — không chỉ trả lời câu hỏi mà còn chủ động *hành động*: đọc ghi file, chạy lệnh terminal, điều khiển trình duyệt, gọi API. Bài này là hướng dẫn thực hành: từ con số 0 đến hội thoại AI đầu tiên trong khoảng 15 phút, trên cả ba hệ điều hành.

## Hai bản phân phối: CLI và Desktop

| Tiêu chí | Hermes CLI / TUI | Hermes Desktop |
| --- | --- | --- |
| **Giao diện** | Terminal, TUI đầy đủ | Cửa sổ đồ họa Electron |
| **Nền tảng** | Linux, macOS, Windows | macOS (Apple Silicon), Windows, Linux (qua CLI) |
| **Điểm mạnh** | Nhẹ, chạy remote qua SSH/VPS | Xem file, preview, trực quan |
| **Cài đặt** | One-liner curl / PowerShell | Tải bộ cài trực tiếp |

Chỉ muốn dùng terminal thì cài bản CLI là đủ. Thích giao diện cửa sổ thì đọc thêm phần Desktop ở cuối bài.

## Cài bản CLI: chuẩn bị gì trước

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
# Ubuntu / Debian / Mint / WSL2
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

## Cài đặt một dòng lệnh

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

## Setup Wizard — cấu hình lần đầu

Ngay sau khi cài xong, wizard tự mở và hỏi bạn muốn thiết lập theo cách nào:

| Lựa chọn | Ý nghĩa |
| --- | --- |
| **Quick Setup (Nous Portal)** | Đăng nhập OAuth miễn phí, không cần API key — phù hợp người mới |
| **Full Setup** | Tự cấu hình từng provider, tool và option — dùng khi muốn kiểm soát toàn bộ, bao gồm cả việc dùng 9Router |
| **Blank Slate** | Tắt tất cả trừ mức tối thiểu, tự opt-in từng tính năng |

Khuyến nghị: **chọn Full Setup** — cho phép kiểm soát hoàn toàn và không khó hơn Quick Setup là mấy, vì wizard dẫn dắt từng bước.

### Bảy bước trong wizard

1. **Chọn kiểu thiết lập** — Full Setup.
2. **Chọn provider** — Hermes hỗ trợ rất nhiều: Nous Portal, OpenAI, Anthropic, OpenRouter, AWS Bedrock, Azure, Ollama, LM Studio... Khi dùng 9Router, chọn **Custom endpoint** ở cuối danh sách.
3. **Nhập Base URL và API Key** — với 9Router: `http://localhost:20128/v1` và key do 9Router cấp.

> ℹ️ Cảnh báo `could not verify this endpoint supports /v1/models` là **bình thường** với custom endpoint — một số endpoint không expose route đó, Hermes vẫn kết nối và hoạt động đúng; chỉ là bạn cần nhập tên model thủ công ở bước sau.

4. **Chọn API compatibility mode** — chọn **Chat Completions** vì 9Router dùng chuẩn `/chat/completions` của OpenAI. Tên model điền **tên combo** đã tạo trong giao diện 9Router (ví dụ `my-first-combo`) — mỗi combo gom nhiều model và rule định tuyến lại, nhưng về phía Hermes nó chỉ là một tên model để chọn.
5. **Chọn terminal backend** — đa số chọn **Local** (chạy trực tiếp trên máy hiện tại). Còn có Docker, SSH, Modal, Daytona cho trường hợp remote/cloud.
6. **Bật/tắt Tool** — hơn 20 nhóm tool: Web Search, Browser Automation, Terminal, File Operations, Vision, Image Generation, TTS, Skills, Memory, Cron Jobs... Mặc định bật tất cả, dùng phím SPACE để toggle, ENTER xác nhận.
7. **Image Generation và Gateway** — nếu chưa cần tạo ảnh thì Skip. Gateway nhắn tin (Telegram, Discord, Slack, WhatsApp) cho phép chat từ điện thoại khi Agent chạy trên máy chủ — chỉ dùng CLI thì bỏ qua.

Hoàn tất, cấu hình được lưu tại: `~/.hermes/config.yaml` (config), `~/.hermes/.env` (API keys), `~/.hermes/` (cron, sessions, logs).

### Đổi provider và model sau khi cài

```bash
hermes model                                     # menu chọn model tương tác
hermes config set provider.base_url "http://localhost:20128/v1"
hermes config set model "ten-combo-moi"
hermes config get                                # xem cấu hình hiện tại
```

## Cài bản Desktop

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

## Sáu khái niệm cốt lõi

| Khái niệm | Nghĩa | Vai trò |
| --- | --- | --- |
| **CLI** | Giao diện dòng lệnh | Hai mục đích: lệnh quản trị ngoài terminal (setup, update) và lệnh slash trong hội thoại (`/model`, `/skills`) |
| **Session** | Phiên làm việc | Mỗi lượt tương tác là một session; lịch sử lưu vết trong SQLite, tự nén khi tiến sát giới hạn ngữ cảnh |
| **Tools** | Công cụ | Hàm chức năng cụ thể: đọc file, chạy terminal, tìm kiếm web, điều khiển trình duyệt |
| **Skills** | Kỹ năng | Tài liệu hướng dẫn dạng Markdown dạy agent cách phối hợp nhiều công cụ cho một loại tác vụ |
| **Memory** | Bộ nhớ | Lưu bền vững thông tin về người dùng và môi trường, tự nạp lại ở mọi session sau |
| **MCP** | Model Context Protocol | Chuẩn giao tiếp mở để kết nối MCP Server bên ngoài: SQL, GitHub API, quản lý dự án |

## Nâng cao: Skills, Tools và MCP

### Quản lý Skills

```bash
hermes skills list            # xem danh sách skill đã cài
hermes skills search QUERY    # tìm skill trong kho
hermes skills install ID      # cài skill theo ID hoặc URL
hermes skills inspect ID      # xem trước nội dung skill
hermes skills opt-out         # tắt tự động seed bundled skills
```

Trong hội thoại: `/excalidraw` gọi một skill cụ thể; ghép nhiều skill trong cùng lệnh `/github-pr-workflow /test-driven-development fix issue #123`; `/learn` tự đóng gói workflow hiện tại thành skill mới.

### Tra cứu bộ Tools tích hợp

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

### Tự viết Custom Tool

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

### Tích hợp MCP

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

## Hội thoại đầu tiên — thử thật

Demo tác vụ 1: *"Tìm kiếm thông tin về thần Hermes trên Wikipedia, tạo thư mục docs tại ~/, ghi nội dung tìm được vào một file trong thư mục này."* Hermes tự phân tích mục tiêu, lập kế hoạch và tự điều phối 4 công cụ liên tiếp: `browser_navigate` mở trang Wikipedia → `terminal` tạo thư mục và file rỗng → `browser_console` trích xuất nội dung trang → `write_file` ghi vào `~/docs/hermes_wikipedia.txt`.

Demo tác vụ 2: *"Hãy xoá file vừa tạo rồi sau đó xoá thư mục docs."* Hermes chạy 2 lệnh terminal liên tiếp để dọn dẹp.

> ⚠️ Nếu tool browser không hoạt động, kiểm tra Node.js đã cài chưa bằng `node --version` — browser tools cần Node.js để chạy Playwright. Thiếu thì cài từ nodejs.org rồi chạy lại `hermes setup`.

Sau khi xác nhận hoạt động, thử thêm: `/skills` xem danh sách skill, `/model` đổi model nhanh trong chat, dán một đoạn code bất kỳ để yêu cầu giải thích, chạy `hermes doctor` khi gặp vấn đề.

## 8 lỗi thường gặp và cách xử lý

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

## Bài tiếp theo trong lộ trình

- Bài trước: [9Router và Hermes Agent: 2 công cụ AI mà dev nào cũng nên biết](/bai-viet/9router-va-hermes-agent/)
- Cùng chủ đề: [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te/)

## Nguồn

- Nguồn chính thức: [Hermes Agent documentation](https://hermes-agent.nousresearch.com/docs/), [GitHub Repository](https://github.com/NousResearch/hermes-agent), [Cộng đồng Discord của Nous Research](https://discord.gg/NousResearch)
- Nội dung biên tập lại từ tài liệu hướng dẫn cài đặt Hermes Agent của AI Guru x TiniX theo phong cách LearnWithHuy; đường dẫn và lệnh nên đối chiếu lại với tài liệu chính thức tại thời điểm đọc.

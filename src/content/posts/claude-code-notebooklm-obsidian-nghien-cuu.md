---
title: "Biến Claude Code, NotebookLM và Obsidian thành cỗ máy nghiên cứu cá nhân"
description: "Một quy trình từng bước để nghiên cứu bất kỳ chủ đề phức tạp nào nhanh hơn, có hệ thống hơn: Claude Code điều phối, NotebookLM phân tích, Obsidian ghi nhớ — càng dùng càng sắc bén."
topic: "cong-cu-ai"
date: "2026-11-17"
cover: "/images/covers/posts/claude-code-notebooklm-obsidian-nghien-cuu.jpg"
views: 1200
---

Bạn có bao giờ thấy mình trong cảnh này chưa: mở mười tab, xem video, đọc bài viết, ghi chú vào một nơi nào đó — rồi một tiếng sau nhận ra mình có một đống thông tin nhưng không biết nên kết luận gì, dùng vào đâu, hay lưu lại thế nào để lần sau tận dụng tiếp?

Cách làm đó không sai, nhưng nó có ba điểm yếu lớn. **Thứ nhất**, việc thu thập nguồn tốn nhiều thời gian. **Thứ hai**, phần phân tích thường phụ thuộc vào trí nhớ và năng lượng của bạn trong từng phiên làm việc. **Thứ ba**, những gì bạn học được không tự động tích lũy thành một hệ thống tri thức có thể dùng lại.

Bài này hướng dẫn bạn xây một workflow nghiên cứu dùng **Claude Code**, **Skill Creator**, **NotebookLM** và **Obsidian**. Thiết lập dưới 30 phút, không đòi hỏi biết lập trình.

## Kết quả bạn sẽ có

Một quy trình nghiên cứu có thể chạy theo lệnh: nhận một yêu cầu nghiên cứu → tìm nguồn → đưa nguồn vào NotebookLM để phân tích → trả kết quả về dạng markdown → lưu vào Obsidian. Và điểm khác biệt quan trọng nhất: **không chỉ chạy một lần** — mỗi tài liệu mới được lưu vào Obsidian giúp hệ thống hiểu phong cách và ưu tiên của bạn hơn theo thời gian.

## Bốn công cụ, bốn vai trò

Workflow có bốn lớp. Mỗi công cụ xử lý một phần khác nhau của vấn đề, nên bạn không phải ép một công cụ làm mọi thứ:

| Công cụ | Vai trò | Làm gì |
| --- | --- | --- |
| Claude Code | Bộ điều phối | Chạy lệnh, gọi skill, quản lý file, điều phối toàn bộ pipeline. Bạn nói bằng ngôn ngữ tự nhiên, nó biến thành các bước thực thi. |
| Skill Creator | Lớp tùy biến | Plugin giúp tạo skill tái sử dụng bằng mô tả tự nhiên — bạn nói muốn skill làm gì, Claude Code tạo cấu trúc và cài đặt. |
| NotebookLM | Bộ phân tích | Đọc nguồn và tạo phân tích sâu, tóm tắt, mindmap, flashcard, infographic, audio overview. Phần nặng chạy trên hạ tầng Google, không tốn token Claude của bạn. |
| Obsidian | Bộ nhớ dài hạn | Lưu mọi thứ dạng markdown trong máy bạn. Theo thời gian, Claude Code đọc các file này để hiểu bạn quan tâm điều gì và ra quyết định theo tiêu chí nào. |

Ghép lại, bạn có một hệ thống nghiên cứu thực thi theo lệnh, phân tích ở quy mô lớn hơn sức đọc thủ công của một người, và **cải thiện dần nhờ bộ nhớ trong Obsidian**.

## Trước khi bắt đầu

Chuẩn bị ba thứ:

- Claude Code đã cài trên máy và chạy được trong terminal.
- Một Obsidian vault — nơi lưu toàn bộ kết quả nghiên cứu.
- Python và pip, để cài công cụ kết nối NotebookLM.

> ⚠️ **Lưu ý quan trọng:** NotebookLM hiện chưa có public API chính thức cho workflow kiểu này. Cách làm dưới đây dùng dự án mã nguồn mở [`notebooklm-py`](https://github.com/teng-lin/notebooklm-py) để thao tác với NotebookLM. Vì đây là công cụ không chính thức, hãy kiểm tra lại repo, quyền truy cập và mức ổn định trước khi dùng cho dữ liệu nhạy cảm hoặc workflow sản xuất.

## Thiết lập trong 5 bước

### Bước 1: Cài Skill Creator trong Claude Code

Mở Claude Code trong **thư mục Obsidian vault** — điều này quan trọng vì các file markdown do Claude Code tạo ra sẽ được Obsidian nhận diện ngay. Trong Claude Code, chạy:

```text
/plugin
```

Tìm `skill-creator`, cài plugin, thoát Claude Code rồi mở lại. Từ giờ bạn có thể tạo skill mới chỉ bằng cách mô tả bằng ngôn ngữ tự nhiên.

### Bước 2: Tạo skill tìm kiếm YouTube

Skill này cho phép Claude Code tìm video YouTube và trả về dữ liệu có cấu trúc: tiêu đề, kênh, số subscriber, lượt xem, thời lượng, ngày đăng, URL và tỷ lệ lượt xem trên subscriber.

Trong Claude Code, chạy prompt sau:

```text
/skill-creator I want to create a skill that searches YouTube and returns structured video results.
It should use yt-dlp to search for videos by query, return the top 20 results by default,
and include metadata for each video - title, channel name, subscriber count, view count,
duration, upload date, and URL.
It should filter to the last 6 months by default but support a --months flag to change that.
It should also calculate a views-to-subscribers ratio as an engagement metric.
The output should be nicely formatted with dividers between each result and human-readable numbers.
```

Claude Code sẽ tạo skill, cài đặt và xác nhận. Sau đó bạn dùng được lệnh dạng `/yt-search`. Nếu máy chưa có `yt-dlp`, cài trước khi chạy skill này.

### Bước 3: Cài NotebookLM-py

Mở **terminal riêng** (không phải bên trong Claude Code) rồi chạy:

```text
pip install notebooklm-py
```

Sau đó đăng nhập:

```text
notebooklm login
```

Trình duyệt sẽ mở ra — đăng nhập tài khoản Google, cấp quyền cần thiết, quay lại terminal. Khi hoàn tất, kết nối tới NotebookLM đã sẵn sàng.

### Bước 4: Tạo skill NotebookLM

Giờ dạy Claude Code cách dùng `notebooklm-py`:

```text
/skill-creator create a skill so we can best use the notebooklm-py tool.
Reference the GitHub repo at github.com/teng-lin/notebooklm-py and build a skill that can:
create new notebooks, add sources (YouTube URLs, text, files), run analysis on those sources,
and generate deliverables including audio overview, mindmap, flashcards, and infographic.
```

Sau bước này, Claude Code có một skill NotebookLM đầy đủ: tạo notebook, thêm nhiều nguồn theo giới hạn của NotebookLM, yêu cầu phân tích và xuất các định dạng mà NotebookLM hỗ trợ.

### Bước 5: Ghép mọi thứ thành một pipeline duy nhất

Đây là phần biến workflow thành hệ thống thực sự mạnh — thay vì tự tìm, tự copy nguồn, tự yêu cầu phân tích rồi tự lưu kết quả, bạn tạo một skill pipeline làm tất cả theo thứ tự:

```text
/skill-creator I want to create a YouTube research pipeline skill that combines the yt-search skill
and the NotebookLM skill. When I use this pipeline skill I want it to:
take what I told it to research, go to YouTube and find 10 relevant videos using the yt-search skill,
use the NotebookLM skill to create a new notebook, add those video sources to the notebook,
then do analysis on the topic based on what I said when I invoked the skill.
Furthermore ask me if I want a deliverable - NotebookLM can create flashcards, infographics,
mindmaps, audio overviews. If I don't specify a deliverable assume none.
After analysis bring everything back to me in a markdown file saved to the vault,
and also show it in chat. Include all YouTube search metadata in the output -
sources used, view counts, channel names, engagement ratios.
```

Từ giờ, một lệnh duy nhất là bắt đầu được cả phiên nghiên cứu hoàn chỉnh.

## Workflow chạy thật trông thế nào?

Ví dụ: bạn muốn nghiên cứu các framework AI agent năm 2026 — framework nào đang được developer dùng thật, cái nào bị thổi phồng, và còn góc nội dung nào chưa được khai thác:

```text
/yt-pipeline I want to research AI agent frameworks in 2026.
Which frameworks are developers actually adopting - LangGraph, CrewAI, AutoGen,
Agno, or something else?
I want to understand what's driving views on this topic, where there's disagreement
in the community,
what the outliers are, and what angles haven't been covered well yet.
Find 10 relevant sources, push them to a new NotebookLM notebook,
run a full analysis, and generate an infographic showing the landscape.
```

Pipeline chạy qua 5 chặng:

1. **Nhận chủ đề nghiên cứu** từ yêu cầu của bạn.
2. **Tìm 10 video liên quan** qua skill YouTube — tutorial, video so sánh, nhận định của developer.
3. **Tạo NotebookLM notebook** và thêm các nguồn.
4. **Chạy phân tích sâu** — và tạo deliverable nếu bạn yêu cầu.
5. **Lưu kết quả vào Obsidian** dạng markdown.

Tổng thời gian xử lý trong ví dụ gốc khoảng sáu phút — phần lớn là NotebookLM đọc và phân tích nguồn trên máy chủ Google. Claude Code chủ yếu điều phối, gom kết quả, cấu trúc lại và lưu vào vault.

Kết quả bạn nhận lại nên bao gồm: framework nào đang tăng, framework nào chững lại; các phàn nàn và điểm nghẽn developer nhắc đi nhắc lại; các nguồn có engagement bất thường so với quy mô kênh; các góc nội dung còn thiếu; và một file markdown có nguồn, metadata và kết luận rõ ràng — đã nằm sẵn trong Obsidian vault.

## Vì sao Obsidian làm workflow này khác hẳn?

Nếu chỉ dừng ở tìm nguồn và phân tích một lần, workflow này đã hữu ích. Nhưng Obsidian mới là phần biến nó thành hệ thống có khả năng **tích lũy**.

Sau nhiều phiên, vault của bạn trở thành một corpus gồm mọi thứ đã nghiên cứu: chủ đề, nguồn, phân tích, mô hình lặp lại, kết luận, câu hỏi mở. Claude Code đọc được các file này — nó thấy liên kết giữa các chủ đề, nhận ra lĩnh vực bạn quay lại nhiều lần, và học được định dạng output bạn thích.

File `claude.md` trong vault là nơi biến phần này thành quy tắc rõ ràng: quy ước đặt tên, phong cách phân tích, tiêu chuẩn output, cách lưu file. Bạn có thể cập nhật định kỳ bằng một yêu cầu đơn giản:

```text
Can we update claude.md so it better reflects my work style,
analysis approach, and output preferences based on our latest conversations?
```

Claude Code sẽ đọc các phiên gần đây, nhận diện pattern và cập nhật file. Làm mỗi tuần một lần, sau khoảng một tháng output bắt đầu khớp với cách bạn nghĩ mà không cần prompt dài. Duy trì trong một năm, bạn có một trợ lý nghiên cứu đã hấp thụ hàng trăm phiên làm việc — vận hành giống một hệ thống được huấn luyện trên chính cách bạn tư duy.

## YouTube không phải phần cốt lõi

Dễ nhìn workflow này và nghĩ "đây là quy trình nghiên cứu YouTube". Cách hiểu đó quá hẹp — **YouTube chỉ là một nguồn dữ liệu, phần quan trọng là cấu trúc pipeline**. Bạn có thể thay bằng bất kỳ nguồn nào Claude Code truy cập được:

- **PDF**: paper học thuật, báo cáo ngành, whitepaper, tài liệu nội bộ.
- **Web công khai**: bài báo, documentation, blog, landing page, changelog.
- **File local**: note cá nhân, transcript, dữ liệu export, bản nháp.
- **Google Drive**: Docs, Sheets, Slides hoặc tài liệu đã lưu sẵn.

Template giữ nguyên: lấy nguồn → đưa vào lớp phân tích → yêu cầu output phù hợp → lưu vào bộ nhớ dài hạn. Nghiên cứu crypto ecosystem bằng whitepaper, phân tích công nghệ mới từ talk hội nghị, map một ngách nội dung dựa trên video đang perform — cùng một logic.

## Checklist triển khai nhanh

- Mở Claude Code trong thư mục Obsidian vault.
- Cài plugin `skill-creator`, thoát và mở lại Claude Code.
- Tạo skill tìm YouTube bằng `yt-dlp`.
- Cài `notebooklm-py` và đăng nhập Google bằng `notebooklm login`.
- Tạo skill NotebookLM: tạo notebook, thêm nguồn, sinh deliverable.
- Tạo pipeline skill kết hợp tìm nguồn → phân tích → xuất markdown → lưu vault.
- Chạy pipeline với một chủ đề nghiên cứu thật.
- Cập nhật `claude.md` hằng tuần để hệ thống ngày càng hiểu cách bạn làm việc.

> **Công thức cốt lõi:** nguồn dữ liệu tốt + pipeline rõ ràng + phân tích bằng NotebookLM + bộ nhớ Obsidian = một hệ thống nghiên cứu càng dùng càng có ngữ cảnh.

## Kết

Điểm hay nhất của workflow này không phải là "làm nhanh hơn" — mà là nó **tích lũy**: mỗi phiên nghiên cứu làm hệ thống hiểu bạn hơn một chút, giống tinh thần từng bước một mà blog này luôn nhắc. Hãy bắt đầu bằng một chủ đề thật sự bạn đang cần nghiên cứu tuần này, rồi để claude.md học dần theo cách bạn làm việc.

---
title: "CLAUDE.md, Project và Skills — ba trụ cột để Claude hiểu doanh nghiệp bạn"
description: "Bài 3 series hệ thống AI Agent với Claude: cấu trúc CLAUDE.md 6 phần, mẫu theo 4 vai trò, cách dựng Project trong 30 phút, và công thức viết Skill 6 thành phần với ví dụ thực tế."
topic: "cong-cu-ai"
date: "2026-11-17"
cover: "/images/covers/posts/claude-claude-md-project-skills.jpg"
views: 920
---

Sau kiến trúc tổng thể ([bài 2](/bai-viet/claude-kienc-truc-7-tang-6-tai-san-tri-thuc/)), bài này đi vào ba trụ cột thực tế nhất: file CLAUDE.md, không gian Project, và cơ chế Skills — nơi "cách công ty bạn làm việc" được đóng gói thành thứ Claude hiểu được và tái sử dụng được.

## CLAUDE.md — bộ não thứ hai của doanh nghiệp

CLAUDE.md là file ngữ cảnh nền luôn hiện diện trong mỗi phiên làm việc — đặc biệt trong Claude Code và Cowork. Tên file đúng là **CLAUDE.md, viết hoa hết, đặt ở thư mục gốc của project** — Claude tìm file với tên này tự động; đặt là claude.md hay CONTEXT.md thì Claude sẽ không tự đọc.

Khác với ABOUT-ME (về cá nhân) và GLOBAL-INSTRUCTIONS (quy tắc tổng quát), CLAUDE.md là **ngữ cảnh dự án cụ thể**: dự án này là gì, vai trò của bạn trong dự án, đối tượng người dùng, phong cách team, chuẩn đầu ra, định dạng báo cáo, điều cấm tuyệt đối. Mỗi project nên có CLAUDE.md riêng — đừng dùng chung cho mọi project vì ngữ cảnh sẽ bị loãng.

Một CLAUDE.md tốt **dưới 2.000 từ**. Nếu dài hơn, tách thành các file phụ (about-me.md, voice-profile.md, anti-ai-style.md, output-templates.md) và tham chiếu từ file gốc.

### Cấu trúc 6 phần tiêu chuẩn

| Phần | Nội dung | Ví dụ |
| --- | --- | --- |
| **1. Định nghĩa vai trò** | Vai trò Claude nhập vai, cấp độ chuyên môn, phạm vi trách nhiệm — đủ cụ thể để Claude biết "đây là project về gì" trong vài giây | "Bạn là chuyên gia tư vấn AI cho doanh nghiệp Việt Nam, cấp senior, phối hợp đội Marketing và Sales của công ty XYZ" |
| **2. Mô hình tư duy** | Cách ra quyết định, mức chi tiết, nguyên tắc ưu tiên — phần một nói "bạn là ai", phần hai nói "bạn nghĩ thế nào" | "Ưu tiên thực tế trên lý thuyết. Khi có hai phương án, chọn phương án triển khai được trong 30 ngày. Luôn kèm số liệu nếu có thể; không có số thì nêu rõ giả định" |
| **3. Nguyên tắc làm việc** | Những điều mặc định tuân thủ trong mọi tác vụ | "Làm rõ mục tiêu trước khi bắt tay. Yêu cầu mơ hồ thì đặt 1–2 câu hỏi ngược thay vì đoán. Nêu rủi ro hoặc trade-off nếu có" |
| **4. Điều cấm** | Điều tuyệt đối không làm — giới hạn là cách bảo vệ uy tín thương hiệu | "Không bịa thông tin. Không hứa SLA hoặc cam kết doanh số nhân danh công ty. Không nói thay khách hàng" |
| **5. Định dạng đầu ra** | Quy ước về checklist, bảng, kế hoạch, email, deck | "Mặc định markdown. Email tối đa 200 từ với subject rõ. Deck tối đa 10 slide, mỗi slide một thông điệp" |
| **6. Tham chiếu tài sản** | Liên kết đến các file liên quan | "Xem voice-profile.md cho phong cách viết, templates/ cho mẫu đầu ra, outputs/ cho ví dụ chất lượng cao" |

### Mẫu theo bốn vai trò phổ biến

- **Marketing (SaaS B2B):** ưu tiên ROI đo được, insight từ data thực, ngại buzzword. Mỗi đề xuất kèm số liệu, mỗi campaign kèm KPI và thời gian đánh giá. Cấm tự ý xác định budget, hứa hẹn lead volume không cơ sở. Định dạng: campaign brief 1 trang, content draft 300–500 từ, social post tối đa 280 ký tự.
- **Sales (B2B):** ưu tiên tốc độ phản hồi, cá nhân hoá thật, số liệu CRM hơn cảm tính. Mỗi proposal có giá trị cụ thể cho khách, mỗi follow-up có lý do gửi. Cấm bịa thông tin khách hàng, hứa giảm giá nhân danh sales rep. Định dạng: discovery prep 1 trang, proposal 3–5 trang, follow-up email 80–120 từ.
- **Vận hành:** ưu tiên giảm tắc nghẽn hơn cải thiện đột phá, SOP rõ hơn linh hoạt cao. Mỗi đề xuất kèm impact-effort matrix, mỗi SOP kèm checklist. Cấm đề xuất automation khi quy trình thủ công còn thiếu nhất quán. Định dạng: daily brief 5 mục dưới 200 từ, SOP markdown có numbered steps.
- **HR:** ưu tiên công bằng minh bạch, đánh giá behavioral hơn kỹ năng, câu hỏi STAR. Mỗi JD kèm rationale, mỗi resume screening kèm match score + 3 lý do. Cấm phán xét trên dữ liệu thiếu, dùng ngôn từ phân biệt giới tính/tuổi tác. Định dạng: JD 1 trang, screening report top 20, onboarding plan 30/60/90.

### Kiểm thử và rà soát

Hai chu trình cần thiết lập ngay: **kiểm thử bằng tác vụ thật** (dùng 3–5 tác vụ đa dạng — email ngắn, báo cáo 1 trang, đề xuất chiến lược 3 trang; mỗi lỗi quan sát được phải dẫn tới một dòng bổ sung trong CLAUDE.md) và **rà soát hàng tháng** (quy tắc nào không còn hợp lý? Ưu tiên nào đã thay đổi?). Mẹo nâng cao: lưu lịch sử thay đổi trong git — mỗi commit là một bài học vận hành.

> Ba bài học từ thất bại của doanh nghiệp khác: (1) không viết bằng ngôn ngữ trừu tượng — "Hãy chuyên nghiệp" là vô nghĩa, "Mỗi câu dưới 25 từ" là cụ thể và thực thi được; (2) không bỏ phần điều cấm — ít nhất 5 điều cấm rõ ràng, vì không có ranh giới thì Claude trượt vào hành vi không mong muốn; (3) không sao chép CLAUDE.md của doanh nghiệp khác mà không điều chỉnh — lấy cảm hứng được, sao chép thì không.

## Project — bộ nhớ làm việc bền vững

Project là không gian làm việc có ngữ cảnh riêng: tài liệu nền, ví dụ, quy tắc và bộ nhớ. Nếu CLAUDE.md là bộ não, Project là không gian làm việc — nơi bộ não đó vận dụng vào tác vụ cụ thể.

**Bốn dấu hiệu cần tạo Project:** làm một mảng việc lặp lại (tuyển dụng, báo cáo tuần, proposal); cần lưu bối cảnh dài hạn (deal 6 tháng); có nhiều file phải tham chiếu cùng lúc; muốn Claude học từ output tốt trước đó. Một Project nên gắn với **một workstream rõ ràng** — "Báo cáo tuần đội Marketing — 2026 Q2" là tên tốt, "Project Marketing" là tên xấu.

### Ba lớp tạo nên Project hiệu quả

1. **Quy tắc làm việc** — CLAUDE.md của Project: vai trò Claude trong project, naming convention, tiêu chuẩn đầu ra, điều không được làm. Đừng copy nguyên CLAUDE.md cấp công ty xuống.
2. **Tài liệu và dữ liệu nền** — "trí nhớ" Claude truy cập khi làm việc: SOP, brief khách, tài liệu tham chiếu, dữ liệu bối cảnh. Quy tắc: ít mà chất — 3–5 file cốt lõi tốt hơn 50 file bừa bộn.
3. **Đầu ra tốt** — "kim chỉ nam" chất lượng: mẫu báo cáo đã duyệt, proposal đã được khách ký, email nhận phản hồi tích cực. Mỗi mẫu có metadata: ngày, mục đích, đối tượng, kết quả.

### Thiết lập Project trong 30 phút — 7 bước

1. Tạo Project, đặt tên rõ theo workstream
2. Viết phiên bản đầu của CLAUDE.md cho project (không cần hoàn hảo)
3. Nạp 3–5 tài liệu cốt lõi nhất — hỏi: "nếu chỉ có 5 file để giúp một nhân viên mới, tôi chọn 5 file nào?"
4. Lưu 2–3 output mẫu tốt nhất từng có (gold standard)
5. Viết một prompt mẫu ("first task prompt") bám cấu trúc 6 lớp
6. Bắt đầu giao việc thật; sau 5–10 lần dùng, project tự ổn định
7. Sau 2 tuần, review project: tài liệu nào không còn dùng, quy tắc nào cần thêm, output mẫu mới nào nên thêm

> Ba sai lầm phổ biến: dồn quá nhiều việc khác nhau vào một Project (tách thành nhiều project riêng); không có CLAUDE.md trong project (Claude phải tự đoán cách dùng tài liệu); không lưu các đầu ra tốt (mỗi tuần dành 5 phút lưu 1 output xuất sắc nhất).

## Skills — đóng gói cách công ty bạn làm việc thành code

Skill là một thư mục chứa tri thức, hướng dẫn và logic để Claude **tự kích hoạt** khi gặp đúng tác vụ. Khác với prompt (gõ tay mỗi lần), skill là gói knowledge mà Claude tự dùng đúng lúc. Một skill về bản chất là code, không phải prompt: nó có thể version (git), review (đồng nghiệp xem qua), share (cả đội dùng chung), scale (toàn công ty triển khai). Skill hoạt động trên mọi bề mặt: Chat, Cowork, Code, API.

### Ba loại skill

| Loại | Ví dụ | Ghi chú |
| --- | --- | --- |
| **Built-in Skills** | Làm việc với Excel, Word, PowerPoint, PDF; data analysis cơ bản; phân tích hình ảnh | Ship sẵn, dùng ngay, được Anthropic duy trì |
| **Company Skills** | Brand voice của marketing; quy trình thẩm định khoản vay; SOP onboarding 30/60/90; template proposal theo segment | **Giá trị lớn nhất nằm ở đây** — tri thức đặc thù không AI mặc định nào biết |
| **Individual Skills** | Note-taking style cá nhân, code review style, email signature template | Cho từng người làm việc theo cách riêng |

Lộ trình tự nhiên là: built-in → company skills → cá nhân hoá. Doanh nghiệp Việt thường đảo ngược — bắt đầu bằng skill cá nhân và bị mắc kẹt ở đó vì không ai chuyển lên thành skill công ty. **Một công ty có 10 Company Skills tốt hơn một công ty có 100 Individual Skills.**

### Cấu trúc skill tốt — 6 thành phần bắt buộc

Ví dụ skill "weekly-report" (báo cáo tuần đội Marketing):

| Thành phần | Nội dung | Ví dụ |
| --- | --- | --- |
| **1. Trigger** | Tình huống kích hoạt — đủ cụ thể để không kích hoạt nhầm, đủ rộng để bao phủ biến thể | "Người dùng nhắc đến 'báo cáo tuần', 'weekly digest', 'recap tuần', hoặc khi đến chiều thứ Sáu và Marketing manager khởi tạo cuộc trò chuyện" |
| **2. Context** | Tài liệu, dữ liệu, biểu mẫu bắt buộc — nếu thiếu thì hỏi lại, không bịa | "Cần dữ liệu Slack #marketing tuần qua, Notion roadmap, GA traffic, CRM pipeline. Thiếu nguồn nào, hỏi lại trước khi tạo report" |
| **3. Rules** | Tiêu chuẩn đầu ra: định dạng, độ dài, checklist, tone | "Tối đa 1 trang A4. 5 mục cố định: Win, Insight, Vấn đề cần escalate, 3 metric chính, Ưu tiên tuần tới. Không bịa số" |
| **4. Steps** | Các bước thực hiện theo thứ tự, có kiểm tra và rẽ nhánh | "Bước 1: pull data từ 4 nguồn. Bước 2: kiểm tra đủ chưa. Bước 3: phân tích so tuần trước. Bước 4: nhận diện 3 win lớn nhất..." |
| **5. Output** | Định dạng đầu ra cụ thể, mẫu, cách trình bày | "Markdown 1 trang, đặt trong reports/weekly/YYYY-WW.md. H1 tên tuần, H2 cho mỗi mục, bullet không quá 5 mỗi mục" |
| **6. Examples** | Few-shot, mẫu tốt và mẫu xấu, case minh hoạ | "examples/good-weekly-2026-W12.md (xuất sắc), examples/bad-weekly-2026-W08.md (quá dài, generic), examples/template.md" |

Cộng thêm phần **Giới hạn và ngoại lệ** (nên có): điều skill không được làm, khi nào hỏi lại, khi nào escalate — "Không tự ý gửi email. Không cập nhật CRM. Nếu anomaly nghiêm trọng (giảm trên 30%), escalate ngay cho Marketing Manager."

### Tạo skill bằng skill-creator — 4 bước

1. **Mô tả ý tưởng:** "Tôi muốn skill tóm tắt cuộc họp với template công ty" — skill-creator hỏi 4–5 câu để hiểu đủ ngữ cảnh; trả lời cụ thể, câu trả lời mơ hồ dẫn tới skill mơ hồ.
2. **Generate file:** Claude tạo file SKILL.md kèm examples/ và reference/. Kiểm tra kỹ Trigger — trigger sai là skill vô dụng.
3. **Test và refine:** chạy trên 3 tình huống thật; sửa trigger nếu kích hoạt sai, rules nếu output sai chuẩn. Vòng test-refine thường mất 3–5 lần lặp.
4. **Share toàn team:** upload lên private marketplace; quy tắc vàng — chia sẻ khi đã được test bởi ít nhất 2 người và pass 5 use case thật.

Bốn use case skill nên xây sớm: **báo cáo định kỳ** (5 phút thay vì 90 phút mỗi báo cáo), **soạn proposal** (tiết kiệm 60–70% thời gian draft), **tóm tắt họp** (biên bản 1 trang trong 3 phút), **phân tích phản hồi khách hàng** (hàng trăm phản hồi thành 5 theme với recommended action).

> Công thức ngắn: **Skill = Trigger + Context + Rules + Steps + Output + Examples.** Đừng viết skill như một bài văn — hãy viết như một quy trình làm việc với các bước rõ ràng. Đừng cố làm skill "all-in-one". Một skill tốt không chỉ giúp Claude làm đúng hơn — nó giúp cả đội làm giống nhau và nhanh hơn. Đó là khác biệt giữa "nhiều người giỏi" và "một tổ chức giỏi".

## Bài tiếp theo trong series

- **Bài 4:** [Connectors, MCP, Plugins và đội ngũ sub-agent: đưa Claude chạm vào hệ thống thật](/bai-viet/claude-connectors-mcp-sub-agents/)
- Bài 5: Prompt giao việc chuẩn 6 lớp và bộ kỹ năng người dùng giỏi
- Bài 6: Claude cho 8 phòng ban, tự động hoá và lộ trình 30 ngày
- [Bài 1](/bai-viet/claude-doanh-nghiep-tu-duy-va-he-sinh-thai/) · [Bài 2](/bai-viet/claude-kienc-truc-7-tang-6-tai-san-tri-thuc/)

## Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn xây dựng hệ thống AI Agent với Claude (CES Global 2026) — có biên tập lại cấu trúc theo phong cách LearnWithHuy. Các số liệu là kinh nghiệm chia sẻ trong tài liệu gốc, mang tính tham khảo.

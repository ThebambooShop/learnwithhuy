---
title: "Prompt giao việc chuẩn 6 lớp cho Claude: cấu trúc và cách tránh 3 lỗi phổ biến"
description: "Cấu trúc prompt 6 lớp (Goal, Context, Data, Output, Constraints, Validation) với 3 mẫu áp dụng thực tế, 3 lỗi mà 90% người dùng vẫn mắc, 7 thói quen của power user và cách dùng memory đúng."
topic: "prompt-engineering"
date: "2026-11-17"
cover: "/images/covers/posts/prompt-giao-viec-6-lop-best-practices.jpg"
featured: true
views: 1650
faq:
  - q: "Prompt 6 lớp là gì?"
    a: "Là cấu trúc giao việc cho AI gồm 6 thành phần: Goal (mục tiêu), Context (bối cảnh), Data (dữ liệu), Output (tiêu chuẩn đầu ra), Constraints (ràng buộc), Validation (cách kiểm tra). Mỗi lớp giải quyết một dạng mơ hồ — bỏ qua lớp nào Claude phải đoán lớp đó."
  - q: "Prompt bao nhiêu từ là đủ?"
    a: "Không quan trọng độ dài — quan trọng đủ 6 lớp. Một prompt 80 từ đầy đủ sáu lớp cho kết quả ổn định hơn prompt 500 từ rườm rà. Khi đã có CLAUDE.md và Project, prompt càng ngắn càng tốt vì bối cảnh nền đã có sẵn."
  - q: "Prompt 6 lớp khác gì với Skill?"
    a: "Prompt dùng cho một lần giao việc cụ thể; skill là gói tri thức đóng gói để Claude tự kích hoạt khi gặp đúng tác vụ — dùng lặp lại, cho cả đội. Tìm được prompt hay cho tác vụ lặp lại? Đóng gói nó thành skill (xem <a href='/bai-viet/claude-claude-md-project-skills/'>bài 3 trong series</a>)."
  - q: "Mẹo nào nâng chất lượng đầu ra nhanh nhất?"
    a: "Cho Claude phản biện chính nó: 'Hãy chỉ ra 3 điểm yếu của bản nháp.' Một vòng phản biện nâng chất lượng lên 1–2 bậc. Cách thứ hai: đính kèm ví dụ tốt — với ba ví dụ mẫu, chất lượng tăng thêm 50%."
---

Sau khi đã có kiến trúc, tài sản tri thức, project, skills và workflow ([bài 1–4](/bai-viet/claude-doanh-nghiep-tu-duy-va-he-sinh-thai/)), bạn vẫn cần biết cách giao một việc cụ thể cho Claude. Đó là cấu trúc prompt sáu lớp — phần thực hành thiết yếu của mỗi người dùng AI.

Prompt tốt không cần dài vô tận. Nó cần đủ rõ về sáu lớp: mục tiêu, bối cảnh, dữ liệu, tiêu chuẩn đầu ra, ràng buộc, cách kiểm tra. Mỗi lớp giải quyết một dạng mơ hồ phổ biến. Bỏ qua một lớp là Claude phải đoán — và đoán thường không đúng ý.

## Cấu trúc prompt 6 lớp

| Lớp | Nội dung | Câu hỏi để đảm bảo đầy đủ |
| --- | --- | --- |
| **1. Mục tiêu (Goal)** | Kết quả mong muốn, phạm vi, ưu tiên | "Sau khi Claude xong, tôi sẽ có sản phẩm gì cụ thể?" |
| **2. Bối cảnh (Context)** | Dự án, người dùng, tình huống sử dụng | "Claude cần biết gì về tình huống này để tránh đoán?" |
| **3. Dữ liệu (Data)** | File, link, nguồn tham chiếu | "Claude sẽ dựa vào dữ liệu nào, không phải đoán?" |
| **4. Tiêu chuẩn đầu ra (Output)** | Format, độ dài, checklist chất lượng | "Đầu ra trông như thế nào, dài bao nhiêu, có những phần gì?" |
| **5. Ràng buộc (Constraints)** | Điều không được làm, phạm vi sửa đổi | "Có gì Claude không được làm để tránh rủi ro?" |
| **6. Cách kiểm tra (Validation)** | Test case, tiêu chí đạt, cách review | "Làm sao biết đầu ra đạt chuẩn?" |

Ví dụ lớp 1: "Tôi cần một bản nháp proposal một trang cho khách hàng ngành bảo hiểm phi nhân thọ" — không phải "giúp tôi với khách hàng bảo hiểm". Ví dụ lớp 6: "Cuối cùng, tự kiểm tra lại theo checklist 5 tiêu chí: (1) rõ vấn đề khách đang gặp, (2) rõ đề xuất với ROI cụ thể, (3) có số liệu hỗ trợ từ tài liệu đính kèm, (4) có bước tiếp theo cụ thể, (5) không vi phạm điều cấm."

**Công thức ngắn để nhớ: Goal + Context + Data + Output + Constraints + Validation.** Ví dụ thực tế dưới 80 từ nhưng đầy đủ sáu lớp: "Hãy tạo bản nháp proposal 1 trang cho khách hàng ngành bảo hiểm. Dùng tài liệu brief.pdf và pricing.xlsx. Giữ giọng điệu chuyên nghiệp, ngắn gọn. Trả ra dạng bullet rõ ràng, có 3 phần: vấn đề, đề xuất, bước tiếp theo. Không bịa số liệu. Cuối cùng, tự kiểm tra lại theo checklist 5 tiêu chí." So với prompt 500 từ rườm rà, prompt sáu lớp cho kết quả ổn định hơn vì Claude biết chính xác đang được yêu cầu gì và sẽ bị đánh giá theo tiêu chí nào.

### Ba tình huống áp dụng thực tế

**Soạn email cold outreach:** Mục tiêu — viết email cold outreach cho Giám đốc CNTT công ty bảo hiểm phi nhân thọ, để đặt demo 30 phút về giải pháp AI cho bộ phận underwriting. Bối cảnh — công ty 200–500 nhân viên, đang đầu tư chuyển đổi số. Dữ liệu — brief đính kèm, profile LinkedIn người nhận. Đầu ra — 1 email tối đa 120 từ, subject line rõ, một CTA. Ràng buộc — không từ sáo rỗng, không hứa ROI cụ thể, không đề cập giá. Kiểm tra — tự đánh giá theo 5 tiêu chí: cá nhân hoá, ngắn gọn, rõ giá trị, một CTA, không bị lọc spam.

**Tóm tắt cuộc họp:** Mục tiêu — tóm tắt cuộc họp 60 phút với khách hàng X về giải pháp ABC. Bối cảnh — discovery thứ 2. Dữ liệu — transcript đính kèm. Đầu ra — 1 trang chia 4 phần: quyết định, đầu việc kèm người và hạn, câu hỏi cần làm rõ, follow-up. Ràng buộc — chỉ dùng thông tin trong transcript, không bịa thêm. Kiểm tra — mỗi đầu việc có người chịu trách nhiệm và hạn chót cụ thể.

**Phân tích doanh thu Q3:** Mục tiêu — phân tích doanh thu Q3 2026 và đề xuất 3 hành động cho Q4. Bối cảnh — công ty SaaS B2B, doanh thu subscription, 3 segment. Dữ liệu — file revenue_q3.xlsx, báo cáo Q2. Đầu ra — báo cáo 2 trang. Ràng buộc — thiếu dữ liệu cho phân tích nào thì ghi rõ "thiếu dữ liệu" thay vì bịa. Kiểm tra — mỗi đề xuất có dự kiến tác động doanh thu và effort triển khai.

## Ba lỗi prompt phổ biến

**Lỗi 1 — Nói quá chung chung.** "Hãy giúp tôi viết một báo cáo về thị trường" — Claude không biết thị trường nào, đối tượng đọc là ai, độ dài bao nhiêu. Hệ quả: phải iterate 3–5 lần mới ổn. Cách sửa: thêm bốn lớp còn thiếu. Cùng prompt nhưng đủ sáu lớp: "Phân tích thị trường AI training cho doanh nghiệp Việt 2026. Đối tượng đọc là CEO. Dùng dữ liệu IDC và báo cáo nội bộ Q3. Đầu ra 3 trang chia phần market size, segment, competitive landscape. Không tổng hợp dài dòng — đi thẳng vào số."

**Lỗi 2 — Không chỉ rõ dữ liệu dùng.** "Phân tích doanh thu Q3" — Claude không biết doanh thu của ai, lấy ở đâu, đơn vị tiền nào. Hệ quả: phân tích trên dữ liệu giả định hoặc bịa số. Cách sửa: gắn file hoặc nêu rõ nguồn, kèm năm, đơn vị, scope. "Phân tích doanh thu Q3 2026 dựa trên file revenue_q3.xlsx, đơn vị triệu VND, scope toàn công ty không gồm subsidiary."

**Lỗi 3 — Không quy định đầu ra.** "Viết một bài blog về AI cho doanh nghiệp" — Claude tự chọn format, đôi khi là essay 1.500 từ trong khi bạn cần post LinkedIn 200 từ. Cách sửa: luôn nêu format, độ dài, tiêu chí đánh giá. "Viết LinkedIn post 200–280 từ về cách doanh nghiệp Việt nên bắt đầu với AI. Hook 1 câu, 3 ý chính, kết bằng câu hỏi tương tác."

> Một quan sát quan trọng: **prompt tốt không thay thế tư duy.** Nó giúp Claude bắt đầu đúng hướng ngay từ vòng đầu — tiết kiệm thời gian iterate. Nhưng bạn vẫn phải biết bạn muốn gì. Nếu bạn không biết bạn muốn gì, không prompt nào giải quyết được.

## Checklist 7 mục triển khai một use case Claude

1. **Bài toán rõ** — mô tả pain point và đầu ra mong muốn cụ thể. Không phải "chúng ta dùng AI cho marketing" mà là "giảm thời gian soạn weekly report của Marketing manager từ 90 phút xuống 15 phút".
2. **Owner rõ** — ai vận hành, ai duyệt đầu ra, ai quyết định khi có lỗi. Một người duy nhất, không phải uỷ ban.
3. **Dữ liệu sẵn** — tài liệu, file, dữ liệu cần thiết đã có; chưa có thì có kế hoạch chuẩn bị trước.
4. **Prompt hoặc skill rõ** — đã có công thức cụ thể, đã test trên 3 tình huống. Không phải "chúng ta sẽ dùng prompt phù hợp".
5. **Cách kiểm duyệt và review** — ai review, theo tiêu chí gì, tần suất ra sao. Không có review là không kiểm soát chất lượng.
6. **Đo lường** — thời gian xử lý, chất lượng đầu ra, tỷ lệ tái sử dụng.
7. **Lưu tri thức** — output tốt lưu vào CLAUDE OUTPUTS, bài học cập nhật vào CLAUDE.md hoặc skill.

Trình tự triển khai 7 ngày: chọn use case → tạo prompt hoặc skill → test với dữ liệu thật → tinh chỉnh → ban hành cho nhóm rộng hơn → đo ROI tuần đầu. Use case tốt là use case nhỏ nhưng đầu vào thật, lặp lại thật và đo được hiệu quả.

## Bảy thói quen của người dùng Claude xuất sắc

1. **Cho Claude biết bạn là ai và bối cảnh ngay từ đầu.** Người dùng trung bình gõ "viết email cho khách hàng X". Người dùng giỏi gõ: "Tôi là sales rep tại công ty SaaS B2B, viết email follow-up sau cuộc demo cho Giám đốc CNTT công ty bảo hiểm. Mục tiêu là chốt cuộc họp tiếp theo. Cuộc demo đã có 3 pain point được xác định."
2. **Nói rõ kết quả mong muốn** — định dạng cụ thể, độ dài, giọng điệu, mức chi tiết. Thiếu thông tin này, Claude tự chọn — và 30% thời gian sự lựa chọn không trùng với mong muốn của bạn.
3. **Đính kèm ví dụ tốt nếu có** — few-shot learning hoạt động: với một ví dụ Claude tốt hơn 30%, với ba ví dụ Claude tốt hơn 50%.
4. **Yêu cầu kế hoạch trước khi làm** — "Trước khi viết, hãy lập outline có 5 mục, tôi review rồi mới viết." Sửa kế hoạch dễ hơn sửa sản phẩm cuối.
5. **Cho Claude phản biện chính nó** — câu thần chú: "Hãy chỉ ra 3 điểm yếu của bản nháp." Một vòng phản biện tốt nâng chất lượng lên 1–2 bậc. Chuỗi power user: viết bản nháp → phản biện → viết lại → phản biện lần hai → finalize.
6. **Chia nhỏ thành nhiều bước** — đừng dồn 5 yêu cầu vào một lệnh. Chia nhỏ giúp dễ kiểm soát, dễ sửa sai, dễ tối ưu.
7. **Lưu prompt tốt thành Project hoặc Skill** — một prompt tốt dùng một lần là một prompt lãng phí. Một prompt tốt đóng gói thành skill là một tài sản tổ chức.

**Thông điệp chính của bảy thói quen:** chất lượng đầu ra đến từ thói quen làm việc, không chỉ từ model. Một người dùng có thói quen tốt với Claude đời cũ vẫn cho ra kết quả tốt hơn người dùng có thói quen kém với Claude đời mới.

## Memory đúng cách — Claude nhớ bạn là ai

Bộ nhớ Claude có ba lớp riêng biệt:

- **User Preferences** — thiết lập một lần, áp dụng vĩnh viễn: ngôn ngữ làm việc chính, giọng điệu mặc định, cách trình bày (markdown, không emoji), tiêu chuẩn đầu ra (luôn có khuyến nghị, luôn nêu giả định).
- **Memory tự động** — sau mỗi cuộc trò chuyện, Claude đề xuất ghi nhớ những điều ổn định về bạn và công việc; bạn xem qua và đồng ý từng điểm trước khi save.
- **Tham chiếu chat cũ** — yêu cầu Claude xem lại cuộc trò chuyện trước để tiếp nối ngữ cảnh; hữu ích cho project dài, deal nhiều tháng.

Bộ nhớ tốt giúp tiết kiệm 5–10 phút mỗi cuộc chat khi không phải lặp lại background. Ba mẹo: chỉ lưu những gì bạn đồng ý và có giá trị lâu dài (một memory sai sẽ ảnh hưởng mọi cuộc trò chuyện sau); không dùng memory chứa việc ngắn hạn (chỉ lưu những gì có giá trị trong 6–12 tháng tới); định kỳ rà soát và xoá memory không còn đúng (mỗi 3 tháng dành 15 phút review).

## Skillset và Toolset — bộ kỹ năng cần nắm

**Skillset gồm 5 kỹ năng cốt lõi:** viết yêu cầu rõ (mục tiêu, người nhận, đầu ra, tiêu chuẩn); cung cấp ngữ cảnh (tài liệu, ví dụ, giả định quan trọng); phản biện đầu ra (yêu cầu Claude tự kiểm tra điểm yếu); đóng gói tri thức (biến cách làm tốt thành project, skill, SOP); thiết kế workflow (ghép nhiều bước thành luồng lặp lại được).

**Toolset gồm 8 thành phần:** Claude Chat (hỏi đáp, phân tích nhanh), Projects (tổ chức công việc theo workstream), Artifacts (tạo và quản lý nội dung đầu ra), Skills (lưu tái sử dụng năng lực chuyên biệt), Connectors (kết nối nguồn dữ liệu), MCP (chuẩn kết nối mở), Cowork (không gian làm việc nhóm), Claude Code (viết, chạy và kiểm thử mã).

> Người giỏi dùng AI không chỉ biết hỏi — họ biết đóng gói tri thức và khuếch đại năng lực của chính mình. Skillset và Toolset không thay thế nhau — chúng **nhân lên nhau**: Skillset 8/10 cộng Toolset 8/10 không tạo giá trị cộng (16) mà tạo giá trị nhân (64).

## Bài tiếp theo trong series

- **Bài 6:** [Claude cho 8 phòng ban, tự động hoá quy trình và lộ trình 30 ngày](/bai-viet/claude-8-phong-ban-lo-trinh-30-ngay/)
- [Bài 1](/bai-viet/claude-doanh-nghiep-tu-duy-va-he-sinh-thai/) · [Bài 2](/bai-viet/claude-kienc-truc-7-tang-6-tai-san-tri-thuc/) · [Bài 3](/bai-viet/claude-claude-md-project-skills/) · [Bài 4](/bai-viet/claude-connectors-mcp-sub-agents/)
- Đọc thêm: [Cách viết prompt rõ ràng để AI hiểu đúng yêu cầu](/bai-viet/viet-prompt-ro-rang/)

## Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn xây dựng hệ thống AI Agent với Claude (CES Global 2026) — có biên tập lại cấu trúc theo phong cách LearnWithHuy. Các con số là kinh nghiệm chia sẻ trong tài liệu gốc, mang tính tham khảo.

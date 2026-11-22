---
title: "Connectors, MCP, Plugins và sub-agents: đưa Claude chạm vào hệ thống thật"
description: "Bài 4 series hệ thống AI Agent với Claude: hơn 50 connector có sẵn, chuẩn mở MCP, 6 plugin phòng ban, đội ngũ sub-agent 4 vai trò, và hooks tự động hoá trước-trong-sau tác vụ."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-17"
cover: "/images/covers/posts/claude-connectors-mcp-sub-agents.jpg"
views: 780
---

Khi đã có CLAUDE.md, Project và Skills ([bài 3](/bai-viet/claude-claude-md-project-skills/)), bước tiếp theo là cho Claude chạm vào dữ liệu và hệ thống thật của doanh nghiệp — tầng tạo bước nhảy lớn về giá trị. Bài này giải thích ba khái niệm thường bị nhầm lẫn (Connectors, MCP, Plugins) và tầng cao nhất (sub-agents, Cowork, Hooks).

## Connectors — Claude nói chuyện với mọi tool bạn đang dùng

Connector là gói kết nối có sẵn để Claude truy cập đúng ngữ cảnh làm việc của doanh nghiệp — email, file, lịch, ticket, task, dữ liệu vận hành. Anthropic và đối tác đã ship sẵn hơn 50 connector: Slack, Gmail, GitHub, Google Drive, Salesforce, Jira, Figma, Notion, Linear, ClickUp, HubSpot, Microsoft 365, Asana, Monday, Canva, Intercom...

Cách cài rất đơn giản: vào claude.com → /settings → Connectors, click 1-click cho công cụ cần. Sau xác thực OAuth, Claude có quyền đọc và (tuỳ cấu hình) ghi vào hệ thống đó. Cài một connector chỉ tốn 2–3 phút, nhưng tác động có thể toàn diện cho cách bạn làm việc.

**Bốn nhóm tình huống nên kết nối ngay từ tháng đầu:**

1. **Tìm tài liệu và tri thức nội bộ** — Drive, Notion, Confluence, SharePoint: Claude tự tìm và tham chiếu khi bạn hỏi, thay vì cả đội mất nhiều giờ tìm tài liệu cũ mỗi tuần.
2. **Lấy số liệu từ CRM hoặc hệ thống báo cáo** — Salesforce, HubSpot, Close: phân tích pipeline, dự báo doanh thu, xem khách sắp churn — Claude truy cập trực tiếp thay vì export rồi upload.
3. **Gửi email hoặc tạo ticket** — Gmail, Microsoft 365, Linear, Jira, ClickUp, Asana: nhóm "ghi dữ liệu" nên cẩn thận hơn (xem nguyên tắc an toàn dưới đây).
4. **Đồng bộ thông tin giữa nhiều công cụ** — Notion với Slack, Linear với GitHub, CRM với Email: Claude là "chất keo" giữa các công cụ rời rạc.

**Sáu nguyên tắc an toàn bắt buộc khi triển khai connectors:**

1. **Ưu tiên đọc trước, ghi sau** — bắt đầu chỉ với quyền đọc trong 2–4 tuần đầu.
2. **Tác vụ ghi dữ liệu phải có bước thử nghiệm và xác nhận** — không bao giờ để AI tự gửi email sản xuất hay update CRM mà không có review.
3. **Tách môi trường staging và production** — test trên staging trước, chỉ chuyển sang production khi đã ổn định.
4. **Chỉ cấp quyền tối thiểu cần thiết** — nếu skill chỉ cần đọc folder X trên Drive, đừng cấp quyền truy cập toàn Drive.
5. **Bắt đầu từ một use case rõ ROI rồi mới mở rộng** — không cài 10 connector cùng lúc "để cho có".
6. **Theo dõi log và trách nhiệm** — biết rõ ai cài connector, khi nào, dùng cho mục đích gì.

## MCP — chuẩn mở để AI nói với mọi tool

Model Context Protocol (MCP) là giao thức mở ra đời năm 2024 do Anthropic phát triển và đóng góp cho cộng đồng. Hình dung MCP như **USB-C của AI**: bạn viết một MCP server một lần, dùng được với Claude, ChatGPT, Cursor và nhiều ứng dụng AI khác.

**Bốn lý do MCP quan trọng:** Mở (đầu tư không bị mất nếu sau này dùng AI khác); Composable (ghép nhiều công cụ dễ dàng — 5 MCP server cho 5 hệ thống nội bộ, Claude chuyển qua lại tự nhiên); Dễ mở rộng cho hệ thống riêng (database nội bộ, API riêng, file system bảo mật cao); Chuẩn hoá (không phải mỗi AI một cách kết nối, một format khác nhau).

**Khác biệt với Connectors cần nắm:** Connector là gói có sẵn cho người dùng cuối — click cài, không cần code, phù hợp giai đoạn 0–3 tháng. MCP là chuẩn để developer tự mở rộng — cần engineer viết MCP server (thường 1–2 tuần cho server đầu tiên), mạnh nhất để mở rộng dài hạn, phù hợp giai đoạn 3–12 tháng.

> ⚠️ Sai lầm phổ biến: MCP không thay thế quy trình quản trị hiện có. Nó là cây cầu, không phải nhà máy. Doanh nghiệp tốt nhất dùng MCP để "AI hoá" 30–50% các bước trong quy trình, giữ con người làm các bước quyết định.

**Khi nào nên đầu tư xây MCP server riêng?** Ba dấu hiệu: đã dùng connector ổn định 3 tháng và thấy giới hạn (connector không truy cập được hệ thống nội bộ X); có ít nhất 3 use case sẽ dùng MCP server đó; có engineer có thể duy trì server dài hạn.

## Plugins — biến Claude thành chuyên gia phòng ban

Plugin là gói sub-agent đầy đủ cho một use case hoàn chỉnh — đóng gói tri thức + quy trình + kết nối. Khác với Connector (chỉ là kết nối) và MCP (chỉ là chuẩn giao tiếp), plugin là một "chuyên gia ảo" cho phòng ban có sẵn để cài và dùng.

Sáu plugin phổ biến đáng khám phá:

| Plugin | Khả năng đi kèm |
| --- | --- |
| **Brand Voice (Marketing)** | brand-voice-enforcement, discover-brand, generate-guidelines |
| **Sales** | account-research, call-prep, draft-outreach, pipeline-review, forecast, competitive-intelligence |
| **Legal** | triage-nda, review-contract, compliance-check, vendor-check, legal-risk-assessment |
| **HR** | comp-analysis, interview-prep, draft-offer, onboarding, performance-review, org-planning |
| **Finance** | reconciliation, variance-analysis, sox-testing, journal-entry-prep, financial-statements |
| **Customer Support** | ticket-triage, draft-response, kb-article, customer-research, customer-escalation |

Cách dùng: vào marketplace tại claude.com → /plugins. Doanh nghiệp lớn có thể tự host private marketplace — phù hợp khi tổ chức có yêu cầu tuân thủ cao (tài chính, y tế, pháp lý) hoặc có plugin nội bộ không muốn chia sẻ.

> Ba câu khẩu quyết để nhớ: **Connector = dùng sẵn. MCP = tự mở rộng. Plugin = triển khai use case hoàn chỉnh.** Doanh nghiệp Việt nên tận dụng plugin có sẵn trước, dùng connector cho dữ liệu, đầu tư MCP khi đã đủ trưởng thành. Đảo ngược thứ tự là tốn kém không cần thiết.

## Sub-agents — đội ngũ tác nhân chuyên biệt

Một AI duy nhất phải làm mọi việc thường gặp ba vấn đề: prompt rất dài và phức tạp dễ bị hiểu sai; không thể chạy song song (quy trình 4 bước mất 4 lần thời gian); khó kiểm soát chất lượng từng bước.

**Sub-agents giải quyết cả ba:** một orchestrator (điều phối viên) chia task lớn thành nhiều sub-task; mỗi sub-agent đảm nhận một vai trò chuyên biệt, có prompt riêng, kiểm tra riêng; chạy song song khi không phụ thuộc nhau; kết quả ghép lại bởi orchestrator và pass qua reviewer trước khi bàn giao.

**Bốn dấu hiệu nên dùng Cowork và sub-agents:** công việc nhiều bước (3+) và nhiều vai trò; cần song song hoá để nhanh hơn (4 bước tuần tự 60 phút → 20 phút); cần chuẩn hoá đầu ra trước khi bàn giao (pass QA tự động); công việc có sự bàn giao rõ ràng giữa người và AI (AI làm 80%, người duyệt 20% có giá trị cao).

**Bốn vai trò tác nhân phổ biến — đủ xử lý 80% quy trình doanh nghiệp:**

| Vai trò | Nhận | Trả lại |
| --- | --- | --- |
| **Research Agent** | Câu hỏi nghiên cứu | Tài liệu tổng hợp có nguồn rõ ràng — cần kết nối nhiều nguồn (web, internal docs, CRM) và biết phân biệt nguồn tin cậy |
| **Analyst Agent** | Dữ liệu (từ Research hoặc trực tiếp) | Insight có cấu trúc, có khuyến nghị — cần tính toán, vẽ biểu đồ, phân tích trend |
| **Execution Agent** | Brief từ Analyst Agent | Sản phẩm cuối: báo cáo, email, slide deck, proposal — cần biết template, tone, chuẩn đầu ra |
| **Reviewer Agent** | Sản phẩm cuối từ Execution Agent | Phản hồi và bản hiệu chỉnh — vai trò cuối cùng trước khi bàn giao cho người |

Quy trình điển hình: orchestrator nhận mục tiêu → phân vai → research, analyst, execution chạy song song hoặc tuần tự (tuỳ phụ thuộc) → reviewer kiểm tra → orchestrator tổng hợp và bàn giao. Toàn bộ mất từ 2 phút (task nhỏ) đến 30 phút (task lớn).

> Tip thực chiến: **đừng tạo nhiều tác nhân chỉ để cho đẹp.** Bắt đầu bằng một orchestrator cộng hai sub-agent (thường Research và Execution), mở rộng khi đã có ROI. Một quy trình với 5 sub-agent phức tạp thường thua một quy trình với 2 sub-agent rõ ràng.

## Hooks và Workflow — tự động hoá trước, trong, sau tác vụ

Hooks là các điểm kích hoạt tự động — chuyển Claude từ "phải gõ tay khởi động" sang "chạy theo lịch hoặc theo sự kiện".

**Vòng đời của một workflow tốt gồm 5 bước:** trigger hoặc sự kiện kích hoạt (lịch trình 8h sáng, hoặc event: PR opened, ticket created, email mới có label cụ thể) → Claude phân tích yêu cầu và chuẩn bị context → gọi công cụ và xử lý (kích hoạt skill, gọi connector, gọi sub-agents) → kiểm tra và xác nhận (QA tự động, escalate nếu cần) → bàn giao đầu ra qua kênh đã định (email, Slack, Notion, file). Mỗi bước có log để truy vết.

**Bốn loại hook phổ biến:**

| Loại | Chức năng | Ví dụ |
| --- | --- | --- |
| **PRE-TOOL** | Kiểm tra điều kiện trước khi chạy | Trước khi skill báo cáo tuần chạy, kiểm tra dữ liệu Slack đã đủ chưa — nếu chưa thì hỏi lại thay vì tạo báo cáo trên dữ liệu thiếu |
| **POST-TOOL** | Chuẩn hoá, kiểm tra hoặc gửi kết quả sau khi chạy | Sau khi viết proposal, kiểm tra đủ 3 phần (vấn đề, đề xuất, bước tiếp theo), pass anti-AI-style filter, save vào Drive với tên chuẩn |
| **ON-EDIT** | Kích hoạt khi file/dữ liệu thay đổi | Khi roadmap.md trên Notion được cập nhật, tự động kích hoạt skill thông báo stakeholder |
| **ON-NOTIFICATION** | Phản hồi khi có thông báo/yêu cầu mới | Khi Linear nhận issue mới label P1, kích hoạt skill triage và tag người phụ trách |

**Bốn use case nên triển khai sớm:** báo cáo định kỳ (daily brief 8h, weekly recap, monthly review); đồng bộ tài liệu/dữ liệu (PRD được duyệt → tự tạo task trong Linear; deal close-won → tự tạo onboarding ticket); kiểm tra chất lượng đầu ra (mỗi bài blog mới tự pass qua brand voice check); giao việc và nhắc việc tự động (ticket support quá 24h chưa response → tự reminder agent).

**Bốn nguyên tắc vàng cho hooks:** phải có trigger rõ (không có trigger mơ hồ "khi cần"); phải có bước kiểm tra (không tự động chạy kết thúc mà không có QA); phải có log (biết workflow chạy lúc nào, dùng gì, kết quả ra sao); phải có cơ chế dừng khẩn cấp (phát hiện anomaly nghiêm trọng → dừng workflow và escalate).

**Bốn việc đừng làm:** đừng tự động hoá khi chưa rõ quy trình thủ công (automation chuyện chưa rõ chỉ tạo rác nhanh hơn); đừng làm tự động hoá rủi ro mà không theo dõi (tự gửi email khách hàng mà không có human-in-the-loop); đừng nhồi quá nhiều bước vào một workflow (chia nhỏ để dễ debug); đừng quên rà soát workflow định kỳ.

> **Điểm cần nhớ:** hook tốt không thay thế tư duy quản trị. Nó giải phóng bạn khỏi việc thấp giá trị (gom dữ liệu, format) để tập trung vào việc cao giá trị (đánh giá, ra quyết định).

## Bài tiếp theo trong series

- **Bài 5:** [Prompt giao việc chuẩn 6 lớp và bộ kỹ năng người dùng giỏi](/bai-viet/prompt-giao-viec-6-lop-best-practices/)
- Bài 6: Claude cho 8 phòng ban, tự động hoá và lộ trình 30 ngày
- [Bài 1](/bai-viet/claude-doanh-nghiep-tu-duy-va-he-sinh-thai/) · [Bài 2](/bai-viet/claude-kienc-truc-7-tang-6-tai-san-tri-thuc/) · [Bài 3](/bai-viet/claude-claude-md-project-skills/)

## Nguồn

- Nội dung tổng hợp từ tài liệu hướng dẫn xây dựng hệ thống AI Agent với Claude (CES Global 2026) — có biên tập lại cấu trúc theo phong cách LearnWithHuy. Danh sách connector/plugin và số liệu theo tài liệu gốc, nên kiểm tra lại trên trang chính thức của Anthropic tại thời điểm đọc.

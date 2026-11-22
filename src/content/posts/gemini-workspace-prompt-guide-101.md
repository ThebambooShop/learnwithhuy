---
title: "Prompting Guide 101 cho Gemini for Workspace: bản dịch handbook Google (tháng 10/2024)"
description: "Bản dịch chi tiết Prompting Guide 101 của Google Workspace: khung 4 thành phần (Persona, Task, Context, Format), 6 mẹo viết prompt, kho prompt mẫu theo 11 vai trò từ admin đến startup leader, và 6 cách nâng cấp kỹ năng prompting."
topic: "prompt-engineering"
date: "2026-11-18"
cover: "/images/covers/posts/gemini-workspace-prompt-guide-101.jpg"
views: 560
faq:
  - q: "Khung 4 thành phần của prompt hiệu quả là gì?"
    a: "Theo Google: Persona (bạn là ai), Task (nhiệm vụ cần làm), Context (bối cảnh chi tiết), Format (định dạng đầu ra). Không cần dùng đủ cả 4 trong mọi prompt, nhưng dùng một vài sẽ giúp — và luôn nhớ đưa động từ hoặc mệnh lệnh vào Task vì đó là thành phần quan trọng nhất của một prompt."
  - q: "Prompt bao nhiêu từ là hiệu quả?"
    a: "Theo số liệu Google thu thập từ người dùng: những prompt hiệu quả nhất trung bình khoảng 21 từ kèm ngữ cảnh liên quan, trong khi prompt người dùng thường gõ chỉ dưới 9 từ. Thêm ngữ cảnh là chênh lệch quyết định chất lượng đầu ra."
  - q: "Cách dùng @file name trong Gemini for Workspace là gì?"
    a: "Trong Gmail, Docs, Sheets, Drive, Gemini có thể truy cập tệp của bạn trong Workspace. Gõ @tên-file trong prompt để gắn tài liệu riêng của bạn làm ngữ cảnh — ví dụ Use @[2024 H2 Team Vision] to generate a summary — giúp output cá nhân hóa theo dữ liệu thật thay vì đoán."
  - q: "Khi kết quả chưa ưng thì làm gì?"
    a: "Làm thành hội thoại: dùng follow-up prompt để tinh chỉnh (thêm ý, đổi format, nêu cụ thể điều muốn sửa). Google cũng khuyên với Gemini Advanced hãy mở đầu bằng 'Make this a power prompt: [prompt gốc]' để chính Gemini đề xuất cách cải thiện prompt của bạn."
---

Google Workspace được xây từ đầu để bạn cộng tác theo thời gian thực với người khác — giờ bạn có thể cộng tác với AI qua **Gemini for Google Workspace** để tăng productivity và sáng tạo mà không đánh đổi privacy hay security. Gemini nằm ngay trong các app bạn dùng hằng ngày — Gmail, Google Docs, Google Drive, Google Sheets, Google Meet, Google Slides — và **Gemini Advanced** (trải nghiệm chat độc lập tại gemini.google.com với bảo mật cấp doanh nghiệp). Bạn có thể tạo email cá nhân hóa trong vài giây tham chiếu Docs của mình, generate Slides dựa trên brief hoặc report riêng, và nhiều hơn nữa — ít chuyển tab, ít gián đoạn hơn.

Guide này (bản tháng 10/2024) cung cấp kỹ năng nền để viết prompt hiệu quả khi dùng Gemini for Workspace. Hãy coi một prompt là **câu mở đầu hội thoại** với trợ lý AI — bạn có thể viết nhiều prompt tiếp nối trong cuộc trò chuyện.

Gemini for Workspace có thể giúp bạn: cải thiện cách viết; tổ chức dữ liệu; tạo ảnh gốc; tóm tắt thông tin và khai insight; họp tốt hơn với ghi chú tự động; research chủ đề lạ dễ dàng; phát hiện xu hướng, tổng hợp thông tin và nhận diện cơ hội kinh doanh.

Về dữ liệu: nguyên tắc nền đá của Google — **dữ liệu của bạn là của bạn**, không thuộc về Google. Dữ liệu nằm trong môi trường Workspace của bạn, quyền riêng tư được bảo vệ, và nội dung của bạn **không bao giờ** được dùng để quảng cáo nhắm mục tiêu hay huấn luyện Gemini hay bất kỳ model sinh nào khác.

## Khung 4 thành phần của một prompt hiệu quả

| Thành phần | Là gì | Ví dụ |
| --- | --- | --- |
| **Persona** | Bạn là ai trong tình huống này | "You are a program manager in [industry]" |
| **Task** | Nhiệm vụ cụ thể cần AI làm — **luôn có động từ/mệnh lệnh** | "Draft an executive summary email" |
| **Context** | Chi tiết, dữ liệu, file liên quan | "based on [details about relevant program docs]" |
| **Format** | Hình dạng đầu ra mong muốn | "Limit to bullet points" |

Ví dụ một prompt dùng đủ cả 4 thành phần, chạy tốt trong Gmail và Google Docs:

```text
You are a program manager in [industry]. Draft an executive summary email
to [persona] based on [details about relevant program docs].
Limit to bullet points.
```

Bạn không cần dùng đủ cả 4 trong mọi prompt, nhưng dùng một vài sẽ giúp! Và luôn nhớ: **đưa động từ hoặc mệnh lệnh vào Task** — đây là thành phần quan trọng nhất của một prompt.

## Sáu mẹo nhanh để bắt đầu

1. **Dùng ngôn ngữ tự nhiên.** Viết như đang nói với một người khác — diễn đạt ý trọn vẹn trong câu đầy đủ.
2. **Cụ thể và lặp.** Nói rõ bạn cần Gemini làm gì (tóm tắt, viết, đổi giọng, tạo). Cung cấp càng nhiều ngữ cảnh càng tốt.
3. **Ngắn gọn, tránh phức tạp.** Nêu yêu cầu ngắn nhưng cụ thể. Tránh thuật ngữ khó hiểu.
4. **Biến nó thành hội thoại.** Tinh chỉnh prompt khi kết quả chưa đạt — dùng follow-up prompt và quy trình review–refine lặp để có kết quả tốt hơn.
5. **Dùng tài liệu của bạn.** Cá nhân hóa output với thông tin từ chính file của bạn trong Google Drive.
6. **Biến Gemini thành prompt editor.** Với Gemini Advanced, mở đầu prompt bằng: *"Make this a power prompt: [prompt gốc]."* — Gemini sẽ đề xuất cách cải thiện. Chỉnh cho đúng ý rồi dán lại để lấy output.

> **Con số đáng nhớ:** Prompting là kỹ năng ai cũng học được — bạn không cần là prompt engineer để dùng generative AI. Theo số liệu Google thu thập từ người dùng: **prompt hiệu quả nhất trung bình khoảng 21 từ** kèm ngữ cảnh liên quan, trong khi prompt người dùng thường gõ **dưới 9 từ**. Thêm ngữ cảnh là chênh lệch quyết định.

> ⚠️ Generative AI vẫn còn mới — dù model ngày càng tốt hơn, prompt đôi khi cho phản hồi không thể đoán trước. Trước khi đưa output của Gemini vào hành động, hãy review để bảo đảm rõ ràng, liên quan và chính xác. Và điều quan trọng nhất: **Generative AI được sinh ra để giúp con người, nhưng output cuối cùng thuộc về bạn.**

## Cách dùng thư viện prompt dưới đây

- **Dấu ngoặc [..]** đánh dấu chỗ bạn điền chi tiết riêng hoặc gắn file cá nhân bằng cách gõ `@tên-file`
- Một số prompt hiển thị không highlight để bạn thấy một prompt hoàn chỉnh trông thế nào
- Mọi prompt trong guide gốc đều **để lấy cảm hứng** — cuối cùng cần được tùy chỉnh theo công việc của bạn
- Mỗi vai trò có một **Prompt iteration example**: chuỗi prompt lặp cho thấy cách viết follow-up prompt để xây trên phản hồi đầu tiên

## Kho prompt theo vai trò

Guide gốc tổ chức prompt theo 11 vai trò — hơn 100 prompt. Dưới đây là bản dịch đầy đủ khung PTCF của mỗi vai trò (iteration example) và tuyển chọn prompt đại diện cho từng use case chính.

### 1. Administrative support — hỗ trợ hành chính

Bạn giữ mọi thứ được tổ chức và hiệu quả — kể cả khi áp lực, juggling nhiều ưu tiên cùng lúc.

**Iteration example — Use case: Lên agenda (offsite, họp...)** — bạn lên kế hoạch offsite 3 ngày:

```text
Bước 1: I am an executive administrator to a team director. [Context] Our newly
formed team now consists of content marketers, digital marketers, and product
marketers. We are gathering for the first time at a three-day offsite in
Washington, DC. Plan activities for each day that include team bonding
activities and time for deeper strategic work. Create a sample agenda for me.
(Gemini Advanced)

Bước 2 (follow-up): Suggest three different icebreaker activities that encourage
people to learn about their teammates' preferred working styles, strengths, and
goals. Make sure the icebreaker ideas are engaging and can be completed by a
group of 25 people in 30 minutes or less. (Gemini Advanced)

Bước 3 (follow-up): Organize this agenda in a table format. Include one of your
suggested icebreakers for each day. (Gemini Advanced)

Bước 4 (trong Docs, gắn file): Use @[2024 H2 Team Vision] to generate a summary
for the opening remarks on Day 1 of this agenda. (Gemini in Docs)
```

| Use case | Prompt |
| --- | --- |
| Quản nhiều hộp thư | Summarize emails from [manager] from the last week. *(Gmail)* |
| Tóm thread email | Summarize this email thread and list all action items and deadlines. *(Gmail)* |
| Soạn thư trả lời dùng file | Generate a response to this email and use @[file name] to describe how the [initiative] can complement the workstream outlined in [colleague's name]'s message. *(Gmail)* |
| Lập lịch công tác | I am an executive assistant. I need to create an itinerary for a two-day business trip in [location] during [dates]. My manager is staying at [hotel]. Suggest different options for breakfast and dinner within a 10-minute walk of the hotel, and find one entertainment option. Put it in a table for me. *(Gemini Advanced)* |
| Theo dõi ngân sách đi lại | Create a budget tracker for business travel. Columns for: date, expense type (meal, entertainment, transportation), vendor name, and a description. *(Sheets)* |

### 2. Communications — truyền thông

Bạn bảo đảm doanh nghiệp được hiểu đúng, cập nhật trend, giao tiếp hiệu quả với nhiều stakeholder và xây narrative thuyết phục.

**Iteration example — Use case: Viết thông cáo báo chí** — công ty vừa acquired một brand nhỏ, quotes CEO đã lưu trong Doc:

```text
Bước 1: I'm a PR manager. I need to create a press release with a catchy title.
Include quotes from @[VIP Quotes Acquisition]. (Gemini in Docs)

Bước 2 (follow-up): Use @[Biography and Mission Statement] to add more
information about the company that is being acquired, its mission, and how it
got started. (Gemini in Docs) → chọn Insert để đưa vào bản nháp
```

| Use case | Prompt |
| --- | --- |
| Chuẩn bị briefing báo chí | Generate a brief template to prepare [spokesperson] for an upcoming media and analyst briefing for @[Product Launch]. Include space for a synopsis, key messages, and supporting data. *(Docs)* |
| Synopsis sản phẩm | Craft a synopsis of the product launch in three main points using @[Product Launch - Notes]. *(Docs)* |
| Quản danh sách media | Organize my media and analyst contacts from @[Analyst and Journalist Contact Notes] for a new product briefing. Track: names, type of contact, focus area, outlet, agency, and priority level (low, medium, high). *(Sheets)* |
| Slide giới thiệu | Create a slide describing what [product] is from @[Product Launch - Notes]. Make sure it is short and easily understood by a broad audience. *(Slides)* |
| Mock interview cho phát ngôn viên | I am a [PR/AR] manager at [company name]. We just launched [product]. Generate a list of mock interview questions to help [spokesperson] prepare. Include a mixture of easy and hard questions. *(Gemini Advanced)* |
| Memo nội bộ | I need to draft a company-wide memo unveiling our relaunched intranet. The [new page] addresses [common feedback]. Draft an upbeat memo announcing [the new site] using @[Intranet Launch Plan Notes]. *(Docs)* |

### 3. Customer service — chăm sóc khách hàng

**Iteration example — Use case: Soạn thư trả lời khách hàng** — khách nhận tai nghe bị hỏng:

```text
Bước 1: Help me craft an empathetic email response. I am a customer service
representative. The customer ordered a pair of headphones that arrived damaged.
They've already contacted us via email and provided pictures of the damage.
I've offered a replacement, but they're requesting an expedited shipping option
that isn't typically included with their order. Include a paragraph that
acknowledges their frustration and three bullet points with potential
resolutions. (Gemini in Docs)

Bước 2 (follow-up): Suggest 10 alternative options in place of expedited
shipping to resolve the customer's frustration about receiving the damaged
package. (Gemini in Docs)
```

| Use case | Prompt |
| --- | --- |
| Trả lời câu hỏi phức tạp | Summarize information about [product name] including the product's specific [return policy], [ingredients], and [certifications]. *(Drive)* → Generate a response to the customer question about our [return policy] and [product certifications] based on @[Customer FAQ Document]. Use a helpful and professional tone. *(Gmail)* |
| Chuẩn hóa template | Draft templates for three different types of customer communication: apology emails, order confirmation messages, and thank you notes for loyal customers. Keep each template to one paragraph and use a friendly tone. *(Docs)* |
| Best practices cho team mới | Craft a list of customer communication best practices to train new team members. Outline three sections: happy, neutral, and dissatisfied customer inquiries. *(Docs)* |
| Ngôn ngữ điện thoại chuẩn hóa | I am a [customer service manager]. Generate templates for common call openings, greetings, and closures for a customer service representative at a retail store. Templates should allow personalization with customer details. *(Gemini Advanced)* |
| Phối hợp liên phòng ban | Draft an email to my colleagues proposing a meeting to discuss customer experience improvement initiatives. Request that marketing, sales, and product stakeholders meet in the next week. *(Gmail)* |
| Phân tích feedback | Using the attached spreadsheet, identify trends and patterns in our [customer feedback] by [category] over [time period]. Investigate potential reasons. *(Gemini Advanced)* |
| Self-service | Summarize this content to write a clear and concise product return policy and outline 5 steps for customers in sequential order. *(Docs)* |
| Khảo sát sau cuộc gọi | Create five different questions for customers who have just spoken to an agent on the phone. Gauge how effective the call was, if the concern was addressed, and if they would recommend us. *(Docs)* |

### 4. Executives — lãnh đạo

Thời gian của bạn cực kỳ giới hạn — mọi quyết định đều tác động đến tăng trưởng và quỹ đạo doanh nghiệp.

**Iteration example — Use case: Giao tiếp khi đang đi** — sắp lên chuyến bay dài, vừa nhận thư mời họp board:

```text
Bước 1: Draft an email confirming that I will be at the board meeting. Ask if
we can adjust the agenda to give 15 minutes to [urgent topics]. (Gemini in Gmail)

Bước 2: Refine → Formalize (đổi giọng văn trang trọng nhất)
→ Insert, chỉnh nhẹ câu cảm ơn đội ngũ trước khi gửi.
```

| Use case | Prompt |
| --- | --- |
| CEO — bắt kịp email dài | Generate a response to [person] about [topic]. Include details on [deliverable] and [timeline] using @[Project A Status Report]. *(Gmail)* |
| CEO — outline thuyết trình bằng giọng nói | I'm the CEO giving a presentation to [audience] at [event]. Create a detailed outline including [areas of focus], how our company is innovating with [company initiatives], and time for a customer Q&A with suggested questions from the [industry] industry. *(Gemini Advanced)* |
| COO — phát biểu town hall | Write two uplifting paragraphs for employees who have just finished a challenging quarter. Acknowledge [difficulties] and emphasize [positives]. Tone: motivating, optimistic, fosters unity. *(Docs)* |
| COO — tập trả lời câu hỏi khó | I'm the COO of a mid-sized company hosting a quarterly town hall. Help me write challenging questions employees may ask about [URL of company announcement] and generate potential answers with a confident but firm tone. *(Gemini Advanced)* |
| CMO — nghiên cứu thị trường | I'm a marketing leader conducting analysis in preparation for next year's [launch]. Define my target audiences [audiences] for my new line of [product]. Include interests, relevant marketing channels, and top trends driving consideration and purchase behavior. *(Gemini Advanced)* |
| CMO — phân tích đối thủ | I am a CMO conducting a competitive analysis. My company is considering expanding into [a new line of business]. Generate the top five competitors in the [industry] industry with their pricing, strengths, weaknesses, and target audience. *(Gemini Advanced)* |
| CTO — tổng hợp tech trends | I am the CTO of [company] in [industry]. Summarize the top five emerging technologies with the most significant potential impact on [industry]. For each: potential benefits, challenges, and how it could impact [company] in the next two to three years. *(Gemini Advanced)* |
| CIO — nói chuyện kỹ thuật cho người không kỹ thuật | I am the CIO at [company], trying to build the case to [adopt generative AI solutions]. Help me write talking points conveying what generative AI is, ways it could help us digitally transform, and why it matters to our growth. *(Gemini Advanced)* |
| CIO — theo dõi license | Create a tracker of software licenses for employees with columns for license types, usage rights, and renewal dates. *(Sheets)* |
| CHRO — khảo sát hài lòng | Draft an anonymous employee satisfaction survey with questions touching upon workload, work-life balance, compensation, and career growth. Ensure questions are clear, concise, and avoid leading answers. *(Docs)* |

### 5. Frontline management — quản lý tuyến đầu

Đội của bạn có thể không làm việc chủ yếu trên máy tính, nhưng giao tiếp và cộng tác vẫn là chìa khóa.

**Iteration example — Use case: Tìm thông tin nhanh** — khách hỏi về chương trình sale đang chạy:

```text
Bước 1: Find the document that details the [company name]'s [holiday] sale
details. (Gemini in Drive)

Bước 2 (mở Doc gợi ý): How much can customers save on [product type] during
this sale? (Gemini in Docs)
```

| Use case | Prompt |
| --- | --- |
| Tìm policy mới | Find the document that discusses our new return and exchange policies. *(Drive)* → Write an email to my new colleagues summarizing @[Updated Return and Exchange Policy H2 2024]. *(Gmail)* |
| Checklist ca làm | I am a retail manager. Create a checklist for my opening and closing duties. Create a template with columns for [opening and closing duties] from @[Onboarding New Hire Information]. *(Sheets)* |
| Bàn giao việc còn lại | Write an email to the team telling them what still needs to be done from the AM shift from @[Opening and Closing Duties Tracker]. *(Gmail)* |
| Kiểm kho | How many [units] of [product] do we have left in our inventory? *(Sheets)* |
| Công thức đối chiếu audit | Create a formula that helps me calculate the difference between two columns. Which items have a discrepancy in [the total number counted] versus [the quantity on hand]? *(Sheets)* |

### 6. Human resources — nhân sự

Bạn là xương sống tổ chức, xử lý lượng lớn thông tin nhạy cảm, định hình văn hóa và trải nghiệm nhân viên.

**Iteration example — Use case: Welcome nhân viên mới** — viết kịch bản thuyết trình onboarding:

```text
Bước 1: I am an HR manager, and I am developing a script for my presentation
for new hires. Help me draft talking points that showcase why employee
mentorship and development are core values for our company using
@[Mission Statement and Core Values]. (Gemini in Docs)

Bước 2 (follow-up): Add four talking points for a new section that explains how
we support our employees' development. Mention our training and certification
programs and mentorship opportunities using @[Learning and Development Paths],
and write a strong closing statement. Use a professional tone. (Gemini in Docs)
```

| Use case | Prompt |
| --- | --- |
| Metrics tuyển dụng | Help me create a formula to calculate the total number of [hires] by [department]. *(Sheets)* → In what month did we hire the most people? *(Sheets)* |
| Mô tả vị trí mới | I am opening a new job position on the marketing team. Write a compelling role description for a content marketing manager. Highlight key responsibilities [insert] and requirements, including B2B and B2C content creation, a minimum of five years experience, and a portfolio. *(Docs)* |
| Câu hỏi phỏng vấn | I am a recruiter preparing for candidate interviews. Using the job description in the file I'm uploading, write a list of 20 open-ended interview questions to screen candidates. *(Gemini Advanced)* |
| Offer + rejection letter | Create a template for an offer letter for the [selected candidate] for the [position]... *(Docs)* → Help me write a rejection letter for [candidate] for the [position]. Use an empathetic tone. *(Docs)* |
| Dọn dữ liệu khảo sát | Help me clean my employee survey spreadsheet. Fill any blank values in the name column with "Anonymous," replace "Headquarters" with "HQ," remove rows where the satisfaction column is blank. Generate a new file with my cleaned data. *(Gemini Advanced)* |
| Lộ trình học cá nhân hóa | Create a personalized learning and development plan for a new hire who needs to learn about [topic]. Organize it by day and suggest relevant files. *(Drive)* |
| Lịch tuần đầu của nhân viên mới | Create a table outlining a new employee's first-week schedule, including key meetings, training sessions, and introductions. Provide a column for key contacts and priority level. *(Sheets)* |
| Team bonding | Design a team-bonding activity, such as an office scavenger hunt, to have team members work together during their team meeting. *(Docs)* |

### 7. Marketing

Bạn là lực lượng sáng tạo đằng sau campaign, brand experience, lead generation — hiểu sức mạnh data-driven insights và kết nối với audience ở tầng sâu hơn.

**Iteration example — Use case: Phát triển visual identity** — khách sắp mở quán cà phê kết hợp game cafe:

```text
Bước 1: Generate ideas for a creative and eye-catching logo for my new business,
a coffee shop combined with a video game cafe. Generate a logo considering the
following:
- Dual Concept: The logo needs to clearly signal both the coffee and gaming
  aspects without being too cluttered.
- Target Audience: Appeal to a wide range of gamers (casual and enthusiast), as
  well as coffee lovers seeking a unique hangout spot.
- Style Options: let's get a few examples in each of these three styles to
  compare: Modern and Playful / Retro-Cool / Sleek and Minimalist.
(Gemini Advanced)

Bước 2 (follow-up): I like the retro-cool options. Can you provide three more
in that same style? (Gemini Advanced)

Bước 3 (follow-up): Write a tagline and 10 potential names for the business to
go with these logos. (Gemini Advanced)
```

| Use case | Prompt |
| --- | --- |
| Kiến trúc thương hiệu | I am a brand manager at [company]. Help me define a clear and effective brand architecture considering its diverse products and service portfolio. Current portfolio: [list]. Mission and vision: [overview]. Target audience(s): [describe]. Desired positioning: [explain]. *(Gemini Advanced)* |
| Tìm brand partner | Identify potential types of influencers and complementary brands that [company] could partner with to amplify the [campaign] on social media channels. *(Gemini Advanced)* |
| A/B test thông điệp | I need to A/B test new messaging. Here is our messaging: [messaging]. Generate three different variations of ad copy. *(Gemini Advanced)* |
| Content cá nhân hóa quy mô lớn | Create a 5-step nurture email cadence to [prospective customers] who have signed up for [our newsletter], with the goal of getting them to [purchase] [product] using @[Product Specific Notes] and @[Product FAQ]. *(Docs)* |
| Hình ảnh campaign | Help me create inspirational images for a marketing campaign for [type of product]. Images should use [colors] and [natural elements]. Use a [photorealistic] style. *(Slides)* |
| Ý tưởng blog du lịch | Suggest blog post topics interesting for people passionate about travel. Make topics unique, fresh angles that stand out. Each topic should include: Target audience, Content outline, and Call to action. *(Gemini Advanced)* |
| SEM keywords | I am a digital marketing manager working on SEM ads for [product]. Here are my seed keywords: [list keywords]. Help me generate additional keywords and long-tail keywords that can maximize ad performance. *(Gemini Advanced)* |
| Kế hoạch marketing chiến lược | I'm developing a marketing plan for a new app that provides [functionality]. Target audience is [audience]. Cover: competitor analysis, ideal channel mix with rationale, budget recommendations, key messaging ideas, and campaign timeline with KPIs. *(Gemini Advanced)* |
| Ghi chú họp Meet | Take notes with Gemini *(Meet)* → Generate a project tracker using the action items from @[Meeting Notes from Gemini]. *(Sheets)* |

> 💡 Mẹo từ guide: khi nghiên cứu social trend, dùng nút **Double-check response** bên dưới câu trả lời của Gemini để xác minh.

### 8. Project management — quản lý dự án

Bạn là nhạc trưởng của dự án phức tạp liên tục thay đổi — điều phối timeline, teams và bảo đảm chương trình đạt tác động như kỳ vọng.

**Iteration example — Use case: Tạo user acceptance tests** — form đăng ký vừa hoàn thành:

```text
Bước 1: Create a table with 10 user acceptance tests (UAT) for the website
registration form. (Gemini Advanced)

Bước 2 (follow-up): Draft an email to [my colleague] who is running this UAT
and explain what they need to do next. (Gemini Advanced)
```

| Use case | Prompt |
| --- | --- |
| Báo cáo trạng thái từ transcript | Summarize this call transcript in a short paragraph. In bullet points, highlight action items, decisions made, and owners based off of [call transcript]. *(Docs)* |
| Template update trạng thái | Draft a project status update email template to send to my manager. Include sections for a summary of key accomplishments, challenges faced, and the top three priorities for next week. *(Docs)* |
| Project retrospective | I need to write a report detailing successes, failures, and lessons learned from [project]. Draft a list of 20 questions to guide a cross-team process investigation. *(Docs)* |
| Issue tracker | Create a spreadsheet to track project issues, including descriptions, status, assigned owner, and action items for resolution. *(Sheets)* |
| Email escalate | Draft an email template to a stakeholder to escalate a critical project issue, outlining the impact and proposed solution. *(Docs)* |
| Workback schedule | I am a [technical project manager] at [company] overseeing [project]. Scope: [scope]. Goals: [project goals]. Deliverables: [project deliverables]. Budget: [budget]. Delivery date: [delivery date]. Help me create a workback schedule to keep the team on track. Include dates for key milestones and demos. *(Gemini Advanced)* |

### 9. Sales — bán hàng

Hiểu khách hàng từ trong ra ngoài là vé vào cửa thành công: giữ quan hệ then chốt, đọc tín hiệu mua, thiết kế giải pháp riêng và driving revenue.

**Iteration example — Use case: Nghiên cứu khách hàng mới** — vừa được assign một khách hàng mới:

```text
Bước 1: Write an email to [name], the new [title] at [company]. Congratulate
them on their new role. Introduce me as their contact point at [company name].
Invite them to lunch next week and check if they prefer Monday or Tuesday.
(Gemini in Gmail) → Refine → Formalize

Bước 2: I am an account executive in charge of a new account, [customer name].
What is the market strategy of [customer]? (Gemini Advanced)

Bước 3: [URLs] Summarize these articles. Provide key insights and contextualize
why these announcements are important. (Gemini Advanced)

Bước 4: [YouTube URL] Summarize this interview and tell me more about
[executive name]. What does [executive] care about? (Gemini Advanced)

Bước 5: Create an email draft for [customer] explaining why [your company] is
the perfect partner for them to achieve their market goals. (Gemini in Docs)
```

| Use case | Prompt |
| --- | --- |
| Onboarding materials riêng | Create personalized onboarding materials for [customer]. Use @[Standard Onboarding Documents] and @[New Customer Migration Notes] to personalize. *(Docs)* |
| Nghiên cứu RFP | I just received an RFP from [company]. Give me a business profile including all of the basics (location, offerings, target audience, recent news). *(Gemini Advanced)* → [URL or uploaded file] Summarize this RFP. What is the customer seeking, what is the budget, and when is a response due? *(Gemini Advanced)* |
| Script sales call | Draft a customized script for my sales call with a prospect. 30-minute video call. Include: how [company products] address pain points, delivery system guarantees, competitive pricing and volume-discount table, and space for a customer reference in the [customer's industry]. *(Gemini Advanced)* |
| Elevator pitch | Generate an elevator pitch for [product name] and include key benefits, competitive points of differentiation, and the pain points [product name] solves for. *(Docs)* |
| Dự đoán objections | List the most likely objections [customer] might have during a sales call, with suggestions on how to respond. I work in [industry], and I am trying to sell [product]. *(Gemini Advanced)* |
| Follow-up sau sự kiện | Draft an email thanking customers for their time at the happy hour on [date, time, location]. End with an invitation to continue the conversations in the next few weeks. Use a friendly tone. *(Gmail)* |
| Sales materials cá nhân hóa từ transcript | I am an [account manager] and I just finished a call with [customer]. Summarize the [pain points] mentioned by [customer]. Provide direct quotes from @[Customer Call Transcript] where [customer] discusses what they are trying to solve. *(Docs)* |
| Đền bù khách hàng | Draft an email to all Southeast region sales leads. Inform them of [issues]. Advise them to contact their customers and offer a 20% discount on a future order as an apology. *(Gmail)* |

### 10. Small business owners — chủ doanh nghiệp nhỏ

Bạn juggling nhiều vai trò — hiểu thị trường, phục vụ khách và cân nhiều ưu tiên cạnh nhau cùng lúc.

**Iteration example — Use case: So sánh báo giá** — đánh giá 2 công ty vệ sinh cho spa:

```text
I'm a business owner and I'm trying to determine the right cleaning vendor using
@[Company A Proposal] and @[Company B Proposal]. I need someone to come twice a
week, and I want them to vacuum, mop, dust, clean the windows, and wipe down all
surfaces. If available, include information about the booking and cancellation
policy. Create a comparison table between the two companies' proposals.
(Gemini in Docs)
```

| Use case | Prompt |
| --- | --- |
| Nội dung marketing đa kênh | I own a [type of business] in [location]. I am working on marketing materials to advertise [event/sale] on [services]. Suggest some social copy with relevant hashtags, suggested newsletter copy, and two email drafts (one for existing customers, one for new). *(Gemini Advanced)* |
| Phân tích cạnh tranh | I am an online business owner considering opening a brick-and-mortar store. Conduct an analysis into the competitive landscape focusing on [focus area]. Identify actionable insights for how [my company] can gain a competitive advantage. *(Gemini Advanced)* |
| Huy động nhà đầu tư | Draft a personalized email template to potential investors, highlighting [company's] unique value proposition and recent progress on [initiatives]. *(Docs)* |
| Chính sách nghỉ phép dễ hiểu | Generate a step-by-step checklist summarizing the company's time-off request policy. Ensure it is written in plain language. *(Docs)* |
| Bảng xếp ca | Create a table that tracks weekly staffing. Columns for date, name, shift (AM or PM), and notes. *(Sheets)* |

### 11. Startup leaders — lãnh đạo startup

Bạn đeo nhiều mũ, driven bởi passion cho innovation — không chỉ thực thi tác vụ mà đang dựng cái gì đó từ con số 0.

**Iteration example — Use case: Brainstorm chiến lược** — vừa brainstorm xong, notes nằm trên whiteboard:

```text
Bước 1: I am a founder at a startup focused on [industry]. I was brainstorming
with colleagues about [topic], and we took notes on this whiteboard. Turn these
notes into text. (Gemini Advanced — chụp ảnh whiteboard upload lên)

Bước 2 (follow-up): Suggest follow-up items we could discuss for our [topic of
brainstorm session]. What was not covered that could have been, and what are we
potentially missing? (Gemini Advanced)

Bước 3: Use @[Brainstorm Notes and Ideas 9/1/24] to write a meeting recap to
the team using an upbeat and friendly tone. (Gemini in Gmail)
```

| Use case | Prompt |
| --- | --- |
| Elevator pitch bằng giọng nói | I'm the founder of [startup] in [industry]. Create a short elevator pitch for [company and product description]. Highlight [key features] because I want them to [take this action]. Include a compelling hook and anticipate investor questions. Professional but relaxed and confident tone. *(Gemini Advanced)* |
| Xây personal brand | Help me grow my personal brand. I am the founder of [a startup] in [industry]. I am passionate about [topics]. My goals are to build a following so that I can [generate more media] for the business. *(Gemini Advanced)* |
| Đàm phán vendor | I need to make a vendor decision for packaging manufacturing. Create a table comparing the two proposals @[Company A's Proposal] and @[Company B's Proposal]. *(Docs)* |
| Phân tích chi tiêu 3 năm | Using the attached spreadsheet, identify trends and patterns in our expenses by category over the last three years. Identify areas where costs have increased significantly and investigate potential reasons. *(Gemini Advanced)* |
| Kịch bản ra mắt sản phẩm | We are building a product launch plan for [product]. We are considering two price points [A and B] and launching in [December or January]. Provide pros and cons of each scenario and suggest ideas we may not have considered. *(Gemini Advanced)* |
| Roadmap từ user feedback | Help me clean my [user feedback] survey spreadsheet... *(Gemini Advanced)* → I am head of product. We are adding [features] to address recurring user feedback, including [feedback trends]. Build a high-level roadmap for a Q4 delivery. Put it in a table format. *(Gemini Advanced)* |

## Nâng cấp kỹ năng prompting — 6 cách

| Cách | Cụ thể |
| --- | --- |
| **Break it up** | Muốn Gemini làm nhiều tác vụ liên quan? Tách thành các prompt riêng biệt |
| **Give constraints** | Để có kết quả cụ thể, thêm chi tiết: giới hạn số ký tự, số lượng lựa chọn muốn nhận |
| **Assign a role** | Khuyến khích sáng tạo bằng cách giao vai trò: "You are the head of a creative department for a leading advertising agency…" |
| **Ask for feedback** | Nói với Gemini rằng bạn đang giao một dự án, đưa đủ chi tiết rồi mô tả output mong muốn. Tiếp tục hội thoại bằng câu hỏi như: *"What questions do you have for me that would help you provide the best output?"* |
| **Consider tone** | Đo ni đóng giày theo audience: yêu cầu output có tone cụ thể — formal, informal, technical, creative hoặc casual |
| **Say it another way** | Kết quả chưa đạt? Viết lại prompt theo cách khác — quy trình review và tinh chỉnh lặp thường cho kết quả tốt hơn |

> ⚠️ Nhắc lại nguyên tắc quan trọng nhất của guide: trước khi đưa output của Gemini vào hành động, **review để bảo đảm rõ ràng, liên quan và chính xác**. Generative AI được sinh ra để giúp con người — nhưng **output cuối cùng là của bạn**.

## So với khung prompt 6 lớp trên blog này

Guide của Google dạy khung **4 thành phần cho cuộc hội thoại hàng ngày trong Workspace** (Persona–Task–Context–Format) — tối ưu cho người dùng cá nhân làm việc nhanh trong app. Nếu bạn cần giao việc phức tạp, có hệ thống hơn cho Claude hoặc các agent, đọc thêm [cấu trúc prompt 6 lớp](/bai-viet/prompt-giao-viec-6-lop-best-practices/) (thêm Data, Constraints và Validation) và [cách viết prompt rõ ràng](/bai-viet/viet-prompt-ro-rang/). Hai khung không mâu thuẫn — một cái cho tốc độ hằng ngày, một cái cho tác vụ quan trọng.

## Nguồn

- Bản gốc: Google Workspace — *Gemini for Workspace Prompting Guide 101, October 2024 edition* (workspace.google.com). Bản dịch chi tiết có biên tập lại cấu trúc theo phong cách LearnWithHuy; prompt giữ nguyên tiếng Anh để dùng trực tiếp, phần chú thích bằng tiếng Việt.
- Khám phá tính năng: g.co/gemini/features
- Prompt gốc của guide mang tính minh họa — cần tùy chỉnh theo công việc cụ thể của bạn.

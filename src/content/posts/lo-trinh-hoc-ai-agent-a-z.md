---
title: "Lộ trình học AI Agent từ A đến Z: 47 tài nguyên cho người mới bắt đầu"
description: "Lộ trình học AI Agent đầy đủ nhất 2026: 47 tài nguyên chọn lọc gồm 8 video, 10 repo GitHub, 5 tài liệu chính thức, 7 sách, 4 bài nghiên cứu và 13 khóa học — xếp theo thứ tự học cho người mới, kèm hướng dẫn bắt đầu."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-17"
cover: "/images/covers/posts/lo-trinh-hoc-ai-agent-a-z.jpg"
featured: true
views: 1750
faq:
  - q: "Học AI Agent có cần biết lập trình không?"
    a: "Không bắt buộc để bắt đầu. Nhóm Video và tài liệu chính thức (Google/Anthropic/OpenAI) đọc hiểu được mà không cần code. Tuy nhiên để đi sâu vào repo GitHub và sách (xây agent bằng Python), bạn cần Python cơ bản — có thể học song song theo <a href='/bai-viet/bat-dau-hoc-lap-trinh-cung-ai/'>lộ trình học lập trình cùng AI</a>."
  - q: "Nên bắt đầu học AI Agent từ đâu?"
    a: "Từ nhóm Video nhập môn (số 1–8) và repo Microsoft AI Agents for Beginners (số 10) — đây là tài liệu được thiết kế riêng cho người mới. Sau đó chuyển sang ba whitepaper chính thức của Google, Anthropic và OpenAI để có khung tư duy chuẩn."
  - q: "Học trọn lộ trình này mất bao lâu?"
    a: "Tùy nền tảng và thời gian mỗi ngày. Với mức 5–7 giờ/tuần: khoảng 2–3 tháng cho phần nhập môn + thực hành, 4–6 tháng để bao trọn 47 tài nguyên. Quan trọng hơn tốc độ là chạy được sản phẩm thật ở mỗi giai đoạn — giống tinh thần <a href='/bai-viet/lo-trinh-vibe-coding-6-thang/'>lộ trình Vibe Coding 6 tháng</a>."
  - q: "Bao nhiêu tài nguyên trong lộ trình là miễn phí?"
    a: "Phần lớn: 8 video, 10 repo GitHub, 5 tài liệu chính thức và 4 papers đều miễn phí (tổng 27/39 — nhóm 8 chứng chỉ Coursera từ số 40 có học phí theo gói). Sách là phần trả phí (một số có bản đọc thử miễn phí), khóa học Datapot trả phí."
---

AI Agent đang là chủ đề nóng nhất của kỹ thuật AI hiện nay — nhưng tài liệu về nó nằm rải rác khắp nơi: video YouTube, repo GitHub, whitepaper của Google và Anthropic, sách chuyên sâu, bài nghiên cứu trên arXiv. Người mới dễ lạc giữa "biển tài nguyên" mà không biết bắt đầu từ đâu.

Bài này tổng hợp thành **một lộ trình học AI Agent từ A đến Z gồm 47 tài nguyên**, sắp xếp theo 6 nhóm và thứ tự học hợp lý: từ khái niệm nhập môn (video) → thực hành (GitHub) → tài liệu chính thức → nền tảng chuyên sâu (sách) → nghiên cứu gốc (papers) → khóa học hệ thống. Bạn có thể dùng nó như checklist: học xong cái nào, tick cái đó — đúng tinh thần "từng bước một" của blog này.

Nếu chưa rõ AI Agent là gì, hãy đọc nhanh [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te/) hoặc [LLM hoạt động như thế nào?](/bai-viet/llm-hoat-dong-nhu-the-nao/) trước khi bắt đầu lộ trình này.

## Tổng quan lộ trình

| Nhóm tài liệu | Số lượng |
| --- | --- |
| 🎬 Video | 8 |
| 💻 GitHub | 10 |
| 📘 Tài liệu hướng dẫn chính thức | 5 |
| 📚 Sách | 7 |
| 🔬 Bài nghiên cứu | 4 |
| 🎓 Khóa học | 13 (5 Datapot + 8 Coursera) |
| **Tổng cộng** | **47** |

## 🎬 Video — nhập môn khái niệm (bắt đầu từ đây)

Tám video để hiểu mô hình ngôn ngữ lớn và AI Agent bằng hình ảnh, không đòi hỏi nền tảng lập trình:

| # | Video | Nội dung |
| --- | --- | --- |
| 1 | [LLM Introduction](https://www.youtube.com/watch?v=zjkBMFhNj_g) | Giới thiệu về mô hình ngôn ngữ lớn (LLM) |
| 2 | [LLMs from Scratch](https://www.youtube.com/watch?v=9vM4p9NN0Ts) | Tìm hiểu cách xây dựng LLM từ đầu |
| 3 | [Agentic AI Overview (Stanford)](https://www.youtube.com/watch?v=kJLiOGle3Lw) | Tổng quan về AI Agent từ Stanford |
| 4 | [Building & Evaluating Agents](https://www.youtube.com/watch?v=d5EltXhbcfA) | Xây dựng và đánh giá AI Agent |
| 5 | [Building Effective Agents](https://www.youtube.com/watch?v=D7_ipDqhtwk) | Cách xây dựng AI Agent hiệu quả |
| 6 | [Building Agents with MCP](https://www.youtube.com/watch?v=kQmXtrmQ5Zg) | Xây dựng AI Agent với MCP |
| 7 | [Building an Agent from Scratch](https://www.youtube.com/watch?v=xzXdLRUyjUg) | Tự xây dựng một AI Agent từ đầu |
| 8 | [Philo Agents](https://www.youtube.com/playlist?list=PLacQJwuclt_sV-tfZmpT1Ov6jldHl30NR) | Chuỗi video tìm hiểu về AI Agent |

## 💻 GitHub — thực hành với tài nguyên cộng đồng

Mười repo GitHub chất lượng cao — nơi học bằng code và ví dụ thực tế:

| # | Repo | Nội dung |
| --- | --- | --- |
| 9 | [GenAI Agents](https://github.com/NirDiamant/GenAI_Agents) | Tài nguyên thực hành và bộ sưu tập ví dụ xây dựng AI Agent |
| 10 | [Microsoft AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) | Tài liệu nhập môn AI Agent dành cho người mới |
| 11 | [Prompt Engineering Guide](https://github.com/NirDiamant/Prompt_Engineering) | Hướng dẫn kỹ thuật viết và tối ưu prompt |
| 12 | [Hands-On Large Language Models](https://github.com/HandsOnLLM/Hands-On-Large-Language-Models) | Học về LLM thông qua thực hành |
| 13 | [Made with ML](https://github.com/GokuMohandas/MadeWithML) | Thực hành xây dựng và triển khai hệ thống Machine Learning |
| 14 | [Agents Towards Production](https://github.com/NirDiamant/agents-towards-production) | Tài nguyên thực hành kỹ thuật AI từ prototype đến production |
| 15 | [Awesome Generative AI Guide](https://github.com/aishwaryanr/awesome-generative-ai-guide) | Bộ sưu tập tài nguyên về Generative AI |
| 16 | [Designing Machine Learning Systems](https://github.com/chiphuyen/machine-learning-systems-design) | Tài liệu về thiết kế hệ thống Machine Learning |
| 17 | [Machine Learning for Beginners](https://github.com/microsoft/ML-For-Beginners) | Tài liệu nhập môn Machine Learning |
| 18 | [LLM Course](https://github.com/mlabonne/llm-course) | Lộ trình học về mô hình ngôn ngữ lớn |

## 📘 Tài liệu hướng dẫn chính thức — đọc từ các nhà phát triển

| # | Tài liệu | Nội dung |
| --- | --- | --- |
| 19 | [Google's Agent Whitepaper](https://www.kaggle.com/whitepaper-agent) | Tài liệu chuyên sâu của Google về AI Agent |
| 20 | [Google's Agent Companion](https://www.kaggle.com/whitepaper-agent-companion) | Tài liệu bổ trợ giúp hiểu rõ hơn về AI Agent |
| 21 | [Building Effective Agents by Anthropic](https://www.anthropic.com/engineering/building-effective-agents) | Hướng dẫn xây dựng AI Agent hiệu quả từ Anthropic |
| 22 | [Claude Code Agentic Coding Practices](https://code.claude.com/docs/en/best-practices) | Phương pháp lập trình theo hướng AI Agent với Claude Code |
| 23 | [OpenAI's Practical Guide to Building Agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf) | Hướng dẫn thực tiễn của OpenAI về xây dựng AI Agent |

> 💡 Ba tài liệu chính thức của Google, Anthropic và OpenAI (số 19–23) là phần "cốt lõi" của lộ trình — chúng đã được đội ngũ các phòng lab chắt lọc thành thực hành tốt nhất từ hàng trăm triển khai thực tế. Bài [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te/) trên blog chính là bản đọc nhanh của tài liệu số 23.

## 📚 Sách — nền tảng chuyên sâu

| # | Sách | Nội dung |
| --- | --- | --- |
| 24 | [Understanding Deep Learning](https://udlbook.github.io/udlbook/) | Hiểu sâu về Deep Learning |
| 25 | [Build a Large Language Model (From Scratch)](https://www.manning.com/books/build-a-large-language-model-from-scratch) | Xây dựng mô hình ngôn ngữ lớn từ đầu |
| 26 | The LLM Engineering Handbook | Cẩm nang kỹ thuật xây dựng ứng dụng LLM — tìm trên [O'Reilly](https://www.oreilly.com/library/search/?q=LLM+Engineering+Handbook) |
| 27 | AI Agents: The Definitive Guide | Hướng dẫn toàn diện về AI Agent — tìm trên [O'Reilly](https://www.oreilly.com/library/search/?q=AI+Agents+The+Definitive+Guide) |
| 28 | Building Applications with AI Agents | Xây dựng ứng dụng với AI Agent — tìm trên [O'Reilly](https://www.oreilly.com/library/search/?q=Building+Applications+with+AI+Agents) |
| 29 | AI Agents with MCP | Xây dựng AI Agent với MCP — tìm trên [O'Reilly](https://www.oreilly.com/library/search/?q=AI+Agents+with+MCP) |
| 30 | AI Engineering | Kỹ thuật xây dựng và triển khai ứng dụng AI — tìm trên [O'Reilly](https://www.oreilly.com/library/search/?q=AI+Engineering+Chip+Huyen) |

## 🔬 Bài nghiên cứu — hiểu gốc rễ

Bốn bài nghiên cứu nền tảng của lĩnh vực AI Agent, tất cả đều miễn phí trên arXiv:

| # | Paper | Nội dung |
| --- | --- | --- |
| 31 | [ReAct](https://arxiv.org/abs/2210.03629) | Phương pháp kết hợp suy luận và hành động trong AI |
| 32 | [Generative Agents](https://arxiv.org/abs/2304.03442) | Tác nhân mô phỏng hành vi và tương tác xã hội |
| 33 | [Toolformer](https://arxiv.org/abs/2302.04761) | Mô hình ngôn ngữ tự học cách sử dụng công cụ |
| 34 | [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903) | Kỹ thuật prompting theo chuỗi suy luận |

## 🎓 Khóa học — hệ thống hóa kỹ năng dữ liệu

Năm khóa học của Datapot (datapot.edu.vn) — nhà đào tạo dữ liệu tại Việt Nam, đi kèm lộ trình Data Analyst:

| # | Khóa học | Nội dung |
| --- | --- | --- |
| 35 | Data Analytics Foundation Plus | Lộ trình Data Analyst từ cơ bản đến nâng cao: SQL, Power BI, Python, Azure (116 giờ) |
| 36 | Combo SQL: From Zero to Job-Ready | Truy vấn dữ liệu với T-SQL từ cơ bản đến nâng cao, theo giáo trình Microsoft |
| 37 | Agentic AI for Data Analytics | Ứng dụng AI Agent vào toàn bộ quy trình phân tích dữ liệu và Power BI |
| 38 | Power BI từ cơ bản đến nâng cao | PL-300 và Power BI Advanced Data Modeling & Visualization |
| 39 | Power Platform: Power Automate, Power Apps & Power BI | Tự động hóa quy trình, xây ứng dụng không cần code và trực quan hóa dữ liệu |

### Bổ sung: 8 chứng chỉ Coursera cho nền tảng dữ liệu

Nhóm chứng chỉ quốc tế từ Coursera — lựa chọn khi bạn muốn lộ trình có chứng chỉ được công nhận rộng:

| # | Khóa học | Nội dung |
| --- | --- | --- |
| 40 | [Meta Data Analyst Professional Certificate](https://www.coursera.org/professional-certificates/meta-data-analyst) | Chứng chỉ chuyên nghiệp về phân tích dữ liệu của Meta |
| 41 | [Google Advanced Data Analytics](https://www.coursera.org/professional-certificates/google-advanced-data-analytics) | Chứng chỉ phân tích dữ liệu nâng cao của Google |
| 42 | [Microsoft Power BI Data Analyst](https://www.coursera.org/professional-certificates/microsoft-power-bi-data-analyst) | Chứng chỉ phân tích dữ liệu với Power BI |
| 43 | [Google Data Analytics](https://www.coursera.org/professional-certificates/google-data-analytics) | Chứng chỉ phân tích dữ liệu của Google |
| 44 | [Introduction to Data Analytics](https://www.coursera.org/learn/introduction-to-data-analytics) | Nhập môn phân tích dữ liệu |
| 45 | [Machine Learning Specialization](https://www.coursera.org/specializations/machine-learning-introduction) | Chương trình chuyên sâu Machine Learning |
| 46 | [IBM Deep Learning với PyTorch, Keras và TensorFlow](https://www.coursera.org/professional-certificates/ibm-deep-learning-with-pytorch-keras-tensorflow) | Chứng chỉ Deep Learning của IBM |
| 47 | [Deep Learning Specialization](https://www.coursera.org/specializations/deep-learning) | Chương trình chuyên sâu Deep Learning |

> ⚠️ Tại thời điểm bài viết được xuất bản, website datapot.edu.vn không truy cập được (domain không resolve) — hãy kiểm tra lại trực tiếp hoặc tìm tên khóa học trên mạng trước khi đăng ký.

## Gợi ý thứ tự học

Lộ trình 47 tài nguyên không cần học theo đúng số thứ tự — gợi ý chia giai đoạn:

1. **Giai đoạn nhập môn (1–2 tuần):** nhóm Video (số 1–8) để nắm khái niệm LLM và AI Agent.
2. **Giai đoạn thực hành (3–6 tuần):** repo nhập môn (số 10, 17, 18) rồi các repo thực hành Agent (số 9, 11, 14).
3. **Giai đoạn nền tảng chính thống (song song):** ba tài liệu chính thức Google/Anthropic/OpenAI (số 19–23).
4. **Giai đoạn chuyên sâu (1–3 tháng):** sách (số 24–30) và papers (số 31–34) khi muốn hiểu gốc rễ.
5. **Giai đoạn hệ thống hóa (tùy chọn):** khóa học (số 35–47) nếu cần lộ trình có người dẫn và chứng chỉ.

## Bài liên quan trên LearnWithHuy

- [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te/) — bản đọc nhanh của guide OpenAI trong lộ trình này
- [9Router và Hermes Agent: 2 công cụ AI mà dev nào cũng nên biết](/bai-viet/9router-va-hermes-agent/) — hạ tầng và agent thực thi thực tế
- [Series OpenClaw (6 bài)](/bai-viet/openclaw-la-gi/) — nếu bạn muốn chạy Agent tự động hóa trên máy của mình
- [Lộ trình Vibe Coding 6 tháng](/bai-viet/lo-trinh-vibe-coding-6-thang/) — lộ trình xây sản phẩm bằng AI cho người kinh doanh

## Nguồn

- Danh sách 39 tài nguyên tổng hợp từ bộ "Roadmap AI Agent" — có biên tập lại cấu trúc, xác minh lại từng liên kết và viết thêm hướng dẫn thứ tự học theo phong cách LearnWithHuy.
- Các liên kết đã được kiểm tra trạng thái truy cập tại thời điểm xuất bản; video YouTube là link tìm kiếm vì tài liệu gốc không chỉ định video cụ thể.

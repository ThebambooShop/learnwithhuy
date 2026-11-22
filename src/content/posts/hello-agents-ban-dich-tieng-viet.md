---
title: "Hello-Agents bản tiếng Việt: bộ sách 16 chương tự học AI Agent từ con số 0"
description: "Bản dịch tiếng Việt trọn vẹn của Hello-Agents — giáo trình 87.000 sao nổi tiếng nhất về xây dựng AI Agent. Có lộ trình học 3 cấp, sơ đồ trực quan hóa, quiz tự kiểm tra và tải file Word miễn phí."
topic: "generative-ai-llm"
date: "2026-11-20"
cover: "/images/covers/posts/hello-agents-ban-dich-tieng-viet.jpg"
featured: true
views: 0
draft: false
faq:
  - q: "Cuốn Hello-Agents này dành cho ai?"
    a: "Người biết Python cơ bản và hiểu khái niệm LLM ở mức gọi API. Không cần nền tảng machine learning sâu — sách tập trung vào ứng dụng và xây dựng."
  - q: "Bản dịch tiếng Việt có mất phí không?"
    a: "Không. Cả bản gốc (CC BY-NC-SA 4.0) lẫn bản dịch đều miễn phí. Bạn tải file Word đầy đủ 16 chương kèm sơ đồ ở cuối bài này."
  - q: "Nên bắt đầu từ chương nào?"
    a: "Nếu mới bắt đầu: Chương 1–3 để hiểu Agent là gì. Nếu đã làm việc với LLM API: nhảy thẳng Chương 4 (ReAct) rồi Chương 7 (tự xây framework)."
  - q: "Code trong sách giữ tiếng Anh hay đã dịch?"
    a: "Toàn bộ mã nguồn giữ nguyên bản gốc để chạy đúng tài liệu tham chiếu. Chỉ phần diễn giải mới được dịch sang tiếng Việt."
---

Nếu năm 2024 là "năm của trăm mô hình" thì 2025–2026 là năm của **Agent**. Vấn đề là: tài liệu học agent bằng tiếng Việt gần như không có, còn tài liệu tốt bằng tiếng Anh/Trung thì nằm rải rác. Mình đã dịch trọn vẹn **Hello-Agents** — giáo trình được cộng đồng Datawhale biên soạn, hiện **87.000+ sao GitHub** (nằm trong top những dự án AI nhiều sao nhất) — thành một bộ sách tiếng Việt hoàn chỉnh 16 chương, kèm sơ đồ trực quan hóa do mình vẽ thêm.

> **Tóm tắt nhanh:** Bộ sách miễn phí, ~1.300 trang bản dịch, học bằng code thực hành. Có 3 lộ trình theo trình độ. Tải Word ở cuối bài.

## Sau bài này bạn sẽ

- Chọn được **lộ trình học phù hợp** với trình độ hiện tại của mình
- Hiểu **bản đồ 5 phần / 16 chương** của giáo trình và thứ tự nên đọc
- Nắm **12 thuật ngữ nền tảng** xuất hiện xuyên suốt cuốn sách
- Biết cách học sao cho **chạy được code ngay lần đầu**

## Hello-Agents là gì?

Hello-Agents là dự án mã nguồn mở của Datawhale (cộng đồng học dữ liệu/AI lớn nhất Trung Quốc), tên gốc là *"从零开始构建智能体"* — xây dựng hệ thống Agent từ con số 0. Điểm khác biệt so với tài liệu khác: nó **không dạy dùng framework có sẵn, mà dẫn bạn tự viết framework agent từ đầu** bằng OpenAI API thuần — để bạn hiểu tận gốc vòng lặp agent vận hành thế nào.

Cấu trúc gồm 5 phần, 16 chương, mỗi chương đều có mã nguồn chạy được trong repo gốc:

![](/images/posts/hello-agents/d01_book_map.png)

* Bản đồ 5 phần của cuốn sách và 3 lộ trình học — click tải sách để xem bản full ở trang "Cách dùng cuốn sách"

## Ba lộ trình học — chọn đúng cái cho bạn

Đừng đọc tuần tự cả 1.300 trang. Hãy chọn lộ trình theo mục tiêu:

| Lộ trình | Dành cho ai | Chương nên đọc | Thời gian ước tính |
|---|---|---|---|
| 🌱 **Nền tảng** | Người mới tiếp cận AI Agent | Chương 1–3 | ~2 tuần, 1 giờ/ngày |
| 🛠️ **Builder** | Developer muốn tự tay xây agent | Chương 4–7, sau đó 8–10 | ~1 tháng, 2 giờ/ngày |
| 🚀 **Nâng cao** | Đã làm việc với agent, muốn tối ưu | Chương 9–12, chọn lọc 13–15 | ~3 tuần, 2 giờ/ngày |

Mọi lộ trình đều kết thúc ở **Chương 16 — Đồ án tốt nghiệp**: tự xây một ứng dụng multi-agent hoàn chỉnh và đưa lên open-source. Hoàn thành được đồ án này là bạn đã đủ nền tảng làm sản phẩm agent thực tế.

## 12 thuật ngữ nền tảng của cuốn sách

| Thuật ngữ | Nghĩa | Xuất hiện chính ở |
|---|---|---|
| **Agent** | Thực thể cảm nhận môi trường → suy luận → hành động để đạt mục tiêu | Chương 1 |
| **LLM** | Mô hình ngôn ngữ lớn — "bộ não" của agent | Chương 3 |
| **ReAct** | Vòng lặp Suy nghĩ → Gọi tool → Quan sát kết quả | Chương 4 |
| **Plan-and-Solve** | Chia bài toán thành các bước rồi lần lượt thực hiện | Chương 4 |
| **Reflection** | Agent tự xem lại kết quả của chính mình để sửa lỗi | Chương 4 |
| **Low-code** | Xây agent bằng kéo–thả (Coze, Dify, n8n) | Chương 5 |
| **Framework** | Bộ khung code có sẵn (LangGraph, AutoGen...) | Chương 6 |
| **RAG** | Truy hồi kiến thức từ kho tài liệu riêng trước khi trả lời | Chương 8 |
| **Memory** | Bộ nhớ ngắn hạn/dài hạn của agent | Chương 8 |
| **Context Engineering** | Đưa đúng thông tin vào cửa sổ context hữu hạn của LLM | Chương 9 |
| **MCP** | Giao thức mở chuẩn hóa kết nối Agent ↔ công cụ ("USB-C của AI") | Chương 10 |
| **Agentic RL** | Dạy agent bằng phần thưởng từ tương tác thật (GRPO) | Chương 11 |

Để hình dung cách sách trình bày một concept, đây là sơ đồ ReAct (Chương 4) — một trong những sơ đồ mình vẽ thêm cho bản dịch:

![ReAct: Thought → Action → Observation](/images/posts/hello-agents/d05_react.png)

Và pipeline RAG (Chương 8) — concept quan trọng nhất khi làm agent có kiến thức riêng:

![Pipeline RAG](/images/posts/hello-agents/d09_rag.png)

Trong file Word, mỗi chương đều có sơ đồ dạng này ở đúng vị trí liên quan (tổng cộng 12 sơ đồ mới kèm chú thích "bổ sung của người dịch" để phân biệt với hình gốc).

## 5 nguyên tắc để học bộ sách này hiệu quả

1. **Chạy code trước khi đọc tiếp.** Sách thiết kế theo nguyên tắc "học bằng tay". Repo gốc `datawhalechina/hello-agents` có đủ code từng chương trong thư mục `code/`.
2. **Đọc mở đầu mỗi chương trước khi quyết định đọc sâu.** Mỗi chương đều nêu mục tiêu ngay đầu — dùng nó để quyết định đọc lướt hay đọc kỹ.
3. **Không hiểu thuật ngữ thì quay lại bảng trên.** Các thuật ngữ trong sách giữ tiếng Anh (đã kèm nghĩa Việt lần đầu xuất hiện) — đây là chuẩn đặt tên mà tài liệu quốc tế đều dùng.
4. **Học đến Chương 7 thì dừng "đọc", chuyển sang "sửa".** Thử sửa code framework của chương 7: thêm 1 tool mới, đổi logic retry... Sửa hỏng rồi fix lại là lúc bạn hiểu thật.
5. **Chương 16 là bài kiểm tra.** Tránh "đọc xong 15 chương rồi chưa làm đồ án" — đó là bẫy phổ biến nhất của self-learning.

## Kiểm tra nhanh: bạn đã sẵn sàng chưa?

Trả lời 5 câu sau — nếu đúng ≥ 4, bạn có thể bắt đầu Builder path ngay:

<details>
<summary><b>Câu 1:</b> Agent khác chatbot thông thường ở điểm nào?</summary>

Chatbot chỉ sinh text từ prompt. Agent có <b>vòng lặp</b>: cảm nhận môi trường → suy luận → <b>thực thi hành động thật</b> (gọi API, chạy code) → quan sát kết quả → lặp lại cho đến khi đạt mục tiêu.
</details>

<details>
<summary><b>Câu 2:</b> Ba bước của vòng lặp ReAct là gì?</summary>

<b>Thought</b> (suy nghĩ về bước tiếp theo) → <b>Action</b> (gọi tool) → <b>Observation</b> (nhận kết quả từ môi trường). Observation được nối vào context rồi lặp lại.
</details>

<details>
<summary><b>Câu 3:</b> RAG giải quyết 3 giới hạn nào của LLM?</summary>

(1) Kiến thức riêng tư/công ty không có trong dữ liệu huấn luyện, (2) kiến thức bị đóng băng theo thời điểm huấn luyện, (3) giảm hallucination bằng cách neo câu trả lời vào tài liệu thật.
</details>

<details>
<summary><b>Câu 4:</b> MCP giải quyết bài toán N×M như thế nào?</summary>

Trước MCP: mỗi ứng dụng AI × mỗi nguồn dữ liệu cần một tích hợp riêng. MCP chuẩn hóa thành giao thức chung — mỗi bên chỉ cần 1 connector, giảm từ N×M xuống N+M.
</details>

<details>
<summary><b>Câu 5:</b> Tại sao Agentic RL (GRPO) mạnh hơn SFT thuần?</summary>

SFT chỉ học theo ví dụ có sẵn (bị chặn ở mức dữ liệu). Agentic RL để agent <b>tương tác thật</b> với môi trường, nhận phần thưởng từ kết quả — từ đó khám phá hành vi mà không ai chỉ trước.
</details>

## Tải bộ sách

- 📥 **[Tải file Word bản tiếng Việt (16 chương + 12 sơ đồ, ~56MB)](/downloads/hello-agents-tieng-viet.docx)**
- 🔗 **[Repo gốc Hello-Agents (mã nguồn từng chương)](https://github.com/datawhalechina/hello-agents)**
- 📄 Bản gốc phát hành theo CC BY-NC-SA 4.0 — dùng học tập, phi thương mại.

## Tiếp theo trên LearnWithHuy

Bộ sách này là "giáo trình". Trong các bài tiếp theo, mình sẽ làm chuỗi **thực hành rút gọn**: mỗi bài một chương trọng tâm (ReAct, RAG, MCP, Context Engineering) với code chạy được và ví dụ closer cho công việc thực tế. Nếu bạn muốn được thông báo, hãy đăng ký newsletter ở cuối trang này.

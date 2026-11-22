---
title: "AI chấm bài và đánh giá tự động: dùng được đến đâu, an toàn thế nào"
description: "AI chấm bài đạt độ chính xác nào trong nghiên cứu 2024–2026, cách chấm theo rubric với prompt mẫu, đánh giá thích ứng GMOCAT/BOBCAT, và 3 nguyên tắc dùng an toàn trong lớp học."
topic: "ai-trong-giao-duc"
date: "2026-11-22"
cover: "/images/covers/posts/ai-cham-diem-danh-gia-tu-dong.jpg"
views: 0
faq:
  - q: "AI chấm bài chính xác bao nhiêu phần trăm?"
    a: "Với rubric rõ ràng và bài gõ chữ, các nghiên cứu cho kết quả tương đồng cao với chấm của người (benchmark chấm bài viết tay Toán đại học ICML 2026 chỉ sai lệch nhỏ). Nhưng với bài viết tay khó đọc hoặc rubric mơ hồ thì sai số tăng nhanh — nên AI chấm sơ bộ, giáo viên duyệt."
  - q: "Dùng AI chấm có lộ dữ liệu học sinh không?"
    a: "Có thể. Luôn ẩn danh trước khi dán vào AI công cộng: bỏ tên, lớp, trường. Nếu dùng trong hệ thống trường, ưu tiên công cụ có hợp đồng bảo mật dữ liệu."
  - q: "AI có thay được phần chấm thi tốt nghiệp không?"
    a: "Không. AI phù hợp với chấm thường xuyên (bài tập, tiểu luận nội bộ) để phản hồi nhanh; thi chính thức cần quy trình chấm có pháp lý của người."
---

Chấm bài là việc AI đã chạm ngưỡng **dùng được hàng ngày** — nhưng chỉ khi hiểu đúng giới hạn của nó. Bài này dựa trên các nghiên cứu chấm tự động trong giai đoạn 2024–2026: từ chấm bài viết tay Toán đại học (ICML 2026) đến chấm tiểu luận theo rubric (PsyScore, ACL 2026).

## Mức chính xác thực tế: đủ dùng cho phản hồi, chưa đủ cho quyết định

Ba nghiên cứu đáng nhớ trong danh mục:

| Nghiên cứu | Việc gì | Kết quả |
| --- | --- | --- |
| [EduMARS](https://aclanthology.org/2026.findings-acl.466/) (ACL 2026) | Chấm bài làm bằng rubric + vision model, dùng cho bài tự luận K-12 | Khớp chấm của giáo viên ở mức cao khi rubric rõ |
| Chấm bài viết tay Toán ĐH ([ICML 2026](https://openreview.net/forum?id=vcdsMrNGqP)) | Benchmark lớn chấm chữ viết tay | AI đạt chất lượng chấp nhận được, nhưng chữ khó đọc là nguồn sai chính |
| [LLMs as MOOC graders](https://arxiv.org/abs/2402.03776) (2024) | Chấm mở rộng quy mô hàng nghìn bài | Chấm nhanh hàng loạt, sai lệch tập trung ở bài độ khó trung bình |

Đọc kỹ cả ba nghiên cứu sẽ thấy cùng một mẫu hình: **rubric rõ → AI gần giáo viên; rubric mơ hồ → AI đoán mò**. Nói cách khác, AI chấm tốt hay tệ phần lớn do *người đưa tiêu chí chấm*, không phải do AI.

## Cách chấm theo rubric với prompt (dùng ngay)

Mẫu dưới đây cài nguyên tắc từ EduMARS/PsyScore: chấm theo tiêu chí từng mục, mỗi điểm số kèm dẫn chứng từ bài, và phản hồi cho học sinh:

```text
Bạn là giáo viên chấm bài theo rubric. Chấm bài làm dưới đây.

RUBRIC (thang 10):
- 4 điểm: [tiêu chí 1 — mô tả rõ mức đạt]
- 3 điểm: [tiêu chí 2]
- 2 điểm: [tiêu chí 3]
- 1 điểm: trình bày

YÊU CẦU:
1. Chấm từng tiêu chí một, mỗi tiêu chí trích dẫn câu trong bài làm làm dẫn chứng.
2. Tổng điểm + nhận xét 3 câu theo cấu trúc: điểm mạnh → lỗi chính → việc làm tiếp theo.
3. Nếu không đọc được phần nào của bài, ghi rõ "KHÔNG ĐỌC ĐƯỢC" — KHÔNG đoán điểm.
4. Bài làm (đã ẩn tên, lớp): [DÁN BÀI]
```

Quy tắc 3 là quan trọng nhất: các benchmark chấm bài viết tay cho thấy phần lớn sai số đến từ **AI đoán thay vì nói không đọc được**. Buộc nó khai nhận giúp bạn biết bài nào cần chấm tay.

Ba việc nên làm kèm: (1) ẩn danh bài làm trước khi dán; (2) thử chấm 10 bài AI + đối chiếu tay để biết độ lệch của lớp mình; (3) luôn duyệt trước khi nhập điểm.

## Đánh giá thích ứng: chấm thông minh hơn là chấm nhiều

Một hướng khác trong danh mục là **adaptive testing** — đề thi tự điều chỉnh theo năng lực: trả lời đúng thì câu sau khó hơn, sai thì dễ hơn, nhờ vậy 20 câu đo được như 60 câu. [GMOCAT (KDD 2023)](https://arxiv.org/abs/2305.10473) và [BOBCAT (IJCAI 2021)](https://arxiv.org/abs/2106.03354) là hai hệ chuẩn. Điểm lấy được cho giáo viên thường: **quizzing ngắn với số câu ít nhưng chọn câu theo kết quả vừa làm** cho thông tin chẩn đoán hơn nhiều so với đề dài ngẫu nhiên.

## Ba nguyên tắc an toàn

1. **AI chấm sơ bộ + phản hồi; người chấm điểm chính thức.** Đặc biệt với điểm ảnh hưởng xếp loại.
2. **Ẩn danh dữ liệu trước khi đưa lên AI công cộng** — tên, lớp, chữ ký, hình học sinh.
3. **Không dùng AI làm "máy phát bài gian lận AI"** — các công cụ phát hiện AI-text có tỷ lệ báo sai cao với người viết không bản xứ; dùng phản hồi chất lượng bài làm là đủ.

Nguồn: các entry Assessment/Grading trong [Awesome AI-LLM4Education](https://github.com/GeminiLight/awesome-ai-llm4education).

Bài tiếp theo giải thích mảnh ghép khiến hệ thống trên chạy được lâu dài: [**AI biết người học đang ở đâu? — Knowledge tracing**](/bai-viet/ai-biet-nguoi-hoc-dang-o-dau/)

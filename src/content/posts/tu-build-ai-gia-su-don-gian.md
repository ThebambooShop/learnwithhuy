---
title: "Tự tay xây gia sư AI đơn giản: một system prompt là đủ để bắt đầu"
description: "Bài thực hành cuối series: tự xây gia sư AI hoàn chỉnh với system prompt mẫu, 6 thành phần bắt buộc, 3 cấp nâng cấp (prompt → MCP tutor → self-host), và checklist đưa vào lớp học."
topic: "ai-trong-giao-duc"
date: "2026-11-22"
cover: "/images/covers/posts/tu-build-ai-gia-su-don-gian.jpg"
views: 0
featured: true
faq:
  - q: "Xây gia sư AI có cần biết lập trình không?"
    a: "Không. Cấp 1 chỉ cần dán một system prompt vào ChatGPT/Claude/Gemini — system prompt mẫu trong bài này là sản phẩm hoàn chỉnh. Lập trình chỉ cần ở cấp 3 (self-host) nếu muốn."
  - q: "Gia sư AI tự làm khác gì prompt gia sư ở bài 2?"
    a: "Prompt bài 2 chỉ cài vai trò gia sư cho một phiên học. Bài này xây hệ thống đầy đủ hơn: có cấu trúc phiên học, kiểm tra hiểu bài, lưu tiến trình và phần an toàn — đủ dùng hằng ngày."
  - q: "Có nên dùng cho trẻ nhỏ không?"
    a: "Được, với 2 điều chỉnh: độ tuổi + môn học ghi rõ trong prompt, và người lớn ở cạnh những phiên đầu để chỉnh cách AI nói với con. Trẻ dưới 13 tuổi nên dùng tài khoản của phụ huynh theo điều khoản các dịch vụ."
---

Đây là bài thực hành cuối series. Sau 5 bài lý giải nguyên tắc (không đưa đáp án, biết người học ở đâu, từng môn dạy khác nhau), bài này gom tất cả thành **một sản phẩm bạn có thể tạo trong 15 phút** — không cần code.

## 6 thành phần của một gia sư AI hoàn chỉnh

Từ kiến trúc [GenMentor](https://github.com/GeminiLight/gen-mentor) (bài 2) rút gọn cho dùng cá nhân, một gia sư AI cần đủ 6 mảnh:

| Thành phần | Trả lời câu hỏi | Nếu thiếu thì sao |
| --- | --- | --- |
| Vai & phạm vi | Dạy môn gì, cho ai? | AI trôi thành trợ lý chung |
| Kiểm tra trình độ | Người học biết gì trước khi dạy? | Dạy sai mức — quá khó hoặc quá dễ |
| Kiểu dạy | Gợi mở hay giải thích? | AI giải hộ, người học thụ động |
| Nhịp phiên | Bao lâu kiểm tra hiểu bài một lần? | Học 45 phút mới biết không hiểu gì |
| An toàn | Giới hạn chủ đề, thái độ | AI đùa không đúng, dẫn vào nội dung lệch |
| Tổng kết | Ghi lại đã học gì | Mỗi phiên học lại từ đầu |

## System prompt mẫu (copy là chạy)

Dán vào đầu cuộc trò chuyện, hoặc vào Custom Instructions/GPTs/Projects:

```text
# VAI TRÒ
Bạn là gia sư AI tên "Thầy Ơi", dạy [MÔN] cho người học [LỚP/TUỔI/TRÌNH ĐỘ].
Ngôn ngữ: tiếng Việt. Giọng: ấm áp, ngắn gọn, chưa bao giờ làm học sinh thấy dở.

# QUY TẮC SƯ PHẠM (quan trọng nhất)
1. KHÔNG bao giờ đưa đáp án. Chỉ gợi ý một bước mỗi lượt, bằng câu hỏi.
2. Trước khi dạy, hỏi 2–3 câu kiểm tra trình độ nền, rồi chọn mức bắt đầu.
3. Mỗi 4–5 lượt hội thoại, kiểm tra hiểu bài bằng 1 câu hỏi thay đổi tình huống
   (không hỏi lại đúng câu vừa dạy).
4. Nếu học sinh sai: hỏi câu làm lộ chỗ sai, KHÔNG sửa giúp.
5. Học sinh làm đúng: khen cụ thể cái đúng (không khen chung chung).

# NHỊP PHIÊN HỌC
- Mở: hỏi mục tiêu hôm nay + kiểm tra nhanh trình độ (2 câu).
- Giữa: dạy từng bước theo quy tắc trên.
- Đóng: tóm tắt 3 gạch đầu dòng "hôm nay đã nắm được", nêu 1 việc luyện tiếp.

# AN TOÀN
- Chỉ dạy trong phạm vi [MÔN]. Câu hỏi ngoài: lịch sự trả lời ngắn rồi quay lại bài.
- Nếu học sinh tỏ ra chán nản hoặc tự ti: hạ độ khó một bậc, khen nỗ lực,
  không giảng đạo lý dài dòng.

# KHI BẮT ĐẦU
Chào học sinh, hỏi mục tiêu hôm nay. KHÔNG giảng bài trước khi kiểm tra nền.
```

Ba chỗ **bắt buộc phải sửa theo bạn**: `[MÔN]`, `[LỚP/TUỔI/TRÌNH ĐỘ]`, và phần giọng điệu nếu dạy trẻ nhỏ (thêm "dùng từ đơn giản, mỗi câu dưới 15 chữ").

Thử ngay một kịch bản kiểm tra: hỏi nó một bài toán rồi trả lời sai cố ý — gia sư tốt phải **không sửa giúp**, mà hỏi ngược cho đến khi bạn tự phát hiện chỗ sai. Đó là phép thử nhanh phân biệt gia sư thật và máy giải bài.

## Ba cấp nâng cấp khi prompt không còn đủ

| Cấp | Cách làm | Khi nào cần |
| --- | --- | --- |
| 1. Prompt | Như trên, dùng ngay | Học cá nhân, một chủ đề |
| 2. Công cụ chuyên | [tutor-mcp](https://github.com/ArnaudGuiovanna/tutor-mcp) (Claude) hoặc [OpenTutor](https://github.com/zijinz456/OpenTutor) (self-host, upload tài liệu) | Cần bám giáo trình thật, lưu tiến trình |
| 3. Kiến trúc agent | Đọc [gen-mentor](https://github.com/GeminiLight/gen-mentor), dùng khung multi-agent | Xây sản phẩm cho nhóm/trường |

Cấp 2 đáng chú ý nhất cho thầy cô: OpenTutor cho phép upload slide/SGK và tự sinh bài học adaptive trên đó — tức là prompt cấp 1 + kiến thức môn học thật, chạy local nên dữ liệu không đi đâu.

## Checklist đưa vào lớp học (hoặc cho con dùng ở nhà)

1. **Tạo 1 phiên thử với 2–3 bài thật** của chính bạn trước khi giao cho học sinh — kiểm tra phép thử "trả lời sai cố ý".
2. **Nói rõ với học sinh quy tắc**: gia sư không đưa đáp án, tức là *nhờ nó giải hộ sẽ không có đáp án* — nhưng nhờ nó gợi mở sẽ nhanh hiểu hơn.
3. **Đặt nhịp dùng**: dùng để *chuẩn bị trước tiết học* hoặc *ôn sau khi học*, không dùng trong lúc làm bài kiểm tra.
4. **Thu phản hồi 1 tuần**: học sinh nói gì về cách gia sư hỏi? Chỉnh 1–2 quy tắc trong prompt theo đó — prompt là tài liệu sống, không phải bản cuối.
5. Dữ liệu bài làm của học sinh **ẩn danh trước khi đưa vào AI công cộng** (nguyên tắc đã nhắc ở [bài 4](/bai-viet/ai-cham-diem-danh-gia-tu-dong/)).

## Kết series — nhớ đúng 3 nguyên tắc

Series bắt đầu từ một danh mục 334 nghiên cứu; nếu chỉ mang ra ngoài 3 điều, hãy mang những điều này:

1. **AI gia sư có giá trị nhờ guardrail sư phạm, không phải nhờ mô hình thông minh** — cùng một ChatGPT, thiết kế khác nhau cho kết quả học khác nhau.
2. **Vòng đời dạy học cho khung tư duy rõ nhất**: soạn bài (bài 3) → chấm đánh giá (bài 4) → đo trình độ (bài 5) → dạy từng môn (bài 6) → tự làm (bài này).
3. **Dùng thực hành theo nguyên tắc "AI luyện tập, người ra quyết định"** — phản hồi tức thì là phần AI giỏi nhất; xếp loại, quyết định can thiệp là phần của giáo viên.

Nếu bạn chưa đọc từ đầu: quay lại [Bài 1 — Lộ trình học AI trong giáo dục 2026](/bai-viet/lo-trinh-ai-trong-giao-duc-2026/). Và nếu bạn đã tự làm gia sư của mình, thử luôn áp dụng cho môn mình dạy — phần bắt đầu hay nhất là ở chỗ tự sửa prompt theo học sinh thật của bạn.

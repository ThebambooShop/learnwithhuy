---
title: "Kho từ vựng tech với Anki và AI"
description: "Sentence mining kết hợp Anki spaced repetition và AI sinh flashcard — xây kho từ vựng tech bền vững, kèm script Python sinh CSV nhập thẳng vào Anki không cần API key."
topic: "tieng-anh-voi-ai"
date: "2026-11-22"
cover: "/images/covers/posts/kho-tu-vung-tech-voi-anki-va-ai.jpg"
views: 0
featured: false
faq:
  - q: "Anki có khó dùng, mất bao lâu để quen?"
    a: "Cài đặt và import CSV mất chưa đến 10 phút. Phần khó là kỷ luật review mỗi ngày — mức 10 card mới/ngày giữ workload ổn định nhiều tháng."
  - q: "Sao không dùng Quizlet cho nhanh?"
    a: "Quizlet tiện cho bộ card làm sẵn, nhưng import hàng loạt hạn chế và lịch review ít kiểm soát hơn. Khi cần nạp vài trăm card từ công việc của mình, Anki là lựa chọn đích."
  - q: "Mỗi ngày bao nhiêu card mới là hợp lý?"
    a: "Khoảng 10. Con số này cho ~70 từ mỗi tuần mà tổng review vẫn dưới 20 phút/ngày; nhảy thẳng 50-100 card/ngày sẽ kẹt review trong một tuần."
  - q: "AI sinh card có đáng tin không?"
    a: "Tạm được, đừng tin mù. AI thỉnh thoảng đặt ví dụ gượng hoặc nghĩa chưa sát ngành. Đọc lướt từng card trước khi import và sửa chỗ gượng — đó cũng là một lượt ôn miễn phí."
---
Từ "deprecate" xuất hiện trong changelog lần thứ mười hôm nay, và lần thứ mười đó bạn vẫn tra Google như lần thứ nhất. Không phải bạn lười — mà là nhớ bằng cách đọc lại không giữ được gì: một tuần sau, từ đó biến mất như chưa từng học.

Cái giữ được là spaced repetition — và Anki là công cụ chuẩn cho phương pháp này.

> **Spaced repetition** là nhắc lại một từ vào đúng lúc nó sắp bị quên, theo đường cong quên lãng (forgetting curve) của Ebbinghaus. Mỗi lần nhớ được trước ngưỡng quên, khoảng cách tới lần nhắc tiếp theo được kéo dài hơn — review ít mà nhớ lâu.

## Anki — công cụ chuẩn cho spaced repetition

Anki quản lý flashcard và tự tính lịch review: đúng từ, đúng lúc, số lượng nhỏ mỗi ngày. Miễn phí trên máy tính, app điện thoại đồng bộ thẳng, không tốn subscription như app thương mại.

Các thay thế quen thuộc so với Anki:

| Công cụ | Ưu | Nhược |
| --- | --- | --- |
| Anki | Import hàng loạt, lịch review kiểm soát được, đồng bộ PC + điện thoại miễn phí | Giao diện khô, phải tự tạo card |
| Memrise | Game hóa, dễ bắt đầu | Ít kiểm soát lịch review, khó nạp card riêng hàng loạt |
| Quizlet | Dễ dùng, nhiều bộ card làm sẵn | Free bị thu hẹp dần, spaced repetition yếu hơn |

Anki thắng khi bạn cần nạp vài trăm card từ chính công việc mình và lịch review phải chạy bền nhiều tháng — hai điểm Memrise và Quizlet không cho toàn quyền.

## Sentence Mining — card phải có ngữ cảnh

[Sentence Mining](/bai-viet/5-phuong-phap-hoc-tieng-anh-hieu-qua) là lấy từ từ câu thật bạn gặp, thay vì list 3000 từ phổ biến. Card tốt chứa câu thật + từ được che; card xấu chỉ có từ trơ và nghĩa.

Nguồn câu cho dân IT:

- **Câu trong doc vừa đọc** — ví dụ "This endpoint is deprecated and will be removed in the next release" trong release notes.
- **Log hoặc error message thật** — câu lỗi bạn vừa debug là câu có động lực hiểu nhất.
- **Câu hay trong podcast transcript** — nơi "trade-off", "edge case" lỏi vào hội thoại thật.

Bài [luyện đọc tài liệu kỹ thuật tiếng Anh](/bai-viet/luyen-doc-tai-lieu-ky-thuat-tieng-anh) là nguồn cấp câu cho pipeline này: đọc chậm, gạch câu có từ mới, đưa vào danh sách chờ sinh card.

## AI sinh card hàng loạt

Bước thủ công chậm nhất là viết nghĩa và ví dụ cho từng từ. Dán danh sách từ vào prompt dưới đây, nhận card đúng cấu trúc, kiểm tra rồi import:

```text
You are building Anki flashcards for an IT professional learning English.
I will give you a list of words. For EACH word, produce one JSON object:
{
  "word": "...",
  "meaning": "one-line definition, max 15 words",
  "example1": "a sentence using the word in a tech context, max 20 words",
  "example2": "a second sentence with a common collocation",
  "collocations": "2-3 common collocations"
}
Return only a JSON array, no explanation text.
Words: deprecate, idempotent, throughput, race condition
```

Dán chuỗi JSON trả về vào file tạm, dò nhanh từng nghĩa và ví dụ — AI thỉnh thoảng đặt ví dụ hơi cứng — rồi đưa vào bước sinh CSV.

## Script sinh CSV cho Anki

Script dưới đây chạy offline, không cần API key: output là file `anki-flashcards.csv` import thẳng vào Anki (File → Import). Mặt trước là từ + câu đã che từ; mặt sau là nghĩa, collocations và hai ví dụ khác.

```python
#!/usr/bin/env python3
"""Sinh CSV flashcards cho Anki từ danh sách từ vựng tech.

Cách chạy:
    python3 sinh-flashcards-anki.py

Script chạy offline, KHÔNG cần API key. Kết quả là file anki-flashcards.csv
import thẳng vào Anki (File > Import).
"""

import csv
import os
import re

# -------------------------------------------------------------
# Dữ liệu đầu vào: thêm hoặc sửa từ ngay tại đây, mỗi từ một dict.
# -------------------------------------------------------------
VOCAB = [
    {
        "word": "deprecate",
        "meaning": "đánh dấu là không còn khuyến khích dùng và sẽ bị loại bỏ sau",
        "sentence": "The team plans to deprecate the v1 endpoint in the next release.",
        "examples": [
            "The team deprecated the old API in favor of v2.",
            "Avoid calling deprecated methods in new code.",
        ],
        "collocations": "deprecated API, deprecated method, mark as deprecated",
    },
    {
        "word": "idempotent",
        "meaning": "gọi lại nhiều lần vẫn cho cùng kết quả như gọi một lần",
        "sentence": "Make the payment endpoint idempotent so retrying a failed request does not charge twice.",
        "examples": [
            "GET requests are idempotent by definition.",
            "The deploy script is idempotent, so running it twice is safe.",
        ],
        "collocations": "idempotent operation, idempotent request, idempotent by design",
    },
    {
        "word": "throughput",
        "meaning": "lượng công việc hệ thống xử lý được trong một đơn vị thời gian",
        "sentence": "Batching increased throughput from 200 to 900 requests per second.",
        "examples": [
            "The new index improved database throughput noticeably.",
            "We monitor throughput before touching latency numbers.",
        ],
        "collocations": "high throughput, network throughput, throughput per second",
    },
    {
        "word": "race condition",
        "meaning": "lỗi xảy ra khi hai luồng truy cập cùng tài nguyên mà thứ tự không đảm bảo",
        "sentence": "The duplicate invoice bug was caused by a race condition between the two workers.",
        "examples": [
            "Use a mutex to prevent a race condition on the counter.",
            "Race conditions often appear only under heavy load.",
        ],
        "collocations": "avoid a race condition, potential race condition, race condition under load",
    },
    {
        "word": "backpressure",
        "meaning": "cơ chế báo ngược cho phía gửi chậm lại khi hệ thống xử lý không kịp",
        "sentence": "The queue applies backpressure when the consumer falls behind the producer.",
        "examples": [
            "Without backpressure, memory grows until the service crashes.",
            "Reactive streams treat backpressure as a first-class feature.",
        ],
        "collocations": "apply backpressure, backpressure mechanism, signal backpressure",
    },
    {
        "word": "technical debt",
        "meaning": "nợ kỹ thuật: phần code thiếu chuẩn phải trả lãi bằng việc sửa về sau",
        "sentence": "Shipping the hotfix without tests added technical debt we will pay back next sprint.",
        "examples": [
            "We schedule two days per sprint to reduce technical debt.",
            "Ignoring technical debt slows every future release.",
        ],
        "collocations": "accrue technical debt, pay down technical debt, technical debt backlog",
    },
]

BLANK = "[______]"


def blank_sentence(sentence, word):
    """Che từ trong câu bằng BLANK, không phân biệt hoa/thường.

    Câu mẫu phải chứa đúng từ (kể cả chữ hoa/chữ thường khác).
    Nếu không khớp, báo lỗi thay vì tạo card sai.
    """
    pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
    blanked, count = pattern.subn(BLANK, sentence)
    if count == 0:
        raise ValueError("Khong tim thay '{}' trong cau mau: {}".format(word, sentence))
    return blanked


def build_front(entry):
    """Front: từ + câu ngữ cảnh đã che từ."""
    return "{} — {}".format(entry["word"], blank_sentence(entry["sentence"], entry["word"]))


def build_back(entry):
    """Back: nghĩa + collocations + hai ví dụ khác."""
    examples = " / ".join(entry["examples"])
    return "Nghĩa: {} | Collocations: {} | Ví dụ khác: {}".format(
        entry["meaning"], entry["collocations"], examples
    )


def write_csv(rows, path):
    """Ghi CSV đúng format Anki import (phân tách bằng ;, kèm BOM cho Excel)."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
        writer.writerow(["Front", "Back"])
        writer.writerows(rows)


def run():
    rows = [[build_front(e), build_back(e)] for e in VOCAB]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anki-flashcards.csv")
    write_csv(rows, path)
    return rows, path


def self_test(rows):
    """Tự kiểm tra cấu trúc card trước khi báo thành công."""
    assert len(rows) == len(VOCAB), "Số dòng CSV không khớp số từ đầu vào"
    for (front, back), entry in zip(rows, VOCAB):
        assert front.startswith(entry["word"]), "Front phải bắt đầu bằng từ: " + front
        assert BLANK in front, "Front thiếu dấu che từ: " + front
        assert "Nghĩa:" in back and "Collocations:" in back, "Back thiếu cấu trúc: " + back
    print("Self-test: OK — {} card, cấu trúc front/back đúng.".format(len(rows)))


if __name__ == "__main__":
    rows, path = run()
    self_test(rows)
    print("Đã tạo {} flashcard.".format(len(rows)))
    print("File CSV: {}".format(path))
```

Chạy bằng lệnh:

```bash
python3 sinh-flashcards-anki.py
```

Kết quả in ra số card đã tạo và đường dẫn CSV. Muốn thêm từ, sửa biến `VOCAB` đầu file rồi chạy lại. Script dùng dấu `;` phân tách cột để tránh xung đột với dấu phẩy trong nghĩa; Anki tự nhận khi import.

## Tra từ đúng chỗ

Khi nghĩa hoặc ví dụ của AI chưa ổn, tra từ ở đúng nguồn:

| Nguồn | Tra được gì |
| --- | --- |
| Forvo | Nghe người bản xứ phát âm từ, nhiều giọng khác nhau |
| YouGlish | Nghe từ được dùng trong video thật trên YouTube |
| Cambridge Dictionary, Oxford Learner's Dictionaries | Định nghĩa chuẩn cho người học, kèm ví dụ và mức CEFR |
| Linguee, Reverso Context | Ngữ cảnh song ngữ: câu thật hai chiều để thấy cách ghép từ |
| Visuwords | Sơ đồ quan hệ giữa từ và các từ họ hàng |
| Test Your Vocab | Đo quy mô vốn từ hiện tại của bạn |

## Bài tập thực hành

**Làm theo.** Chép script ở trên vào file `sinh-flashcards-anki.py`, chạy, mở Anki → File → Import → chọn `anki-flashcards.csv`. Đặt mức 10 card mới/ngày và giữ review 7 ngày liên tiếp. Nếu chưa từng dùng AI cho việc học tiếng Anh, đọc [bắt đầu học tiếng Anh với AI](/bai-viet/bat-dau-hoc-tieng-anh-voi-ai) trước.

**Tự sửa.** Mở biến `VOCAB`, thay bằng 5-6 từ bạn gặp tuần này trong doc, log hoặc code review — mỗi từ kèm câu thật. Chạy lại và import vào một deck riêng "Từ tuần này".

**Mở rộng.** Nối script với prompt AI ở trên: nhận JSON trả về, viết hàm nhỏ đọc JSON thành list dict đúng cấu trúc `VOCAB`. Phần này là tùy chọn và cần API key — script gốc chỉ cần Python 3.

## Lỗi thường gặp

⚠️ **Tạo 100 card/ngày rồi bị kẹt review.** Tuần sau queue vài trăm card và bạn bỏ hẳn. Chốt ~10 card mới/ngày — ít nhưng đều, review vẫn dưới 20 phút.

⚠️ **Card không có ngữ cảnh.** Mặt trước chỉ có "deprecate nghĩa là gì?" thì gặp câu thật bạn vẫn không biết ghép. Mọi card phải mang câu thật từ doc, log hoặc transcript.

⚠️ **Chọn từ từ nguồn quá hiếm gặp.** Từ học thuật mà công việc IT không dùng là công review đổ ra biển. Chỉ thêm từ đã gặp tối thiểu hai lần ngoài sách.

⚠️ **Bỏ review vài ngày rồi buông cả deck.** Nghỉ 3 ngày là queue kẹt, tâm lý "kẹt quá nên bỏ" cướp luôn cả deck. Cách cứu: một buổi làm sạch backlog, hôm sau quay lại nhịp bình thường.

## Câu hỏi thường gặp

**Anki có khó dùng, mất bao lâu để quen?**
Cài đặt và import CSV mất chưa đến 10 phút. Phần khó là kỷ luật review mỗi ngày — mức 10 card mới/ngày giữ workload ổn định nhiều tháng.

**Sao không dùng Quizlet cho nhanh?**
Quizlet tiện cho bộ card làm sẵn, nhưng import hàng loạt hạn chế và lịch review ít kiểm soát hơn. Khi cần nạp vài trăm card từ công việc của mình, Anki là lựa chọn đích.

**Mỗi ngày bao nhiêu card mới là hợp lý?**
Khoảng 10. Con số này cho ~70 từ mỗi tuần mà tổng review vẫn dưới 20 phút/ngày; nhảy thẳng 50-100 card/ngày sẽ kẹt review trong một tuần.

**AI sinh card có đáng tin không?**
Tạm được, đừng tin mù. AI thỉnh thoảng đặt ví dụ gượng hoặc nghĩa chưa sát ngành. Đọc lướt từng card trước khi import và sửa chỗ gượng — đó cũng là một lượt ôn miễn phí.

## Tài liệu gốc

Công cụ tra từ và nguyên tắc Sentence Mining trong bài lấy từ section **Vocabulary** của dự án [yvoronoy/awesome-english](https://github.com/yvoronoy/awesome-english) — repo tuyển chọn tài nguyên học tiếng Anh do cộng đồng duy trì.

Đọc tiếp: [5 phương pháp học tiếng Anh hiệu quả](/bai-viet/5-phuong-phap-hoc-tieng-anh-hieu-qua) giải thích Sentence Mining đầy đủ, [luyện đọc tài liệu kỹ thuật tiếng Anh](/bai-viet/luyen-doc-tai-lieu-ky-thuat-tieng-anh) chỉ cách thu thập câu, còn [bắt đầu học tiếng Anh với AI](/bai-viet/bat-dau-hoc-tieng-anh-voi-ai) là nơi xuất phát.

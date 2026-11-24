---
title: "Chart digitiser: đọc số liệu từ biểu đồ trong PDF — caption không đủ"
description: "Chart digitiser đọc giá trị từ biểu đồ raster bằng axis calibration, OCR-voted tick labels (5 scale + 2 binarisation) và interpolation; giá trị đọc được gắn cờ approximate và bị loại khỏi conflict resolution."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-23"
cover: "/images/covers/posts/meridian-chart-digitiser-doc-bieu-do.jpg"
featured: false
views: 265
faq:
  - q: "Tại sao caption không đủ cho câu hỏi giá trị từ biểu đồ?"
    a: "Caption chỉ mô tả loại và chủ đề (curve of head vs flow), không chứa giá trị số. Hỏi giá trị tại 70 m³/h cần bộ số (x → y) — số chỉ nằm trong pixel của đường cong, nên phải digitiser đọc từ ảnh."
  - q: "Vì sao tick label phải vote nhiều pass OCR thay vì đọc một lần?"
    a: "Tesseract một pass đọc sai chuỗi ngắn với độ tin cậy cao (50% thành 90%). Digitiser vote qua 5 scale + 2 biến thể nhị phân bằng Counter — dừng sớm khi kết quả thắng rõ, cuối cùng yêu cầu ≥ 2 phiếu."
  - q: "Giá trị đọc từ chart có được dùng để trả lời câu hỏi spec không?"
    a: "Có, nhưng chỉ làm evidence: gắn approximate: true, tham gia fact retrieval và interpolation, nhưng bị loại khỏi conflict resolution — không đè số chính xác trong manual hay bulletin."
  - q: "Ảnh truy vấn không phải biểu đồ (photo data plate) thì xử lý thế nào?"
    a: "Dùng visual descriptor (HSV + HOG-like + ink-layout, 264 chiều) cho image-to-figure retrieval, kết hợp OCR và alarm-code/model detection. Confidence dưới 55% → cảnh báo verify mã trên thiết bị, không trình bày như chắc chắn."
---

Caption của biểu đồ trong manual máy bơm thường chỉ viết vậy: *curve of head vs flow*. Người dùng hỏi: *head tại 70 m³/h là bao nhiêu?* Câu trả lời nằm trong các pixel của đường cong — captioning trả lời được "biểu đồ này vẽ cái gì", không trả lời được "giá trị là bao nhiêu tại điểm X".

Vì vậy Meridian có khối riêng — **chart digitiser** trong `ingest/figures.py` — biến ảnh bar/line chart thành bộ số (x → y): tìm hộp trục, calibration pixel → giá trị, OCR tick label bằng vote nhiều pass, tách series theo màu, nội suy tại điểm hỏi. Mọi giá trị đọc được gắn cờ approximate. Bài này đi qua từng bước với hằng số thật.

## Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Chart digitiser** | Biến ảnh bar/line chart thành bộ số (x → y): trục, calibration, series, interpolation |
| **Axis calibration** | Fit `value = a·pixel + b` từ cặp (vị trí tick, giá trị tick label) |
| **Tick label voting** | Đọc cùng nhãn qua nhiều scale OCR + binarisation, chọn nhãn phổ biến |
| **Visual descriptor** | Vector 264 chiều: HSV + HOG-like + ink-layout, image-to-figure retrieval |
| **Approximate fact** | Giá trị đọc từ chart, gắn `approximate: true` — evidence, không thi đấu khi resolve conflict |
| **Photo perception** | Hiểu ảnh truy vấn: OCR + alarm-code/model detection + cảnh báo khi khó đọc |

## Ba bước digitise

**Bước 0 — phân loại.** `classify_figure` phân ảnh chart / diagram / photo / document qua ImageStats: pixel trắng, màu bão hoà, nền tối, trục dài, tỷ lệ số OCR. Nền tối → photo; trục + nền trắng > 50% + màu hoặc nhiều số → chart; ≥ 60 từ → document; còn lại → diagram; chỉ ảnh `chart` được digitise.

**Bước 1 — tìm hộp trục.** `_axes_geometry` binarise ảnh (pixel tối dưới 90), morphology opening với kernel ngang/dọc dài 30% để giữ đường thẳng dài. Hộp phải chiếm tối thiểu 25% chiều rộng, 20% chiều cao ảnh — không đạt là không digitise.

**Bước 2 — calibration trục.** Đét tick marks ngoài trục, OCR từng nhãn, fit `value = a·pixel + b`; điểm lệch quá 4% span bị loại rồi fit lại. Trục y bắt buộc slope âm; trục x cần ≥ 3 cặp tick, slope dương, RMS ≤ 0.02 — không đạt thì refuse.

**Bước 3 — tách series theo màu.** Pixel bão hoà (S > 90, V > 60) gom theo hue histogram (18 bin, bin ≥ 120 pixel, tối đa 4 series, merge bin kề bù anti-aliasing). Connected components ≥ 40 pixel: rộng-phẳng cùng đáy (lấp đầy ≥ 0.85, baseline lệch ≤ 4 pixel) là bar — đọc đỉnh cột; còn lại là line — trung bình y theo cột.

> ⚠️ **Refuse over guess:** fit kém, slope sai chiều, tick quá ít → trả `None`. Giá trị sai còn tệ hơn không có gì.

## Tick label: vote nhiều pass OCR

Một pass Tesseract đọc sai chuỗi ngắn với độ tin cậy cao: "50%" thành "90%" và không có dấu hiệu để biết. `figures.py` xử lý bằng vote: crop nhãn đọc qua 5 scale phóng (3.0, 4.0, 2.0, 5.0, 6.0) và 2 biến thể (raw + Otsu) — tối đa 10 pass; kết quả hợp lệ bỏ vào `Counter`, dừng sớm khi kết quả thắng rõ (≥ 4 phiếu, gấp ≥ 3 lần runner-up); hết pass chấp nhận khi có ≥ 2 phiếu.

Nhãn thiếu được `_repair_labels` tái dựng từ cấp số cộng (25%, 50%, 75%, 100%), chỉ sửa khi ≥ 3 nhãn đồng thuận. Confidence = 0.35 + 0.2·(số tick y) + 0.2·(1 − RMS) + 0.15·(có title) + 0.1·(có x-labels); dưới 0.55 bị vứt, cap 0.99.

## Bốn cách đọc biểu đồ

| Cách đọc | Đầu vào | Cho được gì | Không cho được gì |
| --- | --- | --- | --- |
| Caption | Text chú thích | Loại chart, chủ đề | Giá trị tại điểm bất kỳ |
| OCR toàn ảnh | Text nhãn trục | Tick values, tên trục | Đường cong — không có (x → y) |
| **Chart digitiser** | Pixel + OCR vote | Bộ (x → y), interpolation tại điểm hỏi | Precision tuyệt đối — sai số ± vài % |
| Vision LLM | Ảnh + prompt | Mô tả xu hướng linh hoạt | Numeric-exact, reproducible, offline |

Bốn cách không thay thế nhau: caption và OCR cho ngữ cảnh, digitiser cho số kiểm soát sai số, Vision LLM cho mô tả tự do, kết quả vào fact index.

## Giá trị approximate: không được phép đè số chính xác

Chart digitised được convert thành **approximate facts** (`approximate: true`): mỗi điểm (x → y) một fact, gắn chunk và model. Câu hỏi *What is the HX-500 specific power at 50% load?* được trả lời — fact channel tìm fact HX-500 chủ đề specific power, rồi `interpolate_series` nội suy tại 50% giữa hai mốc gần nhất.

Nhưng cờ approximate quyết định ranh giới quan trọng hơn. Trong `resolve_conflicts` của `index/facts.py`, chỉ **exact facts** thi đấu: revised thắng previous, bulletin thắng manual, date mới nhất thắng; thua cuộc báo thành ConflictNote. Approximate facts không bao giờ tham gia — comment trong code: *they are evidence, not specifications*.

Vì sao? Sai số đọc ảnh là vô tránh; sai số bảng spec là 0. Cho approximate trả lời câu hỏi — không cho nó đè số manual.

## Visual descriptor và photo perception

Photo alarm panel, data plate không có trục — không digitise được nhưng vẫn cần tìm lại. `visual_descriptor` tạo vector 264 chiều: HSV histogram 8×3×3 = 72 bin (0.5), gradient grid 4×4×8 = 128 (1.0), ink-layout 8×8 = 64 (0.8); letterbox 256×256, sqrt-normalised rồi L2-normalise — robust với resize, nhiễu nhẹ, JPEG artefact.

Khi upload ảnh truy vấn, `retrieval/perception.py` OCR, trích alarm code và model name, tính descriptor. Descriptor vào kênh retrieval `visual`: cosine với index visual, top 10 score ≥ 0.5 — photo data plate tìm lại đúng trang chứa figure.

Photo perception còn biết nó đọc không được: OCR thiếu → "only visual similarity can be used"; rỗng → "relying on visual similarity only"; confidence < 55% → cảnh báo *Verify the alarm code*.

```python
"""Hai khối nhỏ của chart digitiser: interpolation và tick-label voting."""
from collections import Counter


def interpolate_value(x, points):
    """Nội suy tuyến tính trên danh sách (x, y); None khi x ngoài khoảng đã digitise."""
    pts = sorted((float(px), float(py)) for px, py in points)
    if len(pts) < 2 or x < pts[0][0] - 1e-9 or x > pts[-1][0] + 1e-9:
        return None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


def vote_tick_labels(reads):
    """Chọn nhãn tick xuất hiện nhiều nhất qua nhiều pass OCR.

    Một pass Tesseract đọc sai chuỗi ngắn với độ tin cậy cao (50% -> 90%);
    vote qua nhiều pass khôi phục chúng. Dừng sớm khi một kết quả thắng rõ
    (>= 4 phiếu và >= 3 lần runner-up); cuối cùng yêu cầu >= 2 phiếu.
    """
    votes = Counter(r.strip() for r in reads if r and r.strip())
    if not votes:
        return None
    (top, c1), *rest = votes.most_common(2)
    if c1 >= 4 and (not rest or c1 >= 3 * rest[0][1]):
        return top
    return top if c1 >= 2 else None


if __name__ == "__main__":
    # Đường cong specific power digitised từ chart HX-500 (load % -> kW/kg)
    curve = [(20, 3.1), (40, 4.6), (60, 6.0), (80, 7.2), (100, 8.0)]
    value = interpolate_value(50, curve)
    print(f"HX-500 specific power @ 50% load = {value:.2f} kW/kg")

    # 7 pass OCR trên cùng một tick label: 4 lần đọc 50, 2 lần 90, 1 lần rỗng
    print("tick label cuối cùng:", vote_tick_labels(["50", "50", "90", "50", "90", "50", ""]))

    assert interpolate_value(50, curve) == (4.6 + 6.0) / 2      # 5.3
    assert interpolate_value(150, curve) is None                # ngoài range
    assert vote_tick_labels(["50", "50", "50", "50"]) == "50"   # thắng sớm rõ ràng
    assert vote_tick_labels(["x", "y"]) is None                 # không đủ 2 phiếu
    print("OK")
```

## Bài tập

**Làm theo:** Copy code block vào `digitiser.py`, chạy. Thử `interpolate_value(0, curve)` và `interpolate_value(150, curve)` — ngoài range trả `None`.

**Tự sửa:** Thêm nhiễu vào tick-label reads (ví dụ `["50", "5O", "90", "50", "50", "90"]` — chữ O thay số 0), sửa dừng sớm thành `c1 >= 3`: case `["50", "90", "50", "90", "50"]` có đổi kết quả không?

**Mở rộng:** Viết `repair_arithmetic(labels)` mô phỏng `_repair_labels`: tìm cấp số cộng có ≥ 3 nhãn đồng thuận, tái dựng cả dãy, giữ `%` khi đa số nhãn gốc có.

## Lỗi thường gặp

| Biểu hiện | Nguyên nhân | Xử lý |
| --- | --- | --- |
| Digitiser trả `None` dù ảnh rõ là chart | Không tìm thấy hộp trục hoặc confidence < 0.55 | Tăng độ phân giải, trục đủ dài, nền trắng; xem từng thành phần confidence |
| Tick label đọc sai (50% thành 90%) | Một pass OCR không đáng tin | Vote nhiều scale + Otsu; repair chỉ sửa khi ≥ 3 nhãn đồng thuận |
| Giá trị chart đè số trong manual | Approximate fact lọt vào conflict resolution | Giữ `approximate: true`; conflict chỉ xét exact facts |
| Ảnh photo truy vấn đọc không được | OCR confidence thấp | Cảnh báo verify; fallback sang visual descriptor |
| Line chart cho số vô nghĩa | Trục x chưa calibration (dưới 3 cặp tick) | Refuse: trả `None`, không interpolate |

## FAQ

**Tại sao caption không đủ cho câu hỏi giá trị từ biểu đồ?**
Caption chỉ mô tả loại và chủ đề (curve of head vs flow), không chứa giá trị số. Hỏi giá trị tại 70 m³/h cần bộ số (x → y) — số chỉ nằm trong pixel của đường cong, nên phải digitiser đọc từ ảnh.

**Vì sao tick label phải vote nhiều pass OCR thay vì đọc một lần?**
Tesseract một pass đọc sai chuỗi ngắn với độ tin cậy cao (50% thành 90%). Digitiser vote qua 5 scale + 2 biến thể nhị phân bằng Counter — dừng sớm khi kết quả thắng rõ, cuối cùng yêu cầu ≥ 2 phiếu.

**Giá trị đọc từ chart có được dùng để trả lời câu hỏi spec không?**
Có, nhưng chỉ làm evidence: gắn `approximate: true`, tham gia fact retrieval và interpolation, nhưng bị loại khỏi conflict resolution — không đè số chính xác trong manual hay bulletin.

**Ảnh truy vấn không phải biểu đồ (photo data plate) thì xử lý thế nào?**
Dùng visual descriptor (HSV + HOG-like + ink-layout, 264 chiều) cho image-to-figure retrieval, kết hợp OCR và alarm-code/model detection. Confidence dưới 55% → cảnh báo verify mã trên thiết bị, không trình bày như chắc chắn.

## Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — README và [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md)
- Code: `meridian/ingest/figures.py` (digitiser, visual descriptor), `meridian/retrieval/perception.py`, `meridian/index/facts.py` (approximate)
- Bài liền kề: [Ingest PDF, bảng biểu và trang scan](/bai-viet/meridian-ingest-pdf-bang-bieu-scan/) · [8 kênh hybrid retrieval](/bai-viet/meridian-hybrid-retrieval-8-kenh/) · [Fact index và conflict resolution](/bai-viet/meridian-fact-index-conflict-resolution/)
- Từ blog cũ: [Multimodal RAG cho PDF tiếng Việt](/bai-viet/multimodal-rag-pdf-tieng-viet/) — nền Vision QA cho biểu đồ

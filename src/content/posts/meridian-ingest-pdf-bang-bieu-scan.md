---
title: "Ingestion layout-aware: biến PDF bảng biểu và scan thành evidence có citation"
description: "Một bảng PDF 40 dòng trở thành 1 table chunk + 40 row chunks + typed facts kèm unit và provenance; trang scan tự OCR multi-pass; index snapshot swap atomic. Đi vào ingest/pdf.py, ocr.py, office.py và schemas Chunk/Fact/Citation của Meridian."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-23"
cover: "/images/covers/posts/meridian-ingest-pdf-bang-bieu-scan.jpg"
featured: false
views: 248
faq:
  - q: "Một dòng bảng thành một chunk thì số chunk tăng nhiều, retrieval có chậm không?"
    a: "Có tăng (bảng 40 dòng → 41 chunks) nhưng đổi lại precision truy xuất: câu hỏi khớp một dòng thay vì cả bảng. RRF fuse và MMR lọc gần-trùng; chi phí build một lần khi upload, không phải mỗi câu hỏi."
  - q: "Tesseract có bắt buộc phải cài không?"
    a: "Chỉ cần cho trang scan. macOS: brew install tesseract; Ubuntu: sudo apt install tesseract-ocr. Không có Tesseract thì mọi path khác — PDF text, bảng, DOCX bulletin, CSV/XLSX log, TXT/MD — vẫn ingest bình thường."
  - q: "Unit nằm ở header bảng hay ở cột riêng thì fact gắn unit thế nào?"
    a: "Header kiểu 'Torque (Nm)' được regex tách '(Nm)' thành unit cho value; nếu bảng có cột unit/uom thì unit lấy theo từng dòng. Header chứa 'previous/old' hoặc 'revised/new' gắn cờ previous/revised phục vụ conflict resolution."
  - q: "Vì sao phải build snapshot mới rồi mới swap, không update index tại chỗ?"
    a: "Mỗi upload hoặc xóa rebuild một object Indexes mới và swap atomic sau khi build xong — người đọc không bao giờ thấy index dở dang. Start lại thì index rebuild từ SQLite nên không mất gì."
---

Một manual PDF chứa bảng torque 40 dòng, một service bulletin DOCX, một CSV log 6 tháng và một trang scan mờ — nạp cả bốn vào hệ thống. Ingestion là nơi RAG thắng hoặc thua trước cả khi LLM xuất hiện. Chunk-text truyền thống làm phẳng toàn trang: bảng thành chuỗi ký tự, warning box dính vào đoạn kề, scan thành trang trắng, citation trỏ cả trang thay vì đúng vùng.

Meridian chọn hướng ngược lại: **layout-aware parsing** — đọc PDF theo bố cục thật, xuất chunks có cấu trúc, facts có kiểu dữ liệu, bbox có tọa độ. Bài này đi qua từng module ingestion.

## Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Layout-aware parsing** | Phân tích PDF theo bố cục: heading theo font-size, bảng qua pdfplumber, call-out box, figure crop — không làm phẳng toàn trang |
| **Per-row chunk** | Mỗi dòng bảng thành một chunk riêng, mang caption bảng + section làm context |
| **Typed fact** | Cặp (attribute, value, unit) khai thác từ dòng bảng, lưu kèm provenance để lookup chính xác |
| **Bounding box (bbox)** | Tọa độ vùng chứa chunk trên trang; UI highlight đúng vùng khi mở "View source page" |
| **Multi-pass OCR (`ocr_best`)** | Chạy Tesseract nhiều cấu hình (deskew, adaptive threshold) rồi chọn/ghép kết quả tốt nhất |
| **Immutable snapshot** | Index build hoàn chỉnh trong object mới rồi swap atomic; không có index dở dang |
| **Dedupe SHA-256** | Trước khi lưu, hash file; file trùng bị bỏ qua an toàn khi upload lại |

## PDF đi qua ingest/pdf.py

Sáu bước mỗi trang:

- **Heading detection theo font-size** — đoạn cỡ chữ lớn hơn thân bài là section heading; tên section gắn vào context của mọi chunk thuộc section đó.
- **Bảng qua pdfplumber** — lưới ô được bóc thành một **table chunk** (toàn bảng, giữ ngữ cảnh) + **per-row chunks** (mỗi dòng một chunk, để truy xuất) + **typed numeric facts** cho từng ô số.
- **Call-out box → WARNING chunk riêng** — box cảnh báo không trộn vào đoạn văn; Evidence stage attach các WARNING cùng section khi trả lời.
- **Figure crop + page render** — mỗi figure cắt riêng (phục vụ chart digitiser và visual retrieval), trang được render PNG để highlight evidence.
- **Per-chunk bounding boxes** — mọi chunk mang tọa độ vùng trên trang.
- **Auto OCR** — trang trích xuất được quá ít ký tự → render → chạy Tesseract.

> **Rows as chunks:** một câu hỏi khớp một dòng bảng, không phải cả bảng 40 dòng. Row chunk mang caption của bảng ("Table 2 — Fastening torques") làm context, nên retrieval vẫn biết dòng đó thuộc bảng nào.

Hệ quả trực tiếp: hỏi "Torque bulông cánh quạt HX-200?" khớp đúng dòng "Impeller bolt: 45 Nm" thay vì nạp cả bảng cho LLM — loại bỏ nguy cơ trượt cột (COLUMN_SLIP) đã phân tích trong bài nền Multimodal RAG PDF tiếng Việt.

## Facts as first-class index

> **Facts as first-class index:** mỗi fact là một tuple (model, subject, attribute, value, unit, provenance) — không phải text. Từ tuple này hệ thống làm được exact lookup, unit conversion (10 bar = 145 psi) và conflict resolution — việc bất khả thi với text chunk thuần.

Đây là quyết định kiến trúc quan trọng nhất của ingestion. Shape thật của `Fact` trong `meridian/schemas.py`:

| Field | Ý nghĩa |
| --- | --- |
| `model`, `subject`, `attribute` | Khóa tra cứu: "HX-200" + "impeller bolt" + "torque" |
| `value`, `unit`, `display` | 45.0, "nm", "45 Nm" — value là số thật, không phải string |
| `doc_id`, `doc_type`, `doc_title` | Provenance: manual \| bulletin \| log \| card |
| `effective_date` | Bản effective mới hơn thắng khi conflict |
| `revised`, `previous` | Cờ nhận từ header cột "revised/new" hay "previous/old" |
| `approximate` | Giá trị đọc từ chart digitiser — bị loại khỏi conflict resolution |

Khi hai document cùng khẳng định (HX-200, impeller bolt, torque) bằng hai giá trị khác nhau, `resolve_conflicts` trong `index/facts.py` áp precedence: cột revised trước, rồi bulletin trên manual, rồi effective date mới nhất. Giá trị thua không bị xóa — thành `ConflictNote` hiển thị trong UI. Dòng key-value ("Maximum starts per hour: 6") được khai thác qua `mine_kv_facts` thành fact cùng shape.

## Scan: ocr.py

Trang scan không phải fallback rẻ tiền mà là path có chất lượng kiểm soát:

- **Deskew** — chỉnh nghiêng trang trước khi OCR.
- **Adaptive threshold** — tăng tương phản cho ảnh chụp/scan kém.
- **Multi-pass `ocr_best`** — chạy Tesseract nhiều cấu hình, vote chọn kết quả tốt nhất thay vì tin một lần chạy.
- **Regex repair cho alarm code** — OCR đọc "HX2O0" được sửa về dạng mẫu `[A-Z]{1,4}-\d{3,4}`; cùng regex này rút entities cho channel entity retrieval.

## Formats khác: office.py, images.py

- **DOCX service bulletin** — parse thành chunks + facts; doc_type gắn "bulletin" để precedence đúng khi conflict với manual.
- **CSV/XLSX log** — log không bị chunk thành text mà trở thành **datasets + aggregate chunks**: analytics chạy pandas trên dataset gốc, đếm chính xác thay vì LLM đếm bằng văn.
- **TXT/MD** và ảnh — path đơn giản hơn; ảnh đi qua perception (OCR + visual descriptor + phát hiện model/alarm code).

## Persistence: SQLite + snapshot immutable

Document và chunks persist vào SQLite cùng các file dẫn xuất (page images, figure crops, table data). Mỗi file hash SHA-256 — upload lại file y hệt bị bỏ qua. Index gồm nhiều lớp: lexical + char-n-gram, entity + fact + visual + graph, dense (LSA in-memory mặc định, hoặc Qdrant trong Docker). Khi corpus thay đổi:

> **Immutable index snapshots:** mỗi thay đổi rebuild một object `Indexes` mới và swap atomic sau khi build xong — readers never see half-built state. **SQLite + files:** persistence zero-ops; index rebuild từ SQLite khi start.

## Schemas thật: Chunk và Citation

Hai text field của `Chunk` là điểm dễ bỏ sót nhất khi tự thiết kế:

| Field | Vai trò |
| --- | --- |
| `text` | Text được **index**: prefix "doc title \| section" + content — phục vụ retrieval |
| `content` | Text sạch cho **evidence** — answer chỉ được phép quote phần này |
| `modality` | text \| table \| table_row \| figure \| chart \| warning \| ocr_page \| image |
| `parent_id` | Trỏ về section root (`doc_id:sec:...`) — dùng khi expand evidence |
| `bbox` | `BBox(x0, y0, x1, y1, page_width, page_height)` theo convention pdfplumber, gốc top-left |
| `meta` | Chứa `refs` (tham chiếu "Table 4") và `facts` mined từ chunk |

`Citation` là contract trả về UI: `index`, `chunk_id`, `doc_title`, `page`, `modality`, `snippet`, `bbox` (list `[x0, y0, x1, y1]`), `via` (retrieval \| crossref \| warning \| tool \| calculator) và `score`. Nhờ bbox, "View source page" highlight đúng dòng bảng, không phải cả trang.

## Sketch Chunk + Fact chạy offline

```python
"""Sketch data contracts của Meridian (rút gọn từ schemas.py) + build_fact chạy offline."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float
    page_width: float
    page_height: float


@dataclass
class Chunk:
    id: str
    doc_id: str
    page: int = 1
    modality: str = "text"        # text | table | table_row | figure | chart | warning | ocr_page | image
    text: str = ""                # text được index: "title | section\ncontent"
    content: str = ""             # text sạch cho evidence — answer chỉ được quote phần này
    section: str = ""
    parent_id: Optional[str] = None
    bbox: Optional[BBox] = None
    entities: list = field(default_factory=list)   # alarm code, model name rút từ regex


@dataclass
class Fact:
    model: str
    subject: str
    attribute: str
    value: float
    unit: Optional[str]
    chunk_id: str
    doc_id: str
    doc_type: str = "manual"      # manual | bulletin | log | card | image | notes
    effective_date: Optional[str] = None
    revised: bool = False         # đến từ cột "revised/new"
    previous: bool = False        # đến từ cột "previous/old"
    approximate: bool = False     # đến từ chart digitiser — loại khỏi conflict resolution


UNIT_ALIASES = {"nm": "nm", "n·m": "nm", "bar": "bar", "psi": "psi"}


def build_fact(value, unit, model, subject, attribute, provenance):
    """provenance là dict nguồn gốc (chunk_id, doc_id, doc_type...) — Fact cần nó để giải conflict."""
    p = dict(provenance)
    return Fact(
        model=model.upper(),
        subject=subject,
        attribute=attribute.lower(),
        value=float(value),
        unit=UNIT_ALIASES.get((unit or "").lower(), unit),
        chunk_id=p["chunk_id"],
        doc_id=p["doc_id"],
        doc_type=p.get("doc_type", "manual"),
        effective_date=p.get("effective_date"),
        revised=bool(p.get("revised")),
        previous=bool(p.get("previous")),
        approximate=bool(p.get("approximate")),
    )


def resolve_conflicts(facts):
    """Thứ tự ưu tiên: revised > bulletin > manual > effective_date mới hơn."""
    def rank(f):
        return (1 if f.revised else 0,
                {"bulletin": 2, "manual": 1}.get(f.doc_type, 0),
                f.effective_date or "")
    winner = max(facts, key=rank)
    return winner, [f for f in facts if f is not winner]


if __name__ == "__main__":
    bbox = BBox(x0=72, y0=340, x1=520, y1=360, page_width=595, page_height=842)
    row = Chunk(id="hx_manual:0012", doc_id="hx_manual", page=4, modality="table_row",
                content="Impeller bolt: 45 Nm", bbox=bbox, entities=["HX-200"])
    facts = [
        build_fact(45, "Nm", "hx-200", "Impeller Bolt", "Torque",
                   {"chunk_id": row.id, "doc_id": row.doc_id,
                    "doc_type": "manual", "effective_date": "2024-03-01"}),
        build_fact(52, "Nm", "hx-200", "Impeller Bolt", "Torque",
                   {"chunk_id": "hx_sb7:0003", "doc_id": "hx_sb7",
                    "doc_type": "bulletin", "effective_date": "2025-06-15"}),
    ]
    winner, losers = resolve_conflicts(facts)
    print(f"winner: {winner.value} {winner.unit} ({winner.doc_type})")
    for f in losers:
        print(f"conflict: {f.value} {f.unit} ({f.doc_type}) -> ConflictNote")
```

Chạy thuần stdlib. Trong repo thật, `ChunkBuilder.add` tự sinh id tăng dần (`doc_id:0001`), nối context "title | section" vào `text` và `add_facts` đính fact vào `chunk.meta["facts"]` — toàn bộ hàm thuần, dễ unit-test.

## Bài tập

**Làm theo** — Chạy `python -m meridian --load-demo`, mở Knowledge base tab, upload một PDF có bảng. Đếm số chunk theo modality qua UI; click `[n]` trong câu trả lời, mở "View source page" và quan sát bbox highlight đúng dòng bảng.

**Tự sửa** — Thêm alias unit mới vào `UNIT_ALIASES` (ví dụ "n.m" → "nm"); thêm test `build_fact` cho header "Torque (N·m)". Sau đó sửa `resolve_conflicts` đảo ưu tiên: effective_date mới hơn thắng trước doc_type — ghi nhận kết quả demo đổi thế nào và vì sao precedence gốc an toàn hơn.

**Mở rộng** — Viết `table_to_records` mini: nhận bảng Markdown pipe (`| Model | Torque (Nm) |`) và trả list fact dict (subject, attribute, value, unit). Đối chiếu với hàm thật `table_to_records` trong `meridian/ingest/common.py` — pure function, xử lý thêm cột unit và cờ previous/revised.

## Lỗi thường gặp

- ⚠️ Trang scan ra chunk rỗng → Tesseract chưa cài hoặc trang quá mờ → cài Tesseract; pipeline có sẵn deskew + adaptive threshold trong `ocr_best`; nếu vẫn kém, tăng DPI khi render trang.
- ⚠️ Fact không có unit → header không chứa "(unit)" và bảng không có cột unit/uom → chuẩn hoá header nguồn hoặc đưa unit vào cột riêng; dòng "key: value" dùng `mine_kv_facts` vẫn ra fact.
- ⚠️ Row chunk tìm thấy nhưng "View source page" highlight sai chỗ → chunk thiếu bbox riêng → bbox bắt buộc per-chunk lấy từ pdfplumber; kiểm tra `Citation.bbox` khác None khi debug.
- ⚠️ Upload lại file tạo bản trùng → dedupe SHA-256 chỉ nhận đúng file y nguyên; file đã tự chỉnh một chút → hash khác → là document mới, không phải bug → muốn thay thế thì xóa bản cũ trước khi upload.
- ⚠️ Câu trả lời vẫn dùng giá trị cũ ngay sau upload → snapshot mới chưa build xong, swap atomic chưa xảy ra → đây là hành vi đúng (không index dở dang); chờ trace rebuild hoàn tất hoặc refresh.

## FAQ

**Một dòng bảng thành một chunk thì số chunk tăng nhiều, retrieval có chậm không?**
Có tăng (bảng 40 dòng → 41 chunks) nhưng đổi lại precision truy xuất: câu hỏi khớp một dòng thay vì cả bảng. RRF fuse và MMR lọc gần-trùng; chi phí build một lần khi upload, không phải mỗi câu hỏi.

**Tesseract có bắt buộc phải cài không?**
Chỉ cần cho trang scan. macOS: brew install tesseract; Ubuntu: sudo apt install tesseract-ocr. Không có Tesseract thì mọi path khác — PDF text, bảng, DOCX bulletin, CSV/XLSX log, TXT/MD — vẫn ingest bình thường.

**Unit nằm ở header bảng hay ở cột riêng thì fact gắn unit thế nào?**
Header kiểu 'Torque (Nm)' được regex tách '(Nm)' thành unit cho value; nếu bảng có cột unit/uom thì unit lấy theo từng dòng. Header chứa 'previous/old' hoặc 'revised/new' gắn cờ previous/revised phục vụ conflict resolution.

**Vì sao phải build snapshot mới rồi mới swap, không update index tại chỗ?**
Mỗi upload hoặc xóa rebuild một object Indexes mới và swap atomic sau khi build xong — người đọc không bao giờ thấy index dở dang. Start lại thì index rebuild từ SQLite nên không mất gì.

## Tài liệu gốc

- [Meridian README](https://github.com/punit2911/meridian-multimodal-rag#readme) — quick start, kiến trúc ingestion, measured results
- [docs/MODULES.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/MODULES.md) — bảng module và 15 kỹ thuật
- [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) — decisions table ("Rows as chunks", "Facts as first-class index", immutable snapshots)
- Mã nguồn đọc trong bài: [meridian/schemas.py](https://github.com/punit2911/meridian-multimodal-rag/blob/main/meridian/schemas.py) · [meridian/ingest/common.py](https://github.com/punit2911/meridian-multimodal-rag/blob/main/meridian/ingest/common.py)
- Bài liền kề trong series: [Bài 1 — Meridian: vì sao text-chunk RAG thất bại trên tài liệu bảo trì công nghiệp](/bai-viet/meridian-rag-bao-tri-cong-nghiep/) · [Bài 3 — Chart digitiser đọc biểu đồ](/bai-viet/meridian-chart-digitiser-doc-bieu-do/) · bài nền [Multimodal RAG PDF tiếng Việt](/bai-viet/multimodal-rag-pdf-tieng-viet/)

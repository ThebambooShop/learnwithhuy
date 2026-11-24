---
title: "Fact index và conflict resolution: khi manual và bulletin nói khác nhau"
description: "Fact index lưu (model, subject, attribute, value, unit, provenance) và resolve_conflicts áp precedence rules — cột revised, bulletin đè manual, effective date mới nhất — để manual 45 Nm và bulletin 52 Nm không bao giờ bị trộn lẫn."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-23"
cover: "/images/covers/posts/meridian-fact-index-conflict-resolution.jpg"
featured: false
views: 310
faq:
  - q: "Fact index khác gì vector search?"
    a: "Vector search trả về chunk giống câu hỏi nhất theo cosine — xác suất. Fact index trả về giá trị đúng theo (model, subject, attribute) kèm unit, nên có thể làm exact lookup, unit conversion và conflict resolution — những việc chunk văn bản làm không được."
  - q: "Ai thắng khi manual và bulletin cho giá trị khác nhau?"
    a: "Thứ tự precedence: giá trị cột revised bỏ giá trị previous của cùng hàng; bulletin đè manual khi cùng ngày; ngày hiệu lực mới nhất thắng. Người thua không bị xóa — ghi thành ConflictNote hiển thị trong UI."
  - q: "Giá trị đọc từ biểu đồ có tham gia conflict resolution không?"
    a: "Không. Chart digitiser đánh dấu giá trị nội suy là approximate — evidence, không phải specification, nên bị loại khỏi mọi nhóm conflict. Chúng vẫn dùng để trả lời nhưng luôn kèm nhãn approximate."
  - q: "check_premise xử lý giả định sai thế nào?"
    a: "Câu 'Is the HX-200 rated for fluid at 150 °C?' chứa premise 150 °C nhưng corpus không có evidence phù hợp → refuted → refuse rõ ràng thay vì bịa câu trả lời. Nếu premise khớp giá trị superseded cũ, verdict là superseded kèm giải thích giá trị mới."
---

Hỏi "What torque should I use for the HX-200 impeller bolt?" và nhận câu trả lời nghe rất chắc: 45 Nm. Hoặc 52 Nm — tùy lúc chạy. Corpus của Meridian chứa cả hai số này: Maintenance Manual ghi 45 Nm, Service Bulletin SB-118 revision mới hơn ghi 52 Nm. Khi cả hai chunk cùng rơi vào top-k, RAG text trộn lẫn chúng hoặc chọn ngẫu nhiên theo thứ tự chunk. Không ai nói cho bạn biết bulletin mới hơn; cũng không ai nói 45 Nm đã bị supersede. Với lệnh torque sai 7 Nm trên máy móc công nghiệp, đó không phải lỗi demo — đó là sự cố.

Meridian giải bằng một quyết định kiến trúc: fact index tách khỏi vector search. Bài này đi qua cấu trúc Fact, precedence rules của `resolve_conflicts`, `check_premise` bắt giả định sai, và nhóm tool tính chính xác đi kèm.

## Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Fact** | Bản ghi có cấu trúc `(model, subject, attribute, value, unit, provenance)` khai thác từ bảng biểu và chart đã digitise — không phải chunk văn bản |
| **Provenance** | Nguồn gốc của fact: doc_type (manual/bulletin), cờ `revised`/`previous`, effective date, chunk_id để trích dẫn trang gốc |
| **Conflict resolution** | Nhiều nguồn cho cùng `(model, subject, attribute)` nhưng khác giá trị — precedence rules chọn người thắng và giải thích người thua |
| **ConflictNote** | Đối tượng ghi giá trị thắng/thua, tên cả hai tài liệu, quy tắc áp dụng — hiển thị trong UI, không bao giờ âm thầm |
| **lookup_spec** | Tool tìm fact đúng câu hỏi yêu cầu, có attribute-aware scoring và companion lookup để không sót conflict |

## Vì sao fact index là tài sản hạng nhất

> "Facts as first-class index (model, subject, attribute, value, unit, provenance) — lets the system do exact lookup, unit conversion and conflict resolution — impossible from text chunks alone."
> — docs/ARCHITECTURE.md §3, bảng Decisions and why

Câu "impossible from text chunks alone" không phải rhetoric: exact lookup, unit conversion và conflict resolution đòi hỏi biết thuộc tính nào, của chủ thể nào, đơn vị nào, từ tài liệu nào — thông tin chỉ tồn tại khi parse giữ được cấu trúc.

| Tiêu chí | RAG trên text chunk | Fact index trong Meridian |
| --- | --- | --- |
| Trả lời "torque của HX-200?" | Chunk giống câu hỏi nhất theo cosine — có thể là hàng khác của bảng | Fact đúng `(HX-200, impeller bolt, torque)` kèm value + unit |
| Đơn vị | Trộn vào văn bản, LLM tự đoán | Trường `unit` riêng; so sánh theo unit dimension |
| Xung đột nguồn | Cả hai chunk vào context, LLM tự xử lý | Precedence rules quyết định, ConflictNote ghi lại |
| Yes/no premise | Evidence không đủ → trả lời theo cảm tính | check_premise: confirmed / refuted / superseded / unknown |
| Giá trị từ chart | Caption mô tả "curve of head vs flow" | Giá trị nội suy, luôn đánh dấu `approximate` |

Facts được khai thác ở khâu ingest (bài [Ingest PDF, bảng biểu, scan](/bai-viet/meridian-ingest-pdf-bang-bieu-scan/): mỗi table row trở thành một chunk và một fact). `FactIndex` nhóm theo `group_key` — `(model, subject_tokens, attribute, unit_dimension)` — để mọi nguồn nói về cùng đại lượng vật lý nằm chung một nhóm; giá trị approximate từ chart không bao giờ vào nhóm.

## resolve_conflicts: precedence rules rõ ràng, người thua được báo cáo

`index/facts.py` áp precedence theo thứ tự cố định:

| Thứ tự | Quy tắc | Ví dụ |
| --- | --- | --- |
| 1 | Giá trị cột `revised` bỏ giá trị `previous` cùng hàng | Row ghi "45 (previous) → 52 (revised)": chỉ 52 cạnh tranh |
| 2 | Bulletin đè manual khi cùng ngày hiệu lực | SB-118 đè Maintenance Manual |
| 3 | Effective date mới nhất thắng | Bulletin 2025-03-01 thắng manual 2024-01-15 |

Ba chi tiết trong code đáng chú ý hơn bảng rules:

- **So sánh giá trị đi qua unit conversion và tolerance**: `quantities_match` với tolerance tương đối 1e-3 — hai nguồn cùng giá trị khác đơn vị (bar vs psi) không bị đếm nhầm là conflict.
- **Người thua không bị xóa**: mỗi nhóm sinh một `ConflictNote` gồm subject, model, giá trị thắng/thua, tên cả hai tài liệu, quy tắc áp dụng và chunk_id hai bên. UI hiển thị "45 Nm từ HX-200 Maintenance Manual đã bị SB-118 (52 Nm) thay thế". Không mất dữ liệu, không âm thầm.
- **Một nhóm chỉ sinh một note** — đủ giải thích, không tràn màn hình.

Kết quả cho câu hỏi demo là duy nhất và có giải thích: **52 Nm** kèm ConflictNote cho 45 Nm — deterministic, cùng input cho cùng output, không phụ thuộc mô hình ngôn ngữ nào.

## check_premise: bắt giả định sai trước khi trả lời

Câu hỏi "Is the HX-200 rated for fluid at 150 °C?" là yes/no question chứa premise "HX-200 có rating 150 °C cho fluid". Analyzer trích quantity `150 °C`; `lookup_spec` tìm fact theo unit dimension tương ứng. Không có evidence phù hợp → premise không được xác nhận → hệ thống refuse rõ ràng, không bịa một câu "yes" trơn tru. Đó là false premise detection: giả định sai phải bị bắt trước khi câu trả lời được viết, không phải sau.

`check_premise` trả về bốn verdict:

| Verdict | Điều kiện | Hành vi |
| --- | --- | --- |
| confirmed | Premise khớp giá trị đã resolve (tolerance ~0.3%) | Trả lời yes kèm nguồn |
| refuted | Có giá trị resolve nhưng khác premise | Từ chối premise, chỉ ra giá trị đúng |
| superseded | Premise khớp giá trị đã bị supersede | Giải thích: giá trị cũ từ manual, giá trị mới từ bulletin |
| unknown | Premise dùng đơn vị khác dimension với fact | Không xác nhận cũng không phủ định — refuse |

Chi tiết đáng học nhất là `superseded`: premise khớp giá trị cũ 45 Nm không bị phán "sai" — hệ thống trả lời bằng giá trị mới kèm giải thích nguồn cũ và mới. Người dùng giữ câu hỏi của mình nhưng được cập nhật thông tin.

## lookup_spec và nhóm tool tính chính xác

Fact index là nền; agent dùng qua các tool deterministic — không cái nào gọi LLM, không cái nào đánh giá code người dùng:

- **lookup_spec** — attribute-aware scoring: hỏi về "torque" thì fact torque được cộng điểm, fact interval trông giống nhau nhưng khác thuộc tính bị trừ điểm. Nó nạp companion facts cùng `group_key` để conflict không bị bỏ sót, và lọc theo rare terms — fact không nhắc đến "baseplate" không được trả lời câu hỏi về baseplate.
- **Safe pandas analytics** — "Which alarm code occurs most often?" không qua LLM tính số: tool map vào vetted operations (count, sum, mean, argmax), chạy trên DataFrame và hiển thị biểu thức thật (`df[filter].error_code.value_counts().head(5)`) kèm số dòng đã dùng — không expression tự do nào được đánh giá.
- **Unit conversion** — "torque in lb-ft" → giá trị chuyển sang đơn vị yêu cầu trước khi trả lời; 10 bar = 145 psi là phép tính.
- **Chart interpolation** — "What is the HX-500 specific power at 50% load?" đọc điểm từ đường curve đã digitise, nội suy tại x=50, đánh dấu `interpolated=True` khi x không trùng điểm đo.

Nhóm này giải quyết phần "số học do LLM": mỗi số trong câu trả lời đến từ một phép tính hoặc một fact có nguồn, không từ xác suất sinh token.

## Mini implementation: resolve_conflicts bằng stdlib

Đoạn sau giữ precedence của `index/facts.py` thu về stdlib — chạy offline, không dependency:

```python
"""Mini conflict resolver: manual vs bulletin vs effective date (stdlib only)."""
from collections import defaultdict


def group_key(f):
    return (f["model"], f["subject"], f["attribute"])


def same_value(a, b):
    # cùng đơn vị và gần nhau theo tolerance tương đối thì coi là cùng giá trị
    if a["unit"] != b["unit"]:
        return False
    return abs(a["value"] - b["value"]) <= 1e-3 * max(1.0, abs(a["value"]))


def rank(f):
    # precedence: cột revised > bulletin > manual, rồi ngày hiệu lực mới nhất
    return (1 if f["revised"] else 0, 1 if f["doc_type"] == "bulletin" else 0, f["effective_date"])


def resolve_conflicts(facts):
    groups = defaultdict(list)
    for f in facts:
        groups[group_key(f)].append(f)
    selected, notes = [], []
    for key, members in groups.items():
        if any(m["revised"] for m in members):
            members = [m for m in members if not m["previous"]]
        distinct = []
        for m in members:
            if not any(same_value(m, d) for d in distinct):
                distinct.append(m)
        if len(distinct) == 1:
            selected.append(max(members, key=rank))
            continue
        ranked = sorted(members, key=rank, reverse=True)
        winner = ranked[0]
        selected.append(winner)
        loser = ranked[1]
        rule = ("bulletin đè manual" if winner["doc_type"] == "bulletin" and loser["doc_type"] != "bulletin"
                else "ngày hiệu lực mới nhất thắng")
        notes.append({"subject": winner["subject"], "model": winner["model"],
                      "winner": winner["doc_title"], "loser": loser["doc_title"],
                      "winner_value": f"{winner['value']} {winner['unit']}",
                      "loser_value": f"{loser['value']} {loser['unit']}", "rule": rule})
    return selected, notes


facts = [
    {"model": "HX-200", "subject": "impeller bolt", "attribute": "torque",
     "value": 45, "unit": "Nm", "revised": False, "previous": False,
     "doc_type": "manual", "doc_title": "HX-200 Maintenance Manual", "effective_date": "2024-01-15"},
    {"model": "HX-200", "subject": "impeller bolt", "attribute": "torque",
     "value": 52, "unit": "Nm", "revised": True, "previous": False,
     "doc_type": "bulletin", "doc_title": "Service Bulletin SB-118", "effective_date": "2025-03-01"},
]
selected, notes = resolve_conflicts(facts)
assert selected[0]["value"] == 52, "bulletin revised phải thắng"
assert notes[0]["rule"] == "bulletin đè manual"
assert notes[0]["winner_value"] == "52 Nm" and notes[0]["loser_value"] == "45 Nm"

# cùng ngày hiệu lực: bulletin vẫn thắng manual
facts2 = [dict(facts[0]), dict(facts[1])]
facts2[0]["effective_date"] = "2025-03-01"
facts2[1]["revised"] = False
selected2, notes2 = resolve_conflicts(facts2)
assert selected2[0]["doc_type"] == "bulletin", "cùng ngày: bulletin đè manual"
print("OK —", selected2[0]["value"], selected2[0]["unit"], "| note:", notes2[0]["rule"])
```

## Bài tập

**Làm theo:** Chạy code block trên. Thêm fact thứ ba — manual cũ cho giá trị 48 Nm, effective date 2023 — và kiểm tra note vẫn chỉ sinh một bản cho nhóm.

**Tự sửa:** Thay `same_value` bằng so sánh theo unit dimension với bảng quy đổi (bar↔psi, Nm↔lb-ft): hai fact cùng giá trị khác đơn vị là đồng thuận, không phải conflict.

**Mở rộng:** Kết nối với bài [8 kênh hybrid retrieval](/bai-viet/meridian-hybrid-retrieval-8-kenh/): fact channel gọi `FactIndex.search` với IDF nội bộ. Viết wrapper nhận output retrieval của bạn, dựng fact giả lập rồi chạy `resolve_conflicts` trước khi compose — conflict resolution chạy trước generation, không phải sửa sau.

## Lỗi thường gặp

- **LLM trộn lẫn hai giá trị trong một câu trả lời** → cả manual và bulletin cùng vào context qua top-k → đặt fact index + `resolve_conflicts` trước khâu compose; kiểm tra ConflictNote có được render trong UI không — note bị nuốt thì người thua "mất" âm thầm.
- **Conflict được đếm nhầm khi hai nguồn ghi cùng giá trị khác đơn vị** → so sánh số thô thay vì đi qua unit conversion → so sánh theo unit dimension kèm tolerance như `quantities_match`.
- **Premise sai được trả lời "yes"** → analyzer không trích premise quantity hoặc lookup_spec không lọc theo unit dimension → bật trace của analyzer (intent yes/no, quantities) trước khi debug tool.
- **Giá trị chart nội suy lọt vào conflict resolution** → quên loại approximate → `resolve_conflicts` loại approx ngay từ đầu; giữ nhãn approximate khi hiển thị — chúng vẫn là evidence hợp lệ.
- **lookup_spec trả về fact của model khác** → model filtering chỉ áp ở retrieval mà không áp ở fact search → lọc theo models của câu hỏi ngay trong `FactIndex.search` — một chunk HX-500 không bao giờ trả lời câu hỏi HX-200.

## FAQ

**Fact index khác gì vector search?**
Vector search trả về chunk giống câu hỏi nhất theo cosine — xác suất. Fact index trả về giá trị đúng theo (model, subject, attribute) kèm unit, nên có thể làm exact lookup, unit conversion và conflict resolution — những việc chunk văn bản làm không được.

**Ai thắng khi manual và bulletin cho giá trị khác nhau?**
Thứ tự precedence: giá trị cột revised bỏ giá trị previous của cùng hàng; bulletin đè manual khi cùng ngày; ngày hiệu lực mới nhất thắng. Người thua không bị xóa — ghi thành ConflictNote hiển thị trong UI.

**Giá trị đọc từ biểu đồ có tham gia conflict resolution không?**
Không. Chart digitiser đánh dấu giá trị nội suy là approximate — evidence, không phải specification, nên bị loại khỏi mọi nhóm conflict. Chúng vẫn dùng để trả lời nhưng luôn kèm nhãn approximate.

**check_premise xử lý giả định sai thế nào?**
Câu 'Is the HX-200 rated for fluid at 150 °C?' chứa premise 150 °C nhưng corpus không có evidence phù hợp → refuted → refuse rõ ràng thay vì bịa câu trả lời. Nếu premise khớp giá trị superseded cũ, verdict là superseded kèm giải thích giá trị mới.

## Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) mục 3 (bảng Decisions) và mục 5 (Conflict resolution), kèm [docs/MODULES.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/MODULES.md)
- Code trong bài: `meridian/index/facts.py` (FactIndex, resolve_conflicts, ConflictNote), `meridian/agent/tools.py` (lookup_spec, check_premise, run_analytics, convert_fact, read_chart_values)
- Bài liền kề trong series: [8 kênh hybrid retrieval](/bai-viet/meridian-hybrid-retrieval-8-kenh/) · [CRAG grader và abstention](/bai-viet/meridian-crag-grader-abstention/) · [Ingest PDF, bảng biểu, scan](/bai-viet/meridian-ingest-pdf-bang-bieu-scan/)

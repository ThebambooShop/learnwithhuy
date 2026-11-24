---
title: "Claim-level verifier: chặn hallucination trước khi câu trả lời ra tới người dùng"
description: "Verifier tách khỏi generator: bốn lớp check claim-level — số unit-aware, identifiers/dates, negation, lexical coverage — bảo vệ cả composer offline lẫn LLM; repair ladder drop câu sai → fallback extractive → abstain; benchmark injection phát hiện 91.7% hallucination, faithfulness 100% câu delivered."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-23"
cover: "/images/covers/posts/meridian-claim-verifier-hallucination.jpg"
featured: false
views: 342
faq:
  - q: "Verifier khác grader ở bài trước chỗ nào?"
    a: "Grader chấm evidence TRƯỚC generation — quyết định trả lời hay abstain. Verifier chấm từng claim SAU generation — đối chiếu câu trả lời đã viết với evidence được cite. Grader chặn generation chạy thiếu evidence; verifier bắt những gì lọt qua trong lúc viết. Hai lớp cùng hoạt động, không thay thế nhau."
  - q: "Vì sao composer offline không thể bịa?"
    a: "Composer extractive ghép mỗi câu từ row bảng, step procedure, chart reading hoặc kết quả tool đã truy xuất, mỗi câu kèm citation [n] do CiteBook gán theo thứ tự xuất hiện đầu tiên. Không có bước sinh ngữ mới — chỉ trích và nối. Trade-off: fluency thấp hơn LLM, đổi lấy faithfulness được đảm bảo bằng cấu trúc."
  - q: "Số người dùng đưa vào câu hỏi bị flag là hallucination thì sao?"
    a: "Verifier có echo-refutation: số người dùng trích lại trong phần correction ('... is 140 degC, not 150 degC') được phép — đây là số đang bị bác bỏ, không phải số bịa. Không có cơ chế này, mọi câu phản bác false premise đều bị verifier đánh chết và repair xóa nhầm phần correction đúng."
  - q: "False positive 12.3% trên benchmark injection nghĩa là gì?"
    a: "Trên câu trả lời sạch, 12.3% claim bị flag không chính xác — chủ yếu paraphrase mạnh làm IDF-weighted lexical coverage rơi dưới ngưỡng. Chi phí chấp nhận được vì repair chỉ drop câu unsupported (không sửa câu), faithfulness của câu delivered vẫn 100%, và nó hiện rõ trong reports/eval_report.md chứ không được giấu."
---

RAG demo đo chất lượng bằng "câu trả lời có mượt không". Nhưng hallucination không phải lỗi tổng thể của câu trả lời — nó lẩn vào từng claim: một con số sai, một mã lỗi không tồn tại, một câu phủ định evidence chưa bao giờ nói. Câu trả lời 90% đúng với 10% bịa nguy hiểm hơn câu từ chối. Bài [trước](/bai-viet/meridian-crag-grader-abstention/) chặn generation chạy khi evidence không đủ; bài này xử lý phần còn lại: kiểm từng claim trước khi ra tới người dùng.

Quyết định kiến trúc nằm ngay trong bảng Decisions của ARCHITECTURE.md:

> "Verifier is separate from the generator — same checks guard the offline composer and any LLM. Independent of what writes the text."

Bộ check viết **một lần**, bảo vệ **mọi nguồn sinh văn bản** — composer offline extractive lẫn LLM Anthropic/OpenAI/Ollama. Verifier không quan tâm ai viết câu trả lời, chỉ quan tâm câu trả lời có bám evidence hay không. Chất lượng trust vì thế không bị rewrite mỗi lần đổi generator hay nâng cấp model — trust layer sống ở chỗ không có model nào trong pipeline.

## Thuật ngữ cốt lõi

| Thuật ngữ | Nghĩa |
| --- | --- |
| **Claim** | Từng câu/bullet atom của câu trả lời — verifier chấm từng claim, không chấm cả đoạn |
| **Verifier** | Bộ kiểm deterministic, không LLM — đối chiếu từng claim với evidence được cite |
| **Verdict** | supported / partial / unsupported / contradicted — bốn mức của một claim |
| **Unit-aware check** | So số theo kích thước vật lý: 10 bar = 145 psi là khớp, không phải khác |
| **Repair** | Drop câu claim không được support — xóa, không sửa lại câu |
| **CiteBook** | Sổ citation của composer: gán [n] theo thứ tự xuất hiện đầu tiên của evidence |
| **Faithfulness** | Tỷ trọng claim được support (partial tính nửa) của câu trả lời delivered |

## Bốn lớp kiểm tra trong verify/verifier.py

`split_claims` tách answer thành atomic claims: mỗi bullet là một claim, mỗi câu là một claim; heading kết thúc bằng hai chấm bị loại. Mỗi claim giữ danh sách citation [n] nó trích. Từng claim đi qua bốn lớp:

| Lớp | Kiểm tra gì | Ví dụ lỗi bị bắt |
| --- | --- | --- |
| **Numeric** | Mọi số phải tồn tại trong evidence, so theo unit conversion, tolerance 0.4% | "torque 60 Nm" khi evidence ghi 52 Nm → contradicted |
| **Identifier/reference** | Mã lỗi, model, ngày, tham chiếu "Table 3" phải nằm trong evidence **đã cite** — không phải toàn corpus | Mã SB-12 chỉ có trong [5] nhưng claim trích [2] → unsupported |
| **Negation** | Claim chứa phủ định khi không câu nào trong evidence phủ định → contradicted | "Valve is NOT auto-closing" khi evidence chỉ ghi mô tả khẳng định |
| **Lexical coverage** | IDF-weighted coverage của thuật ngữ claim so với evidence — từ hiếm có trọng số lớn | Paraphrase lố bịch làm coverage rơi dưới ngưỡng → unsupported |

Hai chi tiết quyết định chất lượng. **Số đối chiếu theo kích thước vật lý, không theo ký tự**: evidence "10 bar", claim "145 psi" — so chuỗi sai, so unit conversion khớp; "60 Nm" khi evidence "52 Nm" là lệch cùng kích thước torque → **contradicted**, nặng hơn unsupported; số có trong corpus nhưng ở evidence khác cái được cite cũng bị bắt. **Số người dùng trích lại trong correction được phép**: hệ thống phản bác false premise "Is the HX-200 rated for 150 degC?" bằng "rating is 140 degC, not 150 degC" — con số 150 do người dùng đưa; không có ngoại lệ này, mọi câu sửa false premise đều bị đánh chết.

Verdict cuối của mỗi claim:

| Verdict | Điều kiện | Score band |
| --- | --- | --- |
| supported | đủ coverage, không số lẻ, không identifier thiếu | ≥ 0.72 |
| partial | một phần số khớp, hoặc coverage trung bình | 0.48–0.72 |
| unsupported | số không có trong evidence, coverage thấp | < 0.48 |
| contradicted | lệch cùng kích thước vật lý, hoặc negation lật nghĩa | bị ép ≤ 0.2 |

## Composer offline: extractive là cách không thể bịa

Composer offline là **evidence-extractive**: mỗi câu ghép trực tiếp từ một row bảng, một step procedure, một chart reading hoặc kết quả tool — không sinh ngữ mới. `agent/compose.py` dùng **CiteBook** gán citation `[n]` theo thứ tự evidence xuất hiện lần đầu, và nhớ verifier-text của từng evidence để verifier đối chiếu đúng chỗ.

> "Composer is extractive in offline mode — cannot invent facts; fluency is traded for guaranteed faithfulness."

| Tiêu chí | Offline composer (extractive) | LLM mode (Anthropic / OpenAI-compatible) |
| --- | --- | --- |
| Nguồn câu chữ | Ghép từ row/step/chart/computed + template cố định | Viết tự do từ numbered evidence |
| Citation | CiteBook gán [n] theo thứ tự xuất hiện đầu tiên | Prompt bắt buộc trích [n], được gọi 2 tools |
| Risk bịa | Không thể bịa — chỉ trích và nối | Có thể bịa — bị verifier bắt |
| Fluency | Thấp — câu dạng bản ghi | Cao — văn xuôi tự nhiên |
| Offline / chi phí | Không key, không network | Cần server (Ollama local cũng được) |
| Vai trò | Default + fallback bắt buộc | Tùy chọn, output vẫn đi cùng verifier |

Điểm cần nhấn: offline composer là **fallback bắt buộc** của LLM mode. LLM chết (network, auth, malformed reply) hoặc output không qua verifier → pipeline quay về composer extractive — người dùng vẫn nhận câu trả lời có citation, chỉ kém mượt hơn.

## LLM mode: tùy chọn, viết từ numbered evidence

Default là offline thuần. Khi bật, LLM viết câu trả lời **từ numbered evidence** (chính là các [1], [2] CiteBook đã đánh số) và được gọi hai tool: `search_documents` và `lookup_spec` — tìm thêm tài liệu hoặc tra fact index với conflict resolution. LLM không được "tra google", chỉ được nhìn đúng kho evidence retrieval đã chọn.

Cấu hình với Ollama chạy local llama3.1 (miễn phí, không key):

```bash
MERIDIAN_LLM_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:11434/v1
MERIDIAN_LLM_MODEL=llama3.1
MERIDIAN_AGENT_MODE=auto
```

`MERIDIAN_AGENT_MODE=auto` — có LLM server thì dùng, không có thì offline; `policy` ép offline cứng. Với Docker Compose, base URL đổi thành `http://host.docker.internal:11434/v1` vì `localhost` trong container không trỏ về host.

⚠️ **Ghi chú API stability:** giao diện LLM và bộ env var của repo có thể đổi giữa các phiên bản — khi chạy thật, check README mới nhất trên repo trước khi copy cấu hình.

## Repair ladder: drop câu sai, không sửa câu sai

Câu trả lời có claim không được support thì repair ladder đi bốn nấc:

| Nấc | Hành động | Điều kiện |
| --- | --- | --- |
| 1 | **Pass-through** | Tất cả claim supported → delivered |
| 2 | **Repair** | Drop câu chứa claim unsupported/contradicted — câu còn lại giữ nguyên |
| 3 | **Fallback extractive** | Repair xong không còn đủ câu → quay về composer offline |
| 4 | **Abstain** | Cả hai fail → từ chối trả lời kèm lý do trong trace |

Nguyên tắc: **drop, không sửa**. Sửa câu sai bằng cách sinh câu mới là làm việc của generator — đưa vào repair là mở lỗ cho hallucination quay lại. Repair chỉ xóa. Nấc 3 và 4 là hai đường về an toàn: nấc 3 trả về câu có citation được đảm bảo, nấc 4 trả về "không trả lời được" — cả hai tốt hơn một câu bịa.

## Benchmark hallucination-injection: phát hiện 91.7%

Làm sao tin verifier không phải nơi trang trí? Benchmark injection lấy câu trả lời đã verify sạch, **tiêm lỗi có kiểm soát** — đổi số, thêm câu bịa, lật negation, đổi entity — rồi đo tỷ lệ phát hiện:

| Loại injection | Detection |
| --- | --- |
| Overall | 91.7% |
| Numeric | 87.5% |
| Fabricated sentence | 94.4% |
| Negation | 93.8% |
| Entity | 91.5% |
| False positive trên answer sạch | 12.3% |

False positive 12.3% là giá của độ nghiêm ngặt — câu sạch bị flag vì paraphrase mạnh làm coverage rơi; chấp nhận được vì repair chỉ drop câu. Kết quả cuối quan trọng nhất: faithfulness **100% claims supported** trên câu delivered — chưa có hallucination nào lọt tới người dùng trong benchmark này. Calibration đi cùng: confidence Platt-scaled trên train split, ECE held-out từ 0.027 → 0.008 — con số hiển thị cho người dùng đáng tin hơn gần 3.5 lần.

## Mini implementation: split_claims + check_number_claim

Sketch giữ ý chính của `verify/verifier.py` — tách claim, citation index, kiểm số unit-aware theo kích thước vật lý — thu về stdlib:

```python
"""Claim verifier sketch: split_claims + unit-aware number check (stdlib only)."""
import re

_CITE_RE = re.compile(r"\[(\d+)\]")
QTY_RE = re.compile(r"(\d+(?:\.\d+)?)\s*([a-z]+(?:-[a-z]+)?)")
_META_PREFIX = re.compile(r"\b(table|figure|fig\.?|section|step|page|rev(?:ision)?)\s*$")

# đơn vị → (kích thước vật lý, hệ số nhân về đơn vị chuẩn của kích thước đó)
UNIT_MAP = {
    "bar":   ("pressure", 100_000.0),
    "kpa":   ("pressure", 1_000.0),
    "psi":   ("pressure", 6_894.757),
    "nm":    ("torque", 1.0),
    "n-m":   ("torque", 1.0),
    "lb-ft": ("torque", 1.35582),
    "mm":    ("length", 0.001),
    "inch":  ("length", 0.0254),
}


def split_claims(answer):
    """Mỗi bullet/câu là một atomic claim → (text không citation, cites)."""
    claims = []
    for line in (answer or "").split("\n"):
        line = line.strip().lstrip("-*•> ").strip()
        if not line:
            continue
        cites = [int(m.group(1)) for m in _CITE_RE.finditer(line)]
        text = _CITE_RE.sub("", line).strip()
        text = re.sub(r"^\d{1,2}[.)]\s+", "", text)      # bỏ marker list
        if text.endswith(":"):                            # heading, không phải claim
            continue
        if len(re.findall(r"[A-Za-z0-9]+", text)) < 2:
            continue
        claims.append((text, cites))
    return claims


def _match(target, evidence_numbers, dim, rel_tol):
    for v, u in evidence_numbers:
        conv = UNIT_MAP.get(u)
        if conv and conv[0] == dim:
            if abs(v * conv[1] - target) <= rel_tol * max(abs(target), 1.0):
                return True
    return False


def check_number_claim(claim_text, evidence_numbers, rel_tol=0.004):
    """Số trong claim đối chiếu evidence theo kích thước vật lý:
    khớp hết → supported; lệch cùng kích thước → contradicted; thiếu hẳn → unsupported."""
    checks = []
    lower = claim_text.lower()
    for m in QTY_RE.finditer(lower):
        value, unit = float(m.group(1)), m.group(2)
        conv = UNIT_MAP.get(unit)
        if conv is None:
            continue                                      # identifier hoặc từ thường
        prefix = lower[max(0, m.start() - 14):m.start()]
        if _META_PREFIX.match(prefix):
            continue                                      # số bảng/trang/bước, không phải quantity
        dim, factor = conv
        target = value * factor
        checks.append((f"{value:g} {unit}", _match(target, evidence_numbers, dim, rel_tol), dim))
    if not checks:
        return "supported", []                            # không chứa số → fail ở bước khác
    reasons = [f"number {name} không được evidence hỗ trợ" for name, ok, _ in checks if not ok]
    if all(ok for _, ok, _ in checks):
        return "supported", []
    ev_dims = {UNIT_MAP[u][0] for _, u in evidence_numbers if u in UNIT_MAP}
    if any(not ok and dim in ev_dims for _, ok, dim in checks):
        reasons.append("same-dimension number differs → contradicted")
        return "contradicted", reasons
    if any(ok for _, ok, _ in checks):
        return "partial", reasons
    return "unsupported", reasons


answer = (
    "Impeller bolt torque is 52 Nm [1].\n"
    "Maximum inlet pressure is 145 psi [2].\n"
    "Shaft runout limit is 0.05 mm [3]."
)
claims = split_claims(answer)
assert len(claims) == 3, claims

ev = [(52.0, "nm"), (10.0, "bar")]          # evidence đã cite: torque + pressure
v1, r1 = check_number_claim(claims[0][0], ev)
assert v1 == "supported", (v1, r1)

v2, r2 = check_number_claim(claims[1][0], ev)   # 10 bar = 145 psi — khác đơn vị, cùng pressure
assert v2 == "supported", (v2, r2)

v3, r3 = check_number_claim("Impeller bolt torque is 60 Nm", ev)
assert v3 == "contradicted", (v3, r3)           # lệch cùng kích thước torque

v4, r4 = check_number_claim(claims[2][0], ev)
assert v4 == "unsupported", (v4, r4)            # length không có trong evidence

print("OK —", v1, "|", v2, "|", v3, "|", v4)
for text, cites in claims:
    print(f"  claim: {text!r}  cites={cites}")
```

## Bài tập

**Làm theo:** Chạy code block trên, rồi sửa `ev` thành `[(52.0, "lb-ft")]` — claim "52 Nm" giờ khớp không, vì sao? Ghi lại kết quả trước khi chạy.

**Tự sửa:** Thêm echo-refutation vào `check_number_claim`: nhận thêm `echo_numbers` (số người dùng đưa); số khớp echo được miễn trừ khi claim có từ phủ định. Test với "Rating is 140 degC, not 150 degC" và evidence chỉ có 140 — phải supported thay vì contradicted.

**Mở rộng:** Viết `repair_ladder(answer, verdicts)` mô phỏng repair của `verifier.py`: drop câu chứa claim unsupported/contradicted; nếu sau repair faithfulness dưới 0.6, trả về "FALLBACK_EXTRACTIVE". So sánh với prompt flow trong bài [Agent RAG và GraphRAG](/bai-viet/agent-rag-va-graphrag/).

## Lỗi thường gặp

- **Verifier bắt claim đúng vì paraphrase mạnh** → lexical coverage rơi dưới ngưỡng 0.72 dù nghĩa đúng → nguồn false positive 12.3%; hạ ngưỡng hoặc so thêm câu evidence khác, không dùng coverage một mình.
- **Số correction của người dùng bị flag hallucination** → thiếu echo-refutation → truyền `echo_text` (câu hỏi gốc) vào `verify()` để số trích lại được miễn trừ trong phần correction.
- **Citation [n] chỉ vào evidence không tồn tại** → LLM tự sáng tạo số citation ngoài range → verifier bắt "cites non-existent evidence" ngay lớp đầu; composer offline không xảy ra vì CiteBook gán số theo thứ tự thật.
- **Số bảng/trang bị đếm là quantity** ("see Table 3" → 3 là số?) → thiếu lọc meta-prefix → số sau "table/figure/section/step/page" phải loại trước khi check numeric.
- **Verifier chậm trên request lớn** → evidence set không cache → `EvidenceDoc.prepare()` cache sẵn sentence windows, quantities, identifiers; verify chỉ chạy trên claims đã tách.

## FAQ

**Verifier khác grader ở bài trước chỗ nào?**
Grader chấm evidence TRƯỚC generation — quyết định trả lời hay abstain. Verifier chấm từng claim SAU generation — đối chiếu câu trả lời đã viết với evidence được cite. Grader chặn generation chạy thiếu evidence; verifier bắt những gì lọt qua trong lúc viết. Hai lớp cùng hoạt động, không thay thế nhau.

**Vì sao composer offline không thể bịa?**
Composer extractive ghép mỗi câu từ row bảng, step procedure, chart reading hoặc kết quả tool đã truy xuất, mỗi câu kèm citation [n] do CiteBook gán theo thứ tự xuất hiện đầu tiên. Không có bước sinh ngữ mới — chỉ trích và nối. Trade-off: fluency thấp hơn LLM, đổi lấy faithfulness được đảm bảo bằng cấu trúc.

**Số người dùng đưa vào câu hỏi bị flag là hallucination thì sao?**
Verifier có echo-refutation: số người dùng trích lại trong phần correction ('... is 140 degC, not 150 degC') được phép — đây là số đang bị bác bỏ, không phải số bịa. Không có cơ chế này, mọi câu phản bác false premise đều bị verifier đánh chết và repair xóa nhầm phần correction đúng.

**False positive 12.3% trên benchmark injection nghĩa là gì?**
Trên câu trả lời sạch, 12.3% claim bị flag không chính xác — chủ yếu paraphrase mạnh làm IDF-weighted lexical coverage rơi dưới ngưỡng. Chi phí chấp nhận được vì repair chỉ drop câu unsupported (không sửa câu), faithfulness của câu delivered vẫn 100%, và nó hiện rõ trong reports/eval_report.md chứ không được giấu.

## Tài liệu gốc

- Repo: [meridian-multimodal-rag](https://github.com/punit2911/meridian-multimodal-rag) — [docs/ARCHITECTURE.md](https://github.com/punit2911/meridian-multimodal-rag/blob/main/docs/ARCHITECTURE.md) mục 3 (Decisions: verifier separate from generator, composer extractive) và mục 5 (Trust layer); README mục "Optional: use an LLM" và Measured results
- Code trong bài: `meridian/verify/verifier.py` (split_claims, bốn lớp check, verdicts, repair), `meridian/agent/compose.py` (composer extractive, CiteBook gán [n]), `meridian/llm/base.py` (provider-neutral client, LLMError → fallback), `meridian/agent/llm_agent.py` (LLM writer, tools search_documents / lookup_spec)
- Bài liền kề trong series: [CRAG grader và abstention](/bai-viet/meridian-crag-grader-abstention/) · [Benchmark và deploy](/bai-viet/meridian-benchmark-qdrant-deployment/)
- Từ blog cũ: [Agent RAG và GraphRAG](/bai-viet/agent-rag-va-graphrag/) — so sánh cách agent RAG thông thường xử lý output LLM với repair ladder trong bài

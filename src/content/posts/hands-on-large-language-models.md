---
title: "Hands-On Large Language Models: học LLM qua 275+ hình minh họa và notebook thực hành"
description: "Bài học elearning về phương pháp trực quan hóa của sách Hands-On Large Language Models (Jay Alammar & Maarten Grootendorst) — repo 30.000 sao: pipeline từ token đến ứng dụng RAG, kèm cách học bằng hình ảnh và notebook."
topic: "generative-ai-llm"
date: "2026-11-19"
cover: "/images/covers/posts/hands-on-large-language-models.jpg"
views: 145
faq:
  - q: "Ai nên đọc Hands-On LLM?"
    a: "Người học trực quan — những ai đọc lý thuyết khô khan dễ mất động lực. Nếu đã đọc bài The Illustrated Transformer của Jay Alammar và thấy cách giải thích bằng hình hiệu quả thì đây là bản đầy đủ của phong cách đó."
  - q: "Sách này có thay thế được LLMs-from-scratch không?"
    a: "Không — chúng bổ sung cho nhau. Hands-On LLM giúp bạn hiểu nhanh khái niệm bằng hình ảnh và code mẫu để dùng model; LLMs-from-scratch cho bạn tự xây từng tầng để hiểu sâu cơ chế. Người học hiệu quả thường đi Hands-On trước, from-scratch sau."
  - q: "Nội dung có cập nhật không?"
    a: "Repo notebook trên GitHub (30.000+ sao) được cộng đồng cập nhật theo phiên bản thư viện mới; phần khái niệm trong sách (kiến trúc transformer, attention, embedding) ít lỗi thời vì là nền tảng ổn định của lĩnh vực."
---

Trong nhóm tài nguyên LLM được biên tập tốt, có một nhánh riêng dành cho **người học trực quan**: [Hands-On Large Language Models](https://github.com/HandsOnLLM/Hands-On-Large-Language-Models) của Jay Alammar (tác giả series "The Illustrated Transformer" nổi tiếng) và Maarten Grootendorst. Repo kèm sách đạt **30.000+ sao**, điểm mạnh rõ nhất là 275+ hình minh họa tự vẽ — giải thích kiến trúc và pipeline bằng sơ đồ trước khi vào code.

Nói cách khác: đây là tài nguyên "đọc hình để hiểu, chạy notebook để chắc" — đối xứng hoàn toàn với cách "tự xây từng dòng" của LLMs-from-scratch.

<div style="margin:1.6em 0;">
  <span class="level-badge level-badge--mid">🟡 Trung cấp</span>
  <span class="level-badge">🖼️ Trực quan hóa</span>
  <span class="level-badge">⏱️ 3–5 tuần</span>
</div>

## Cấu trúc nội dung theo pipeline

<div class="lesson-grid">
  <div class="lesson-card">
    <div class="lc-icon">🔤</div>
    <p class="lc-title">Phần nền — Token & embedding</p>
    <p class="lc-desc">Tokenization, word embedding, contextual embedding — vì sao cùng một từ có nhiều vector khác nhau theo ngữ cảnh.</p>
  </div>
  <div class="lesson-card">
    <div class="lc-icon">🏗️</div>
    <p class="lc-title">Phần giữa — Kiến trúc</p>
    <p class="lc-desc">Attention và transformer được giải thích bằng sơ đồ luồng dữ liệu, gồm cả các biến thể encoder-only và decoder-only.</p>
  </div>
  <div class="lesson-card">
    <div class="lc-icon">🛠️</div>
    <p class="lc-title">Phần sau — Ứng dụng</p>
    <p class="lc-desc">Semantic search, classification, clustering, RAG, fine-tuning — mỗi ứng dụng một notebook chạy được.</p>
  </div>
</div>

## Ba phần học kỹ nhất

<ol class="steps">
  <li>
    <p class="st-title">Embedding — "tọa độ ý nghĩa" của văn bản</p>
    <p class="st-desc">Phần giá trị nhất với người làm ứng dụng: sentence embedding biến câu thành vector có tính chất "gần nhau nghĩa gần nhau". Đây là nền của semantic search, clustering và RAG — hiểu được hình minh họa nghĩa là thiết kế được hệ thống retrieval tốt hơn.</p>
  </li>
  <li>
    <p class="st-title">Attention qua sơ đồ</p>
    <p class="st-desc">Thay vì công thức khô, luồng Q-K-V được vẽ thành sơ đồ từng bước. Cách này giúp bạn giải thích lại attention cho đồng nghiệp không kỹ thuật — kỹ năng presentation quan trọng trong công việc thực tế.</p>
  </li>
  <li>
    <p class="st-title">RAG end-to-end</p>
    <p class="st-desc">Từ chunking, embedding, vector store, retrieval đến generation — pipeline đủ để dựng một hệ thống hỏi–đáp tài liệu nội bộ. Có loạt bài riêng của LearnWithHuy đi sâu phần này.</p>
  </li>
</ol>

## Khái niệm đáng ghi nhớ

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">📍</span>
    <h3 class="cc-name">Contextual embedding khác word embedding cố định</h3>
  </div>
  <div class="cc-body">
    <p>Word2Vec cho mỗi từ một vector bất kể ngữ cảnh — "đề" trong "đề tài" và "đề nghị" sẽ cùng một vector. Transformer tạo contextual embedding: vector của mỗi token được tính lại theo các token xung quanh. Đây là điểm khác biệt nền tảng mà mọi so sánh model cũ/mới đều quy về.</p>
  </div>
</div>

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">🧲</span>
    <h3 class="cc-name">Semantic search = embedding + đo khoảng cách</h3>
  </div>
  <div class="cc-body">
    <p>Thay vì khớp từ khóa, semantic search embed cả câu hỏi và tài liệu vào cùng không gian vector rồi tìm gần nhất (cosine similarity). Lý do có thể hoạt động: embedding từ cùng một model đặt các câu cùng ý nghĩa gần nhau dù khác từ ngữ — kể cả khác ngôn ngữ với model đa ngôn ngữ.</p>
  </div>
</div>

## Checklist thực hành

<ul class="checklist">
  <li>Chạy notebook chương embedding — thử search tiếng Việt trên một corpus nhỏ</li>
  <li>Vẽ lại sơ đồ attention bằng tay từ hình trong sách (không chụp màn hình)</li>
  <li>Làm notebook RAG end-to-end với một bộ tài liệu của riêng bạn</li>
  <li>So sánh hai embedding model khác nhau trên cùng bộ câu hỏi — ghi chênh lệch retrieval quality</li>
  <li>Thử fine-tune embedding model cho domain chuyên ngành của bạn và đo cải thiện</li>
</ul>

<div class="quiz">
  <p class="quiz-label">Kiểm tra nhanh</p>
  <details>
    <summary>Vì sao chunking sai làm hỏng RAG dù embedding model tốt?</summary>
    <p class="q-answer"><strong>Đáp án:</strong> Embedding đại diện cho nội dung của chunk — chunk quá nhỏ thì thiếu ngữ cảnh, quá lớn thì vector bị "pha loãng" nhiều chủ đề cùng lúc, retrieval tìm ra chunk chứa câu trả lời nhưng kèm nhiễu. Chunking là bước thiết kế quyết định chất lượng retrieval, trước cả việc chọn model.</p>
  </details>
  <details>
    <summary>Nên dùng encoder-only hay decoder-only cho bài toán embedding?</summary>
    <p class="q-answer"><strong>Đáp án:</strong> Encoder-only (kiểu BERT và các sentence-transformer) vì có cơ chế bidirectional attention — mỗi token nhìn được cả hai chiều, tạo embedding ngữ cảnh đầy đủ hơn cho bài toán hiểu văn bản. Decoder-only tối ưu cho sinh văn bản.</p>
  </details>
</div>

<div class="callout callout--info">
  <span class="co-icon">📖</span>
  <div class="co-body">
    <span class="co-title">Đọc thế nào cho hiệu quả</span>
    <p>Mỗi chương có cấu trúc: khái niệm bằng hình → code mẫu → notebook thực hành đầy đủ trên GitHub. Nên mở song song: đọc vài trang, chạy notebook tương ứng ngay. Phần hình minh họa rất đáng screenshot lưu làm tài liệu trình bày nội bộ.</p>
  </div>
</div>

Chuỗi bài liên quan: [Xây dựng LLM từ scratch](/bai-viet/xay-dung-llm-tu-scratch/) cho phần cơ chế sâu, [llm-engineer-roadmap](/bai-viet/llm-engineer-roadmap-mlabonne/) cho lộ trình nghề, và [LLM hoạt động như thế nào?](/bai-viet/llm-hoat-dong-nhu-the-nao/) cho nền khái niệm.

<div class="src-grid">
  <a class="src-card" href="https://github.com/HandsOnLLM/Hands-On-Large-Language-Models">
    <span class="sc-tag">Repo notebook</span>
    <p class="sc-name">HandsOnLLM</p>
    <p class="sc-desc">30k+ sao — toàn bộ notebook từng chương, chạy được trên Colab.</p>
  </a>
  <a class="src-card" href="https://www.oreilly.com/library/view/hands-on-large-language/9781098130957/">
    <span class="sc-tag">Sách gốc</span>
    <p class="sc-name">O'Reilly</p>
    <p class="sc-desc">Bản chính thức của Jay Alammar & Maarten Grootendorst.</p>
  </a>
</div>

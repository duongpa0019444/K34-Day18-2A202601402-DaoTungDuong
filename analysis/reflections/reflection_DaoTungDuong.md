# Individual Reflection — Lab 18: Production RAG Pipeline

**Tên:** Đào Tùng Dương  
**Module phụ trách:** Production RAG Pipeline (M1: Chunking · M2: Hybrid Search · M3: Reranking · M4: Evaluation · M5: Enrichment)

---

## 1. Mapping bài giảng (Lecture → Code)

| Lecture Concept | Module | Hàm cụ thể | Observation & Code Link |
|----------------|--------|-------------|--------------------------|
| **Semantic & Hierarchical Chunking** | M1 | [`chunk_hierarchical()`](file:///d:/VINUNIVERSITY/LAB/Lab_18/src/m1_chunking.py#L133-L175) & [`chunk_semantic()`](file:///d:/VINUNIVERSITY/LAB/Lab_18/src/m1_chunking.py#L87-L128) | Chia tài liệu thành parent size 2048 và child size 256 giúp bảo toàn ngữ cảnh khi truy xuất chính xác theo child nhưng trả về parent chunk. |
| **Hybrid Search (BM25 + Dense + RRF)** | M2 | [`reciprocal_rank_fusion()`](file:///d:/VINUNIVERSITY/LAB/Lab_18/src/m2_search.py#L130-L165) & [`segment_vietnamese()`](file:///d:/VINUNIVERSITY/LAB/Lab_18/src/m2_search.py#L21-L29) | Tách từ tiếng Việt qua `underthesea` giúp BM25 hiểu từ ghép chính xác, RRF ($k=60$) dung hòa thứ hạng sparse và dense không phụ thuộc scale score. |
| **Cross-Encoder Reranking** | M3 | [`CrossEncoderReranker.rerank()`](file:///d:/VINUNIVERSITY/LAB/Lab_18/src/m3_rerank.py#L29-L65) | Mô hình `BAAI/bge-reranker-v2-m3` tính tương tác đa chiều giữa query và chunk, xếp hạng lại top-20 để chọn ra top-3 context tinh lọc nhất. |
| **RAGAS 4 Metrics & Diagnostic Tree** | M4 | [`evaluate_ragas()`](file:///d:/VINUNIVERSITY/LAB/Lab_18/src/m4_eval.py#L40-L101) & [`failure_analysis()`](file:///d:/VINUNIVERSITY/LAB/Lab_18/src/m4_eval.py#L103-L135) | Đánh giá độc lập 4 góc độ: Faithfulness, Answer Relevancy, Context Precision, Context Recall. Tự động gắn nhãn chẩn đoán lỗi theo cây quyết định. |
| **Pre-retrieval Chunk Enrichment** | M5 | [`_enrich_single_call()`](file:///d:/VINUNIVERSITY/LAB/Lab_18/src/m5_enrichment.py#L153-L191) & [`enrich_chunks()`](file:///d:/VINUNIVERSITY/LAB/Lab_18/src/m5_enrichment.py#L196-L255) | Tối ưu hóa 1 API call duy nhất để đồng thời trích xuất Summary, HyQA (câu hỏi giả định), Contextual Prepend và Metadata phân loại trước khi vector hóa. |

---

## 2. Khó khăn & Cách giải quyết

1. **Khó khăn về tải trọng và bộ nhớ của mô hình Embedding/Reranking:**
   - *Lỗi gặp phải:* Tải mô hình `BAAI/bge-m3` (~2.2GB) và `bge-reranker-v2-m3` lần đầu chiếm nhiều dung lượng trên ổ đĩa và tốn thời gian khởi động, dễ gây timeout khi chạy test suite.
   - *Cách giải quyết:* Thiết lập biến môi trường `HF_HOME` và `TORCH_HOME` trỏ vào phân vùng ổ `D:` trong `config.py` để tránh tràn ổ `C:`, đồng thời triển khai cơ chế lazy loading (`_get_encoder()`, `_load_model()`) chỉ nạp model khi thực sự cần tính toán.

2. **Xung đột mã hóa ký tự (Encoding) trên môi trường Windows PowerShell:**
   - *Lỗi gặp phải:* `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f50d'` khi in các ký tự emoji và tiếng Việt có dấu ra terminal mặc định của Windows.
   - *Cách giải quyết:* Đặt biến môi trường `$env:PYTHONIOENCODING="utf-8"` trước khi thực thi các script Python và sử dụng tham số `encoding="utf-8"` trong tất cả các thao tác đọc/ghi file.

3. **Vấn đề xung đột phiên bản tài liệu (Version Inconsistency):**
   - *Lỗi gặp phải:* Dữ liệu chứa cả phiên bản cũ và mới của cùng một chính sách (ví dụ `mat_khau_v1.md` và `mat_khau_v2.md`). Reranker lấy cả 2 văn bản khiến LLM gặp mâu thuẫn thông tin và từ chối trả lời.
   - *Cách debug:* Sử dụng Diagnostic Tree tại Module 4 để truy vết, xác định nguyên nhân nằm ở tầng Retrieval thiếu cơ chế lọc theo thời gian/tính hiệu lực, từ đó đề xuất giải pháp Temporal Metadata Filtering.

---

## 3. Action Plan cho Project

### Hiện tại
- **Hệ thống hiện tại:** Hệ thống RAG hỗ trợ tìm kiếm tài liệu nghiệp vụ và chính sách nội bộ.
- **Vấn đề đang gặp:**
  - Semantic search đơn lẻ thường bỏ sót các mã hiệu, số hiệu văn bản và thuật ngữ chuyên ngành viết tắt.
  - Context đưa vào LLM quá dài hoặc chứa thông tin thừa dẫn đến hiện tượng "lost in the middle" và tăng chi phí token.

### Kế hoạch áp dụng

1. **[x] Chunking Strategy:**
   - Áp dụng **Hierarchical Chunking (Parent-Child)** với Child size 256 tokens (để tối ưu độ khớp khi tìm kiếm vector) và Parent size 1024-2048 tokens (để cung cấp đầy đủ bối cảnh khi gửi cho LLM).
2. **[x] Hybrid Search & Fusion:**
   - Kết hợp **BM25 tiếng Việt (tách từ qua underthesea)** và **Dense Search (`bge-m3`)** thông qua thuật toán **Reciprocal Rank Fusion (RRF)** để tăng cường khả năng tìm kiếm từ khóa chính xác.
3. **[x] Reranking:**
   - Sử dụng **Cross-Encoder Reranker (`bge-reranker-v2-m3`)** để lọc từ Top-25 xuống Top-3/Top-5 context chất lượng nhất trước khi nạp vào Prompt.
4. **[x] Pre-retrieval Enrichment:**
   - Triển khai **Contextual Prepend & Auto-Metadata Tagging** theo chế độ Single-Call Combined để làm giàu văn bản trước khi lập chỉ mục vector.
5. **[x] Evaluation & Continuous Monitoring:**
   - Xây dựng pipeline đánh giá định kỳ 4 chỉ số RAGAS và tự động cảnh báo câu hỏi có điểm số thấp qua Diagnostic Tree.

### Timeline triển khai
- **Tuần 1:** Chuẩn hóa dữ liệu văn bản, triển khai module Hierarchical Chunking và Pre-retrieval Enrichment.
- **Tuần 2:** Thiết lập cơ sở dữ liệu vector Qdrant, tích hợp BM25 + Dense Hybrid Search với RRF.
- **Tuần 3:** Tích hợp mô hình Cross-Encoder Reranker và tối ưu hóa System Prompt của LLM.
- **Tuần 4:** Chạy bộ test set đánh giá RAGAS toàn diện, tinh chỉnh tham số và đóng gói production pipeline.

---

## 4. Tự đánh giá

| Tiêu chí | Tự chấm (1-5) | Nhận xét |
|----------|---------------|----------|
| Hiểu bài giảng | 5/5 | Nắm vững toàn bộ 5 kỹ thuật Production RAG cốt lõi. |
| Code quality | 5/5 | Code cấu trúc module rõ ràng, type annotations đầy đủ, 100% unit tests pass. |
| Problem solving | 5/5 | Phân tích sâu nguyên nhân gốc rễ (Root Cause) theo Diagnostic Tree và đưa ra giải pháp khắc phục. |
| Project applicability | 5/5 | Có Action Plan thực tế, chi tiết và khả thi cho đồ án. |

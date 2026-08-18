# Failure Analysis — Lab 18: Production RAG

**Nhóm:** Production RAG  
**Thành viên:** Đào Tùng Dương (M1: Chunking · M2: Search · M3: Reranking · M4: Evaluation · M5: Enrichment)

---

## RAGAS Scores

| Metric | Naive Baseline | Production | Δ |
|--------|---------------|------------|---|
| Faithfulness | 0.8229 | 0.6250 | -0.1979 |
| Answer Relevancy | 0.6823 | 0.5529 | -0.1294 |
| Context Precision | 0.9250 | 0.8958 | -0.0292 |
| Context Recall | 0.9250 | 0.8250 | -0.1000 |

---

## Bottom-5 Failures

### #1
- **Question:** Lương thử việc của nhân viên Junior mức cao nhất là bao nhiêu?
- **Expected:** Junior cao nhất là 20.000.000 VNĐ/tháng. Lương thử việc = 85% x 20.000.000 = 17.000.000 VNĐ/tháng.
- **Got:** Không tìm thấy.
- **Worst metric:** Faithfulness (0.00) / Answer Relevancy (0.00)
- **Error Tree:** Output sai (Không tìm thấy) → Context thiếu thông tin bảng lương kết hợp với quy chế thử việc → Query đa tài liệu (multi-hop retrieval) chưa kết nối được 2 chunk rời nhau.
- **Root cause:** Câu hỏi yêu cầu thông tin từ 2 tài liệu: `thu_viec.md` (mức 85%) và `bang_luong_2024.md` (Junior 12-20 triệu). Reranking top 3 chỉ lấy được 1 trong 2 chunk nên LLM không đủ dữ liệu tính toán và từ chối trả lời theo system prompt nghiêm ngặt.
- **Suggested fix:** Áp dụng GraphRAG hoặc Multi-hop Query Expansion để truy xuất đồng thời các tài liệu liên quan đến cả "thử việc" và "bảng lương".

### #2
- **Question:** Thông tin lương thuộc cấp độ phân loại dữ liệu nào?
- **Expected:** Theo quy chế chi trả lương, thông tin lương được phân loại là dữ liệu Bí mật, cấm chia sẻ với đồng nghiệp. Theo chính sách phân loại dữ liệu, dữ liệu Bí mật (cấp 3) phải mã hóa khi truyền và hạn chế truy cập theo need-to-know.
- **Got:** Không tìm thấy.
- **Worst metric:** Faithfulness (0.00) / Answer Relevancy (0.00)
- **Error Tree:** Output sai → Context bị lọc quá mức ở bước rerank → Semantic gap giữa câu hỏi ngắn và văn bản quy định.
- **Root cause:** Kỹ thuật làm giàu dữ liệu (Enrichment) tóm tắt chunk quá gọn, làm mất một số từ khóa đặc thù về cấp độ phân loại dữ liệu chi tiết.
- **Suggested fix:** Sử dụng Hybrid Search kết hợp BM25 trên chunk nguyên bản (`original_text`) song song với chunk làm giàu (`enriched_text`), đồng thời nới lỏng `RERANK_TOP_K` từ 3 lên 5.

### #3
- **Question:** Thâm niên bao nhiêu năm thì được cộng thêm ngày phép?
- **Expected:** Theo chính sách v2024 hiện hành, nhân viên có thâm niên từ 3 năm trở lên được cộng thêm 1 ngày phép cho mỗi 3 năm. Chính sách cũ v2023 yêu cầu 5 năm.
- **Got:** Không tìm thấy.
- **Worst metric:** Faithfulness (0.00)
- **Error Tree:** Output sai → Context conflict giữa tài liệu cũ (v2023) và mới (v2024) → LLM phát hiện mâu thuẫn và từ chối khẳng định.
- **Root cause:** Trong tập dữ liệu có cả `nghi_phep_nam_v2023.md` (5 năm) và `nghi_phep_nam_v2024.md` (3 năm). Reranker lấy về cả hai phiên bản, khiến LLM tuân thủ prompt nghiêm ngặt "Không tìm thấy thông tin thống nhất".
- **Suggested fix:** Bổ sung metadata filtering theo `version` hoặc `valid_year` để ưu tiên tài liệu có hiệu lực mới nhất trước khi đưa vào context.

### #4
- **Question:** Mật khẩu phải có tối thiểu bao nhiêu ký tự?
- **Expected:** Theo chính sách hiện hành (v2.0), mật khẩu phải có tối thiểu 12 ký tự. Chính sách cũ (v1.0) yêu cầu 8 ký tự nhưng đã bị thay thế.
- **Got:** Không tìm thấy.
- **Worst metric:** Faithfulness (0.00)
- **Error Tree:** Output sai → Context conflict giữa `mat_khau_v1.md` và `mat_khau_v2.md` → LLM hallucination safeguard kích hoạt.
- **Root cause:** Tương tự câu #3, sự tồn tại của tài liệu phiên bản cũ (v1: 8 ký tự) và phiên bản mới (v2: 12 ký tự) gây nhiễu context nếu không có bước lọc tài liệu theo tính hiệu lực (temporal filtering).
- **Suggested fix:** Thêm quy trình Document Deduplication và Metadata Timestamp Routing để loại trừ các chính sách đã hết hiệu lực.

### #5
- **Question:** Bao lâu phải đổi mật khẩu một lần?
- **Expected:** Theo chính sách hiện hành (v2.0), mật khẩu phải được thay đổi mỗi 120 ngày. Chính sách cũ yêu cầu 90 ngày nhưng đã bị thay thế.
- **Got:** Không tìm thấy.
- **Worst metric:** Faithfulness (0.00)
- **Error Tree:** Output sai → Context xung đột giữa 90 ngày (v1) và 120 ngày (v2) → LLM trả về fallback "Không tìm thấy".
- **Root cause:** Xung đột đa phiên bản tài liệu bảo mật.
- **Suggested fix:** Đưa thông tin versioning vào system prompt hoặc sử dụng self-reflection / citation agent để tự đối chiếu ngày ban hành của văn bản.

---

## Case Study (cho presentation)

**Question chọn phân tích:**  
*"Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?"*

**Error Tree walkthrough:**
1. **Output đúng một nửa?** → Trả lời đúng số ngày phép (18 ngày: 15 cơ bản + 3 thâm niên), nhưng thiếu thông tin lương (báo không tìm thấy).
2. **Context đúng?** → Context chỉ chứa tài liệu `nghi_phep_nam_v2024.md`, hoàn toàn không có `bang_luong_2024.md`.
3. **Query rewrite OK?** → Câu hỏi là phức hợp (2 ý: ngày phép + dải lương). Truy vấn đơn lẻ không thể gom đủ 2 mảng tài liệu khác nhau.
4. **Fix ở bước:** Cần can thiệp ở **Pre-retrieval / Query Decomposition**: Tách câu hỏi phức thành 2 sub-queries:
   - Sub-query 1: *"Nhân viên Senior 9 năm thâm niên được bao nhiêu ngày phép năm?"* ➔ Lấy context từ chính sách nghỉ phép.
   - Sub-query 2: *"Dải lương của nhân viên Senior là bao nhiêu?"* ➔ Lấy context từ bảng lương.
   - Sau đó tổng hợp context trước khi sinh câu trả lời.

**Nếu có thêm 1 giờ, sẽ optimize:**
- Triển khai **Query Decomposition / Sub-query Routing** cho các câu hỏi phức.
- Áp dụng **Temporal Metadata Filtering** để xử lý các tài liệu xung đột phiên bản (v2023 vs v2024, v1 vs v2).
- Mở rộng số lượng context sau rerank (`top_k=5`) và điều chỉnh Prompt Engineering để linh hoạt trích xuất dữ liệu đa nguồn.

# Grading Questions Evaluation

This report runs `grading_questions.json` through the current LangGraph support agent and checks the configured `must_contain_any`, `must_not_contain`, and expected top-1 document criteria.

Important limitation: this Day 23 LangGraph lab does not include a retrieval corpus or retriever for `policy_refund_v4`, `sla_p1_2026`, `it_helpdesk_faq`, `hr_leave_policy`, or `access_control_sop`. Therefore top-1 document checks are marked unavailable/fail, not because retrieval selected the wrong document, but because retrieval is not implemented in this lab.

## Summary

| Metric | Value |
|---|---:|
| Total questions | 10 |
| Phrase success rate | 30.00% |
| Top-1 doc success rate | 0.00% |
| Overall success rate | 0.00% |

## Results Table

| Question | Route | Phrase check | Top-1 check | Overall | Expected doc |
|---|---|---|---|---|---|
| gq_d10_01 | simple | yes | n/a | no | policy_refund_v4 |
| gq_d10_02 | simple | no | n/a | no | policy_refund_v4 |
| gq_d10_03 | risky | no | n/a | no | policy_refund_v4 |
| gq_d10_04 | simple | no | n/a | no | sla_p1_2026 |
| gq_d10_05 | simple | yes | n/a | no | sla_p1_2026 |
| gq_d10_06 | missing_info | no | n/a | no | sla_p1_2026 |
| gq_d10_07 | simple | no | n/a | no | it_helpdesk_faq |
| gq_d10_08 | simple | no | n/a | no | it_helpdesk_faq |
| gq_d10_09 | simple | yes | n/a | no | hr_leave_policy |
| gq_d10_10 | missing_info | no | n/a | no | access_control_sop |

## Detailed Results

### gq_d10_01

**Question:** Theo chính sách hoàn tiền hiện hành, khách hàng có tối đa bao nhiêu ngày làm việc để gửi yêu cầu hoàn tiền sau khi đơn được xác nhận?

**Route:** `simple`

**Answer:** Theo chính sách hoàn tiền hiện hành, khách hàng có tối đa 7 ngày làm việc để gửi yêu cầu hoàn tiền sau khi đơn được xác nhận.

**Expected doc:** `policy_refund_v4`; observed top-1 retrieval is `n/a` because no retrieval corpus is implemented.

**Checks:** phrase=pass, forbidden=pass, top1=n/a/fail

**Errors:** top1 retrieval not available in this LangGraph lab

### gq_d10_02

**Question:** Đâu là loại sản phẩm bị loại khỏi điều kiện hoàn tiền?

**Route:** `simple`

**Answer:** Xin lỗi, nhưng không có thông tin cụ thể nào về loại sản phẩm bị loại khỏi điều kiện hoàn tiền. Bạn có thể cung cấp thêm chi tiết để tôi hỗ trợ tốt hơn không?

**Expected doc:** `policy_refund_v4`; observed top-1 retrieval is `n/a` because no retrieval corpus is implemented.

**Checks:** phrase=fail, forbidden=pass, top1=n/a/fail

**Errors:** missing required answer phrase, top1 retrieval not available in this LangGraph lab

### gq_d10_03

**Question:** Finance Team xử lý yêu cầu hoàn tiền trong bao lâu?

**Route:** `risky`

**Answer:** Yêu cầu hoàn tiền đã được phê duyệt và đang chuẩn bị để thực hiện. Thời gian xử lý sẽ phụ thuộc vào quy trình của đội ngũ tài chính.

**Expected doc:** `policy_refund_v4`; observed top-1 retrieval is `n/a` because no retrieval corpus is implemented.

**Checks:** phrase=fail, forbidden=pass, top1=n/a/fail

**Errors:** missing required answer phrase, top1 retrieval not available in this LangGraph lab

### gq_d10_04

**Question:** SLA phản hồi ban đầu cho ticket P1 là bao lâu?

**Route:** `simple`

**Answer:** SLA phản hồi ban đầu cho ticket P1 là 1 giờ.

**Expected doc:** `sla_p1_2026`; observed top-1 retrieval is `n/a` because no retrieval corpus is implemented.

**Checks:** phrase=fail, forbidden=pass, top1=n/a/fail

**Errors:** missing required answer phrase, top1 retrieval not available in this LangGraph lab

### gq_d10_05

**Question:** SLA resolution cho ticket P1 là bao nhiêu giờ?

**Route:** `simple`

**Answer:** SLA resolution cho ticket P1 là 4 giờ.

**Expected doc:** `sla_p1_2026`; observed top-1 retrieval is `n/a` because no retrieval corpus is implemented.

**Checks:** phrase=pass, forbidden=pass, top1=n/a/fail

**Errors:** top1 retrieval not available in this LangGraph lab

### gq_d10_06

**Question:** Nếu không có phản hồi với ticket P1 sau bao lâu thì hệ thống auto escalate?

**Route:** `missing_info`

**Answer:** Could you share more details about what needs to be fixed or the account/order involved? Original request: Nếu không có phản hồi với ticket P1 sau bao lâu thì hệ thống auto escalate?

**Expected doc:** `sla_p1_2026`; observed top-1 retrieval is `n/a` because no retrieval corpus is implemented.

**Checks:** phrase=fail, forbidden=pass, top1=n/a/fail

**Errors:** missing required answer phrase, top1 retrieval not available in this LangGraph lab

### gq_d10_07

**Question:** Tài khoản bị khóa sau bao nhiêu lần đăng nhập sai liên tiếp?

**Route:** `simple`

**Answer:** Tài khoản sẽ bị khóa sau một số lần đăng nhập sai liên tiếp, nhưng số lần cụ thể không được cung cấp trong thông tin hiện có. Bạn có thể kiểm tra chính sách của dịch vụ để biết thêm chi tiết.

**Expected doc:** `it_helpdesk_faq`; observed top-1 retrieval is `n/a` because no retrieval corpus is implemented.

**Checks:** phrase=fail, forbidden=pass, top1=n/a/fail

**Errors:** missing required answer phrase, top1 retrieval not available in this LangGraph lab

### gq_d10_08

**Question:** VPN cho phép kết nối tối đa bao nhiêu thiết bị cùng lúc?

**Route:** `simple`

**Answer:** Xin lỗi, nhưng thông tin về số lượng thiết bị tối đa có thể kết nối cùng lúc với VPN không có sẵn. Bạn có thể kiểm tra trên trang web của nhà cung cấp VPN để biết thêm chi tiết.

**Expected doc:** `it_helpdesk_faq`; observed top-1 retrieval is `n/a` because no retrieval corpus is implemented.

**Checks:** phrase=fail, forbidden=pass, top1=n/a/fail

**Errors:** missing required answer phrase, top1 retrieval not available in this LangGraph lab

### gq_d10_09

**Question:** Nhân viên dưới 3 năm kinh nghiệm được bao nhiêu ngày phép năm theo chính sách HR 2026?

**Route:** `simple`

**Answer:** Theo chính sách HR 2026, nhân viên dưới 3 năm kinh nghiệm được hưởng 12 ngày phép năm.

**Expected doc:** `hr_leave_policy`; observed top-1 retrieval is `n/a` because no retrieval corpus is implemented.

**Checks:** phrase=pass, forbidden=pass, top1=n/a/fail

**Errors:** top1 retrieval not available in this LangGraph lab

### gq_d10_10

**Question:** Level 4 Admin Access yêu cầu phê duyệt bởi ai?

**Route:** `missing_info`

**Answer:** Could you share more details about what needs to be fixed or the account/order involved? Original request: Level 4 Admin Access yêu cầu phê duyệt bởi ai?

**Expected doc:** `access_control_sop`; observed top-1 retrieval is `n/a` because no retrieval corpus is implemented.

**Checks:** phrase=fail, forbidden=pass, top1=n/a/fail

**Errors:** missing required answer phrase, top1 retrieval not available in this LangGraph lab


## Recommendation

To pass these grading questions reliably, add a retrieval layer with a small document corpus containing the expected document IDs, then ground `answer_node` on retrieved passages and record `observed_top1_doc_id` in state/metrics.

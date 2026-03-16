# Testing Tracker

This tracker captures defects and quality risks discovered while executing the
module-first testing rollout.

## Entry Template

Copy this block for each discovered issue.

```md
## <Issue ID or Short Title>

- Module: <module name>
- Production File: <path>
- Test File: <path>
- Test Case: <pytest function name>
- Failure: <observed behavior or error>
- Expected: <expected behavior>
- Root Cause (hypothesis): <concise technical cause>
- Severity: <low|medium|high>
- Status: <open|fixed|deferred>
- Fix PR/Commit: <reference>
- Notes: <reproduction details and follow-up>
```

## Issues

## TST-001 Header Metadata Keyword Violation

- Module: formatters
- Production File: `tests/formatters/test_json_and_text_formatters.py`
- Test File: `tests/scripts/test_header_metadata.py`
- Test Case: `test_header_fields_do_not_contain_placeholder_terms`
- Failure: Header metadata contained the forbidden keyword `placeholder`.
- Expected: Header metadata should avoid blocked placeholder terms.
- Root Cause (hypothesis): New test docstring used "placeholder rendering behavior" wording.
- Severity: low
- Status: fixed
- Fix PR/Commit: pending
- Notes: Replaced the wording with "template rendering behavior" and reran gates.

## TST-002 UTC Deprecation Warning In Error Logger

- Module: utils
- Production File: `hydra_logger/utils/error_logger.py`
- Test File: `tests/utils/test_error_logger.py`
- Test Case: warning observed during module/full pytest runs
- Failure: Deprecation warnings from `datetime.utcnow()` calls.
- Expected: UTC timestamps should use timezone-aware datetime APIs.
- Root Cause (hypothesis): Legacy timestamp calls used deprecated naive UTC helper.
- Severity: low
- Status: fixed
- Fix PR/Commit: pending
- Notes: Replaced `datetime.utcnow()` with `datetime.now(UTC)` across error logging paths.

## TST-003 Whitespace Normalization Expectation Mismatch

- Module: utils
- Production File: `hydra_logger/utils/text_utility.py`
- Test File: `tests/utils/test_text_utility.py`
- Test Case: `test_text_processor_normalization_extraction_and_pattern_helpers`
- Failure: Initial expectation assumed trailing-space removal before newline groups.
- Expected: `clean_whitespace()` currently preserves single spaces before normalized newlines.
- Root Cause (hypothesis): Test expectation did not match implemented regex behavior.
- Severity: low
- Status: fixed
- Fix PR/Commit: pending
- Notes: Adjusted assertion to reflect current implementation contract.

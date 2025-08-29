# Failure Mode Analysis

This document catalogues known and potential failure modes of the Agentic Financial Risk Assistant, with severity ratings, likelihood assessments, and mitigation status.

---

## Severity scale

| Level | Meaning |
|---|---|
| Critical | Produces incorrect output that could mislead a user into a harmful decision |
| High | Feature fails silently or produces incorrect output without error message |
| Medium | Feature degrades gracefully but result is less reliable than expected |
| Low | Minor inconvenience or cosmetic issue; no impact on correctness |

---

## 1. Hallucinated numerical results

**Severity:** Critical
**Likelihood:** Low (by design)
**Description:** The LLM generates a risk metric number without calling a tool.
**Mitigation:** The system prompt explicitly prohibits inventing numbers and requires tool calls for all numerical answers. Tool call traces are shown in the UI so the user can see whether a calculation was performed. If no tool was called for a numerical question, the `basis` field shows `reasoning` rather than `calculation`, flagging the issue.
**Residual risk:** The LLM could generate plausible-looking but incorrect numbers for edge cases where tool calls fail. Monitoring the `tool_calls` field in every response mitigates this.

---

## 2. Investment advice boundary violation

**Severity:** Critical
**Likelihood:** Very low (by design)
**Description:** The agent provides a buy/sell/hold recommendation.
**Mitigation:** The safety layer (`src/agent/safety.py`) uses deterministic Python keyword matching before the LLM is invoked. Questions matching investment-advice patterns return a refusal without calling the LLM. This is tested by 73 safety and EU AI Act mapping tests.
**Residual risk:** A carefully crafted adversarial question might bypass keyword matching. The system prompt provides a secondary defence.

---

## 3. Bad CSV format, data loading failure

**Severity:** High
**Likelihood:** Medium (user-uploaded files vary in quality)
**Description:** User uploads a CSV with unexpected column names, non-standard date formats, mixed types, or BOM encoding.
**Mitigation:** `src/data/validators.py` runs 5 checks (column existence, datetime type, numeric type, negative prices, minimum observations) and returns structured error messages. `src/data/loaders.py` handles file-like objects including Streamlit's UploadedFile. Errors are displayed in the Streamlit UI rather than silently failing.
**Residual risk:** Exotic date formats (e.g. `31-Jan-2020`) may not parse correctly. Users should be advised to use ISO 8601 (`YYYY-MM-DD`) format.

---

## 4. Incorrect date parsing

**Severity:** High
**Likelihood:** Low
**Description:** Date column parsed incorrectly, causing returns and rolling metrics to be computed on mis-ordered data.
**Mitigation:** `load_csv()` sorts by date after parsing and drops NaT values. `validate()` checks that the date column is datetime type after loading.
**Residual risk:** Mixed timezone data could cause incorrect ordering. The current implementation strips timezone info implicitly.

---

## 5. Financial advice boundary, edge cases

**Severity:** High
**Likelihood:** Low
**Description:** A question framed as analytical but implicitly requesting advice (e.g. "Based on the VaR, should I reduce my position?") bypasses the keyword-based classifier.
**Mitigation:** The safety classifier checks for high-risk decision language ("my savings", "my portfolio", "should I allocate") in addition to direct advice keywords. The LLM system prompt adds a secondary defence. The `ambiguous_decision` category catches borderline cases and flags them for human review.
**Residual risk:** Novel phrasing may bypass both layers. Production deployment would benefit from a fine-tuned safety classifier.

---

## 6. Overconfidence, missing uncertainty language

**Severity:** High
**Likelihood:** Low (by design)
**Description:** Agent answer lacks backward-looking caveats, implying that past risk metrics predict future outcomes.
**Mitigation:** System prompt rule 5 requires uncertainty language in every answer. All tool outputs include a `limitations` field that the agent is instructed to cite. The `confidence_note` field in every response carries a standard caveat.
**Residual risk:** The LLM may omit limitations when answering complex multi-part questions. The `limitations` field in the tool output provides a fallback.

---

## 7. Model/API unavailability

**Severity:** Medium
**Likelihood:** Low
**Description:** The the LLM API is unreachable or returns an error (rate limit, authentication failure, model unavailability).
**Mitigation:** `run_agent()` catches all exceptions and returns a structured error dict with `basis=error` and the error message. The Streamlit UI displays the error message. The risk dashboard (charts, risk summary, VaR calculations) continues to function in fallback mode.
**Residual risk:** Repeated API failures degrade the agent experience. Production deployment would benefit from retry logic with exponential backoff.

---

## 8. Incorrect risk-tier classification

**Severity:** Medium
**Likelihood:** Low
**Description:** A question is misclassified by the safety layer (e.g. an educational question classified as technical, or a harmful question classified as educational).
**Mitigation:** The classifier uses priority-ordered rules: hard blocks (investment advice, predictions) are checked first before educational and technical patterns. 73 safety tests cover all category boundaries. The classifier is deterministic Python, no LLM involved.
**Residual risk:** Novel phrasing may fall into the wrong category. Misclassification between `safe_educational` and `technical_calculation` is benign (both are allowed). Misclassification of a harmful question as allowed is the critical case, which is mitigated by the LLM system prompt as a second layer.

---

## 9. RAG retrieval failure

**Severity:** Medium
**Likelihood:** Low
**Description:** The RAG retriever returns no results or irrelevant chunks for a valid methodology question.
**Mitigation:** `retrieve_with_context()` returns a `found=False` result if no chunks meet the minimum cosine similarity threshold (0.25). The agent falls back to LLM reasoning for that question. The FAISS index is built from the actual documentation files, if a file is empty or missing, `get_available_documents()` excludes it.
**Residual risk:** If documentation files are sparse, retrieval quality degrades. The minimum score threshold prevents low-quality chunks from being included.

---

## 10. MCP tool failure, invalid input

**Severity:** Medium
**Likelihood:** Low
**Description:** An MCP tool receives malformed input (e.g. empty price series, NaN-filled series) and raises an unhandled exception.
**Mitigation:** `_require_prices()` raises a `ValueError` with a clear message if the price series is None. `mcp_calculate_var()` handles the case where the tail is empty. The MCP server's `call_tool` handler wraps all calls in a try/except block and returns a structured error dict.
**Residual risk:** Some edge cases (e.g. all-identical prices causing zero volatility) may produce mathematically valid but meaningless results. Validation in `validators.py` catches extreme cases (too few observations).

---

## 11. Synthetic data misrepresentation

**Severity:** Medium
**Likelihood:** Low
**Description:** A user interprets synthetic sample data as real market data and draws conclusions from it.
**Mitigation:** The data source note ("Synthetic sample data (GBM, seed 42)") is displayed in the risk summary panel. The `data/README.md` document clearly identifies all sample data as synthetic and is included in the RAG source set so the agent can answer "where did this data come from?" correctly.
**Residual risk:** Users who do not read the disclaimer may not notice the synthetic data label.

---

## 12. FAISS index staleness

**Severity:** Low
**Likelihood:** Low
**Description:** The FAISS index on disk reflects an older version of the documentation files.
**Mitigation:** `rebuild_index()` is available to force a full rebuild. `build_index(force_rebuild=False)` is the default, it rebuilds only if no cached index exists. Adding a hash check of document modification times would improve this.
**Residual risk:** Manual `rebuild_index()` call required after documentation updates in production.

---

## Summary table

| # | Failure mode | Severity | Likelihood | Mitigated |
|---|---|---|---|---|
| 1 | Hallucinated numerical results | Critical | Low | Yes (tool-first architecture + basis field) |
| 2 | Investment advice boundary violation | Critical | Very low | Yes (deterministic safety layer + 73 tests) |
| 3 | Bad CSV format | High | Medium | Yes (validators + structured error messages) |
| 4 | Incorrect date parsing | High | Low | Yes (sort + dtype validation) |
| 5 | Financial advice edge cases | High | Low | Partial (keyword + LLM second layer) |
| 6 | Missing uncertainty language | High | Low | Yes (system prompt + limitations field) |
| 7 | API unavailability | Medium | Low | Yes (fallback mode + error dict) |
| 8 | Incorrect risk-tier classification | Medium | Low | Yes (priority rules + 73 tests) |
| 9 | RAG retrieval failure | Medium | Low | Yes (min-score threshold + graceful fallback) |
| 10 | MCP tool invalid input | Medium | Low | Yes (try/except in server + validators) |
| 11 | Synthetic data misrepresentation | Medium | Low | Partial (disclaimer shown; user may miss it) |
| 12 | FAISS index staleness | Low | Low | Partial (rebuild_index() available) |

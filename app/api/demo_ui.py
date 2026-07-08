from fastapi.responses import HTMLResponse


def render_demo_ui() -> HTMLResponse:
    return HTMLResponse(
        """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>rag-eval-lab demo</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #172033;
      --muted: #5f6f84;
      --line: #d8e1ec;
      --panel: #f6f8fb;
      --accent: #126c7a;
      --accent-strong: #0f5864;
      --bad: #b33636;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: #ffffff;
      font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 22px 46px;
    }
    header {
      border-bottom: 1px solid var(--line);
      margin-bottom: 18px;
      padding-bottom: 16px;
    }
    h1, h2, h3 { line-height: 1.15; margin: 0; }
    h1 { font-size: 30px; }
    h2 { font-size: 18px; }
    h3 { font-size: 15px; }
    label {
      color: #2f3b4f;
      display: block;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 6px;
    }
    textarea, input, select, button {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 7px;
      font: inherit;
    }
    textarea, input, select {
      background: #ffffff;
      color: var(--ink);
      padding: 10px 11px;
    }
    textarea {
      min-height: 96px;
      resize: vertical;
    }
    button {
      background: var(--accent);
      border-color: var(--accent);
      color: #ffffff;
      cursor: pointer;
      font-weight: 750;
      padding: 10px 12px;
    }
    button:hover { background: var(--accent-strong); }
    button:disabled {
      background: #8796aa;
      border-color: #8796aa;
      cursor: not-allowed;
    }
    code {
      background: #eef3f7;
      border-radius: 4px;
      padding: 1px 5px;
    }
    .toolbar {
      display: grid;
      gap: 14px;
      grid-template-columns: minmax(280px, 1fr) 220px 120px;
      align-items: end;
    }
    .question-block { grid-column: 1 / -1; }
    .strategy-block { grid-column: 1 / -1; }
    .strategy-grid {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      margin-top: 10px;
    }
    .strategy-option {
      align-items: center;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 7px;
      display: flex;
      gap: 8px;
      min-height: 42px;
      padding: 9px 10px;
    }
    .strategy-option input {
      flex: 0 0 auto;
      width: auto;
    }
    .actions {
      display: grid;
      gap: 10px;
      grid-template-columns: minmax(180px, 220px) 1fr;
      margin-top: 14px;
      align-items: center;
    }
    .status {
      color: var(--muted);
      min-height: 22px;
    }
    .results {
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      margin-top: 20px;
    }
    .result-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      min-width: 0;
      overflow: hidden;
    }
    .result-head {
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 10px;
      padding: 12px 14px;
    }
    .runtime {
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }
    .result-body { padding: 14px; }
    .answer {
      margin: 0 0 12px;
      min-height: 72px;
    }
    .metric-strip {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(3, 1fr);
      margin-bottom: 14px;
    }
    .metric {
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 9px;
    }
    .metric span {
      color: var(--muted);
      display: block;
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 2px;
    }
    .metric strong { font-size: 18px; }
    .list {
      display: grid;
      gap: 8px;
      margin: 8px 0 14px;
      padding: 0;
    }
    .list li {
      border-left: 3px solid var(--accent);
      display: block;
      padding: 2px 0 2px 9px;
    }
    .snippet {
      color: var(--muted);
      display: block;
      font-size: 13px;
      margin-top: 3px;
    }
    .empty {
      color: var(--muted);
      margin: 18px 0 0;
      text-align: center;
    }
    .error {
      border-color: #f1b4b4;
    }
    .error .result-head {
      background: #fff5f5;
      color: var(--bad);
    }
    @media (max-width: 760px) {
      main { padding: 20px 14px 34px; }
      .toolbar, .actions { grid-template-columns: 1fr; }
      .metric-strip { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>rag-eval-lab</h1>
    </header>

    <section class="toolbar" aria-label="Query controls">
      <div class="question-block">
        <label for="preset">Question</label>
        <select id="preset">
          <option value="What should take priority over writing the full incident timeline?">Incident timeline priority</option>
          <option value="How should someone disclose a security flaw before a fix is ready?">Security flaw disclosure</option>
          <option value="What happens if work is submitted late?">Late work policy</option>
          <option value="Does the playbook require weekend pager coverage?">Unanswerable pager coverage</option>
        </select>
        <textarea id="question">What should take priority over writing the full incident timeline?</textarea>
      </div>
      <div>
        <label for="corpus">Corpus directory</label>
        <input id="corpus" type="text" value="data/raw" />
      </div>
      <div>
        <label for="topk">Top K</label>
        <input id="topk" type="number" min="1" max="10" value="3" />
      </div>
      <div class="strategy-block">
        <label>Strategies</label>
        <div class="strategy-grid" id="strategies">
          <label class="strategy-option"><input type="checkbox" value="keyword" checked /> keyword</label>
          <label class="strategy-option"><input type="checkbox" value="semantic" checked /> semantic</label>
          <label class="strategy-option"><input type="checkbox" value="embedding" /> embedding</label>
          <label class="strategy-option"><input type="checkbox" value="embedding_strong" /> embedding_strong</label>
          <label class="strategy-option"><input type="checkbox" value="embedding_strong_rerank" checked /> embedding_strong_rerank</label>
        </div>
      </div>
    </section>

    <div class="actions">
      <button id="run-btn">Run comparison</button>
      <div class="status" id="status"></div>
    </div>

    <section class="results" id="results" aria-live="polite">
      <p class="empty">No runs yet.</p>
    </section>
  </main>

  <script>
    const preset = document.getElementById("preset");
    const question = document.getElementById("question");
    const runButton = document.getElementById("run-btn");
    const statusText = document.getElementById("status");
    const results = document.getElementById("results");

    preset.addEventListener("change", () => {
      question.value = preset.value;
    });

    function selectedStrategies() {
      return [...document.querySelectorAll("#strategies input:checked")].map(
        (input) => input.value
      );
    }

    function clearResults() {
      results.innerHTML = "";
    }

    function number(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return "n/a";
      }
      return Number(value).toFixed(3);
    }

    function supportSummary(data) {
      const checks = data.citation_checks || [];
      if (!checks.length) {
        return "n/a";
      }
      const supported = checks.filter((check) => check.supported).length;
      return `${supported}/${checks.length}`;
    }

    function topScore(data) {
      const citations = data.citations || [];
      if (!citations.length) {
        return "n/a";
      }
      return number(citations[0].retrieval_score);
    }

    function renderCard(strategy, data, elapsedMs) {
      const card = document.createElement("article");
      card.className = "result-card";
      card.innerHTML = `
        <div class="result-head">
          <h2><code>${strategy}</code></h2>
          <span class="runtime">${elapsedMs} ms</span>
        </div>
        <div class="result-body">
          <div class="metric-strip">
            <div class="metric"><span>Top score</span><strong>${topScore(data)}</strong></div>
            <div class="metric"><span>Citations</span><strong>${(data.citations || []).length}</strong></div>
            <div class="metric"><span>Supported</span><strong>${supportSummary(data)}</strong></div>
          </div>
          <p class="answer">${escapeHtml(data.answer || "")}</p>
          <h3>Citations</h3>
          <ol class="list">${renderCitations(data.citations || [])}</ol>
          <h3>Unsupported claims</h3>
          <ol class="list">${renderUnsupported(data.unsupported_claims || [])}</ol>
        </div>
      `;
      results.appendChild(card);
    }

    function renderError(strategy, error) {
      const card = document.createElement("article");
      card.className = "result-card error";
      card.innerHTML = `
        <div class="result-head">
          <h2><code>${strategy}</code></h2>
          <span class="runtime">failed</span>
        </div>
        <div class="result-body">
          <p class="answer">${escapeHtml(error.message)}</p>
        </div>
      `;
      results.appendChild(card);
    }

    function renderCitations(citations) {
      if (!citations.length) {
        return "<li>No citations returned.</li>";
      }
      return citations.map((citation) => `
        <li>
          <code>${escapeHtml(citation.chunk_id)}</code>
          <span class="snippet">${escapeHtml(citation.snippet || "")}</span>
        </li>
      `).join("");
    }

    function renderUnsupported(claims) {
      if (!claims.length) {
        return "<li>None</li>";
      }
      return claims.map((claim) => `<li>${escapeHtml(claim)}</li>`).join("");
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    async function queryStrategy(strategy) {
      const startedAt = performance.now();
      const response = await fetch("/qa/query", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          question: question.value,
          retrieval_strategy: strategy,
          top_k: Number(document.getElementById("topk").value),
          corpus_dir: document.getElementById("corpus").value,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ? JSON.stringify(data.detail) : "Request failed");
      }
      return {
        data,
        elapsedMs: Math.round(performance.now() - startedAt),
      };
    }

    runButton.addEventListener("click", async () => {
      const strategies = selectedStrategies();
      if (!strategies.length) {
        statusText.textContent = "Select at least one strategy.";
        return;
      }

      runButton.disabled = true;
      runButton.textContent = "Running";
      statusText.textContent = (
        `Running ${strategies.length} strategy` +
        `${strategies.length === 1 ? "" : "ies"}.`
      );
      clearResults();

      for (const strategy of strategies) {
        try {
          const {data, elapsedMs} = await queryStrategy(strategy);
          renderCard(strategy, data, elapsedMs);
        } catch (error) {
          renderError(strategy, error);
        }
      }

      statusText.textContent = (
        `Completed ${strategies.length} strategy` +
        `${strategies.length === 1 ? "" : "ies"}.`
      );
      runButton.disabled = false;
      runButton.textContent = "Run comparison";
    });
  </script>
</body>
</html>
        """
    )

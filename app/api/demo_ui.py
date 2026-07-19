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
  <link rel="stylesheet" href="/static/demo.css" />
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

  <script src="/static/demo.js"></script>
</body>
</html>
        """
    )

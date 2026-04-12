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
    :root { color-scheme: light; }
    body { font-family: Inter, system-ui, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }
    .container { max-width: 960px; margin: 32px auto; background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; }
    h1 { margin: 0 0 8px 0; font-size: 1.75rem; }
    p { margin: 0 0 20px 0; color: #334155; }
    .grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
    label { font-weight: 600; display: block; margin-bottom: 6px; }
    input, select, textarea, button { width: 100%; box-sizing: border-box; border-radius: 8px; border: 1px solid #cbd5e1; padding: 10px; font: inherit; }
    textarea { min-height: 88px; resize: vertical; }
    button { background: #0f172a; color: #fff; cursor: pointer; border: none; font-weight: 600; }
    button:disabled { background: #64748b; cursor: not-allowed; }
    .result { margin-top: 20px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }
    .muted { color: #475569; font-size: 0.92rem; }
    ul { padding-left: 20px; }
    code { background: #e2e8f0; padding: 1px 4px; border-radius: 4px; }
  </style>
</head>
<body>
  <main class="container">
    <h1>rag-eval-lab demo UI</h1>
    <p>Submit a question, run retrieval + grounded answer generation, and inspect citations.</p>
    <div class="grid">
      <div style="grid-column: 1 / -1;">
        <label for="question">Question</label>
        <textarea id="question">What should take priority over writing the full incident timeline?</textarea>
      </div>
      <div>
        <label for="strategy">Retrieval strategy</label>
        <select id="strategy">
          <option value="semantic" selected>semantic</option>
          <option value="keyword">keyword</option>
          <option value="embedding">embedding</option>
          <option value="embedding_strong">embedding_strong</option>
          <option value="embedding_strong_rerank">embedding_strong_rerank</option>
        </select>
      </div>
      <div>
        <label for="topk">Top K</label>
        <input id="topk" type="number" min="1" max="10" value="3" />
      </div>
      <div>
        <label for="corpus">Corpus directory</label>
        <input id="corpus" type="text" value="data/raw" />
      </div>
    </div>
    <div style="margin-top: 14px;">
      <button id="run-btn">Generate grounded answer</button>
    </div>
    <section class="result" id="result" hidden>
      <h2 style="margin-top: 0;">Response</h2>
      <p id="answer"></p>
      <p class="muted">Strategy: <code id="used-strategy"></code></p>
      <h3>Citations</h3>
      <ul id="citations"></ul>
      <h3>Unsupported claims</h3>
      <ul id="unsupported"></ul>
    </section>
  </main>
  <script>
    const btn = document.getElementById("run-btn");
    const result = document.getElementById("result");
    const answer = document.getElementById("answer");
    const usedStrategy = document.getElementById("used-strategy");
    const citations = document.getElementById("citations");
    const unsupported = document.getElementById("unsupported");

    function li(text) {
      const item = document.createElement("li");
      item.textContent = text;
      return item;
    }

    btn.addEventListener("click", async () => {
      btn.disabled = true;
      btn.textContent = "Running…";

      const payload = {
        question: document.getElementById("question").value,
        retrieval_strategy: document.getElementById("strategy").value,
        top_k: Number(document.getElementById("topk").value),
        corpus_dir: document.getElementById("corpus").value,
      };

      try {
        const response = await fetch("/qa/query", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail ? JSON.stringify(data.detail) : "Request failed");
        }

        answer.textContent = data.answer;
        usedStrategy.textContent = data.retrieval_strategy;

        citations.innerHTML = "";
        for (const citation of data.citations || []) {
          citations.appendChild(
            li(`${citation.chunk_id} (${citation.document_id}) — score ${citation.retrieval_score.toFixed(3)}`)
          );
        }
        if (!citations.children.length) {
          citations.appendChild(li("No citations returned."));
        }

        unsupported.innerHTML = "";
        for (const claim of data.unsupported_claims || []) {
          unsupported.appendChild(li(claim));
        }
        if (!unsupported.children.length) {
          unsupported.appendChild(li("None"));
        }

        result.hidden = false;
      } catch (error) {
        answer.textContent = `Error: ${error.message}`;
        citations.innerHTML = "";
        unsupported.innerHTML = "";
        result.hidden = false;
      } finally {
        btn.disabled = false;
        btn.textContent = "Generate grounded answer";
      }
    });
  </script>
</body>
</html>
        """
    )

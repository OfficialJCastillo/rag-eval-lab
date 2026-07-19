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

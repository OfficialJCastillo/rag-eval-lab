# Benchmark Report

Generated from `results/retrieval-backend-comparison.json` and per-strategy run artifacts.

## Strategy Summary

| Strategy | Hit Rate | MRR | nDCG | Faithfulness |
| --- | ---: | ---: | ---: | ---: |
| `keyword` | 0.9167 | 0.9167 | 0.9167 | 0.8360 |
| `semantic` | 0.9167 | 0.8333 | 0.8552 | 0.8319 |
| `embedding` | 0.9167 | 0.8750 | 0.8859 | 0.8531 |
| `embedding_strong` | 0.9167 | 0.8750 | 0.8859 | 0.8509 |
| `embedding_strong_rerank` | 0.9167 | 0.9167 | 0.9167 | 0.8436 |

## Key Findings

- `keyword` remains a strong lexical baseline on this benchmark.
- Dense retrieval improves answer faithfulness slightly, but embedding-only variants trail the lexical baseline on rank-sensitive metrics.
- `embedding_strong_rerank` matches the lexical baseline on `MRR` and `nDCG`, which suggests second-stage ranking quality matters more than stronger dense retrieval alone.

## Case Notes

- `What should take priority over writing the full incident timeline?`
  `embedding` ranked `incident_response_playbook-chunk-4` first and pushed the correct chunk to rank 2 (`MRR=0.5`).
  `embedding_strong_rerank` restored `incident_response_playbook-chunk-2` to rank 1 (`MRR=1.0`).
- `How should someone disclose a security flaw before a fix is ready?`
  `keyword` starts with `opensource_maintainer_guide-chunk-1` followed by `public_operations_manual-chunk-3`.
  `embedding` pulls in the near-miss `opensource_maintainer_guide-chunk-3` at rank 2, while `embedding_strong_rerank` restores `public_operations_manual-chunk-3` as the stronger second result.
- `Does the playbook require weekend pager coverage?`
  Both `keyword` and `embedding_strong_rerank` remain unsupported here (`MRR=0.0` and `0.0`), which keeps an explicit unanswerable check in the benchmark.

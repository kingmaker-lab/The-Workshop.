# HEART_005 | Causal Attention research release gate

Date: 2026-11-13
Scope: Python forward-only attention, isolated browser heatmap, Docs and CI.

## Research claims

- Implements single-head scaled dot-product self-attention with deterministic
  untrained Q/K/V matrices, optional sinusoidal positional encodings,
  stable softmax and a causal triangular mask.
- Applies to the existing `TokenEmbeddings` lookup, optionally trained
  separately by skip-gram. **Attention projections are not trained**.
- The browser heatmap uses its own deterministic synthetic token vectors
  and Q/K/V, not learned Python weights and not the trained browser embeddings.
- This is not a Transformer decoder, trained language model, inference API,
  semantic evaluation or autoregressive text generator.

## Local security and reproducibility

- Python: strictly bounded sequence (1..64 tokens), dimension (2..64),
  validated token IDs, finite/bounded input embedding weights, no network
  or model download, no file writes or external dependencies.
- PAD keys and PAD queries return zero attention. Non-PAD rows sum to one,
  future positions receive exactly zero probability.
- Browser: up to 160 text characters scanned by the existing first-party
  Byte-BPE tokenizer and 14 visible tokens; an accessible table, locally
  initialized deterministic weights, client-side DOM `textContent` only.
  No remote telemetry or storage; no `fetch`, WebSocket, eval or external JS.
- The existing `/heartai/` CSP retains `script-src 'self'`,
  `connect-src 'none'`, and `frame-ancestors 'none'`.
- The separate ARGUS, CERBERUS, NEXUS and catalog routes must remain intact.

## Validation

- Python 3.11: **44/44 tests PASS**, including future-token invariance,
  mask normalization, PAD, deterministic seeds, sinusoidal positions,
  rejection of invalid values and integration with tokenizer and embeddings.
- Browser/Worker: **20/20 tests PASS**, including causal heatmap,
  keyboard slider inputs, unicode input limits, strict route headers and
  sibling app preservation.
- Run the integrated CLI experiment and require `causal_mask_ok=True`.
- Additional benchmarks, numerical gradient tests, GPU implementations,
  semantic assessment and independent security audit: **NOT DONE**.
- Public deployment: approved only for **static client-side educational
  demonstration**. No Python runtime, model weights or private data hosted.

CI links and preview / production deployment evidence will be appended after
the corresponding checks. This gate is not a production AI certification.

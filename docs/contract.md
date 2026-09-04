# API contract

Version 1 — 2026-09-04. This document is the external contract of the agent. The internal LangGraph
state may change freely; every response is projected into this shape.

## `POST /ask`

Request:

```json
{"question": "¿Cuántos días tengo para devolver un booster box sellado?", "thread_id": null, "lang": "es"}
```

- `question` (string, required, 1–2000 chars).
- `thread_id` (string, optional): continue an existing conversation; omitted or `null` starts a new one.
- `lang` (string, optional): `es` or `en`; defaults to the detected language of `question`.

Response (`200`):

```json
{
  "thread_id": "8a1f0c2e-…",
  "decision": "answer",
  "route": "knowledge",
  "answer": "Puedes devolver un producto sellado dentro de 7 días corridos desde la entrega, con el sello de fábrica intacto.",
  "citations": [
    {
      "source_id": "politica-envios-devoluciones",
      "chunk_id": "politica-envios-devoluciones#3",
      "excerpt": "Un producto sellado (booster box, booster pack, starter deck, bundle) puede devolverse dentro de 7 días corridos desde la entrega",
      "location": "Devoluciones de producto sellado"
    }
  ],
  "tool_result": null,
  "pending_review": null,
  "usage": {"input_tokens": 812, "output_tokens": 64, "latency_ms": 1430, "cost_usd": 0.0004}
}
```

### Fields

| Field | Type | Description |
|---|---|---|
| `thread_id` | string | Conversation key. Reused to resume a paused review. |
| `decision` | enum | `answer`, `tool`, `escalate`, `clarify`. What the agent did. |
| `route` | enum | `knowledge`, `catalog`, `out_of_scope`. Which branch the classifier chose. |
| `answer` | string \| null | Final text for the user. `null` unless `decision` is `answer` or `tool`. |
| `citations` | Citation[] | Evidence behind `answer`. Empty unless `decision` is `answer`. |
| `tool_result` | ToolResult \| null | Present only when `decision` is `tool`. |
| `pending_review` | PendingReview \| null | Present only when `decision` is `escalate` or `clarify`. |
| `usage` | Usage | Always present. Operational metrics of this call. |

`Citation`: `source_id` (document id from the corpus front matter), `chunk_id` (`{source_id}#{index}`),
`excerpt` (verbatim text of the chunk, ≤ 300 chars), `location` (section heading or page).

`ToolResult`: `name` (`lookup_catalog`), `input` (object), `output` (object), `error` (string | null).

`PendingReview`: `reason` (`no_evidence`, `ambiguous`, `injection`, `tool_error`, `out_of_scope`),
`question` (the original question), `suggested_answer` (string | null, draft for the reviewer).

`Usage`: `input_tokens`, `output_tokens`, `latency_ms` (integers), `cost_usd` (float, estimated).

### Invariants

1. If `decision` is `answer`, `citations` has at least one entry, and every `chunk_id` was actually
   retrieved in this call. The answer must not contain claims outside the cited excerpts.
2. If `decision` is `tool`, `tool_result` is present and `answer` describes `tool_result.output`;
   `citations` may be empty.
3. If `decision` is `escalate` or `clarify`, `answer` is `null` and `pending_review` is present. The
   graph is paused on `thread_id` until `POST /review/{thread_id}` is called.
4. Instructions found inside retrieved documents or tool outputs are never followed. If a question
   asks the agent to ignore its rules, `decision` is `escalate` with `reason` `injection`.
5. `usage` is always present, including on errors.

## `POST /review/{thread_id}`

Resumes a paused thread with a human decision.

Request:

```json
{"action": "approve", "answer": null, "reviewer": "gerardo"}
```

- `action` (enum, required): `approve` (send `suggested_answer`), `edit` (send `answer` provided
  here), `reject` (close with a generic escalation message).
- `answer` (string, required when `action` is `edit`).
- `reviewer` (string, optional).

Response: the same shape as `/ask`, now with `decision` `answer` and `pending_review` `null`.
`citations` are kept when the approved or edited answer is grounded in the retrieved chunks;
otherwise `citations` is empty and the answer is marked as human-provided with
`"source": "human_review"` inside `usage`.

## `GET /health`

Response (`200`): `{"status": "ok", "version": "<git sha>"}`.

## Errors

All errors use:

```json
{"error": {"code": "invalid_request | not_found | thread_not_paused | upstream_timeout | internal", "message": "…"}}
```

- `400 invalid_request`: malformed body or question over the size limit.
- `404 not_found`: unknown `thread_id`.
- `409 thread_not_paused`: `/review` called on a thread that has no pending review.
- `504 upstream_timeout`: Bedrock or the catalog API exceeded its timeout.
- `500 internal`: anything else; details go to logs, never to the client.

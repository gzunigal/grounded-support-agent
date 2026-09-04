# grounded-support-agent

A support agent for a small trading-card game store that answers **only with evidence** or hands the
question to a human. Built as a public portfolio project to demonstrate Python, RAG, LangGraph,
human-in-the-loop workflows, evaluations and an AWS deployment.

**Status: phase 0 (preparation).** No code yet. This commit contains the evaluation dataset, the
synthetic corpus and the API contract, written before any implementation so that quality is defined
first.

## What it does

1. Receives a question through an API (and later a minimal web UI).
2. Classifies it: documentation question, live catalog lookup, or out of scope.
3. Retrieves evidence from a vector index and answers with verifiable citations.
4. Abstains and pauses the workflow when evidence is insufficient.
5. Lets a person approve, edit or reject the pending answer.
6. Records traces, latency, tokens and estimated cost.
7. Runs an evaluation dataset as a gate before every deployment.
8. Exposes the same agent over the A2A protocol (last phase).

The store, **Nexo TCG**, is fictional. All documents are synthetic. No real customer data is used.

## Stack

| Concern | Choice |
|---|---|
| Language | Python 3.12+, FastAPI, Pydantic, pytest |
| Orchestration | LangGraph (routes, tools, interrupts, checkpoints) |
| Chat model | OpenAI GPT-5.6 Luna on Amazon Bedrock (`us.openai.gpt-5.6-luna`) |
| Embeddings | Cohere Embed v4 on Amazon Bedrock (`cohere.embed-v4:0`), multilingual |
| Vector store | Amazon S3 Vectors |
| Graph state | DynamoDB via `langgraph-checkpoint-aws` |
| Runtime | Amazon ECS on Fargate, image in ECR |
| Tracing and evals | LangSmith |
| Region | `us-east-1` |

## Repository layout

```
corpus/            documents the agent can cite (markdown, PDF, PNG)
corpus/src/        markdown sources for the PDF and PNG files, plus render.py
docs/contract.md   API contract: /ask, /review/{thread_id}, /health, errors
evals/dataset.jsonl 20 labeled cases: answerable, catalog, unsupported, adversarial
```

## Corpus

Five synthetic documents in Spanish (one in English) in three formats, so the ingestion pipeline has
to parse text, PDF and images (OCR):

| `source_id` | Format | Topic |
|---|---|---|
| `politica-envios-devoluciones` | markdown | Shipping and returns |
| `preventas-y-reservas` | PDF | Pre-orders and reservations |
| `torneos-y-eventos` | PDF | Weekly tournaments |
| `compra-de-cartas-usadas` | PNG flyer | Purchase price for singles |
| `store-faq` | markdown (en) | Hours, location, membership, store credit |

PDF and PNG files are generated from `corpus/src/*.md` with `corpus/src/render.py` and headless
Chrome, so their text can be checked against the source.

## Evaluation dataset

`evals/dataset.jsonl` holds one case per line. Each case has a `group`, the expected `source_id` or
tool, and the expected behavior (`answer`, `tool`, `escalate`, `clarify`). The "unsupported" cases are
questions the store could plausibly answer but the corpus deliberately does not cover.

Target metrics (to be measured from phase 2): retrieval `recall@5` ≥ 0.85, 100% of citations point
to retrieved chunks, 100% of unsupported cases end in abstention, routing accuracy ≥ 0.90.

## Phases

| Phase | Gate |
|---|---|
| 0 Preparation | Budget alert, Bedrock access, dataset, corpus and contract versioned |
| 1 Deployed skeleton | A push to `main` publishes an image and a public `/health` responds |
| 2 Minimal RAG | Answerable question returns a citation; unsupported one abstains |
| 3 LangGraph + HITL | Three routes work end to end, reviews resume after the task is replaced |
| 4 Evals, observability, security | A metric drop fails CI and blocks deployment |
| 5 Demo | A third party runs the three paths from the public URL |
| 6 A2A | An A2A client gets a cited answer using only the Agent Card |

## Cost

Everything runs pay-per-use except the Fargate task (about USD 9/month). A budget alert is set at
USD 25. The service is stopped between phases; a shutdown guide will be added with phase 1.

## License

MIT.

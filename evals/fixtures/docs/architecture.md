# Ledger service architecture

The ledger service records immutable double-entry postings for the billing platform. It exposes a write path for posting batches and a read path for account balances, and it owns the only copy of the posting history.

## Components

| Component | Responsibility |
|---|---|
| `posting-api` | Validates and accepts posting batches over HTTP |
| `posting-worker` | Applies accepted batches to the ledger tables in transaction order |
| `balance-reader` | Serves point-in-time and current balances from a materialized projection |
| `reconciler` | Nightly job comparing the projection against the posting history |

## Write path

A client submits a batch of postings with an idempotency key. `posting-api` validates that the batch balances to zero, rejects it outright if it does not, and appends it to a durable queue. The API returns before the batch is applied, so callers poll the batch status endpoint or wait for the completion event.

`posting-worker` consumes the queue in order per account partition. Ordering is per partition, not global: two batches touching disjoint accounts may be applied in either order, and the reconciler does not treat that as a discrepancy.

## Read path

Balances are served from a projection rebuilt incrementally as postings land. The projection lags the posting history by the worker's queue depth, typically under a second. Callers that need a balance consistent with a specific batch pass that batch's sequence number and the reader blocks until the projection has caught up to it.

## Failure handling

A worker crash mid-batch leaves the batch unapplied rather than half-applied: each batch is one database transaction. A poisoned batch that fails to apply three times moves to a dead-letter table and pages the on-call engineer, because a stuck partition blocks every later batch for the same accounts.

## Retention

Postings are never deleted. Account closure writes a closing entry and marks the account inactive. The projection drops inactive accounts after ninety days and rebuilds them on demand from the posting history if a late query arrives.

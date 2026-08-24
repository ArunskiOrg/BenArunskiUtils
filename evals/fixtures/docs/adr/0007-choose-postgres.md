# ADR 0007: Choose PostgreSQL for the ledger store

Status: accepted

## Context

The ledger service needs a store for immutable double-entry postings and a balance projection derived from them. Writes arrive in batches that must apply atomically, and the balance projection must be updated in the same transaction as the postings it summarizes, otherwise a crash between the two leaves a balance nobody can explain.

The team evaluated PostgreSQL, DynamoDB, and a purpose-built append-only store. Two engineers have production experience with PostgreSQL, one with DynamoDB, and none with the third option.

Expected volume for the first two years is under ten million postings a month, with balance reads outnumbering writes roughly forty to one.

## Decision

The ledger uses PostgreSQL, with the posting history and the balance projection in the same database and the same transaction.

Multi-statement atomicity is the requirement doing the deciding. DynamoDB's transaction support covers the write pattern but caps a transaction at a size the larger batches exceed, which would push batch splitting and compensation logic into the application. PostgreSQL gives that guarantee without application-level machinery.

The append-only store was rejected on operational cost. Nothing in the requirements needs what it offers over an ordinary table with no update or delete grants.

## Consequences

Write throughput is bounded by a single primary. At the projected volume this leaves substantial headroom, and the partition-per-account design in the worker means sharding later is a routing change rather than a rewrite.

Balance reads share capacity with writes. Read replicas absorb the read path when contention shows up, at the cost of replication lag the `min_sequence` parameter already accounts for.

The team's existing PostgreSQL operational knowledge applies directly: backups, failover, and query tuning all follow practices already in use elsewhere in the platform.

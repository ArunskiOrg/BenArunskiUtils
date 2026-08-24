# Release notes

## 4.2.0

- Balance reads accept a `min_sequence` parameter and block until the projection has caught up to that sequence, replacing the client-side retry loop most callers had written by hand.
- Posting batches larger than 5,000 entries are rejected with a `413` instead of timing out after the request budget expired.
- The reconciler reports per-partition drift rather than a single aggregate number, so a discrepancy points at a partition instead of at the whole ledger.

## 4.1.3

- Fixed a deadlock between the nightly reconciler and the projection rebuild when both ran against the same inactive account.
- Dead-lettered batches now record the failing entry index in the alert payload.

## 4.1.2

- Idempotency keys are scoped per tenant. Two tenants reusing the same key no longer collide.
- Reduced projection lag under sustained write load by batching projection updates into groups of fifty rather than applying them one posting at a time.

## Upgrade notes

4.2.0 rejects oversized batches that earlier versions accepted and then timed out on. Split batches above 5,000 entries before upgrading. No schema migration is required.

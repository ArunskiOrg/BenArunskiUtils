# Onboarding guide

Welcome to the billing platform team. This guide covers your first week. Work through it in order; each section assumes the previous one is done.

## Day one: access

Request the `billing-dev` group in the access portal. It grants read access to the staging database, the deploy pipeline, and the on-call rotation calendar. Production write access is granted separately, after you have shipped a change and shadowed one on-call shift.

## Day two: run the stack locally

The stack runs under a single compose file. Start the database first, let the migrations finish, then start the services. Starting everything at once works most of the time and fails confusingly when it does not, because the workers exit rather than retry if the schema is missing.

Seed data loads a hundred accounts and a few thousand postings. It is enough to exercise the read path and not enough to reproduce any performance issue you will be asked about.

## Day three: read the write path

Trace a posting batch from the API through the queue to the worker and into the ledger tables. Set a breakpoint in the worker's apply function and submit a batch by hand. Understanding where the transaction boundary sits will save you a week later on.

## Day four: ship something small

Pick an issue tagged `good-first-issue`. Open the pull request before it is finished and mark it a draft. Early feedback on the approach costs less than a rewrite after review.

## Day five: on-call shadowing

Sit with the on-call engineer. Read the last month of incident notes first so the alerts have context. Ask what each alert would look like at three in the morning, because that is the only time the wording matters.

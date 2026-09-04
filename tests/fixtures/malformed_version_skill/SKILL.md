---
name: malformed-version-fixture
description: Fixture whose version is missing its patch component so the semver rule has something to fail on. Its name, description, body, and references are all valid, so a failure here can only come from the version.
version: 1.2
---

# Malformed version fixture

`1.2` is the shape a skill author reaches for when treating the version as a decimal number. It is not semver, and it is not comparable against `1.2.0` or `1.10`, so an installer cannot tell from it whether a change is a patch or a behavior change. YAML also reads the unquoted value as a float, which is the failure the validator reports.

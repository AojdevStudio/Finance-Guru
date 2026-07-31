---
title: "Finance Guru repository documentation"
description: "Contributor, operational, and source-reference material"
category: root
---

# Finance Guru repository documentation

The [GitHub Wiki home](https://github.com/AojdevStudio/Finance-Guru/wiki/Home)
is the canonical reader-facing guide. This `docs/` directory remains the
repository source and contains material maintainers need to verify, operate,
and evolve the project without duplicating the Wiki's user-guide pages.

## Start here

| Need | Source |
| --- | --- |
| Install or develop the checked-in engine | [Setup](setup/SETUP.md) |
| Find a verified command entry point | [CLI reference](reference/api.md) |
| Configure optional provider credentials | [API keys](setup/api-keys.md) |
| Resolve an environment or provider failure | [Troubleshooting](setup/TROUBLESHOOTING.md) |
| Understand contribution boundaries and checks | [Contributing](CONTRIBUTING.md) |
| Review data-handling boundaries | [Privacy](../PRIVACY.md) |
| Understand planned standalone-app work | [Vision](VISION.md) |
| Verify a canonical Wiki claim | [Wiki evidence ledger](reference/wiki-evidence-ledger.md) |

## Operations and historical records

- [Runbooks](runbooks/README.md) cover recurring operational procedures.
- [Architecture decisions](adr/) preserve decisions that remain relevant to the
  checked-in repository.
- [Solutions](solutions/) and [reports](reports/) are historical evidence, not
  product guarantees. Check their dates and the current code before reusing a
  claim.
- Historical planning material, when present in a branch or release, does not
  describe released or implemented behavior unless current code proves it.

## Documentation maintenance

When a change affects setup, commands, data storage, privacy, testing, or
release status, update the corresponding Wiki page and this repository source
material as needed. The Wiki's [maintenance page](https://github.com/AojdevStudio/Finance-Guru/wiki/Wiki-Maintenance)
maps changes to pages and records the evidence standard.

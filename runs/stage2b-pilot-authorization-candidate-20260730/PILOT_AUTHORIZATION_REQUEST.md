# Stage 2b pilot authorization request

Status: **REQUEST ONLY — PILOT NOT AUTHORIZED**

## Reviewed source

- Freeze manifest SHA-256:
  `45a138e5829c1e5d23e4dad56e4801ac17d6dd534ef041cf0c595ac92dcec060`
- Frozen source-tree SHA-256:
  `c6454c03f009e66112098c79846e7648f266c2b2b41924e90769cdbca40562d4`
- Frozen entries: `87`
- Independent adversarial verdict: `PASS / GO` for packet generation only

## Exact pilot sources

- Canonical notebook:
  `j-space-lab/jspace_colab_stage2b_discrimination.ipynb`
- Canonical notebook SHA-256:
  `9564236a1f49d7ffe2bea44f8b04be5a584c0ff9740b11dd1e563c93b8dba2fe`
- Deterministic code bundle:
  `stage2b-pilot-code-bundle.zip`
- Deterministic code-bundle SHA-256:
  `aeec8a76a426fa82f3fb96dc6700289a689fcb92fd9952da681fe03fe12dbef4`
- Pinned 20-prompt pilot-view SHA-256:
  `5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4`

The bundle rebuilt byte-for-byte, contains only six allowlisted code/fixture
files plus its manifest, and contains no pilot prompt text or prompt digest. The
notebook is unexecuted and all source authorization, threshold, confirmation,
transfer, commit, and push gates remain false.

## Exact approval statement

Dr. Mani may authorize the pilot by returning this statement unchanged:

> Authorize the isolated 20-prompt Stage 2b Google Colab pilot using canonical notebook SHA-256 9564236a1f49d7ffe2bea44f8b04be5a584c0ff9740b11dd1e563c93b8dba2fe and code-bundle SHA-256 aeec8a76a426fa82f3fb96dc6700289a689fcb92fd9952da681fe03fe12dbef4, bound to pilot-view SHA-256 5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4, including upload of those three exact sources plus the resulting content-addressed authorization record and allocation of one Google Colab GPU with at least 14 GiB VRAM. Run only the ratified dual-floor fully crossed 8×8 pilot. Keep confirmation access and artifact transfer false; retain the pilot artifact in Colab and do not download, publish, commit, push, merge, or access the 180-prompt confirmation set.

Approval of this statement authorizes only the exact pilot scope and source
identities above. It does not authorize confirmation, artifact transfer,
publication, repository operations, or later source identities.

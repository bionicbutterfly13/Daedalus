# Publication Gate

```text
publication_prepared
  -> awaiting_dr_mani_approval
  -> published
     | publication_declined
     | publication_blocked
```

Rules:

1. Preparation and validation may reach `publication_prepared` without outward action.
2. A completed human review moves the article to `awaiting_dr_mani_approval`.
3. Only explicit post-review approval from Dr. Mani authorizes `published`; record it in a separate `publication-approval.json` bound to the exact article SHA-256.
4. No response, inherited permission, study-execution approval, or destination selection counts as publication approval.
5. Privacy, unsupported claims, unavailable destination, or verification failure requires `publication_blocked`; a deliberate decision not to publish is `publication_declined`.
6. A correction must be dated, linked to the original, and preserve the prior record unless privacy or safety requires withdrawal.

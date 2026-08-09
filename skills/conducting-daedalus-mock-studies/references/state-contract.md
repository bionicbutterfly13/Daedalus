# State Contract

```text
intake -> prepared
prepared -> launched
launched -> monitoring
monitoring -> evidence_ready
evidence_ready -> accepted | partial | failed | stopped
accepted | partial | failed | stopped -> publication_prepared
publication_prepared -> awaiting_dr_mani_approval
awaiting_dr_mani_approval -> published | publication_declined | publication_blocked
```

No transition occurs from narration alone. `prepared` requires the frozen packet and authorization record. `launched` requires a verified real Daedalus interface and an identified attempt. `monitoring` requires native event or process evidence. `evidence_ready` requires a complete expected-versus-observed inventory, including explicit missing entries.

The study verdict comes only from Archimedes independent acceptance. `publication_prepared` may follow any terminal study verdict when the article preserves that verdict. `published` requires Dr. Mani's explicit approval after reviewing the final article. Missing approval yields no publication transition.

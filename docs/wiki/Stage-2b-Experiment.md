# Stage 2b Experiment

## Central estimand

For the model's own next-token argmax target:

1. Does the fitted Jacobian map outperform a same-layer,
   geometry-preserving broken map?
2. Is that fitted-over-broken advantage larger for the correct activation than
   for a wrong activation?

The second question is the specificity test. Without it, fitted-map advantage
could be a generic property of the transport.

## Four-cell factorial

| Activation | Fitted map | Broken map |
|---|---|---|
| Correct | `correct_act_fitted_map` | `correct_act_broken_map` |
| Wrong | `wrong_act_fitted_map` | `wrong_act_broken_map` |

The interaction is:

```text
(correct/fitted - correct/broken)
-
(wrong/fitted - wrong/broken)
```

A positive number is not automatically a pass. The pilot used the preregistered
coverage and uncertainty rules, including the rule that an under-covered category
makes the required floor undefined.

## Repeated controls

At each prompt and selected layer:

- eight deterministic wrong-activation donor assignments;
- eight deterministic broken-map draws;
- every donor crossed with every map;
- all 64 logical combinations retained through inference;
- donor IDs, recipient-to-donor digests, map IDs, seeds, and map hashes retained.

The count, crossing, pilot seed identities, and inference rules were fixed before
the authorized 2026-07-31 run. Smoke-only identities were not reused as pilot
authority.

## Selected layers and prompts

The design used four selected layers and a pinned 20-prompt pilot view drawn from
a publicly specified 200-prompt source manifest. The remaining 180 prompts form a
runtime-sealed, unaccessed later confirmation set. The integration smoke used
nine separate engineering prompts whose SHA-256 identities were checked for zero
overlap with all scientific input sets.

## Artifact shape

The compact representation stores:

- one correct/fitted value;
- eight correct/broken values indexed by map;
- eight wrong/fitted values indexed by donor;
- 64 wrong/broken values indexed by donor and map;
- both prompt floors and their named difference;
- target, model, lens, runtime, authorization, and provenance identities.

The validator reconstructs all 64 logical factorials and recomputes every
derivable score. Raw activations and full logits are not retained.

## Settled, pending, deferred

### Settled

- model-output argmax target;
- decoded input-embedding primary floor;
- layer-0 residual sensitivity floor;
- eight donors;
- eight maps;
- full donor-by-map crossing;
- compact 81-readout representation;
- no artifact transfer without separate authorization;
- completed 20-prompt pilot with 80 prompt-layer records;
- primary-floor inference undefined because arithmetic-completion coverage was
  2 against the required 3; and
- positive, defined sensitivity-floor estimates at all four layers.

### Pending

- a preregistered response to the primary-floor category-coverage failure;
- a decision on whether a repeat pilot is scientifically justified;
- derivable thresholds from a future qualifying source analysis; and
- separate authorization for any later GPU execution.

### Deferred

- 180-prompt confirmation;
- Stage 3;
- any confirmed instrument claim;
- Sakshi or Elume consumption.

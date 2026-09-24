# Art-direction review in BB

Use this route for static source artwork or promo composition. Keep the candidate,
cut layers and fixed comparison set at their intended display size. Label each
image in the task-local prompt and state whether the bar is the game's own
released work, a studio reference, or another agreed target. A score without
that reference frame is not a useful acceptance decision.

Use the installed `qwen-review` provider and `qwen/qwen3.8-omni-flash`.
Attach the candidate and references as local PNG, JPEG or WebP images:

```bash
bb thread spawn --project "$BB_PROJECT_ID" --environment "$BB_ENVIRONMENT_ID" \
  --parent-self --visibility hidden --provider qwen-review \
  --model qwen/qwen3.8-omni-flash --permission-mode accept-edits \
  --title "Art-direction review" --prompt-file /absolute/path/review-prompt.md \
  --image /absolute/path/candidate.png --image /absolute/path/reference.png
```

Ask for composition, readability, lighting, typography, style consistency,
specific observed defects and prioritized adjustments. Distinguish changes
possible in the compositor from changes requiring source artwork. If assembler
logic matters, attach its relevant source as a text file or summarize the
specific operations in the prompt.

Wait for `bb thread wait <id> --status idle` and inspect
`bb thread log <id> --all --json`. Save the thread ID, source paths and
SHA-256 hashes, reference set, criteria, coverage and findings in the task-local
report. If an image is inaccessible or the reference set is missing, mark the
audit incomplete. AI feedback is advisory; the user decides acceptance.

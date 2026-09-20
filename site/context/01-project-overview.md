# 01 Project overview

hyodo.app is the public home of HyoDo, an open-source, local-first evidence
and guardrail CLI for AI-assisted development. The site exists to make one
sentence land in thirty seconds: *when your AI says "done", HyoDo tells you
what evidence supports that claim and what remains unknown.*

## Audience, in layers

1. People who build with AI but cannot read code. They need plain language,
   one install command, and a visual that makes "unobserved is never green"
   felt, not explained.
2. Developers. They need exit contracts, Bring-Your-Own-Gates, SARIF, MCP,
   and proof that the tool is honest about what it did not measure.
3. Teams that must show evidence. They need the ledger, policy decisions, and
   the roadmap toward exportable evidence.

## User flows

- Land on `/` → read the headline → copy `pipx install hyodo` → go to
  `/docs/quickstart`.
- Land on `/` → scroll → understand the three layers → open
  `/docs/philosophy` or `/docs/trust`.
- Arrive from GitHub or PyPI → find `/docs/*` as the reference.

## Out of scope for this site

- No hosted service, no accounts, no analytics that phone home by default.
- No claims that are not measured in the repository (no cost savings, no
  probabilities, no legal compliance statements).
- No project-internal vocabulary. Public language is English; the
  six virtue labels stay trilingual because the label is the label.

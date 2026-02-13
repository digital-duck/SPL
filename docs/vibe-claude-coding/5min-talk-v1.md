# Vibe Claude-Coding: From Easy Prototype to Enterprise Product

**Venue:** Anthropic Workshop — Power Talk (5 minutes)
**Speaker:** Wen Gong
**Audience:** Mixed engineers, managers, IT staff (~hundreds in-person + online)

---

## Slide-by-Slide Outline + Speaker Script

---

### SLIDE 1 — The Hook (30 sec)

**Slide title:** "When Enterprise Tooling Fails, Vibe Coding Wins"

**Visuals:** Side-by-side: a failed Jira ticket / AWS SEG error on left, Claude Code terminal on right

**Script:**
> Last year, our team needed to upgrade Node.js across hundreds of repos.
> We filed the ticket with AWS SEG — our enterprise toolchain.
> Weeks passed. Nothing.
> Out of frustration, I opened Claude Code and just... started talking to it.
> Three hours later, the upgrade was done.
> That moment changed how I think about enterprise software development.

---

### SLIDE 2 — What Is "Vibe Claude-Coding"? (30 sec)

**Slide title:** "Vibe Coding: Conversational → Automated → Enterprise"

**Visuals:** Three-step arrow: `Vibe it → Automate it → Deploy it`

**Script:**
> "Vibe coding" isn't just autocomplete on steroids.
> It's a development *pattern*: you start by having a conversation with Claude Code,
> prove the idea works interactively, then harden it into an automated agent
> that runs at enterprise scale — no babysitting required.
> Today I'll show you two products we built this way.

---

### SLIDE 3 — Case Study 1: vg-upgrade-agent (90 sec)

**Slide title:** "vg-upgrade-agent: Node.js Upgrades at Scale, Unattended"

**Visuals:** Workflow diagram — `Repo list → Claude Code → PocketFlow orchestration → npm install/build/test → PR`

**Script:**
> The Node.js story didn't end with one repo.
> We needed to do this across the entire estate — dependency upgrades,
> deprecation fixes, security and vulnerability patches, and full
> `npm install / build / test` cycles.
>
> Here's what I did:
> First, I vibed it — manual proof-of-concept with Claude Code,
> working through one repo interactively to understand every edge case.
> Then I automated it — wrapped the workflow in `claude -p`,
> and used **PocketFlow** as the orchestration layer.
> PocketFlow is an elegant agentic workflow library that let me
> define the upgrade pipeline as composable nodes: detect → patch → test → report.
>
> The result: unattended upgrades across hundreds of repos.
> No babysitting. No AWS SEG ticket. Ship it.

---

### SLIDE 4 — Case Study 2: vg-document-agent (90 sec)

**Slide title:** "vg-document-agent: Any Source → Any Doc Format, Automatically"

**Visuals:** Input/output diagram:
- Input: folder / GitHub URL / .pptx / .xlsx / .docx / .pdf / .html / .ipynb
- Processing: preprocess → knowledge graph → agentic RAG
- Output: README / tutorial / user-guide / CLAUDE.md / slidedeck → .html / .docx / .pdf

**Script:**
> With 5,000 IT staff using Claude Code, we hit a second problem:
> every project needed a `CLAUDE.md` — the context file Claude Code reads
> at the start of every session. Writing these by hand doesn't scale.
>
> So we built vg-document-agent.
> You give it any source: a folder, a GitHub URL, or raw files —
> PowerPoints, spreadsheets, Jupyter notebooks, PDFs, HTML.
> It preprocesses everything into structured markdown, crawls it to
> build a knowledge graph, then runs agentic RAG to generate
> whatever document style you need: README, tutorial, user guide,
> reference guide, slidedeck — or CLAUDE.md.
> Output lands in markdown and converts to HTML, Word, or PDF.
>
> The CLAUDE.md use case alone has measurably cut Claude Code onboarding
> time for new projects across our enterprise. Developers get a
> pre-loaded context file on day one — no `/init` required.

---

### SLIDE 5 — The Pattern (30 sec)

**Slide title:** "The Vibe-to-Enterprise Pattern"

**Visuals:** Repeatable loop diagram:

```
① Vibe it        — Interactive Claude Code session, prove the idea
② Automate it    — claude -p + PocketFlow orchestration
③ Deploy it      — Enterprise scale, unattended, observable
      ↓
  Repeat for the next pain point
```

**Script:**
> Both agents followed the same three-step pattern.
> Vibe it — work interactively with Claude Code until it solves the problem.
> Automate it — use `claude -p` for headless execution, PocketFlow for workflow.
> Deploy it — run at enterprise scale with no human in the loop.
> This pattern turns a weekend prototype into a production agent.
> The key insight: Claude Code is not just a coding assistant —
> it's the runtime for your enterprise automation.

---

### SLIDE 6 — Takeaway + Call to Action (20 sec)

**Slide title:** "What Pain Point in Your Team Could Claude Code Solve This Week?"

**Visuals:** Three bullets, one question

**Script:**
> Three things to take home:
> One — don't wait for enterprise tooling to catch up. Vibe it yourself.
> Two — `claude -p` + PocketFlow is your enterprise automation stack.
> Three — pre-generate `CLAUDE.md` at deploy time; your team will thank you.
>
> The question I'll leave you with:
> *What is the most painful, ticket-that-never-gets-done in your team right now?*
> That's your next Claude Code agent.
> Thank you.

---

## Timing Guide

| Slide | Content | Time |
|-------|---------|------|
| 1 | Hook — AWS SEG failure story | 0:30 |
| 2 | Vibe coding defined | 0:30 |
| 3 | vg-upgrade-agent | 1:30 |
| 4 | vg-document-agent | 1:30 |
| 5 | The repeatable pattern | 0:30 |
| 6 | Takeaways + CTA | 0:20 |
| **Total** | | **~5:00** |

---

## Key Messages (for Q&A preparation)

- **Why PocketFlow?** Lightweight, composable, no vendor lock-in. Designed for agentic workflows — nodes map cleanly to Claude Code invocations.
- **Why `claude -p` not the API?** Subscription billing, no per-token cost at scale during development. Production can migrate to API.
- **How do you handle failures in unattended runs?** PocketFlow nodes have retry logic; failures are logged and flagged for human review — the agent doesn't silently swallow errors.
- **CLAUDE.md and `/init`:** `/init` is interactive-only. Enterprise pre-generation requires `claude -p` with a crafted prompt — which is actually the recommended pattern per Anthropic's own docs.

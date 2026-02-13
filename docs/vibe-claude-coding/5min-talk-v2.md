# Vibe Coding Works, Is It Maintainable?

**Venue:** Anthropic Workshop — Power Talk (5 minutes)
**Speaker:** Wen Gong
**Audience:** Mixed engineers, managers, IT staff (~hundreds in-person + online)
**Version:** v2 — enterprise maintainability as central theme

---

## Slide-by-Slide Outline + Speaker Script

---

### SLIDE 1 — The Hook (30 sec)

**Slide title:** "Speed: Solved. Maintainability: Still a Question."

**Visuals:** Timeline bar — GPT-3 (2022) → today, with "prototype speed" in green and "enterprise maintainability" in amber/open

**Script:**
> Almost four years ago, I watched GPT-3 generate real code for the first time.
> I thought: the hard problem is solved.
>
> And in one sense it was — we can prototype almost anything in an afternoon now.
>
> But last week, at a major tech summit, I asked a prominent industry leader
> about enterprise maintainability in the age of vibe coding.
> His honest answer: *it's still an unsolved problem.*
>
> Four years in, I think he's right.
> This talk isn't about giving you the answer —
> it's about sharing what I've learned, and opening the conversation.

---

### SLIDE 2 — The Gap (30 sec)

**Slide title:** "AI Codes to the Ticket. Engineers Code to the System."

**Visuals:** Two columns
- Left: AI strengths — fast, working, narrow scope, consistent syntax
- Right: Still missing — big-picture architecture, system design, industrial best practices, 20 years of trial-and-error

**Script:**
> Here's the gap I keep running into.
> Claude Code is brilliant at solving the problem in front of it.
> It addresses the ticket — and it does it fast.
>
> What it still lacks is the big-picture perspective:
> module boundaries, dependency direction, what breaks at 10x scale,
> the design patterns that survive a team handover two years from now.
>
> That judgment comes from experience.
> And experience is still not something you can prompt for.

---

### SLIDE 3 — Case Study 1: vg-upgrade-agent (90 sec)

**Slide title:** "From Ad-Hoc Script to Enterprise Pipeline"

**Visuals:** Two-phase diagram
- Phase 1 (Prototype): Claude Code → working script, solves one repo
- Phase 2 (Hardened): PocketFlow nodes (detect → patch → test → report) + error recovery + observability

**Script:**
> Our first agent: vg-upgrade-agent.
> The problem — Node.js upgrades across hundreds of repos,
> plus dependency updates, deprecation fixes, security and vulnerability patches.
>
> With Claude Code, I had a working prototype quickly.
> It solved one repo. It worked in demos.
> But it was ad-hoc — narrow scope, no error recovery,
> no visibility into what failed, not something a teammate could maintain.
>
> That's where engineering judgment came in.
> I introduced **PocketFlow** — a lightweight agentic workflow library —
> to impose structure: composable nodes, each with a single responsibility.
> Detect dependencies. Patch. Run `npm install / build / test`. Report.
>
> Then a proper code review pass: edge cases Claude missed,
> idempotency so reruns don't cause damage, structured logging.
>
> The result: unattended upgrades across hundreds of repos.
> Not because AI got better — because experience shaped the architecture.

---

### SLIDE 4 — Case Study 2: vg-document-agent (90 sec)

**Slide title:** "From Naive Pipeline to Knowledge-Graph-Driven RAG"

**Visuals:** Input/output diagram
- Input: folder / GitHub URL / .pptx / .xlsx / .docx / .pdf / .html / .ipynb
- Processing: preprocess → **knowledge graph** → agentic RAG → generate
- Output: README / tutorial / user-guide / **CLAUDE.md** / slidedeck → .html / .docx / .pdf

**Script:**
> Our second agent: vg-document-agent.
> With 5,000 IT staff adopting Claude Code enterprise-wide,
> every project needed a `CLAUDE.md` — the context file that loads
> at the start of every session.
> Writing these by hand doesn't scale.
>
> The prototype was straightforward — ingest a repo, run RAG, generate markdown.
> It worked in demos. But it was brittle:
> naive chunking, no understanding of how the pieces related to each other,
> output that was technically accurate but architecturally shallow.
>
> The fix wasn't more prompting.
> It was a design decision: add a knowledge graph layer.
> Crawl the source, map relationships between modules, docs, and examples,
> *then* do agentic RAG against that structured understanding.
>
> That decision came from experience with how documentation fails at scale —
> not from anything Claude suggested.
>
> The result: any input source — folders, GitHub URLs, PowerPoints, PDFs, Jupyter notebooks —
> becomes any document format you need, with structural coherence.
> CLAUDE.md pre-generated on day one for every developer.

---

### SLIDE 5 — Closing the Gap: Code Quality in Practice (40 sec)

**Slide title:** "Your Experience Is the Differentiator"

**Visuals:** 5-point list

**Script:**
> So how do you inject engineering judgment into vibe coding?
> Five things that have worked for me:
>
> **One** — Architect before you vibe.
> Design your module map and interfaces yourself, then ask Claude to implement.
> Don't let Claude design while it codes.
>
> **Two** — Use CLAUDE.md as a quality contract.
> Put your standards, patterns, and anti-patterns in that file.
> Claude will follow them if you make them explicit.
>
> **Three** — Dedicated refactoring sessions.
> After a feature works, open a fresh session: "Improve the structure — don't fix bugs."
> Separate the "make it work" pass from the "make it right" pass.
>
> **Four** — Scope upward deliberately.
> Instead of "fix this bug" — say "fix this bug, and tell me if it reveals a design problem."
> Force the big-picture view.
>
> **Five** — Use workflow libraries like PocketFlow.
> Composable nodes enforce single responsibility naturally.
> Structure in the framework becomes structure in the code.

---

### SLIDE 6 — The Pattern + Call to Action (20 sec)

**Slide title:** "Vibe it → Judge it → Harden it → Deploy it"

**Visuals:** Four-step loop

```
① Vibe it    — prove the idea with Claude Code
② Judge it   — apply your engineering experience to the design
③ Harden it  — refactor, review, test, add observability
④ Deploy it  — automate with claude -p + PocketFlow, run at scale
```

**Script:**
> The pattern isn't three steps anymore — it's four.
> Vibe it. Judge it. Harden it. Deploy it.
>
> Claude Code handles the first and last steps brilliantly.
> Steps two and three are still yours.
>
> I don't have all the answers to the maintainability question.
> But I'm convinced this much is true:
> your years of experience are not a liability in the age of AI —
> they are the differentiator.
>
> Thank you.

---

## Timing Guide

| Slide | Content | Time |
|-------|---------|------|
| 1 | Hook — unsolved problem, 4-year perspective | 0:30 |
| 2 | The gap — AI codes to ticket, engineers code to system | 0:30 |
| 3 | vg-upgrade-agent — prototype → PocketFlow → enterprise | 1:30 |
| 4 | vg-document-agent — naive RAG → knowledge graph → production | 1:30 |
| 5 | 5 code quality techniques | 0:40 |
| 6 | 4-step pattern + CTA | 0:20 |
| **Total** | | **~5:00** |

---

## Code Quality Techniques — Extended Reference

*For Q&A, blog post, or follow-up discussion.*

### 1. Architect before you vibe
Define module boundaries, interfaces, and data flow before opening Claude Code.
AI implements to a spec well; it designs specs poorly.
A 30-minute whiteboard session before you start prompting saves hours of refactoring.

### 2. CLAUDE.md as a quality contract
Your `CLAUDE.md` is not just project context — it's your coding standards document.
Include: naming conventions, error handling patterns, logging approach, which libraries
to use (and which to avoid), module structure expectations.
Claude will follow them consistently across sessions.

### 3. Separate "make it work" from "make it right"
Vibe coding conflates these two passes. Keep them separate intentionally.
Session 1: prove the idea. Session 2: dedicated refactor — structure, naming, single
responsibility. Session 3: code review — edge cases, security, error paths.
Never ship straight from session 1.

### 4. Scope upward deliberately
Narrow prompts produce narrow fixes. Broaden the scope explicitly:
- "Fix this bug, and tell me if it reveals a design problem."
- "Add this feature, following the module pattern already established."
- "Review this for maintainability by a new engineer six months from now."

### 5. Use workflow libraries for agentic code
PocketFlow (and similar) force you to decompose problems into composable nodes.
This structural discipline naturally produces better code: each node has one job,
inputs and outputs are explicit, failure is contained and visible.
The library's constraints become your architecture's constraints.

### 6. Ask for trade-offs, not just solutions
"Give me three ways to implement this. For each, describe the maintenance burden
at 10x scale." This surfaces AI's awareness of alternatives and forces
you to apply your own judgment on the trade-offs.

### 7. The SOLID check
After a sprint of vibe coding, run an explicit review:
"Check this against SOLID principles. What would a senior engineer flag
in code review?" You'll catch what the narrow-scope sessions missed.

### 8. Write interfaces before implementations
Define function signatures, class contracts, and error types first.
Then ask Claude to implement. The interface design is where your
experience matters most — don't outsource it.

---

## Key Messages (for Q&A)

- **On maintainability being unsolved:** Industry leaders agree — this is not a solved problem. We're all figuring it out together. The techniques above are what's working *for me*, not a definitive answer.
- **Why PocketFlow?** Lightweight, composable, no vendor lock-in. The structure it imposes is a feature, not a constraint.
- **Why `claude -p` not the API?** Subscription billing during development; no per-token cost. Production agents can migrate to the API.
- **On CLAUDE.md:** `/init` is interactive-only. Enterprise pre-generation uses `claude -p` with a crafted prompt — Anthropic's own docs confirm this is the recommended approach.
- **On AI replacing engineers:** The opposite of the message here. Experience is the differentiator — AI amplifies it.

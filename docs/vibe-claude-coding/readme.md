# Vibe Coding Works, Is It Maintainable?

**Anthropic Workshop — Power Talk Proposal**
**Speaker:** Wen Gong

---

## Files in This Folder

| File | Purpose |
|------|---------|
| `proposal.md` | Submission form draft — abstract, bio, outline, takeaways |
| `5min-talk-v2.md` | Current talk — full slide outline + speaker script |
| `30sec-pitch.md` | Pitch video scripts (two versions) |
| `5min-talk-v1.md` | Archive — original draft, retired |

---

## v1 → v2: What Changed and Why

### v1 title: *Vibe Claude-Coding: From Easy Prototype to Enterprise Product*

The original draft led with a story about an enterprise toolchain failing a Node.js upgrade.
While vivid, it risked coming across as vendor-bashing — inappropriate for an event where
AWS is the company's primary cloud platform and decision-makers are in the room.

It also presented the story too positively: "AI solved it, here's the pattern." That framing
is accurate but incomplete. It skips the harder, more honest question.

### v2 title: *Vibe Coding Works, Is It Maintainable?*

The v2 reframe is built around a real and widely-recognized industry gap:

> **Vibe coding solves speed. Enterprise maintainability is still an open problem.**

This is grounded in four years of AI-assisted development experience (since GPT-3, summer 2022)
and validated in conversation with a prominent industry leader at MIT Sloan Tech Summit 2026,
who confirmed enterprise maintainability in the age of vibe coding remains unsolved.

The new framing is:
- **More honest** — doesn't claim to have all the answers
- **More credible** — speaks from 20+ years of Oracle and enterprise engineering experience
- **More useful** — closes with five concrete code quality techniques attendees can apply immediately
- **More inviting** — poses a question, opens a conversation rather than delivering a verdict
- **Politically neutral** — no vendor criticism; the hook is the industry problem, not a failure story

---

## Core Thesis (v2)

> "AI codes to the ticket. Experienced engineers code to the system.
> That gap hasn't closed in four years — and your experience is the differentiator."

---

## The Four-Step Pattern (v2)

```
① Vibe it    — prove the idea interactively with Claude Code
② Judge it   — apply engineering experience to the design
③ Harden it  — refactor, code review, test, add observability
④ Deploy it  — automate with claude -p + PocketFlow, run at scale
```

The "judge" step is where 20+ years of experience lives. v1 had a three-step pattern
(`vibe → automate → deploy`) that skipped this entirely.

---

## Case Studies

### vg-upgrade-agent
- **Problem:** Node.js upgrades, dependency updates, security/vulnerability patches across hundreds of repos
- **Stack:** Claude Code + PocketFlow workflow orchestration + `npm install/build/test`
- **The journey:** ad-hoc prototype → PocketFlow composable nodes → error recovery → unattended enterprise pipeline
- **Key point:** PocketFlow wasn't AI's suggestion — it came from workflow design experience

### vg-document-agent
- **Problem:** CLAUDE.md pre-generation and documentation at scale for a 5,000-person IT organization
- **Stack:** Claude Code + knowledge graph + agentic RAG → markdown → .html / .docx / .pdf
- **Input:** Any source — folder, GitHub URL, .pptx, .xlsx, .docx, .pdf, .html, .ipynb
- **Output:** Any doc style — README, tutorial, user-guide, reference-guide, slidedeck, CLAUDE.md
- **The journey:** naive RAG → knowledge graph architecture (human design decision) → production pipeline
- **Key point:** The knowledge graph layer came from experience with RAG failure modes at scale

---

## Code Quality Techniques (v2 addition)

Five techniques for injecting engineering judgment into vibe coding sessions:

1. **Architect before you vibe** — design module map and interfaces yourself; Claude implements to spec
2. **CLAUDE.md as a quality contract** — put coding standards, patterns, anti-patterns in the context file
3. **Separate "make it work" from "make it right"** — dedicated refactoring sessions after features work
4. **Scope upward deliberately** — "fix this bug AND tell me if it reveals a design problem"
5. **Use workflow libraries** — PocketFlow's composable nodes enforce single responsibility naturally

Extended reference (8 techniques, for Q&A and follow-up writing) is in `5min-talk-v2.md`.

---

## Submission Checklist

- [ ] Fill in `[YOUR INPUT: company name]` in `proposal.md` (3 places)
- [ ] Fill in `[YOUR INPUT: job title]` in `proposal.md` (2 places)
- [ ] Record 30-sec pitch video using `30sec-pitch.md` (primary script recommended)
- [ ] Attach or link pitch video to submission
- [ ] Confirm abstract length fits submission portal limit (150-word and 50-word versions available)

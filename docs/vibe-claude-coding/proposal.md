# Power Talk Proposal — Anthropic Workshop

> Fill in sections marked **[YOUR INPUT]** before submitting.

---

## Submission Form Fields

---

### Talk Title

**Vibe Coding Works, Is It Maintainable?**

*Subtitle (if allowed):*
Case Studies of Building Enterprise-Grade Agents with Claude Code

---

### Talk Format

- Type: Power Talk (Lightning Talk)
- Duration: 5 minutes
- Format: Slides + speaker narrative (no live demo)

---

### Abstract (150 words)

Almost four years since GPT-3 demonstrated AI code generation, one problem remains
stubbornly open: enterprise maintainability. Vibe coding makes us fast — prototypes
in an afternoon. But speed and production-readiness are not the same thing.
At a major tech summit last week, a prominent industry leader was asked about
enterprise code quality in the age of vibe coding. His honest answer: still unsolved.

This talk shares what four years of AI-assisted development — and 20+ years of
enterprise engineering at Oracle and beyond — have taught one practitioner about
bridging that gap. Two production agents are used as case studies:
**vg-upgrade-agent**, which handles Node.js upgrades, security patches, and full
`npm install/build/test` cycles unattended across hundreds of repos; and
**vg-document-agent**, which transforms any source into any document format via
knowledge-graph-driven agentic RAG.

The talk closes with five concrete techniques for injecting engineering judgment
into vibe coding — and an honest admission: this is a conversation, not a solution.

---

### Short Abstract (50 words, for programme listings)

Vibe coding solves speed. Maintainability is still an open question — industry leaders
agree. This talk shares four years of hard-won lessons bridging the gap, through two
production agents: vg-upgrade-agent (Node.js upgrades at scale, unattended) and
vg-document-agent (any source → any doc format). Plus five techniques you can use Monday.

---

### Key Takeaways (what attendees will leave with)

1. An honest framing of where vibe coding succeeds and where it still falls short — from someone with 20+ years of enterprise engineering experience
2. A four-step pattern — *vibe → judge → harden → deploy* — that produces maintainable enterprise agents, not just working prototypes
3. Five concrete code quality techniques for injecting engineering judgment into Claude Code sessions
4. How `claude -p` + PocketFlow bridges interactive prototype and unattended enterprise automation
5. A practical CLAUDE.md pre-generation strategy for enterprise Claude Code rollouts at scale

---

### Why This Talk / Why Now

The AI coding conversation is dominated by capability demos and enthusiasm.
What is missing is the honest practitioner's voice: someone who has been doing this
since GPT-3 in 2022, has shipped production agents at enterprise scale, and is
willing to name what isn't working yet.
Enterprise maintainability is that thing. Industry leaders at major tech conferences
are saying the same — it remains an open problem.
This talk contributes to that conversation with real case studies, concrete techniques,
and the credibility of 20+ years of enterprise engineering. It gives attendees
something they can apply immediately, and reframes their experience as an asset —
not a liability — in the age of AI.

---

### Talk Outline (for reviewers)

| # | Section | Time |
|---|---------|------|
| 1 | Hook: 4 years of AI coding, speed solved — maintainability still open; validated at major tech summit | 0:30 |
| 2 | The gap: AI codes to the ticket, engineers code to the system | 0:30 |
| 3 | Case study: vg-upgrade-agent — prototype → PocketFlow structure → enterprise-grade unattended pipeline | 1:30 |
| 4 | Case study: vg-document-agent — naive RAG → knowledge graph architecture → production at 5,000-person org | 1:30 |
| 5 | Five code quality techniques for injecting engineering judgment into vibe coding | 0:40 |
| 6 | Four-step pattern (vibe → judge → harden → deploy) + CTA | 0:20 |

---

### Speaker Bio (100 words)

Wen Gong is a **[YOUR INPUT: job title]** at **[YOUR INPUT: company name]** with 20+ years of
experience in enterprise software, data engineering, and SQL-based systems — including Oracle.
He has been working with AI code generation since GPT-3 in 2022 and leads Claude Code adoption
across a 5,000-person IT organization.
He has shipped two production AI agents — vg-upgrade-agent and vg-document-agent — applying
the principle that engineering experience, not just AI speed, is what makes code maintainable.
He is also the creator of SPL (Structured Prompt Language), a declarative SQL-inspired language
for LLM context management, co-created with Claude in a single session.

---

### Speaker Bio (30 words, short version)

**[YOUR INPUT: job title]** at **[YOUR INPUT: company name]**.
Creator of SPL (Structured Prompt Language) and builder of two production Claude Code agents
serving a 5,000-person IT organization.

---

### Supporting Materials

| Material | Location |
|----------|----------|
| 5-min talk script + slide outline (v2) | `docs/vibe-claude-coding/5min-talk-v2.md` |
| 30-sec pitch video script | `docs/vibe-claude-coding/30sec-pitch.md` |
| This proposal | `docs/vibe-claude-coding/proposal.md` |
| SPL project (live code example) | `https://github.com/digital-duck/SPL` |

---

### Session Preferences / Notes for Organizers (optional field)

- Happy to take questions during a panel or open floor after the lightning talks
- Can provide a live terminal demo of `claude -p` in action if a longer slot opens up
- Talk content is applicable to both technical and non-technical attendees; slides will
  be kept visual with minimal code

---

## Submission Checklist

- [ ] Fill in `[YOUR INPUT: company name]` (3 places)
- [ ] Fill in `[YOUR INPUT: job title]` (2 places)
- [ ] Confirm 150-word abstract fits the submission portal's limit
- [ ] Record 30-sec pitch video using `30sec-pitch.md`
- [ ] Attach or link pitch video to submission
- [ ] Review key takeaways match what the submission form asks for

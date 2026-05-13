# Daily Summary: TOPIC 2 - Use Case Selection

**Date:** May 13, 2026
**Topic:** When to Use Agents vs Traditional Code
**Status:** ✅ COMPLETED

---

## What I Learned Today

### The Core Insight
Agents are expensive (cost, complexity, latency). Use them ONLY when you need THINKING and REASONING. For simple rules and lookups, use code.

### The 3 Acid Test Questions
For ANY problem, ask:
1. Does it require thinking/judgment?
2. Are there multiple valid approaches?
3. Is the answer uncertain until you analyze?

If ALL YES → Agent. If ANY NO → Code.

### Examples I Mastered

**Correctly identified as CODE:**
- Email validation (fixed rules)
- Bulk discount calculation (fixed rule: qty > 100)
- Password strength check (fixed rules: 8+ chars, 1 number)

**Correctly identified as AGENT:**
- Spam detection (needs judgment about intent)
- Resume screening (needs judgment about fit + context)
- Code review (needs thinking to find bugs)

### The Key Realization

I initially thought "Resume Screening = CODE" because of pattern matching, but I corrected myself:

**"Claude reads carefully, reasons about context (JD + resume), checks REAL experience—that requires THINKING, not just pattern matching."**

This insight separates developers who understand agents from those who don't.

### Applied to My Project

My ValidatorAgent is the RIGHT choice because:
1. ✅ Needs thinking (analyze market, licensing, competition)
2. ✅ Multiple approaches (different ideas need different analysis)
3. ✅ Uncertain outcome (can't predict startup success with formula)

Why agent > code:
- **Code:** "Netflix clone? Netflix exists. Score 0." (too simple, wrong)
- **Agent:** "Netflix clone? Market saturated, licensing costs $Bs, no advantage. Score 22." (reasons through, accurate)

---

## What I Did

1. ✅ Learned the 3 acid test questions
2. ✅ Worked through 6 real examples (email, discount, password, spam, resume, code review)
3. ✅ Applied to my ValidatorAgent project
4. ✅ Committed TOPIC_2_USE_CASE_SELECTION.md to GitHub
5. ✅ Created memory hooks for long-term retention

---

## Key Takeaways

**When to build AGENT:**
- Problems that require thinking/judgment
- Multiple valid approaches exist
- Success criteria are uncertain
- Examples: Resume screening, project viability, code review

**When to build CODE:**
- Problems with fixed rules
- One correct answer
- Pattern matching sufficient
- Examples: Email validation, discount calculation, password strength

**Why this matters:**
- Saves 6 months building agents for code problems
- 10x better results for actual thinking problems
- Shows hiring managers you choose the right tool

---

## Memory Hooks Created

- **Topic 2 Memory:** `topic_2_use_case_selection.md`
  - The 3 acid test questions
  - Code vs Agent comparison
  - Examples you mastered
  - Applied to ValidatorAgent

---

## Next Topic

**TOPIC 3: Prompt Engineering**
- How to write better instructions for Claude
- Make your agent produce better results
- Structured prompts vs casual prompts
- How small prompt changes = big output improvements

---

## Confidence Level

⭐⭐⭐⭐⭐ (5/5)

I understand when agents are the right choice and why. I can explain the difference to someone else.

---

## Quick Self-Test

**Q: Should you use an AGENT to "check if this credit card is valid"?**
- A: No, that's a CODE problem. Just check the format/checksum (fixed rule).

**Q: Should you use an AGENT to "decide if we should hire this person"?**
- A: Yes, that's an AGENT problem. Needs thinking about fit, potential, culture (judgment + multiple approaches).

**Q: Why is your ValidatorAgent correct and not code?**
- A: Because it needs to think about market, licensing, team, capital (multiple factors + uncertain outcome). Code can't reason.

---
name: re-explain
description: Re-explain earlier content in simple, clear Chinese, filling in the context needed to follow it.
disable-model-invocation: true
---

# Re-Explain: restate in plain Chinese

Re-explain the earlier content, following these rules:

1. Start with 1-2 sentences on the background of the current discussion and where it has got to.
2. Write in short, direct, easy-to-understand Chinese. The full rules and the bad/good sentence pairs are in `references/plain-chinese.md`.
3. Explain each abbreviation and technical term the first time it appears. Avoid jargon and vague wording.
4. Use the terms the project already uses. Look them up in this order: `GLOSSARY.md` (follow `GLOSSARY-MAP.md` to the right one if the repo has more than one), `CLAUDE.md`, `AGENTS.md`, `README.md`, any glossary or vocabulary list, then names in the code. Read only the sources that bear on the content being re-explained. If there is no existing term, use the most ordinary Chinese word and say clearly that it is a term chosen only for this explanation. Don't coin new terms you don't need.
5. Focus on:
   - what is being done now;
   - why it is done this way;
   - how the previous step relates to this one;
   - what happens next.
6. Fill in the background needed to understand the current content. Don't assume the user remembers all the earlier details.
7. Decide whether a picture helps. The text explanation is always given in full; a picture only supplements it. When the user asks for a picture, or for none, do as they say. Otherwise draw one only when both hold:
   - The content has one of these shapes:
     - a flow with 3 or more steps, or with branches;
     - several parts that call or depend on each other;
     - a state that changes over time;
     - things placed or moving in space (vehicles on a map, devices in a rack, elements in a page layout);
     - a before/after or side-by-side comparison.
   - The earlier explanation carried that shape as a list (a sequence of IDs, a long chain of steps), leaving the reader to assemble it in their head. When it already made the shape clear and lost the reader on terms or long sentences, rewriting the text is the fix.

   When unsure, explain in text alone, and leave the choice unmentioned. Pick the lightest form that shows the shape: an ASCII diagram in the reply when all its frames together fit in 25 lines and 80 columns; an HTML page when they don't, or when it needs interaction. Draw either form by `references/visual.md`.

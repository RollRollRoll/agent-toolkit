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
4. Use the terms the project already uses. Look them up in this order: `GLOSSARY.md` (follow `GLOSSARY-MAP.md` to the right one if the repo has more than one), `CLAUDE.md`, `AGENTS.md`, `README.md`, any glossary or vocabulary list, then names in the code. If there is no existing term, use the most ordinary Chinese word and say clearly that it is a term chosen only for this explanation. Don't coin new terms you don't need.
5. Focus on:
   - what is being done now;
   - why it is done this way;
   - how the previous step relates to this one;
   - what happens next.
6. Fill in the background needed to understand the current content. Don't assume the user remembers all the earlier details.

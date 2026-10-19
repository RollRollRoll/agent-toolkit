# Simulated user script template

Generate the script in Phase 3 and finalize it before the run starts. During the driving loop, when you (the orchestrator) play the user, **answer strictly from the script**. For questions the script does not cover, improvise in a way that fits the persona, and record the improvised Q&A in the appendix at the end.

```markdown
# Script: <one sentence describing the user's task scenario>

## Background

<Who the simulated user is: role, technical level, situation.>

## Real intent

<The problem the user actually wants solved. It may differ from what they ask for in the first turn.>

## Hidden pain point

<Key information the user does not volunteer in the first turn. Reveal it only when the agent under test asks a related question.
This is the core mechanism for testing the target skill's ability to dig out intent.>

## Answer material

<Foreseeable questions → answers, one per line:>

- Asked about budget / timeline → "..."
- Asked who will use it → "..."
- Asked about the current solution → "..."

## Answer style

- Brevity: <e.g. no more than two sentences each time>
- Vagueness: <e.g. give a vague answer first, get specific only when pressed>
- Tone: <e.g. easygoing but impatient; shows annoyance when asked more than three questions in a row>

## Never-reveal boundary

<Information the user will not give no matter how they are asked (parts the simulated user has not thought through either), and how to respond when asked, e.g. "I don't know, your call.">

## Improvised answers (fill in during the run)

| Turn | Question from the agent under test | Improvised answer |
|------|------------------------------------|-------------------|
|      |                                    |                   |
```

## Example excerpt

> **Background**: ML engineer who runs model experiments every day and is not familiar with frontend work.
> **Real intent**: wants to know the status and results of every experiment at any time.
> **Hidden pain point**: does not even have a complete list of experiments. The "dashboard" is the solution he imagines, not the real need.
> **Answer style**: short, leans on technical terms; impatient with "why" questions.

## Writing requirements

- There must be a gap between the hidden pain point and the first-turn request ("what they literally ask for ≠ what they really need"); otherwise the test cannot measure intent digging.
- Answer material must cover at least every dimension the target skill explicitly requires asking about (write it against the Phase 1 instruction inventory).
- Any answer material that might be passed verbatim to the process under test must follow the blind-test red line and must not contain wording such as "test / evaluate" (测试 / 评估). Orchestration notes themselves must never be mixed into the per-turn prompt files.

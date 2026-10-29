# Visual rules

> Rules for the picture that supplements a re-explanation: an ASCII diagram in the reply, or an HTML page.
>
> **Scope**: the picture adds to the text explanation; it never replaces it. Like the text, it keeps every fact, condition, and limit.

## Shared rules

- **Every element has a source.** Each node, arrow, step, and position traces back to the text explanation or the source material (code, config, data files, logs in the conversation). Where the source is missing, mark that part "未确认", or leave it out. A picture made complete by guessing misleads more than no picture.
- **Same terms as the text.** Every box, node, and arrow label uses the exact term the text uses. A reader matching the picture against the text finds each label there.
- **Conditions sit on their branch.** When a step only happens under a condition, write that condition on the arrow or branch it governs.
- **One picture, one shape.** A flow and a dependency structure are two pictures. Give each picture a one-line Chinese caption saying what it shows.
- **Chinese labels.** Keep code names (functions, files, commands) as they appear in the code.

## Spatial pictures

A picture of things placed or moving in space needs their positions. Take the first source that exists:

1. **Real position data**: coordinates, sizes, row/column numbers found in code, config, data files, or the conversation. Draw to it.
2. **Known relations**: no positions, but which things are adjacent, contain each other, or come before or after each other. Draw a schematic from those relations and caption it "示意，位置和距离不按真实比例".
3. **Neither**: draw no spatial picture; explain in text alone.

Show movement with arrows from old position to new. When several moments matter, draw one frame per moment, keeping the layout fixed so only the moving things change. An HTML frame shows the whole layout. An ASCII frame may show only the region involved, with the same region, orientation, and scale in every frame.

## ASCII diagram

- Put it in a fenced code block right after the 1-2 sentence background, then continue with the text.
- Stay within 80 columns and 25 lines.
- A Chinese character takes two columns in a terminal. Align by display width, or keep Chinese labels outside closed boxes (on arrows, or after a `──>`) so misalignment cannot break the frame.

## HTML page

- **One self-contained file.** Inline all CSS, JS, and diagrams; draw diagrams as inline SVG. The page opens offline.
- **Location**: `${TMPDIR:-/tmp}/re-explain/<topic-slug>-<YYYYMMDD>.html`, outside the repository. The date is today's, the day the page is written. When that file exists, add `-2`, `-3`, and so on.
- **Structure**: a title naming the topic; the same 1-2 sentence background as the text; the pictures, each with its caption; under each picture, a short plain-Chinese explanation of its parts (follow `plain-chinese.md`). The page reads on its own, without the chat.
- **Readable everywhere**: legible in light and dark color schemes, at narrow window widths, and when printed.
- **Interaction earns its place**: add it only when it shows what a static picture cannot, such as stepping through a flow or a sequence of spatial frames with previous/next buttons, or highlighting a node's links on hover.
- **Hand-off**: after writing the file, try to open it (`open` on macOS, `explorer.exe "$(wslpath -w <path>)"` on WSL, `xdg-open` on other Linux). Whether or not that works, give the absolute path in the reply.
- **Fallback**: when the file cannot be written, say why in one line, then draw the key frames as ASCII diagrams in the reply.

The page is done when the file exists, its absolute path is in the reply, and every label on it matches a term in the text explanation.

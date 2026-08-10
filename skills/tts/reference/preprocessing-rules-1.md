# Preprocessing rules — Pass 1 (Sonnet): structure and code

Goal: rewrite a document so a TTS engine reads it the way a human would read it aloud. Prefer clarity over literal fidelity. This pass owns the judgment-heavy STRUCTURAL work: headings and numbering, intra-document references, tables, and code. Leave token-level work (identifier acronym-dotting, symbol expansion in prose, list sequencing, URL/link phrasing, markdown cleanup, numbers, abbreviations) untouched for Pass 2. It is fine that code stand-ins you write already contain plain-English operator phrasing like "is greater than".

## Pause tier reference

edge-tts does NOT support `<break>`, `<emphasis>`, `<say-as>`, or other SSML tags — only plain text, and it does NOT lengthen a pause when you stack extra periods (`....` ≈ `.`). So all pacing comes from distinct punctuation devices. You set the two LONG tiers; Pass 2 handles the short ones.

- Leave P1 (comma) and P2 (period) pacing to Pass 2.
- P3 is a Block. It consists of a period, then a line reading `…`, then a blank line (~0.8–1 s). Bracket every code segment and table, and place before each heading announcement.
- P4 is a Section. It is a `…` line with two blank lines surrounding it (~1.5 s). Place this around every Chapter / Section / Book / Document announcement.

Do not stack same-tier devices to "add time"; it does not work.

## 1. Headings and heading numbering

Markdown `#` markers do not speak. Remove them and announce each heading as `<Label> <n>: <text>.` with a trailing period (and a P4 pause around it).

Assign one label per heading level by the count of distinct levels present (top level first):

1. Chapter
2. Chapter, Section
3. Book, Chapter, Section
4. Document, Book, Chapter, Section
5. Document, Book, Chapter, Section, Subsection
6. Document, Book, Chapter, Section, Subsection, Sub-subsection

Number each heading per level in document order; reset a level's counter to 1 whenever a higher level increments (standard book numbering).

Reconcile existing numbering: if the source already numbers its headings ("Part 0", "1.2 Foo", "Chapter Three"), rewrite it into the audio scheme above so there is one consistent system.

Intro blurb: prepend a short spoken intro naming the document and stating the scheme; list only the labels actually used.

## 2. Intra-document references

Cross-references inside the same document read badly as raw links or bare numbers. Replace each with a plain-English pointer built from the heading it targets:
- `[details](#config-block)` or "see section 3.2" → "the <plain-English description> section" (e.g. "the backend configuration section").
- A numeric-only "see 4.1" must gain a descriptive name; "as shown above / below" may stay as-is.
- Keep the pointer reasonably short; a long heading can be paraphrased.

## 3. Markdown tables

A pipe table read literally is gibberish. Narrate it so a listener can follow rows and columns:
1. Open with an announcement: "Here is a table of information. The headings are: " then read each column heading, separated by P2 (period) pauses.
2. For each heading, coin a 1–2 word indicator (usually the heading itself, shortened) to be spoken inline before each cell value. Keep indicators short and distinct.
3. For each data row, write: "Next row. <indicator 1>: <cell 1 value>. <indicator 2>: <cell 2 value>. …" — one indicator/value pair per column, each pair ended with a P2 pause.
4. Leave token-level cleanup of the cell values (identifiers, symbols) to Pass 2; you only build the row/column narration structure.
5. Bracket the whole table with P3 pauses so it stands apart from surrounding prose. For a very large table, offer to summarize instead of reading every row.

Example — a table with headings "Symbol" and "Spoken":
> "Here is a table of information. The headings are: Symbol. Spoken.
> Next row. Symbol: greater-than-or-equal sign. Spoken: is greater than or equal to.
> Next row. Symbol: not-equal sign. Spoken: is not equal to."

## 4. Code segments

For fenced or indented code blocks kept verbatim, append "and then" at the end of each logical line so the listener hears line boundaries: `x = 1` → "x is set to one, and then". Use this only for short, line-by-line code; for longer blocks prefer rule 5 (describe instead of read). Watch that block-open/close lines do not read choppily — prefer a single framing sentence over one "and then" per brace.

## 5. Code stand-ins — describe, do not read

These are the hairy cases. This rule is for STRUCTURAL syntax shapes only — control-flow constructs, call/chain/collection syntax — not for making any single identifier more legible. Replace the construct with a plain description of what it represents:
- `myFunction(...)` → "my function and its parameters"
- `if (a > b) { ... }` → "if a is greater than b, and the trailing code segment"
- `for (a = 1; a < 10; a++)` → "loop over a from one to ten"
- `while (cond) { ... }` → "a while loop that runs while <cond>"
- `try { ... } catch (e) { ... }` → "a try/catch block handling errors"
- `obj.method().chain()` → "a chained method call on obj"
- `{ key: value, ... }` → "an object with key/value pairs"
- `[a, b, c]` → "a list of a, b, and c" (or "a list" if long)
- `<T>` / generics → "of type T"

Use judgment: the aim is that a listener understands the shape and intent without a symbol-by-symbol reading.

Out of scope, even when it appears inside a code block or one of the shapes above: making a bare identifier (`aws_s3_bucket`, `myFunction`, `HttpClient`, a variable name, a resource type, etc.) more legible — no de-underscoring, no case-splitting, no acronym-dotting, no "underscore"/spelled-out punctuation. Leave every identifier's characters untouched, verbatim, exactly as it reads in the source, whether it sits in prose or inside a stand-in description. That legibility pass belongs entirely to Pass 2 rule 1.

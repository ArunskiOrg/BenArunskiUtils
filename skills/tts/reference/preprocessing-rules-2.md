# Preprocessing rules — Pass 2 (Sonnet): token-level sweep

Goal: rewrite a document so a TTS engine reads it the way a human would read it aloud. Pass 1 already handled headings/numbering, the intro blurb, intra-document references, tables, and code stand-ins/segments. You apply EVERYTHING ELSE across the whole document, at the token level. Do NOT undo Pass 1's structural work — but DO apply the token rules below inside the narrated table cells and code stand-in descriptions where they contain identifiers, symbols, or acronyms.

## Pause tiers reference

edge-tts does NOT support `<break>`, `<emphasis>`, `<say-as>`, or other SSML tags — only plain text, and it does NOT lengthen a pause when you stack extra periods (`....` ≈ `.`). So all pacing comes from distinct punctuation devices. You set the two SHORT tiers; leave Pass 1's long tiers in place.

- P1 is a Clause. It is implemented as a comma `,` (~0.15 s). Use it for operands, sub-clauses, items in an inline list.
- P2 is a Sentence. It is implemented as a period `.` (~0.4 s). Use it for end of a sentence, each narrated list item, each code line.
- Leave every `…` line and its surrounding blank lines (Pass 1's P3 and P4 devices) exactly as they are. Do not stack same-tier devices to "add time"; it does not work. The global `--rate=-12%` already slows delivery; tiers control relative spacing only.

## 0. Folder structure
Folders do not read well. To help that:
- Name single folders
- Write out long folder names as a list
- Name files first, followed by their folder.

Each file and directory part is also subject to rule 1's identifier treatment. To keep the folder-speech pattern clear, the examples below don't yet show rule 1's acronym-casing and de-underscoring applied — combine both rules for the final text.

Examples:
- elide leading slashes. `/<directory tree>/<file>` reads the same as `<directory tree>/<file>`
- anything ending in a slash `<name>/` → "the <name> directory"
- `~` → "home." (with the period)
- tiered slashes `<a>/<b>/<c>/` → "the directory at a, b, c"
- parent directories `../../` → "the <n'th> parent directory", as in "the second parent directory". If followed by other directories, use "the <n'th> parent directory, then: "
- filenames `<directory structure>/file.ext` → "file.ext in <spoken directory>"
  - specific example: '~/Users/pat/myFile.pdf' → "myFile.pdf in the directory at home. users, pat."
  - specific example: '../../myDocs/archive/myfile.txt' → "my file dot text in the 2nd parent directory, then the directory my docs, archive."

## 1. Identifiers and names

Identifiers get two treatments together: structure (quote, de-underscore, case-split) and all-caps casing of each initialism segment.

- Acronym rule — this is the single canonical treatment for every initialism/acronym in the document, standalone in prose or inside an identifier (see rule 5's word-acronym exceptions like NASA/JSON, which stay unspelled words): a segment that is an initialism (letter-by-letter, not a dictionary word) becomes plain all-caps, no dots — `aws` → "AWS", `vpc` → "VPC", `tf` → "TF", `api` → "API". A digit fused to letters `s3` → "S3" Real-word segments stay lowercase words — `bucket`, `function`, `state`.
- snake_case → wrap in double quotes, drop underscores, all-cap each initialism segment: `my_function` → `"my function"`; `aws_s3_bucket` → `"AWS S3 bucket"`; `aws_S3_vpc` → `"AWS S3 VPC"`. The quotes read as a brief pause.
- camelCase / PascalCase → split at case boundaries, then all-cap any initialism segment: `myFunction` → "my function"; `HttpClient` → "Http client".
- SCREAMING_SNAKE constants → "the constant <words>": `MAX_RETRIES` → `the constant "max retries"`.
- Adjacent identifiers: when two or more identifiers sit next to each other (function arguments, tuple destructuring, chained names, multi-argument declaration headers like `resource "type" "name"`), two complex names run together are hard to follow. Narrate them as "the variable <x>, then variable <y>, then variable <z>" so each stands apart.
- Dots: version/namespace dots → "dot" (`v1.2` → "version one dot two", `os.path` → "os dot path"). File extensions: real-word extension keeps "dot" + word (`config.json` → "config dot Jason"); non-word extension drops the dot and becomes an all-caps acronym (`main.tf` → "main dot TF"; `state.hcl` → "state dot HCL"; `terraform.tfstate` → "terraform dot TF state"). Ordinary decimals/sentence periods unchanged (`3.14` → "3.14").
- File paths and folders: see rule 0 — it is the sole authority for all path/folder speech (trailing-slash directories, tiered paths, filenames-in-a-directory). Do not read a path as "slash"-joined segments inline; that duplicates rule 0 and conflicts with it. For URLs and links, see rule 4.

## 2. Lists

Rewrite ordered and bulleted lists into narrated sequence:
- First item → "First, …"
- Second item → "Next, …", then "Then, …" for each following item up to the penultimate.
- Last item → "Finally, …"

A two-item list is "First, …" then "Finally, …". A one-item list needs no sequence word. Nested lists: narrate the parent item, then introduce the sub-sequence ("…, which breaks down as follows. First, …"). End each item with a period.

## 3. Symbols and operators

Replace with their spoken English:
- `==` / `===` → "is equal to"; `!=` / `!==` → "is not equal to"
- `>=` → "is greater than or equal to"; `<=` → "is less than or equal to"
- `>` → "is greater than"; `<` → "is less than"
- `&&` → "and"; `||` → "or"; `!` (prefix) → "not"
- `->` / `=>` → "maps to" / "arrow" (by context: return / lambda)
- `+` `-` `*` `/` `%` → "plus", "minus", "times", "divided by", "modulo"
- `=` (assignment) → "is set to"; `++` / `--` → "increment" / "decrement"
- `&` `|` `^` `~` `<<` `>>` → "bitwise and / or / xor / not, left shift, right shift"
- `#` → "hash" (or "sharp" / "number" by context); `@` → "at"; `$` → "dollar" / describe
- `%` (format) → "a format placeholder"; backtick → drop it; standalone `_` → "underscore" if meaningful, else drop
- `0.0.0.0/0` → describe: "the entire internet"

Ordinary prose punctuation (commas, periods, question marks) stays.

## 4. Markdown and other cleanup

- `**bold**`, `*italic*`, `__x__` → keep the inner text, drop the markers.
- `[text](url)`, bare URLs, and other hyperlinks → announce a link without reading the address: "and here's a link to '<site>'s <page description> page." Never speak the full URL, query string, or tracking parameters. If there is no obvious site/page, fall back to "and here's a link to <text>."
- Images `![alt](src)` → read the alt text as "Image: <alt>." or drop if decorative.
- Blockquotes `>` → "Quote: …". Horizontal rules `---`, `***` → drop.
- Emoji and decorative glyphs → drop, or name if meaningful. HTML tags → strip, keep inner text.
- Inline-code backticks → drop the backticks (apply the identifier/symbol rules to the content).

## 5. Abbreviations and acronyms

- Expand read-as-phrase abbreviations: "e.g." → "for example", "i.e." → "that is", "etc." → "and so on", "vs." → "versus", "approx." → "approximately", "cf." → "compare".
- Initialisms read letter-by-letter → plain all-caps, no dots, same rule as rule 1's acronym rule regardless of context (prose or inside an identifier): `URL` → "URL", `SQL` → "SQL", `IAM` → "IAM". Plurals: `AZs` → "AZs".
- Word-acronyms (pronounced as a word, not spelled) stay as the spoken word — do NOT dot them: `NASA`, `JSON` ("Jason"), `README` ("read me"), `regex`, `CORS` ("cors"), `YAML` ("yamel"), `SQL` when you say "sequel". When unsure whether a token is spelled or spoken, prefer the common developer pronunciation and flag it as a doubt.
- Numbers: leave normal cardinals as digits (the engine reads them). Spell out where ambiguous (version numbers per rule 1; `1-10` → "one to ten"). Read bare digit strings like ports as separate digits: `5432` → "5 4 3 2".

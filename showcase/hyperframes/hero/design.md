# Skill X hero composition — design source of truth

Tokens are taken from the site itself: `showcase/build_index.py` CSS `:root`.
Do not invent colors or fonts.

## Colors

| Role | Value |
| --- | --- |
| background | `#0A0D11` |
| surface | `#141A21` |
| line | `#232C38` |
| line-2 | `#33404F` |
| text | `#E6EAF0` |
| text-2 | `#98A5B5` |
| text-3 | `#6A7686` |
| accent | `#FF6B2C` |
| accent-2 | `#FF9351` |
| signal | `#4A9EFF` |
| ok | `#3DD68C` |

## Type

- mono / display: `ui-monospace, "Cascadia Code", Consolas, monospace`
- sans / CJK: `"Segoe UI", "Microsoft YaHei", sans-serif`

## Rules

- One accent (orange) owns the frame; signal blue only for secondary marks.
- Hairline borders around `rgba(255,255,255,.08)`.
- Solid or radial backgrounds only; no full-screen linear gradient fills.
- Numbers use tabular figures.

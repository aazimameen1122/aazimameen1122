# How these profile cards work

Adapted for Aazim Ameen from Avi Vashishta's method:
https://www.avivashishta.com/blog/github-profile-readme-animated-svg-cards

## Why SVG cards

A GitHub README can't run JavaScript or load CSS. What survives is `<img>`,
`<a>`, `<picture>`, `width` and `align`. So the layout lives in `README.md`
and everything visual lives inside the images in `cards/`:

- An SVG shown through `<img>` is sandboxed (no scripts, no external
  requests), but its own `<style>` block runs — CSS keyframes work, and so
  does SMIL (`<animate>`, `<set>`).
- Fonts can't be loaded, so Noto Serif / Noto Sans / Noto Sans Mono are
  subset with `pyftsubset` to printable ASCII + a few symbols and embedded
  as base64 WOFF data URIs (12–15 KB each) in every card.
- Animations are staggered so the page plays top to bottom: hero → blue
  graph → monthly bars → three tiles → repo cards. Everything is disabled
  under `prefers-reduced-motion`.

## Cards

| File | What it shows |
| --- | --- |
| `cards/hero.svg` | Name (serif, with a SMIL shine sweep), one-liner, ASCII portrait of the GitHub avatar printing in row by row |
| `cards/heatmap.svg` | The last year of contributions in blue, one cell per day |
| `cards/activity.svg` | Contributions per month (best month in blue) + total, active days, best streak, busiest day |
| `cards/build.svg` | Tile: public repositories (both accounts) — SMIL count-up |
| `cards/lens.svg` | Tile: years behind the camera |
| `cards/language.svg` | Tile: Burushaski words archived |
| `cards/repo-*.svg` | One card per featured project |

## Data — honest numbers only

`scripts/fetch_contributions.py` scrapes the public contribution calendars
of **both** accounts (`aazimameen1-dotcom` + `aazimameen1122`) from
`github.com/users/<username>/contributions`, merges them day by day, and
writes `data/contributions.json`. It also records the combined public-repo
count via the GitHub API. No token is needed and nothing is estimated:
if GitHub changes the calendar markup, the fetch fails loudly instead of
rendering invented numbers.

The lens (6+ years) and language (63+ archive entries) tile numbers are
editorial constants in `scripts/render_readme_cards.py` (`TILES` /
`tile_values`) — update them there when they change.

## Daily refresh

`.github/workflows/render-cards.yml` runs at 03:30 UTC (09:00 IST) daily:
fetch data → regenerate the ASCII portrait from the current avatar →
re-render the cards → commit if anything changed.

## Local preview

```bash
python scripts/fetch_contributions.py
python scripts/make_portrait.py        # needs Pillow
python scripts/render_readme_cards.py  # animated cards -> cards/
STATIC=1 python scripts/render_readme_cards.py
# STATIC=1 renders the final frame only — screenshot that before pushing.
```

## Publishing

This folder is the content of the profile repository
`<username>/<username>`. Push it to a repo with exactly that name and the
README appears on the profile page.

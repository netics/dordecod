## What changes

<!-- One or two sentences. For new jokes, paste them below in both languages. -->

## Type

- [ ] New content (Code article, dictionary entry, excuse, Jira row, FAQ…)
- [ ] Edit to existing content
- [ ] Design / CSS
- [ ] SEO, structured data, `llms.txt`, robots, sitemap
- [ ] Build, scripts, Vercel config

## Content checklist

<!-- Skip this section if no copy changed. -->

- [ ] Romanian and English versions are both included and each is funny on its own
- [ ] Romanian uses correct diacritics (ă â î ș ț, with a comma below) and „…” quotes
- [ ] New Code articles are appended at the end. Existing articles are **never renumbered**, because people link to `#art-N`.
- [ ] No real names, companies, politics, or jokes at the expense of any group
- [ ] `MODIFIED` in `build.py` is bumped (it feeds JSON-LD `dateModified`, sitemap `lastmod` and the footer)

## Build checklist

- [ ] Ran `python3 build.py`, the self-checks pass, and `public/` + `vercel.json` are committed
- [ ] If the OG images changed: ran `python3 build.py --images` and bumped `OG_VERSION`
- [ ] Checked `/` and `/en/` locally (`python3 -m http.server 8000 -d public`) on mobile and desktop widths
- [ ] Nothing in `public/` was edited by hand. Everything there comes from `build.py`.

## After merge

- [ ] Vercel production deploy is green
- [ ] `scripts/smoke.sh https://www.dordecod.ro` passes
- [ ] For content changes: `scripts/indexnow.sh https://www.dordecod.ro`

## Screenshots

<!-- For visual changes: before / after, RO and EN. -->

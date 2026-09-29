# dordecod

**Dor de codul românesc**: a bilingual (RO/EN) humour site for Romanian developers and for the PMs and CTOs who work with them. Made by [Sergiu Vlad](https://sergiuvlad.com).

The site includes:
- The Romanian Developer's Code, the Romanian-to-corporate dictionary and the official excuse generator
- Jira translated, an estimate converter and standup bingo for PMs
- A spec sheet and FAQ for CTOs

It is fully static, with no forms, no cookies, no analytics and no third-party requests. Fonts are self-hosted.

## Layout

| Path | What |
|---|---|
| `build.py` | Generator (Python 3, standard library only). All page copy lives here. |
| `content/jokes.json` | The jokes: Code articles, excuses, dictionary, Jira, FAQ and the rest |
| `src/` | CSS, the mascot SVG and the stitch pattern |
| `public/` | Generated output, committed and served by Vercel as-is |
| `vercel.json` | Generated. Headers, CSP, caching, trailing slashes |
| `scripts/` | Post-deploy smoke test and IndexNow ping |

## Build

```bash
SITE_URL=https://your-domain python3 build.py
```

To also regenerate the favicons and OG images (needs Chrome, `rsvg-convert` and `magick`):

```bash
SITE_URL=https://your-domain python3 build.py --images
```

The build checks itself and fails if the canonical URLs, hreflang, sitemap, anchors or JSON-LD drift apart. After changing content, bump `MODIFIED` in `build.py`. After changing the OG images, bump `OG_VERSION`.

## Run locally

```bash
python3 -m http.server 8000 -d public
```

## What the build produces for SEO and AI

- One static URL per language: `/` (ro) and `/en/` (en), with a self-referencing canonical, reciprocal hreflang and `x-default`
- JSON-LD `@graph` per page: WebSite, WebPage (linked with `workTranslation`), Person (author), SatiricalArticle with an ItemList of the Code, DefinedTermSet (dictionary) and FAQPage. The fictional reviews are intentionally not marked up and are wrapped in `data-nosnippet`.
- Open Graph and Twitter card tags, with versioned 1200×630 PNG images per language
- `sitemap.xml` with hreflang alternates, and `robots.txt` that allows search and AI crawlers explicitly, with Content Signals
- `llms.txt`, `llms-full.txt`, and markdown twins (`/index.md`, `/en/index.md`) that carry a canonical `Link` header back to the HTML
- Stable anchors for every quotable item: `#art-N`, `#dict-…`, `#faq-N`, `#jira-N`, `#scuza-N`
- A favicon set (ico, svg, 96px, apple-touch), a web manifest, and theme colours for light and dark mode

## Deploy checklist

1. Import the repo in Vercel. `vercel.json` sets `outputDirectory: public`, and no build command is needed.
2. Add the custom domain, then rebuild with `SITE_URL` set to it, commit and push.
3. Redirect the `*.vercel.app` production alias to the custom domain (Vercel → Domains).
4. Keep Vercel Firewall → Bot Management → "AI Bots" off, or set it to Log.
5. Verify the domain in Google Search Console with DNS, import it into Bing Webmaster Tools, and submit `sitemap.xml` to both.
6. Run `scripts/smoke.sh https://your-domain`, then `scripts/indexnow.sh https://your-domain`.
7. Check the previews with the Facebook Sharing Debugger, LinkedIn Post Inspector and validator.schema.org.

## Contributing

To add a Code article or dictionary entry, open a pull request. Append new articles at the end and never renumber them, because people link to `#art-N`.

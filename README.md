# dordecod

**Dor de codul românesc**: a single-page, bilingual (RO/EN) humour site for Romanian developers and for the PMs and CTOs who work with them.

- The Romanian Developer's Code, the Romanian-to-corporate dictionary and the official excuse generator
- Jira translated, an estimate converter and standup bingo for PMs
- A spec sheet, FAQ and client reviews for CTOs

It is one static `index.html` with no build step, no forms and no data collection. The only thing it stores is your language choice, in `localStorage`.

## Run locally

```bash
python3 -m http.server 8000
```

## Deploy

Import the repo in Vercel. The framework preset is "Other", with no build command and no output directory. Vercel serves `index.html` from the root.

## Contributing

To propose a new Code article or dictionary entry, open a pull request.

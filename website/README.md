# ehubX website

Static site for GitHub Pages, aimed at non-modellers: what ehubX is, use cases, projects and publications. No build step.

## Editing content

Projects, publications and the contributor list are in [`data/content.js`](data/content.js). Add or edit entries there; the page renders them automatically. Entries with `todo: true` show a **draft** badge. Remove that line once an entry has been checked.

Page text (about, how it works, use cases, get started) is in [`index.html`](index.html). Styles are in [`assets/style.css`](assets/style.css).

## Preview locally

Open `index.html` in a browser, or run:

```
python -m http.server -d website 8000
```

## Deployment

The workflow [`.github/workflows/pages.yml`](../.github/workflows/pages.yml) publishes this folder on every push to `main` that touches `website/`.

One-time setup: in the GitHub repository, go to **Settings → Pages → Build and deployment** and set **Source** to **GitHub Actions**. The site will be available at `https://uesl-empa.github.io/ehubx/`.

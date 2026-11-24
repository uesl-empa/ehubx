# ehubX website

Static site for GitHub Pages, aimed at non-modellers: what ehubX is, use cases, projects and publications. No build step.

## Editing content

Projects, publications, theses and the contributor list are in [`data/content.js`](data/content.js). Add or edit entries there; the pages render them automatically. Projects with `featured: true` also appear on the home page; the home page shows the three newest publications. Entries with `todo: true` show a **draft** badge. Remove that line once an entry has been checked.

The site has three pages:

- [`index.html`](index.html): home page with the about, how it works, use cases, team and get started text, plus featured projects and the newest publications
- [`projects.html`](projects.html): all projects
- [`research.html`](research.html): all publications and student theses

The header and footer are repeated in each page, so change them in all three. The "Sign up for updates" button (home page, "Stay informed" section) and the footer "Updates" link point to the sign-up form; if the form moves, change the link in all three pages. Styles are in [`assets/style.css`](assets/style.css).

## Fonts, citation and search files

- Fonts (Inter, JetBrains Mono) are served from [`assets/fonts/`](assets/fonts/), not from Google. Licence notes are in the README there.
- The "How to cite" box on the home page cites the ehubX paper first. When the paper is published in a journal, update that BibTeX entry. The software entry has no version on purpose, so it does not go stale.
- [`sitemap.xml`](sitemap.xml) lists the three pages. Add a line there when you add a page.
- [`404.html`](404.html) uses absolute paths starting with `/ehubx/`. If the site moves to a different address, update them.

## Preview locally

Open `index.html` in a browser, or run:

```
python -m http.server -d website 8000
```

## Deployment

The workflow [`.github/workflows/pages.yml`](../.github/workflows/pages.yml) publishes this folder on every push to `main` that touches `website/`.

One-time setup: in the GitHub repository, go to **Settings → Pages → Build and deployment** and set **Source** to **GitHub Actions**. The site will be available at `https://uesl-empa.github.io/ehubx/`.

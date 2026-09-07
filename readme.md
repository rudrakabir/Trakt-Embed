# Trakt Watch History Widget

**A small window into what you've been watching.**

Show your latest episode and movie on your website. A scheduled GitHub Action reads your **public Trakt profile**, generates HTML and JSON, and optionally adds TMDB posters.

**No Trakt VIP, Trakt API key, sign-in cookies, or always-on computer needed for the public-profile reader.**

[Live example](https://rudrakabir.com/now/) · [Report an issue](https://github.com/rudrakabir/Trakt-Embed/issues) · [Buy Me a Coffee](https://www.buymeacoffee.com/rudrakabir)

## How it works

1. A fresh, signed-out Chromium browser opens your public profile's show and movie views.
2. Python reads the latest displayed history entry in each view.
3. Optional TMDB artwork is added when an exact, unambiguous title match exists.
4. GitHub Actions publishes `trakt_embed.html` and `trakt_data.json` every six hours.
5. Your website reads the JSON on page load, without needing a new website deployment.

The public page exposes **watch dates, not exact times**. The widget preserves that precision. A missing history section, unrecognized date, changed layout, or network failure fails the update and retains the previous published files.

This is a reader for Trakt's public website, not an official API integration. Page changes can break it. Private profiles are unsupported by this reader; no login or access-control bypass is attempted.

## Set up scheduled updates

Fork this repository and enable GitHub Actions. In **Settings → Secrets and variables → Actions**, set:

| Setting | Type | Purpose |
|---|---|---|
| `TRAKT_USERNAME` | Optional variable | Public profile username; defaults to repository owner |
| `TMDB_ACCESS_TOKEN` | Optional secret | TMDB API Read Access Token for posters |

Run **Actions → Update Trakt Embed HTML → Run workflow** to verify setup. The schedule runs at minute 17 every six hours. GitHub may delay scheduled runs or disable inactive schedules.

Your computer can be off. GitHub runs the reader, and visitors load the saved feed.

## Run locally

Use Python 3.10+:

```sh
git clone https://github.com/rudrakabir/Trakt-Embed.git
cd Trakt-Embed
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt playwright
python -m playwright install chromium
python public_history.py --username YOUR_USERNAME
```

Set the optional `TMDB_ACCESS_TOKEN` environment variable before running for artwork. Otherwise, cards use a local placeholder.

## Add it to your website

Host the generated HTML on your static website and embed it in an iframe, or copy `widget.css` and `widget.js` into your site and use the JSON feed:

```html
<link rel="stylesheet" href="/assets/widget.css">
<section class="trakt-embed"
  data-trakt-feed="https://raw.githubusercontent.com/YOUR_NAME/Trakt-Embed/main/trakt_data.json">
  <header><h1>Recently watched</h1><span class="badge">Trakt</span></header>
  <div class="trakt-cards"><!-- Saved cards copied from trakt_embed.html --></div>
  <footer><span class="trakt-status" role="status"></span>
    Watch history from <a href="https://trakt.tv">Trakt</a>.
    Artwork from <a href="https://www.themoviedb.org">TMDB</a>.<br>
    This product uses the TMDB API but is not endorsed or certified by TMDB.
  </footer>
</section>
<script src="/assets/widget.js" defer></script>
```

Replace `YOUR_NAME` with the repository owner. Supply saved cards for visitors without JavaScript and for failed requests. The script validates the feed and inserts titles as text. CDN caching may delay a newly published update.

To use a static Jekyll include, extract the generated section and its style into `_includes/trakt_embed.html`, then add `{% include trakt_embed.html %}` to your page. A static include changes only after a site rebuild; the JSON integration updates independently.

## Optional official API mode

`images.py` remains available for accounts with a valid Trakt application ID:

```sh
python images.py --username YOUR_USERNAME --json-output trakt_data.json
```

Set `TRAKT_CLIENT_ID` first. For private-profile local use, `embed.py` supports device authorization and `images.py --username me` uses `TRAKT_ACCESS_TOKEN`. Publishing output makes the displayed history public.

Trakt currently restricts application registration, and some existing personal applications have stopped working. The default scheduled workflow does not depend on those credentials.

## Test and customize

```sh
python -m unittest discover -s tests -v
```

Tests cover public date parsing, changed pages, API failures, preserved output, escaping, optional artwork, and authorization helpers. They need no real credentials. Edit `widget.css` to adjust the visual design.

## Credits and support

Built by **[Rudra Kabir](https://github.com/rudrakabir)** with [Trakt](https://trakt.tv) watch history and optional [TMDB](https://www.themoviedb.org) artwork.

This product uses the TMDB API but is not endorsed or certified by TMDB.

☕ **[Buy Me a Coffee](https://www.buymeacoffee.com/rudrakabir)** if you find this useful.

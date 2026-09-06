# Trakt Watch History Widget

**A small window into what you've been watching.**

Display your latest watched episode and movie on a personal website, with optional poster artwork and a responsive light/dark design. Python publishes static HTML and a tiny JSON feed; GitHub Actions refreshes them every six hours.

**[See it on my Now page](https://rudrakabir.com/now/)** · [Report an issue](https://github.com/rudrakabir/Trakt-Embed/issues) · [Buy Me a Coffee](https://www.buymeacoffee.com/rudrakabir)

## Why this approach?

- **Public history needs no OAuth.** A Trakt application ID and public username are enough. No expiring personal tokens or secret-writing PAT is needed for scheduled updates.
- **No visitor-facing API credentials.** Visitors read generated display data, not your Trakt or TMDB keys.
- **Failed requests preserve the last good output.** Authentication, rate-limit and service errors fail the workflow instead of publishing empty history.
- **Artwork is optional.** Missing posters have a local placeholder.
- **One feed, multiple websites.** A website can fetch the JSON without rebuilding every time you watch something.

Publishing the output makes the displayed watch history public.

## Quick start

Use Python 3.10+ and create an application in [Trakt's application settings](https://trakt.tv/oauth/applications).

```sh
git clone https://github.com/rudrakabir/Trakt-Embed.git
cd Trakt-Embed
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `TRAKT_CLIENT_ID` and your public `TRAKT_USERNAME` in `.env`. For posters, optionally add your **TMDB API Read Access Token** as `TMDB_ACCESS_TOKEN`.

```sh
python images.py --json-output trakt_data.json
```

This generates `trakt_embed.html` and `trakt_data.json`. The JSON contains only the title, episode details, watch date and poster URL needed for display. It omits account credentials and raw history records.

## Scheduled updates

In **Settings → Secrets and variables → Actions**, configure:

| Setting | Type | Purpose |
|---|---|---|
| `TRAKT_CLIENT_ID` | Secret | Trakt application ID |
| `TMDB_ACCESS_TOKEN` | Optional secret | Poster artwork |
| `TRAKT_USERNAME` | Optional variable | Public Trakt username; defaults to the repository owner |

Run **Actions → Update Trakt Embed HTML → Run workflow** once to verify setup. The schedule runs every six hours, at minute 17, and commits only changed generated files. GitHub may delay scheduled runs or disable inactive schedules; re-enable the workflow if that happens.

The scheduled workflow is for **public profiles**. It does not refresh OAuth tokens or require a PAT.

## Add it to your website

### Static HTML

Host `trakt_embed.html` on your static website and embed it:

```html
<iframe src="/trakt_embed.html" title="Recently watched on Trakt"
        width="100%" height="540" style="border:0" loading="lazy"></iframe>
```

A GitHub repository file page is not an HTML hosting URL. Copy the generated file into your site's published directory, and adjust the iframe height for long titles.

### Jekyll fragment

```sh
python images.py --fragment --output /path/to/site/_includes/trakt_embed.html
```

Then use `{% include trakt_embed.html %}` in your page. Static includes change only when your site is rebuilt.

### Live JSON feed

Copy `widget.css` and `widget.js` to your website. Wrap your saved cards in `.trakt-cards` inside a `.trakt-embed` element:

```html
<link rel="stylesheet" href="/assets/widget.css">
<section class="trakt-embed"
  data-trakt-feed="https://raw.githubusercontent.com/YOUR_NAME/Trakt-Embed/main/trakt_data.json">
  <header><h1>Recently watched</h1><span class="badge">Trakt</span></header>
  <div class="trakt-cards"><!-- Saved cards from the generated HTML --></div>
  <footer><span class="trakt-status" role="status"></span>
    Watch history from <a href="https://trakt.tv">Trakt</a>.
    Artwork from <a href="https://www.themoviedb.org">TMDB</a>.<br>
    This product uses the TMDB API but is not endorsed or certified by TMDB.
  </footer>
</section>
<script src="/assets/widget.js" defer></script>
```

Replace `YOUR_NAME` with the repository owner. The script validates the feed, inserts titles as text, formats dates in the visitor's timezone, and retains saved cards if fetching fails. Supply saved cards for visitors without JavaScript. Updates appear on the next page load after the feed and CDN refresh.

## Optional private-profile authorization

For a private profile, set `TRAKT_CLIENT_ID` and `TRAKT_CLIENT_SECRET`, run `python embed.py`, and follow the device authorization instructions. It saves tokens to your ignored `.env` file without printing them.

Run `python images.py --username me` to use that authorization locally. Exit code 10 means authorization failed; authorize again when needed. Private-profile token renewal is not part of the public scheduled workflow. Do not publish private history unless you intend it to be public.

## Troubleshooting and development

- **HTTP 401/403:** check the application ID, profile visibility and, when using `me`, authorization.
- **HTTP 429 or service error:** retry later; the existing published output is preserved.
- **No watch history yet:** Trakt returned an empty list for that media type.
- **Missing poster:** check the optional TMDB token; some records have no matching artwork.
- **Stale website:** check the workflow result and JSON feed, then the site's integration. A static include also requires a site deployment.

Customize `widget.css`, then regenerate. Tests use mocked HTTP responses and need no real credentials:

```sh
python -m unittest discover -s tests -v
```

## Credits and support

Built by **[Rudra Kabir](https://github.com/rudrakabir)** with [Trakt](https://trakt.tv) and optional [TMDB](https://www.themoviedb.org) artwork.

This product uses the TMDB API but is not endorsed or certified by TMDB.

☕ **[Buy Me a Coffee](https://www.buymeacoffee.com/rudrakabir)** if you find this useful.

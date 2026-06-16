# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Jekyll static site (a fork of [ai-deadlines](https://github.com/paperswithcode/ai-deadlines)) showing countdown timers to HCI conference paper deadlines. The live site is served by GitHub Pages directly from the `gh-pages` branch — there is no separate build/deploy step; pushing to `gh-pages` publishes.

Conference data upstream is intended to come via PRs to the separate [conf-database](https://github.com/hci-deadlines/conf-database) repo, but in this fork `_data/conferences.yml` is edited directly here.

## Commands

```bash
bundle install                      # one-time: install Ruby gems (uses Bundler + github-pages gem)
bundle exec jekyll serve --livereload   # local dev server with autoreload
bundle exec jekyll build            # build into _site/
bundle exec jekyll build --future   # build including future-dated content (matches CI)
bundle exec jekyll clean            # remove _site/ and caches
./bin/serve-local                   # serve with local personal-filter mode enabled (see below)
python3 utils/export_calendar.py    # write my-calendar.ics from conferences + local_filter
```

Link checking (run in CI via `.travis.yml`):
```bash
bundle exec htmlproofer ./_site --only-4xx --check-favicon --check-html --url-ignore "/#.*/" --http-status-ignore "400,441"
```

There is no test suite. Validation = `jekyll build` succeeds + htmlproofer passes.

## Architecture

### Data is the source of truth
- `_data/conferences.yml` — one YAML record per conference instance. Key fields: `title`, `year`, `id` (unique, e.g. `chi2026`), `deadline` (with `timezone` like `UTC-12`), optional `abstract_deadline`, `place`/`date`/`start`/`end`, and `sub` (one tag or a list, e.g. `['HCI', 'GM']`).
- `_data/types.yml` — defines the subject tags (`HCI`, `CSCW`, `XR`, …), their display names, and the colors used throughout the UI. Adding a new `sub` value to a conference requires a matching entry here.

### Rendering is mostly client-side
`index.html` and `_pages/conference.html` (permalink `/conference/`) emit the conference data as JSON via Liquid, then JS in `_includes/` computes countdowns, filtering, and sorting in the browser:
- `load_data.js` exposes `site.data.types` to JS and builds `sub2name`/`name2sub` maps.
- `multiselect_handler.js`, `utils.js`, `handle_url_retrieval.js` drive the subject filter checkboxes and per-conference deep links.
- `calendar.js` / `calendar.html` render the calendar view.

### Calendar (.ics) subscription
`_layouts/calendar.ics` is a Liquid template that generates an iCal feed from `conferences.yml` (one VEVENT per deadline / abstract deadline, with timezone conversion). This is the *published, shareable* feed.

### `_plugins/data_page_generator.rb`
Inherited from upstream — a generic Jekyll generator that can create one page per data record (driven by a `page_gen` config key). It is **not currently wired up** in `_config.yml`; conference detail pages use the single JS-driven `/conference/` page instead. Leave it unless you intentionally enable `page_gen`.

## Local personal-filter mode (this fork's main addition)

A way to view/export only the conferences *you* care about without touching the published data. It is git-ignored and opt-in.

Setup:
```bash
cp _config.local.yml.example _config.local.yml
cp _data/local_filter.yml.example _data/local_filter.yml   # then edit filter rules
```

`_data/local_filter.yml` supports (all combined with AND): `subs` (keep only these subject tags), `include_ids` (whitelist), `exclude_ids` (blacklist), `min_year`.

**The filter logic exists in three places that must stay in sync:**
1. `_includes/conf_filter.liquid` — the canonical Liquid implementation. It sets `include_conf` and is `{% include %}`d by both `index.html` (twice) and `_layouts/calendar.ics`. It only filters when `site.local_mode` is true (set by `_config.local.yml`), so the published site is unaffected.
2. `utils/export_calendar.py` — a standalone Python reimplementation of the same rules that writes `my-calendar.ics` (git-ignored personal feed).

If you change the filtering semantics, update both `conf_filter.liquid` and `export_calendar.py`.

`bin/serve-local` requires `_config.local.yml` + `_data/local_filter.yml` to exist, pins Ruby 3.1 via Homebrew on PATH, and serves with `--config _config.yml,_config.local.yml`.

## Notes
- `.gitignore` covers the local-mode files (`_config.local.yml`, `_data/local_filter.yml`, `my-calendar.ics`) — don't commit them.
- Some inline docs/comments in the fork-specific files are written in Chinese; preserve them when editing those files.

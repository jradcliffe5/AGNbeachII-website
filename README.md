# GGOS-Africa 2026 Website

Static conference website for GGOS-Africa 2026 — the official launch of GGOS-Africa (4–8 May 2026, Naivasha, Kenya) — designed as a single-page experience with rich programme detail, cost snapshot, and delegate resources.

## Structure

- `index.html` &mdash; Main landing page containing hero, thematic tracks, draft programme, registration timelines, venue info, partners, and contact form.
- `programme.html` &mdash; Generated detailed schedule with per-session metadata, speaker abstracts, parallel track overview, and quick navigation.
- `participants.html` &mdash; Generated roster of registered delegates sourced from a CSV export.
- `assets/css/styles.css` &mdash; Core visual system used across pages, including programme and participant layouts.
- `data/programme.json` &mdash; Source of truth for the schedule content.
- `data/participants.csv` &mdash; Example CSV exported from the registration sheet.
- `templates/programme_template.html` &mdash; HTML skeleton populated by the render script.
- `templates/participants_template.html` &mdash; HTML skeleton for the roster page.
- `scripts/render_programme.py` &mdash; Utility that renders `programme.html` from the JSON data.
- `scripts/render_participants.py` &mdash; Utility that renders `participants.html` from the CSV export.

## Usage

Open `index.html` or `programme.html` in any modern browser to view the site. When hosting, copy the entire `ggos-africa-website` directory to your web server or static hosting service (GitHub Pages, Netlify, etc.).

### Regenerate the detailed programme

```bash
cd ggos-africa-website
python3 scripts/render_programme.py
```

Optional arguments allow you to supply alternative data, template, or output paths:

```bash
python3 scripts/render_programme.py --data data/custom.json --output build/programme.html
```

Publish a placeholder page before sessions are finalised by adding `--coming-soon` (customise the message if you like):

```bash
python3 scripts/render_programme.py --coming-soon --coming-soon-message "Programme launches in January 2026."
```

### Regenerate the participant roster

1. In Google Sheets choose **File → Download → Comma-separated values (.csv)** to export your current registrations.
2. Save/replace the file at `data/participants.csv`.
3. Render the page:

```bash
python3 scripts/render_participants.py
```

Optional arguments let you point to alternate CSV, template, or output paths:

```bash
python3 scripts/render_participants.py --csv data/latest.csv --output build/participants.html
```

Use `--coming-soon` to show a temporary notice before the roster is available:

```bash
python3 scripts/render_participants.py --coming-soon --coming-soon-message "Delegate list available after confirmations."
```

## Customisation Tips

- Update event dates, venue, and links (e.g., registration form) directly in the relevant sections of `index.html`.
- Replace the hero background image URL in `styles.css` with local imagery if preferred.
- Add speaker biographies by duplicating the markup inside the `card-grid--people` container.
- Extend the summary on `index.html` or update the detailed agenda by editing `data/programme.json` and re-running the render script. You can add optional `"materials"` arrays to sessions or parallel tracks to surface links to slide decks, papers, or toolkits. Speaker entries support objects with `name`, `role`, `affiliation`, and `abstract` fields for richer content.
- Tailor `data/participants.csv` columns to match your registration workflow—just keep the header names consistent with the render script or adjust the script accordingly.

No build tools are required; the site relies on vanilla HTML, CSS, and a small snippet of JavaScript for mobile navigation.

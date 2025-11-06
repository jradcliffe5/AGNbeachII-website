#!/usr/bin/env python3
"""
Render the registered participants page from a CSV export.

Usage:
    python scripts/render_participants.py
    python scripts/render_participants.py --csv data/alt.csv --output participants.html
"""

import argparse
import csv
from datetime import datetime
from html import escape
from pathlib import Path
from string import Template
from typing import Dict, Iterable, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CSV = BASE_DIR / "data" / "participants.csv"
DEFAULT_TEMPLATE = BASE_DIR / "templates" / "participants_template.html"
DEFAULT_OUTPUT = BASE_DIR / "participants.html"


def read_rows(path: Path) -> Iterable[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield {key: value.strip() for key, value in row.items()}


def render_rows(rows: Iterable[Dict[str, str]]) -> str:
    html_rows = []
    for row in rows:
        html_rows.append(
            "<tr>"
            f"<td>{escape(row.get('registration_id', ''))}</td>"
            f"<td>{escape(row.get('display_name', ''))}</td>"
            f"<td>{escape(row.get('organisation', ''))}</td>"
            f"<td>{escape(row.get('country', ''))}</td>"
            f"<td>{escape(row.get('participation_type', ''))}</td>"
            "</tr>"
        )
    return "\n".join(html_rows) if html_rows else '<tr><td colspan="5">No registrations found.</td></tr>'


def render_coming_soon_row(message: str) -> str:
    return (
        '<tr class="participants-table__coming-soon">'
        f'<td colspan="5">{escape(message)}</td>'
        "</tr>"
    )


def render_paragraphs(paragraphs: Optional[Iterable[str]]) -> str:
    blocks = []
    if paragraphs is None:
        return ""
    for text in paragraphs:
        value = (text or "").strip()
        if not value:
            continue
        blocks.append(f"<p>{escape(value)}</p>")
    return "\n".join(blocks)


def render_optional_paragraph(text: Optional[str], css_class: str) -> str:
    if not text:
        return ""
    return f'<p class="{css_class}">{escape(text)}</p>'


def build_page(
    csv_path: Path,
    template_path: Path,
    *,
    coming_soon: bool = False,
    coming_soon_message: Optional[str] = None,
    coming_soon_note: Optional[str] = None,
) -> str:
    event_title = "AGN on the Beach II"
    event_dates = "21–25 September 2026"
    event_location = "Diani, Kenya"
    hero_eyebrow = f"{event_dates} · {event_location}"

    roster_subheading = "List generated from the latest export of the registration system."

    if coming_soon:
        rows_html = render_coming_soon_row(
            coming_soon_message
            or "Participant information will appear after the call for abstracts closes."
        )
        page_lead = coming_soon_note or "Registration opens soon. Subscribe for updates from the SOC."
        intro_paragraphs_html = render_paragraphs(
            [
                "We look forward to welcoming observers, theorists, and students working across the AGN jet community.",
                "Confirmed participants will be listed once registrations are processed by the Scientific Organising Committee.",
            ]
        )
        intro_note_html = render_paragraphs(
            [
                "Need assistance? Contact the SOC once mailing list details are released with the January 2026 circular."
            ]
        )
        table_footnote = "Participant roster will go live immediately after the registration window closes."
        hero_note_html = ""
        roster_subheading = "The list below will populate automatically from the registration system between April and June 2026."
    else:
        rows_html = render_rows(read_rows(csv_path))
        page_lead = (
            "Live roster of confirmed delegates, contributors, and supporters for AGN on the Beach II."
        )
        intro_paragraphs_html = render_paragraphs(
            [
                "This attendee roster lets confirmed delegates review their status ahead of the workshop. It reflects the latest submissions validated by the Scientific Organising Committee.",
            ]
        )
        intro_note_html = render_paragraphs(
            [
                "Need an update? Email the SOC once the mailing list opens to request corrections."
            ]
        )
        table_footnote = "Only confirmed registrants appear here. Contact the SOC if you require corrections."
        hero_note_html = ""

    template = Template(template_path.read_text(encoding="utf-8"))
    timestamp = datetime.utcnow().strftime("%d %B %Y · %H:%M UTC")
    substitutions = {
        "page_title": f"{event_title} · Registered Participants",
        "event_title": event_title,
        "hero_eyebrow": hero_eyebrow,
        "page_heading": "Registered Participants",
        "page_lead": page_lead,
        "hero_note_html": hero_note_html,
        "roster_heading": "Participation Overview",
        "roster_subheading": roster_subheading,
        "intro_paragraphs_html": intro_paragraphs_html,
        "intro_note_html": intro_note_html,
        "participant_rows": rows_html,
        "table_footnote": table_footnote,
        "generated_timestamp": timestamp,
        "coming_soon_notice": "coming-soon" if coming_soon else "",
    }
    return template.safe_substitute(substitutions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the participants page from a CSV export.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to the participants CSV.")
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help="Path to the HTML template file.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output HTML path.")
    parser.add_argument(
        "--coming-soon",
        action="store_true",
        help="Generate a coming-soon placeholder instead of the roster.",
    )
    parser.add_argument(
        "--coming-soon-message",
        type=str,
        default=None,
        help="Custom message for the coming-soon placeholder row.",
    )
    parser.add_argument(
        "--coming-soon-note",
        type=str,
        default=None,
        help="Optional secondary line shown beneath the hero when using --coming-soon.",
    )

    args = parser.parse_args()

    html = build_page(
        args.csv,
        args.template,
        coming_soon=args.coming_soon,
        coming_soon_message=args.coming_soon_message,
        coming_soon_note=args.coming_soon_note,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")

    try:
        rel_path = args.output.relative_to(BASE_DIR)
    except ValueError:
        rel_path = args.output
    print(f"Participants page rendered to {rel_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Render the detailed programme page from structured data.

Usage:
    python scripts/render_programme.py
    python scripts/render_programme.py --data custom.json --output out.html
"""

import argparse
import json
from datetime import datetime
from html import escape
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional, Union


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA = BASE_DIR / "data" / "programme.json"
DEFAULT_TEMPLATE = BASE_DIR / "templates" / "programme_template.html"
DEFAULT_OUTPUT = BASE_DIR / "programme.html"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_legend(legend: List[Dict[str, Any]]) -> str:
    items = []
    for entry in legend:
        color = entry.get("color", "#0f4c3a")
        label = escape(entry.get("type", "Session"))
        items.append(
            f'<li class="legend-item"><span class="legend-dot" '
            f'style="background: {color};"></span>{label}</li>'
        )
    return "\n".join(items)


def format_time(start: str, end: str) -> str:
    if start and end:
        if start == end:
            return escape(start)
        return f"{escape(start)} – {escape(end)}"
    return escape(start or end or "")


SpeakerEntry = Union[str, Dict[str, Any]]


def format_chair_entry(entry: SpeakerEntry) -> str:
    if isinstance(entry, str):
        name = escape(entry)
        return name

    data = entry or {}
    name = escape(data.get("name", "") or "")
    if not name:
        return ""

    affiliation = data.get("affiliation") or data.get("organisation") or ""
    affiliation = escape(affiliation)

    if affiliation:
        return f"{name} ({affiliation})"
    return name


def render_chairs(people: List[SpeakerEntry], element_class: str) -> str:
    if not people:
        return ""

    labels = [format_chair_entry(person) for person in people]
    labels = [label for label in labels if label]
    if not labels:
        return ""

    prefix = "Chair" if len(labels) == 1 else "Chairs"
    chairs_text = ", ".join(labels)
    return f'<p class="{element_class}"><strong>{prefix}:</strong> {chairs_text}</p>'


def normalise_remote_entries(remote: Union[None, Dict[str, Any], List[Any], str]) -> List[Dict[str, Any]]:
    if not remote:
        return []
    if isinstance(remote, dict):
        return [remote]
    if isinstance(remote, str):
        return [{"url": remote}]

    normalised = []
    for entry in remote:
        if isinstance(entry, dict):
            normalised.append(entry)
        elif isinstance(entry, str):
            normalised.append({"url": entry})
        else:
            normalised.append({})
    return normalised


def render_remote_access(
    remote: Union[None, Dict[str, Any], List[Any], str],
    wrapper_class: str,
    item_class: str,
    label: str = "Online connection details",
) -> str:
    entries = normalise_remote_entries(remote)
    if not entries:
        return ""

    connection_blocks = []
    for raw_entry in entries:
        data = raw_entry or {}

        url = escape(data.get("url", "") or "")
        link_label = escape(data.get("label", "") or "Join session")
        meeting_id = escape(data.get("meeting_id", "") or "")
        passcode = escape(data.get("passcode", "") or "")
        dial_in = escape(data.get("dial_in", "") or "")
        note_text = data.get("note") or data.get("instructions") or ""
        note = escape(note_text)

        if not (url or link_label or meeting_id or passcode or note or dial_in):
            continue

        segments: List[str] = []
        if url:
            segments.append(
                f'<a class="{item_class}__link" href="{url}" target="_blank" rel="noopener">{link_label}</a>'
            )
        elif link_label:
            segments.append(link_label)

        if meeting_id:
            segments.append(f"Meeting ID: {meeting_id}")
        if passcode:
            segments.append(f"Passcode: {passcode}")
        if dial_in:
            segments.append(f"Dial-in: {dial_in}")
        if note:
            segments.append(f"Note: {note}")

        connection_blocks.append(" | ".join(segments))

    if not connection_blocks:
        return ""

    label_text = escape(label.rstrip(":")) if label else ""
    connections_html = "<br>".join(connection_blocks)
    if label_text:
        return f'<p class="{wrapper_class}"><strong>{label_text}:</strong> {connections_html}</p>'
    return f'<p class="{wrapper_class}">{connections_html}</p>'


def render_speakers(speakers: List[SpeakerEntry], list_class: str = "session__speakers") -> str:
    if not speakers:
        speakers = [
            {
                "name": "To be announced",
                "role": "Session chair",
                "affiliation": "Details to follow",
            },
            {
                "name": "To be announced",
                "role": "Invited speaker",
                "affiliation": "Details to follow",
            },
            {
                "name": "To be announced",
                "role": "Contributed talk",
                "affiliation": "Details to follow",
            },
        ]

    items = []
    for raw in speakers:
        if isinstance(raw, str):
            data = {"name": raw}
        else:
            data = raw or {}

        name = escape(data.get("name", "Speaker"))
        role = escape(data.get("role", ""))
        affiliation = escape(data.get("affiliation", ""))
        abstract = escape(data.get("abstract", ""))

        meta_parts = [f'<span class="speaker__name">{name}</span>']
        if role:
            meta_parts.append(f'<span class="speaker__role">{role}</span>')
        if affiliation:
            meta_parts.append(f'<span class="speaker__affiliation">{affiliation}</span>')

        header = '<div class="speaker__meta">' + " · ".join(meta_parts) + "</div>"

        details_sections = []
        if abstract:
            details_sections.append(f'<p class="speaker__abstract">{abstract}</p>')

        speaker_materials = render_materials(
            data.get("materials", []),
            wrapper_class="speaker__materials",
            label="Resources:",
        )
        if speaker_materials:
            details_sections.append(speaker_materials)

        details_html = ""
        if details_sections:
            if abstract and speaker_materials:
                summary_label = "View abstract & resources"
            elif abstract:
                summary_label = "View abstract"
            else:
                summary_label = "View resources"
            details_html = (
                '<details class="speaker__details">'
                f'<summary>{escape(summary_label)}</summary>'
                + "".join(details_sections)
                + "</details>"
            )

        filler = ""
        if not abstract and not speaker_materials:
            filler = '<p class="speaker__placeholder">Abstract and resources will be shared when available.</p>'
        items.append(f'<li class="speaker">{header}{details_html}{filler}</li>')

    return f'<ul class="{list_class}">' + "".join(items) + "</ul>"


def render_parallel(session: Dict[str, Any]) -> str:
    blocks = []
    for item in session.get("parallel", []):
        heading = escape(item.get("track", "Parallel session"))
        location = escape(item.get("location", ""))
        description = escape(item.get("description", ""))
        speakers_html = render_speakers(item.get("speakers", []), "parallel-session__speakers")
        materials_html = render_materials(item.get("materials", []), "parallel-session__materials")
        chairs_html = render_chairs(item.get("chairs", []), "parallel-session__chairs")
        remote_html = render_remote_access(
            item.get("remote"),
            "parallel-session__remote",
            "parallel-remote-connection",
            item.get("remote_label", "Online connection details"),
        )

        location_html = f'<p class="parallel-session__location">{location}</p>' if location else ""
        description_html = (
            f'<p class="parallel-session__description">{description}</p>' if description else ""
        )

        block = (
            '<article class="parallel-session">'
            f"<h5>{heading}</h5>"
            f"{location_html}"
            f"{description_html}"
            f"{chairs_html}"
            f"{remote_html}"
            f"{speakers_html}"
            f"{materials_html}"
            "</article>"
        )
        blocks.append(block)
    return '<div class="parallel-group">' + "".join(blocks) + "</div>"


def render_materials(
    materials: List[Dict[str, Any]],
    wrapper_class: str = "session__materials",
    label: str = "Materials:",
) -> str:
    if not materials:
        return ""

    links = []
    for item in materials:
        link_label = escape(item.get("label", "View material"))
        url = escape(item.get("url", ""))
        if not url:
            continue
        links.append(
            f'<a class="material-link" href="{url}" target="_blank" rel="noopener">{link_label}</a>'
        )

    if not links:
        return ""

    link_group = '<div class="material-links">' + "".join(links) + "</div>"
    label_html = f"<span>{escape(label)}</span>" if label else ""
    return f'<div class="{wrapper_class}">{label_html}{link_group}</div>'


def render_paragraphs(paragraphs: Optional[List[str]]) -> str:
    blocks: List[str] = []
    for text in paragraphs or []:
        value = (text or "").strip()
        if not value:
            continue
        blocks.append(f"<p>{escape(value)}</p>")
    return "\n".join(blocks)


def render_optional_paragraph(text: Optional[str], css_class: str) -> str:
    if not text:
        return ""
    return f'<p class="{css_class}">{escape(text)}</p>'


def render_people_cards(people: Optional[List[Dict[str, Any]]], grid_modifier: str = "card-grid--people") -> str:
    if not people:
        return ""

    cards = []
    for raw_person in people:
        person = raw_person or {}
        name = escape(person.get("name") or "To be announced")

        detail_parts: List[str] = []
        role = person.get("role")
        if role:
            detail_parts.append(str(role))
        affiliation = person.get("affiliation") or person.get("organisation")
        if affiliation:
            detail_parts.append(str(affiliation))
        detail = person.get("detail")
        if detail:
            detail_parts.append(str(detail))

        detail_text = " · ".join(detail_parts).strip()
        if detail_text:
            detail_html = f"<p>{escape(detail_text)}</p>"
        else:
            detail_html = "<p>Details coming soon.</p>"

        cards.append(f'<article class="card person"><h3>{name}</h3>{detail_html}</article>')

    grid_class = f"card-grid {grid_modifier}".strip()
    return f'<div class="{grid_class}">' + "".join(cards) + "</div>"


def render_people_section(
    block: Optional[Dict[str, Any]],
    section_id: str,
    default_title: str,
    grid_modifier: str = "card-grid--people",
) -> str:
    if not block:
        return ""

    title = escape(block.get("title") or default_title)
    lead_html = render_optional_paragraph(block.get("lead"), "section__subhead")
    paragraphs_html = render_paragraphs(block.get("paragraphs"))

    people_cards_html = render_people_cards(block.get("people"), grid_modifier)
    if not people_cards_html:
        people_cards_html = render_people_cards(
            [{"name": "To be announced", "detail": "Details to follow."}], grid_modifier
        )

    note_html = render_optional_paragraph(block.get("footnote"), "footnote")

    body_segments = [lead_html, paragraphs_html, people_cards_html, note_html]
    body_html = "\n".join(segment for segment in body_segments if segment)

    return (
        f'<section class="section section--people" id="{escape(section_id)}">'
        '<div class="section__inner">'
        f"<h2>{title}</h2>"
        f"{body_html}"
        "</div>"
        "</section>"
    )


def render_coming_soon_card(message: str, details: Optional[str] = None) -> str:
    primary = escape(message or "The detailed programme will be published soon.")
    details_html = (
        f'<p class="coming-soon-card__details">{escape(details)}</p>'
        if details
        else ""
    )
    return (
        '<div class="coming-soon-card">'
        '<h3>Coming soon</h3>'
        f'<p>{primary}</p>'
        f'{details_html}'
        '</div>'
    )


def render_session(session: Dict[str, Any]) -> str:
    session_type = escape(session.get("type", "Session"))
    type_class = session_type.replace(" ", "")
    session_classes = f"session session--type-{type_class}"

    if session.get("parallel"):
        session_classes += " session--parallel"

    time_html = format_time(session.get("start"), session.get("end"))
    title_html = escape(session.get("title", "Untitled session"))
    description_html = escape(session.get("description", ""))
    location = escape(session.get("location", ""))
    track = escape(session.get("track", ""))

    meta_parts = []
    if location:
        meta_parts.append(f'<span><strong>Location:</strong> {location}</span>')
    if track:
        meta_parts.append(f'<span><strong>Theme:</strong> {track}</span>')
    meta_html = f'<div class="session__meta">{"".join(meta_parts)}</div>' if meta_parts else ""

    description_block = (
        f'<p class="session__description">{description_html}</p>'
        if description_html
        else '<p class="session__description">Session abstract to be provided.</p>'
    )
    speakers_html = render_speakers(session.get("speakers", []))
    materials_html = render_materials(session.get("materials", []))
    if not materials_html:
        materials_html = '<div class="session__materials"><span>Materials:</span><div class="material-links"><span>To be shared closer to the event.</span></div></div>'
    chairs_html = render_chairs(session.get("chairs", []), "session__chairs")
    remote_html = render_remote_access(
        session.get("remote"),
        "session__remote",
        "remote-connection",
        session.get("remote_label", "Online connection details"),
    )
    parallel_html = render_parallel(session)

    return (
        f'<li class="{session_classes}">' 
        f'<div class="session__time">{time_html}</div>'
        '<div class="session__content">'
        f'<h4 class="session__title">{title_html}</h4>'
        f"{meta_html}"
        f"{chairs_html}"
        f"{description_block}"
        f"{remote_html}"
        f"{speakers_html}"
        f"{materials_html}"
        f"{parallel_html}"
        "</div>"
        "</li>"
    )


def render_day(day: Dict[str, Any]) -> str:
    day_id = escape(day.get("id", "day"))
    label = escape(day.get("label", "Day"))
    date = escape(day.get("date", ""))
    theme = escape(day.get("theme", ""))

    sessions_html = "\n".join(render_session(session) for session in day.get("sessions", []))

    theme_html = f'<p class="day-schedule__theme">{theme}</p>' if theme else ""

    return (
        f'<article class="day-schedule" id="{day_id}">'
        '<header class="day-schedule__header">'
        '<div>'
        f'<p class="day-schedule__label">{label}</p>'
        f"<h3>{date}</h3>"
        f"{theme_html}"
        "</div>"
        '<a class="day-schedule__back" href="#top">Back to top ↑</a>'
        "</header>"
        f'<ol class="session-list">{sessions_html}</ol>'
        "</article>"
    )


def render_day_nav(days: List[Dict[str, Any]]) -> str:
    chips = []
    for day in days:
        day_id = escape(day.get("id", "day"))
        label = escape(day.get("label", "Day"))
        theme = escape(day.get("theme", ""))
        chip = (
            f'<a class="day-chip" href="#{day_id}">'
            f"<span>{label}</span>"
            f"<small>{theme}</small>"
            "</a>"
        )
        chips.append(chip)
    return "\n".join(chips)


def render_schedule(days: List[Dict[str, Any]]) -> str:
    return "\n".join(render_day(day) for day in days)


def build_page(
    data: Dict[str, Any],
    template_path: Path,
    *,
    coming_soon: bool = False,
    coming_soon_message: Optional[str] = None,
    coming_soon_details: Optional[str] = None,
) -> str:
    template = Template(template_path.read_text(encoding="utf-8"))

    legend_html = render_legend(data.get("legend", []))
    days = data.get("days", [])
    day_nav_html = render_day_nav(days)
    schedule_html = render_schedule(days)

    event = data.get("event", {})
    copy = data.get("copy", {})

    hero_copy = copy.get("hero", {})
    intro_copy = copy.get("intro", {})
    quicknav_copy = copy.get("quicknav", {})
    schedule_copy = copy.get("schedule", {})
    resources_copy = copy.get("resources", {})

    event_dates = event.get("dates", "")
    event_location = event.get("location", "")
    if event_dates and event_location:
        default_eyebrow = f"{event_dates} · {event_location}"
    else:
        default_eyebrow = event_dates or event_location or ""

    hero_eyebrow = hero_copy.get("eyebrow") or default_eyebrow
    hero_heading = hero_copy.get("heading") or "Detailed programme"
    hero_lead = hero_copy.get("lead") or event.get("subtitle", "") or "Schedule updates for the workshop."
    hero_description_html = render_optional_paragraph(hero_copy.get("description"), "hero__description")

    intro_title = intro_copy.get("title") or "Programme overview"
    intro_paragraphs_html = (
        render_paragraphs(intro_copy.get("paragraphs"))
        or render_paragraphs(
            [
                "Explore the sessions planned for the workshop, including plenaries, working discussions, and collaborative sprints.",
                "Use the quick navigation chips to jump between days as you plan your participation.",
            ]
        )
    )
    legend_heading = intro_copy.get("sidebar_title") or "Session legend"
    legend_note_html = render_optional_paragraph(intro_copy.get("sidebar_note"), "legend-card__note")

    quicknav_heading = quicknav_copy.get("title") or "Jump to a day"
    quicknav_note_html = render_optional_paragraph(quicknav_copy.get("note"), "quicknav-note")

    schedule_heading = schedule_copy.get("title") or "Draft daily structure"
    schedule_note_html = render_optional_paragraph(schedule_copy.get("note"), "footnote")

    resources_section_html = ""

    if coming_soon:
        legend_html = ""
        day_nav_html = '<span class="day-chip day-chip--placeholder">Schedule coming soon</span>'
        schedule_html = render_coming_soon_card(
            coming_soon_message
            or "The detailed programme will be published soon. Check back for the full agenda.",
            coming_soon_details,
        )

    substitutions = {
        "page_title": f"{data['event']['title']} · Programme",
        "event_title": data["event"]["title"],
        "event_subtitle": data["event"].get("subtitle", ""),
        "event_dates": data["event"].get("dates", ""),
        "event_location": data["event"].get("location", ""),
        "event_timezone": data["event"].get("timezone", ""),
        "hero_eyebrow": hero_eyebrow,
        "hero_heading": hero_heading,
        "hero_lead": hero_lead,
        "hero_description_html": hero_description_html,
        "intro_title": intro_title,
        "intro_paragraphs_html": intro_paragraphs_html,
        "legend_heading": legend_heading,
        "legend_note_html": legend_note_html,
        "legend_items": legend_html,
        "quicknav_heading": quicknav_heading,
        "quicknav_note_html": quicknav_note_html,
        "day_nav": day_nav_html,
        "schedule_heading": schedule_heading,
        "schedule_sections": schedule_html,
        "schedule_note_html": schedule_note_html,
        "generated_timestamp": datetime.utcnow().strftime("%d %B %Y · %H:%M UTC"),
        "coming_soon_notice": "coming-soon" if coming_soon else "",
    }

    return template.safe_substitute(substitutions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the programme page from structured data.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="Path to programme JSON.")
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
        help="Generate a coming-soon placeholder instead of the detailed programme.",
    )
    parser.add_argument(
        "--coming-soon-message",
        type=str,
        default=None,
        help="Custom message to display when using --coming-soon.",
    )
    parser.add_argument(
        "--coming-soon-details",
        type=str,
        default=None,
        help="Optional secondary line for the coming-soon placeholder.",
    )

    args = parser.parse_args()

    data = load_json(args.data)
    html = build_page(
        data,
        args.template,
        coming_soon=args.coming_soon,
        coming_soon_message=args.coming_soon_message,
        coming_soon_details=args.coming_soon_details,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    try:
        rel_path = args.output.relative_to(BASE_DIR)
    except ValueError:
        rel_path = args.output
    print(f"Programme page rendered to {rel_path}")


if __name__ == "__main__":
    main()

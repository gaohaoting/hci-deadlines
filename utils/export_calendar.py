#!/usr/bin/env python3
"""Export a filtered .ics calendar from conferences + local_filter config."""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_data"
TBA = {"tba", "tbd"}


def normalize_subs(sub):
    if isinstance(sub, list):
        return [str(s) for s in sub]
    if isinstance(sub, str):
        return [sub]
    return []


def included(conf: dict, filt: dict) -> bool:
    if filt.get("min_year"):
        year = int(conf.get("year", 0) or 0)
        if year and year < int(filt["min_year"]):
            return False

    conf_id = conf.get("id", "")
    if conf_id in (filt.get("exclude_ids") or []):
        return False

    include_ids = filt.get("include_ids") or []
    if include_ids and conf_id not in include_ids:
        return False

    subs_filter = [s.upper() for s in (filt.get("subs") or [])]
    if subs_filter:
        conf_subs = [s.upper() for s in normalize_subs(conf.get("sub"))]
        if not set(conf_subs) & set(subs_filter):
            return False

    return True


def parse_deadline(value: str, timezone: str) -> str:
    if not value or value.lower() in TBA:
        return ""
    value = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            break
        except ValueError:
            dt = None
    if dt is None:
        return ""
    tz = timezone or "UTC"
    if tz.startswith("UTC"):
        offset = tz[3:] or "+0"
        if offset.startswith("+"):
            tzid = f"Etc/GMT-{offset[1:]}"
        elif offset.startswith("-"):
            tzid = f"Etc/GMT+{offset[1:]}"
        else:
            tzid = "Etc/GMT"
    else:
        tzid = tz
    return f"DTSTART;TZID={tzid}:{dt.strftime('%Y%m%dT%H%M%S')}"


def ics_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def build_event(uid: str, summary: str, deadline: str, timezone: str) -> str:
    if not deadline:
        return ""
    dt_line = parse_deadline(deadline, timezone)
    if not dt_line:
        return ""
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return "\n".join(
        [
            "BEGIN:VEVENT",
            f"SUMMARY:{ics_escape(summary)}",
            f"UID:{ics_escape(uid)}",
            "ORGANIZER:hci-deadlines-local",
            f"DTSTAMP:{now}",
            dt_line,
            "END:VEVENT",
        ]
    )


def main() -> int:
    conf_path = DATA / "conferences.yml"
    filter_path = DATA / "local_filter.yml"
    out_path = ROOT / "my-calendar.ics"

    if not filter_path.exists():
        print("缺少 _data/local_filter.yml，请先复制 local_filter.yml.example", file=sys.stderr)
        return 1

    with conf_path.open(encoding="utf-8") as f:
        conferences = yaml.safe_load(f) or []
    with filter_path.open(encoding="utf-8") as f:
        filt = yaml.safe_load(f) or {}

    selected = [c for c in conferences if included(c, filt)]
    events = []
    for conf in selected:
        title = f"{conf.get('title', '')} {conf.get('year', '')}".strip()
        tz = conf.get("timezone", "UTC-12")
        abstract = conf.get("abstract_deadline", "")
        if abstract and str(abstract).lower() not in TBA:
            events.append(
                build_event(
                    f"{conf['id']}-abstract",
                    f"{title} abstract deadline",
                    abstract,
                    tz,
                )
            )
        deadline = conf.get("deadline", "")
        if deadline and str(deadline).lower() not in TBA:
            events.append(
                build_event(
                    conf["id"],
                    f"{title} deadline",
                    deadline,
                    tz,
                )
            )

    body = "\n".join(e for e in events if e)
    ics = "\n".join(
        [
            "BEGIN:VCALENDAR",
            "METHOD:PUBLISH",
            "VERSION:2.0",
            "PRODID:-//hci-deadlines-local//EN",
            "X-PUBLISHED-TTL:PT1H",
            body,
            "END:VCALENDAR",
        ]
    )
    out_path.write_text(ics + "\n", encoding="utf-8")
    print(f"Exported {len(selected)} conferences ({len(events)} events) -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

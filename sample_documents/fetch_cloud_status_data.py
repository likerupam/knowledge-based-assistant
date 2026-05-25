#!/usr/bin/env python3
"""Fetch real cloud/SaaS status data and turn it into KB-ready documents."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROVIDERS = {
    "cloudflare": {
        "name": "Cloudflare",
        "incidents_url": "https://www.cloudflarestatus.com/api/v2/incidents.json",
        "components_url": "https://www.cloudflarestatus.com/api/v2/components.json",
    },
    "github": {
        "name": "GitHub",
        "incidents_url": "https://www.githubstatus.com/api/v2/incidents.json",
        "components_url": "https://www.githubstatus.com/api/v2/components.json",
    },
}

OUTPUT_DIR = Path(__file__).resolve().parent / "generated"


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "knowledge-base-assistant/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while fetching {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error while fetching {url}: {exc.reason}") from exc


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_dt(value: str | None) -> str:
    parsed = parse_dt(value)
    if not parsed:
        return "Unknown"
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def duration_minutes(start: str | None, end: str | None) -> int | None:
    started = parse_dt(start)
    finished = parse_dt(end)
    if not started or not finished:
        return None
    minutes = int((finished - started).total_seconds() // 60)
    return max(minutes, 0)


def incident_components(incident: dict[str, Any]) -> list[str]:
    names = []
    for component in incident.get("components", []):
        name = component.get("name")
        if name:
            names.append(name)
    return sorted(set(names))


def collect_provider(slug: str, limit: int) -> dict[str, Any]:
    provider = PROVIDERS[slug]
    incidents = fetch_json(provider["incidents_url"]).get("incidents", [])[:limit]
    components = fetch_json(provider["components_url"]).get("components", [])
    return {
        "slug": slug,
        "name": provider["name"],
        "incidents": incidents,
        "components": components,
    }


def build_raw_document(provider_data: list[dict[str, Any]], fetched_at: datetime) -> str:
    lines = [
        "REAL CLOUD STATUS INCIDENT DATA",
        "================================",
        "",
        f"Fetched At: {fetched_at.strftime('%Y-%m-%d %H:%M UTC')}",
        "Source APIs: Public Statuspage incident and component APIs",
        "Purpose: Real operational data for TechCorp-style cloud platform analysis.",
        "",
    ]

    for provider in provider_data:
        lines.extend(
            [
                f"{provider['name'].upper()} INCIDENTS",
                "-" * (len(provider["name"]) + 10),
                "",
            ]
        )
        if not provider["incidents"]:
            lines.extend(["No incidents returned by the API.", ""])
            continue

        for index, incident in enumerate(provider["incidents"], start=1):
            components = incident_components(incident)
            updates = incident.get("incident_updates", [])
            minutes = duration_minutes(incident.get("created_at"), incident.get("resolved_at"))
            duration = f"{minutes} minutes" if minutes is not None else "Ongoing or unknown"

            lines.extend(
                [
                    f"{index}. {incident.get('name', 'Untitled incident')}",
                    f"Status: {incident.get('status', 'unknown')}",
                    f"Impact: {incident.get('impact', 'unknown')}",
                    f"Created: {fmt_dt(incident.get('created_at'))}",
                    f"Resolved: {fmt_dt(incident.get('resolved_at'))}",
                    f"Duration: {duration}",
                    f"Affected Components: {', '.join(components) if components else 'Not listed'}",
                    f"Short Link: {incident.get('shortlink', 'Not provided')}",
                ]
            )

            if updates:
                latest = updates[0]
                body = " ".join(str(latest.get("body", "")).split())
                if len(body) > 500:
                    body = body[:497] + "..."
                lines.append(f"Latest Update: {body or 'No update text provided'}")

            lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_insights_document(provider_data: list[dict[str, Any]], fetched_at: datetime) -> str:
    all_incidents: list[tuple[str, dict[str, Any]]] = []
    for provider in provider_data:
        for incident in provider["incidents"]:
            all_incidents.append((provider["name"], incident))

    impact_counts = Counter(incident.get("impact", "unknown") for _, incident in all_incidents)
    status_counts = Counter(incident.get("status", "unknown") for _, incident in all_incidents)
    component_counts: Counter[str] = Counter()
    durations: list[tuple[int, str, str]] = []

    for provider_name, incident in all_incidents:
        for component in incident_components(incident):
            component_counts[component] += 1
        minutes = duration_minutes(incident.get("created_at"), incident.get("resolved_at"))
        if minutes is not None:
            durations.append((minutes, provider_name, incident.get("name", "Untitled incident")))

    longest = sorted(durations, reverse=True)[:5]
    avg_duration = round(sum(minutes for minutes, _, _ in durations) / len(durations), 1) if durations else None
    active = [f"{provider}: {incident.get('name', 'Untitled incident')}" for provider, incident in all_incidents if incident.get("status") != "resolved"]

    lines = [
        "REAL CLOUD STATUS INSIGHTS BRIEF",
        "================================",
        "",
        f"Generated At: {fetched_at.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Incidents Analyzed: {len(all_incidents)}",
        "Context: These public incidents are useful comparison data for TechCorp Cloud Platform reliability, incident response, customer support, and SLA planning.",
        "",
        "EXECUTIVE INSIGHTS",
        "",
    ]

    if not all_incidents:
        lines.append("No incidents were returned, so no operational trend analysis could be generated.")
        return "\n".join(lines).strip() + "\n"

    lines.extend(
        [
            f"- Incident severity mix: {format_counter(impact_counts)}.",
            f"- Resolution state mix: {format_counter(status_counts)}.",
        ]
    )

    if avg_duration is not None:
        lines.append(f"- Average resolved incident duration: {avg_duration} minutes across {len(durations)} resolved incidents.")

    if component_counts:
        top_components = ", ".join(f"{name} ({count})" for name, count in component_counts.most_common(8))
        lines.append(f"- Most frequently affected components: {top_components}.")

    if active:
        lines.append(f"- Active or non-resolved incidents to watch: {len(active)}.")
    else:
        lines.append("- No active incidents were present in the fetched incident sample.")

    lines.extend(["", "LONGEST RESOLVED INCIDENTS", ""])
    if longest:
        for minutes, provider, name in longest:
            lines.append(f"- {provider}: {name} lasted {minutes} minutes.")
    else:
        lines.append("- No resolved incident durations were available.")

    lines.extend(
        [
            "",
            "TECHCORP KNOWLEDGE BASE CONNECTIONS",
            "",
            "- Technical documentation: compare public incident component names with TechCorp compute, storage, networking, CDN, and database layers.",
            "- Application logs: use these incidents as real examples for detecting customer-visible degradation, slow queries, timeout clusters, and recovery events.",
            "- Security policy: incident status updates can be reviewed against escalation rules, customer communication timing, and audit-log retention expectations.",
            "- Quarterly report: recurring provider outages are relevant to gross margin, infrastructure cost, retention risk, and SLA credit exposure.",
            "",
            "SUGGESTED QUERIES",
            "",
            "- Which cloud components appear most vulnerable based on recent public incidents?",
            "- How should TechCorp update its incident escalation matrix based on real status data?",
            "- What operational risks could affect TechCorp customer retention or SLA commitments?",
            "- Compare the public incident durations with TechCorp's 99.99% uptime target.",
        ]
    )

    return "\n".join(lines).strip() + "\n"


def format_counter(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counter.most_common())


def write_documents(provider_data: list[dict[str, Any]], output_dir: Path) -> list[Path]:
    fetched_at = datetime.now(timezone.utc)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_path = output_dir / "real_cloud_status_incidents.txt"
    insights_path = output_dir / "real_cloud_status_insights.txt"

    raw_path.write_text(build_raw_document(provider_data, fetched_at), encoding="utf-8")
    insights_path.write_text(build_insights_document(provider_data, fetched_at), encoding="utf-8")

    return [raw_path, insights_path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch real cloud/SaaS status data for the knowledge base.")
    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDERS),
        action="append",
        help="Provider to fetch. Defaults to Cloudflare and GitHub. Can be passed multiple times.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Maximum incidents per provider.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Directory for generated .txt documents.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    slugs = args.provider or list(PROVIDERS)

    try:
        provider_data = [collect_provider(slug, args.limit) for slug in slugs]
    except RuntimeError as exc:
        print(f"Failed to fetch cloud status data: {exc}", file=sys.stderr)
        return 1

    paths = write_documents(provider_data, args.output_dir)
    print("Generated knowledge-base documents:")
    for path in paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

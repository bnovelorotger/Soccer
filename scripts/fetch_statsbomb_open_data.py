import argparse
import json
import os
from pathlib import Path
import requests

RAW_BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    dest.write_bytes(r.content)


def load_competitions(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch StatsBomb open-data files.")
    parser.add_argument("--out", default="data/statsbomb_open_data", help="Output directory")
    parser.add_argument("--competition-id", type=int, default=None, help="Competition ID to download matches/events")
    parser.add_argument("--season-id", type=int, default=None, help="Season ID (required with --competition-id)")
    parser.add_argument("--events", action="store_true", help="Download events for matches")
    parser.add_argument("--lineups", action="store_true", help="Download lineups for matches")
    parser.add_argument("--limit-matches", type=int, default=None, help="Limit number of matches (for quick tests)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    competitions_path = out_dir / "competitions.json"
    if not competitions_path.exists():
        download(f"{RAW_BASE}/competitions.json", competitions_path)

    if args.competition_id is None:
        print(f"Saved competitions to {competitions_path}")
        print("Use --competition-id and --season-id to fetch matches, and --events/--lineups for deeper data.")
        return

    if args.season_id is None:
        raise SystemExit("--season-id is required when --competition-id is provided")

    matches_url = f"{RAW_BASE}/matches/{args.competition_id}/{args.season_id}.json"
    matches_path = out_dir / "matches" / f"{args.competition_id}_{args.season_id}.json"
    download(matches_url, matches_path)
    matches = json.loads(matches_path.read_text(encoding="utf-8"))

    if args.limit_matches is not None:
        matches = matches[: args.limit_matches]

    if args.events:
        for m in matches:
            mid = m.get("match_id")
            if mid is None:
                continue
            events_url = f"{RAW_BASE}/events/{mid}.json"
            events_path = out_dir / "events" / f"{mid}.json"
            if not events_path.exists():
                download(events_url, events_path)

    if args.lineups:
        for m in matches:
            mid = m.get("match_id")
            if mid is None:
                continue
            lineups_url = f"{RAW_BASE}/lineups/{mid}.json"
            lineups_path = out_dir / "lineups" / f"{mid}.json"
            if not lineups_path.exists():
                download(lineups_url, lineups_path)

    print(f"Saved matches to {matches_path}")
    if args.events:
        print("Downloaded events for selected matches")
    if args.lineups:
        print("Downloaded lineups for selected matches")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
import json
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path('data/statsbomb_open_data')
LINEUPS_DIR = BASE / 'lineups'
EVENTS_DIR = BASE / 'events'
MATCHES_PATH = BASE / 'matches' / '11_90.json'
OUT_DOC = Path('docs') / 'barca_lineup.md'
OUT_DOC.parent.mkdir(parents=True, exist_ok=True)
VIS_DIR = Path('visuals')
VIS_DIR.mkdir(exist_ok=True)
OUT_MATCHES_CHART = VIS_DIR / 'barca_matches_played.png'
OUT_MINUTES_CHART = VIS_DIR / 'barca_minutes_played.png'

TEAM_NAMES = {'Barcelona', 'FC Barcelona'}


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def get_match_ids():
    matches = load_json(MATCHES_PATH)
    return [m['match_id'] for m in matches]


def match_end_minute(match_id):
    events_path = EVENTS_DIR / f"{match_id}.json"
    if not events_path.exists():
        return 90.0
    events = load_json(events_path)
    max_min = 90.0
    for ev in events:
        minute = ev.get('minute')
        second = ev.get('second', 0)
        if minute is None:
            continue
        t = float(minute) + (float(second) / 60.0)
        if t > max_min:
            max_min = t
    return max_min

def parse_time(value, fallback=0.0):
    if value is None:
        return fallback
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        if ':' in value:
            parts = value.split(':')
            try:
                mins = float(parts[0])
                secs = float(parts[1]) if len(parts) > 1 else 0.0
                return mins + (secs / 60.0)
            except ValueError:
                return fallback
        try:
            return float(value)
        except ValueError:
            return fallback
    return fallback


def collect_players(match_ids):
    appearances = Counter()
    minutes = defaultdict(float)

    for mid in match_ids:
        lp = LINEUPS_DIR / f"{mid}.json"
        if not lp.exists():
            continue
        data = load_json(lp)
        end_min = match_end_minute(mid)

        for team_entry in data:
            team_name = team_entry.get('team_name')
            if team_name not in TEAM_NAMES:
                continue
            for p in team_entry.get('lineup', []):
                name = p.get('player_name')
                if not name:
                    continue
                appearances[name] += 1
                # Positions provide from/to minutes
                total_minutes = 0.0
                for pos in p.get('positions', []):
                    start = parse_time(pos.get('from', 0), 0.0)
                    end = parse_time(pos.get('to'), None)
                    if end is None:
                        end = end_min
                    total_minutes += max(0.0, float(end) - float(start))
                minutes[name] += total_minutes

    return appearances, minutes


def build_doc(appearances, minutes, total_matches):
    rows = sorted(appearances.items(), key=lambda x: (-x[1], x[0]))
    lines = []
    lines.append('# FC Barcelona Lineup (StatsBomb Open Data)')
    lines.append('')
    lines.append('Season: La Liga 2020/2021 (partial, open-data subset)')
    lines.append(f'Total matches in dataset: {total_matches}')
    lines.append('')
    lines.append('## Players, Matches, and Minutes')
    lines.append('')
    lines.append('| Player | Matches | Minutes |')
    lines.append('| --- | ---: | ---: |')
    for name, count in rows:
        mins = int(round(minutes.get(name, 0)))
        lines.append(f'| {name} | {count} | {mins} |')
    OUT_DOC.write_text('\n'.join(lines), encoding='utf-8')


def build_chart(appearances, minutes):
    # All players, sorted by matches
    rows = sorted(appearances.items(), key=lambda x: x[1], reverse=True)
    names = [r[0] for r in rows]
    counts = [r[1] for r in rows]

    plt.figure(figsize=(10, max(6, len(names) * 0.25)))
    plt.barh(names[::-1], counts[::-1], color='#A50044')
    plt.title('Barcelona – Matches Played (All Players)')
    plt.xlabel('Matches')
    plt.tight_layout()
    plt.savefig(OUT_MATCHES_CHART, dpi=150)
    plt.close()

    # All players, sorted by minutes
    rows_m = sorted(minutes.items(), key=lambda x: x[1], reverse=True)
    names_m = [r[0] for r in rows_m]
    mins = [r[1] for r in rows_m]

    plt.figure(figsize=(10, max(6, len(names_m) * 0.25)))
    plt.barh(names_m[::-1], mins[::-1], color='#004D98')
    plt.title('Barcelona – Minutes Played (All Players)')
    plt.xlabel('Minutes')
    plt.tight_layout()
    plt.savefig(OUT_MINUTES_CHART, dpi=150)
    plt.close()


def main():
    match_ids = get_match_ids()
    appearances, minutes = collect_players(match_ids)
    if not appearances:
        raise SystemExit('No Barcelona lineups found in dataset.')
    build_doc(appearances, minutes, len(match_ids))
    build_chart(appearances, minutes)
    print('Saved', OUT_DOC)
    print('Saved', OUT_MATCHES_CHART)
    print('Saved', OUT_MINUTES_CHART)


if __name__ == '__main__':
    main()

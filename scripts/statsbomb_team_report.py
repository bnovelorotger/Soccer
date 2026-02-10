import json
from pathlib import Path
import pandas as pd
import unicodedata

BASE = Path('data/statsbomb_open_data')
EVENTS_DIR = BASE / 'events'
LINEUPS_DIR = BASE / 'lineups'
MATCHES_PATH = BASE / 'matches' / '11_90.json'

TARGET_TEAMS = [
    'Barcelona', 'Real Madrid', 'Atletico Madrid',
    'Manchester City', 'Bayern Munich', 'Paris S-G'
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def collect_match_ids():
    matches = load_json(MATCHES_PATH)
    return [m['match_id'] for m in matches]

def normalize_name(name: str) -> str:
    if name is None:
        return ''
    return ''.join(c for c in unicodedata.normalize('NFKD', name) if ord(c) < 128)

def is_progressive(start_x, end_x, min_gain=10):
    if start_x is None or end_x is None:
        return False
    return (end_x - start_x) >= min_gain

def is_final_third_entry(end_x):
    return end_x is not None and end_x >= 80

def is_box_entry(end_x, end_y):
    if end_x is None or end_y is None:
        return False
    return end_x >= 102 and 18 <= end_y <= 62


def build_team_stats(match_ids):
    rows = []
    for mid in match_ids:
        events_path = EVENTS_DIR / f"{mid}.json"
        if not events_path.exists():
            continue
        events = load_json(events_path)

        team_stats = {}
        match_total_duration = 0.0
        for ev in events:
            team = ev.get('team', {}).get('name')
            if not team:
                continue
            s = team_stats.setdefault(team, {
                'Team': team,
                'Matches': set(),
                'Shots': 0,
                'Goals': 0,
                'xG': 0.0,
                'Passes': 0,
                'Passes_Completed': 0,
                'Possession_Secs': 0.0,
                'Possession_Share_Sum': 0.0,
                'Possession_Share_Count': 0,
                'Pressures': 0,
                'Tackles': 0,
                'Interceptions': 0,
                'Fouls': 0,
                'Dribbles': 0,
                'Dribbles_Success': 0,
                'Carries': 0,
                'Progressive_Passes': 0,
                'Progressive_Carries': 0,
                'FinalThird_Entries': 0,
                'Box_Entries': 0,
            })
            s['Matches'].add(mid)

            etype = ev.get('type', {}).get('name')
            if etype == 'Shot':
                s['Shots'] += 1
                shot = ev.get('shot', {})
                if shot.get('outcome', {}).get('name') == 'Goal':
                    s['Goals'] += 1
                xg = shot.get('statsbomb_xg')
                if xg is not None:
                    s['xG'] += float(xg)
            elif etype == 'Pass':
                s['Passes'] += 1
                if ev.get('pass', {}).get('outcome') is None:
                    s['Passes_Completed'] += 1
                loc = ev.get('location') or [None, None]
                end_loc = ev.get('pass', {}).get('end_location') or [None, None]
                if is_progressive(loc[0], end_loc[0]):
                    s['Progressive_Passes'] += 1
                if is_final_third_entry(end_loc[0]):
                    s['FinalThird_Entries'] += 1
                if is_box_entry(end_loc[0], end_loc[1]):
                    s['Box_Entries'] += 1
            elif etype == 'Pressure':
                s['Pressures'] += 1
            elif etype == 'Tackle':
                s['Tackles'] += 1
            elif etype == 'Interception':
                s['Interceptions'] += 1
            elif etype == 'Foul Committed':
                s['Fouls'] += 1
            elif etype == 'Dribble':
                s['Dribbles'] += 1
                if ev.get('dribble', {}).get('outcome', {}).get('name') == 'Complete':
                    s['Dribbles_Success'] += 1
            elif etype == 'Carry':
                s['Carries'] += 1
                loc = ev.get('location') or [None, None]
                end_loc = ev.get('carry', {}).get('end_location') or [None, None]
                if is_progressive(loc[0], end_loc[0]):
                    s['Progressive_Carries'] += 1
                if is_final_third_entry(end_loc[0]):
                    s['FinalThird_Entries'] += 1
                if is_box_entry(end_loc[0], end_loc[1]):
                    s['Box_Entries'] += 1

            duration = ev.get('duration')
            if duration is not None:
                d = float(duration)
                s['Possession_Secs'] += d
                match_total_duration += d

        for team, s in team_stats.items():
            s['Matches'] = len(s['Matches'])
            if match_total_duration > 0:
                s['Possession_Share_Sum'] += s['Possession_Secs'] / match_total_duration
                s['Possession_Share_Count'] += 1
            rows.append(s)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    agg = df.groupby('Team', as_index=False).sum(numeric_only=True)

    agg['Shots_per_match'] = agg['Shots'] / agg['Matches']
    agg['Goals_per_match'] = agg['Goals'] / agg['Matches']
    agg['xG_per_match'] = agg['xG'] / agg['Matches']
    agg['Pass_Completion'] = agg['Passes_Completed'] / agg['Passes']
    agg['Pressures_per_match'] = agg['Pressures'] / agg['Matches']
    agg['Tackles_per_match'] = agg['Tackles'] / agg['Matches']
    agg['Interceptions_per_match'] = agg['Interceptions'] / agg['Matches']
    agg['Fouls_per_match'] = agg['Fouls'] / agg['Matches']
    agg['Dribbles_per_match'] = agg['Dribbles'] / agg['Matches']
    agg['Dribble_Success'] = agg['Dribbles_Success'] / agg['Dribbles']
    agg['Carries_per_match'] = agg['Carries'] / agg['Matches']
    agg['Progressive_Passes_per_match'] = agg['Progressive_Passes'] / agg['Matches']
    agg['Progressive_Carries_per_match'] = agg['Progressive_Carries'] / agg['Matches']
    agg['FinalThird_Entries_per_match'] = agg['FinalThird_Entries'] / agg['Matches']
    agg['Box_Entries_per_match'] = agg['Box_Entries'] / agg['Matches']
    agg['xG_per_shot'] = agg['xG'] / agg['Shots']
    agg['Goals_per_shot'] = agg['Goals'] / agg['Shots']
    agg['Possession_Share'] = agg['Possession_Share_Sum'] / agg['Possession_Share_Count']

    agg['Team_Normalized'] = agg['Team'].apply(normalize_name)

    return agg


def main():
    match_ids = collect_match_ids()
    df = build_team_stats(match_ids)
    if df.empty:
        print('No data found in events.')
        return

    out_full = Path('statsbomb_team_stats.csv')
    df.to_csv(out_full, index=False)

    target_norm = set(normalize_name(t) for t in TARGET_TEAMS)
    target_df = df[df['Team_Normalized'].isin(target_norm)]
    if not target_df.empty:
        target_df.to_csv('statsbomb_team_stats_targets.csv', index=False)

    print('Saved statsbomb_team_stats.csv')
    print('Saved statsbomb_team_stats_targets.csv')


if __name__ == '__main__':
    main()

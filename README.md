# Futbol – FlickLens

## Objective
FlickLens is a lightweight football analysis pipeline to profile team styles and generate Pep-inspired tactical summaries using publicly available data. It prioritizes clear, coach-friendly outputs (text reports + visuals) built from StatsBomb Open Data.

## What We Built
- **StatsBomb Open Data ingestion** (competitions, matches, events, lineups).
- **Team-level metrics** (possession share proxy, progression, final-third/box entries, xG per shot, etc.).
- **Pep-style tactical section** in the Barcelona report.
- **Visuals** comparing Barcelona to league averages and rivals.
- **Bundled PDF report** with text + charts.
- **Lineup report** with matches and minutes played per player.

## Data Source
This project uses StatsBomb Open Data (public) from the official repository.

Note: La Liga 2025/2026 is **not available** in open data. The latest La Liga available is 2020/2021 (partial matches).

## Project Structure
- `scout_flick.py` – Main report generator. Uses StatsBomb CSV if present; otherwise tries FBref.
- `scripts/fetch_statsbomb_open_data.py` – Downloads open data from StatsBomb.
- `scripts/statsbomb_team_report.py` – Builds team metrics CSVs from StatsBomb event data.
- `scripts/barca_lineup_report.py` – Builds lineup table with matches and minutes.
- `data/statsbomb_open_data/` – Downloaded competitions/matches/events/lineups.
- `visuals/` – Generated charts.
- `barca_report.txt` – Pep-style text report.
- `barca_report_bundle.pdf` – Text + charts bundle.
- `docs/barca_lineup.md` – Barcelona lineup with matches and minutes.

## Setup
Install dependencies:

```powershell
C:\Users\bnove\AppData\Local\Python\bin\python.exe -m pip install -r requirements.txt
```

## Usage
1. Download the StatsBomb Open Data needed (La Liga 2020/2021):

```powershell
C:\Users\bnove\AppData\Local\Python\bin\python.exe scripts\fetch_statsbomb_open_data.py --competition-id 11 --season-id 90 --events --lineups
```

2. Build team metrics:

```powershell
C:\Users\bnove\AppData\Local\Python\bin\python.exe scripts\statsbomb_team_report.py
```

3. Generate reports and charts:

```powershell
C:\Users\bnove\AppData\Local\Python\bin\python.exe scout_flick.py
```

4. Generate lineup report:

```powershell
C:\Users\bnove\AppData\Local\Python\bin\python.exe scripts\barca_lineup_report.py
```

## Outputs
- `statsbomb_team_stats.csv` – All team metrics.
- `statsbomb_team_stats_targets.csv` – Target teams subset.
- `barca_report.txt` – Barcelona Pep-style report.
- `visuals/*.png` – Charts.
- `barca_report_bundle.pdf` – Combined PDF report.
- `docs/barca_lineup.md` – Lineup table with matches and minutes.
- `visuals/barca_matches_played.png` – Matches played by all players.
- `visuals/barca_minutes_played.png` – Minutes played by all players.

## Notes
- StatsBomb Open Data is partial. Some seasons have limited matches.
- 360 frames are not available for La Liga 2020/2021 in open data.

## Credits
- StatsBomb Open Data repository: https://github.com/statsbomb/open-data

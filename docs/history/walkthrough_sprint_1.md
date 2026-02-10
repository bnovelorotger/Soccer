# FlickLens (Explain the Play) - Walkthrough (Sprint 1)

Summary of the work completed in Sprint 1 for analyzing FC Barcelona under Hansi Flick.

## Changes Made

### 1. Data Scraper & Processor
Created [scout_flick.py](file:///C:/Users/bnove/Documents/Futbol/scout_flick.py) which:
- Scrapes 8 different tables from FBref for the top 5 European leagues.
- Handles HTML-commented tables (a common FBref scraping hurdle).
- Normalizes columns and merges metrics into a unified DataFrame.

### 2. Feature Engineering
Implemented proxies for tactical analysis:
- **Field Tilt**: Touch distribution in the final third.
- **Verticality Index**: Ratio of progressive passing distance.
- **High Line Proxy**: Offsides provoked per 90.

### 3. Reporting Layer
Built a template-based generator that produces:
- A 6-bullet style summary comparing a team (e.g., Barça) to the sample mean.
- 3 actionable insights based on statistical deviations (Strengths, Weaknesses, Drivers).

## Verification Results

### Execution Test
The script was tested to ensure it handles both web access and local fallback.

```bash
python scout_flick.py
```

### Sample Output Structures
- [barca_report.txt](file:///C:/Users/bnove/Documents/Futbol/barca_report.txt): Textual analysis.
- [flick_scout_top_teams.csv](file:///C:/Users/bnove/Documents/Futbol/flick_scout_top_teams.csv): Cleaned dataset for the top 6 teams.

## Manual Execution Guide
1. Ensure `pandas`, `requests`, `beautifulsoup4`, and `lxml` are installed.
2. Run `python scout_flick.py`.
3. If blocked by FBref (429 error), you can provide a local `flick_scout_full.csv` by manual export and the script will automatically process it.

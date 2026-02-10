import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import io
import os

class FBRefScraper:
    def __init__(self, season="2025-2026"):
        self.season = season
        self.base_url = "https://fbref.com/en/comps"
        self.leagues = {
            "La-Liga": 12,
            "Premier-League": 9,
            "Serie-A": 11,
            "Bundesliga": 20,
            "Ligue-1": 13
        }
        self.target_teams = [
            "Barcelona", "Real Madrid", "Atlético Madrid", 
            "Manchester City", "Bayern Munich", "Paris S-G"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_league_stats(self, league_name, league_id):
        url = f"{self.base_url}/{league_id}/{self.season}/{league_name}-Stats"
        print(f"Fetching data from: {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # FBref hides many tables in comments. We need to extract them.
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            commented_soup = BeautifulSoup("".join(comments), 'html.parser')
            
            tables = {}
            
            # List of table IDs we want
            target_table_ids = [
                'stats_squads_standard_for',
                'stats_squads_shooting_for',
                'stats_squads_passing_for',
                'stats_squads_passing_types_for',
                'stats_squads_gca_for',
                'stats_squads_defense_for',
                'stats_squads_possession_for',
                'stats_squads_misc_for'
            ]
            
            for table_id in target_table_ids:
                # Try finding in main soup first, then in commented soup
                table = soup.find('table', {'id': table_id}) or commented_soup.find('table', {'id': table_id})
                if table:
                    df = pd.read_html(io.StringIO(str(table)))[0]
                    # Clean MultiIndex
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = ['_'.join(col).strip() if 'Unnamed' not in col[0] else col[1] for col in df.columns]
                    tables[table_id] = df
            
            return tables
        except Exception as e:
            print(f"Error fetching {league_name}: {e}")
            return None

    def process_data(self, all_tables):
        merged_df = None
        
        for table_id, df in all_tables.items():
            # Standardize 'Squad' column name
            df = df.rename(columns={'Squad': 'Team'})
            
            if merged_df is None:
                merged_df = df
            else:
                # Merge on Team, avoiding duplicate columns
                cols_to_use = list(df.columns.difference(merged_df.columns)) + ['Team']
                merged_df = pd.merge(merged_df, df[cols_to_use], on='Team', how='outer')
        
        # Clean numeric columns
        for col in merged_df.columns:
            if col != 'Team':
                merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
        
        return merged_df

    def engineer_features(self, df):
        # Derived Metrics
        # xG Difference
        if 'Expected_xG' in df.columns and 'Expected_xGA' in df.columns:
            df['xg_diff'] = df['Expected_xG'] - df['Expected_xGA']
        
        # PPDA Proxy: Opponent Passes / (Tackles + Interceptions)
        # Note: FBref has 'Handling' and 'Defense' tables. 
        # Proxy: (Misc_CrdY + Misc_CrdR) is not enough. 
        # Using Tkl+Int from Defense table.
        # We'd need Opponent Passes which is hard from team-only view. 
        # Let's use a "Defensive Intensity" proxy: (Tackles + Interceptions) / Opponent Possession (if possible)
        # For now, let's stick to accessible ones:
        
        # Field Tilt Proxy: Touches in Final 3rd / (Total Touches)
        if 'Possession_Att 3rd' in df.columns and 'Possession_Touches' in df.columns:
            df['field_tilt_proxy'] = df['Possession_Att 3rd'] / df['Possession_Touches']
            
        # Verticality: Progressive Distance / Total Distance
        if 'Passing_PrgDist' in df.columns and 'Passing_TotDist' in df.columns:
            df['verticality_index'] = df['Passing_PrgDist'] / df['Passing_TotDist']
            
        # High Line Proxy: Offsides against / 90 (found in Misc table)
        if 'Misc_Off' in df.columns and '90s' in df.columns:
            df['high_line_proxy'] = df['Misc_Off'] / df['90s']

        return df

class ReportGenerator:
    def __init__(self, full_df):
        self.df = full_df
        self.avg_stats = full_df.mean(numeric_only=True)

    def generate_style_summary(self, team_name):
        team_data = self.df[self.df['Team'] == team_name].iloc[0]
        
        bullets = []
        
        # 1. Verticality
        if 'verticality_index' in team_data:
            rel_vert = (team_data['verticality_index'] / self.avg_stats['verticality_index'] - 1) * 100
            bullets.append(f"- **Verticalidad**: {team_name} registra un índice de verticalidad un {rel_vert:.1f}% {'superior' if rel_vert > 0 else 'inferior'} al promedio de la muestra.")
            
        # 2. Field Tilt
        if 'field_tilt_proxy' in team_data:
            rel_tilt = (team_data['field_tilt_proxy'] / self.avg_stats['field_tilt_proxy'] - 1) * 100
            bullets.append(f"- **Presión Territorial (Field Tilt)**: El equipo mantiene una presencia en el último tercio un {rel_tilt:.1f}% {'más' if rel_tilt > 0 else 'menos'} activa que la media.")
            
        # 3. High Line
        if 'high_line_proxy' in team_data:
            rel_line = (team_data['high_line_proxy'] / self.avg_stats['high_line_proxy'] - 1) * 100
            bullets.append(f"- **Línea Defensiva**: Su proxy de línea alta (fueras de juego provocados) es un {abs(rel_line):.1f}% {'más agresivo' if rel_line > 0 else 'conservador'} que el promedio.")
            
        # 4. xG Efficiency
        if 'xg_diff' in team_data:
            bullets.append(f"- **Eficiencia xG**: El diferencial neto de xG es de {team_data['xg_diff']:.2f} por partido.")
            
        # 5. Passing Volume
        if 'Passing_Total_Cmp' in team_data:
            rel_pass = (team_data['Passing_Total_Cmp'] / self.avg_stats['Passing_Total_Cmp'] - 1) * 100
            bullets.append(f"- **Volumen de Pases**: Completa {team_data['Passing_Total_Cmp']:.0f} pases ({rel_pass:+.1f}% vs promedio).")
            
        # 6. Progressive Carries
        if 'Possession_PrgC' in team_data:
            rel_carry = (team_data['Possession_PrgC'] / self.avg_stats['Possession_PrgC'] - 1) * 100
            bullets.append(f"- **Progresión con Balón**: Sus conducciones progresivas están un {rel_carry:+.1f}% respecto a la media.")
            
        return "\n".join(bullets)

    def generate_actionable_insights(self, team_name):
        team_data = self.df[self.df['Team'] == team_name].iloc[0]
        insights = []
        
        # Insight 1: Strength in Verticality/Progression
        if team_data['verticality_index'] > self.avg_stats['verticality_index'] * 1.1:
            insights.append(f"1. **Fortaleza Vertical**: {team_name} ignora el control horizontal excesivo, priorizando envíos directos que rompen líneas.")
        elif team_data['field_tilt_proxy'] > self.avg_stats['field_tilt_proxy'] * 1.1:
            insights.append(f"1. **Dominio Territorial**: El equipo asfixia al rival instalándose permanentemente en campo contrario.")
        else:
            insights.append(f"1. **Estilo Mixto**: El equipo mantiene un equilibrio entre posesión y progresión vertical.")

        # Insight 2: Weakness relative point
        if 'Expected_xGA' in team_data and team_data['Expected_xGA'] > self.avg_stats['Expected_xGA']:
            insights.append(f"2. **Vulnerabilidad Defensiva**: Pese a su ataque, concede un xG en contra elevado ({team_data['Expected_xGA']:.2f}), sugiriendo riesgos en transiciones.")
        else:
            insights.append(f"2. **Solidez Estructural**: Logra mantener un xGA por debajo de la media, validando su sistema defensivo.")

        # Insight 3: Key Driver
        if 'Passing_PrgDist' in team_data:
            insights.append(f"3. **Motor del Juego**: La ganancia de metros vía pases ({team_data['Passing_PrgDist']:.0f}m) es el principal motor de su avance ofensivo.")

        return "\n".join(insights)

from bs4 import Comment

def main():
    # Check if we should load local data if scraping fails
    try:
        scraper = FBRefScraper()
        all_leagues_data = []
        
        for league, lid in scraper.leagues.items():
            tables = scraper.get_league_stats(league, lid)
            if tables:
                df = scraper.process_data(tables)
                all_leagues_data.append(df)
                time.sleep(3) # Respectful scraping

        if not all_leagues_data:
            raise Exception("No web data found")
            
        final_df = pd.concat(all_leagues_data, ignore_index=True)
        final_df = scraper.engineer_features(final_df)
    except Exception as e:
        print(f"Web scraping issue or limited access: {e}")
        print("Intentando cargar datos de ejemplo/manuales si existen...")
        if os.path.exists("flick_scout_full.csv"):
            final_df = pd.read_csv("flick_scout_full.csv")
        else:
            print("No hay datos disponibles. Por favor, exporta las tablas de FBref a CSV manualmente.")
            return

    # Save full dataset
    final_df.to_csv("flick_scout_full.csv", index=False)
    
    # Filter for target teams
    target_teams = ["Barcelona", "Real Madrid", "Atlético Madrid", "Manchester City", "Bayern Munich", "Paris S-G"]
    target_data = final_df[final_df['Team'].isin(target_teams)].copy()
    
    # Reporting
    reporter = ReportGenerator(final_df)
    
    if "Barcelona" in target_data['Team'].values:
        print("\n=== FLICKLENS REPORT: FC BARCELONA ===")
        print("\n--- Style Summary ---")
        print(reporter.generate_style_summary("Barcelona"))
        print("\n--- Actionable Insights ---")
        print(reporter.generate_actionable_insights("Barcelona"))
        
        # Save report to text
        with open("barca_report.txt", "w", encoding="utf-8") as f:
            f.write("=== FLICKLENS REPORT: FC BARCELONA ===\n")
            f.write(reporter.generate_style_summary("Barcelona"))
            f.write("\n\n--- Actionable Insights ---\n")
            f.write(reporter.generate_actionable_insights("Barcelona"))
    
    print("\nSuccess! Results saved to barca_report.txt and flick_scout_top_teams.csv")

if __name__ == "__main__":
    main()

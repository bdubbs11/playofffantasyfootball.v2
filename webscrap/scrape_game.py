from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import json
import time
import re

import sys
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# parse table while loop skips every 2 so if searching for game that doesnt have full table could accidentaly skip table
# one table doesnt have int so it not there and mess everything up.

# Team name to ESPN abbreviation mapping
TEAM_NAME_TO_ABBR = {
    "cardinals": "ARI", "falcons": "ATL", "ravens": "BAL", "bills": "BUF",
    "panthers": "CAR", "bears": "CHI", "bengals": "CIN", "browns": "CLE",
    "cowboys": "DAL", "broncos": "DEN", "lions": "DET", "packers": "GB",
    "texans": "HOU", "colts": "IND", "jaguars": "JAX", "chiefs": "KC",
    "raiders": "LV", "chargers": "LAC", "rams": "LAR", "dolphins": "MIA",
    "vikings": "MIN", "patriots": "NE", "saints": "NO", "giants": "NYG",
    "jets": "NYJ", "eagles": "PHI", "steelers": "PIT", "49ers": "SF",
    "seahawks": "SEA", "buccaneers": "TB", "titans": "TEN", "commanders": "WSH"
}

def get_team_abbrev(team_name):
    """Convert team name to 3-letter abbreviation"""
    if not team_name:
        return "UNK"
    name_lower = team_name.lower()
    for key, abbr in TEAM_NAME_TO_ABBR.items():
        if key in name_lower:
            return abbr
    return team_name.split()[-1][:3].upper()

def setup_driver():
    """Initialize Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

def fetch_page_with_requests(url):
    """Fetch page using requests"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: HTTP {response.status_code}")
    
    return response.text

def extract_teams_from_title(soup):
    """
    Extract teams from SCORE TABLE (table 0), not page title.
    Left row = away team, right row = home team.
    """
    tables = soup.find_all("table")
    if not tables:
        print("⚠️ No tables found for team extraction")
        return "Team 1", "Team 2"

    score_rows = tables[0].find_all("tr")
    teams = []

    for row in score_rows[1:]:
        cells = row.find_all("td")
        if not cells:
            continue
        team_raw = cells[0].get_text(strip=True)

        # Clean "JetsNYJ" → "Jets"
        team_name = re.sub(r'[A-Z]{2,3}$', '', team_raw).strip()
        teams.append(team_name)

    if len(teams) != 2:
        print("⚠️ Unexpected score table format")
        return "Team 1", "Team 2"

    print(f"✅ Teams detected from score table: {teams[0]} vs {teams[1]}")
    return teams[0], teams[1]


def classify_category(headers):
    # print(f"classifying category headers: {headers}")
    """Classify what type of stats this table contains"""
    h = " ".join(headers)
    if "1" in h and "T" in h:
        return "score"
    if "C/ATT" in h:
        return "passing"
    if "CAR" in h and "REC" not in h:
        return "rushing"
    # if "REC" in h:
    #     return "receiving"
    if {"REC", "TGTS"}.issubset(set(headers)):
        return "receiving"
    if "FG" in h or "XP" in h:
        return "kicking"
    if {"FUM", "LOST"}.issubset(set(headers)):
        return "fumbles"
    if {"TOT", "SOLO", "SACKS"}.issubset(set(headers)):
        return "defense"
    if {"INT", "YDS", "TD"}.issubset(set(headers)) and len(headers) == 3:
        return "interceptions"
    return None

def extract_rows(table):
    """Extract all rows from table"""
    rows = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
        if cells:
            rows.append(cells)
    # print(f"extracting rows: {rows}")
    return rows

def extract_player_name(text):
    """Extract clean player name from text like 'Sam Darnold #14'"""
    name = re.sub(r'\s*#\d+\s*$', '', text).strip()
    if name.lower() == 'team':
        return None
    return name if name else None

def parse_stat(s):
    """Convert string to int or float if possible"""
    try:
        return int(s.replace(',', '').strip())
    except:
        try:
            return float(s.replace(',', '').strip())
        except:
            return s.strip()

def determine_position(stats):
    """Determine position based on stats - use rushing/receiving ratio"""
    # If has passing stats, definitely QB
    if "passing" in stats:
        return "QB"
    
    # If has kicking stats, K
    if "kicking" in stats:
        return "K"
    
    # If has both rushing and receiving, compare attempts/receptions
    if "rushing" in stats and "receiving" in stats:
        rush_att = stats["rushing"].get("rushing_attempts", 0)
        receptions = stats["receiving"].get("receptions", 0)
        
        # RBs typically have more rushing attempts than receptions
        # WRs typically have more receptions than rushing attempts
        if rush_att > receptions:
            return "RB"  # More rushes = RB (like Bijan Robinson)
        else:
            return "WR"  # More catches = WR (like Jaxon Smith-Njigba)
    
    # If only rushing, definitely RB
    if "rushing" in stats:
        return "RB"
    
    # If only receiving, likely WR/TE
    if "receiving" in stats:
        return "WR"
    
    return "FLEX"

def scrape_kicker_details(driver, player_url, opponent_abbrev, team_score, opp_score):
    """Scrape kicker's field goal details from player page"""
    print(f"      → Fetching kicker details...")
    try:
        if not player_url.startswith("http"):
            return []
        driver.get(player_url)
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, "lxml")
        tables = soup.find_all("table")
        
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            
            # Recent Games table
            if "Date" in headers and any("19" in h for h in headers):
                rows = table.find_all("tr")[1:]
                opp_idx = headers.index("OPP") if "OPP" in headers else 1
                result_idx = headers.index("Result") if "Result" in headers else 2
                range_start = next((i for i, h in enumerate(headers) if "1-19" in h or "19" in h), None)
                
                if not range_start:
                    continue
                
                # Find matching game
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) <= result_idx:
                        continue
                    
                    game_opp = re.sub(r'[@\s]|vs\.?', '', cells[opp_idx].get_text(strip=True), flags=re.IGNORECASE).upper()
                    score_match = re.search(r'(\d+)-(\d+)', cells[result_idx].get_text(strip=True))
                    if not score_match:
                        continue
                    
                    s1, s2 = int(score_match.group(1)), int(score_match.group(2))
                    opp_match = opponent_abbrev.upper() in game_opp or game_opp in opponent_abbrev.upper()
                    score_match_exact = (s1 == team_score and s2 == opp_score) or (s1 == opp_score and s2 == team_score)
                    
                    if opp_match and score_match_exact:
                        print(f"      ✓ Found game: {cells[opp_idx].get_text(strip=True)} {cells[result_idx].get_text(strip=True)}")
                        
                        kick_details = []
                        ranges = [
                            (cells[range_start].get_text(strip=True), 19),
                            (cells[range_start + 1].get_text(strip=True), 25),
                            (cells[range_start + 2].get_text(strip=True), 35),
                            (cells[range_start + 3].get_text(strip=True), 45),
                            (cells[range_start + 4].get_text(strip=True), 52)
                        ]
                        for stat, dist in ranges:
                            if stat and "-" in stat:
                                made, att = map(int, stat.split("-"))
                                for i in range(att):
                                    kick_details.append({
                                        "distance": dist,
                                        "made": i < made
                                    })
                        return kick_details
        print(f"      ⚠️  No matching game found for kicker")
        return []
    except Exception as e:
        print(f"      ⚠️  Error scraping kicker details: {str(e)[:100]}")
        return []



def parse_stats_by_category(category, cells):
    """Parse stats based on category"""
    stats = {}

    if category == "passing":
        if len(cells) >= 5:
            comp_att = cells[0].strip()
            if '/' in comp_att:
                parts = comp_att.split('/')
                stats["passing_completions"] = parse_stat(parts[0])
                stats["passing_attempts"] = parse_stat(parts[1])
            stats["passing_yards"] = parse_stat(cells[1])
            stats["passing_tds"] = parse_stat(cells[3])
            stats["interceptions"] = parse_stat(cells[4])

    elif category == "rushing":
        if len(cells) >= 4:
            stats["rushing_attempts"] = parse_stat(cells[0])
            stats["rushing_yards"] = parse_stat(cells[1])
            stats["rushing_tds"] = parse_stat(cells[3])

    elif category == "receiving":
        if len(cells) >= 4:
            stats["receptions"] = parse_stat(cells[0])
            stats["receiving_yards"] = parse_stat(cells[1])
            stats["receiving_tds"] = parse_stat(cells[3])

    elif category == "fumbles":
        if len(cells) >= 2:
            stats["fumbles_lost"] = parse_stat(cells[1])
            stats["fumbles_recovered"] = parse_stat(cells[2]) if len(cells) > 2 else 0

    elif category == "kicking":
        for i, cell in enumerate(cells):
            text = cell.strip()
            if '/' in text and i < 2:
                parts = text.split('/')
                stats["fg_made"] = parse_stat(parts[0])
                stats["fg_att"] = parse_stat(parts[1])
            elif i == len(cells) - 2:
                stats["xp_made"] = parse_stat(text)

    return stats

# helper function to detect empty tables so doesnt mess up whole scraping
def has_numeric_cell(rows):
    for row in rows:
        for cell in row:
            if any(c.isdigit() for c in cell):
                return True
    return False


def is_valid_stat_table(table):
    rows = extract_rows(table)
    if len(rows) < 2:
        return False
    if not has_numeric_cell(rows):
        return False
    return True


def parse_tables(tables, team1, team2, driver):
    """Main parsing function for NFL game tables"""
    print("\nParsing tables...")
    game = {
        "score": {},
        "players": {},
        "defense": {
            team1: {"points_allowed": 0, "sacks": 0, "interceptions": 0, "fumbles_recovered": 0, "defensive_tds": 0},
            team2: {"points_allowed": 0, "sacks": 0, "interceptions": 0, "fumbles_recovered": 0, "defensive_tds": 0}
        }
    }

    fumbles_lost_tracker = {team1: 0, team2: 0}

    # --- Collect all player links first (needed for kicker scrape) ---
    player_links = {}
    for table in tables[1:]:
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            player_name = extract_player_name(cells[0].get_text(strip=True))
            if not player_name:
                continue
            link_tag = cells[0].find("a")
            if link_tag and link_tag.get("href"):
                href = link_tag["href"]
                if not href.startswith("http"):
                    href = "https://www.espn.com" + (href if href.startswith("/") else "/" + href)
                player_links[player_name] = href

    # =====================
    # SCORE TABLE (TABLE 0)
    # =====================
    if tables:
        rows = extract_rows(tables[0])
        print("\n=== SCORE ===")
        for row in rows[1:]:
            team = team1 if team1 in row[0] else team2
            game["score"][team] = int(row[-1])
            print(f"{team}: {row[-1]} points")

    # =====================
    # PLAYER/STAT TABLE PAIRS
    # =====================
    idx = 1
    while idx < len(tables) - 1:

        # just to skip empty tables
        if not is_valid_stat_table(tables[idx]):
            idx += 1
            continue

        if not is_valid_stat_table(tables[idx + 1]):
            idx += 1
            continue

      
        player_table = tables[idx]
        stat_table = tables[idx + 1]

        # --- Extract player names ---
        players = []
        for row in player_table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            player_name = extract_player_name(cells[0].get_text(strip=True))
            if not player_name:
                continue
            players.append(player_name)

        if not players:
            idx += 2
            continue

        headers = [th.get_text(strip=True) for th in stat_table.find_all("th")]
        stat_rows = extract_rows(stat_table)[1:]  # skip header 
        category = classify_category(headers)
        # only kicker needs this info
        team = team1 if (idx // 2) % 2 == 0 else team2
        opponent = team1 if team == team2 else team2

        if category is None:
            idx += 2
            continue

        # --- Defense totals ---
        if category == "defense":
            team_total_row = stat_rows[-1] if stat_rows else []
            if team_total_row and len(team_total_row) > 6:
                game["defense"][team]["sacks"] = parse_stat(team_total_row[2])
                game["defense"][team]["defensive_tds"] = parse_stat(team_total_row[6])
                game["defense"][team]["points_allowed"] = game["score"].get(opponent, 0)
            idx += 2
            continue

        # --- Interceptions totals ---
        if category == "interceptions":
            team_total_row = stat_rows[-1] if stat_rows else []
            if team_total_row:
                game["defense"][team]["interceptions"] = parse_stat(team_total_row[0])
                if len(team_total_row) > 2:
                    game["defense"][team]["defensive_tds"] += parse_stat(team_total_row[2])
            idx += 2
            continue

        # --- Fumbles ---
        if category == "fumbles":
            for p_idx, player in enumerate(players):
                if p_idx >= len(stat_rows):
                    continue
                row = stat_rows[p_idx]
                lost = parse_stat(row[1]) if len(row) > 1 else 0
                rec = parse_stat(row[2]) if len(row) > 2 else 0
                if lost > 0:
                    fumbles_lost_tracker[team] += lost
                if player not in game["players"]:
                    game["players"][player] = {"team": team, "position": None, "stats": {}}
                if lost > 0 or rec > 0:
                    game["players"][player]["stats"]["fumbles"] = {"LOST": lost, "REC": rec}
            idx += 2
            continue

        # --- Regular player stats (passing, rushing, receiving, kicking) ---
        for p_idx, player in enumerate(players):
            if p_idx >= len(stat_rows):
                continue
            row = stat_rows[p_idx]
            if player not in game["players"]:
                game["players"][player] = {"team": team, "position": None, "stats": {}}

            stats_dict = parse_stats_by_category(category, row)
            # print(f"categories: {category}")

            # --- Kicker field goals scrape ---
            if category == "kicking" and driver and player in player_links:
                # Assign team and opponent deterministically: first kicker table = team1 vs team2, second = team2 vs team1
                if not hasattr(parse_tables, "_kicker_call_count"):
                    parse_tables._kicker_call_count = 0
                if parse_tables._kicker_call_count % 2 == 0:
                    kicker_team = team1
                    kicker_opponent = team2
                else:
                    kicker_team = team2
                    kicker_opponent = team1
                parse_tables._kicker_call_count += 1

                print(f"Scraping kicker stats for {player} ({kicker_team}) vs {kicker_opponent}")
                kicks = scrape_kicker_details(
                    driver,
                    player_links[player],
                    get_team_abbrev(kicker_opponent),
                    int(game["score"].get(kicker_team, 0)),
                    int(game["score"].get(kicker_opponent, 0))
                )
                print(f"Found {len(kicks)} kicks for {player}")
                if kicks:
                    stats_dict["field_goals"] = kicks

                # Override the team in the player record (important if it was saved wrong earlier)
                game["players"][player]["team"] = kicker_team

            if stats_dict:
                # Merge stats_dict with existing player stats to avoid overwriting
                game["players"][player]["stats"][category] = {
                    **game["players"][player]["stats"].get(category, {}),
                    **stats_dict
                }

        idx += 2

    # --- Assign fumbles recovered to opposing defense ---
    game["defense"][team1]["fumbles_recovered"] = fumbles_lost_tracker[team2]
    game["defense"][team2]["fumbles_recovered"] = fumbles_lost_tracker[team1]

    # --- Determine player positions ---
    for player, info in game["players"].items():
        if info["position"] is None:
            info["position"] = determine_position(info["stats"])

    return game



def scrape_game_stats(game_id, driver=None):
    """Main scraping function"""
    url = f"https://www.espn.com/nfl/boxscore/_/gameId/{game_id}"
    print(f"\n{'='*60}")
    print(f"🏈 Scraping Game ID: {game_id}")
    print(f"{'='*60}")

    html = fetch_page_with_requests(url)
    soup = BeautifulSoup(html, "lxml")

    team1, team2 = extract_teams_from_title(soup)

    print(f"\nTeams detected:")
    print(f"  {team1} vs {team2}")

    tables = soup.find_all("table")
    print(f"\n📊 Found {len(tables)} tables")

    game_data = parse_tables(tables=tables, team1=team1, team2=team2, driver=driver)

    print("\n" + "="*80)
    print("=== FINAL PLAYER STATS ===")
    print("="*80)
    for player, info in game_data["players"].items():
        stat_line = f"{player}, {info['position']}, {info['team']}"
        
        # Add passing stats
        if "passing" in info["stats"]:
            p = info["stats"]["passing"]
            stat_line += f", {p['passing_completions']}/{p['passing_attempts']} passing, {p['passing_yards']} pass yds, {p['passing_tds']} pass TD, {p['interceptions']} INT"
        
        # Add rushing stats
        if "rushing" in info["stats"]:
            r = info["stats"]["rushing"]
            stat_line += f", {r['rushing_attempts']} rush att, {r['rushing_yards']} rush yds, {r['rushing_tds']} rush TD"
        
        # Add receiving stats
        if "receiving" in info["stats"]:
            rec = info["stats"]["receiving"]
            stat_line += f", {rec['receptions']} rec, {rec['receiving_yards']} rec yds, {rec['receiving_tds']} rec TD"
        
        # Add kicking stats
        if "kicking" in info["stats"]:
            k = info["stats"]["kicking"]
            stat_line += f", {k.get('fg_made', 0)}/{k.get('fg_att', 0)} FG, {k.get('xp_made', 0)} XP"
        
        # Add fumble stats
        if "fumbles" in info["stats"]:
            f = info["stats"]["fumbles"]
            stat_line += f", {f['LOST']} fumbles lost"
        
        print(stat_line)

    print("\n" + "="*80)
    print("=== DEFENSE STATS ===")
    print("="*80)
    for team, d_stats in game_data["defense"].items():
        print(f"{team} Defense: {d_stats['interceptions']} INT, {d_stats['fumbles_recovered']} Fum Rec, "
              f"{d_stats['sacks']} sacks, {d_stats['defensive_tds']} TD, {d_stats['points_allowed']} pts allowed")

    # Save to JSON
    output_file = f"game_stats_output.json"
    with open(output_file, "w") as f:
        json.dump(game_data, f, indent=2)
    print(f"\n✅ Data saved to {output_file}")

    return game_data

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# if __name__ == "__main__":
#     print("="*60)
#     print("🏈 NFL FANTASY FOOTBALL STATS SCRAPER")
#     print("="*60)
    
#     print("\n📋 TEST MODE: Scraping single game")
#     test_game_id = "401772900"
    
#     driver = setup_driver()
#     try:
#         game_data = scrape_game_stats(test_game_id, driver)
        
#     finally:
#         driver.quit()
    
#     print("\n" + "="*60)
#     print("✅ SCRAPING COMPLETE!")
#     print("="*60)


if __name__ == "__main__":
    print("="*60)
    print("🏈 NFL FANTASY FOOTBALL STATS SCRAPER")
    print("="*60)

    # Check if a game URL or ID is passed as an argument
    if len(sys.argv) > 1:
        game_url_or_id = sys.argv[1]
        print(f"\n📋 Scraping game: {game_url_or_id}")
    else:
        game_url_or_id = "401772900"  # fallback test game
        print("\n📋 TEST MODE: Scraping single game")

    driver = setup_driver()
    try:
        game_data = scrape_game_stats(game_url_or_id.split("/")[-1] if "http" in game_url_or_id else game_url_or_id, driver)
    finally:
        driver.quit()

    # Save output to a unique file per game
    # If game_url_or_id is a URL, extract ID from it
    game_id = game_url_or_id.split("/")[-1] if "http" in game_url_or_id else game_url_or_id
    
    # Check if folder path was provided as second argument
    if len(sys.argv) > 2:
        folder = sys.argv[2]
    else:
        folder = "scraped_games"  # Default folder
    
    save_path = os.path.join(folder, f"game_{game_id}.json")
    
    os.makedirs(folder, exist_ok=True)
    with open(save_path, "w") as f:
        json.dump(game_data, f, indent=4)

    print(f"\n✅ SCRAPING COMPLETE! Saved to {save_path}")
    print("="*60)
# might need to add a timer rest period to let page load fully before scraping
# just testing right now but the wifi could also be slow that makes most recent game played also scaped when looking for games from previous year.
#  (weeks might not matter but will test later)

# rams vs seahawks 2025 week 15 does not have proper rams defense stats. no clue why not will need to hammer debug again and check later. 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import json
import time
import re

# Team name to ESPN abbreviation mapping
TEAM_NAME_TO_ABBR = {
    "cardinals": "ARI", "falcons": "ATL", "ravens": "BAL", "bills": "BUF",
    "panthers": "CAR", "bears": "CHI", "bengals": "CIN", "browns": "CLE",
    "cowboys": "DAL", "broncos": "DEN", "lions": "DET", "packers": "GB",
    "texans": "HOU", "colts": "IND", "jaguars": "JAX", "chiefs": "KC",
    "raiders": "LV", "chargers": "LAC", "rams": "LAR", "dolphins": "MIA",
    "vikings": "MIN", "patriots": "NE", "saints": "NO", "giants": "NYG",
    "jets": "NYJ", "eagles": "PHI", "steelers": "PIT", "49ers": "SF",
    "seahawks": "SEA", "buccaneers": "TB", "titans": "TEN", "commanders": "WAS"
}

def get_team_abbrev(team_name):
    """Convert team name to 3-letter abbreviation"""
    if not team_name:
        return "UNK"
    name_lower = team_name.lower()
    for key, abbr in TEAM_NAME_TO_ABBR.items():
        if key in name_lower:
            return abbr
    # Fallback: last word, first 3 letters
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
    """Fetch page using requests - gets all 40 tables"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch: HTTP {response.status_code}")
    return response.text

def parse_stat(text):
    """Convert stat text to int"""
    if not text or text == '--':
        return 0
    if '/' in text:
        return int(text.split('/')[0]) if text.split('/')[0].isdigit() else 0
    try:
        return int(text.replace(',', '').strip())
    except:
        return 0

def extract_player_name(text):
    """Extract player name, remove jersey number and 'team'"""
    name = re.sub(r'\s*#\d+\s*$', '', text).strip()
    return None if name.lower() == 'team' else (name if name else None)

def scrape_kicker_details(driver, player_url, opponent_abbrev, team_score, opp_score):
    """Scrape kicker's field goal details from player page"""
    print(f"      → Fetching kicker details...")
    print(f"      → Looking for: vs {opponent_abbrev}, score {team_score}-{opp_score}")
    
    try:
        if not player_url.startswith("http"):
            return []
        
        driver.get(player_url)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, "lxml")
        tables = soup.find_all("table")
        
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            
            # Find Recent Games table
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
                    
                    opp_text = cells[opp_idx].get_text(strip=True)
                    result_text = cells[result_idx].get_text(strip=True)
                    
                    # Clean opponent text
                    game_opp = re.sub(r'[@\s]|vs\.?', '', opp_text, flags=re.IGNORECASE).upper()
                    
                    # Extract score
                    score_match = re.search(r'(\d+)-(\d+)', result_text)
                    if not score_match:
                        continue
                    
                    s1, s2 = int(score_match.group(1)), int(score_match.group(2))
                    
                    # Check if this matches our game
                    opp_match = opponent_abbrev.upper() in game_opp or game_opp in opponent_abbrev.upper()
                    score_match_exact = (s1 == team_score and s2 == opp_score) or (s1 == opp_score and s2 == team_score)
                    
                    if opp_match and score_match_exact:
                        print(f"      ✓ Found game: {opp_text} {result_text}")
                        
                        # Extract kicks by range
                        kick_details = []
                        ranges = [
                            (cells[range_start].get_text(strip=True), "1-19", 19),
                            (cells[range_start + 1].get_text(strip=True), "20-29", 25),
                            (cells[range_start + 2].get_text(strip=True), "30-39", 35),
                            (cells[range_start + 3].get_text(strip=True), "40-49", 45),
                            (cells[range_start + 4].get_text(strip=True), "50+", 52)
                        ]
                        
                        for stat, range_name, dist in ranges:
                            if stat and stat != "0-0" and "-" in stat:
                                parts = stat.split("-")
                                made = int(parts[0]) if parts[0].isdigit() else 0
                                attempts = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                                
                                for i in range(attempts):
                                    kick_details.append({
                                        "distance": dist,
                                        "made": i < made,
                                        "range": range_name
                                    })
                        
                        # Get exact longest distance
                        lng_idx = headers.index("LNG") if "LNG" in headers else None
                        if lng_idx and len(cells) > lng_idx:
                            lng_text = cells[lng_idx].get_text(strip=True)
                            if lng_text.isdigit():
                                lng = int(lng_text)
                                for kick in reversed(kick_details):
                                    if kick["made"] and kick["distance"] >= 40:
                                        kick["distance"] = lng
                                        break
                        
                        print(f"      ✓ Extracted {len(kick_details)} kicks")
                        return kick_details
                
                print(f"      ⚠️  No matching game found")
                return []
        
        return []
    except Exception as e:
        print(f"      ⚠️  Error: {str(e)[:100]}")
        return []

def scrape_game_stats(game_id, driver=None):
    """Scrape stats for one game"""
    url = f"https://www.espn.com/nfl/boxscore/_/gameId/{game_id}"
    print(f"\n{'='*60}")
    print(f"🏈 Game ID: {game_id}")
    print(f"{'='*60}")
    
    html = fetch_page_with_requests(url)
    soup = BeautifulSoup(html, "lxml")
    
    title = soup.title.string if soup.title else ""
    print(f"📰 {title}")
    
    # Parse teams and scores
    match = re.search(r'(.+?)\s+(\d+)-(\d+)\s+(.+?)\s+\(', title)
    if match:
        team1_name = match.group(1).strip()
        team1_score = int(match.group(2))
        team2_score = int(match.group(3))
        team2_name = match.group(4).strip()
    else:
        team1_name, team2_name = "Team1", "Team2"
        team1_score, team2_score = 0, 0
    
    team1_abbr = get_team_abbrev(team1_name)
    team2_abbr = get_team_abbrev(team2_name)
    winner = team1_name if team1_score > team2_score else team2_name
    
    print(f"🏆 {team1_name} ({team1_abbr}) {team1_score} vs {team2_name} ({team2_abbr}) {team2_score}")
    print(f"   Winner: {winner}")
    
    tables = soup.find_all("table")
    print(f"\n📊 Found {len(tables)} tables")
    
    # Determine winner/loser for alternating pattern
    if team1_score > team2_score:
        winner_name, winner_abbr, winner_score = team1_name, team1_abbr, team1_score
        loser_name, loser_abbr, loser_score = team2_name, team2_abbr, team2_score
    else:
        winner_name, winner_abbr, winner_score = team2_name, team2_abbr, team2_score
        loser_name, loser_abbr, loser_score = team1_name, team1_abbr, team1_score
    
    game_data = {
        "game_id": game_id,
        "teams": {
            winner_name: {"score": winner_score, "players": {}},
            loser_name: {"score": loser_score, "players": {}}
        },
        "winner": winner
    }
    
    # Process tables in alternating pairs
    # Pairs 0-1, 4-5, 8-9... = Winner
    # Pairs 2-3, 6-7, 10-11... = Loser
    print(f"\n📋 Processing tables (alternating winner/loser pattern)")
    
    i = 0
    while i < len(tables) - 1:
        pair_idx = i // 2
        is_winner = (pair_idx % 2 == 0)
        
        if is_winner:
            team_name, team_abbr, team_score = winner_name, winner_abbr, winner_score
            opp_abbr, opp_score = loser_abbr, loser_score
        else:
            team_name, team_abbr, team_score = loser_name, loser_abbr, loser_score
            opp_abbr, opp_score = winner_abbr, winner_score
        
        current_table = tables[i]
        next_table = tables[i + 1]
        
        headers = [th.get_text(strip=True) for th in next_table.find_all("th")]
        
        # Identify stat category
        category = None
        if "C/ATT" in headers and "INT" in headers:
            category = "passing"
        elif "CAR" in headers and "YDS" in headers and "REC" not in headers:
            category = "rushing"
        elif "REC" in headers and "YDS" in headers:
            category = "receiving"
        elif "FUM" in headers and "LOST" in headers:
            category = "fumbles"
        elif "INT" in headers and "YDS" in headers and "TD" in headers and "CAR" not in headers:
            category = "interceptions"
        elif any("TOT" in h or "SOLO" in h for h in headers):
            category = "defense"
        elif "FG" in headers or "XP" in headers:
            category = "kicking"
        
        if category:
            print(f"\n  {category.upper()} - {team_name} ({team_abbr})")
            
            # Get player names
            name_rows = current_table.find_all("tr")
            player_names = []
            player_links = {}
            
            for row in name_rows:
                cells = row.find_all("td")
                if cells:
                    text = cells[0].get_text(strip=True)
                    name = extract_player_name(text)
                    if name:
                        player_names.append(name)
                        link = cells[0].find("a")
                        if link and link.get("href"):
                            href = link["href"]
                            if not href.startswith("http"):
                                href = "https://www.espn.com" + (href if href.startswith("/") else "/" + href)
                            player_links[name] = href
            
            # Get stats
            stat_rows = next_table.find_all("tr")[1:]
            
            for idx, row in enumerate(stat_rows):
                if idx >= len(player_names):
                    break
                
                player_name = player_names[idx]
                cells = row.find_all("td")
                
                if not cells:
                    continue
                
                # Initialize player
                players_dict = game_data["teams"][team_name]["players"]
                if player_name not in players_dict:
                    players_dict[player_name] = {
                        "name": player_name,
                        "team": team_name,
                        "position": get_position(category),
                        "stats": {}
                    }
                
                # Parse stats
                stats = parse_stats(category, cells)
                
                # Kicker details
                if category == "kicking" and player_name in player_links and driver:
                    kick_details = scrape_kicker_details(driver, player_links[player_name], 
                                                         opp_abbr, team_score, opp_score)
                    if kick_details:
                        stats["field_goals"] = kick_details
                
                players_dict[player_name]["stats"].update(stats)
                
                if category == "passing":
                    players_dict[player_name]["position"] = "QB"
                elif category == "kicking":
                    players_dict[player_name]["position"] = "K"
                
                # Print
                if stats:
                    stats_str = ", ".join([f"{k}: {v}" for k, v in stats.items() if k != "field_goals"])
                    if stats_str:
                        print(f"    {player_name}: {stats_str}")
        
        i += 2
    
    # Convert to list
    for team in game_data["teams"]:
        game_data["teams"][team]["players"] = list(game_data["teams"][team]["players"].values())
    
    return game_data

def parse_stats(category, cells):
    """Parse stats by category"""
    stats = {}
    
    if category == "passing":
        if len(cells) >= 5:
            comp_att = cells[0].get_text().strip()
            if '/' in comp_att:
                parts = comp_att.split('/')
                stats["passing_completions"] = parse_stat(parts[0])
                stats["passing_attempts"] = parse_stat(parts[1])
            stats["passing_yards"] = parse_stat(cells[1].get_text())
            stats["passing_tds"] = parse_stat(cells[3].get_text())
            stats["interceptions"] = parse_stat(cells[4].get_text())
    
    elif category == "rushing":
        if len(cells) >= 4:
            stats["rushing_attempts"] = parse_stat(cells[0].get_text())
            stats["rushing_yards"] = parse_stat(cells[1].get_text())
            stats["rushing_tds"] = parse_stat(cells[3].get_text())
    
    elif category == "receiving":
        if len(cells) >= 4:
            stats["receptions"] = parse_stat(cells[0].get_text())
            stats["receiving_yards"] = parse_stat(cells[1].get_text())
            stats["receiving_tds"] = parse_stat(cells[3].get_text())
    
    elif category == "fumbles":
        if len(cells) >= 2:
            stats["fumbles"] = parse_stat(cells[0].get_text())
            stats["fumbles_lost"] = parse_stat(cells[1].get_text())
    
    elif category == "interceptions":
        if len(cells) >= 1:
            stats["interceptions"] = parse_stat(cells[0].get_text())
        if len(cells) >= 2:
            stats["int_return_yards"] = parse_stat(cells[1].get_text())
        if len(cells) >= 3:
            stats["int_return_tds"] = parse_stat(cells[2].get_text())
    
    elif category == "kicking":
        for i, cell in enumerate(cells):
            text = cell.get_text().strip()
            if '/' in text and i < 2:
                parts = text.split('/')
                stats["fg_made"] = parse_stat(parts[0])
                stats["fg_att"] = parse_stat(parts[1])
            elif i == len(cells) - 2:
                stats["xp_made"] = parse_stat(text)
    
    elif category == "defense":
        if len(cells) >= 1:
            stats["tackles"] = parse_stat(cells[0].get_text())
        if len(cells) >= 3:
            stats["sacks"] = parse_stat(cells[2].get_text())
        if len(cells) >= 6:
            stats["defensive_tds"] = parse_stat(cells[-1].get_text())
    
    return stats

def get_position(category):
    """Map category to position"""
    return {
        "passing": "QB", "rushing": "RB", "receiving": "WR",
        "kicking": "K", "defense": "DEF", "interceptions": "DEF", "fumbles": "FLEX"
    }.get(category, "FLEX")

def scrape_multiple_games(game_ids):
    """Scrape multiple games"""
    driver = setup_driver()
    all_games = []
    
    try:
        for i, game_id in enumerate(game_ids, 1):
            print(f"\n{'#'*60}\nGAME {i}/{len(game_ids)}\n{'#'*60}")
            game_data = scrape_game_stats(game_id, driver)
            all_games.append(game_data)
            if i < len(game_ids):
                time.sleep(3)
        return all_games
    finally:
        driver.quit()

def save_results(games_data, filename="fantasy_stats.json"):
    """Save to JSON"""
    with open(filename, 'w') as f:
        json.dump(games_data, f, indent=2)
    print(f"\n💾 Saved to {filename}")

if __name__ == "__main__":
    print("="*60)
    print("🏈 NFL FANTASY STATS SCRAPER")
    print("="*60)
    
    test_game_id = "401772900"
    
    driver = setup_driver()
    try:
        game_data = scrape_game_stats(test_game_id, driver)
        save_results([game_data], "test_game.json")
        
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        for team_name, team_info in game_data["teams"].items():
            print(f"\n{team_name} ({team_info['score']} points)")
            print(f"  Players: {len(team_info['players'])}")
            
            positions = {}
            for player in team_info['players']:
                pos = player['position']
                positions[pos] = positions.get(pos, 0) + 1
            
            for pos, count in sorted(positions.items()):
                print(f"    {pos}: {count}")
        
        print(f"\n🏆 Winner: {game_data['winner']}")
    finally:
        driver.quit()
    
    print("\n" + "="*60)
    print("✅ COMPLETE")
    print("="*60)


    # count tables.py

#     from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
# from bs4 import BeautifulSoup
# import requests
# import time
# import sys

# def setup_driver():
#     """Initialize Chrome driver with options"""
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
#     driver = webdriver.Chrome(
#         service=Service(ChromeDriverManager().install()),
#         options=chrome_options
#     )
#     return driver

# def scrape_with_requests(url):
#     """Scrape using requests (finds all 40 tables)"""
#     print(f"\n{'='*60}")
#     print(f"🌐 METHOD 1: Using requests (direct HTML fetch)")
#     print(f"{'='*60}")
    
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#         'Accept-Language': 'en-US,en;q=0.5',
#         'Accept-Encoding': 'gzip, deflate, br',
#         'Connection': 'keep-alive',
#         'Upgrade-Insecure-Requests': '1'
#     }
    
#     try:
#         response = requests.get(url, headers=headers, timeout=10)
#         print(f"✅ Status Code: {response.status_code}")
        
#         if response.status_code != 200:
#             print(f"❌ Request failed with status {response.status_code}")
#             return None, None
        
#         html = response.text
#         soup = BeautifulSoup(html, "lxml")
#         return html, soup
#     except Exception as e:
#         print(f"❌ Error with requests: {str(e)}")
#         return None, None

# def count_tables_selenium(driver, url):
#     """Count tables using Selenium (for comparison)"""
#     print(f"\n{'='*60}")
#     print(f"🤖 METHOD 2: Using Selenium (browser automation)")
#     print(f"{'='*60}")
    
#     driver.get(url)
    
#     # Wait for content
#     print("⏳ Loading page...")
#     try:
#         WebDriverWait(driver, 15).until(
#             EC.presence_of_element_located((By.TAG_NAME, "table"))
#         )
#     except:
#         print("⚠️  No tables found or page didn't load in time")
#         return None, None
    
#     # More aggressive scrolling to load all content (both teams)
#     print("📜 Scrolling to load all content...")
    
#     # Get initial page height
#     initial_height = driver.execute_script("return document.body.scrollHeight")
#     print(f"   Initial page height: {initial_height}px")
    
#     # Scroll in increments to trigger lazy loading
#     scroll_pause = 1
#     last_height = initial_height
#     scroll_attempts = 0
#     max_scrolls = 10
    
#     while scroll_attempts < max_scrolls:
#         # Scroll down
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(scroll_pause)
        
#         # Check if new content loaded
#         new_height = driver.execute_script("return document.body.scrollHeight")
#         if new_height == last_height:
#             break
#         last_height = new_height
#         scroll_attempts += 1
#         print(f"   Scroll {scroll_attempts}: New height = {new_height}px")
    
#     # Scroll back to top
#     driver.execute_script("window.scrollTo(0, 0);")
#     time.sleep(2)
    
#     # Scroll down again slowly to ensure everything loads
#     print("   Final scroll pass...")
#     for i in range(0, last_height, 500):
#         driver.execute_script(f"window.scrollTo(0, {i});")
#         time.sleep(0.5)
    
#     # Scroll to bottom one more time
#     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#     time.sleep(3)  # Extra time for all tables to load
    
#     html = driver.page_source
#     soup = BeautifulSoup(html, "lxml")
#     return html, soup

# def analyze_tables(soup, method_name):
#     """Analyze tables from BeautifulSoup object"""
    
#     # Get page title
#     title = soup.title.string if soup.title else "Unknown"
#     print(f"📰 Page Title: {title}")
    
#     # Find all tables using different methods
#     tables = soup.find_all("table")
#     tables_select = soup.select("table")
    
#     total_tables = len(tables)
#     total_tables_select = len(tables_select)
    
#     print(f"\n📊 TABLE COUNT RESULTS ({method_name}):")
#     print(f"   find_all('table'): {total_tables}")
#     print(f"   select('table'): {total_tables_select}")
    
#     if total_tables != total_tables_select:
#         print(f"   ⚠️  Different counts! Using find_all result: {total_tables}")
    
#     # Analyze table structure and identify teams
#     print(f"\n📋 TABLE DETAILS ({method_name}):")
    
#     # Track teams found
#     teams_found = set()
#     tables_by_team = {"Seahawks": [], "Falcons": [], "Unknown": []}
    
#     for i, table in enumerate(tables, 1):
#         rows = table.find_all("tr")
#         cols = []
#         if rows:
#             # Get column count from first row
#             first_row = rows[0]
#             cols = first_row.find_all(["th", "td"])
        
#         # Get table class/id for identification
#         table_class = table.get("class", [])
#         table_id = table.get("id", "")
        
#         # Try to identify team by looking at parent elements and nearby text
#         team_name = "Unknown"
#         parent = table.parent
#         search_depth = 0
#         while parent and search_depth < 5:
#             parent_text = parent.get_text() if hasattr(parent, 'get_text') else str(parent)
#             if "Seattle" in parent_text or "Seahawks" in parent_text:
#                 team_name = "Seahawks"
#                 teams_found.add("Seahawks")
#                 break
#             elif "Atlanta" in parent_text or "Falcons" in parent_text:
#                 team_name = "Falcons"
#                 teams_found.add("Falcons")
#                 break
#             parent = parent.parent if hasattr(parent, 'parent') else None
#             search_depth += 1
        
#         # Also check table content for team names
#         table_text = table.get_text()
#         if "Seattle" in table_text or "Seahawks" in table_text:
#             team_name = "Seahawks"
#             teams_found.add("Seahawks")
#         elif "Atlanta" in table_text or "Falcons" in table_text:
#             team_name = "Falcons"
#             teams_found.add("Falcons")
        
#         tables_by_team[team_name].append(i)
        
#         # Try to identify table type
#         table_type = "Unknown"
#         if rows:
#             headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]
#             if headers:
#                 if "C/ATT" in headers or "PASS" in str(headers).upper():
#                     table_type = "Passing Stats"
#                 elif "CAR" in headers and "YDS" in headers:
#                     table_type = "Rushing Stats"
#                 elif "REC" in headers:
#                     table_type = "Receiving Stats"
#                 elif "FG" in headers or "XP" in headers:
#                     table_type = "Kicking Stats"
#                 elif "TOT" in headers or "TACK" in headers:
#                     table_type = "Defense Stats"
#                 elif "FUM" in headers:
#                     table_type = "Fumbles"
#                 elif "INT" in headers:
#                     table_type = "Interceptions"
#                 elif "NO" in headers and "YDS" in headers and ("RET" in str(headers).upper() or "PUNT" in str(headers).upper()):
#                     table_type = "Returns"
#                 elif "PUNT" in str(headers).upper():
#                     table_type = "Punting"
#                 else:
#                     table_type = "Player Names" if len(headers) < 3 else "Stats Table"
#             else:
#                 table_type = "Player Names"
        
#         print(f"   Table {i:2d}: [{team_name:8s}] {len(rows):2d} rows, {len(cols):2d} cols | Type: {table_type}")
#         if table_class:
#             print(f"            Classes: {table_class}")
#         if table_id:
#             print(f"            ID: {table_id}")
    
#     # Team analysis
#     print(f"\n🏈 TEAM ANALYSIS ({method_name}):")
#     print(f"   Teams detected: {', '.join(teams_found) if teams_found else 'None'}")
#     print(f"   Seahawks tables: {len(tables_by_team['Seahawks'])}")
#     print(f"   Falcons tables: {len(tables_by_team['Falcons'])}")
#     print(f"   Unknown team tables: {len(tables_by_team['Unknown'])}")
    
#     if len(teams_found) < 2:
#         print(f"\n⚠️  WARNING: Only found tables for {len(teams_found)} team(s)!")
#         print(f"   Expected 2 teams. This suggests some tables may not have loaded.")
#         if "Seahawks" in teams_found and "Falcons" not in teams_found:
#             print(f"   ⚠️  Missing Falcons tables!")
#         elif "Falcons" in teams_found and "Seahawks" not in teams_found:
#             print(f"   ⚠️  Missing Seahawks tables!")
    
#     # Check for nested tables
#     nested_tables = soup.find_all("table", recursive=True)
#     nested_count = len(nested_tables)
#     if nested_count != total_tables:
#         print(f"\n⚠️  Found {nested_count} total tables (including nested), but {total_tables} top-level tables")
    
#     # Check for tables in different sections
#     print(f"\n🔍 SEARCHING BY SECTION ({method_name}):")
#     sections = soup.find_all(["div", "section"], class_=lambda x: x and ("table" in str(x).lower() or "stats" in str(x).lower() or "box" in str(x).lower()))
#     print(f"   Found {len(sections)} potential stat sections")
    
#     # Look for tables by data attributes
#     data_tables = soup.find_all("table", attrs={"data-testid": True})
#     if data_tables:
#         print(f"   Found {len(data_tables)} tables with data-testid attributes")
    
#     return tables, total_tables

# def count_tables(url, use_selenium=False):
#     """Count all tables on the page - compare requests vs Selenium"""
#     print(f"\n{'='*60}")
#     print(f"🔍 Analyzing: {url}")
#     print(f"{'='*60}")
    
#     # Method 1: Use requests (this finds all 40 tables)
#     html_requests, soup_requests = scrape_with_requests(url)
    
#     if soup_requests:
#         tables_requests, count_requests = analyze_tables(soup_requests, "REQUESTS")
#         print(f"\n✅ REQUESTS METHOD: Found {count_requests} tables")
#     else:
#         tables_requests = []
#         count_requests = 0
#         print(f"\n❌ REQUESTS METHOD: Failed")
    
#     # Method 2: Use Selenium (for comparison)
#     if use_selenium:
#         driver = setup_driver()
#         try:
#             html_selenium, soup_selenium = count_tables_selenium(driver, url)
#             if soup_selenium:
#                 tables_selenium, count_selenium = analyze_tables(soup_selenium, "SELENIUM")
#                 print(f"\n✅ SELENIUM METHOD: Found {count_selenium} tables")
                
#                 # Compare results
#                 print(f"\n{'='*60}")
#                 print(f"📊 COMPARISON:")
#                 print(f"   Requests: {count_requests} tables")
#                 print(f"   Selenium: {count_selenium} tables")
#                 print(f"   Difference: {abs(count_requests - count_selenium)} tables")
                
#                 if count_requests > count_selenium:
#                     print(f"\n⚠️  REQUESTS found {count_requests - count_selenium} MORE tables!")
#                     print(f"   This suggests Selenium is missing some tables.")
#                     find_missing_tables(tables_requests, tables_selenium)
#             else:
#                 print(f"\n❌ SELENIUM METHOD: Failed")
#         finally:
#             driver.quit()
#     else:
#         # Just use requests results (default - this finds all 40 tables)
#         if soup_requests:
#             tables_requests, count_requests = analyze_tables(soup_requests, "REQUESTS")
    
#     return count_requests

# def find_missing_tables(tables_requests, tables_selenium):
#     """Find which tables are in requests but not in Selenium"""
#     print(f"\n🔍 ANALYZING MISSING TABLES:")
    
#     # Create signatures for each table (first few rows of text)
#     def get_table_signature(table):
#         rows = table.find_all("tr")[:3]  # First 3 rows
#         return " | ".join([row.get_text(strip=True)[:50] for row in rows])
    
#     selenium_signatures = {get_table_signature(t): i for i, t in enumerate(tables_selenium)}
#     missing = []
    
#     for i, table in enumerate(tables_requests):
#         sig = get_table_signature(table)
#         if sig not in selenium_signatures:
#             missing.append((i+1, table))
#             print(f"   Missing Table {i+1}:")
#             # Try to identify what it is
#             rows = table.find_all("tr")
#             if rows:
#                 headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]
#                 if headers:
#                     print(f"      Headers: {headers[:5]}")
#                 else:
#                     first_cells = [td.get_text(strip=True) for td in rows[0].find_all("td")[:3]]
#                     print(f"      First row: {first_cells}")
    
#     if missing:
#         print(f"\n   Total missing: {len(missing)} tables")
#     else:
#         print(f"   ✅ All tables found in both methods")

# def main():
#     """Main function"""
#     use_selenium = "--selenium" in sys.argv or "-s" in sys.argv
    
#     if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
#         # Use game ID from command line
#         game_id = sys.argv[1]
#         url = f"https://www.espn.com/nfl/boxscore/_/gameId/{game_id}"
#     else:
#         # Default game ID (you can change this)
#         print("No game ID provided. Using default or enter URL manually.")
#         print("Usage: python count_tables.py <game_id> [--selenium]")
#         print("   OR: python count_tables.py <full_url> [--selenium]")
#         print("   Use --selenium to also test with Selenium for comparison")
#         print("\nEnter game ID or full URL (or press Enter for default): ", end="")
#         user_input = input().strip()
        
#         if user_input:
#             if user_input.startswith("http"):
#                 url = user_input
#             else:
#                 url = f"https://www.espn.com/nfl/boxscore/_/gameId/{user_input}"
#         else:
#             # Default to a recent game
#             url = "https://www.espn.com/nfl/boxscore/_/gameId/401772900"
#             print(f"Using default URL: {url}")
    
#     try:
#         count = count_tables(url, use_selenium=use_selenium)
#         print(f"\n✅ Analysis complete. Found {count} tables using requests method.")
#         print(f"\n💡 TIP: Use --selenium flag to compare with Selenium method")
#     except Exception as e:
#         print(f"\n❌ Error: {str(e)}")
#         import traceback
#         traceback.print_exc()

# if __name__ == "__main__":
#     main()
    


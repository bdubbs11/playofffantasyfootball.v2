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
    
    game_data = {
        "game_id": game_id,
        "teams": {
            team1_name: {"score": team1_score, "players": {}},
            team2_name: {"score": team2_score, "players": {}}
        },
        "winner": winner
    }
    
    # Process tables in pairs
    # Pattern: Seahawks, Falcons, Seahawks, Falcons (alternating by pair, not by score)
    # Tables 2-3: Team1, 4-5: Team2, 6-7: Team1, 8-9: Team2, etc.
    print(f"\n📋 Processing tables (alternating {team1_name}/{team2_name} pattern)")
    
    i = 0
    while i < len(tables) - 1:
        pair_idx = i // 2
        
        # Determine which team based on pair index
        # Even pairs (0, 2, 4...) = Team 1
        # Odd pairs (1, 3, 5...) = Team 2
        if pair_idx % 2 == 0:
            team_name, team_abbr, team_score = team1_name, team1_abbr, team1_score
            opp_abbr, opp_score = team2_abbr, team2_score
        else:
            team_name, team_abbr, team_score = team2_name, team2_abbr, team2_score
            opp_abbr, opp_score = team1_abbr, team1_score
        
        current_table = tables[i]
        next_table = tables[i + 1]
        
        # ESPN structure: current table has headers, next table has stats
        # But actually both might have headers - check both
        headers_current = [th.get_text(strip=True) for th in current_table.find_all("th")]
        headers_next = [th.get_text(strip=True) for th in next_table.find_all("th")]
        
        # Use whichever has actual headers
        if headers_next and any(h for h in headers_next):
            headers = headers_next
        else:
            headers = headers_current
        
        # Debug: show what we're looking at
        if i < 20:  # Only show first 20 tables
            print(f"\n  [DEBUG] Pair {pair_idx} (tables {i}-{i+1}):")
            print(f"          Current headers: {headers_current[:5]}")
            print(f"          Next headers: {headers_next[:5]}")
            print(f"          Using: {headers[:5]}")
        
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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import json
import time
import re

def setup_driver():
    """Initialize Chrome driver with options (only for kicker detail pages)"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

def fetch_page_with_requests(url):
    """Fetch page using requests - this gets ALL 40 tables!"""
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

def parse_stat(stat_text):
    """Convert stat text to number (handles '2/3' format, etc.)"""
    if not stat_text or stat_text == '--':
        return 0
    
    # Handle fractions like "2/3" for FG
    if '/' in stat_text:
        parts = stat_text.split('/')
        return int(parts[0]) if parts[0].isdigit() else 0
    
    # Remove commas and convert to int
    clean = stat_text.replace(',', '').strip()
    try:
        # Handle negative numbers
        return int(clean)
    except ValueError:
        return 0

def extract_player_name(text):
    """Extract clean player name from text like 'Sam Darnold #14'"""
    # Remove jersey number
    name = re.sub(r'\s*#\d+\s*$', '', text).strip()
    # Remove 'team' entries
    if name.lower() == 'team':
        return None
    return name if name else None

def scrape_kicker_details(driver, player_url, current_url):
    """Scrape detailed kicking stats from player page"""
    print(f"      → Fetching kicker details...")
    
    try:
        # Validate URL
        if not player_url.startswith("http"):
            print(f"      ⚠️  Invalid URL: {player_url}")
            return []
        
        driver.get(player_url)
        time.sleep(3)
        
        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")
        
        kick_details = []
        
        # Look for "Recent Games" table with kicking stats
        tables = soup.find_all("table")
        
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            
            # Check if this is the game log table (has columns like Date, OPP, Result, 1-19, 20-29, etc.)
            if "Date" in headers or "OPP" in headers or any("19" in h or "29" in h or "39" in h for h in headers):
                rows = table.find_all("tr")[1:]  # Skip header
                
                # Get the most recent game (first row)
                if rows:
                    first_game = rows[0]
                    cells = first_game.find_all("td")
                    
                    # The columns are: Date, OPP, Result, 1-19, 20-29, 30-39, 40-49, 50+, FG, FG%, LNG, XP, PTS
                    # We need columns 3-7 for distance ranges
                    if len(cells) >= 11:
                        # Parse each distance range
                        ranges = [
                            (cells[3].get_text(strip=True), "1-19"),    # 1-19 yards
                            (cells[4].get_text(strip=True), "20-29"),   # 20-29 yards
                            (cells[5].get_text(strip=True), "30-39"),   # 30-39 yards
                            (cells[6].get_text(strip=True), "40-49"),   # 40-49 yards
                            (cells[7].get_text(strip=True), "50+")      # 50+ yards
                        ]
                        
                        for stat, range_name in ranges:
                            if stat and stat != "0-0" and "-" in stat:
                                # Format is "made-attempts" like "2-2" or "1-2"
                                parts = stat.split("-")
                                made = int(parts[0]) if parts[0].isdigit() else 0
                                attempts = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                                
                                # Add each kick in this range
                                for i in range(attempts):
                                    # Estimate distance based on range
                                    if range_name == "1-19":
                                        distance = 19
                                    elif range_name == "20-29":
                                        distance = 25
                                    elif range_name == "30-39":
                                        distance = 35
                                    elif range_name == "40-49":
                                        distance = 45
                                    elif range_name == "50+":
                                        distance = 52
                                    
                                    # First 'made' kicks are successful
                                    kick_made = i < made
                                    kick_details.append({
                                        "distance": distance,
                                        "made": kick_made,
                                        "range": range_name
                                    })
                        
                        # Try to get exact LNG (longest) for more accuracy
                        lng_text = cells[10].get_text(strip=True) if len(cells) > 10 else ""
                        if lng_text.isdigit():
                            lng = int(lng_text)
                            # Update the longest kick with exact distance
                            if kick_details:
                                # Find the longest successful kick and update it
                                for kick in kick_details:
                                    if kick["made"] and kick["distance"] >= 40:
                                        kick["distance"] = lng
                                        break
                        
                        break
        
        if not kick_details:
            print(f"      ⚠️  No kick details found on player page")
        
        return kick_details
        
    except Exception as e:
        print(f"      ⚠️  Could not fetch kicker details: {str(e)[:100]}")
        return []

def scrape_game_stats(game_id, driver=None):
    """Scrape complete stats for one game"""
    url = f"https://www.espn.com/nfl/boxscore/_/gameId/{game_id}"
    print(f"\n{'='*60}")
    print(f"🏈 Scraping Game ID: {game_id}")
    print(f"{'='*60}")
    
    # Fetch page with requests (gets all 40 tables!)
    print("🌐 Fetching page with requests...")
    html = fetch_page_with_requests(url)
    soup = BeautifulSoup(html, "lxml")
    
    # Get game info from title
    title = soup.title.string if soup.title else ""
    print(f"📰 {title}")
    
    # Parse team names and scores from title
    match = re.search(r'(.+?)\s+(\d+)-(\d+)\s+(.+?)\s+\(', title)
    if match:
        team1_name = match.group(1).strip()
        team1_score = int(match.group(2))
        team2_score = int(match.group(3))
        team2_name = match.group(4).strip()
        winner = team1_name if team1_score > team2_score else team2_name
    else:
        team1_name = "Team 1"
        team2_name = "Team 2"
        team1_score = 0
        team2_score = 0
        winner = "TBD"
    
    print(f"🏆 Winner: {winner}")
    
    # Find all tables
    tables = soup.find_all("table")
    print(f"\n📊 Found {len(tables)} tables total")
    
    if len(tables) < 40:
        print(f"⚠️  WARNING: Expected ~40 tables but only found {len(tables)}")
    
    # Initialize team data
    game_data = {
        "game_id": game_id,
        "teams": {
            team1_name: {
                "score": team1_score,
                "players": {}
            },
            team2_name: {
                "score": team2_score,
                "players": {}
            }
        },
        "winner": winner
    }
    
    # Process tables in pairs (names table + stats table)
    # First 20 tables are team 1, next 20 are team 2
    midpoint = len(tables) // 2
    
    # Process Team 1 (first half of tables)
    print(f"\n{'='*60}")
    print(f"Processing {team1_name}")
    print(f"{'='*60}")
    process_team_tables(tables[:midpoint], game_data["teams"][team1_name]["players"], driver, url)
    
    # Process Team 2 (second half of tables)
    print(f"\n{'='*60}")
    print(f"Processing {team2_name}")
    print(f"{'='*60}")
    process_team_tables(tables[midpoint:], game_data["teams"][team2_name]["players"], driver, url)
    
    # Convert players dict to list
    for team_name in game_data["teams"]:
        game_data["teams"][team_name]["players"] = list(game_data["teams"][team_name]["players"].values())
    
    return game_data

def process_team_tables(tables, players_dict, driver, box_score_url):
    """Process tables for one team"""
    i = 0
    while i < len(tables) - 1:
        current_table = tables[i]
        next_table = tables[i + 1]
        
        # Get headers from next table to identify stat type
        headers = [th.get_text(strip=True) for th in next_table.find_all("th")]
        
        # Determine stat category
        stat_category = None
        if "C/ATT" in headers and "INT" in headers:
            stat_category = "passing"
        elif "CAR" in headers and "YDS" in headers and "REC" not in headers:
            stat_category = "rushing"
        elif "REC" in headers and "YDS" in headers:
            stat_category = "receiving"
        elif "FUM" in headers and "LOST" in headers:
            stat_category = "fumbles"
        elif "INT" in headers and "YDS" in headers and "TD" in headers and "CAR" not in headers:
            stat_category = "interceptions"
        elif any("TOT" in h or "SOLO" in h or "SACKS" in h for h in headers):
            stat_category = "defense"
        elif "FG" in headers or "XP" in headers:
            stat_category = "kicking"
        
        if not stat_category:
            i += 1
            continue
        
        print(f"\n  📋 {stat_category.upper()}")
        
        # Extract player names from current table
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
                    # Check for player link (for kickers)
                    link = cells[0].find("a")
                    if link and link.get("href"):
                        href = link["href"]
                        # Make sure it's a full URL
                        if href.startswith("http"):
                            player_links[name] = href
                        elif href.startswith("/"):
                            player_links[name] = "https://www.espn.com" + href
                        else:
                            player_links[name] = "https://www.espn.com/" + href
        
        # Extract stats from next table
        stat_rows = next_table.find_all("tr")[1:]  # Skip header
        
        # Match names with stats
        for idx, row in enumerate(stat_rows):
            if idx >= len(player_names):
                break
                
            player_name = player_names[idx]
            cells = row.find_all("td")
            
            if not cells:
                continue
            
            # Initialize player if not exists
            if player_name not in players_dict:
                players_dict[player_name] = {
                    "name": player_name,
                    "position": get_position_from_category(stat_category),
                    "stats": {}
                }
            
            # Parse stats based on category
            stats = parse_stats_by_category(stat_category, cells)
            
            # Special handling for kickers - get detailed kick distances
            if stat_category == "kicking" and player_name in player_links and driver:
                kick_details = scrape_kicker_details(driver, player_links[player_name], box_score_url)
                if kick_details:
                    stats["field_goals"] = kick_details
                    print(f"      ✓ {player_name}: {len(kick_details)} FG attempts")
            
            # Merge stats into player
            players_dict[player_name]["stats"].update(stats)
            
            # Update position if we have better info
            if stat_category == "passing":
                players_dict[player_name]["position"] = "QB"
            elif stat_category == "kicking":
                players_dict[player_name]["position"] = "K"
            
            # Print summary
            if stats:
                stats_str = ", ".join([f"{k}: {v}" for k, v in stats.items() if k != "field_goals"])
                if stats_str:
                    print(f"    ✓ {player_name}: {stats_str}")
        
        # Skip both tables (name + stats)
        i += 2

def parse_stats_by_category(category, cells):
    """Parse stats based on category"""
    stats = {}
    
    if category == "passing":
        # Headers: C/ATT, YDS, AVG, TD, INT, SACKS, QBR, RTG
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
        # Headers: CAR, YDS, AVG, TD, LONG
        if len(cells) >= 4:
            stats["rushing_attempts"] = parse_stat(cells[0].get_text())
            stats["rushing_yards"] = parse_stat(cells[1].get_text())
            stats["rushing_tds"] = parse_stat(cells[3].get_text())
    
    elif category == "receiving":
        # Headers: REC, YDS, AVG, TD, LONG, TGTS
        if len(cells) >= 4:
            stats["receptions"] = parse_stat(cells[0].get_text())
            stats["receiving_yards"] = parse_stat(cells[1].get_text())
            stats["receiving_tds"] = parse_stat(cells[3].get_text())
    
    elif category == "fumbles":
        # Headers: FUM, LOST, REC
        if len(cells) >= 2:
            stats["fumbles"] = parse_stat(cells[0].get_text())
            stats["fumbles_lost"] = parse_stat(cells[1].get_text())
    
    elif category == "interceptions":
        # Headers: INT, YDS, TD (for defensive interceptions)
        if len(cells) >= 1:
            stats["interceptions"] = parse_stat(cells[0].get_text())
            if len(cells) >= 2:
                stats["int_return_yards"] = parse_stat(cells[1].get_text())
            if len(cells) >= 3:
                stats["int_return_tds"] = parse_stat(cells[2].get_text())
    
    elif category == "kicking":
        # Headers: FG, FG%, LONG, XP, PTS
        for i, cell in enumerate(cells):
            text = cell.get_text().strip()
            if '/' in text and i < 2:  # FG made/att
                parts = text.split('/')
                stats["fg_made"] = parse_stat(parts[0])
                stats["fg_att"] = parse_stat(parts[1])
            elif i == len(cells) - 2:  # Usually XP is second to last
                stats["xp_made"] = parse_stat(text)
    
    elif category == "defense":
        # Headers: TOT, SOLO, SACKS, etc.
        if len(cells) >= 1:
            stats["tackles"] = parse_stat(cells[0].get_text())
        if len(cells) >= 3:
            stats["sacks"] = parse_stat(cells[2].get_text())
    
    return stats

def get_position_from_category(category):
    """Map category to position"""
    position_map = {
        "passing": "QB",
        "rushing": "RB",
        "receiving": "WR",
        "kicking": "K",
        "defense": "DEF",
        "interceptions": "DEF",
        "fumbles": "FLEX"
    }
    return position_map.get(category, "FLEX")

def scrape_multiple_games(game_ids):
    """Scrape multiple games"""
    # Only initialize driver once for kicker details
    driver = setup_driver()
    all_games = []
    
    try:
        for i, game_id in enumerate(game_ids, 1):
            print(f"\n{'#'*60}")
            print(f"GAME {i} of {len(game_ids)}")
            print(f"{'#'*60}")
            
            game_data = scrape_game_stats(game_id, driver)
            all_games.append(game_data)
            
            print(f"\n✅ Completed game {game_id}")
            
            # Wait between requests
            if i < len(game_ids):
                print("⏸️  Waiting 3 seconds...")
                time.sleep(3)
        
        return all_games
        
    finally:
        driver.quit()
        print("\n🔒 Browser closed")

def save_results(games_data, filename="fantasy_stats.json"):
    """Save scraped data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(games_data, f, indent=2)
    print(f"\n💾 Saved to {filename}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🏈 NFL FANTASY FOOTBALL STATS SCRAPER")
    print("="*60)
    
    # TEST MODE: Single game
    print("\n📋 TEST MODE: Scraping single game")
    test_game_id = "401772900"
    
    # Initialize driver for kicker details only
    driver = setup_driver()
    try:
        game_data = scrape_game_stats(test_game_id, driver)
        save_results([game_data], "test_game.json")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        for team_name, team_info in game_data["teams"].items():
            print(f"\n{team_name} ({team_info['score']} points)")
            print(f"  Players scraped: {len(team_info['players'])}")
            
            # Count by position
            positions = {}
            for player in team_info['players']:
                pos = player['position']
                positions[pos] = positions.get(pos, 0) + 1
            
            for pos, count in sorted(positions.items()):
                print(f"    {pos}: {count} players")
        
        print(f"\n🏆 Winner: {game_data['winner']}")
        
    finally:
        driver.quit()
    
    print("\n" + "="*60)
    print("✅ SCRAPING COMPLETE!")
    print("="*60)
    
    # UNCOMMENT TO SCRAPE MULTIPLE GAMES:
    # game_ids = ["401772900", "401772901", "401772902"]
    # all_games = scrape_multiple_games(game_ids)
    # save_results(all_games, "weekly_stats.json")
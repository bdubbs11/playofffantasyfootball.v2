from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import subprocess
import os
import glob
import sys

# Path to your existing game scraper script
GAME_SCRAPER_SCRIPT = "scrape_game.py"

def get_box_score_links(week: int, year: int, season_type: int):
    url = f"https://www.espn.com/nfl/scoreboard/_/week/{week}/year/{year}/seasontype/{season_type}"

    # Initialize browser with headless options for GitHub Actions compatibility
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    
    # Step 1: Wait for scoreboard to fully load
    print("Waiting for scoreboard to load...")
    try:
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "section.Scoreboard, section[class*='Scoreboard'], div[class*='Scoreboard']")
        ))
    except:
        # Fallback: just wait for any game links to appear
        print("   Scoreboard section not found, waiting for game links...")
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "a[href*='boxscore']")
        ))
    
    # Scroll to top to ensure we're viewing the current week's games
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    # Step 2: Wait for JavaScript to finish loading and stabilize
    # Check that the link count stabilizes (doesn't keep growing)
    print("   Waiting for JavaScript to finish loading and stabilize...")
    stable_count = 0
    previous_count = 0
    max_wait_attempts = 15
    stable_links = None
    
    for attempt in range(max_wait_attempts):
        time.sleep(1)
        # Find all box score links on the page
        box_score_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='boxscore'][href*='gameId']")
        
        # Filter for visible links
        visible_links = []
        for link in box_score_links:
            if link.is_displayed():
                try:
                    location = link.location
                    size = link.size
                    if (location['x'] >= 0 and location['y'] >= 0 and 
                        size['width'] > 0 and size['height'] > 0):
                        visible_links.append(link)
                except:
                    visible_links.append(link)
        
        current_count = len(visible_links)
        
        if current_count == previous_count:
            stable_count += 1
            if stable_count >= 3:  # Count is stable for 3 seconds
                print(f"   ✓ Link count stabilized at {current_count} visible links")
                stable_links = visible_links  # Save the stable links
                break
        else:
            stable_count = 0
            if attempt < 5:  # Only print first few changes to avoid spam
                print(f"   Link count changed: {previous_count} → {current_count}, waiting...")
        
        previous_count = current_count
    
    # Step 3: Use the stable links we found, or do a final search if we didn't capture them
    if stable_links is None:
        print("   Final search for box score links...")
        box_score_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='boxscore'][href*='gameId']")
        visible_links = []
        for link in box_score_links:
            if link.is_displayed():
                try:
                    location = link.location
                    size = link.size
                    if (location['x'] >= 0 and location['y'] >= 0 and 
                        size['width'] > 0 and size['height'] > 0):
                        visible_links.append(link)
                except:
                    visible_links.append(link)
        stable_links = visible_links
    
    print(f"   Using {len(stable_links)} visible box score links")
    
    # Step 4: Collect hrefs and deduplicate (no limit - capture all visible games)
    links = []
    seen = set()
    
    for link in stable_links:
        href = link.get_attribute("href")
        if href and href not in seen:
            # Only include valid boxscore URLs
            if "boxscore" in href.lower() and "gameId" in href:
                links.append(href)
                seen.add(href)
                print(f"   Found game {len(links)}: {href.split('/')[-1]}")
    
    # Step 5: Sort links for consistency
    links.sort()
    
    driver.quit()
    return links

def get_expected_game_count(season_type: int, week: int) -> int:
    """Get expected number of games based on season type and week"""
    if season_type == 3:  # Playoffs
        # Playoffs: Wild Card (6), Divisional (4), Conference (2), Super Bowl (1)
        # Note: On ESPN, week 4 = Pro Bowl (skip), week 5 = Super Bowl
        # But for our system, Super Bowl is logically week 4
        if week == 1:
            return 6  # Wild Card
        elif week == 2:
            return 4  # Divisional
        elif week == 3:
            return 2  # Conference Championships
        elif week == 5:
            return 1  # Super Bowl (week 5 on ESPN, but logically week 4 for us)
        elif week == 4:
            return 0  # Pro Bowl - skip this week
        else:
            return 1
    else:  # Regular season
        # Regular season typically has 16 games per week (some weeks have 15 or 17)
        # Week 18 can have more games
        if week == 18:
            return 16  # Most teams play
        else:
            return 16  # Standard week
    
def validate_game_count(links: list, season_type: int, week: int):
    """Sanity check: compare collected links with expected number"""
    expected = get_expected_game_count(season_type, week)
    actual = len(links)
    
    print(f"\n📊 Game Count Validation:")
    print(f"   Expected: ~{expected} games")
    print(f"   Found: {actual} games")
    
    if actual > expected + 2:  # Allow some variance
        print(f"   ⚠️  WARNING: Found {actual} games, expected ~{expected}")
        print(f"   This might indicate duplicate or incorrect links were captured.")
        return False
    elif actual < expected - 2:
        print(f"   ⚠️  WARNING: Found {actual} games, expected ~{expected}")
        print(f"   Some games might be missing.")
        return False
    else:
        print(f"   ✅ Game count looks reasonable")
        return True

def get_playoff_week_name(week: int):
    """Return a human-readable name for playoff weeks"""
    if week == 1:
        return "WildCard"
    elif week == 2:
        return "Divisional"
    elif week == 3:
        return "Conference"
    elif week == 5:
        return "SuperBowl"  # Week 5 on ESPN is Super Bowl (logically week 4 for us)
    else:
        return f"Week_{week}"

def get_week_folder(year: int, week: int, season_type: int):
    """Return path to folder for this week"""
    base_folder = "scraped_data"
    if season_type == 3:  # Playoffs
        # Special case: Super Bowl is week 5 on ESPN but should be labeled as Week_4_SuperBowl
        if week == 5:
            # Week 5 on ESPN = Super Bowl, but folder should be Week_4_SuperBowl
            folder = os.path.join(base_folder, str(year), "Week_4_SuperBowl")
        else:
            week_name = get_playoff_week_name(week)
            folder = os.path.join(base_folder, str(year), f"Week_{week}_{week_name}")
    else:  # Regular season
        folder = os.path.join(base_folder, str(year), f"Week_{week}_Regular")
    
    os.makedirs(folder, exist_ok=True)
    return folder

def process_all_games_in_folder(folder_path: str, week: int, season_type: int):
    """Process all game JSON files in a folder using process_game_data.py"""
    # Map week number to week name for process_game_data
    week_name_map = {
        1: "Wildcard",
        2: "Divisional", 
        3: "Conference",
        5: "SuperBowl"  # Week 5 on ESPN = Super Bowl
    }
    
    if week not in week_name_map:
        print(f"⚠️  No week name mapping for week {week}")
        return
    
    week_name = week_name_map[week]
    
    # Find all JSON game files in the folder
    game_files = glob.glob(os.path.join(folder_path, "game_*.json"))
    
    if not game_files:
        print(f"⚠️  No game files found in {folder_path}")
        return
    
    print(f"\n🔄 Processing {len(game_files)} game files...")
    
    # Process each game file
    for game_file in sorted(game_files):
        print(f"\n{'='*60}")
        print(f"Processing: {os.path.basename(game_file)}")
        result = subprocess.run(
            ["python", "process_game_data.py", game_file, week_name],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully processed {os.path.basename(game_file)}")
        else:
            print(f"❌ Error processing {os.path.basename(game_file)}")
    
    print(f"\n✅ Finished processing all games for {week_name}")

def scrape_all_games(links, year: int, week: int, season_type: int):
    """Scrape all games and save to week-specific folder"""
    folder = get_week_folder(year, week, season_type)
    print(f"Saving scraped data to folder: {folder}")
    
    for link in links:
        print(f"Scraping game: {link}")
        # Call your existing game scraper script for this link
        # Pass the folder path as second argument
        subprocess.run(["python", GAME_SCRAPER_SCRIPT, link, folder])
    
    # After scraping, automatically process all games
    print(f"\n{'='*60}")
    print("📊 Starting automatic game processing...")
    process_all_games_in_folder(folder, week, season_type)

if __name__ == "__main__":
    # Allow command line arguments: week, year, season_type
    # Usage: python scrape_week.py [week] [year] [season_type]
    if len(sys.argv) >= 2:
        week = int(sys.argv[1])
    else:
        week = 1  # Default
    
    if len(sys.argv) >= 3:
        year = int(sys.argv[2])
    else:
        year = 2025  # Default
    
    if len(sys.argv) >= 4:
        season_type = int(sys.argv[3])
    else:
        season_type = 3  # Default (playoffs)
    
    # Skip week 4 (Pro Bowl)
    if week == 4 and season_type == 3:
        print("⚠️  Week 4 is Pro Bowl - skipping. Use week 5 for Super Bowl.")
        exit(0)
    
    links = get_box_score_links(week, year, season_type)
    print(f"Found {len(links)} games.")
    
    # Sanity check
    validate_game_count(links, season_type, week)
    
    # Display all links found
    if links:
        print(f"\n📋 Box Score Links:")
        for i, link in enumerate(links, 1):
            print(f"   {i}. {link}")
    
    scrape_all_games(links, year, week, season_type)

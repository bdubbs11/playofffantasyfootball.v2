from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import subprocess

# Path to your existing game scraper script
GAME_SCRAPER_SCRIPT = "scrape_game.py"

def get_box_score_links(week: int, year: int, season_type: int):
    url = f"https://www.espn.com/nfl/scoreboard/_/week/{week}/year/{year}/seasontype/{season_type}"

    # Initialize browser
    driver = webdriver.Chrome()  # or .Firefox()
    driver.get(url)

    wait = WebDriverWait(driver, 10)
    # Wait for "Box Score" links to appear
    box_score_links = wait.until(EC.presence_of_all_elements_located(
        (By.LINK_TEXT, "Box Score")
    ))

    # Collect hrefs
    links = [link.get_attribute("href") for link in box_score_links]

    driver.quit()
    return links

def scrape_all_games(links):
    for link in links:
        print(f"Scraping game: {link}")
        # Call your existing game scraper script for this link
        # Assumes your script accepts the URL as a command line argument
        subprocess.run(["python", GAME_SCRAPER_SCRIPT, link])

if __name__ == "__main__":
    week = 1
    year = 2024
    season_type = 3
    links = get_box_score_links(week, year, season_type)
    print(f"Found {len(links)} games.")
    scrape_all_games(links)

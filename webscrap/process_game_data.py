# webscrap/process_game_data.py
import json
import os
import sys
import math
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize Supabase client
# Using VITE_ prefixed variables from your .env file
supabase_url = os.getenv("VITE_SUPABASE_URL")
supabase_key = os.getenv("VITE_SUPABASE_ANON_KEY")

# Note: For production, consider using SUPABASE_SERVICE_ROLE_KEY instead of anon key
# The anon key will work but has RLS restrictions. Service role key bypasses RLS.

if not supabase_url or not supabase_key:
    print("Error: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY must be set in .env file")
    print(f"Looking for .env at: {env_path}")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

# Week to array index mapping
# 0 = Wildcard, 1 = Divisional, 2 = Conference, 3 = Super Bowl
WEEK_INDEX_MAP = {
    "Wildcard": 0,
    "WildCard": 0,
    "Divisional": 1,
    "Conference": 2,
    "Super Bowl": 3,
    "SuperBowl": 3,
}

# Special player name mappings (same as JS version)
SPECIAL_PLAYER_NAME_MAPPINGS = {
    'jsn': 'jaxon smith-njigba',
    'cmc': 'christian mccaffrey',
}

def normalize_player_name(name):
    """Normalize player name for matching (same logic as JS)"""
    if not name:
        return ''
    
    lower_name = name.lower().strip()
    
    # Check special cases first
    if lower_name in SPECIAL_PLAYER_NAME_MAPPINGS:
        return SPECIAL_PLAYER_NAME_MAPPINGS[lower_name]
    
    # Normalize: lowercase, replace hyphens with spaces, normalize multiple spaces
    normalized = lower_name.replace('-', ' ').replace('  ', ' ').strip()
    return normalized

def parse_xp_string(xp_str):
    """Parse XP string like '3/3' and return made attempts"""
    if isinstance(xp_str, (int, float)):
        return int(xp_str)
    if isinstance(xp_str, str) and '/' in xp_str:
        return int(xp_str.split('/')[0])
    return 0

def calculate_fantasy_points(stats, position):
    """
    Calculate fantasy points from stats.
    - Floor all non-reception points to whole numbers
    - Then add reception points (0.5 per reception)
    - Final result: whole number or whole number + 0.5
    
    Scoring:
    - Passing: 1 pt per 25 yards, 4 pts per TD, -2 per INT
    - Rushing: 1 pt per 10 yards, 6 pts per TD
    - Receiving: 0.5 pt per reception, 1 pt per 10 yards, 6 pts per TD
    - Kicking: Distance-based FG (0-39: 3, 40-49: 4, 50-59: 5, 60-69: 6, 70+: 7)
                Missed FG <40: -2, Missed FG >=40: -1
                Made XP: +1, Missed XP: -2
    """
    points = 0.0
    
    # Passing stats (floor these)
    if 'passing' in stats:
        p = stats['passing']
        points += math.floor(p.get('passing_yards', 0) / 25.0)
        points += (p.get('passing_tds', 0) * 4)  # Already whole
        points += (p.get('interceptions', 0) * -2)  # Already whole
    
    # Rushing stats (floor these)
    if 'rushing' in stats:
        r = stats['rushing']
        points += math.floor(r.get('rushing_yards', 0) / 10.0)
        points += (r.get('rushing_tds', 0) * 6)  # Already whole
    
    # Receiving stats - yards and TDs (floor these), receptions added separately
    reception_points = 0.0
    if 'receiving' in stats:
        rec = stats['receiving']
        points += math.floor(rec.get('receiving_yards', 0) / 10.0)
        points += (rec.get('receiving_tds', 0) * 6)  # Already whole
        # Receptions added separately (not floored)
        reception_points = rec.get('receptions', 0) * 0.5
    
    # Kicking stats (all whole numbers)
    if 'kicking' in stats:
        k = stats['kicking']
        
        # Process field goals from array (distance-based scoring)
        field_goals = k.get('field_goals', [])
        if field_goals:
            for fg in field_goals:
                distance = fg.get('distance', 0)
                made = fg.get('made', False)
                
                if made:
                    # Made FGs: 0-39: 3, 40-49: 4, 50-59: 5, 60-69: 6, 70+: 7
                    if distance <= 39:
                        points += 3
                    elif distance <= 49:
                        points += 4
                    elif distance <= 59:
                        points += 5
                    elif distance <= 69:
                        points += 6
                    else:  # 70+
                        points += 7
                else:
                    # Missed/Blocked FGs
                    if distance < 40:
                        points += -2  # Under 39yds: -2
                    else:
                        points += -1  # Over 40yds: -1
        
        # Process extra points
        xp_str = k.get('xp_made', 0)
        if isinstance(xp_str, str) and '/' in xp_str:
            parts = xp_str.split('/')
            xp_made = int(parts[0])
            xp_att = int(parts[1])
            points += xp_made * 1  # Made XP: +1 each
            points += (xp_att - xp_made) * -2  # Missed XP: -2 each
        elif isinstance(xp_str, (int, float)):
            points += int(xp_str) * 1
    
    # Add reception points last (not floored, always 0.5 increments)
    points += reception_points
    
    return points  # Result: whole number or whole + 0.5

def calculate_defense_points(def_stats):
    """
    Calculate defense fantasy points.
    Standard scoring - customize as needed:
    - Points allowed: 0 pts = 10, 1-6 = 7, 7-13 = 4, 14-20 = 1, 21-34 = 0, 35+ = -2
    - Sacks: 1 pt each
    - Interceptions: 2 pts each
    - Fumble recoveries: 2 pts each
    - Defensive TDs: 6 pts each
    """
    points = 0.0
    
    points_allowed = def_stats.get('points_allowed', 0)
    if points_allowed == 0:
        points += 10
    elif points_allowed <= 6:
        points += 7
    elif points_allowed <= 13:
        points += 4
    elif points_allowed <= 20:
        points += 1
    elif points_allowed <= 34:
        points += 0
    else:
        points += -2
    
    points += def_stats.get('sacks', 0) * 1
    points += def_stats.get('interceptions', 0) * 2
    points += def_stats.get('fumbles_recovered', 0) * 2
    points += def_stats.get('defensive_tds', 0) * 6
    
    return round(points, 2)

def determine_winner(score, teams):
    """Determine which team won based on score"""
    if len(teams) != 2:
        return None
    
    team1, team2 = teams[0], teams[1]
    score1 = score.get(team1, 0)
    score2 = score.get(team2, 0)
    
    if score1 > score2:
        return team1
    elif score2 > score1:
        return team2
    return None  # Tie

def process_game_file(game_file_path, week_name):
    """
    Process a single game JSON file and update database
    """
    print(f"\n{'='*60}")
    print(f"📄 Processing: {game_file_path}")
    print(f"📅 Week: {week_name}")
    print(f"{'='*60}")
    
    # Read game JSON
    if not os.path.exists(game_file_path):
        print(f"❌ Error: File not found: {game_file_path}")
        return False
    
    with open(game_file_path, 'r') as f:
        game_data = json.load(f)
    
    # Get week index (0=Wildcard, 1=Divisional, 2=Conference, 3=Super Bowl)
    week_index = WEEK_INDEX_MAP.get(week_name, None)
    if week_index is None:
        print(f"❌ Error: Invalid week name '{week_name}'. Must be one of: {list(WEEK_INDEX_MAP.keys())}")
        return False
    
    print(f"📊 Week Index: {week_index}")
    
    # Get all players from database
    try:
        response = supabase.table('players').select('id, name, points, won, team, position').execute()
        all_players = response.data
        print(f"✅ Loaded {len(all_players)} players from database")
    except Exception as e:
        print(f"❌ Error loading players from database: {e}")
        return False
    
    # Create normalized name map for quick lookup
    player_map = {}
    for player in all_players:
        normalized = normalize_player_name(player['name'])
        if normalized:
            if normalized not in player_map:
                player_map[normalized] = []
            player_map[normalized].append(player)
    
    # Determine winner
    teams = list(game_data['score'].keys())
    winner = determine_winner(game_data['score'], teams)
    print(f"🏆 Winner: {winner}")
    print(f"📊 Score: {game_data['score']}")
    
    updated_count = 0
    
    # Process each player in the game
    print(f"\n📈 Processing {len(game_data['players'])} players...")
    for player_name, player_data in game_data['players'].items():
        normalized_name = normalize_player_name(player_name)
        
        # Try to find matching player in database
        matched_players = player_map.get(normalized_name, [])
        
        if not matched_players:
            # Try fuzzy matching (exact match with different case/spacing)
            for db_player in all_players:
                if normalize_player_name(db_player['name']) == normalized_name:
                    matched_players = [db_player]
                    break
        
        if not matched_players:
            print(f"⚠️  Player not found in database: {player_name} (normalized: {normalized_name})")
            continue
        
        # Use first match (or you could add logic to match by team/position if multiple)
        matched_player = matched_players[0]
        
        # Calculate fantasy points
        stats = player_data.get('stats', {})
        points = calculate_fantasy_points(stats, player_data.get('position', ''))
        
        # Check if player's team won
        player_team = player_data.get('team', '')
        won = player_team == winner if winner else None
        
        # Get current points and won arrays
        current_points = matched_player.get('points', [None, None, None, None])
        current_won = matched_player.get('won', [None, None, None, None])
        
        # Ensure arrays have 4 elements
        while len(current_points) < 4:
            current_points.append(None)
        while len(current_won) < 4:
            current_won.append(None)
        
        # Update the specific week index
        current_points[week_index] = float(points) if points else None
        current_won[week_index] = won
        
        # Update player in database
        try:
            supabase.table('players').update({
                'points': current_points,
                'won': current_won
            }).eq('id', matched_player['id']).execute()
            
            won_str = "✅" if won else "❌" if won is False else "❓"
            print(f"✅ Updated {player_name}: {points} pts {won_str} (DB: {matched_player['name']})")
            updated_count += 1
        except Exception as e:
            print(f"❌ Error updating {player_name}: {e}")
    
    # Handle players in database who are on teams in this game but didn't play
    print(f"\n🔍 Checking for players who didn't play...")
    teams_in_game = [normalize_player_name(team) for team in teams]
    played_player_names = {normalize_player_name(pname) for pname in game_data['players'].keys()}
    
    for db_player in all_players:
        # Skip defense (handled separately)
        if db_player.get('position') == 'DEF':
            continue
        
        db_team_normalized = normalize_player_name(db_player.get('team', ''))
        
        # Check if this player is on one of the teams in the game
        if db_team_normalized in teams_in_game:
            # Check if player was already processed (played in the game)
            db_name_normalized = normalize_player_name(db_player['name'])
            
            if db_name_normalized not in played_player_names:
                # Player is on a team in the game but didn't play - set to 0 points
                current_points = db_player.get('points', [None, None, None, None])
                current_won = db_player.get('won', [None, None, None, None])
                
                while len(current_points) < 4:
                    current_points.append(None)
                while len(current_won) < 4:
                    current_won.append(None)
                
                # Set to 0 points for this week
                current_points[week_index] = 0.0
                # Won status based on team result
                player_team = db_player.get('team', '')
                won = player_team == winner if winner else None
                current_won[week_index] = won
                
                try:
                    supabase.table('players').update({
                        'points': current_points,
                        'won': current_won
                    }).eq('id', db_player['id']).execute()
                    
                    won_str = "✅" if won else "❌" if won is False else "❓"
                    print(f"⚠️  Set {db_player['name']} ({db_player.get('team', '')}) to 0 pts {won_str} (didn't play)")
                    updated_count += 1
                except Exception as e:
                    print(f"❌ Error updating {db_player['name']}: {e}")
    
    # Process defense stats
    print(f"\n🛡️  Processing defense stats...")
    for team_name, defense_stats in game_data.get('defense', {}).items():
        normalized_team = normalize_player_name(team_name)
        
        # Search for defense player with this team
        found = False
        for db_player in all_players:
            if db_player.get('position') == 'DEF':
                db_team_normalized = normalize_player_name(db_player.get('team', ''))
                if db_team_normalized == normalized_team:
                    # Calculate defense points
                    def_points = calculate_defense_points(defense_stats)
                    won = team_name == winner if winner else None
                    
                    current_points = db_player.get('points', [None, None, None, None])
                    current_won = db_player.get('won', [None, None, None, None])
                    
                    while len(current_points) < 4:
                        current_points.append(None)
                    while len(current_won) < 4:
                        current_won.append(None)
                    
                    current_points[week_index] = float(def_points) if def_points else None
                    current_won[week_index] = won
                    
                    try:
                        supabase.table('players').update({
                            'points': current_points,
                            'won': current_won
                        }).eq('id', db_player['id']).execute()
                        
                        won_str = "✅" if won else "❌" if won is False else "❓"
                        print(f"✅ Updated {team_name} Defense: {def_points} pts {won_str}")
                        updated_count += 1
                        found = True
                        break
                    except Exception as e:
                        print(f"❌ Error updating {team_name} Defense: {e}")
        
        if not found:
            print(f"⚠️  Defense not found in database: {team_name}")
    
    print(f"\n{'='*60}")
    print(f"✅ Processing complete! Updated {updated_count} players")
    print(f"{'='*60}\n")
    return True

def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python process_game_data.py <game_json_file> <week_name>")
        print("\nWeek names: Wildcard, Divisional, Conference, Super Bowl")
        print("\nExample:")
        print("  python process_game_data.py scraped_data/2025/Week_17_Regular/game_401772825.json Wildcard")
        sys.exit(1)
    
    game_file = sys.argv[1]
    week_name = sys.argv[2]
    
    success = process_game_file(game_file, week_name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()


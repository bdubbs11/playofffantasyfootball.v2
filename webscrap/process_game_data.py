# webscrap/process_game_data.py
import json
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from scoring_helpers import (
    calculate_fantasy_points,
    calculate_defense_points,
    calculate_sb_winner_points,
    calculate_team_totals_and_ranks,
    get_multiplier,
    is_bye_team,
    normalize_team_name,
    WEEK_INDEX_MAP
)

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

# Note: WEEK_INDEX_MAP is imported from scoring_helpers

# Canonical name mappings - same as JavaScript
# Maps any variant to the canonical database name
CANONICAL_NAME_MAPPINGS = {
    # Suffix variations
    'brian thomas': 'brian thomas jr',
    'travis etienne': 'travis etienne jr',
    'luther burden iii': 'luther burden',
    'luther burden': 'luther burden',
    
    # Dot/period variations
    'a.j. brown': 'aj brown',
    'aj brown': 'aj brown',
    'c.j. stroud': 'cj stroud',
    'cj stroud': 'cj stroud',
    
    # Existing mappings
    'jsn': 'jaxon smith-njigba',
    'cmc': 'christian mccaffrey',
    'andres borregales': 'andy borregales',
}

def create_matchable_name(name):
    """Create matchable name (strips suffixes and dots for comparison)"""
    if not name:
        return ''
    
    matchable = name.lower().strip()
    
    # Strip periods from initials
    matchable = matchable.replace('.', '')
    
    # Strip common suffixes for matching
    matchable = re.sub(r'\s+(jr|sr|iii|ii|iv|v)$', '', matchable, flags=re.IGNORECASE)
    
    # Normalize spaces and hyphens
    matchable = matchable.replace('-', ' ').replace('  ', ' ').strip()
    
    return matchable

def normalize_player_name(name):
    """Normalize player name for matching and get canonical name"""
    if not name:
        return ''
    
    lower_name = name.lower().strip()
    
    # Check canonical mappings first
    if lower_name in CANONICAL_NAME_MAPPINGS:
        return CANONICAL_NAME_MAPPINGS[lower_name]
    
    # Create matchable version and check if it maps to canonical
    matchable = create_matchable_name(name)
    if matchable in CANONICAL_NAME_MAPPINGS:
        return CANONICAL_NAME_MAPPINGS[matchable]
    
    # For storage, use matchable version
    return matchable

# Note: calculate_fantasy_points and calculate_defense_points are imported from scoring_helpers

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
    
    # Get all sbWinner player IDs (for special handling)
    try:
        fantasy_teams_for_sb = supabase.table('fantasy_teams').select('players').execute()
        sb_winner_ids = set()
        for team in (fantasy_teams_for_sb.data or []):
            players_json = team['players']
            if isinstance(players_json, str):
                players_json = json.loads(players_json)
                if isinstance(players_json, str):
                    players_json = json.loads(players_json)
            sb_winner_id = players_json.get('sbWinner')
            if sb_winner_id:
                sb_winner_ids.add(sb_winner_id)
    except Exception as e:
        print(f"⚠️  Error fetching sbWinner IDs: {e}")
        sb_winner_ids = set()
    
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
        
        # Calculate BASE fantasy points (before multiplier)
        stats = player_data.get('stats', {})
        base_points = calculate_fantasy_points(stats, player_data.get('position', ''))
        
        # Get current points and won arrays for multiplier calculation
        current_points = matched_player.get('points', [None, None, None, None])
        current_won = matched_player.get('won', [None, None, None, None])
        
        # Ensure arrays have 4 elements
        while len(current_points) < 4:
            current_points.append(None)
        while len(current_won) < 4:
            current_won.append(None)
        
        # Get multiplier based on team (bye team or not)
        player_team = player_data.get('team', '')
        multiplier = get_multiplier(player_team, week_index, current_points, current_won)
        
        # Apply multiplier to base points
        final_points = base_points * multiplier
        
        # Check if player's team won
        won = player_team == winner if winner else None
        
        # Update the specific week index
        current_points[week_index] = float(final_points) if final_points else None
        current_won[week_index] = won
        
        # Update player in database
        try:
            supabase.table('players').update({
                'points': current_points,
                'won': current_won
            }).eq('id', matched_player['id']).execute()
            
            won_str = "✅" if won else "❌" if won is False else "❓"
            print(f"✅ Updated {player_name}: {base_points} (base) × {multiplier} = {final_points} pts {won_str} (DB: {matched_player['name']})")
            updated_count += 1
        except Exception as e:
            print(f"❌ Error updating {player_name}: {e}")
    
    # Handle players in database who are on teams in this game but didn't play
    print(f"\n🔍 Checking for players who didn't play...")
    teams_in_game = [normalize_player_name(team) for team in teams]
    played_player_names = {normalize_player_name(pname) for pname in game_data['players'].keys()}
    
    for db_player in all_players:
        # Skip defense (handled separately), BUT handle sbWinner here
        if db_player.get('position') == 'DEF':
            # Check if this DEF player is an sbWinner
            if db_player['id'] in sb_winner_ids:
                # sbWinner: handle separately (update won status, but only points for Super Bowl)
                db_team_normalized = normalize_player_name(db_player.get('team', ''))
                
                # Check if this player's team is in the game
                if db_team_normalized in teams_in_game:
                    current_points = db_player.get('points', [None, None, None, None])
                    current_won = db_player.get('won', [None, None, None, None])
                    
                    while len(current_points) < 4:
                        current_points.append(None)
                    while len(current_won) < 4:
                        current_won.append(None)
                    
                    # Won status based on team result (for blackout)
                    player_team = db_player.get('team', '')
                    won = player_team == winner if winner else None
                    
                    # Only set points if it's Super Bowl (week_index == 3)
                    # Otherwise leave as None (don't score until Super Bowl)
                    if week_index == 3:
                        # Super Bowl: calculate SB Winner points ONLY if this player's team won
                        if won:  # Only give points if their team won
                            sb_points = calculate_sb_winner_points(winner) if winner else None
                            current_points[week_index] = float(sb_points) if sb_points else None
                        else:
                            # Team lost - set to 0 points
                            current_points[week_index] = 0.0
                    
                    current_won[week_index] = won
                    
                    try:
                        supabase.table('players').update({
                            'points': current_points,
                            'won': current_won
                        }).eq('id', db_player['id']).execute()
                        
                        won_str = "✅" if won else "❌" if won is False else "❓"
                        if week_index == 3:
                            print(f"✅ Updated sbWinner {db_player['name']} ({db_player.get('team', '')}): {current_points[week_index]} pts {won_str}")
                        else:
                            print(f"⚠️  Updated sbWinner {db_player['name']} ({db_player.get('team', '')}): won={won_str} (no points until Super Bowl)")
                        updated_count += 1
                    except Exception as e:
                        print(f"❌ Error updating sbWinner {db_player['name']}: {e}")
            # If it's DEF but not sbWinner, skip (handled in defense section)
            continue
        
        db_team_normalized = normalize_player_name(db_player.get('team', ''))
        
        # Check if this player is on one of the teams in the game
        if db_team_normalized in teams_in_game:
            # Check if player was already processed (played in the game)
            db_name_normalized = normalize_player_name(db_player['name'])
            
            if db_name_normalized not in played_player_names:
                # Check if this is an sbWinner player for Super Bowl
                if db_player['id'] in sb_winner_ids and week_index == 3:
                    # sbWinner in Super Bowl: give points if team won, 0 if lost
                    current_points = db_player.get('points', [None, None, None, None])
                    current_won = db_player.get('won', [None, None, None, None])
                    
                    while len(current_points) < 4:
                        current_points.append(None)
                    while len(current_won) < 4:
                        current_won.append(None)
                    
                    # Won status based on team result
                    player_team = db_player.get('team', '')
                    won = player_team == winner if winner else None
                    
                    # Super Bowl: calculate SB Winner points ONLY if this player's team won
                    if won:  # Only give points if their team won
                        sb_points = calculate_sb_winner_points(winner) if winner else None
                        current_points[week_index] = float(sb_points) if sb_points else None
                    else:
                        # Team lost - set to 0 points
                        current_points[week_index] = 0.0
                    
                    current_won[week_index] = won
                    
                    try:
                        supabase.table('players').update({
                            'points': current_points,
                            'won': current_won
                        }).eq('id', db_player['id']).execute()
                        
                        won_str = "✅" if won else "❌" if won is False else "❓"
                        print(f"✅ Updated sbWinner {db_player['name']} ({db_player.get('team', '')}): {current_points[week_index]} pts {won_str}")
                        updated_count += 1
                    except Exception as e:
                        print(f"❌ Error updating sbWinner {db_player['name']}: {e}")
                else:
                    # Regular player who didn't play - set to 0 points
                    current_points = db_player.get('points', [None, None, None, None])
                    current_won = db_player.get('won', [None, None, None, None])
                    
                    while len(current_points) < 4:
                        current_points.append(None)
                    while len(current_won) < 4:
                        current_won.append(None)
                    
                    # Get multiplier for 0 points (multiplier still applies even if 0)
                    player_team = db_player.get('team', '')
                    multiplier = get_multiplier(player_team, week_index, current_points, current_won)
                    
                    # Set to 0 points for this week (0 × multiplier = 0, but we track it)
                    current_points[week_index] = 0.0
                    # Won status based on team result
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
                # Skip sbWinner players (they're handled separately)
                if db_player['id'] in sb_winner_ids:
                    continue
                
                db_team_normalized = normalize_player_name(db_player.get('team', ''))
                if db_team_normalized == normalized_team:
                    # Calculate BASE defense points (before multiplier)
                    base_def_points = calculate_defense_points(defense_stats)
                    
                    current_points = db_player.get('points', [None, None, None, None])
                    current_won = db_player.get('won', [None, None, None, None])
                    
                    while len(current_points) < 4:
                        current_points.append(None)
                    while len(current_won) < 4:
                        current_won.append(None)
                    
                    # Get multiplier and apply it
                    multiplier = get_multiplier(team_name, week_index, current_points, current_won)
                    final_def_points = base_def_points * multiplier
                    
                    won = team_name == winner if winner else None
                    
                    current_points[week_index] = float(final_def_points) if final_def_points else None
                    current_won[week_index] = won
                    
                    try:
                        supabase.table('players').update({
                            'points': current_points,
                            'won': current_won
                        }).eq('id', db_player['id']).execute()
                        
                        won_str = "✅" if won else "❌" if won is False else "❓"
                        print(f"✅ Updated {team_name} Defense: {base_def_points} (base) × {multiplier} = {final_def_points} pts {won_str}")
                        updated_count += 1
                        found = True
                        break
                    except Exception as e:
                        print(f"❌ Error updating {team_name} Defense: {e}")
        
        if not found:
            print(f"⚠️  Defense not found in database: {team_name}")
    
    # After all player points are updated, calculate and update fantasy team totals and ranks
    calculate_team_totals_and_ranks(supabase)
    
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


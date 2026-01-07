# webscrap/scoring_helpers.py
"""
Fantasy scoring helper functions for playoff fantasy football.
Handles multiplier logic, point calculations, and team totals.
"""
import json
import math
from supabase import Client

# Team seeds - #1 seeds had a bye in Wildcard round
TEAM_SEEDS = {
  'AFC': {
    "Broncos": 1,
    "Patriots": 2,
    "Jaguars": 3,
    "Steelers": 4,
    "Texans": 5,
    "Bills": 6,
    "Chargers": 7
  },
  'NFC': {
    "Seahawks": 1,
    "Bears": 2,
    "Eagles": 3,
    "Panthers": 4,
    "Rams": 5,
    "49ers": 6,
    "Packers": 7
  }
};

# Week to array index mapping
WEEK_INDEX_MAP = {
    "Wildcard": 0,
    "WildCard": 0,
    "Divisional": 1,
    "Conference": 2,
    "Super Bowl": 3,
    "SuperBowl": 3,
}

def normalize_team_name(team_name):
    """Normalize team name for comparison"""
    if not team_name:
        return ''
    return team_name.lower().strip()

def is_bye_team(team_name, player_points=None, player_won=None):
    """
    Determine if a team had a bye (is a #1 seed).
    
    Uses team seeds file to check if team is a #1 seed.
    
    Args:
        team_name: Team name
        player_points: Points array (unused, kept for API consistency)
        player_won: Won array (unused, kept for API consistency)
    
    Returns:
        bool: True if #1 seed (had bye), False otherwise
    """
    team_normalized = normalize_team_name(team_name)
    
    # Check team seeds file
    for conference in TEAM_SEEDS.values():
        for team, seed in conference.items():
            if normalize_team_name(team) == team_normalized:
                return seed == 1
    
    return False

def get_multiplier(team_name, round_index, player_points=None, player_won=None):
    """
    Get multiplier for a player/team in a given round.
    
    #1 seeds (bye teams): multiplier = round_index
    - Divisional (index 1): 1×
    - Conference (index 2): 2×
    - Super Bowl (index 3): 3×
    
    Non-#1 seeds: multiplier = round_index + 1
    - Wildcard (index 0): 1×
    - Divisional (index 1): 2×
    - Conference (index 2): 3×
    - Super Bowl (index 3): 4×
    
    Args:
        team_name: Team name
        round_index: 0=Wildcard, 1=Divisional, 2=Conference, 3=SuperBowl
        player_points: Points array (optional, for checking if bye team)
        player_won: Won array (optional, for checking if bye team)
    
    Returns:
        int: Multiplier (1, 2, 3, or 4)
    """
    if is_bye_team(team_name, player_points, player_won):
        # #1 seeds: multiplier = round_index (1, 2, 3)
        return round_index
    else:
        # Non-#1 seeds: multiplier = round_index + 1 (1, 2, 3, 4)
        return round_index + 1

def parse_xp_string(xp_str):
    """Parse XP string like '3/3' and return made attempts"""
    if isinstance(xp_str, (int, float)):
        return int(xp_str)
    if isinstance(xp_str, str) and '/' in xp_str:
        return int(xp_str.split('/')[0])
    return 0

def calculate_fantasy_points(stats, position):
    """
    Calculate BASE fantasy points from stats (before multiplier).
    - Floor all non-reception points to whole numbers
    - Then add reception points (0.5 per reception)
    - Final result: whole number or whole number + 0.5
    
    Scoring:
    - Passing: 1 pt per 25 yards, 4 pts per TD, -2 per INT
    - Rushing: 1 pt per 10 yards, 6 pts per TD
    - Receiving: 0.5 pt per reception, 1 pt per 10 yards, 6 pts per TD
    - Fumbles: -2 pts per fumble lost (QB), -3 pts per fumble lost (non-QB)
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
                    else:
                        points += 6
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
    
    # Fumbles lost penalty: -2 points per fumble lost (QB), -3 points per fumble lost (non-QB)
    if 'fumbles' in stats:
        f = stats['fumbles']
        # Handle both dict format {"LOST": 1, "REC": 0} and direct key format
        if isinstance(f, dict):
            fumbles_lost = f.get('LOST', 0) or f.get('fumbles_lost', 0)
        else:
            fumbles_lost = f if isinstance(f, (int, float)) else 0
        # QB fumbles: -2 points, non-QB fumbles: -3 points
        fumble_penalty = -2 if position == "QB" else -3
        points += fumbles_lost * fumble_penalty
    
    # Add reception points last (not floored, always 0.5 increments)
    points += reception_points
    
    return points  # Result: whole number or whole + 0.5

def calculate_defense_points(def_stats):
    """
    Calculate BASE defense fantasy points (before multiplier).
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

def calculate_sb_winner_points(winner_team_name):
    """
    Calculate SB Winner points based on whether winner was a #1 seed.
    
    - #1 seed winner: 42 points (multiplier 3×, base 14)
    - Non-#1 seed winner: 56 points (multiplier 4×, base 14)
    
    Args:
        winner_team_name: Name of the Super Bowl winner
    
    Returns:
        float: Points (42.0 or 56.0)
    """
    is_bye = is_bye_team(winner_team_name)
    
    if is_bye:
        return 42.0  # #1 seed: 3× multiplier, 14 base
    else:
        return 56.0  # Non-#1 seed: 4× multiplier, 14 base

def calculate_team_totals_and_ranks(supabase: Client):
    """
    Calculate and update fantasy team totals and ranks.
    Recalculates from scratch for all teams.
    
    Args:
        supabase: Supabase client instance
    
    Returns:
        int: Number of teams updated
    """
    print(f"\n📊 Calculating fantasy team totals and ranks...")
    updated_count = 0
    
    try:
        # Fetch all fantasy teams
        fantasy_teams_result = supabase.table('fantasy_teams').select('id, players').execute()
        fantasy_teams = fantasy_teams_result.data if fantasy_teams_result.data else []
        
        if not fantasy_teams:
            print("⚠️  No fantasy teams found")
            return 0
        
        # Fetch all players' updated points (get fresh data after updates)
        all_players_result = supabase.table('players').select('id, points').execute()
        players_points_map = {}
        for p in (all_players_result.data or []):
            points_array = p.get('points', [None, None, None, None])
            # Ensure array has 4 elements
            while len(points_array) < 4:
                points_array.append(None)
            players_points_map[p['id']] = points_array
        
        # Calculate total points for each fantasy team
        team_totals = []
        for team in fantasy_teams:
            try:
                players_json = team['players']
                # Handle double-encoded JSON (may need to parse twice)
                if isinstance(players_json, str):
                    players_json = json.loads(players_json)
                    if isinstance(players_json, str):
                        players_json = json.loads(players_json)
                
                # Extract all player IDs from the team
                player_ids = [
                    players_json.get('qb1'), players_json.get('qb2'), players_json.get('wr'),
                    players_json.get('rb'), players_json.get('te'), players_json.get('flex1'),
                    players_json.get('flex2'), players_json.get('flex3'), players_json.get('flex4'),
                    players_json.get('kicker'), players_json.get('def'), players_json.get('sbWinner'),
                ]
                
                # Sum all points from all rounds for all players on this team
                total_from_scratch = 0.0
                for player_id in player_ids:
                    if player_id and player_id in players_points_map:
                        points_array = players_points_map[player_id]
                        for p in points_array:
                            if p is not None:
                                total_from_scratch += float(p)
                
                team_totals.append({
                    'id': team['id'],
                    'total_points': total_from_scratch
                })
                
            except Exception as e:
                print(f"❌ Error calculating totals for team {team.get('id', 'unknown')}: {e}")
        
        # Sort teams by total_points (descending) to determine ranks
        team_totals.sort(key=lambda x: x['total_points'], reverse=True)
        
        # Update each team's total_points and rank
        for rank, team_data in enumerate(team_totals, start=1):
            try:
                supabase.table('fantasy_teams').update({
                    'total_points': team_data['total_points'],
                    'rank': rank
                }).eq('id', team_data['id']).execute()
                
                print(f"✅ Updated team {team_data['id']}: {team_data['total_points']} total points (Rank #{rank})")
                updated_count += 1
            except Exception as e:
                print(f"❌ Error updating team {team_data['id']}: {e}")
    
    except Exception as e:
        print(f"❌ Error calculating team totals and ranks: {e}")
    
    return updated_count


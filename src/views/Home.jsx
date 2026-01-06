import React, { useState, useEffect } from 'react';
import TeamRow from '../components/TeamRow';
import { supabase } from '../lib/supabase';

function Home(){
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentRound, setCurrentRound] = useState({ name: 'Wildcard', week: 1 });

  useEffect(() => {
    fetchTeams();
  }, []);

  const fetchTeams = async () => {
    try {
      // 1. Fetch all fantasy teams
      const { data: fantasyTeams, error: teamsError } = await supabase
        .from('fantasy_teams')
        .select('*');

      if (teamsError) throw teamsError;

      if (!fantasyTeams || fantasyTeams.length === 0) {
        setTeams([]);
        setLoading(false);
        return;
      }

      // 2. Extract all unique player IDs from all teams
      const allPlayerIds = new Set();
      fantasyTeams.forEach(team => {
        try {
          // Parse the double-encoded JSON string (may need to parse twice)
          let playersJson = team.players;
          if (typeof playersJson === 'string') {
            playersJson = JSON.parse(playersJson);
            // If it's still a string, parse again
            if (typeof playersJson === 'string') {
              playersJson = JSON.parse(playersJson);
            }
          }
          const playerIds = Object.values(playersJson);
          playerIds.forEach(id => {
            if (id) allPlayerIds.add(id);
          });
        } catch (e) {
          console.error('Error parsing players JSON:', e, team.players);
        }
      });

      // 3. Fetch all players by IDs (include points and won fields)
      const { data: players, error: playersError } = await supabase
        .from('players')
        .select('id, name, points, won')
        .in('id', Array.from(allPlayerIds));

      if (playersError) throw playersError;

      // 4. Determine current round by checking players' points arrays
      let highestRoundIndex = -1;
      players?.forEach(player => {
        const pointsArray = player.points || [];
        // Check from highest round (Super Bowl = 3) down to lowest (Wildcard = 0)
        for (let i = 3; i >= 0; i--) {
          if (pointsArray[i] !== null && pointsArray[i] !== undefined) {
            if (i > highestRoundIndex) {
              highestRoundIndex = i;
            }
            break; // Found the highest round for this player, move to next
          }
        }
      });

      // Map round index to round name and week number
      const roundMap = [
        { name: 'Wildcard', week: 1 },
        { name: 'Divisional', week: 2 },
        { name: 'Conference', week: 3 },
        { name: 'Super Bowl', week: 4 }
      ];

      // Default to Wildcard if no data found, otherwise use the highest round found
      const round = highestRoundIndex >= 0 
        ? roundMap[highestRoundIndex] 
        : roundMap[0];
      
      setCurrentRound(round);

      // 5. Create a map of player ID to full player object (including points)
      const playerMap = {};
      players?.forEach(player => {
        playerMap[player.id] = player;
      });

      // 6. Transform fantasy teams to match TeamRow format
      const transformedTeams = fantasyTeams.map(team => {
        try {
          // Parse the double-encoded JSON (may need to parse twice)
          let playersJson = team.players;
          if (typeof playersJson === 'string') {
            playersJson = JSON.parse(playersJson);
            // If it's still a string, parse again
            if (typeof playersJson === 'string') {
              playersJson = JSON.parse(playersJson);
            }
          }
          
          // Helper to get player data (name, points, and won status for each round)
          const getPlayerData = (playerId) => {
            const player = playerMap[playerId];
            if (!player) {
              return {
                name: 'Unknown',
                points: {
                  wildcard: 0,
                  divisional: 0,
                  conference: 0,
                  superBowl: 0
                },
                won: {
                  wildcard: null,
                  divisional: null,
                  conference: null,
                  superBowl: null
                },
                isEliminated: false
              };
            }
            
            // Parse points array: [wildcard, divisional, conference, superBowl]
            const pointsArray = player.points || [];
            // Parse won array: [wildcard, divisional, conference, superBowl]
            const wonArray = player.won || [];
            
            // Check if player is eliminated (any round is false)
            const isEliminated = wonArray.some(won => won === false);
            
            return {
              name: player.name || 'Unknown',
              points: {
                wildcard: pointsArray[0] !== null && pointsArray[0] !== undefined ? parseFloat(pointsArray[0]) : null,
                divisional: pointsArray[1] !== null && pointsArray[1] !== undefined ? parseFloat(pointsArray[1]) : null,
                conference: pointsArray[2] !== null && pointsArray[2] !== undefined ? parseFloat(pointsArray[2]) : null,
                superBowl: pointsArray[3] !== null && pointsArray[3] !== undefined ? parseFloat(pointsArray[3]) : null
              },
              won: {
                wildcard: wonArray[0] !== undefined ? wonArray[0] : null,
                divisional: wonArray[1] !== undefined ? wonArray[1] : null,
                conference: wonArray[2] !== undefined ? wonArray[2] : null,
                superBowl: wonArray[3] !== undefined ? wonArray[3] : null
              },
              isEliminated
            };
          };

          return {
            ownerName: team.owner_name || '',
            teamName: team.team_name || '',
            totalPoints: parseFloat(team.total_points) || 0,
            qb1: getPlayerData(playersJson.qb1),
            qb2: getPlayerData(playersJson.qb2),
            wr: getPlayerData(playersJson.wr),
            rb: getPlayerData(playersJson.rb),
            te: getPlayerData(playersJson.te),
            flex1: getPlayerData(playersJson.flex1),
            flex2: getPlayerData(playersJson.flex2),
            flex3: getPlayerData(playersJson.flex3),
            flex4: getPlayerData(playersJson.flex4),
            k: getPlayerData(playersJson.kicker),
            def: getPlayerData(playersJson.def),
            sbWinner: getPlayerData(playersJson.sbWinner),
          };
        } catch (e) {
          console.error('Error transforming team:', e, team);
          return null;
        }
      }).filter(team => team !== null);

      // 7. Sort teams by total points (descending) and assign ranks
      transformedTeams.sort((a, b) => b.totalPoints - a.totalPoints);
      transformedTeams.forEach((team, index) => {
        team.rank = index + 1;
      });

      setTeams(transformedTeams);
    } catch (error) {
      console.error('Error fetching teams:', error);
      setTeams([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-screen">
      <div className="container grid grid-cols-1 md:grid-cols-16 mx-auto "> 
        <div className="col-start-2 col-span-14"> 

          <div className="flex flex-col items-center justify-center mt-10 mb-6">
            <h1 className="text-4xl font-bold mb-2">Postseason Fantasy Football</h1>
            <p className="text-lg">{currentRound.name} Round : Week {currentRound.week}</p>
          </div>

        <div className="overflow-x-auto ">
          <div className="min-w-max">
            {/* Header Row */}
            <div 
              className="grid gap-2 mb-2 px-2 text-slate-300"
              style={{ gridTemplateColumns: '200px repeat(12, minmax(100px, 1fr))' }}
            >
              <div className="text-center">Team Info</div>
              <div className="text-center">QB1</div>
              <div className="text-center">QB2</div>
              <div className="text-center">WR</div>
              <div className="text-center">RB</div>
              <div className="text-center">TE</div>
              <div className="text-center">Flex 1</div>
              <div className="text-center">Flex 2</div>
              <div className="text-center">Flex 3</div>
              <div className="text-center">Flex 4</div>
              <div className="text-center">K</div>
              <div className="text-center">DEF</div>
              <div className="text-center">SB Winner</div>
              
            </div>
            {/* Team Rows */}
            {loading ? (
              <div className="text-white text-center py-8">Loading teams...</div>
            ) : teams.length > 0 ? (
              teams.map((team) => (
                <TeamRow key={team.rank} team={team} />
              ))
            ) : (
              <div className="text-white text-center py-8">No teams found. Be the first to submit a team!</div>
            )}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

export default Home;
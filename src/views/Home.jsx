import React, { useState, useEffect } from 'react';
import TeamRow from '../components/TeamRow';
import { supabase } from '../lib/supabase';

// Helper function to generate image paths
const getImagePath = (name, capitalize = false) => {
  if (!name) return 'images/placeholder.png';
  if (capitalize) {
    // Capitalize first letter of each word, then remove spaces
    const capitalized = name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join('');
    return `images/${capitalized}.png`;
  }
  // Lowercase (remove spaces)
  return `images/${name.replace(/\s+/g, '')}.png`;
};

// Helper component for images with fallback: tries lowercase, then capitalized, then placeholder
const ImageWithFallback = ({ name, alt, className }) => {
  const [imgSrc, setImgSrc] = useState(getImagePath(name, false)); // Start with lowercase
  const [attempt, setAttempt] = useState(0); // 0 = lowercase, 1 = capitalized, 2 = placeholder

  const handleError = () => {
    if (attempt === 0) {
      // Try capitalized version
      setImgSrc(getImagePath(name, true));
      setAttempt(1);
    } else if (attempt === 1) {
      // Fall back to placeholder
      setImgSrc('images/placeholder.png');
      setAttempt(2);
    }
  };

  return <img src={imgSrc} alt={alt} className={className} onError={handleError} />;
};

function Home(){
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentRound, setCurrentRound] = useState({ name: 'Wildcard', week: 1 });
  const [timeUntilReveal, setTimeUntilReveal] = useState(null);
  const [canViewTeams, setCanViewTeams] = useState(false);

  // Set reveal date: Friday, January 9th, 2026 at 8pm EST
  const REVEAL_DATE = new Date('2026-01-09T18:30:00-05:00'); // EST timezone

  useEffect(() => {
    checkRevealTime();
    const interval = setInterval(checkRevealTime, 1000); // Update every second
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (canViewTeams) {
      fetchTeams();
    }
  }, [canViewTeams]);

  const checkRevealTime = () => {
    const now = new Date();
    const timeDiff = REVEAL_DATE - now;
    
    if (timeDiff <= 0) {
      setCanViewTeams(true);
      setTimeUntilReveal(null);
    } else {
      setCanViewTeams(false);
      // Calculate time remaining
      const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);
      setTimeUntilReveal({ days, hours, minutes, seconds });
    }
  };

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

  // Helper function to capitalize names for display
  const capitalizeName = (name) => {
    if (!name) return '';
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  // Helper component for mobile player cards
  const TeamPlayerCard = ({ player, label }) => {
    const getPlayerBoxClassName = (player) => {
      const baseClasses = "rounded p-2 text-center";
      if (player.isEliminated) {
        return `${baseClasses} bg-black`;
      }
      return `${baseClasses} bg-slate-700`;
    };

    const totalPoints = [player.points.wildcard, player.points.divisional, player.points.conference, player.points.superBowl]
      .filter(p => p !== null && p !== undefined)
      .reduce((sum, p) => sum + p, 0);

    return (
      <div className={getPlayerBoxClassName(player)}>
        <div className="text-xs text-slate-400 mb-1">{label}</div>
        <div className="flex justify-center mb-2">
          <ImageWithFallback 
            name={player.name} 
            alt={capitalizeName(player.name)} 
            className="w-20 h-16 object-contain" 
          />
        </div>
        <div className="text-sm text-white font-semibold mb-2">{capitalizeName(player.name)}</div>
        <div className="space-y-1">
          <div className="text-xs text-slate-300">
            Wildcard: {player.points.wildcard !== null && player.points.wildcard !== undefined ? player.points.wildcard : '-'}
          </div>
          <div className="text-xs text-slate-300">
            Divisional: {player.points.divisional !== null && player.points.divisional !== undefined ? player.points.divisional : '-'}
          </div>
          <div className="text-xs text-slate-300">
            Conference: {player.points.conference !== null && player.points.conference !== undefined ? player.points.conference : '-'}
          </div>
          <div className="text-xs text-slate-300">
            Super Bowl: {player.points.superBowl !== null && player.points.superBowl !== undefined ? player.points.superBowl : '-'}
          </div>
          <div className="text-xs text-emerald-400 font-semibold mt-1 pt-1 border-t border-slate-600">
            Total: {totalPoints}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col flex-1 min-h-screen">
      <div className="container mx-auto px-4 w-full"> 
        <div className="flex flex-col items-center justify-center mt-10 mb-6">
          <h1 className="text-4xl font-bold mb-2 text-white">Postseason Fantasy Football</h1>
          {canViewTeams && (
            <p className="text-lg text-white">{currentRound.name} Round : Week {currentRound.week}</p>
          )}
        </div>

        {!canViewTeams ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-white">
            <h2 className="text-3xl font-bold mb-6 text-center">Teams will be revealed on</h2>
            <p className="text-xl mb-8 text-center">Friday, January 9th, 2026 at 6:30 PM EST</p>
            {timeUntilReveal && (
              <div className="grid grid-cols-4 gap-4 text-center max-w-md w-full">
                <div className="bg-slate-700 rounded-lg p-4">
                  <div className="text-4xl font-bold text-sky-400">{timeUntilReveal.days}</div>
                  <div className="text-sm text-slate-300 mt-2">Days</div>
                </div>
                <div className="bg-slate-700 rounded-lg p-4">
                  <div className="text-4xl font-bold text-sky-400">{timeUntilReveal.hours}</div>
                  <div className="text-sm text-slate-300 mt-2">Hours</div>
                </div>
                <div className="bg-slate-700 rounded-lg p-4">
                  <div className="text-4xl font-bold text-sky-400">{timeUntilReveal.minutes}</div>
                  <div className="text-sm text-slate-300 mt-2">Minutes</div>
                </div>
                <div className="bg-slate-700 rounded-lg p-4">
                  <div className="text-4xl font-bold text-sky-400">{timeUntilReveal.seconds}</div>
                  <div className="text-sm text-slate-300 mt-2">Seconds</div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Desktop: Horizontal scroll table */}
            <div className="hidden md:block overflow-x-auto">
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

            {/* Mobile: Card-based layout */}
            <div className="md:hidden space-y-4">
              {loading ? (
                <div className="text-white text-center py-8">Loading teams...</div>
              ) : teams.length > 0 ? (
                teams.map((team) => (
                  <div key={team.rank} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                    <div className="text-center mb-4">
                      <div className="text-2xl font-bold text-white">#{team.rank}</div>
                      <div className="text-lg text-white font-semibold">{capitalizeName(team.teamName)}</div>
                      <div className="text-sm text-slate-400">{capitalizeName(team.ownerName)}</div>
                      <div className="text-xl font-bold text-emerald-400 mt-2">{team.totalPoints} pts</div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      {/* Mobile: Show key players in a 2-column grid */}
                      <TeamPlayerCard player={team.qb1} label="QB1" />
                      <TeamPlayerCard player={team.qb2} label="QB2" />
                      <TeamPlayerCard player={team.wr} label="WR" />
                      <TeamPlayerCard player={team.rb} label="RB" />
                      <TeamPlayerCard player={team.te} label="TE" />
                      <TeamPlayerCard player={team.flex1} label="Flex 1" />
                      <TeamPlayerCard player={team.flex2} label="Flex 2" />
                      <TeamPlayerCard player={team.flex3} label="Flex 3" />
                      <TeamPlayerCard player={team.flex4} label="Flex 4" />
                      <TeamPlayerCard player={team.k} label="K" />
                      <TeamPlayerCard player={team.def} label="DEF" />
                      <TeamPlayerCard player={team.sbWinner} label="SB Winner" />
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-white text-center py-8">No teams found. Be the first to submit a team!</div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Home;
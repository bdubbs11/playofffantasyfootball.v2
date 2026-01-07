import React, {useState} from 'react';
import { teamSeeds } from '../components/teamSeeds';
import { validateTeam } from '../components/TeamValidator';
import { useNavigate } from 'react-router-dom';

// imports for supabase and submit team
import { createClient } from '@supabase/supabase-js';

const supabaseURL = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseURL, supabaseAnonKey);

// Canonical name mappings - maps any variant to the canonical database name
// Use ESPN's name format as canonical (what actually appears in scraped data)
const CANONICAL_NAME_MAPPINGS = {
  // Suffix variations - map to canonical (database stores canonical)
  'brian thomas': 'brian thomas jr',
  'travis etienne': 'travis etienne jr',
  'luther burden iii': 'luther burden',  // Strip III for storage
  'luther burden': 'luther burden',      // Also handle without suffix
  
  // Dot/period variations
  'a.j. brown': 'aj brown',
  'aj brown': 'aj brown',
  'c.j. stroud': 'cj stroud',
  'cj stroud': 'cj stroud',
  
  // Existing mappings
  'jsn': 'jaxon smith-njigba',
  'cmc': 'christian mccaffrey',
  'andres borregales': 'andy borregales',
};

// Create matchable name for comparison (strips suffixes and dots for matching)
const createMatchableName = (name) => {
  if (!name) return '';
  
  let matchable = name.toLowerCase().trim();
  
  // Strip periods from initials (A.J. → AJ, C.J. → CJ)
  // But preserve single letters that aren't followed by periods (RJ stays RJ)
  matchable = matchable.replace(/\./g, '');
  
  // Strip common suffixes for matching (Jr, Sr, III, II, IV, etc.)
  // Use word boundaries to avoid matching parts of names
  matchable = matchable.replace(/\s+(jr|sr|iii|ii|iv|v)$/i, '');
  
  // Normalize spaces and hyphens
  matchable = matchable.replace(/-/g, ' ').replace(/\s+/g, ' ').trim();
  
  return matchable;
};

// Normalize player name for comparison and get canonical name
const normalizePlayerName = (name) => {
  if (!name) return '';
  
  const lowerName = name.toLowerCase().trim();
  
  // Check canonical mappings first (before any processing)
  if (CANONICAL_NAME_MAPPINGS[lowerName]) {
    return CANONICAL_NAME_MAPPINGS[lowerName];
  }
  
  // Create matchable version and check if matchable version maps to canonical
  const matchable = createMatchableName(name);
  if (CANONICAL_NAME_MAPPINGS[matchable]) {
    return CANONICAL_NAME_MAPPINGS[matchable];
  }
  
  // For storage, use the matchable version (strips dots/suffixes for consistency)
  // This ensures "A.J. Brown" and "AJ Brown" both become "aj brown"
  return matchable;
};

// Calculate Levenshtein distance for fuzzy matching
const calculateLevenshteinDistance = (str1, str2) => {
  const matrix = [];
  const len1 = str1.length;
  const len2 = str2.length;

  for (let i = 0; i <= len2; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= len1; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= len2; i++) {
    for (let j = 1; j <= len1; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }

  return matrix[len2][len1];
};

// Enhanced fuzzy matching that uses matchable names
const findBestFuzzyMatch = (searchName, existingPlayers, maxDistance = 2) => {
  const normalizedSearch = normalizePlayerName(searchName);
  const matchableSearch = createMatchableName(searchName);
  
  let bestMatch = null;
  let bestDistance = Infinity;

  for (const player of existingPlayers) {
    const normalizedPlayer = normalizePlayerName(player.name);
    const matchablePlayer = createMatchableName(player.name);
    
    // Exact match on normalized (canonical) names
    if (normalizedSearch === normalizedPlayer || matchableSearch === matchablePlayer) {
      return { match: player, distance: 0 };
    }
    
    // Fuzzy match on matchable versions
    const distance = calculateLevenshteinDistance(matchableSearch, matchablePlayer);
    
    if (distance < bestDistance && distance <= maxDistance) {
      bestDistance = distance;
      bestMatch = player;
    }
  }

  return bestMatch ? { match: bestMatch, distance: bestDistance } : null;
};

// i will have password protection to submit your team to the database. and then i will have
// you enter yoru email so i can confrim you only created one team. very loose managment.


function EnterTeam(){
  const navigate = useNavigate();
  const initialFormData = {
    yourName: '',
    teamName: '',
    qb1: '',
    'qb1-team': '',
    qb2: '',
    'qb2-team': '',
    wr: '',
    'wr-team': '',
    rb: '',
    'rb-team': '',
    te: '',
    'te-team': '',
    flex1: '',
    'flex1-truepos': '',
    'flex1-team': '',
    flex2: '',
    'flex2-truepos': '',
    'flex2-team': '',
    flex3: '',
    'flex3-truepos': '',
    'flex3-team': '',
    flex4: '',
    'flex4-truepos': '',
    'flex4-team': '',
    def: '',
    'def-team': '',
    kicker: '',
    'kicker-team': '',
    sbWinner: '',
    'sbWinner-team': '',
  };
  const [formData, setFormData] = useState(initialFormData);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalIssues, setModalIssues] = useState([]);
  const [canSubmit, setCanSubmit] = useState(false);
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (name, value) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };


  const handleSubmit = (e) => {
    e.preventDefault();
    const validationResult = validateTeam(formData);
    setModalIssues(validationResult.issues);
    setCanSubmit(validationResult.isValid);
    setModalOpen(true);
    // Reset password and email when modal opens
    setPassword('');
    setEmail('');
    setSubmitError('');
    setIsSubmitting(false);
  }

  const submitTeam = async () => {
    // Prevent double submission
    if (isSubmitting) {
      return;
    }
    
    setIsSubmitting(true);
    setSubmitError('');
    
    // Validate password
    const correctPassword = import.meta.env.VITE_PLAYOFF_PASSWORD;
    if (password !== correctPassword) {
      setSubmitError('Incorrect password');
      setIsSubmitting(false);
      return;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setSubmitError('Please enter a valid email address');
      setIsSubmitting(false);
      return;
    }

    // Normalize email: lowercase and trim whitespace
    const normalizedEmail = email.trim().toLowerCase();

    try {
      // Check if email is in invited_emails table (case-insensitive comparison)
      // Query all invited emails and find match case-insensitively
      const { data: allInvitedEmails, error: invitedError } = await supabase
        .from('invited_emails')
        .select('id, used, email');

      if (invitedError) {
        throw invitedError;
      }

      // Find matching email case-insensitively
      const invitedEmail = allInvitedEmails?.find(
        inv => inv.email?.toLowerCase().trim() === normalizedEmail
      );

      if (!invitedEmail) {
        setSubmitError('This email is not on the invite list. Please use an invited email address.');
        setIsSubmitting(false);
        return;
      }

      if (invitedEmail.used) {
        setSubmitError('This email has already been used to create a team. Only one team per email is allowed.');
        setIsSubmitting(false);
        return;
      }

      // Also check if email already exists in fantasy_teams (extra safety check)
      const { data: allExistingTeams, error: checkError } = await supabase
        .from('fantasy_teams')
        .select('id, email');

      if (checkError) {
        throw checkError;
      }

      const existingTeam = allExistingTeams?.find(
        team => team.email?.toLowerCase().trim() === normalizedEmail
      );

      if (existingTeam) {
        setSubmitError('This email has already been used to create a team. Only one team per email is allowed.');
        setIsSubmitting(false);
        return;
      }

      // 1️⃣ Build the list of players from formData
      // For defense and SB winner, only use the team select value (dropdown)
      const playersList = [
        { name: formData.qb1.toLowerCase().trim(), team: formData['qb1-team'], position: "QB" },
        { name: formData.qb2.toLowerCase().trim(), team: formData['qb2-team'], position: "QB" },
        { name: formData.wr.toLowerCase().trim(), team: formData['wr-team'], position: "WR" },
        { name: formData.rb.toLowerCase().trim(), team: formData['rb-team'], position: "RB" },
        { name: formData.te.toLowerCase().trim(), team: formData['te-team'], position: "TE" },
        { name: formData.flex1.toLowerCase().trim(), team: formData['flex1-team'], position: formData['flex1-truepos'] },
        { name: formData.flex2.toLowerCase().trim(), team: formData['flex2-team'], position : formData['flex2-truepos'] },
        { name: formData.flex3.toLowerCase().trim(), team: formData['flex3-team'], position: formData['flex3-truepos'] },
        { name: formData.flex4.toLowerCase().trim(), team: formData['flex4-team'], position: formData['flex4-truepos'] },
        { name: formData['def-team'].toLowerCase().trim(), team: formData['def-team'], position: "DEF" },
        { name: formData.kicker.toLowerCase().trim(), team: formData['kicker-team'], position: "K" },
        { name: formData['sbWinner-team'].toLowerCase().trim(), team: formData['sbWinner-team'], position: "SB Winner" },
      ].filter(p => p.name && p.team && p.position);

      // 2️⃣ Get existing players
      const { data: existingPlayers, error: existingError } = await supabase
        .from('players')
        .select('id, name');

      if (existingError) throw existingError;

      // Create a map: normalized name -> player object (for exact matches)
      // Note: player names in DB are already lowercase, but we normalize for comparison
      const normalizedPlayersMap = new Map();
      existingPlayers.forEach(p => {
        const normalized = normalizePlayerName(p.name);
        if (normalized && !normalizedPlayersMap.has(normalized)) {
          normalizedPlayersMap.set(normalized, p);
        }
      });

      // 3️⃣ Insert only new players (with fuzzy matching)
      const newPlayers = [];
      const playerNameMapping = new Map(); // Maps form input name to database player
      
      playersList.forEach(p => {
        const normalized = normalizePlayerName(p.name);
        
        // Check for exact normalized match first
        if (normalizedPlayersMap.has(normalized)) {
          playerNameMapping.set(p.name, normalizedPlayersMap.get(normalized));
          return;
        }
        
        // Try fuzzy matching
        const fuzzyResult = findBestFuzzyMatch(p.name, existingPlayers, 2);
        if (fuzzyResult && fuzzyResult.distance <= 2) {
          // Found a close match, use the existing player
          playerNameMapping.set(p.name, fuzzyResult.match);
          // Also add to normalized map for future lookups
          normalizedPlayersMap.set(normalized, fuzzyResult.match);
          return;
        }
        
        // No match found, add to new players
        // Use canonical name from mapping (normalized) to ensure consistency
        const canonicalName = normalizePlayerName(p.name);
        newPlayers.push({
          ...p,
          name: canonicalName
        });
      });
      
      let insertedPlayers = [];
      if (newPlayers.length > 0) {
        // Add points and won arrays to new players (4 nulls for 4 rounds)
        const playersToInsert = newPlayers.map(p => ({
          ...p,
          points: [null, null, null, null],
          won: [null, null, null, null]
        }));
        
        const { data, error: insertError } = await supabase
          .from('players')
          .insert(playersToInsert)
          .select();

        if (insertError) throw insertError;
        insertedPlayers = data;
        // Add new players to the mapping
        newPlayers.forEach((newPlayer, index) => {
          playerNameMapping.set(newPlayer.name, insertedPlayers[index]);
        });
      }

      // 4️⃣ Combine existing + inserted players to build a map
      // Build playerMap using normalized form names as keys
      const allPlayers = [...existingPlayers, ...insertedPlayers];
      const playerMap = {};
      
      // Create mappings for all players (both normalized and original names)
      allPlayers.forEach(p => {
        const normalized = normalizePlayerName(p.name);
        playerMap[normalized] = p.id;
        // Also keep original name mapping for backwards compatibility
        playerMap[p.name] = p.id;
      });
      
      // Add mappings from form input names to player IDs
      playerNameMapping.forEach((player, formName) => {
        playerMap[formName] = player.id;
        const normalizedFormName = normalizePlayerName(formName);
        playerMap[normalizedFormName] = player.id;
      });

      // 5️⃣ Build fantasy team object (use normalized names for lookup)
      const getPlayerId = (playerName) => {
        if (!playerName) return null;
        // Try normalized name first, then original name
        return playerMap[normalizePlayerName(playerName)] || playerMap[playerName];
      };

      const fantasyTeam = {
        owner_name: formData.yourName,
        team_name: formData.teamName,
        email: normalizedEmail,
        players: JSON.stringify({
          qb1: getPlayerId(formData.qb1),
          qb2: getPlayerId(formData.qb2),
          wr: getPlayerId(formData.wr),
          rb: getPlayerId(formData.rb),
          te: getPlayerId(formData.te),
          flex1: getPlayerId(formData.flex1),
          flex2: getPlayerId(formData.flex2),
          flex3: getPlayerId(formData.flex3),
          flex4: getPlayerId(formData.flex4),
          def: getPlayerId(formData['def-team']), // Use team select value for defense
          kicker: getPlayerId(formData.kicker),
          sbWinner: getPlayerId(formData['sbWinner-team']), // Use team select value for SB winner
        }),
        total_points: 0,
        rank: 0,
      };

      // 6️⃣ Insert fantasy team into the database
      const { data: teamData, error: teamError } = await supabase
        .from('fantasy_teams')
        .insert([fantasyTeam]);

      if (teamError) throw teamError;

      console.log('Team saved:', teamData);

      // 7️⃣ Update invited_emails to mark email as used
      // Use the actual email from the database record for the update
      const { error: updateError } = await supabase
        .from('invited_emails')
        .update({ 
          used: true,
          used_at: new Date().toISOString()
        })
        .eq('id', invitedEmail.id);

      if (updateError) {
        console.error('Error updating invited_emails:', updateError);
        throw updateError;
      }

      // Reset form and navigate to home
      setFormData(initialFormData);
      setModalOpen(false);
      setIsSubmitting(false);
      navigate('/');

    } catch (err) {
      console.error(err);
      setSubmitError('An error occurred while submitting your team. Please try again.');
      setIsSubmitting(false);
    }
  };



  // Helper component for team dropdown
  const TeamSelect = ({ name, id, required, fullWidth }) => {
    return (
      <select 
        name={name} 
        id={id}
        value={formData[name] || ''}
        onChange={(e) => handleInputChange(name, e.target.value)}
        required={required}
        className={`border-2 border-gray-400 rounded-md px-3 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all ${fullWidth ? 'flex-1' : ''}`}
      >
        <option value="" disabled>Team</option>
        <optgroup label="AFC">
          {Object.keys(teamSeeds.AFC).sort().map(team => (
            <option key={team} value={team}>{team}</option>
          ))}
        </optgroup>
        <optgroup label="NFC">
          {Object.keys(teamSeeds.NFC).sort().map(team => (
            <option key={team} value={team}>{team}</option>
          ))}
        </optgroup>
      </select>
    );
  };

  // Helper component for flex position dropdown
  const FlexPositionSelect = ({ name, id, required }) => (
    <select
      name={name}
      id={id}
      value={formData[name] || ''}
      onChange={(e) => handleInputChange(name, e.target.value)}
      required={required}
      className="border-2 border-gray-400 rounded-md px-3 py-3 bg-white text-gray-800"
    >
      <option value="" disabled>Pos</option>
      <option value="RB">RB</option>
      <option value="WR">WR</option>
      <option value="TE">TE</option>
    </select>
  );

  return (
    <>
    <div className="flex flex-col flex-1 min-h-screen">
    <div className="container grid grid-cols-1 md:grid-cols-16 mx-auto "> 
      <div className="col-start-2 col-span-14"> 
        <div className="flex flex-col items-center justify-center mt-10 mb-6">
            <h1 className="text-4xl font-bold mb-8 text-white">Enter Team</h1>

          {/* form for entering team */}
            <form className="w-full max-w-6xl" onSubmit={handleSubmit}>
              <div className="bg-gray-200 rounded-lg p-8 shadow-lg">
                {/* Owner and Team Name Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  <div className="flex flex-col">
                    <label htmlFor="your-name" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide"> Your Name </label>
                    <input type="text" id="your-name" name="your-name" value={formData.yourName} onChange={(e) => handleInputChange('yourName', e.target.value)} required className="border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Enter your name" />
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="team-name" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide"> Team Name </label>
                    <input type="text" id="team-name" name="team-name" value={formData.teamName} onChange={(e) => handleInputChange('teamName', e.target.value)} required className="border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Enter team name" /> 
                  </div>
                </div>

                {/* Player Positions Section */}

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col">
                    <label htmlFor="qb1" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">QB1</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="qb1" name="qb1" value={formData.qb1} onChange={(e) => handleInputChange('qb1', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="qb1-team" id="qb1-team" required />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="qb2" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">QB2</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="qb2" name="qb2" value={formData.qb2} onChange={(e) => handleInputChange('qb2', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="qb2-team" id="qb2-team" required />
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <label htmlFor="wr" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">WR</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="wr" name="wr" value={formData.wr} onChange={(e) => handleInputChange('wr', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="wr-team" id="wr-team" required />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="rb" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">RB</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="rb" name="rb" value={formData.rb} onChange={(e) => handleInputChange('rb', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="rb-team" id="rb-team" required />
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <label htmlFor="te" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">TE</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="te" name="te" value={formData.te} onChange={(e) => handleInputChange('te', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="te-team" id="te-team" required />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="flex1" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Flex 1</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="flex1" name="flex1" value={formData.flex1} onChange={(e) => handleInputChange('flex1', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <FlexPositionSelect name="flex1-truepos" id="flex1-truepos" required/>
                      <TeamSelect name="flex1-team" id="flex1-team" required />
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <label htmlFor="flex2" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Flex 2</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="flex2" name="flex2" value={formData.flex2} onChange={(e) => handleInputChange('flex2', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <FlexPositionSelect name="flex2-truepos" id="flex2-truepos" required/>
                      <TeamSelect name="flex2-team" id="flex2-team" required />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="flex3" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Flex 3</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="flex3" name="flex3" value={formData.flex3} onChange={(e) => handleInputChange('flex3', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <FlexPositionSelect name="flex3-truepos" id="flex3-truepos" required/>
                      <TeamSelect name="flex3-team" id="flex3-team" required />
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <label htmlFor="flex4" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Flex 4</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="flex4" name="flex4" value={formData.flex4} onChange={(e) => handleInputChange('flex4', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <FlexPositionSelect name="flex4-truepos" id="flex4-truepos" required/>
                      <TeamSelect name="flex4-team" id="flex4-team" required />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="def-team" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Defense</label>
                    <div className="flex flex-row gap-2">
                      {/* <input  type="text" id="def" name="def" value={formData.def} onChange={(e) => handleInputChange('def', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/> */}
                      <TeamSelect name="def-team" id="def-team" required fullWidth />
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <label htmlFor="kicker" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Kicker</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="kicker" name="kicker" value={formData.kicker} onChange={(e) => handleInputChange('kicker', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="kicker-team" id="kicker-team" required />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="sbWinner-team" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">SB Winner</label>
                    <div className="flex flex-row gap-2">
                      {/* <input  type="text" id="sbWinner" name="sbWinner" value={formData.sbWinner} onChange={(e) => handleInputChange('sbWinner', e.target.value)} required className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/> */}
                      <TeamSelect name="sbWinner-team" id="sbWinner-team" required fullWidth />
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <div className="mt-8 flex justify-center">
                  <button type="submit" className="bg-sky-500 hover:bg-sky-600 text-white font-semibold py-3 px-8 rounded-md ease-in-out duration-300 shadow-md hover:shadow-lg">Submit Team</button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
    </div>

    {/* Modal for validation */}
    {modalOpen && (
      <div className="fixed inset-0 bg-transparent backdrop-blur-sm flex justify-center items-center z-50 h-full w-full">
        <div className="bg-white p-6 rounded w-96 rounded-lg shadow-lg">
          <h2 className="text-xl font-bold mb-3">
            {canSubmit ? "Your Team Passes!" : "Rule Violations"}
          </h2>

          {!canSubmit && (
            <ul className="text-red-600 list-disc pl-4">
              {modalIssues.map((issue, i) => <li key={i}>{issue}</li>)}
            </ul>
          )}

          {canSubmit && (
            <>
              <p className="text-black mb-4">Everything looks good! You are ready to submit!</p>
              
              <div className="flex flex-col gap-3 mb-4">
                <div className="flex flex-col">
                  <label htmlFor="modal-email" className="text-gray-700 mb-2 font-semibold mb-1 text-sm">Email</label>
                  <input 
                    type="email" 
                    id="modal-email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="border-2 border-gray-400 rounded-md px-3 py-2 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all"
                    placeholder="Enter your email"
                  />
                </div>
                
                <div className="flex flex-col">
                  <label htmlFor="modal-password" className="text-gray-700 font-semibold mb-1 text-sm">Password</label>
                  <input 
                    type="password" 
                    id="modal-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        submitTeam();
                      }
                    }}
                    className="border-2 border-gray-400 rounded-md px-3 py-2 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all"
                    placeholder="Enter password"
                  />
                </div>
              </div>

              {submitError && (
                <p className="text-red-600 text-sm mb-3">{submitError}</p>
              )}
            </>
          )}

          <div className="flex justify-between gap-3 mt-5 mx-auto">
            <button onClick={() => setModalOpen(false)} className="px-4 py-2 bg-gray-500 rounded ease-in-out duration-300">Close</button>

            {canSubmit && (
              <button
                type="button"
                onClick={submitTeam}
                className="px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded ease-in-out duration-300"
              >
                Submit
              </button>
            )}
          </div>
        </div>
      </div>
    )}
    </>
  )
}

export default EnterTeam;
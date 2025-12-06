import React, {useState} from 'react';
import { teamSeeds } from '../components/teamseeds';

function EnterTeam(){
  const [formData, setFormData] = useState({
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
  });
  const [modalOpen, setModalOpen] = useState(false);
  const [modalIssues, setModalIssues] = useState([]);
  const [canSubmit, setCanSubmit] = useState(false);

  const handleInputChange = (name, value) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };


  const handleSubmit = (e) => {
    e.preventDefault();
    validateTeam();
  }

  const validateTeam = () => {
    console.log('=== VALIDATION START ===');
    console.log('Form Data:', formData);
    
    const entries = {
      qb1: {team: formData["qb1-team"], pos: "QB"},
      qb2: {team: formData["qb2-team"], pos: "QB"},
      wr: {team: formData["wr-team"], pos: "WR"},
      rb: {team: formData["rb-team"], pos: "RB"},
      te: {team: formData["te-team"], pos: "TE"},
  
      flex1: {team: formData["flex1-team"], pos: formData["flex1-truepos"]},
      flex2: {team: formData["flex2-team"], pos: formData["flex2-truepos"]},
      flex3: {team: formData["flex3-team"], pos: formData["flex3-truepos"]},
      flex4: {team: formData["flex4-team"], pos: formData["flex4-truepos"]},
  
      def: {team: formData["def-team"], pos: "Defense"},
      kicker: {team: formData["kicker-team"], pos: "Kicker"},
      sbWinner: {team: formData["sbWinner-team"], pos: "SB Winner"},
    };
    console.log('Entries:', entries);
    
    const issues = [];

    // Helper maps
    const teamCounts = {};
    const seedCounts = { "6or7": 0, "4or5": 0 };
    const teamsUsed = new Set();
    const qbTeams = [];
    const qbConferences = new Set();

    // Loop players
    Object.values(entries).forEach(p => {
      if (!p.team) return;

      // Count total players per team (Rule 4)
      teamCounts[p.team] = (teamCounts[p.team] || 0) + 1;

      // Track different teams (Rule 3)
      teamsUsed.add(p.team);

      // Get seeds
      const seed = teamSeeds.AFC[p.team] || teamSeeds.NFC[p.team];
      console.log(`Player ${p.pos} from ${p.team} - Seed: ${seed}`);

      if (seed === 6 || seed === 7) seedCounts["6or7"]++;
      if (seed === 4 || seed === 5) seedCounts["4or5"]++;

      // Gather QB info (Rule 6)
      if (p.pos === "QB") {
        qbTeams.push(p.team);

        const conf = teamSeeds.AFC[p.team] ? "AFC" : "NFC";
        qbConferences.add(conf);
      }
    });

    console.log('Team Counts:', teamCounts);
    console.log('Seed Counts:', seedCounts);
    console.log('Teams Used (Set):', Array.from(teamsUsed));
    console.log('Teams Used Count:', teamsUsed.size);
    console.log('QB Teams:', qbTeams);
    console.log('QB Conferences (Set):', Array.from(qbConferences));

    // -----------------------------
    // RULE 1 — Must have 2 players from seeds 6 or 7
    // -----------------------------
    console.log('RULE 1 Check - Seed 6or7 count:', seedCounts["6or7"], 'Required: 2');
    if (seedCounts["6or7"] < 2) {
      issues.push("You must have at least **2 players from a #6 or #7 seed team**.");
      console.log('❌ RULE 1 FAILED');
    } else {
      console.log('✅ RULE 1 PASSED');
    }

    // -----------------------------
    // RULE 2 — Must have 1 player from seeds 4 or 5
    // -----------------------------
    console.log('RULE 2 Check - Seed 4or5 count:', seedCounts["4or5"], 'Required: 1');
    if (seedCounts["4or5"] < 1) {
      issues.push("You must have at least **1 player from a #4 or #5 seed team**.");
      console.log('❌ RULE 2 FAILED');
    } else {
      console.log('✅ RULE 2 PASSED');
    }

    // -----------------------------
    // RULE 3 — Players from at least 9 different teams
    // -----------------------------
    console.log('RULE 3 Check - Unique teams:', teamsUsed.size, 'Required: 9');
    if (teamsUsed.size < 9) {
      issues.push("You must have players from at least **9 different teams**.");
      console.log('❌ RULE 3 FAILED');
    } else {
      console.log('✅ RULE 3 PASSED');
    }

    // -----------------------------
    // RULE 4 — No more than 3 players from one team
    // -----------------------------
    console.log('RULE 4 Check - Team counts:', teamCounts);
    let rule4Passed = true;
    Object.entries(teamCounts).forEach(([team, count]) => {
      if (count > 3) {
        issues.push(`You selected **${count} players from ${team}**. Max allowed is 3.`);
        console.log(`❌ RULE 4 FAILED - ${team} has ${count} players (max 3)`);
        rule4Passed = false;
      }
    });
    if (rule4Passed) {
      console.log('✅ RULE 4 PASSED');
    }

    // -----------------------------
    // RULE 5 — No stacking (QB/WR/TE from same team)
    // -----------------------------
    const WRteam = entries.wr.team;
    const TEteam = entries.te.team;
    const flexTeams = [
      entries.flex1,
      entries.flex2,
      entries.flex3,
      entries.flex4
    ].filter(f => f.pos === "WR" || f.pos === "TE").map(f => f.team);

    console.log('RULE 5 Check - WR team:', WRteam, 'TE team:', TEteam);
    console.log('RULE 5 Check - QB teams:', qbTeams);
    console.log('RULE 5 Check - Flex WR/TE teams:', flexTeams);

    let rule5Passed = true;
    qbTeams.forEach(qbTeam => {
      if (qbTeam === WRteam) {
        issues.push("QB and WR cannot be from the same team.");
        console.log(`❌ RULE 5 FAILED - QB ${qbTeam} matches WR team`);
        rule5Passed = false;
      }
      if (qbTeam === TEteam) {
        issues.push("QB and TE cannot be from the same team.");
        console.log(`❌ RULE 5 FAILED - QB ${qbTeam} matches TE team`);
        rule5Passed = false;
      }
      if (flexTeams.includes(qbTeam)) {
        issues.push("QB cannot match the team of any WR/TE flex players.");
        console.log(`❌ RULE 5 FAILED - QB ${qbTeam} matches flex WR/TE team`);
        rule5Passed = false;
      }
    });
    if (rule5Passed) {
      console.log('✅ RULE 5 PASSED');
    }

    // -----------------------------
    // RULE 6 — QBs must be:
    //    - from different conferences
    //    - at least 1 must play Wildcard Weekend (not a #1 seed)
    // -----------------------------
    console.log('RULE 6 Check - QB Conferences count:', qbConferences.size, 'Required: 2');
    if (qbConferences.size !== 2) {
      issues.push("Your two QBs must be from **different conferences (AFC + NFC)**.");
      console.log('❌ RULE 6 FAILED - Conferences check');
    } else {
      console.log('✅ RULE 6 PASSED - Conferences check');
    }

    // At least ONE QB must NOT be seed #1
    const qbSeeds = qbTeams.map(t =>
      teamSeeds.AFC[t] || teamSeeds.NFC[t]
    );
    console.log('RULE 6 Check - QB Seeds:', qbSeeds);

    if (!qbSeeds.some(seed => seed !== 1)) {
      issues.push("At least **one QB must play on Wildcard Weekend** (cannot be both #1 seeds).");
      console.log('❌ RULE 6 FAILED - Both QBs are #1 seeds');
    } else {
      console.log('✅ RULE 6 PASSED - At least one QB is not #1 seed');
    }

    // -----------------------------
    // RULE 7 — No more than 4 players from #1 seeds
    // -----------------------------
    let numFromOnes = 0;
    const playersFromOnes = [];
    Object.entries(entries).forEach(([k, p]) => {
      if (!p.team) return;
      const seed = teamSeeds.AFC[p.team] || teamSeeds.NFC[p.team];
      if (seed === 1) {
        numFromOnes++;
        playersFromOnes.push(`${p.pos} from ${p.team}`);
      }
    });

    console.log('RULE 7 Check - Players from #1 seeds:', numFromOnes, 'Max allowed: 4');
    console.log('RULE 7 Check - Players from #1 seeds list:', playersFromOnes);
    if (numFromOnes > 4) {
      issues.push("You may not have more than **4 total players from the #1 seeds**.");
      console.log('❌ RULE 7 FAILED');
    } else {
      console.log('✅ RULE 7 PASSED');
    }

    console.log('=== VALIDATION RESULTS ===');
    console.log('Total Issues Found:', issues.length);
    console.log('Issues Array:', issues);
    console.log('Can Submit:', issues.length === 0);
    console.log('=== VALIDATION END ===\n');

    setModalIssues(issues);
    setCanSubmit(issues.length === 0);
    setModalOpen(true);
  }



  // Helper component for team dropdown
  const TeamSelect = ({ name, id }) => {
    return (
      <select 
        name={name} 
        id={id}
        value={formData[name] || ''}
        onChange={(e) => handleInputChange(name, e.target.value)}
        className="border-2 border-gray-400 rounded-md px-3 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all"
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
  const FlexPositionSelect = ({ name, id }) => (
    <select
      name={name}
      id={id}
      value={formData[name] || ''}
      onChange={(e) => handleInputChange(name, e.target.value)}
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
                    <input type="text" id="your-name" name="your-name" value={formData.yourName} onChange={(e) => handleInputChange('yourName', e.target.value)} className="border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Enter your name" />
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="team-name" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide"> Team Name </label>
                    <input type="text" id="team-name" name="team-name" value={formData.teamName} onChange={(e) => handleInputChange('teamName', e.target.value)} className="border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Enter team name" /> 
                  </div>
                </div>

                {/* Player Positions Section */}

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col">
                    <label htmlFor="qb1" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">QB1</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="qb1" name="qb1" value={formData.qb1} onChange={(e) => handleInputChange('qb1', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="qb1-team" id="qb1-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="qb2" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">QB2</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="qb2" name="qb2" value={formData.qb2} onChange={(e) => handleInputChange('qb2', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="qb2-team" id="qb2-team" />
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <label htmlFor="wr" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">WR</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="wr" name="wr" value={formData.wr} onChange={(e) => handleInputChange('wr', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="wr-team" id="wr-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="rb" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">RB</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="rb" name="rb" value={formData.rb} onChange={(e) => handleInputChange('rb', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="rb-team" id="rb-team" />
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <label htmlFor="te" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">TE</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="te" name="te" value={formData.te} onChange={(e) => handleInputChange('te', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="te-team" id="te-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="flex1" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Flex 1</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="flex1" name="flex1" value={formData.flex1} onChange={(e) => handleInputChange('flex1', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <FlexPositionSelect name="flex1-truepos" id="flex1-truepos" />
                      <TeamSelect name="flex1-team" id="flex1-team" />
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <label htmlFor="flex2" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Flex 2</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="flex2" name="flex2" value={formData.flex2} onChange={(e) => handleInputChange('flex2', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <FlexPositionSelect name="flex2-truepos" id="flex2-truepos" />
                      <TeamSelect name="flex2-team" id="flex2-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="flex3" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Flex 3</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="flex3" name="flex3" value={formData.flex3} onChange={(e) => handleInputChange('flex3', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <FlexPositionSelect name="flex3-truepos" id="flex3-truepos" />
                      <TeamSelect name="flex3-team" id="flex3-team" />
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <label htmlFor="flex4" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Flex 4</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="flex4" name="flex4" value={formData.flex4} onChange={(e) => handleInputChange('flex4', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <FlexPositionSelect name="flex4-truepos" id="flex4-truepos" />
                      <TeamSelect name="flex4-team" id="flex4-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="def" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Defense</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="def" name="def" value={formData.def} onChange={(e) => handleInputChange('def', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="def-team" id="def-team" />
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <label htmlFor="kicker" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">Kicker</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="kicker" name="kicker" value={formData.kicker} onChange={(e) => handleInputChange('kicker', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="kicker-team" id="kicker-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="sbWinner" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">SB Winner</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="sbWinner" name="sbWinner" value={formData.sbWinner} onChange={(e) => handleInputChange('sbWinner', e.target.value)} className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="sbWinner-team" id="sbWinner-team" />
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

          {canSubmit && <p className="text-black">Everything looks good! You are ready to submit!</p>}

          <div className="flex justify-between gap-3 mt-5 mx-auto">
            <button onClick={() => setModalOpen(false)} className="px-4 py-2 bg-gray-500 rounded ease-in-out duration-300">Close</button>

            {canSubmit && (
              <button
                onClick={() => {
                  setModalOpen(false);
                  console.log('Submit to backend:', formData);
                  // TODO: API POST here
                }}
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
import React from 'react';
import { teamSeeds } from './teamseeds';

/**
 * Validates a fantasy team against all rules
 * @param {Object} formData - The form data containing all player selections
 * @returns {Object} - Object containing issues array and isValid boolean
 */
export const validateTeam = (formData) => {
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

  return {
    issues,
    isValid: issues.length === 0
  };
};

function TeamValidator(){
  return (
    <div>
      <h1></h1>
    </div>
  )
}

export default TeamValidator;


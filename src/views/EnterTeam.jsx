import React from 'react';
import { teamSeeds } from '../components/teamseeds';

function EnterTeam(){
  // Helper component for team dropdown
  const TeamSelect = ({ name, id }) => {
    return (
      <select 
        name={name} 
        id={id}
        defaultValue=""
        className="border-2 border-gray-400 rounded-md px-3 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all"
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

  return (
    <div className="flex flex-col flex-1 min-h-screen">
    <div className="container grid grid-cols-1 md:grid-cols-16 mx-auto "> 
      <div className="col-start-2 col-span-14"> 
        <div className="flex flex-col items-center justify-center mt-10 mb-6">
            <h1 className="text-4xl font-bold mb-8 text-white">Enter Team</h1>

          {/* form for entering team */}
            <form className="w-full max-w-6xl">
              <div className="bg-gray-200 rounded-lg p-8 shadow-lg">
                {/* Owner and Team Name Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  <div className="flex flex-col">
                    <label htmlFor="your-name" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide"> Your Name </label>
                    <input type="text" id="your-name" name="your-name" className="border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" placeholder="Enter your name" />
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="team-name" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide"> Team Name </label>
                    <input type="text" id="team-name" name="team-name" className="border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" placeholder="Enter team name" /> 
                  </div>
                </div>

                {/* Player Positions Section */}

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col">
                    <label htmlFor="qb1" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide text-left ml-4">QB1</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="qb1" name="qb1" className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="qb1-team" id="qb1-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="qb1" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">QB2</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="qb2" name="qb2" className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="qb2-team" id="qb2-team" />
                    </div>
                  </div>
                </div>



                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="flex flex-col">
                    <label htmlFor="qb1" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">QB1</label>
                    <div className="flex flex-row gap-2">
                      <input  type="text" id="qb1" name="qb1" className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" placeholder="Player name"/>
                      <TeamSelect name="qb1-team" id="qb1-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="qb2" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      QB2
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="qb2" 
                        name="qb2" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Player name"
                      />
                      <TeamSelect name="qb2-team" id="qb2-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="wr" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      WR
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="wr" 
                        name="wr" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Player name"
                      />
                      <TeamSelect name="wr-team" id="wr-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="rb" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      RB
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="rb" 
                        name="rb" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Player name"
                      />
                      <TeamSelect name="rb-team" id="rb-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="te" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      TE
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="te" 
                        name="te" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Player name"
                      />
                      <TeamSelect name="te-team" id="te-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="flex1" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      Flex 1
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="flex1" 
                        name="flex1" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Player name"
                      />
                      <TeamSelect name="flex1-team" id="flex1-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="flex2" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      Flex 2
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="flex2" 
                        name="flex2" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Player name"
                      />
                      <TeamSelect name="flex2-team" id="flex2-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="flex3" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      Flex 3
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="flex3" 
                        name="flex3" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Player name"
                      />
                      <TeamSelect name="flex3-team" id="flex3-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="flex4" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      Flex 4
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="flex4" 
                        name="flex4" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Player name"
                      />
                      <TeamSelect name="flex4-team" id="flex4-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="sbWinner" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      SB Winner
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="sbWinner" 
                        name="sbWinner" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Team name"
                      />
                      <TeamSelect name="sbWinner-team" id="sbWinner-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="def" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      Defense
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="def" 
                        name="def" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Team name"
                      />
                      <TeamSelect name="def-team" id="def-team" />
                    </div>
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="k" className="text-gray-700 font-semibold mb-2 text-sm uppercase tracking-wide">
                      Kicker
                    </label>
                    <div className="flex flex-row gap-2">
                      <input 
                        type="text" 
                        id="k" 
                        name="k" 
                        className="flex-1 border-2 border-gray-400 rounded-md px-4 py-3 bg-white text-gray-800 focus:outline-none focus:border-violet-600 focus:ring-2 focus:ring-violet-200 transition-all" 
                        placeholder="Player name"
                      />
                      <TeamSelect name="k-team" id="k-team" />
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <div className="mt-8 flex justify-center">
                  <button 
                    type="submit" 
                    className="bg-violet-600 hover:bg-violet-700 text-white font-semibold py-3 px-8 rounded-md transition-colors duration-200 shadow-md hover:shadow-lg"
                  >
                    Submit Team
                  </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
    </div>
  )
}

export default EnterTeam;
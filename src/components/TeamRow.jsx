import React from 'react';

function TeamRow({ team }) {

  return (
    <div 
      className="grid gap-2 px-2 border border-slate-700 rounded-md p-6 mb-2"
      style={{ gridTemplateColumns: '200px repeat(12, minmax(100px, 1fr))' }}
    >
      {/* Combined Team Info Column */}
      <div className="flex flex-col justify-center">
        <div className="text-white text-center font-bold m-1">#{team.rank}</div>
        <div className="text-white text-center m-1">{team.teamName}</div>
        <div className="text-white text-center text-sm m-1">{team.ownerName}</div>
        <div className="text-emerald-400 text-center font-bold m-1">{team.totalPoints}</div>
      </div>

      {/* QB1 */}
      <div className="flex flex-col justify-center rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.qb1.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.qb1.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.qb1.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.qb1.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.qb1.points}</div>
      </div>

      {/* QB2 */}
      <div className="flex flex-col justify-center  rounded px-2 py-1">
      <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.qb2.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.qb2.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.qb2.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.qb2.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.qb2.points}</div>
      </div>

      {/* WR */}
      <div className="flex flex-col justify-center 0 rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.wr.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.wr.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.wr.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.wr.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.wr.points}</div>
      </div>

      {/* RB */}
      <div className="flex flex-col justify-center  rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.rb.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.rb.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.rb.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.rb.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.rb.points}</div>
      </div>

      {/* TE */}
      <div className="flex flex-col justify-center rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.te.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.te.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.te.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.te.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.te.points}</div>
      </div>

      {/* Flex 1 */}
      <div className="flex flex-col justify-center rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.flex1.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.flex1.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.flex1.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.flex1.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.flex1.points}</div>
      </div>

      {/* Flex 2 */}
      <div className="flex flex-col justify-center  rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.flex2.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.flex2.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.flex2.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.flex2.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.flex2.points}</div>
      </div>

      {/* Flex 3 */}
      <div className="flex flex-col justify-center  rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.flex3.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.flex3.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.flex3.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.flex3.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.flex3.points}</div>
      </div>

      {/* Flex 4 */}
      <div className="flex flex-col justify-center rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.flex4.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.flex4.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.flex4.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.flex4.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.flex4.points}</div>
      </div>

      {/* SB Winner */}
      <div className="flex flex-col justify-center  rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.sbWinner.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.sbWinner.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.sbWinner.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.sbWinner.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.sbWinner.points}</div>
      </div>

      {/* DEF */}
      <div className="flex flex-col justify-center  rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.def.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.def.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.def.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.def.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.def.points}</div>
      </div>

      {/* K */}
      <div className="flex flex-col justify-center  rounded px-2 py-1">
        <div className="flex flex-col justify-center"> <img src="images/lamarjackson.png" alt="Lamar Jackson" className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{team.k.name}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.k.points}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.k.points}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.k.points}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.k.points}</div>
      </div>
    </div>
  );
}

export default TeamRow;
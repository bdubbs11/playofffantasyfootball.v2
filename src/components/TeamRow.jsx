import React, { useState } from 'react';

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

function TeamRow({ team }) {
  // Helper function to capitalize names for display
  const capitalizeName = (name) => {
    if (!name) return '';
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  // Helper function to get className for player box based on elimination status
  const getPlayerBoxClassName = (player) => {
    const baseClasses = "flex flex-col justify-center rounded px-2 py-1";
    if (player.isEliminated) {
      return `${baseClasses} bg-black`;
    }
    return baseClasses;
  };

  return (
    <div 
      className="grid gap-2 px-2 border border-slate-700 rounded-md p-6 mb-2"
      style={{ gridTemplateColumns: '200px repeat(12, minmax(100px, 1fr))' }}
    >
      {/* Combined Team Info Column */}
      <div className="flex flex-col justify-center">
        <div className="text-white text-center font-bold m-1">#{team.rank}</div>
        <div className="text-white text-center m-1">{capitalizeName(team.teamName)}</div>
        <div className="text-white text-center text-sm m-1">{capitalizeName(team.ownerName)}</div>
        <div className="text-emerald-400 text-center font-bold m-1">{team.totalPoints}</div>
      </div>

      {/* QB1 */}
      <div className={getPlayerBoxClassName(team.qb1)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.qb1.name} alt={capitalizeName(team.qb1.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.qb1.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.qb1.points.wildcard !== null ? team.qb1.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.qb1.points.divisional !== null ? team.qb1.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.qb1.points.conference !== null ? team.qb1.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.qb1.points.superBowl !== null ? team.qb1.points.superBowl : '-'}</div>
      </div>

      {/* QB2 */}
      <div className={getPlayerBoxClassName(team.qb2)}>
      <div className="flex flex-col justify-center"> <ImageWithFallback name={team.qb2.name} alt={capitalizeName(team.qb2.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.qb2.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.qb2.points.wildcard !== null ? team.qb2.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.qb2.points.divisional !== null ? team.qb2.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.qb2.points.conference !== null ? team.qb2.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.qb2.points.superBowl !== null ? team.qb2.points.superBowl : '-'}</div>
      </div>

      {/* WR */}
      <div className={getPlayerBoxClassName(team.wr)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.wr.name} alt={capitalizeName(team.wr.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.wr.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.wr.points.wildcard !== null ? team.wr.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.wr.points.divisional !== null ? team.wr.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.wr.points.conference !== null ? team.wr.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.wr.points.superBowl !== null ? team.wr.points.superBowl : '-'}</div>
      </div>

      {/* RB */}
      <div className={getPlayerBoxClassName(team.rb)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.rb.name} alt={capitalizeName(team.rb.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.rb.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.rb.points.wildcard !== null ? team.rb.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.rb.points.divisional !== null ? team.rb.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.rb.points.conference !== null ? team.rb.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.rb.points.superBowl !== null ? team.rb.points.superBowl : '-'}</div>
      </div>

      {/* TE */}
      <div className={getPlayerBoxClassName(team.te)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.te.name} alt={capitalizeName(team.te.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.te.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.te.points.wildcard !== null ? team.te.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.te.points.divisional !== null ? team.te.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.te.points.conference !== null ? team.te.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.te.points.superBowl !== null ? team.te.points.superBowl : '-'}</div>
      </div>

      {/* Flex 1 */}
      <div className={getPlayerBoxClassName(team.flex1)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.flex1.name} alt={capitalizeName(team.flex1.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.flex1.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.flex1.points.wildcard !== null ? team.flex1.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.flex1.points.divisional !== null ? team.flex1.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.flex1.points.conference !== null ? team.flex1.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.flex1.points.superBowl !== null ? team.flex1.points.superBowl : '-'}</div>
      </div>

      {/* Flex 2 */}
      <div className={getPlayerBoxClassName(team.flex2)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.flex2.name} alt={capitalizeName(team.flex2.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.flex2.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.flex2.points.wildcard !== null ? team.flex2.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.flex2.points.divisional !== null ? team.flex2.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.flex2.points.conference !== null ? team.flex2.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.flex2.points.superBowl !== null ? team.flex2.points.superBowl : '-'}</div>
      </div>

      {/* Flex 3 */}
      <div className={getPlayerBoxClassName(team.flex3)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.flex3.name} alt={capitalizeName(team.flex3.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.flex3.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.flex3.points.wildcard !== null ? team.flex3.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.flex3.points.divisional !== null ? team.flex3.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.flex3.points.conference !== null ? team.flex3.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.flex3.points.superBowl !== null ? team.flex3.points.superBowl : '-'}</div>
      </div>

      {/* Flex 4 */}
      <div className={getPlayerBoxClassName(team.flex4)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.flex4.name} alt={capitalizeName(team.flex4.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.flex4.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.flex4.points.wildcard !== null ? team.flex4.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.flex4.points.divisional !== null ? team.flex4.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.flex4.points.conference !== null ? team.flex4.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.flex4.points.superBowl !== null ? team.flex4.points.superBowl : '-'}</div>
      </div>

      {/* K */}
      <div className={getPlayerBoxClassName(team.k)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.k.name} alt={capitalizeName(team.k.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.k.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.k.points.wildcard !== null ? team.k.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.k.points.divisional !== null ? team.k.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.k.points.conference !== null ? team.k.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.k.points.superBowl !== null ? team.k.points.superBowl : '-'}</div>
      </div>

      {/* DEF */}
      <div className={getPlayerBoxClassName(team.def)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.def.name} alt={capitalizeName(team.def.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.def.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.def.points.wildcard !== null ? team.def.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.def.points.divisional !== null ? team.def.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.def.points.conference !== null ? team.def.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.def.points.superBowl !== null ? team.def.points.superBowl : '-'}</div>
      </div>

      {/* SB Winner */}
      <div className={getPlayerBoxClassName(team.sbWinner)}>
        <div className="flex flex-col justify-center"> <ImageWithFallback name={team.sbWinner.name} alt={capitalizeName(team.sbWinner.name)} className="w-40 h-30 mb-4" /></div>
        <div className="text-white text-center text-base">{capitalizeName(team.sbWinner.name)}</div>
        <div className="text-slate-400 text-center text-sm">Wildcard : {team.sbWinner.points.wildcard !== null ? team.sbWinner.points.wildcard : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Divsional : {team.sbWinner.points.divisional !== null ? team.sbWinner.points.divisional : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Conference : {team.sbWinner.points.conference !== null ? team.sbWinner.points.conference : '-'}</div>
        <div className="text-slate-400 text-center text-sm">Super Bowl : {team.sbWinner.points.superBowl !== null ? team.sbWinner.points.superBowl : '-'}</div>
      </div>      
    </div>
  );
}

export default TeamRow;
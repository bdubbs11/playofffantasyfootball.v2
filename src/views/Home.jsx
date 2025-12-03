import React from 'react';
import TeamRow from '../components/TeamRow';

function Home(){
  // Sample team data
  const sampleTeam = [
    {
    rank: 1,
    ownerName: "John Doe",
    teamName: "The Champions",
    totalPoints: 125.5,
    qb1: { name: "Patrick Mahomes", points: 28.5 },
    qb2: { name: "Josh Allen", points: 25.2 },
    wr: { name: "Tyreek Hill", points: 18.3 },
    rb: { name: "Derrick Henry", points: 15.8 },
    te: { name: "Travis Kelce", points: 12.4 },
    flex1: { name: "Davante Adams", points: 16.2 },
    flex2: { name: "Austin Ekeler", points: 14.7 },
    flex3: { name: "Cooper Kupp", points: 13.9 },
    flex4: { name: "Jonathan Taylor", points: 11.5 },
    sbWinner: { name: "Kansas City Chiefs", points: 20.0 },
    def: { name: "Buffalo Bills", points: 8.5 },
    k: { name: "Justin Tucker", points: 12.0 },
  },
  {
    rank: 2,
    ownerName: "Jane Doe",
    teamName: "The Runners Up",
    totalPoints: 120.0,
    qb1: { name: "Lamar Jackson", points: 28.5 },
    qb2: { name: "Josh Allen", points: 25.2 },
    wr: { name: "Tyreek Hill", points: 18.3 },
    rb: { name: "Derrick Henry", points: 15.8 },
    te: { name: "Travis Kelce", points: 12.4 },
    flex1: { name: "Davante Adams", points: 16.2 },
    flex2: { name: "Austin Ekeler", points: 14.7 },
    flex3: { name: "Cooper Kupp", points: 13.9 },
    flex4: { name: "Jonathan Taylor", points: 11.5 },
    sbWinner: { name: "Kansas City Chiefs", points: 20.0 },
    def: { name: "Buffalo Bills", points: 8.5 },
    k: { name: "Justin Tucker", points: 12.0 },
  },
  {
    rank: 3,
    ownerName: "Jim Doe",
    teamName: "The Third Place Team",
    totalPoints: 115.0,
    qb1: { name: "Lamar Jackson", points: 28.5 },
    qb2: { name: "Josh Allen", points: 25.2 },
    wr: { name: "Tyreek Hill", points: 18.3 },
    rb: { name: "Derrick Henry", points: 15.8 },
    te: { name: "Travis Kelce", points: 12.4 },
    flex1: { name: "Davante Adams", points: 16.2 },
    flex2: { name: "Austin Ekeler", points: 14.7 },
    flex3: { name: "Cooper Kupp", points: 13.9 },
    flex4: { name: "Jonathan Taylor", points: 11.5 },
    sbWinner: { name: "Kansas City Chiefs", points: 20.0 },
    def: { name: "Buffalo Bills", points: 8.5 },
    k: { name: "Justin Tucker", points: 12.0 },
  },
  {
    rank: 4,
    ownerName: "Jill Doe",
    teamName: "The Fourth Place Team",
    totalPoints: 110.0,
    qb1: { name: "Lamar Jackson", points: 28.5 },
    qb2: { name: "Josh Allen", points: 25.2 },
    wr: { name: "Tyreek Hill", points: 18.3 },
    rb: { name: "Derrick Henry", points: 15.8 },
    te: { name: "Travis Kelce", points: 12.4 },
    flex1: { name: "Davante Adams", points: 16.2 },
    flex2: { name: "Austin Ekeler", points: 14.7 },
    flex3: { name: "Cooper Kupp", points: 13.9 },
    flex4: { name: "Jonathan Taylor", points: 11.5 },
    sbWinner: { name: "Kansas City Chiefs", points: 20.0 },
    def: { name: "Buffalo Bills", points: 8.5 },
    k: { name: "Justin Tucker", points: 12.0 },
  },
];

  return (
    <div className="flex flex-col flex-1 min-h-screen">
      <div className="container grid grid-cols-1 md:grid-cols-16 mx-auto "> 
        <div className="col-start-2 col-span-14"> 

          <div className="flex flex-col items-center justify-center mt-10 mb-6">
            <h1 className="text-4xl font-bold mb-2">Wilson Playoff Fantasy Football</h1>
            <p className="text-lg">WildCard Round : Week 1</p>
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
              <div className="text-center">SB Winner</div>
              <div className="text-center">DEF</div>
              <div className="text-center">K</div>
            </div>
            {/* Team Rows */}
            {sampleTeam.map((team) => (
              <TeamRow key={team.rank} team={team} />
            ))}
            </div>
          </div>

          {/* header section above team names */}
          {/* <div className="flex flex-row items-center justify-between">
            <div className="flex flex-col items-center justify-center">
              <h2 className="text-2xl font-bold">Team Names</h2>
            </div>
            <div className="flex flex-col items-center justify-center">
              <h2 className="text-2xl font-bold">Team Names</h2>
            </div>
          </div> */}

        </div>
      </div>
    </div>
  )
}

export default Home;
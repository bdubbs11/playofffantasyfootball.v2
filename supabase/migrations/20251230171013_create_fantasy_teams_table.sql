create table fantasy_teams (
  id uuid primary key default gen_random_uuid(),
  owner_name text not null,
  team_name text not null,
  players jsonb not null,
  total_points numeric default 0,
  rank integer default 0,
  created_at timestamp with time zone default now()
)
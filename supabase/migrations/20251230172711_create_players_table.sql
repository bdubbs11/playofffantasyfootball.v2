create table players (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  team text not null,
  position text not null,
  points numeric[] default '{}',
  won boolean[] default '{}',
  created_at timestamp with time zone default now()
)

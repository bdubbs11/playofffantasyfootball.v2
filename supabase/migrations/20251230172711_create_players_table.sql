create table players (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  team text not null,
  position text not null,
  points numeric[] default ARRAY[NULL, NULL, NULL, NULL]::numeric[],
  won boolean[] default ARRAY[NULL, NULL, NULL, NULL]::boolean[],
  created_at timestamp with time zone default now()
)

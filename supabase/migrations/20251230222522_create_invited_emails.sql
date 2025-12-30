create table invited_emails (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  used boolean default false,
  created_at timestamp with time zone default now(),
  used_at timestamp with time zone
);

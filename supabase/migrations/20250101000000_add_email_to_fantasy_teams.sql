-- Add email column to fantasy_teams table
ALTER TABLE fantasy_teams 
ADD COLUMN IF NOT EXISTS email text UNIQUE;

-- Add index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_fantasy_teams_email ON fantasy_teams(email);


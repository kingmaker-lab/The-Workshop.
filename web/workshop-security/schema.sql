CREATE TABLE IF NOT EXISTS players (
 id TEXT PRIMARY KEY,nickname TEXT NOT NULL,nickname_key TEXT NOT NULL UNIQUE,
 session_hash TEXT NOT NULL UNIQUE,recovery_hash TEXT NOT NULL UNIQUE,
 created_at INTEGER NOT NULL,attempt_window INTEGER NOT NULL DEFAULT 0,
 attempt_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS solves (
 player_id TEXT NOT NULL,challenge_id TEXT NOT NULL,points INTEGER NOT NULL,
 solved_at INTEGER NOT NULL,PRIMARY KEY(player_id,challenge_id),
 FOREIGN KEY(player_id) REFERENCES players(id)
);
CREATE INDEX IF NOT EXISTS solves_player_idx ON solves(player_id);
CREATE INDEX IF NOT EXISTS solves_time_idx ON solves(solved_at);
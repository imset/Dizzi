CREATE TABLE IF NOT EXISTS guildsettings (
	GuildId integer PRIMARY KEY,
	Prefix text DEFAULT ";",
	Welcome text DEFAULT ""
);

CREATE TABLE IF NOT EXISTS exp (
	UserID integer PRIMARY KEY,
	XP integer DEFAULT 0,
	Level integer DEFAULT 0,
	XPLock text DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS avatarhistory (
	UserID integer PRIMARY KEY,
	Current text DEFAULT "",
	Store0 text DEFAULT "",
	Store1 text DEFAULT "",
	Store2 text DEFAULT "",
	Store3 text DEFAULT "",
	Store4 text DEFAULT ""
);

CREATE TABLE IF NOT EXISTS emojicount (
	dbid text PRIMARY KEY,
	reactiondict text DEFAULT "{}"
);

CREATE TABLE IF NOT EXISTS alert (
	dbid text PRIMARY KEY,
	alertset text DEFAULT "[]"
);

CREATE TABLE IF NOT EXISTS birthday (
	dbid text PRIMARY KEY,
	monthday text DEFAULT "",
	year text DEFAULT "",
	wished integer DEFAULT "0"
);
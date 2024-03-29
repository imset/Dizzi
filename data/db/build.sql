CREATE TABLE IF NOT EXISTS guildsettings (
	GuildId integer PRIMARY KEY,
	Prefix text DEFAULT "!",
	Welcome text DEFAULT ""
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

CREATE TABLE IF NOT EXISTS stand (
	UserID text PRIMARY KEY,
	name text DEFAULT " ",
	ability text DEFAULT " ",
	overview text DEFAULT " ",
	description text DEFAULT " ",
	pro1 text DEFAULT " ",
	pro2 text DEFAULT " ",
	pro3 text DEFAULT " ",
	con1 text DEFAULT " ",
	con2 text DEFAULT " ",
	con3 text DEFAULT " ",
	tags text DEFAULT "[]",
	total_comparisons integer DEFAULT 0,
	preference_ratio text DEFAULT "0.0",
	stats text DEFAULT "C, C, C, C, C, C",
	battlerecord text DEFAULT "0, 0",
	traits text DEFAULT " ",
	origin integer DEFAULT 0
);

CREATE TABLE IF NOT EXISTS arrows (
	UserID text PRIMARY KEY,
	arrowheads integer DEFAULT 4,
	shopclaim integer DEFAULT 0
);

CREATE TABLE IF NOT EXISTS email_queue (
	id SERIAL PRIMARY KEY,
	field varchar(150),
	reference varchar(20),
	date_created date,
	status int
);


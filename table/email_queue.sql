
CREATE TABLE IF NOT EXISTS email_queue (
	id BIGSERIAL PRIMARY KEY,
	field varchar(150),
	reference varchar(20),
	date_created datetime,
	status int
);


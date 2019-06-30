
CREATE TABLE IF NOT EXISTS email_queue (
	id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
	field varchar(150),
	reference varchar(20),
	date_created datetime,
	status int
);



CREATE TABLE IF NOT EXISTS item (
	id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
	item_desc varchar(150),
	qty int,
	rate int,
	amount varchar(20),
	invoice_id int,
    FOREIGN KEY (invoice_id) REFERENCES invoice(inv_id)
);
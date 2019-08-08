
CREATE TABLE IF NOT EXISTS item (
	id BIGSERIAL PRIMARY KEY,
	item_desc varchar(150),
	qty int,
	rate int,
	amount varchar(20),
	invoice_id int,
    FOREIGN KEY (invoice_id) REFERENCES invoice(inv_id)
);
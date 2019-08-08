
CREATE TABLE IF NOT EXISTS invoice (
    inv_id BIGSERIAL PRIMARY KEY ,
    name varchar(50),
	address Text,
	email varchar(150),
	phone varchar(20),
	post_addr varchar(20),
	disc_type varchar(10),
	disc_value varchar(10),
    purchase_no int,
    invoice_no varchar(30),
    date_value datetime,
    invoice_due datetime,
    currency varchar(3)
);




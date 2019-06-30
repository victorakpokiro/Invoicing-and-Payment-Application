
CREATE TABLE IF NOT EXISTS invoice (
    inv_id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name varchar(50),
	address varchar(50),
	email varchar(20),
	phone varchar(15),
	post_addr varchar(20),
	disc_type varchar(10),
	disc_value varchar(10),
    purch_no int,
    invoice_no varchar(30),
    date_value date,
    invoice_due date,
    paid_to_date varchar(20),
    balance varchar(20),
    sub_total int,
    total varchar(20),
    currency varchar(3)
);




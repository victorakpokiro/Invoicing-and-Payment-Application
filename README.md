# Invoicing-and-Payment-Application.
<br />
In-house web-app to Create, Issue and Track Invoices and Receipts accurately and quickly<br /><br />

There are three layers inplay, which are ` the main service `,  ` the api service`  and ` the background service `.

### The Main Service: 
This is the main application layer that generate client and invoice details and initiate a send invoice/receipt action via email,its tracking of sent invoice and receipt. Lastly its job start at a designated table, which serves as the point where all the information it requires will be stored.
This project has a url_prefix of '/admin' and was written with Python Flask with other libraries involved<br /><br />
This service is able to perform the following tasks. <br />
<ul>
	<li>Create Client/Customer, Invoice details</li>
	<li>Generate Invoice and Receipts with proper details.</li>
	<li>Send Generated Invoice and Receipts via emails and optionally texts 
	</li>
	<li>Keep Track of Payment and Expenditure records of the Company</li>
	<li>Check details created for deletes and edits before sending</li>

</ul>

### The APi Service: 
This is the application layer that is responsible for receiving the request that from the external service, its job is to validate details before the data is saved into the database. After the data is process and saved into the database, it must report the transaction on the email_queue table, before returning a response back to the external service. <br />
This service is yet to be completed and tested, as it should be able to receive invoice and receipt details, validate those details properly and also save the validated details to the database. After which it will then also create a record on the designated table, where the background service can start processing the transaction. The main reason why that part is not done at this layer is because it’s a tedious task and will therefore reduce general system response time. So to achieve a faster response time, its job must be structure this way. This project was written with Python Flask-RestFul with a few libraries involved<br /><br />




### The Background Service: 
This is a minor service after completion should be to perform the following tasks 
Send periodic Invoice notification reminders, 
Send Invoice notifications via emails and optionally texts 


#### Dependcies and Installation
SQLAlchemy and Flask-SQLAlchemy is the ORM used to connect to Postgres relational database<br />
	"""<br />
		# Postgres default uri <br />
		# dialect+driver://username:password@host:port/database<br />

	"""<br />
**Install libraries with "pip install"**


*The Main Service is live but it requires code clean-up some UI works to full completion*








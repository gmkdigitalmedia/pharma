CREATE TABLE user (
	id INTEGER NOT NULL, 
	username VARCHAR(64) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	role VARCHAR(20), 
	is_active BOOLEAN, 
	created_at DATETIME, 
	invited_by INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	UNIQUE (email), 
	FOREIGN KEY(invited_by) REFERENCES user (id)
);
CREATE TABLE hcp (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	hcp_id VARCHAR(50) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	specialty VARCHAR(100), 
	prescribing_pattern FLOAT, 
	engagement_score FLOAT, 
	tag VARCHAR(50), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE invitation (
	id INTEGER NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	token VARCHAR(100) NOT NULL, 
	role VARCHAR(20), 
	sender_id INTEGER NOT NULL, 
	used BOOLEAN, 
	created_at DATETIME, 
	expires_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (token), 
	FOREIGN KEY(sender_id) REFERENCES user (id)
);
CREATE TABLE api_connection (
	id INTEGER NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	api_key VARCHAR(256) NOT NULL, 
	api_secret VARCHAR(256), 
	base_url VARCHAR(256), 
	is_active BOOLEAN, 
	created_by INTEGER NOT NULL, 
	created_at DATETIME, 
	last_updated DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES user (id)
);
CREATE TABLE content (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	hcp_id INTEGER NOT NULL, 
	content_text TEXT NOT NULL, 
	risk_flags TEXT, 
	status VARCHAR(20), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user (id), 
	FOREIGN KEY(hcp_id) REFERENCES hcp (id)
);
CREATE TABLE campaign (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	content_id INTEGER NOT NULL, 
	channel VARCHAR(50) NOT NULL, 
	timing VARCHAR(50), 
	status VARCHAR(20), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user (id), 
	FOREIGN KEY(content_id) REFERENCES content (id)
);
CREATE TABLE analytics (
	id INTEGER NOT NULL, 
	campaign_id INTEGER NOT NULL, 
	open_rate FLOAT, 
	response_rate FLOAT, 
	compliance_status VARCHAR(20), 
	flags_resolved INTEGER, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(campaign_id) REFERENCES campaign (id)
);
CREATE TABLE asset (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	original_filename VARCHAR(255) NOT NULL, 
	stored_filename VARCHAR(255) NOT NULL, 
	file_type VARCHAR(50) NOT NULL, 
	mime_type VARCHAR(100) NOT NULL, 
	file_size INTEGER NOT NULL, 
	description VARCHAR(500), 
	tags VARCHAR(255), 
	is_active BOOLEAN, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE content_asset (
	id INTEGER NOT NULL, 
	content_id INTEGER NOT NULL, 
	asset_id INTEGER NOT NULL, 
	position INTEGER, 
	alt_text VARCHAR(255), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(content_id) REFERENCES content (id), 
	FOREIGN KEY(asset_id) REFERENCES asset (id)
);

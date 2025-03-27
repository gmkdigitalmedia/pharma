from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    industry = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='organization', lazy=True)
    
    def __repr__(self):
        return f'<Organization {self.name}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='agent')  # 'admin', 'manager', 'agent'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invited_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    
    invites = db.relationship('User', 
                              backref=db.backref('inviter', remote_side=[id]),
                              foreign_keys=[invited_by])
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
        
    def is_manager(self):
        return self.role == 'manager'
        
    def is_agent(self):
        return self.role == 'agent'
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class HCP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    hcp_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100))
    prescribing_pattern = db.Column(db.Float)
    engagement_score = db.Column(db.Float)
    tag = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add relationship to organization
    organization = db.relationship('Organization', backref=db.backref('hcps', lazy=True))
    
    # Keep track of which user created the HCP
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('created_hcps', lazy=True))
    
    def __repr__(self):
        return f'<HCP {self.hcp_id} - {self.name}>'

class Asset(db.Model):
    """Model for uploaded assets like images, PDFs, etc."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # image, document, video, etc.
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    description = db.Column(db.String(500))
    tags = db.Column(db.String(255))  # Comma-separated tags
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('assets', lazy=True))
    
    @property
    def file_url(self):
        """Get URL for the stored file"""
        return '/' + self.stored_filename
    
    @property
    def file_path(self):
        """Get absolute file path"""
        return self.stored_filename
    
    @property
    def human_readable_size(self):
        """Convert file size to human-readable format"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.2f} {unit}"
            size /= 1024
    
    def __repr__(self):
        return f'<Asset {self.original_filename} ({self.file_type})>'


class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hcp_id = db.Column(db.Integer, db.ForeignKey('hcp.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    content_text = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(20), default='email')  # email, pdf, presentation
    risk_flags = db.Column(db.Text)  # JSON-encoded list of flagged words
    status = db.Column(db.String(20), default='Draft')  # Draft, Flagged, Approved
    content_metadata = db.Column(db.Text)  # JSON-encoded additional information
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ai_generated = db.Column(db.Boolean, default=False)
    ai_model = db.Column(db.String(100))
    
    user = db.relationship('User', backref=db.backref('contents', lazy=True))
    hcp = db.relationship('HCP', backref=db.backref('contents', lazy=True))
    organization = db.relationship('Organization', backref=db.backref('contents', lazy=True))
    
    def get_flags(self):
        if self.risk_flags:
            return json.loads(self.risk_flags)
        return []
    
    def set_flags(self, flags):
        self.risk_flags = json.dumps(flags)
    
    def get_metadata(self):
        if self.content_metadata:
            return json.loads(self.content_metadata)
        return {}
    
    def set_metadata(self, metadata_dict):
        self.content_metadata = json.dumps(metadata_dict)
    
    def __repr__(self):
        return f'<Content {self.id} for HCP {self.hcp_id}>'


class ContentAsset(db.Model):
    """Association table for linking content with assets"""
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    position = db.Column(db.Integer, default=0)  # For ordering assets within content
    alt_text = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    content = db.relationship('Content', backref=db.backref('content_assets', lazy=True, cascade='all, delete-orphan'))
    asset = db.relationship('Asset', backref=db.backref('content_assets', lazy=True))
    
    def __repr__(self):
        return f'<ContentAsset {self.content_id} - {self.asset_id}>'

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    channel = db.Column(db.String(50), nullable=False)  # email, webinar, in-person
    timing = db.Column(db.String(50))  # time of day
    status = db.Column(db.String(20), default='Planned')  # Planned, Sent, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('campaigns', lazy=True))
    content = db.relationship('Content', backref=db.backref('campaigns', lazy=True))
    organization = db.relationship('Organization', backref=db.backref('campaigns', lazy=True))
    
    def __repr__(self):
        return f'<Campaign {self.id} - {self.channel}>'

class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    open_rate = db.Column(db.Float, default=0.0)
    response_rate = db.Column(db.Float, default=0.0)
    compliance_status = db.Column(db.String(20), default='Pending')  # Pending, Compliant, Non-Compliant
    flags_resolved = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    campaign = db.relationship('Campaign', backref=db.backref('analytics', lazy=True))
    
    def __repr__(self):
        return f'<Analytics for Campaign {self.campaign_id}>'

class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), default='agent')  # 'manager', 'agent'
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    sender = db.relationship('User', backref=db.backref('sent_invitations', lazy=True))
    organization = db.relationship('Organization', backref=db.backref('invitations', lazy=True))
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<Invitation to {self.email} by {self.sender_id}>'

class ApiConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 'VEEVA', 'Salesforce', 'Slack', etc.
    api_key = db.Column(db.String(256), nullable=False)
    api_secret = db.Column(db.String(256), nullable=True)
    base_url = db.Column(db.String(256), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', backref=db.backref('api_connections', lazy=True))
    organization = db.relationship('Organization', backref=db.backref('api_connections', lazy=True))
    
    def __repr__(self):
        return f'<ApiConnection {self.name}>'

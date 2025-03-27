from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, URL, Optional
from models import User, Invitation, Organization
from datetime import datetime, timedelta

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class OrganizationRegistrationForm(FlaskForm):
    organization_name = StringField('Organization Name', validators=[DataRequired(), Length(max=100)])
    organization_description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    industry = StringField('Industry', validators=[Optional(), Length(max=100)])
    
    username = StringField('Admin Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Admin Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register Organization')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose another one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use another one.')
            
    def validate_organization_name(self, organization_name):
        org = Organization.query.filter_by(name=organization_name.data).first()
        if org:
            raise ValidationError('Organization name already taken. Please choose another one.')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose another one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use another one.')

class UploadHCPDataForm(FlaskForm):
    file = FileField('Upload CSV File', validators=[DataRequired()])
    submit = SubmitField('Upload and Tag')

class HCPTagSelectionForm(FlaskForm):
    hcp = SelectField('Select HCP', validators=[DataRequired()])
    submit = SubmitField('Generate Content')

class ContentCraftForm(FlaskForm):
    hcp = SelectField('Select HCP', validators=[DataRequired()])
    content = TextAreaField('Generated Content', render_kw={'readonly': True})
    submit = SubmitField('Save Content')

class EngageOpticForm(FlaskForm):
    hcp = SelectField('Select HCP', validators=[DataRequired()])
    content = SelectField('Select Content', validators=[DataRequired()])
    submit = SubmitField('Generate Campaign Plan')

class InsightLensForm(FlaskForm):
    campaign = SelectField('Select Campaign', validators=[DataRequired()])
    submit = SubmitField('Generate Analytics')

# Forms for role-based functionality

class AdminInviteForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    # Admins can only invite managers (role is fixed)
    submit = SubmitField('Invite Manager')
    
    def validate_email(self, email):
        # Check if email is already registered
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered in the system.')
        
        # Check if there's already a pending invitation
        invitation = Invitation.query.filter_by(email=email.data, used=False).first()
        if invitation and not invitation.is_expired():
            raise ValidationError('An invitation has already been sent to this email.')
            
class ManagerInviteForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    # Managers can only invite agents (role is fixed)
    submit = SubmitField('Invite Sales Agent')
    
    def validate_email(self, email):
        # Check if email is already registered
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered in the system.')
        
        # Check if there's already a pending invitation
        invitation = Invitation.query.filter_by(email=email.data, used=False).first()
        if invitation and not invitation.is_expired():
            raise ValidationError('An invitation has already been sent to this email.')

class AcceptInvitationForm(FlaskForm):
    username = StringField('Choose Username', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Choose Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    token = HiddenField('Invitation Token', validators=[DataRequired()])
    submit = SubmitField('Create Account')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose another one.')

class ApiConnectionForm(FlaskForm):
    name = SelectField('API Service', 
                      choices=[('VEEVA', 'VEEVA CRM'), 
                               ('Salesforce', 'Salesforce'), 
                               ('Slack', 'Slack'), 
                               ('Oncore', 'Oncore'),
                               ('Custom', 'Custom API')],
                      validators=[DataRequired()])
    custom_name = StringField('Custom API Name', validators=[Optional(), Length(max=50)])
    api_key = StringField('API Key', validators=[DataRequired(), Length(max=256)])
    api_secret = StringField('API Secret (if required)', validators=[Optional(), Length(max=256)])
    base_url = StringField('API Base URL (if required)', 
                          validators=[Optional(), URL(message='Please enter a valid URL')])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save API Connection')

class AdminUserManagementForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', 
                      choices=[('admin', 'Administrator'), 
                               ('manager', 'Manager'), 
                               ('agent', 'Agent')],
                      validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Update User')
    
class AssetUploadForm(FlaskForm):
    file = FileField('Upload File', validators=[
        FileRequired(),
        FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'pdf', 'doc', 'docx', 
                     'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'mp4', 'webm', 'mov', 'mp3', 'wav', 'ogg'], 
                    'File type not allowed')
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    tags = StringField('Tags (comma-separated)', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Upload Asset')
    
    def __init__(self, *args, **kwargs):
        super(AssetUploadForm, self).__init__(*args, **kwargs)
        self.submit.label.text = 'Upload Asset'  # Set initial label

from flask import render_template, redirect, url_for, flash, request, session, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import csrf  # Import csrf from app
import pandas as pd
import os
import random
import json
import uuid
from io import StringIO
from datetime import datetime, timedelta
from functools import wraps
import logging

from app import db
from models import User, HCP, Asset, Content, ContentAsset, Campaign, Analytics, Invitation, ApiConnection, Organization

# Helper function to ensure session progress tracking exists
def ensure_progress_tracking():
    """Ensure session progress tracking is initialized"""
    if 'progress' not in session:
        session['progress'] = ['homepage']
        if current_user.is_authenticated:
            session['progress'].append('login')
        session.modified = True
from forms import (
    LoginForm, RegistrationForm, UploadHCPDataForm, 
    HCPTagSelectionForm, ContentCraftForm, EngageOpticForm, InsightLensForm,
    AdminInviteForm, ManagerInviteForm, AcceptInvitationForm, ApiConnectionForm, AdminUserManagementForm,
    AssetUploadForm, OrganizationRegistrationForm
)
from utils import (
    tag_hcps, load_content_blocks, generate_content, 
    mlr_prescreen, select_channel, select_timing, generate_mock_analytics
)
from asset_utils import (
    process_uploaded_file, get_user_assets, delete_asset,
    generate_asset_preview_html
)

def register_routes(app):
    
    # Register filters
    @app.template_filter('date')
    def date_filter(value, format='%Y-%m-%d %H:%M'):
        if value is None:
            return ""
        return value.strftime(format)
        
    # Theme and language routes
    @app.route('/set_theme/<theme>', methods=['GET', 'POST'])
    @csrf.exempt
    def set_theme(theme):
        if theme in ['light', 'dark']:
            session['theme'] = theme
            # Force session save
            session.modified = True
        return jsonify(success=True)
    
    @app.route('/set_language/<lang>')
    def set_language(lang):
        if lang in ['en', 'ja']:
            session['language'] = lang
        return redirect(request.referrer or url_for('homepage'))
    
    # Role-based access control decorators
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.is_admin():
                flash('Access denied. Admin privileges required.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
        
    def manager_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not (current_user.is_admin() or current_user.is_manager()):
                flash('Access denied. Manager privileges required.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function

    @app.route('/')
    def homepage():
        return render_template('homepage.html')
        
    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            
            if user and user.check_password(form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                # Track user progress
                session['progress'] = ['homepage', 'login']
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Login unsuccessful. Please check username and password', 'danger')
                
        return render_template('login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        # Only allow registration via invitation token
        token = request.args.get('token')
        
        if not token:
            # If no token, redirect to organization registration
            flash('Direct registration is not allowed. Please register an organization or use an invitation link.', 'info')
            return redirect(url_for('register_organization'))
            
        # Find the invitation
        invitation = Invitation.query.filter_by(token=token, used=False).first()
        if not invitation or invitation.is_expired():
            flash('Invalid or expired invitation token.', 'danger')
            return redirect(url_for('login'))
            
        form = RegistrationForm()
        
        if form.validate_on_submit():
            try:
                # Use role from invitation
                role = invitation.role
                invited_by = invitation.sender_id
                
                # Create the user with the invitation's organization
                user = User(
                    username=form.username.data, 
                    email=form.email.data,
                    role=role,
                    invited_by=invited_by,
                    organization_id=invitation.organization_id
                )
                    
                user.set_password(form.password.data)
                
                # Mark invitation as used
                invitation.used = True
                
                db.session.add(user)
                db.session.add(invitation)
                db.session.commit()
                
                flash(f'Your account has been created as a {role}! You can now log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error creating user: {str(e)}")
                flash(f'Error creating account: {str(e)}', 'danger')
                
        return render_template('login.html', form=form, register=True, is_first_user=False, invitation_token=token)
    
    @app.route('/register_organization', methods=['GET', 'POST'])
    def register_organization():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        form = OrganizationRegistrationForm()
        
        if form.validate_on_submit():
            # Create the organization
            organization = Organization(name=form.name.data)
            db.session.add(organization)
            db.session.flush()  # Flush to get the organization ID
            
            # Create the admin user
            user = User(
                username=form.username.data,
                email=form.email.data,
                role='admin',
                organization_id=organization.id
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Organization registered successfully! You can now log in as the admin.', 'success')
            return redirect(url_for('login'))
            
        return render_template('auth/register_organization.html', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        # Clear session
        session.clear()
        return redirect(url_for('homepage'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Ensure progress tracking is initialized
        ensure_progress_tracking()
        
        if 'dashboard' not in session['progress']:
            session['progress'].append('dashboard')
            session.modified = True
            
        return render_template('dashboard.html')

    @app.route('/meditag', methods=['GET', 'POST'])
    @login_required
    def meditag():
        # Ensure progress tracking is initialized
        ensure_progress_tracking()
        
        form = UploadHCPDataForm()
        
        if form.validate_on_submit():
            # Handle file upload
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(request.url)
                
            if file:
                # Read CSV file
                try:
                    contents = file.stream.read().decode('utf-8')
                    data = pd.read_csv(StringIO(contents))
                    
                    # Process HCP data and tag them
                    tagged_data = tag_hcps(data)
                    
                    # Save to database
                    for _, row in tagged_data.iterrows():
                        hcp = HCP(
                            user_id=current_user.id,
                            organization_id=current_user.organization_id,
                            hcp_id=row['hcp_id'],
                            name=row.get('name', f"Dr. {row['hcp_id']}"),
                            specialty=row.get('specialty', 'General'),
                            prescribing_pattern=row.get('prescribing_pattern', 0),
                            engagement_score=row.get('engagement_score', 0),
                            tag=row['tag']
                        )
                        db.session.add(hcp)
                    
                    db.session.commit()
                    flash('HCP data uploaded and tagged successfully!', 'success')
                    
                    # Track user progress
                    if 'meditag' not in session['progress']:
                        session['progress'].append('meditag')
                        session.modified = True
                        
                    return redirect(url_for('meditag'))
                    
                except Exception as e:
                    flash(f'Error processing file: {str(e)}', 'danger')
                    return redirect(request.url)
        
        # Get existing HCPs for current user's organization
        hcps = HCP.query.filter_by(organization_id=current_user.organization_id).all()
        
        return render_template('meditag.html', form=form, hcps=hcps)

    @app.route('/contentcraft', methods=['GET', 'POST'])
    @login_required
    def contentcraft():
        # Ensure progress tracking is initialized
        ensure_progress_tracking()
        
        # Get HCPs for the current user's organization
        hcps = HCP.query.filter_by(organization_id=current_user.organization_id).all()
        
        if not hcps:
            flash('Please upload and tag HCPs first in MediTag', 'warning')
            return redirect(url_for('meditag'))
        
        # Create form and populate HCP dropdown
        form = ContentCraftForm()
        form.hcp.choices = [(str(hcp.id), f"{hcp.name} ({hcp.tag})") for hcp in hcps]
        
        if request.method == 'POST':
            # Generate content for selected HCP
            hcp_id = int(request.form['hcp'])
            hcp = HCP.query.get_or_404(hcp_id)
            
            # Load content blocks and generate content
            content_blocks = load_content_blocks()
            generated_content = generate_content(hcp.tag, hcp.name, content_blocks)
            
            # Check for risky phrases
            flags = mlr_prescreen(generated_content)
            
            # Save content to database
            content = Content(
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                hcp_id=hcp_id,
                content_text=generated_content,
                status='Flagged' if flags else 'Approved'
            )
            
            if flags:
                content.set_flags(flags)
                
            db.session.add(content)
            db.session.commit()
            
            flash('Content generated and saved!', 'success')
            
            # Track user progress
            if 'contentcraft' not in session['progress']:
                session['progress'].append('contentcraft')
                session.modified = True
                
            return redirect(url_for('contentcraft'))
        
        # Get existing content for current user's organization
        contents = Content.query.filter_by(organization_id=current_user.organization_id).all()
        
        return render_template('contentcraft.html', form=form, contents=contents)

    @app.route('/engageoptic', methods=['GET', 'POST'])
    @login_required
    def engageoptic():
        # Ensure progress tracking is initialized
        ensure_progress_tracking()
        
        # Get contents for the current user's organization
        contents = Content.query.filter_by(organization_id=current_user.organization_id).all()
        
        if not contents:
            flash('Please generate content first in ContentCraft', 'warning')
            return redirect(url_for('contentcraft'))
        
        # Create form and populate content dropdown
        form = EngageOpticForm()
        
        # Get HCPs for populating dropdown
        hcps = HCP.query.filter_by(organization_id=current_user.organization_id).all()
        form.hcp.choices = [(str(hcp.id), f"{hcp.name} ({hcp.tag})") for hcp in hcps]
        
        # Get content for populating dropdown
        contents = Content.query.filter_by(organization_id=current_user.organization_id).all()
        form.content.choices = [(str(content.id), f"Content {content.id} for {content.hcp.name}") for content in contents]
        
        if form.validate_on_submit():
            hcp_id = int(form.hcp.data)
            content_id = int(form.content.data)
            
            hcp = HCP.query.get_or_404(hcp_id)
            content = Content.query.get_or_404(content_id)
            
            # Select channel and timing
            channel = select_channel(hcp.tag)
            timing = select_timing(channel)
            
            # Create campaign
            campaign = Campaign(
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                content_id=content_id,
                channel=channel,
                timing=timing,
                status='Planned'
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            flash(f'Campaign plan created! Channel: {channel}, Timing: {timing}', 'success')
            
            # Track user progress
            if 'engageoptic' not in session['progress']:
                session['progress'].append('engageoptic')
                session.modified = True
                
            return redirect(url_for('engageoptic'))
        
        # Get existing campaigns for current user's organization
        campaigns = Campaign.query.filter_by(organization_id=current_user.organization_id).all()
        
        return render_template('engageoptic.html', form=form, campaigns=campaigns)

    @app.route('/insightlens', methods=['GET', 'POST'])
    @login_required
    def insightlens():
        # Ensure progress tracking is initialized
        ensure_progress_tracking()
        
        # Get campaigns for the current user's organization
        campaigns = Campaign.query.filter_by(organization_id=current_user.organization_id).all()
        
        if not campaigns:
            flash('Please create campaigns first in EngageOptic', 'warning')
            return redirect(url_for('engageoptic'))
        
        # Check if we need to generate mock analytics
        for campaign in campaigns:
            if not campaign.analytics:
                # Generate mock analytics
                mock_analytics = generate_mock_analytics(campaign.id)
                db.session.add(mock_analytics)
                db.session.commit()
        
        # Get analytics data for visualization
        analytics_data = []
        for campaign in campaigns:
            if campaign.analytics:
                analytics = campaign.analytics[0]  # Take the first analytics record
                analytics_data.append({
                    'campaign_id': campaign.id,
                    'channel': campaign.channel,
                    'open_rate': analytics.open_rate,
                    'response_rate': analytics.response_rate,
                    'compliance_status': analytics.compliance_status,
                    'flags_resolved': analytics.flags_resolved
                })
        
        # Track user progress
        if 'insightlens' not in session['progress']:
            session['progress'].append('insightlens')
            session.modified = True
            
        return render_template('insightlens.html', analytics_data=json.dumps(analytics_data), campaigns=campaigns)

    # Asset Management Routes
    @app.route('/assets', methods=['GET'])
    @login_required
    def assets_dashboard():
        """Main dashboard for asset management"""
        # Ensure progress tracking is initialized
        ensure_progress_tracking()
        
        # Get all user assets
        assets = get_user_assets(current_user.id)
        
        # Filter by type if requested
        asset_type = request.args.get('type')
        if asset_type and asset_type in ['image', 'document', 'video', 'audio']:
            assets = [a for a in assets if a.file_type == asset_type]
            
        # Track user progress
        if 'assets' not in session['progress']:
            session['progress'].append('assets')
            session.modified = True
            
        return render_template('assets.html', assets=assets)
        
    @app.route('/assets/upload', methods=['GET', 'POST'])
    @login_required
    def upload_asset():
        """Handle asset uploads"""
        # Ensure progress tracking is initialized
        ensure_progress_tracking()
        
        form = AssetUploadForm()
        
        if form.validate_on_submit():
            file = form.file.data
            description = form.description.data
            tags = form.tags.data
            
            # Process and save the file
            asset = process_uploaded_file(file, current_user.id, description, tags)
            
            if asset:
                flash('File uploaded successfully!', 'success')
                return redirect(url_for('assets_dashboard'))
            else:
                flash('Error uploading file. Please ensure the file type is allowed and file size is less than 10MB.', 'danger')
                
        return render_template('upload_asset.html', form=form)
        
    @app.route('/assets/<int:asset_id>/delete', methods=['POST'])
    @login_required
    def delete_asset_route(asset_id):
        """Delete an asset"""
        success = delete_asset(asset_id, current_user.id)
        
        if success:
            flash('Asset deleted successfully.', 'success')
        else:
            flash('Error deleting asset.', 'danger')
            
        return redirect(url_for('assets_dashboard'))
        
    @app.route('/assets/<int:asset_id>/view')
    @login_required
    def view_asset(asset_id):
        """View a single asset"""
        # Ensure progress tracking is initialized
        ensure_progress_tracking()
        
        asset = Asset.query.filter_by(id=asset_id, user_id=current_user.id).first_or_404()
        return render_template('view_asset.html', asset=asset)
        
    @app.route('/api/assets', methods=['GET'])
    @login_required
    def api_get_assets():
        """API endpoint to get assets for AJAX calls"""
        # Ensure progress tracking is initialized
        ensure_progress_tracking()
        
        assets = get_user_assets(current_user.id)
        
        # Filter by type if requested
        asset_type = request.args.get('type')
        if asset_type:
            assets = [a for a in assets if a.file_type == asset_type]
            
        # Format for JSON response
        assets_data = []
        for asset in assets:
            assets_data.append({
                'id': asset.id,
                'name': asset.original_filename,
                'type': asset.file_type,
                'url': asset.file_url,
                'preview_html': generate_asset_preview_html(asset)
            })
            
        return jsonify(assets_data)
        
    @app.route('/api/assets/<int:asset_id>/link', methods=['POST'])
    @login_required
    def api_link_asset_to_content(asset_id):
        """API endpoint to link an asset to content"""
        content_id = request.json.get('content_id')
        position = request.json.get('position', 0)
        alt_text = request.json.get('alt_text', '')
        
        if not content_id:
            return jsonify({'success': False, 'message': 'Content ID is required'}), 400
            
        # Check if asset and content exist and belong to user's organization
        asset = Asset.query.filter_by(id=asset_id, user_id=current_user.id).first()
        content = Content.query.filter_by(id=content_id, organization_id=current_user.organization_id).first()
        
        if not asset or not content:
            return jsonify({'success': False, 'message': 'Asset or content not found'}), 404
            
        # Create the link
        content_asset = ContentAsset(
            content_id=content_id,
            asset_id=asset_id,
            position=position,
            alt_text=alt_text
        )
        
        db.session.add(content_asset)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Asset linked to content successfully'})
        
    @app.route('/api/assets/<int:asset_id>/unlink', methods=['POST'])
    @login_required
    def api_unlink_asset_from_content(asset_id):
        """API endpoint to unlink an asset from content"""
        content_id = request.json.get('content_id')
        
        if not content_id:
            return jsonify({'success': False, 'message': 'Content ID is required'}), 400
            
        # Find the link
        content_asset = ContentAsset.query.filter_by(
            content_id=content_id,
            asset_id=asset_id
        ).first()
        
        if not content_asset:
            return jsonify({'success': False, 'message': 'Asset not linked to this content'}), 404
            
        # Delete the link
        db.session.delete(content_asset)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Asset unlinked from content successfully'})

    @app.context_processor
    def utility_processor():
        def get_progress():
            return session.get('progress', [])
            
        def get_progress_percentage():
            progress = session.get('progress', [])
            total_steps = 6  # homepage, login, dashboard, meditag, contentcraft, engageoptic, insightlens
            return min(100, int((len(progress) / total_steps) * 100))
            
        return dict(get_progress=get_progress, get_progress_percentage=get_progress_percentage)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_code=404, message="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', error_code=500, message="Internal server error"), 500
        
    # Admin routes
    @app.route('/admin')
    @login_required
    @admin_required
    def admin_dashboard():
        ensure_progress_tracking()
        
        # Get user counts by role
        admin_count = User.query.filter_by(role='admin', organization_id=current_user.organization_id).count()
        manager_count = User.query.filter_by(role='manager', organization_id=current_user.organization_id).count()
        agent_count = User.query.filter_by(role='agent', organization_id=current_user.organization_id).count()
        
        # Get API connection counts for current organization
        active_api_count = ApiConnection.query.filter_by(is_active=True, organization_id=current_user.organization_id).count()
        inactive_api_count = ApiConnection.query.filter_by(is_active=False, organization_id=current_user.organization_id).count()
        
        # Check connections to external services for current organization
        veeva_connected = ApiConnection.query.filter_by(name='VEEVA', is_active=True, organization_id=current_user.organization_id).first() is not None
        salesforce_connected = ApiConnection.query.filter_by(name='Salesforce', is_active=True, organization_id=current_user.organization_id).first() is not None
        
        # Mock recent activity for demo
        recent_activity = [
            {
                'user': 'system',
                'action': 'System started',
                'time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        # Stats dictionary
        stats = {
            'admin_count': admin_count,
            'manager_count': manager_count,
            'agent_count': agent_count,
            'active_api_count': active_api_count,
            'inactive_api_count': inactive_api_count,
            'veeva_connected': veeva_connected,
            'salesforce_connected': salesforce_connected,
            'last_checked': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template('admin/dashboard.html', stats=stats, recent_activity=recent_activity)
        
    @app.route('/admin/users', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_user_management():
        ensure_progress_tracking()
        
        # Get all users in the current organization
        users = User.query.filter_by(organization_id=current_user.organization_id).all()
        
        # Get pending invitations for current organization with debug logging
        invitations = Invitation.query.filter_by(used=False, organization_id=current_user.organization_id).all()
        print(f"Found {len(invitations)} pending invitations for organization {current_user.organization_id}")
        
        # Debug information about each invitation
        for inv in invitations:
            print(f"Invitation: {inv.id}, Email: {inv.email}, Role: {inv.role}, Sender: {inv.sender_id}, Used: {inv.used}")
            try:
                print(f"Sender username: {inv.sender.username}")
            except Exception as e:
                print(f"Error getting sender username: {str(e)}")
        
        # Create forms
        invite_form = AdminInviteForm()
        user_form = AdminUserManagementForm()
        
        return render_template('admin/user_management.html', 
                              users=users, 
                              invitations=invitations, 
                              invite_form=invite_form, 
                              user_form=user_form)
                              
    @app.route('/admin/invite', methods=['POST'])
    @login_required
    @admin_required
    def admin_invite_user():
        form = AdminInviteForm()
        
        if form.validate_on_submit():
            # Generate a unique token
            token = str(uuid.uuid4())
            
            # Create an invitation (admins can only invite managers)
            invitation = Invitation(
                email=form.email.data,
                token=token,
                role='manager',  # Role is fixed to manager for admin invitations
                sender_id=current_user.id,
                organization_id=current_user.organization_id,
                expires_at=datetime.utcnow() + timedelta(days=7)  # Expires in 7 days
            )
            
            db.session.add(invitation)
            db.session.commit()
            
            # Send invitation email
            invite_url = url_for('accept_invitation', token=token, _external=True)
            organization = Organization.query.get(current_user.organization_id)
            org_name = organization.name if organization else "Vivvo.ai"
            
            from email_service import send_invitation_email
            email_sent = send_invitation_email(
                to_email=form.email.data,
                invitation_link=invite_url,
                role='manager',
                organization_name=org_name
            )
            
            if email_sent:
                flash(f'Invitation sent to {form.email.data}', 'success')
            else:
                # Email service failed but invitation is still created
                flash(f'Invitation created for {form.email.data}, but email sending failed. Manual URL: {invite_url}', 'warning')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'danger')
                    
        return redirect(url_for('admin_user_management'))
        
    @app.route('/admin/resend-invitation', methods=['POST'])
    @login_required
    @admin_required
    def admin_resend_invitation():
        invitation_id = request.form.get('invitation_id')
        
        if not invitation_id:
            flash('Invalid invitation ID', 'danger')
            return redirect(url_for('admin_user_management'))
            
        invitation = Invitation.query.get_or_404(invitation_id)
        
        # Update expiration date
        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        db.session.commit()
        
        # Send invitation email
        invite_url = url_for('accept_invitation', token=invitation.token, _external=True)
        organization = Organization.query.get(current_user.organization_id)
        org_name = organization.name if organization else "Vivvo.ai"
        
        from email_service import send_invitation_email
        email_sent = send_invitation_email(
            to_email=invitation.email,
            invitation_link=invite_url,
            role=invitation.role,
            organization_name=org_name
        )
        
        if email_sent:
            flash(f'Invitation resent to {invitation.email}', 'success')
        else:
            # Email service failed but invitation is still updated
            flash(f'Invitation updated for {invitation.email}, but email sending failed. Manual URL: {invite_url}', 'warning')
            
        return redirect(url_for('admin_user_management'))
        
    @app.route('/admin/cancel-invitation', methods=['POST'])
    @login_required
    @admin_required
    def admin_cancel_invitation():
        invitation_id = request.form.get('invitation_id')
        
        if not invitation_id:
            flash('Invalid invitation ID', 'danger')
            return redirect(url_for('admin_user_management'))
            
        invitation = Invitation.query.get_or_404(invitation_id)
        
        db.session.delete(invitation)
        db.session.commit()
        
        flash(f'Invitation to {invitation.email} cancelled', 'success')
        return redirect(url_for('admin_user_management'))
        
    @app.route('/admin/update-user', methods=['POST'])
    @login_required
    @admin_required
    def admin_update_user():
        user_id = request.form.get('user_id')
        
        if not user_id:
            flash('Invalid user ID', 'danger')
            return redirect(url_for('admin_user_management'))
            
        user = User.query.get_or_404(user_id)
        form = AdminUserManagementForm()
        
        if form.validate_on_submit():
            user.username = form.username.data
            user.email = form.email.data
            user.role = form.role.data
            user.is_active = form.is_active.data
            
            db.session.commit()
            
            flash(f'User {user.username} updated successfully', 'success')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'danger')
                    
        return redirect(url_for('admin_user_management'))
        
    @app.route('/admin/api-connections', methods=['GET'])
    @login_required
    @admin_required
    def admin_api_connections():
        ensure_progress_tracking()
        
        # Get API connections for current organization
        api_connections = ApiConnection.query.filter_by(organization_id=current_user.organization_id).all()
        
        # Create form
        api_form = ApiConnectionForm()
        
        return render_template('admin/api_connections.html', 
                              api_connections=api_connections, 
                              api_form=api_form)
                              
    @app.route('/admin/add-api-connection', methods=['POST'])
    @login_required
    @admin_required
    def admin_add_api_connection():
        ensure_progress_tracking()
        
        form = ApiConnectionForm()
        
        if form.validate_on_submit():
            name = form.name.data
            custom_name = form.custom_name.data if name == 'Custom' else None
            
            connection = ApiConnection(
                name=name,
                custom_name=custom_name,
                api_key=form.api_key.data,
                api_secret=form.api_secret.data,
                base_url=form.base_url.data,
                is_active=form.is_active.data,
                created_by=current_user.id,
                organization_id=current_user.organization_id
            )
            
            db.session.add(connection)
            db.session.commit()
            
            service_name = custom_name if name == 'Custom' else name
            flash(f'Connection to {service_name} added successfully', 'success')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'danger')
                    
        return redirect(url_for('admin_api_connections'))
        
    @app.route('/admin/update-api-connection', methods=['POST'])
    @login_required
    @admin_required
    def admin_update_api_connection():
        connection_id = request.form.get('connection_id')
        
        if not connection_id:
            flash('Invalid connection ID', 'danger')
            return redirect(url_for('admin_api_connections'))
            
        connection = ApiConnection.query.get_or_404(connection_id)
        form = ApiConnectionForm()
        
        if form.validate_on_submit():
            connection.name = form.name.data
            connection.custom_name = form.custom_name.data if form.name.data == 'Custom' else None
            connection.api_key = form.api_key.data
            connection.api_secret = form.api_secret.data
            connection.base_url = form.base_url.data
            connection.is_active = form.is_active.data
            connection.last_updated = datetime.utcnow()
            
            db.session.commit()
            
            service_name = connection.custom_name if connection.name == 'Custom' else connection.name
            flash(f'Connection to {service_name} updated successfully', 'success')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'danger')
                    
        return redirect(url_for('admin_api_connections'))
        
    @app.route('/admin/delete-api-connection', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_api_connection():
        connection_id = request.form.get('connection_id')
        
        if not connection_id:
            flash('Invalid connection ID', 'danger')
            return redirect(url_for('admin_api_connections'))
            
        connection = ApiConnection.query.get_or_404(connection_id)
        
        service_name = connection.custom_name if connection.name == 'Custom' else connection.name
        
        db.session.delete(connection)
        db.session.commit()
        
        flash(f'Connection to {service_name} deleted successfully', 'success')
        return redirect(url_for('admin_api_connections'))
        
    @app.route('/admin/toggle-api-connection', methods=['POST'])
    @login_required
    @admin_required
    def admin_toggle_api_connection():
        data = request.get_json()
        
        if not data or 'connection_id' not in data or 'is_active' not in data:
            return jsonify({'success': False, 'message': 'Invalid request data'})
            
        connection_id = data['connection_id']
        is_active = data['is_active']
        
        connection = ApiConnection.query.get(connection_id)
        
        if not connection:
            return jsonify({'success': False, 'message': 'Connection not found'})
            
        connection.is_active = is_active
        connection.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    # Manager routes
    @app.route('/manager/invite', methods=['GET', 'POST'])
    @login_required
    @manager_required
    def manager_invite_user():
        form = ManagerInviteForm()
        
        if form.validate_on_submit():
            # Generate a unique token
            token = str(uuid.uuid4())
            
            # Create an invitation (managers can only invite agents)
            invitation = Invitation(
                email=form.email.data,
                token=token,
                role='agent',  # Role is fixed to agent for manager invitations
                sender_id=current_user.id,
                organization_id=current_user.organization_id,
                expires_at=datetime.utcnow() + timedelta(days=7)  # Expires in 7 days
            )
            
            db.session.add(invitation)
            db.session.commit()
            
            # Send invitation email
            invite_url = url_for('accept_invitation', token=token, _external=True)
            organization = Organization.query.get(current_user.organization_id)
            org_name = organization.name if organization else "Vivvo.ai"
            
            from email_service import send_invitation_email
            email_sent = send_invitation_email(
                to_email=form.email.data,
                invitation_link=invite_url,
                role='agent',
                organization_name=org_name
            )
            
            if email_sent:
                flash(f'Invitation sent to {form.email.data}', 'success')
            else:
                # Email service failed but invitation is still created
                flash(f'Invitation created for {form.email.data}, but email sending failed. Manual URL: {invite_url}', 'warning')
                
            return redirect(url_for('manager_invite_user'))
            
        # Get pending invitations sent by this manager
        invitations = Invitation.query.filter_by(sender_id=current_user.id, used=False).all()
        
        # Get team members (users invited by this manager)
        team = User.query.filter_by(invited_by=current_user.id).all()
        
        return render_template('manager/invite.html', form=form, invitations=invitations, team=team)
        
    @app.route('/manager/resend-invitation', methods=['POST'])
    @login_required
    @manager_required
    def manager_resend_invitation():
        invitation_id = request.form.get('invitation_id')
        
        if not invitation_id:
            flash('Invalid invitation ID', 'danger')
            return redirect(url_for('manager_invite_user'))
            
        invitation = Invitation.query.get_or_404(invitation_id)
        
        # Check if this invitation belongs to the current manager
        if invitation.sender_id != current_user.id:
            flash('Access denied. You can only manage your own invitations.', 'danger')
            return redirect(url_for('manager_invite_user'))
            
        # Update expiration date
        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        db.session.commit()
        
        # Send invitation email
        invite_url = url_for('accept_invitation', token=invitation.token, _external=True)
        organization = Organization.query.get(current_user.organization_id)
        org_name = organization.name if organization else "Vivvo.ai"
        
        from email_service import send_invitation_email
        email_sent = send_invitation_email(
            to_email=invitation.email,
            invitation_link=invite_url,
            role=invitation.role,
            organization_name=org_name
        )
        
        if email_sent:
            flash(f'Invitation resent to {invitation.email}', 'success')
        else:
            # Email service failed but invitation is still updated
            flash(f'Invitation updated for {invitation.email}, but email sending failed. Manual URL: {invite_url}', 'warning')
            
        return redirect(url_for('manager_invite_user'))
        
    @app.route('/manager/cancel-invitation', methods=['POST'])
    @login_required
    @manager_required
    def manager_cancel_invitation():
        invitation_id = request.form.get('invitation_id')
        
        if not invitation_id:
            flash('Invalid invitation ID', 'danger')
            return redirect(url_for('manager_invite_user'))
            
        invitation = Invitation.query.get_or_404(invitation_id)
        
        # Check if this invitation belongs to the current manager
        if invitation.sender_id != current_user.id:
            flash('Access denied. You can only manage your own invitations.', 'danger')
            return redirect(url_for('manager_invite_user'))
            
        db.session.delete(invitation)
        db.session.commit()
        
        flash(f'Invitation to {invitation.email} cancelled', 'success')
        return redirect(url_for('manager_invite_user'))

    # Invitation routes
    @app.route('/invitation/<token>', methods=['GET', 'POST'])
    def accept_invitation(token):
        # Find the invitation
        invitation = Invitation.query.filter_by(token=token).first()
        
        # Check if invitation exists and is valid
        invitation_valid = invitation and not invitation.used and not invitation.is_expired()
        
        form = AcceptInvitationForm()
        
        if invitation_valid and form.validate_on_submit():
            # Create a new user from invitation
            user = User(
                username=form.username.data,
                email=invitation.email,
                role=invitation.role,
                invited_by=invitation.sender_id,
                organization_id=invitation.organization_id
            )
            user.set_password(form.password.data)
            
            # Mark invitation as used
            invitation.used = True
            
            db.session.add(user)
            db.session.commit()
            
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        return render_template('auth/invitation.html', 
                              form=form, 
                              invitation=invitation if invitation_valid else None, 
                              invitation_valid=invitation_valid,
                              token=token)

import os
from werkzeug.utils import secure_filename
from flask import current_app
from models import Asset, db

def process_uploaded_file(file, user_id):
    """Process and save an uploaded file."""
    if not file:
        return None
        
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Save file
    file.save(filepath)
    
    # Create asset record
    asset = Asset(
        filename=filename,
        filepath=filepath,
        user_id=user_id
    )
    db.session.add(asset)
    db.session.commit()
    
    return asset

def get_user_assets(user_id):
    """Get all assets for a user."""
    return Asset.query.filter_by(user_id=user_id).all()

def delete_asset(asset_id, user_id):
    """Delete an asset."""
    asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first()
    if asset:
        try:
            # Delete file
            if os.path.exists(asset.filepath):
                os.remove(asset.filepath)
            
            # Delete record
            db.session.delete(asset)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False
    return False

def generate_asset_preview_html(asset):
    """Generate HTML preview for an asset."""
    if not asset:
        return ""
        
    file_ext = os.path.splitext(asset.filename)[1].lower()
    
    # Image preview
    if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
        return f'<img src="/static/uploads/{asset.filename}" class="img-fluid" alt="{asset.filename}">'
    
    # PDF preview (link)
    elif file_ext == '.pdf':
        return f'<a href="/static/uploads/{asset.filename}" target="_blank" class="btn btn-primary">View PDF</a>'
    
    # Default - download link
    return f'<a href="/static/uploads/{asset.filename}" download class="btn btn-primary">Download {asset.filename}</a>' 
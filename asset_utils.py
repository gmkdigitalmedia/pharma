"""
Asset management utilities for Xupra

This module handles asset uploads, validation, and processing:
- File uploads for images and documents
- Processing uploaded assets for use in content generation
- Validation of file types and sizes
"""

import os
import secrets
import mimetypes
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import logging

from models import Asset
from app import db

# Configuration
UPLOAD_FOLDER = 'static/uploads/assets'
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'},
    'document': {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt'},
    'video': {'mp4', 'webm', 'mov'},
    'audio': {'mp3', 'wav', 'ogg'}
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if the file has an allowed extension"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return True, file_type
    
    return False, None


def get_file_type(filename):
    """Determine file type from extension"""
    if '.' not in filename:
        return 'unknown'
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    
    return 'unknown'


def process_uploaded_file(file, user_id, description=None, tags=None, organization_id=None):
    """
    Process an uploaded file and save it to the filesystem
    
    Args:
        file: The uploaded file object from Flask's request.files
        user_id: ID of the user uploading the file
        description: Optional description for the asset
        tags: Optional comma-separated tags for the asset
        organization_id: Optional organization ID for multi-tenant isolation
        
    Returns:
        Asset: The created Asset object or None if processing failed
    """
    if not file or file.filename == '':
        logging.error("No file selected")
        return None
    
    # Validate file
    is_allowed, file_type = allowed_file(file.filename)
    if not is_allowed:
        logging.error(f"File type not allowed: {file.filename}")
        return None
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > MAX_FILE_SIZE:
        logging.error(f"File too large: {file_size} bytes")
        return None
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    unique_id = secrets.token_hex(4)
    filename_parts = original_filename.rsplit('.', 1)
    new_filename = f"{filename_parts[0]}_{timestamp}_{unique_id}.{filename_parts[1]}"
    file_path = os.path.join(UPLOAD_FOLDER, new_filename)
    
    # Save file
    try:
        file.save(file_path)
        logging.info(f"Saved file to {file_path}")
        
        # Process image if needed
        if file_type == 'image' and filename_parts[1].lower() in ['jpg', 'jpeg', 'png']:
            try:
                # Create thumbnail or optimize
                optimize_image(file_path)
            except Exception as e:
                logging.error(f"Error processing image: {str(e)}")
        
        # Create asset record
        mime_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
        asset = Asset(
            user_id=user_id,
            organization_id=organization_id,
            original_filename=original_filename,
            stored_filename=file_path,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            description=description,
            tags=tags
        )
        
        db.session.add(asset)
        db.session.commit()
        
        return asset
    except Exception as e:
        logging.error(f"Error saving file: {str(e)}")
        # Clean up if file was saved but record creation failed
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return None


def optimize_image(file_path, max_width=1200):
    """Optimize an image for web use"""
    try:
        img = Image.open(file_path)
        
        # Only resize if larger than max_width
        if img.width > max_width:
            # Calculate new height to maintain aspect ratio
            wpercent = max_width / float(img.width)
            hsize = int(float(img.height) * float(wpercent))
            img = img.resize((max_width, hsize), Image.LANCZOS)
            
        # Save with optimized settings
        img.save(file_path, optimize=True, quality=85)
        logging.info(f"Optimized image: {file_path}")
    except Exception as e:
        logging.error(f"Failed to optimize image: {str(e)}")
        # Don't raise, just log the error


def delete_asset(asset_id, user_id=None):
    """
    Delete an asset and its file
    
    Args:
        asset_id: ID of the asset to delete
        user_id: Optional user ID for permission check
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        query = Asset.query.filter_by(id=asset_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
            
        asset = query.first()
        
        if not asset:
            return False
        
        # Delete file
        if os.path.exists(asset.stored_filename):
            os.remove(asset.stored_filename)
            
        # Delete record
        db.session.delete(asset)
        db.session.commit()
        
        return True
    except Exception as e:
        logging.error(f"Error deleting asset: {str(e)}")
        db.session.rollback()
        return False


def get_user_assets(user_id, file_type=None, tag=None, limit=50):
    """
    Get a list of assets for a user
    
    Args:
        user_id: ID of the user
        file_type: Optional filter by file type
        tag: Optional filter by tag
        limit: Maximum number of assets to return
        
    Returns:
        list: List of Asset objects
    """
    query = Asset.query.filter_by(user_id=user_id, is_active=True)
    
    if file_type:
        query = query.filter_by(file_type=file_type)
        
    if tag:
        # Search for tag in comma-separated list
        query = query.filter(Asset.tags.like(f"%{tag}%"))
        
    return query.order_by(Asset.created_at.desc()).limit(limit).all()


def generate_asset_preview_html(asset, include_controls=True):
    """
    Generate HTML for previewing an asset
    
    Args:
        asset: The Asset object
        include_controls: Whether to include controls (delete, edit buttons)
        
    Returns:
        str: HTML string for the asset preview
    """
    preview_html = '<div class="asset-preview">'
    
    # Image preview
    if asset.file_type == 'image':
        preview_html += f'<img src="{asset.file_url}" alt="{asset.original_filename}" class="img-fluid rounded">'
    
    # Document preview
    elif asset.file_type == 'document':
        extension = asset.original_filename.rsplit('.', 1)[1].lower() if '.' in asset.original_filename else ''
        
        if extension == 'pdf':
            preview_html += f'<div class="document-preview"><i class="far fa-file-pdf fa-3x text-danger"></i><span>{asset.original_filename}</span></div>'
        elif extension in ['doc', 'docx']:
            preview_html += f'<div class="document-preview"><i class="far fa-file-word fa-3x text-primary"></i><span>{asset.original_filename}</span></div>'
        elif extension in ['ppt', 'pptx']:
            preview_html += f'<div class="document-preview"><i class="far fa-file-powerpoint fa-3x text-warning"></i><span>{asset.original_filename}</span></div>'
        elif extension in ['xls', 'xlsx']:
            preview_html += f'<div class="document-preview"><i class="far fa-file-excel fa-3x text-success"></i><span>{asset.original_filename}</span></div>'
        else:
            preview_html += f'<div class="document-preview"><i class="far fa-file fa-3x"></i><span>{asset.original_filename}</span></div>'
    
    # Video preview
    elif asset.file_type == 'video':
        preview_html += f'<div class="video-preview"><i class="far fa-file-video fa-3x text-info"></i><span>{asset.original_filename}</span></div>'
    
    # Audio preview
    elif asset.file_type == 'audio':
        preview_html += f'<div class="audio-preview"><i class="far fa-file-audio fa-3x text-secondary"></i><span>{asset.original_filename}</span></div>'
    
    # Unknown type
    else:
        preview_html += f'<div class="file-preview"><i class="far fa-file fa-3x"></i><span>{asset.original_filename}</span></div>'
    
    # Asset metadata
    preview_html += f'<div class="asset-meta mt-2"><small>{asset.human_readable_size}</small>'
    
    if asset.description:
        preview_html += f'<p class="text-muted small">{asset.description}</p>'
    
    preview_html += '</div>'
    
    # Controls
    if include_controls:
        preview_html += f'''
        <div class="asset-controls mt-2">
            <button class="btn btn-sm btn-outline-primary select-asset" data-asset-id="{asset.id}" data-asset-type="{asset.file_type}">
                <i class="fas fa-plus-circle"></i> Select
            </button>
            <button class="btn btn-sm btn-outline-danger delete-asset" data-asset-id="{asset.id}">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        '''
    
    preview_html += '</div>'
    
    return preview_html
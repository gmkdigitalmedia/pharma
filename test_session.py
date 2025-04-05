"""
Test script for session management in Xupra.
"""
import os
from app import app, db, login_manager
from models import User
from flask import session
from flask_login import current_user, login_user, logout_user

def test_session():
    """Test session management."""
    with app.app_context():
        # Test user login
        user = User.query.filter_by(username='testadmin').first()
        if not user:
            print("User 'testadmin' not found.")
            return
        
        # Create a test request context
        with app.test_request_context():
            # Login the user
            login_user(user)
            
            # Check if user is logged in
            if current_user.is_authenticated:
                print("User logged in successfully.")
                print(f"Current user: {current_user.username}")
            else:
                print("User login failed.")
                
            # Set session to permanent
            session.permanent = True
            session['test_key'] = 'test_value'
            
            # Check session
            print(f"Session data: {dict(session)}")
            
            # Logout the user
            logout_user()
            
            # Check if user is logged out
            if not current_user.is_authenticated:
                print("User logged out successfully.")
            else:
                print("User logout failed.")

if __name__ == "__main__":
    test_session()
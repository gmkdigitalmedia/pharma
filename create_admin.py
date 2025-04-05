#!/usr/bin/env python3
"""
Utility script to create an admin user for Xupra.
This is intended for initial setup only.
"""

from app import app, db
from models import User
from werkzeug.security import generate_password_hash
import sys

def create_admin(username, email, password):
    """Create an admin user with the given credentials."""
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            print(f"Error: User with username '{username}' or email '{email}' already exists.")
            return False
            
        # Create new admin user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='admin', 
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        print(f"Success: Admin user '{username}' created!")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        sys.exit(1)
        
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    if create_admin(username, email, password):
        sys.exit(0)
    else:
        sys.exit(1)
#!/usr/bin/env python3
"""
Utility script to list all users in the Xupra database.
"""

from app import app, db
from models import User

def list_users():
    """List all users in the database."""
    with app.app_context():
        users = User.query.all()
        if not users:
            print("No users found in the database.")
            return
            
        print("Users in the database:")
        print("-" * 80)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Active':<10}")
        print("-" * 80)
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<10} {'Yes' if user.is_active else 'No':<10}")

if __name__ == "__main__":
    list_users()
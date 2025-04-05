"""
Utility script to reset a user's password in the Xupra database.
"""
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def reset_password(username, new_password):
    """Reset the password for a user."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User {username} not found.")
            return False
        
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print(f"Password for {username} has been reset.")
        return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <username> <new_password>")
        sys.exit(1)
    
    username = sys.argv[1]
    new_password = sys.argv[2]
    reset_password(username, new_password)
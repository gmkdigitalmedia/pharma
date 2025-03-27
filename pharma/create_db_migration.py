from app import app, db
from models import Organization, User, Invitation

def create_tables():
    """Create tables for new models and update existing tables."""
    with app.app_context():
        # Create tables
        db.create_all()
        print("Database tables created or updated successfully.")

if __name__ == '__main__':
    create_tables() 
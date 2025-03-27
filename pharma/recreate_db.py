from app import app, db
from models import User
import os

def recreate_database():
    """Drop and recreate the entire database."""
    with app.app_context():
        # Check if database file exists and remove it
        db_path = 'instance/database.sqlite'  # Default SQLite path for Flask apps
        
        # Check if a custom path was set in Flask configuration
        if app.config.get('SQLALCHEMY_DATABASE_URI'):
            uri = app.config.get('SQLALCHEMY_DATABASE_URI')
            if uri.startswith('sqlite:///'):
                db_path = uri.replace('sqlite:///', '')
        
        # First, drop all tables
        print(f"Dropping all tables...")
        db.drop_all()
        print("Tables dropped successfully.")

        # Recreate all tables
        print(f"Creating all tables...")
        db.create_all()
        print("Tables created successfully.")
        
        print("Database has been reset.")

if __name__ == '__main__':
    recreate_database() 
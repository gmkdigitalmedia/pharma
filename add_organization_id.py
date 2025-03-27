"""
One-time migration script to add organization_id column to the user table
"""
from app import app, db
import logging
from sqlalchemy import Column, Integer, ForeignKey, text

def migrate():
    try:
        with app.app_context():
            # Check if organization_id column already exists
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='user' AND column_name='organization_id'"))
                if result.rowcount > 0:
                    print("organization_id column already exists.")
                    return
                
            # Add organization_id column to user table
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE \"user\" ADD COLUMN organization_id INTEGER"))
                conn.execute(text("ALTER TABLE \"user\" ADD CONSTRAINT fk_user_organization FOREIGN KEY (organization_id) REFERENCES organization(id)"))
                conn.commit()
                print("Added organization_id column to user table.")
    except Exception as e:
        logging.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    migrate()
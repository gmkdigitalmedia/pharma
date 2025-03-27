"""
One-time migration script to add organization_id column to the invitation table
"""
import os
import sys
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from flask import Flask

def migrate():
    """Add organization_id column to invitation table."""
    app = Flask(__name__)
    
    # Configure database
    database_url = os.environ.get("DATABASE_URL", "sqlite:///pharmaceptor.db")
    # Handle Postgres connection string format for SQLAlchemy
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    engine = create_engine(database_url)
    
    # Check if the column already exists
    with engine.connect() as conn:
        inspector = sa.inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('invitation')]
        
        if 'organization_id' not in columns:
            print("Adding organization_id column to invitation table...")
            
            # Add the column
            conn.execute(text("ALTER TABLE invitation ADD COLUMN organization_id INTEGER"))
            
            # Update existing rows to set a default organization_id
            # For each invitation, set the organization_id to the sender's organization_id
            conn.execute(text("""
                UPDATE invitation
                SET organization_id = (
                    SELECT organization_id 
                    FROM "user" 
                    WHERE "user".id = invitation.sender_id
                )
            """))
            
            # Add the foreign key constraint
            conn.execute(text("""
                ALTER TABLE invitation 
                ADD CONSTRAINT fk_invitation_organization 
                FOREIGN KEY (organization_id) 
                REFERENCES organization(id)
            """))
            
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Column organization_id already exists in invitation table.")

if __name__ == "__main__":
    migrate()
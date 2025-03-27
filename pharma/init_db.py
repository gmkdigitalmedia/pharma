from app import app, db
from models import User, HCP, Asset, Content, ContentAsset, Campaign, Analytics, Invitation, ApiConnection, Organization

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 
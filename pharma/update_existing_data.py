from app import app, db
from models import User, HCP, Content, Campaign, ApiConnection, Organization
import uuid

def update_existing_data():
    """Updates existing data to add organization context."""
    with app.app_context():
        # Check if there's any data that needs migration
        user_count = User.query.count()
        if user_count == 0:
            print("No users found. No migration needed.")
            return
        
        # Check if any user already has an organization_id
        users_with_org = User.query.filter(User.organization_id.isnot(None)).count()
        if users_with_org > 0:
            print(f"{users_with_org} users already have organization_id. Skipping migration.")
            return
        
        print("Starting data migration to add organization context...")
        
        # Create a default organization for existing data
        default_org = Organization(
            name=f"Default Organization {uuid.uuid4().hex[:8]}",
            description="Auto-generated during migration to multi-tenant system",
            industry="Pharmaceutical"
        )
        db.session.add(default_org)
        db.session.flush()  # Get the ID without committing
        
        print(f"Created default organization with ID {default_org.id}")
        
        # Update all users
        users = User.query.all()
        for user in users:
            user.organization_id = default_org.id
            print(f"Assigned user {user.username} to organization {default_org.id}")
        
        # Update all HCPs
        hcps = HCP.query.all()
        for hcp in hcps:
            hcp.organization_id = default_org.id
            print(f"Assigned HCP {hcp.name} to organization {default_org.id}")
        
        # Update all content
        contents = Content.query.all()
        for content in contents:
            content.organization_id = default_org.id
            print(f"Assigned content {content.id} to organization {default_org.id}")
        
        # Update all campaigns
        campaigns = Campaign.query.all()
        for campaign in campaigns:
            campaign.organization_id = default_org.id
            print(f"Assigned campaign {campaign.id} to organization {default_org.id}")
        
        # Update all API connections
        api_connections = ApiConnection.query.all()
        for connection in api_connections:
            connection.organization_id = default_org.id
            print(f"Assigned API connection {connection.name} to organization {default_org.id}")
        
        # Commit all changes
        db.session.commit()
        print("Migration completed successfully!")

if __name__ == '__main__':
    update_existing_data() 
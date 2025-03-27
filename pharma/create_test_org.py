from app import app, db
from models import User, Organization
from werkzeug.security import generate_password_hash

def create_test_organization_and_admin():
    """Create a test organization and admin user for testing."""
    with app.app_context():
        # Create organization
        org = Organization(
            name="Pharma Test Org",
            description="Test organization for pharmaceutical company",
            industry="Pharmaceutical"
        )
        db.session.add(org)
        db.session.flush()  # Get the org ID
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=generate_password_hash("password"),
            role="admin",
            organization_id=org.id,
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Created organization '{org.name}' with ID {org.id}")
        print(f"Created admin user '{admin.username}' with ID {admin.id}")
        print("Login credentials: username='admin', password='password'")

if __name__ == '__main__':
    create_test_organization_and_admin() 
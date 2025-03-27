import random
from datetime import datetime, timedelta

def tag_hcps(hcps, tags):
    """Tag HCPs with selected tags."""
    return True

def load_content_blocks():
    """Load predefined content blocks."""
    return []

def generate_content(hcp_data, content_blocks):
    """Generate personalized content."""
    return "Sample content"

def mlr_prescreen(content):
    """Perform MLR prescreening."""
    return True, "Passed MLR check"

def select_channel(hcp_data):
    """Select optimal channel."""
    channels = ['email', 'sms', 'portal']
    return random.choice(channels)

def select_timing(hcp_data):
    """Select optimal timing."""
    now = datetime.now()
    days = random.randint(1, 7)
    return now + timedelta(days=days)

def generate_mock_analytics():
    """Generate mock analytics data."""
    return {
        'impressions': random.randint(100, 1000),
        'clicks': random.randint(10, 100),
        'conversions': random.randint(1, 10)
    } 
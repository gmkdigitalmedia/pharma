import pandas as pd
import json
import os
import random
import logging
from models import Analytics
from ai_services import (
    ml_classify_hcps, 
    generate_personalized_content,
    screen_content_compliance,
    predict_optimal_channel,
    predict_campaign_performance
)

# Set up logging
logging.basicConfig(level=logging.INFO)

def tag_hcps(data):
    """
    Tags HCPs based on their prescribing patterns and engagement scores using ML algorithms.
    
    Args:
        data (pandas.DataFrame): DataFrame containing HCP data
    
    Returns:
        pandas.DataFrame: DataFrame with added tag and tag_ml columns
    """
    # Ensure required columns exist
    required_columns = ['hcp_id']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Required column '{col}' not found in the data")
    
    # Create a copy of the data
    result = data.copy()
    
    # Add default values if columns are missing
    if 'prescribing_pattern' not in result.columns:
        result['prescribing_pattern'] = [random.uniform(0, 100) for _ in range(len(result))]
    
    if 'engagement_score' not in result.columns:
        result['engagement_score'] = [random.uniform(0, 100) for _ in range(len(result))]
    
    # First, apply traditional rules for backward compatibility (legacy approach)
    def assign_tag(row):
        if row['prescribing_pattern'] > 70:
            return 'early-adopter'
        elif row['engagement_score'] > 70:
            return 'evidence-driven'
        elif row['prescribing_pattern'] > 50 and row['engagement_score'] > 50:
            return 'balanced'
        else:
            return 'patient-focused'
    
    result['tag'] = result.apply(assign_tag, axis=1)
    
    try:
        # Now apply ML-based classification for more sophisticated tagging
        result_with_ml = ml_classify_hcps(result)
        
        # Merge ML tags back to main dataframe
        if 'tag_ml' in result_with_ml.columns:
            result['tag_ml'] = result_with_ml['tag_ml']
            logging.info(f"ML-based classification completed. Tags: {result['tag_ml'].value_counts().to_dict()}")
        else:
            logging.warning("ML classification did not return expected tag_ml column")
    except Exception as e:
        logging.error(f"ML-based classification failed: {str(e)}")
        # If ML fails, copy the rule-based tags as a fallback
        result['tag_ml'] = result['tag']
    
    return result

def load_content_blocks():
    """
    Loads pre-approved content blocks from JSON file.
    
    Returns:
        dict: Dictionary mapping HCP tags to content blocks
    """
    # Check if content_blocks.json exists, if not create it with default values
    content_blocks_path = os.path.join('static', 'data', 'content_blocks.json')
    
    if not os.path.exists(os.path.dirname(content_blocks_path)):
        os.makedirs(os.path.dirname(content_blocks_path))
    
    if not os.path.exists(content_blocks_path):
        default_blocks = {
            "early-adopter": [
                "Our latest innovation in {therapy_area} is now available for early clinical adoption.",
                "As a pioneer in {therapy_area}, you might be interested in our newest treatment approach.",
                "Leading physicians like yourself are already seeing benefits with our innovative therapy."
            ],
            "evidence-driven": [
                "Recent clinical trials show a {percent}% improvement in patient outcomes using our approach.",
                "Evidence from our Phase III study demonstrates statistically significant benefits (p<0.001).",
                "Data from {sample_size} patients indicates robust efficacy with minimal adverse events."
            ],
            "patient-focused": [
                "Patients report improved quality of life scores in recent satisfaction surveys.",
                "Our treatment regimen is designed with patient convenience and compliance in mind.",
                "Patient testimonials highlight the positive impact on daily living activities."
            ],
            "balanced": [
                "Our balanced approach combines clinical efficacy with patient-friendly administration.",
                "Both clinical data and patient experience reports support the value of our therapy.",
                "The dual benefits of improved outcomes and patient satisfaction make this a compelling option."
            ]
        }
        
        with open(content_blocks_path, 'w') as f:
            json.dump(default_blocks, f, indent=4)
    
    # Load content blocks from file
    with open(content_blocks_path, 'r') as f:
        content_blocks = json.load(f)
    
    return content_blocks

def generate_content(hcp_tag, hcp_name, content_blocks=None, specialty=None, use_ai=True):
    """
    Generates personalized content for an HCP based on their tag, using AI if available.
    
    Args:
        hcp_tag (str): The HCP's tag (e.g., "evidence-driven")
        hcp_name (str): The HCP's name
        content_blocks (dict, optional): Dictionary of content blocks by tag
        specialty (str, optional): The HCP's specialty
        use_ai (bool): Whether to use AI for content generation
        
    Returns:
        dict: Dictionary containing generated content and metadata
    """
    # If AI is enabled, attempt to use it
    if use_ai:
        try:
            # Create HCP data structure for AI
            hcp_data = {
                'name': hcp_name,
                'tag': hcp_tag,
                'specialty': specialty or 'Physician',
                'prescribing_pattern': random.uniform(50, 95) if hcp_tag in ['early-adopter', 'balanced'] else random.uniform(20, 70),
                'engagement_score': random.uniform(50, 95) if hcp_tag in ['evidence-driven', 'balanced'] else random.uniform(20, 70)
            }
            
            # Use AI service for content generation
            ai_result = generate_personalized_content(hcp_data, content_type="email")
            
            logging.info(f"Generated AI content using {ai_result['model_used']} for {hcp_name} ({hcp_tag})")
            
            # Return the AI-generated content and metadata
            return {
                'content': ai_result['content'],
                'model_used': ai_result['model_used'],
                'flags': ai_result['compliance_flags'],
                'ai_generated': True
            }
        except Exception as e:
            logging.error(f"AI content generation failed: {str(e)}")
            logging.info("Falling back to template-based content generation")
    
    # Fallback to template-based approach if AI is disabled or failed
    if content_blocks is None:
        content_blocks = load_content_blocks()
    
    # Default tag if the specific tag isn't found
    if hcp_tag not in content_blocks:
        hcp_tag = "balanced"
    
    # Select a random content block for the tag
    block = random.choice(content_blocks[hcp_tag])
    
    # Customize the content with HCP name and random values
    therapy_areas = ["cardiovascular health", "diabetes management", "oncology", "neurology", "immunology"]
    
    content = f"Dear {hcp_name},\n\n"
    content += block.format(
        therapy_area=random.choice(therapy_areas),
        percent=random.randint(15, 45),
        sample_size=random.randint(500, 5000)
    )
    
    content += "\n\nWe would be pleased to discuss how this might benefit your patients. Please let me know if you would like to schedule a meeting or webinar.\n\n"
    content += "Best regards,\nYour Xupra Representative"
    
    # Basic flagging for template-based content
    flags = mlr_prescreen(content)
    
    return {
        'content': content,
        'model_used': "Template-based",
        'flags': [{'term': flag, 'context': flag, 'severity': 'medium', 'reason': 'Flagged term'} for flag in flags],
        'ai_generated': False
    }

def mlr_prescreen(content):
    """
    Pre-screens content for risky phrases.
    
    Args:
        content (str): The content to screen
    
    Returns:
        list: List of flagged words/phrases
    """
    # List of banned words/phrases for medical content
    banned_words = [
        "cure", "guarantee", "proven", "100%", "miracle", 
        "breakthrough", "revolutionary", "magic", "perfect", 
        "safe", "most effective", "superior", "best"
    ]
    
    # Check content for banned words
    flags = []
    content_lower = content.lower()
    
    for word in banned_words:
        if word.lower() in content_lower:
            flags.append(word)
    
    return flags

def select_channel(hcp_tag):
    """
    Selects the best channel for content delivery based on HCP tag.
    
    Args:
        hcp_tag (str): The HCP's tag
    
    Returns:
        str: Selected channel (email, webinar, in-person)
    """
    # Channel mapping based on HCP tag
    channel_mapping = {
        "early-adopter": "webinar",
        "evidence-driven": "webinar",
        "patient-focused": "email",
        "balanced": "in-person"
    }
    
    # Default to email if tag not found
    return channel_mapping.get(hcp_tag, "email")

def select_timing(channel):
    """
    Selects the best timing for content delivery based on channel.
    
    Args:
        channel (str): The delivery channel
    
    Returns:
        str: Selected timing
    """
    # Timing mapping based on channel
    timing_mapping = {
        "email": "9 AM",
        "webinar": "12 PM",
        "in-person": "2 PM"
    }
    
    # Default to 9 AM if channel not found
    return timing_mapping.get(channel, "9 AM")

def generate_mock_analytics(campaign_id):
    """
    Generates mock analytics for a campaign.
    
    Args:
        campaign_id (int): The campaign ID
    
    Returns:
        Analytics: The generated analytics object
    """
    # Generate random analytics values
    open_rate = random.uniform(0.2, 0.8)
    response_rate = random.uniform(0.1, min(0.5, open_rate))  # Response rate should be less than open rate
    
    # Determine compliance status randomly
    compliance_statuses = ["Compliant", "Non-Compliant", "Pending"]
    compliance_weights = [0.7, 0.1, 0.2]  # More likely to be compliant
    compliance_status = random.choices(compliance_statuses, weights=compliance_weights)[0]
    
    # Random number of flags resolved
    flags_resolved = random.randint(0, 3)
    
    # Create and return analytics object
    return Analytics(
        campaign_id=campaign_id,
        open_rate=open_rate,
        response_rate=response_rate,
        compliance_status=compliance_status,
        flags_resolved=flags_resolved
    )

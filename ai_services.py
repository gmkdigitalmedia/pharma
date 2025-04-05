"""
AI Service Integrations for Xupra

This module provides AI capabilities to Xupra through:
- OpenAI API for content generation and NLP tasks
- Anthropic API as a fallback for content generation
- ML-based HCP classification
- Predictive analytics for engagement optimization
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Any, Optional
from openai import OpenAI
from anthropic import Anthropic
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split


# Initialize API clients based on available keys
openai_client = None
anthropic_client = None

if os.environ.get("OPENAI_API_KEY"):
    try:
        openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        logging.info("OpenAI client initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize OpenAI client: {str(e)}")

if os.environ.get("ANTHROPIC_API_KEY"):
    try:
        anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        logging.info("Anthropic client initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Anthropic client: {str(e)}")


# Content Generation with AI
def generate_personalized_content(hcp_data: Dict[str, Any], content_type: str = "email") -> Dict[str, Any]:
    """
    Generate personalized content for an HCP using AI models.
    
    Args:
        hcp_data: Dictionary containing HCP information (name, specialty, prescribing_pattern, engagement_score, tag)
        content_type: Type of content to generate (email, webinar, in-person)
        
    Returns:
        Dictionary containing generated content and metadata
    """
    # Construct prompt with HCP data and content requirements
    prompt = f"""
You are an AI assistant for Xupra, a pharmaceutical engagement company. Create personalized content for Dr. {hcp_data['name']}, 
a {hcp_data['specialty']} who has been categorized as a '{hcp_data['tag']}' type HCP.

Additional information:
- Prescribing pattern: {hcp_data['prescribing_pattern']} (higher is more frequent prescribing)
- Engagement score: {hcp_data['engagement_score']} (higher means more likely to engage)
- Content type: {content_type}

Create appropriate content that:
1. Addresses the HCP by name and specialty
2. Is tailored to their tag type ({hcp_data['tag']})
3. Follows pharmaceutical compliance guidelines (no off-label promotion)
4. Includes relevant scientific information
5. Has a clear call to action
6. Signs off as "Your Xupra Representative" 

Keep the content concise, professional, and compliant with pharmaceutical marketing regulations.
"""

    content = ""
    model_used = ""
    flags = []
    
    # Try OpenAI first if available
    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert pharmaceutical content generator that creates compliant, personalized HCP communications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            content = response.choices[0].message.content
            model_used = "OpenAI GPT-4o"
        except Exception as e:
            logging.error(f"OpenAI content generation failed: {str(e)}")
    
    # Fallback to Anthropic if OpenAI fails or isn't available
    if not content and anthropic_client:
        try:
            response = anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=800,
                temperature=0.7,
                system="You are an expert pharmaceutical content generator that creates compliant, personalized HCP communications.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.content[0].text
            model_used = "Anthropic Claude"
        except Exception as e:
            logging.error(f"Anthropic content generation failed: {str(e)}")
    
    # If both APIs fail, use a template-based fallback
    if not content:
        logging.warning("All AI content generation failed, using template fallback")
        content = f"Dear Dr. {hcp_data['name']},\n\nAs a respected {hcp_data['specialty']}, we thought you might be interested in our latest research...\n\n[Template fallback content for {hcp_data['tag']} HCPs]\n\nBest regards,\nXupra Team"
        model_used = "Template fallback"
    
    # Run content through compliance screening
    flags = screen_content_compliance(content)
    
    return {
        "content": content,
        "model_used": model_used,
        "compliance_flags": flags,
        "hcp_data": hcp_data,
        "content_type": content_type
    }


# NLP-based content screening
def screen_content_compliance(content: str) -> List[Dict[str, Any]]:
    """
    Screen content for compliance issues using NLP.
    
    Args:
        content: The content to screen
        
    Returns:
        List of dictionaries containing flagged words/phrases and their context
    """
    # List of problematic patterns in pharmaceutical communication
    problematic_patterns = [
        # Off-label promotion terms
        "off-label", "off label", "unapproved use", "unapproved indication",
        # Exaggerated efficacy terms
        "cure", "miracle", "guaranteed", "100%", "completely eliminates",
        # Minimizing safety concerns
        "perfectly safe", "no side effects", "risk free", "no risks",
        # Comparative claims without substantial evidence
        "better than", "superior to", "more effective than", "safer than",
        # Absolute statements
        "always works", "never fails", "all patients", "none of the patients",
    ]
    
    flags = []
    content_lower = content.lower()
    
    for pattern in problematic_patterns:
        if pattern.lower() in content_lower:
            # Find the context around the flag (20 chars before and after)
            index = content_lower.find(pattern.lower())
            start = max(0, index - 20)
            end = min(len(content), index + len(pattern) + 20)
            context = content[start:end]
            
            flags.append({
                "term": pattern,
                "context": context,
                "severity": "high" if pattern in ["off-label", "off label", "unapproved use", "guaranteed", "100%"] else "medium",
                "reason": "May violate pharmaceutical compliance guidelines"
            })

    # If we have OpenAI available, use it for more sophisticated screening
    if openai_client:
        try:
            prompt = f"""
Review the following pharmaceutical content for compliance issues. 
Identify any problematic phrases that could:
1. Suggest off-label promotion
2. Make exaggerated efficacy claims
3. Minimize safety concerns
4. Make comparative claims without evidence
5. Use absolute statements about efficacy or safety

Content to review:
{content}

Format your response as a JSON array of objects with the following structure:
[
  {{
    "term": "the problematic phrase",
    "context": "surrounding text that provides context",
    "severity": "high/medium/low",
    "reason": "specific explanation of the compliance issue"
  }}
]
If no issues are found, return an empty array: []
"""
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a pharmaceutical compliance expert that identifies regulatory issues in marketing content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            try:
                ai_flags = json.loads(response.choices[0].message.content)
                if isinstance(ai_flags, list):
                    # Merge with pattern-based flags, removing duplicates
                    existing_terms = {flag["term"] for flag in flags}
                    for ai_flag in ai_flags:
                        if ai_flag["term"] not in existing_terms:
                            flags.append(ai_flag)
                            existing_terms.add(ai_flag["term"])
            except (json.JSONDecodeError, KeyError) as e:
                logging.error(f"Error parsing AI compliance screening results: {str(e)}")
                
        except Exception as e:
            logging.error(f"AI compliance screening failed: {str(e)}")
    
    return flags


# ML-based HCP classification
def ml_classify_hcps(data: pd.DataFrame) -> pd.DataFrame:
    """
    Use machine learning to classify HCPs into meaningful segments.
    
    Args:
        data: DataFrame containing HCP data (must have prescribing_pattern and engagement_score)
        
    Returns:
        DataFrame with added tag_ml column containing ML-generated tags
    """
    # Ensure we have the required columns
    required_cols = ['prescribing_pattern', 'engagement_score']
    if not all(col in data.columns for col in required_cols):
        missing = [col for col in required_cols if col not in data.columns]
        raise ValueError(f"Missing required columns for ML classification: {missing}")
    
    # Extract features for clustering
    features = data[required_cols].copy()
    
    # Handle missing values
    features.fillna(features.mean(), inplace=True)
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Determine optimal number of clusters (simplified approach)
    n_clusters = min(4, len(data))  # Use at most 4 clusters
    
    # Apply K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(features_scaled)
    
    # Map cluster numbers to meaningful tags
    # Get cluster centers to understand what each cluster represents
    centers = scaler.inverse_transform(kmeans.cluster_centers_)
    
    # Create interpretation based on cluster centers
    cluster_interpretations = []
    for i, center in enumerate(centers):
        prescribing, engagement = center
        
        if prescribing > features['prescribing_pattern'].mean() and engagement > features['engagement_score'].mean():
            interpretation = "high-value"
        elif prescribing > features['prescribing_pattern'].mean() and engagement <= features['engagement_score'].mean():
            interpretation = "prescription-focused"
        elif prescribing <= features['prescribing_pattern'].mean() and engagement > features['engagement_score'].mean():
            interpretation = "engagement-focused"
        else:
            interpretation = "low-activity"
            
        cluster_interpretations.append(interpretation)
    
    # Map cluster numbers to interpretations
    tag_mapping = {i: tag for i, tag in enumerate(cluster_interpretations)}
    
    # Add ML-generated tag to the original DataFrame
    data['tag_ml'] = [tag_mapping[c] for c in clusters]
    
    return data


# Predictive engagement optimization
def predict_optimal_channel(hcp_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict the optimal engagement channel based on HCP characteristics.
    
    Args:
        hcp_data: Dictionary containing HCP information
        
    Returns:
        Dictionary with engagement recommendations
    """
    # Extract features for prediction
    features = {}
    
    # Required features
    required_keys = ['prescribing_pattern', 'engagement_score', 'tag']
    for key in required_keys:
        if key not in hcp_data:
            raise ValueError(f"Missing required HCP data: {key}")
        features[key] = hcp_data[key]
    
    # Optional features
    optional_keys = ['specialty', 'age', 'previous_response_rate']
    for key in optional_keys:
        features[key] = hcp_data.get(key, None)
    
    # Normalize the tag as a feature by creating a numeric "tag_value"
    tag_values = {
        'high-value': 1.0,
        'prescription-focused': 0.75,
        'engagement-focused': 0.5,
        'low-activity': 0.25,
        'evidence-driven': 0.8,
        'early-adopter': 0.9,
        'patient-focused': 0.7,
        'balanced': 0.6
    }
    
    tag_value = tag_values.get(features['tag'], 0.5)  # Default if tag is unknown
    
    # Simple rule-based prediction - can be replaced with actual ML model once data is available
    # High-scoring HCPs get more personalized channels
    engagement_score = features['engagement_score']
    prescribing_pattern = features['prescribing_pattern']
    combined_score = (engagement_score * 0.7) + (prescribing_pattern * 0.3) + (tag_value * 0.1)
    
    # Define channel recommendations based on scoring
    if combined_score > 0.8:
        primary_channel = "in-person"
        timing = "early-afternoon"
        secondary_channel = "email"
    elif combined_score > 0.6:
        primary_channel = "webinar"
        timing = "lunch-hour"
        secondary_channel = "email"
    elif combined_score > 0.4:
        primary_channel = "email"
        timing = "morning"
        secondary_channel = "webinar"
    else:
        primary_channel = "email"
        timing = "afternoon"
        secondary_channel = None
    
    # Calculate estimated response probability (simplified model)
    response_probability = min(0.95, combined_score * 0.7 + 0.3)
    
    return {
        "primary_channel": primary_channel,
        "secondary_channel": secondary_channel,
        "recommended_timing": timing,
        "expected_response_rate": round(response_probability * 100, 1),
        "confidence_score": round(min(0.95, 0.5 + combined_score * 0.4), 2),
        "hcp_combined_score": round(combined_score, 2)
    }


# Predictive analytics for campaign performance
def predict_campaign_performance(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict campaign performance metrics.
    
    Args:
        campaign_data: Dictionary containing campaign information
        
    Returns:
        Dictionary with predicted metrics and insights
    """
    # Extract campaign features
    channel = campaign_data.get("channel", "email")
    content_type = campaign_data.get("content_type", "general")
    target_tag = campaign_data.get("target_tag", "balanced")
    timing = campaign_data.get("timing", "morning")
    
    # Base rates for different channels
    base_rates = {
        "email": {"open_rate": 0.25, "response_rate": 0.05},
        "webinar": {"open_rate": 0.40, "response_rate": 0.15},
        "in-person": {"open_rate": 0.90, "response_rate": 0.30}
    }
    
    # Modifier for content type
    content_modifiers = {
        "general": 1.0,
        "educational": 1.2,
        "promotional": 0.8,
        "scientific": 1.15
    }
    
    # Modifier for target HCP tag
    tag_modifiers = {
        "high-value": 1.2,
        "prescription-focused": 1.1,
        "engagement-focused": 1.3,
        "low-activity": 0.7,
        "evidence-driven": 1.25,
        "early-adopter": 1.3,
        "patient-focused": 1.1,
        "balanced": 1.0
    }
    
    # Modifier for timing
    timing_modifiers = {
        "morning": 1.1,
        "lunch-hour": 0.9,
        "afternoon": 0.95,
        "early-afternoon": 1.05,
        "evening": 0.8
    }
    
    # Calculate predicted rates
    base = base_rates.get(channel, base_rates["email"])
    content_mod = content_modifiers.get(content_type, 1.0)
    tag_mod = tag_modifiers.get(target_tag, 1.0)
    timing_mod = timing_modifiers.get(timing, 1.0)
    
    predicted_open_rate = min(0.95, base["open_rate"] * content_mod * tag_mod * timing_mod)
    predicted_response_rate = min(0.75, base["response_rate"] * content_mod * tag_mod * timing_mod)
    
    # Generate insights based on predictions
    insights = []
    
    if predicted_open_rate < 0.2:
        insights.append("The predicted open rate is low. Consider changing the channel or timing.")
    
    if predicted_response_rate < 0.05:
        insights.append("The expected response rate is very low. The content may need revision or a more targeted approach.")
    
    if timing_mod < 1.0:
        insights.append(f"The selected timing ({timing}) may not be optimal for this campaign.")
    
    if tag_mod > 1.2 and predicted_response_rate > 0.2:
        insights.append(f"This campaign is well targeted for {target_tag} HCPs and is likely to perform well.")
    
    return {
        "predicted_open_rate": round(predicted_open_rate * 100, 1),
        "predicted_response_rate": round(predicted_response_rate * 100, 1),
        "predicted_roi_multiplier": round(predicted_response_rate / base["response_rate"], 2),
        "confidence_score": 0.85,  # Placeholder for model confidence
        "insights": insights,
        "recommended_improvements": generate_improvement_recommendations(campaign_data, predicted_open_rate, predicted_response_rate)
    }


def generate_improvement_recommendations(campaign_data: Dict[str, Any], 
                                        open_rate: float, 
                                        response_rate: float) -> List[str]:
    """
    Generate recommendations for improving campaign performance.
    
    Args:
        campaign_data: Dictionary containing campaign information
        open_rate: Predicted open rate
        response_rate: Predicted response rate
        
    Returns:
        List of improvement recommendations
    """
    channel = campaign_data.get("channel", "email")
    timing = campaign_data.get("timing", "morning")
    target_tag = campaign_data.get("target_tag", "balanced")
    
    recommendations = []
    
    # Channel recommendations
    if channel == "email" and response_rate < 0.1:
        recommendations.append("Consider a more direct channel like webinar or in-person visits for higher engagement.")
    
    if channel == "webinar" and open_rate < 0.3:
        recommendations.append("The webinar format may not be ideal. Consider pre-recording content or switching to email with key points.")
    
    # Timing recommendations
    if timing == "morning" and target_tag in ["high-value", "prescription-focused"]:
        recommendations.append("For this HCP segment, early afternoon timing may yield better results.")
    
    if timing == "evening":
        recommendations.append("Evening communications typically have lower engagement. Consider morning or early afternoon instead.")
    
    # Content recommendations
    if response_rate < 0.15 and open_rate > 0.3:
        recommendations.append("Your open rate is good, but response rate is low. The content may need a clearer call to action.")
    
    if target_tag == "evidence-driven" and channel != "webinar":
        recommendations.append("Evidence-driven HCPs respond well to detailed scientific information, which is better delivered via webinar.")
    
    if target_tag == "early-adopter" and "new" not in campaign_data.get("content_keywords", []):
        recommendations.append("Early adopters respond well to content highlighting new innovations or research.")
    
    return recommendations
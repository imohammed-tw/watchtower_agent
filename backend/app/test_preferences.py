# File: backend/test_preferences.py - TEST SCRIPT

"""
Test script to verify user preferences are working correctly
Run this script to test the full preference -> article flow
"""

import asyncio
import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USER_ID = "test_user_preferences"

async def test_user_preferences_workflow():
    """Test the complete user preferences to article generation workflow"""
    
    print("🧪 Testing User Preferences -> Article Generation Workflow")
    print("=" * 60)
    
    # Step 1: Set user preferences
    print("📝 Step 1: Setting user preferences...")
    
    preferences_data = {
        "user_id": TEST_USER_ID,
        "keywords": ["AI governance", "compliance", "security"],
        "preferred_sources": ["TechCrunch", "MIT Technology Review", "Reuters", "Wired", "Bloomberg"],
        "excluded_sources": ["Random Blog", "Spam Site"],
        "industry_focus": ["Healthcare", "Finance", "Manufacturing"],
        "content_types": ["regulatory", "technical", "market"],
        "urgency_threshold": 5,
        "relevance_threshold": 0.7
    }
    
    try:
        # Save preferences
        response = requests.post(
            f"{BASE_URL}/api/v1/users/preferences",
            json=preferences_data,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Preferences saved successfully")
            result = response.json()
            print(f"   Summary: {result.get('preferences_summary', {})}")
        else:
            print(f"❌ Failed to save preferences: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error saving preferences: {e}")
        return
    
    # Step 2: Verify preferences were saved
    print("\n📖 Step 2: Verifying preferences were saved...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/users/preferences/{TEST_USER_ID}")
        
        if response.status_code == 200:
            result = response.json()
            prefs = result.get("preferences", {})
            
            print("✅ Preferences retrieved successfully:")
            print(f"   Keywords: {prefs.get('keywords', [])}")
            print(f"   Preferred Sources: {prefs.get('preferred_sources', [])}")
            print(f"   Industry Focus: {prefs.get('industry_focus', [])}")
            print(f"   Excluded Sources: {prefs.get('excluded_sources', [])}")
        else:
            print(f"❌ Failed to retrieve preferences: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error retrieving preferences: {e}")
        return
    
    # Step 3: Test debug endpoint
    print("\n🔍 Step 3: Testing debug endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/users/preferences/{TEST_USER_ID}/debug")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Debug info retrieved:")
            print(f"   Found in database: {result.get('found_in_database')}")
            if result.get('preferred_sources'):
                print(f"   Stored preferred sources: {result.get('preferred_sources')}")
        else:
            print(f"⚠️ Debug endpoint returned: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Debug endpoint error: {e}")
    
    # Step 4: Generate newsletter to test if preferences are used
    print("\n📰 Step 4: Generating newsletter to test preference usage...")
    
    try:
        # Generate monthly newsletter (smaller for testing)
        newsletter_request = {
            "sections": [
                "Executive Summary",
                "Regulatory & Compliance Watch", 
                "Security & Risk Alerts"
            ],
            "template": "professional",
            "max_articles": 10,
            "max_total_words": 700  # Per requirements
        }
        
        print("   Generating newsletter (this may take 30-60 seconds)...")
        response = requests.post(
            f"{BASE_URL}/api/v1/newsletter/generate?user_id={TEST_USER_ID}",
            json=newsletter_request,
            timeout=120  # Extended timeout for generation
        )
        
        if response.status_code == 200:
            result = response.json()
            newsletter = result.get("newsletter", {})
            
            print("✅ Newsletter generated successfully!")
            print(f"   Title: {newsletter.get('title', 'N/A')}")
            print(f"   Word count: {newsletter.get('summary', {}).get('word_count', 'N/A')}")
            print(f"   Sections: {len(newsletter.get('sections', {}))}")
            print(f"   Generated at: {newsletter.get('generated_at', 'N/A')}")
            
            # Check if newsletter content mentions preferred sources
            content = newsletter.get('content', '')
            sections = newsletter.get('sections', {})
            
            found_preferred_sources = []
            for source in preferences_data['preferred_sources']:
                if source in content:
                    found_preferred_sources.append(source)
                    
                # Check in individual sections too
                for section_content in sections.values():
                    if source in section_content:
                        found_preferred_sources.append(source)
                        break
            
            found_preferred_sources = list(set(found_preferred_sources))  # Remove duplicates
            
            if found_preferred_sources:
                print(f"✅ PREFERENCES WORKING: Found preferred sources in newsletter: {found_preferred_sources}")
            else:
                print(f"⚠️ POSSIBLE ISSUE: No preferred sources found in newsletter content")
                print(f"   This could be due to:")
                print(f"   1. Mock data being used (no real API key)")
                print(f"   2. Perplexity API not finding articles from preferred sources")
                print(f"   3. Recent articles not available from those sources")
            
        else:
            print(f"❌ Newsletter generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error generating newsletter: {e}")
    
    # Step 5: Test with different preferences
    print("\n🔄 Step 5: Testing preference changes...")
    
    try:
        # Update preferences
        updated_prefs = {
            "keywords": ["AI security", "data breach", "cybersecurity"],
            "preferred_sources": ["Wired", "Axios", "Reuters"],  # Different sources
            "excluded_sources": ["TechCrunch"],  # Exclude previously preferred
            "industry_focus": ["Healthcare"],
            "content_types": ["regulatory", "technical"],
            "urgency_threshold": 7,
            "relevance_threshold": 0.8
        }
        
        response = requests.put(
            f"{BASE_URL}/api/v1/users/preferences/{TEST_USER_ID}",
            json=updated_prefs,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Preferences updated successfully")
            result = response.json()
            updated = result.get('updated_preferences', {})
            print(f"   New preferred sources: {updated.get('preferred_sources', [])}")
            print(f"   New excluded sources: {updated.get('excluded_sources', [])}")
        else:
            print(f"❌ Failed to update preferences: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error updating preferences: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 TEST COMPLETE")
    print("\nTo verify preferences are working:")
    print("1. Check that preferred sources appear in generated newsletters")
    print("2. Verify excluded sources do NOT appear")  
    print("3. Confirm keywords influence article selection")
    print("4. Test with real Perplexity API key for full functionality")

if __name__ == "__main__":
    asyncio.run(test_user_preferences_workflow())
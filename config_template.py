"""
Configuration Template for Reddit Scraper
=========================================

Instructions:
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Fill in the details:
   - Name: Your app name (e.g., "My Reddit Scraper")
   - Description: Brief description
   - About URL: Can be left blank
   - Redirect URI: http://localhost:8080 (required but not used)
5. Copy the CLIENT_ID and CLIENT_SECRET from the created app
6. Replace the values below and save as config.py

IMPORTANT: Never commit config.py to version control!
"""

# Reddit API Configuration
CLIENT_ID = "your_client_id_here"  # Found under the app name in your Reddit apps
CLIENT_SECRET = "your_client_secret_here"  # The "secret" field
USER_AGENT = "reddit_scraper_v1.0_by_your_reddit_username"  # Should include your Reddit username

# Scraping Configuration
SUBREDDIT_NAME = "notebookLLM"  # Target subreddit (without r/)
MAX_REQUESTS_PER_MINUTE = 60  # Conservative rate limit for free tier
DATABASE_PATH = "reddit_data.db"  # SQLite database file path

# Time-based scraping configuration
START_DATE = "2020-01-01"  # Format: YYYY-MM-DD, adjust based on subreddit age
MONTHLY_SEGMENTS = True  # Split time-based scraping into monthly chunks

# Search terms for keyword-based scraping (customize for your subreddit)
SEARCH_TERMS = [
    # General terms
    "question", "help", "issue", "problem", "tutorial", "guide",
    "announcement", "update", "discussion", "review", "comparison",
    "tips", "tricks", "best", "worst", "opinion", "thoughts",
    
    # NotebookLLM-specific terms
    "notebook", "llm", "ai", "model", "chat", "conversation",
    "prompt", "generation", "training", "fine-tune", "dataset",
    "google", "gemini", "source", "upload", "summary"
] 
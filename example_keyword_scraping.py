#!/usr/bin/env python3
"""
Example: Reddit Keyword Scraping
================================

This script demonstrates how to use the keyword filtering functionality
to scrape only posts that match specific keywords.
"""

import os
import logging
from dotenv import load_dotenv
from reddit_scraper import RedditScraper
from quick_start import QuickRedditScraper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def example_comprehensive_keyword_scraping():
    """Example of using keyword filtering with the comprehensive scraper"""
    print("=" * 60)
    print("COMPREHENSIVE KEYWORD SCRAPING EXAMPLE")
    print("=" * 60)
    
    # Initialize scraper
    scraper = RedditScraper(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT")
    )
    
    # Example 1: Only scrape posts containing AI/ML keywords
    keywords = ["machine learning", "AI", "neural network", "deep learning", "llm", "gpt"]
    scraper.set_keyword_filter(
        keywords=keywords,
        mode='include_only',  # Only posts with these keywords
        case_sensitive=False,
        search_in_content=True  # Search in both title and post content
    )
    
    print(f"Scraping posts that contain keywords: {keywords}")
    scraper.scrape_subreddit_comprehensive("MachineLearning")
    
    # Print results
    stats = scraper.get_stats()
    print(f"\nResults:")
    print(f"- Total posts scraped: {stats['total_posts']}")
    print(f"- Total comments scraped: {stats['total_comments']}")

def example_quick_keyword_scraping():
    """Example of using keyword filtering with the quick scraper"""
    print("\n" + "=" * 60)
    print("QUICK KEYWORD SCRAPING EXAMPLE")
    print("=" * 60)
    
    # Initialize quick scraper
    scraper = QuickRedditScraper(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT")
    )
    
    # Example 2: Exclude posts with specific keywords
    exclude_keywords = ["meme", "joke", "shitpost"]
    scraper.set_keyword_filter(
        keywords=exclude_keywords,
        mode='exclude',  # Exclude posts with these keywords
        case_sensitive=False
    )
    
    print(f"Scraping posts that DO NOT contain: {exclude_keywords}")
    scraper.scrape_subreddit_sample("programming", limit=50)
    
    print(f"\nResults:")
    print(f"- Posts scraped: {len(scraper.posts_data)}")
    print(f"- Comments scraped: {len(scraper.comments_data)}")
    
    # Save results
    scraper.save_to_json("keyword_filtered_results.json")

def example_targeted_keyword_search():
    """Example of searching for specific keywords only"""
    print("\n" + "=" * 60)
    print("TARGETED KEYWORD SEARCH EXAMPLE")
    print("=" * 60)
    
    # Initialize comprehensive scraper
    scraper = RedditScraper(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT")
    )
    
    # Search only for specific keywords (most efficient method)
    keywords = ["python tutorial", "beginner guide", "best practices"]
    print(f"Searching only for posts containing: {keywords}")
    
    total_posts = scraper.scrape_subreddit_keywords_only(
        subreddit_name="learnpython",
        keywords=keywords,
        case_sensitive=False,
        include_comments=True
    )
    
    print(f"\nResults: {total_posts} posts found and scraped")

def example_quick_targeted_search():
    """Example of targeted search with quick scraper"""
    print("\n" + "=" * 60)
    print("QUICK TARGETED SEARCH EXAMPLE")
    print("=" * 60)
    
    # Initialize quick scraper
    scraper = QuickRedditScraper(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT")
    )
    
    # Search for specific keywords
    keywords = ["docker", "kubernetes", "containerization"]
    print(f"Searching for: {keywords}")
    
    total_posts = scraper.scrape_keywords_only(
        subreddit_name="devops",
        keywords=keywords,
        case_sensitive=False,
        max_posts_per_keyword=50
    )
    
    print(f"\nResults: {total_posts} posts found")
    
    # Save results
    scraper.save_to_json("targeted_search_results.json")
    scraper.print_summary()

def main():
    """Run all examples"""
    print("Reddit Keyword Scraping Examples")
    print("Make sure you have set up your .env file with Reddit API credentials!")
    
    try:
        # Uncomment the examples you want to run:
        
        # Example 1: Comprehensive scraping with keyword filtering
        # example_comprehensive_keyword_scraping()
        
        # Example 2: Quick scraping with keyword exclusion
        example_quick_keyword_scraping()
        
        # Example 3: Targeted keyword search (comprehensive)
        # example_targeted_keyword_search()
        
        # Example 4: Targeted keyword search (quick)
        example_quick_targeted_search()
        
        print("\n" + "=" * 60)
        print("EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with Reddit API credentials")
        print("2. Installed all required packages (pip install -r requirements.txt)")

if __name__ == "__main__":
    main() 
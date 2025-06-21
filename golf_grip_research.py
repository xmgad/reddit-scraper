#!/usr/bin/env python3
"""
Golf Grip Trend Research Script
==============================

Specialized script for researching the trend of larger golf grips.
This script uses comprehensive keyword coverage to ensure no relevant posts are missed.
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

def get_golf_grip_keywords():
    """
    Comprehensive keyword list for golf grip trend research
    Covers all possible ways people might discuss larger/oversized grips
    """
    
    # Core grip terms
    core_terms = [
        "grip", "grips", "regrip", "re-grip", "grip change", "changed grips", 
        "new grips", "grip installation", "grip fitting"
    ]
    
    # Size-related terms
    size_terms = [
        "larger grip", "bigger grip", "oversized grip", "jumbo grip", "thick grip",
        "grip size", "midsize grip", "standard grip", "grip diameter",
        "oversized", "jumbo", "midsize", "thick grips", "fat grips"
    ]
    
    # Brand names (especially those known for larger grips)
    brand_terms = [
        "Golf Pride", "Lamkin", "Winn", "JumboMax", "Karma", "Iomic",
        "SuperStroke", "Tacki-Mac", "Avon", "Loudmouth"
    ]
    
    # Performance and feel terms
    performance_terms = [
        "grip feel", "grip comfort", "hand size", "grip pressure",
        "swing feel", "grip feedback", "grip texture", "grip performance"
    ]
    
    # Health/comfort related (older golfers, arthritis, etc.)
    health_terms = [
        "arthritis", "joint pain", "hand pain", "comfortable grip",
        "grip for seniors", "senior golfers", "older golfer"
    ]
    
    # Equipment discussion terms
    equipment_terms = [
        "equipment change", "club modification", "custom grips",
        "club fitting", "grip recommendation", "grip advice"
    ]
    
    # Community discussion phrases
    discussion_terms = [
        "anyone try", "anyone using", "experience with", "tried larger",
        "switched to", "thinking about", "considering", "recommendation",
        "review", "thoughts on", "opinion on"
    ]
    
    # Technical terms
    technical_terms = [
        "grip tape", "grip solvent", "grip core", "grip weight",
        "swing weight", "club balance", "grip installation"
    ]
    
    # Combine all terms
    all_keywords = (core_terms + size_terms + brand_terms + performance_terms + 
                   health_terms + equipment_terms + discussion_terms + technical_terms)
    
    return list(set(all_keywords))  # Remove duplicates

def research_golf_grips_comprehensive(subreddit_name="golf"):
    """
    Comprehensive research using all scraping strategies with keyword filtering
    """
    print("=" * 70)
    print("COMPREHENSIVE GOLF GRIP TREND RESEARCH")
    print("=" * 70)
    
    keywords = get_golf_grip_keywords()
    print(f"Using {len(keywords)} keywords to capture all grip-related discussions")
    print(f"Keywords: {keywords[:10]}... (and {len(keywords)-10} more)")
    
    # Initialize scraper
    scraper = RedditScraper(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT")
    )
    
    # Set keyword filter to include posts mentioning any grip-related terms
    scraper.set_keyword_filter(
        keywords=keywords,
        mode='include_only',
        case_sensitive=False,
        search_in_content=True  # Search both titles and post content
    )
    
    print(f"\nStarting comprehensive scrape of r/{subreddit_name}...")
    scraper.scrape_subreddit_comprehensive(subreddit_name)
    
    # Get results
    stats = scraper.get_stats()
    print(f"\n📊 RESULTS:")
    print(f"- Total grip-related posts: {stats['total_posts']}")
    print(f"- Total comments: {stats['total_comments']}")
    print(f"- Posts with comments: {stats['posts_with_comments']}")
    
    return stats

def research_golf_grips_targeted(subreddit_name="golf"):
    """
    Targeted research using direct keyword search (faster, more focused)
    """
    print("\n" + "=" * 70)
    print("TARGETED GOLF GRIP RESEARCH")
    print("=" * 70)
    
    # Most important keywords for targeted search
    priority_keywords = [
        "larger grip", "bigger grip", "oversized grip", "jumbo grip",
        "grip size", "midsize grip", "JumboMax", "thick grip",
        "regrip", "grip change", "grip feel", "grip comfort",
        "arthritis grip", "senior grip", "oversized"
    ]
    
    print(f"Searching for priority keywords: {priority_keywords}")
    
    # Initialize scraper
    scraper = RedditScraper(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT")
    )
    
    print(f"\nSearching r/{subreddit_name} for specific grip keywords...")
    total_posts = scraper.scrape_subreddit_keywords_only(
        subreddit_name=subreddit_name,
        keywords=priority_keywords,
        case_sensitive=False,
        include_comments=True
    )
    
    print(f"\n🎯 TARGETED RESULTS: {total_posts} relevant posts found")
    return total_posts

def research_golf_grips_quick_test(subreddit_name="golf"):
    """
    Quick test with a small sample to verify keyword effectiveness
    """
    print("\n" + "=" * 70)
    print("QUICK GRIP RESEARCH TEST")
    print("=" * 70)
    
    # Test keywords
    test_keywords = [
        "grip", "regrip", "oversized", "jumbo", "grip size", 
        "larger grip", "Golf Pride", "Lamkin"
    ]
    
    scraper = QuickRedditScraper(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT")
    )
    
    print(f"Testing with keywords: {test_keywords}")
    total_posts = scraper.scrape_keywords_only(
        subreddit_name=subreddit_name,
        keywords=test_keywords,
        case_sensitive=False,
        max_posts_per_keyword=25
    )
    
    print(f"\n🧪 TEST RESULTS: {total_posts} posts found")
    print(f"Sample of posts found:")
    for i, post in enumerate(scraper.posts_data[:5]):
        print(f"{i+1}. {post['title'][:80]}...")
    
    # Save test results
    scraper.save_to_json("golf_grip_test_results.json")
    return total_posts

def main():
    """Run golf grip trend research"""
    print("🏌️ GOLF GRIP TREND RESEARCH")
    print("Researching the trend of larger/oversized grips in golf")
    print("\nMake sure your .env file has Reddit API credentials!")
    
    try:
        # Run different research approaches
        
        # 1. Quick test first (recommended to start)
        print("\n🚀 Starting with quick test...")
        research_golf_grips_quick_test("golf")
        
        # 2. Targeted search (uncomment to run)
        # print("\n🎯 Running targeted search...")
        # research_golf_grips_targeted("golf")
        
        # 3. Comprehensive search (uncomment for full research)
        # print("\n📊 Running comprehensive research...")
        # research_golf_grips_comprehensive("golf")
        
        print("\n" + "=" * 70)
        print("✅ RESEARCH COMPLETED!")
        print("Check the generated JSON files for detailed results.")
        print("=" * 70)
        
        print("\n📝 NEXT STEPS FOR YOUR RESEARCH:")
        print("1. Review the scraped posts to understand the trend")
        print("2. Look for patterns in who's switching to larger grips")
        print("3. Analyze reasons mentioned (comfort, performance, health)")
        print("4. Note popular brands and grip sizes being discussed")
        print("5. Check time trends to see if this is growing")
        
    except Exception as e:
        logger.error(f"Error running research: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with Reddit API credentials")
        print("2. Installed required packages: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 
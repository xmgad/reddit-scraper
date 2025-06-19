#!/usr/bin/env python3
"""
Quick Start Reddit Scraper
==========================

Simplified version for immediate testing and small-scale scraping.
Use this to test your setup before running the full comprehensive scraper.
"""

import praw
import sqlite3
import json
import time
import logging
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickRedditScraper:
    """Simplified Reddit scraper for testing and small datasets"""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.posts_data = []
        self.comments_data = []
        
        # Keyword filtering
        self.keywords = []
        self.keyword_mode = 'disabled'  # 'disabled', 'include_only', 'exclude'
        self.case_sensitive = False
        self.search_in_content = True
    
    def set_keyword_filter(self, keywords: list, mode: str = 'include_only', 
                          case_sensitive: bool = False, search_in_content: bool = True):
        """
        Set keyword filtering options
        
        Args:
            keywords: List of keywords to filter by
            mode: 'include_only' (only posts with keywords), 'exclude' (posts without keywords), 'disabled' (no filtering)
            case_sensitive: Whether keyword matching should be case sensitive
            search_in_content: Whether to search in post content (selftext) in addition to title
        """
        self.keywords = [k.lower() if not case_sensitive else k for k in keywords]
        self.keyword_mode = mode
        self.case_sensitive = case_sensitive
        self.search_in_content = search_in_content
        
        logger.info(f"Keyword filter set: mode={mode}, keywords={keywords}, case_sensitive={case_sensitive}")
    
    def _matches_keywords(self, post) -> bool:
        """Check if a post matches the current keyword filter"""
        if self.keyword_mode == 'disabled' or not self.keywords:
            return True
        
        # Prepare text to search in
        title = post.title if self.case_sensitive else post.title.lower()
        content = ''
        
        if self.search_in_content and hasattr(post, 'selftext'):
            content = getattr(post, 'selftext', '') 
            content = content if self.case_sensitive else content.lower()
        
        search_text = f"{title} {content}".strip()
        
        # Check for keyword matches
        matches_any_keyword = False
        for keyword in self.keywords:
            if keyword in search_text:
                matches_any_keyword = True
                break
        
        # Apply filtering logic based on mode
        if self.keyword_mode == 'include_only':
            return matches_any_keyword
        elif self.keyword_mode == 'exclude':
            return not matches_any_keyword
        
        return True

    def scrape_subreddit_sample(self, subreddit_name: str, limit: int = 100):
        """Scrape a sample of posts from a subreddit"""
        logger.info(f"Starting sample scrape of r/{subreddit_name} (limit: {limit})")
        if self.keyword_mode != 'disabled':
            logger.info(f"Keyword filtering active: {self.keyword_mode} - {self.keywords}")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Test connectivity
            logger.info(f"Subreddit: {subreddit.display_name}")
            logger.info(f"Subscribers: {subreddit.subscribers:,}")
            
            # Scrape hot posts
            logger.info("Scraping hot posts...")
            for post in subreddit.hot(limit=limit):
                # Apply keyword filter
                if not self._matches_keywords(post):
                    continue
                    
                post_data = self._process_post(post)
                if post_data:
                    self.posts_data.append(post_data)
                    
                    # Get some comments for each post
                    if post.num_comments > 0:
                        self._process_post_comments(post, max_comments=10)
                
                # Simple rate limiting
                time.sleep(0.5)
            
            logger.info(f"Scraped {len(self.posts_data)} posts and {len(self.comments_data)} comments")
            
        except Exception as e:
            logger.error(f"Error scraping: {e}")
            raise
    
    def _process_post(self, post) -> Dict:
        """Process a single post"""
        try:
            return {
                'id': post.id,
                'title': post.title,
                'selftext': getattr(post, 'selftext', ''),
                'author': post.author.name if post.author else '[deleted]',
                'created_utc': post.created_utc,
                'created_datetime': datetime.fromtimestamp(post.created_utc).isoformat(),
                'score': post.score,
                'num_comments': post.num_comments,
                'url': post.url,
                'permalink': post.permalink,
                'subreddit': post.subreddit.display_name,
                'upvote_ratio': getattr(post, 'upvote_ratio', 0.0),
                'is_self': post.is_self
            }
        except Exception as e:
            logger.error(f"Error processing post {post.id}: {e}")
            return None
    
    def _process_post_comments(self, post, max_comments: int = 10):
        """Process comments for a post"""
        try:
            post.comments.replace_more(limit=0)  # Get top-level comments only
            
            comment_count = 0
            for comment in post.comments[:max_comments]:
                if hasattr(comment, 'body') and comment.body != '[deleted]':
                    comment_data = {
                        'id': comment.id,
                        'post_id': post.id,
                        'body': comment.body,
                        'author': comment.author.name if comment.author else '[deleted]',
                        'created_utc': comment.created_utc,
                        'created_datetime': datetime.fromtimestamp(comment.created_utc).isoformat(),
                        'score': comment.score,
                        'permalink': comment.permalink
                    }
                    self.comments_data.append(comment_data)
                    comment_count += 1
            
            if comment_count > 0:
                logger.info(f"Scraped {comment_count} comments for post {post.id}")
                
        except Exception as e:
            logger.error(f"Error processing comments for post {post.id}: {e}")
    
    def save_to_json(self, filename: str = "quick_scrape_results.json"):
        """Save results to JSON file"""
        data = {
            'metadata': {
                'scrape_date': datetime.now().isoformat(),
                'total_posts': len(self.posts_data),
                'total_comments': len(self.comments_data)
            },
            'posts': self.posts_data,
            'comments': self.comments_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved results to {filename}")
    
    def save_to_sqlite(self, filename: str = "quick_scrape_results.db"):
        """Save results to SQLite database"""
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT,
                selftext TEXT,
                author TEXT,
                created_utc REAL,
                created_datetime TEXT,
                score INTEGER,
                num_comments INTEGER,
                url TEXT,
                permalink TEXT,
                subreddit TEXT,
                upvote_ratio REAL,
                is_self BOOLEAN
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                post_id TEXT,
                body TEXT,
                author TEXT,
                created_utc REAL,
                created_datetime TEXT,
                score INTEGER,
                permalink TEXT,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')
        
        # Insert posts
        for post in self.posts_data:
            cursor.execute('''
                INSERT OR REPLACE INTO posts 
                (id, title, selftext, author, created_utc, created_datetime, 
                 score, num_comments, url, permalink, subreddit, upvote_ratio, is_self)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post['id'], post['title'], post['selftext'], post['author'],
                post['created_utc'], post['created_datetime'], post['score'],
                post['num_comments'], post['url'], post['permalink'],
                post['subreddit'], post['upvote_ratio'], post['is_self']
            ))
        
        # Insert comments
        for comment in self.comments_data:
            cursor.execute('''
                INSERT OR REPLACE INTO comments 
                (id, post_id, body, author, created_utc, created_datetime, score, permalink)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                comment['id'], comment['post_id'], comment['body'], comment['author'],
                comment['created_utc'], comment['created_datetime'], 
                comment['score'], comment['permalink']
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved results to {filename}")
    
    def print_summary(self):
        """Print a summary of scraped data"""
        print("\n" + "="*50)
        print("QUICK SCRAPE SUMMARY")
        print("="*50)
        print(f"Posts scraped: {len(self.posts_data)}")
        print(f"Comments scraped: {len(self.comments_data)}")
        
        if self.posts_data:
            scores = [post['score'] for post in self.posts_data]
            print(f"Average post score: {sum(scores) / len(scores):.1f}")
            print(f"Highest scoring post: {max(scores)}")
            
            # Show top 3 posts by score
            sorted_posts = sorted(self.posts_data, key=lambda x: x['score'], reverse=True)
            print(f"\nTop 3 posts by score:")
            for i, post in enumerate(sorted_posts[:3], 1):
                title = post['title'][:60] + "..." if len(post['title']) > 60 else post['title']
                print(f"{i}. {title} (Score: {post['score']})")
        
        print("="*50)

    def scrape_keywords_only(self, subreddit_name: str, keywords: list, 
                           case_sensitive: bool = False, max_posts_per_keyword: int = 100):
        """
        Scrape only posts that match specific keywords using targeted search
        
        Args:
            subreddit_name: Name of the subreddit to scrape
            keywords: List of keywords to search for
            case_sensitive: Whether search should be case sensitive
            max_posts_per_keyword: Maximum posts to collect per keyword
        """
        logger.info(f"Starting keyword-only scrape of r/{subreddit_name} for keywords: {keywords}")
        
        subreddit = self.reddit.subreddit(subreddit_name)
        total_posts = 0
        
        for keyword in keywords:
            try:
                logger.info(f"Searching for keyword: '{keyword}'")
                
                search_results = subreddit.search(
                    keyword, 
                    sort='new', 
                    time_filter='all', 
                    limit=max_posts_per_keyword
                )
                
                keyword_posts = 0
                for post in search_results:
                    # Additional filtering if case sensitive
                    if case_sensitive:
                        title_text = post.title
                        content_text = getattr(post, 'selftext', '')
                        search_text = f"{title_text} {content_text}"
                        
                        if keyword not in search_text:
                            continue
                    
                    post_data = self._process_post(post)
                    if post_data:
                        self.posts_data.append(post_data)
                        keyword_posts += 1
                        total_posts += 1
                        
                        # Get some comments for each post
                        if post.num_comments > 0:
                            self._process_post_comments(post, max_comments=10)
                
                logger.info(f"Keyword '{keyword}': {keyword_posts} posts found")
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error searching for keyword '{keyword}': {e}")
        
        logger.info(f"Keyword-only scrape completed: {total_posts} total posts")
        return total_posts

def main():
    """Main function for quick scraper"""
    
    # Configuration - UPDATE THESE VALUES
    CLIENT_ID = "your_client_id_here"
    CLIENT_SECRET = "your_client_secret_here" 
    USER_AGENT = "quick_reddit_scraper_v1.0_by_your_username"
    SUBREDDIT_NAME = "notebookLLM"
    SAMPLE_SIZE = 50  # Number of posts to scrape
    
    # Check if credentials are still default
    if CLIENT_ID == "your_client_id_here":
        print("❌ ERROR: Please update your Reddit API credentials in this script!")
        print("1. Get credentials from https://www.reddit.com/prefs/apps")
        print("2. Update CLIENT_ID, CLIENT_SECRET, and USER_AGENT in this file")
        return
    
    try:
        # Initialize scraper
        scraper = QuickRedditScraper(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
        
        # Test connection and scrape sample
        scraper.scrape_subreddit_sample(SUBREDDIT_NAME, SAMPLE_SIZE)
        
        # Save results
        scraper.save_to_json()
        scraper.save_to_sqlite()
        
        # Show summary
        scraper.print_summary()
        
        print(f"\n✅ Quick scrape completed successfully!")
        print(f"Files created:")
        print(f"  - quick_scrape_results.json")
        print(f"  - quick_scrape_results.db")
        
        print(f"\nTo run the full comprehensive scraper:")
        print(f"  1. Copy config_template.py to config.py")
        print(f"  2. Update your credentials in config.py")
        print(f"  3. Run: python reddit_scraper.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"  - Verify your Reddit API credentials")
        print(f"  - Check that the subreddit '{SUBREDDIT_NAME}' exists")
        print(f"  - Ensure you have internet connectivity")

if __name__ == "__main__":
    main() 
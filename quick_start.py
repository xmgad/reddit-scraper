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
    
    def scrape_subreddit_sample(self, subreddit_name: str, limit: int = 100):
        """Scrape a sample of posts from a subreddit"""
        logger.info(f"Starting sample scrape of r/{subreddit_name} (limit: {limit})")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Test connectivity
            logger.info(f"Subreddit: {subreddit.display_name}")
            logger.info(f"Subscribers: {subreddit.subscribers:,}")
            
            # Scrape hot posts
            logger.info("Scraping hot posts...")
            for post in subreddit.hot(limit=limit):
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
#!/usr/bin/env python3
"""
Reddit Scraping Pipeline - Free Tier Optimized
===============================================

A comprehensive pipeline to scrape all posts and comments from a subreddit
using only the free tier Reddit API with smart workarounds for limitations.

Key Features:
- Multi-strategy data collection (time-based, sort-based, search-based)
- Rate limiting and exponential backoff
- Deduplication across strategies
- Progress tracking and resume capability
- Comments collection for each post
"""

import praw
import prawcore
import sqlite3
import json
import time
import logging
import hashlib
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import random
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reddit_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RedditPost:
    """Data structure for Reddit posts"""
    id: str
    title: str
    selftext: str
    author: str
    created_utc: float
    score: int
    num_comments: int
    url: str
    permalink: str
    subreddit: str
    upvote_ratio: float
    is_self: bool
    link_flair_text: Optional[str]
    post_hint: Optional[str]
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def get_hash(self) -> str:
        """Generate unique hash for deduplication"""
        return hashlib.md5(f"{self.id}_{self.created_utc}".encode()).hexdigest()

@dataclass
class RedditComment:
    """Data structure for Reddit comments"""
    id: str
    post_id: str
    parent_id: str
    body: str
    author: str
    created_utc: float
    score: int
    permalink: str
    depth: int
    is_submitter: bool
    
    def to_dict(self) -> dict:
        return asdict(self)

class RateLimiter:
    """Smart rate limiting with exponential backoff"""
    
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests_per_minute = max_requests_per_minute
        self.requests = []
        self.backoff_time = 1
        self.max_backoff = 300  # 5 minutes max
    
    def wait_if_needed(self):
        """Wait if we're approaching rate limits"""
        now = time.time()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        if len(self.requests) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.requests[0]) + 1
            logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        
        self.requests.append(now)
    
    def exponential_backoff(self, exception: Exception):
        """Handle API errors with exponential backoff"""
        if isinstance(exception, prawcore.exceptions.TooManyRequests):
            logger.warning(f"Rate limited, backing off for {self.backoff_time} seconds")
            time.sleep(self.backoff_time)
            self.backoff_time = min(self.backoff_time * 2, self.max_backoff)
        elif isinstance(exception, prawcore.exceptions.ServerError):
            logger.warning(f"Server error, retrying in {self.backoff_time} seconds")
            time.sleep(self.backoff_time)
            self.backoff_time = min(self.backoff_time * 1.5, self.max_backoff)
        else:
            # Reset backoff on successful requests
            self.backoff_time = 1
            raise exception

class RedditDatabase:
    """Database manager for storing scraped data"""
    
    def __init__(self, db_path: str = "reddit_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT,
                selftext TEXT,
                author TEXT,
                created_utc REAL,
                score INTEGER,
                num_comments INTEGER,
                url TEXT,
                permalink TEXT,
                subreddit TEXT,
                upvote_ratio REAL,
                is_self BOOLEAN,
                link_flair_text TEXT,
                post_hint TEXT,
                hash TEXT UNIQUE,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                post_id TEXT,
                parent_id TEXT,
                body TEXT,
                author TEXT,
                created_utc REAL,
                score INTEGER,
                permalink TEXT,
                depth INTEGER,
                is_submitter BOOLEAN,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')
        
        # Progress tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_progress (
                strategy TEXT,
                sort_method TEXT,
                time_filter TEXT,
                last_post_id TEXT,
                last_created_utc REAL,
                completed BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_created_utc ON posts(created_utc)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_hash ON posts(hash)')
        
        conn.commit()
        conn.close()
    
    def save_post(self, post: RedditPost) -> bool:
        """Save post to database, return True if new post"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO posts 
                (id, title, selftext, author, created_utc, score, num_comments, 
                 url, permalink, subreddit, upvote_ratio, is_self, 
                 link_flair_text, post_hint, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post.id, post.title, post.selftext, post.author, post.created_utc,
                post.score, post.num_comments, post.url, post.permalink,
                post.subreddit, post.upvote_ratio, post.is_self,
                post.link_flair_text, post.post_hint, post.get_hash()
            ))
            
            is_new = cursor.rowcount > 0
            conn.commit()
            return is_new
        except sqlite3.IntegrityError:
            return False  # Duplicate
        finally:
            conn.close()
    
    def save_comment(self, comment: RedditComment):
        """Save comment to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO comments 
            (id, post_id, parent_id, body, author, created_utc, score, 
             permalink, depth, is_submitter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            comment.id, comment.post_id, comment.parent_id, comment.body,
            comment.author, comment.created_utc, comment.score,
            comment.permalink, comment.depth, comment.is_submitter
        ))
        
        conn.commit()
        conn.close()
    
    def get_scraped_post_ids(self) -> Set[str]:
        """Get all scraped post IDs for deduplication"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM posts')
        post_ids = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        return post_ids
    
    def get_posts_without_comments(self) -> List[str]:
        """Get post IDs that don't have comments scraped yet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id FROM posts p
            LEFT JOIN comments c ON p.id = c.post_id
            WHERE c.post_id IS NULL AND p.num_comments > 0
        ''')
        
        post_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return post_ids
    
    def update_progress(self, strategy: str, sort_method: str, time_filter: str, 
                       last_post_id: str, last_created_utc: float, completed: bool = False):
        """Update scraping progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO scraping_progress
            (strategy, sort_method, time_filter, last_post_id, last_created_utc, completed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (strategy, sort_method, time_filter, last_post_id, last_created_utc, completed))
        
        conn.commit()
        conn.close()

class RedditScraper:
    """Main Reddit scraping class with multi-strategy approach"""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        self.rate_limiter = RateLimiter()
        self.database = RedditDatabase()
        self.scraped_posts = self.database.get_scraped_post_ids()
        
        # Strategy tracking
        self.sort_methods = ['hot', 'new', 'top']
        self.time_filters = ['hour', 'day', 'week', 'month', 'year', 'all']
        
        logger.info(f"Initialized scraper. Already have {len(self.scraped_posts)} posts in database")
    
    def scrape_subreddit_comprehensive(self, subreddit_name: str):
        """Main method to scrape subreddit using all strategies"""
        logger.info(f"Starting comprehensive scrape of r/{subreddit_name}")
        
        subreddit = self.reddit.subreddit(subreddit_name)
        
        # Strategy 1: Sort-based collection with time filters
        self._scrape_by_sort_methods(subreddit)
        
        # Strategy 2: Time-based segmentation
        self._scrape_by_time_periods(subreddit)
        
        # Strategy 3: Search-based collection
        self._scrape_by_search_terms(subreddit)
        
        # Strategy 4: User-based collection
        self._scrape_by_active_users(subreddit)
        
        # Final step: Scrape comments for all posts
        self._scrape_missing_comments()
        
        logger.info(f"Comprehensive scrape completed for r/{subreddit_name}")
    
    def _scrape_by_sort_methods(self, subreddit):
        """Strategy 1: Use different sort methods and time filters"""
        logger.info("Starting sort-based collection strategy")
        
        for sort_method in self.sort_methods:
            for time_filter in self.time_filters if sort_method == 'top' else [None]:
                try:
                    self._scrape_with_sort(subreddit, sort_method, time_filter)
                except Exception as e:
                    logger.error(f"Error in sort method {sort_method}/{time_filter}: {e}")
                    self.rate_limiter.exponential_backoff(e)
    
    def _scrape_with_sort(self, subreddit, sort_method: str, time_filter: Optional[str]):
        """Scrape posts using specific sort method"""
        logger.info(f"Scraping with sort: {sort_method}, time_filter: {time_filter}")
        
        self.rate_limiter.wait_if_needed()
        
        try:
            if sort_method == 'hot':
                posts = subreddit.hot(limit=None)
            elif sort_method == 'new':
                posts = subreddit.new(limit=None)
            elif sort_method == 'top':
                posts = subreddit.top(time_filter=time_filter or 'all', limit=None)
            
            new_posts_count = 0
            total_processed = 0
            
            for post in posts:
                if self._process_post(post):
                    new_posts_count += 1
                
                total_processed += 1
                
                # Log progress every 100 posts
                if total_processed % 100 == 0:
                    logger.info(f"Processed {total_processed} posts, {new_posts_count} new")
                
                # Respect rate limits
                if total_processed % 50 == 0:
                    self.rate_limiter.wait_if_needed()
            
            logger.info(f"Completed {sort_method}/{time_filter}: {new_posts_count} new posts out of {total_processed}")
            
        except Exception as e:
            logger.error(f"Error scraping {sort_method}/{time_filter}: {e}")
            self.rate_limiter.exponential_backoff(e)
    
    def _scrape_by_time_periods(self, subreddit):
        """Strategy 2: Time-based segmentation to get historical posts"""
        logger.info("Starting time-based segmentation strategy")
        
        # Get subreddit creation date or start from a reasonable point
        end_date = datetime.now()
        start_date = datetime(2020, 1, 1)  # Adjust based on subreddit age
        
        # Split into monthly segments
        current_date = start_date
        
        while current_date < end_date:
            next_date = current_date + timedelta(days=30)
            if next_date > end_date:
                next_date = end_date
            
            try:
                self._scrape_time_range(subreddit, current_date, next_date)
            except Exception as e:
                logger.error(f"Error scraping time range {current_date} to {next_date}: {e}")
                self.rate_limiter.exponential_backoff(e)
            
            current_date = next_date
    
    def _scrape_time_range(self, subreddit, start_date: datetime, end_date: datetime):
        """Scrape posts within a specific time range using search"""
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        
        logger.info(f"Scraping time range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Use Reddit search with timestamp filters
        query = f"subreddit:{subreddit.display_name} timestamp:{start_timestamp}..{end_timestamp}"
        
        try:
            search_results = self.reddit.subreddit('all').search(
                query, 
                sort='new', 
                time_filter='all', 
                limit=None
            )
            
            new_posts_count = 0
            for post in search_results:
                if post.subreddit.display_name.lower() == subreddit.display_name.lower():
                    if self._process_post(post):
                        new_posts_count += 1
            
            logger.info(f"Time range {start_date.strftime('%Y-%m-%d')}: {new_posts_count} new posts")
            
        except Exception as e:
            logger.error(f"Error in time range search: {e}")
            self.rate_limiter.exponential_backoff(e)
    
    def _scrape_by_search_terms(self, subreddit):
        """Strategy 3: Search-based collection using common terms"""
        logger.info("Starting search-based collection strategy")
        
        # Get common terms from already scraped post titles
        search_terms = self._extract_search_terms()
        
        for term in search_terms:
            try:
                self._scrape_by_search_term(subreddit, term)
                self.rate_limiter.wait_if_needed()
            except Exception as e:
                logger.error(f"Error searching for term '{term}': {e}")
                self.rate_limiter.exponential_backoff(e)
    
    def _extract_search_terms(self) -> List[str]:
        """Extract common terms from existing post titles for search"""
        # This could be enhanced with NLP, but for now use simple approach
        common_terms = [
            "question", "help", "issue", "problem", "tutorial", "guide",
            "announcement", "update", "discussion", "review", "comparison",
            "tips", "tricks", "best", "worst", "opinion", "thoughts"
        ]
        
        # Add subreddit-specific terms for notebookLLM
        if True:  # You can make this conditional based on subreddit
            common_terms.extend([
                "notebook", "llm", "ai", "model", "chat", "conversation",
                "prompt", "generation", "training", "fine-tune", "dataset"
            ])
        
        return common_terms
    
    def _scrape_by_search_term(self, subreddit, search_term: str):
        """Scrape posts matching a specific search term"""
        logger.info(f"Searching for posts with term: '{search_term}'")
        
        try:
            search_results = subreddit.search(
                search_term, 
                sort='new', 
                time_filter='all', 
                limit=1000
            )
            
            new_posts_count = 0
            for post in search_results:
                if self._process_post(post):
                    new_posts_count += 1
            
            logger.info(f"Search term '{search_term}': {new_posts_count} new posts")
            
        except Exception as e:
            logger.error(f"Error searching for '{search_term}': {e}")
            self.rate_limiter.exponential_backoff(e)
    
    def _scrape_by_active_users(self, subreddit):
        """Strategy 4: Find active users and scrape their posts"""
        logger.info("Starting user-based collection strategy")
        
        # Get active users from recent posts
        active_users = set()
        
        try:
            recent_posts = list(subreddit.new(limit=200))
            for post in recent_posts:
                if hasattr(post, 'author') and post.author:
                    active_users.add(post.author.name)
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return
        
        # Scrape posts from each active user
        for username in list(active_users)[:50]:  # Limit to top 50 users
            try:
                self._scrape_user_posts(username, subreddit.display_name)
                self.rate_limiter.wait_if_needed()
            except Exception as e:
                logger.error(f"Error scraping user {username}: {e}")
                self.rate_limiter.exponential_backoff(e)
    
    def _scrape_user_posts(self, username: str, subreddit_name: str):
        """Scrape posts from a specific user in the subreddit"""
        try:
            user = self.reddit.redditor(username)
            submissions = user.submissions.new(limit=100)
            
            new_posts_count = 0
            for post in submissions:
                if post.subreddit.display_name.lower() == subreddit_name.lower():
                    if self._process_post(post):
                        new_posts_count += 1
            
            if new_posts_count > 0:
                logger.info(f"User {username}: {new_posts_count} new posts")
                
        except Exception as e:
            logger.error(f"Error scraping user {username}: {e}")
    
    def _process_post(self, post) -> bool:
        """Process a single post and return True if it's new"""
        try:
            # Skip if already processed
            if post.id in self.scraped_posts:
                return False
            
            reddit_post = RedditPost(
                id=post.id,
                title=post.title,
                selftext=getattr(post, 'selftext', ''),
                author=post.author.name if post.author else '[deleted]',
                created_utc=post.created_utc,
                score=post.score,
                num_comments=post.num_comments,
                url=post.url,
                permalink=post.permalink,
                subreddit=post.subreddit.display_name,
                upvote_ratio=getattr(post, 'upvote_ratio', 0.0),
                is_self=post.is_self,
                link_flair_text=getattr(post, 'link_flair_text', None),
                post_hint=getattr(post, 'post_hint', None)
            )
            
            is_new = self.database.save_post(reddit_post)
            if is_new:
                self.scraped_posts.add(post.id)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing post {post.id}: {e}")
            return False
    
    def _scrape_missing_comments(self):
        """Scrape comments for posts that don't have comments yet"""
        logger.info("Starting comment collection for posts without comments")
        
        posts_without_comments = self.database.get_posts_without_comments()
        logger.info(f"Found {len(posts_without_comments)} posts without comments")
        
        for i, post_id in enumerate(posts_without_comments):
            try:
                self._scrape_post_comments(post_id)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Scraped comments for {i + 1}/{len(posts_without_comments)} posts")
                
                self.rate_limiter.wait_if_needed()
                
            except Exception as e:
                logger.error(f"Error scraping comments for post {post_id}: {e}")
                self.rate_limiter.exponential_backoff(e)
    
    def _scrape_post_comments(self, post_id: str):
        """Scrape all comments for a specific post"""
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=None)  # Get all comments
            
            comment_count = 0
            
            def process_comment(comment, depth=0):
                nonlocal comment_count
                
                if hasattr(comment, 'body') and comment.body != '[deleted]':
                    reddit_comment = RedditComment(
                        id=comment.id,
                        post_id=post_id,
                        parent_id=comment.parent_id,
                        body=comment.body,
                        author=comment.author.name if comment.author else '[deleted]',
                        created_utc=comment.created_utc,
                        score=comment.score,
                        permalink=comment.permalink,
                        depth=depth,
                        is_submitter=comment.is_submitter
                    )
                    
                    self.database.save_comment(reddit_comment)
                    comment_count += 1
                
                # Process replies recursively
                if hasattr(comment, 'replies'):
                    for reply in comment.replies:
                        process_comment(reply, depth + 1)
            
            # Process all top-level comments
            for comment in submission.comments:
                process_comment(comment)
            
            if comment_count > 0:
                logger.info(f"Scraped {comment_count} comments for post {post_id}")
                
        except Exception as e:
            logger.error(f"Error scraping comments for post {post_id}: {e}")
    
    def get_stats(self) -> Dict:
        """Get scraping statistics"""
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM posts')
        total_posts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM comments')
        total_comments = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT post_id) FROM comments')
        posts_with_comments = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(created_utc), MAX(created_utc) FROM posts')
        time_range = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_posts': total_posts,
            'total_comments': total_comments,
            'posts_with_comments': posts_with_comments,
            'earliest_post': datetime.fromtimestamp(time_range[0]) if time_range[0] else None,
            'latest_post': datetime.fromtimestamp(time_range[1]) if time_range[1] else None
        }

def main():
    """Main function to run the scraper"""
    # Reddit API credentials - you need to get these from Reddit
    CLIENT_ID = "your_client_id_here"
    CLIENT_SECRET = "your_client_secret_here"
    USER_AGENT = "reddit_scraper_v1.0_by_your_username"
    
    # Initialize scraper
    scraper = RedditScraper(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    
    # Target subreddit
    subreddit_name = "notebookLLM"
    
    try:
        # Run comprehensive scraping
        scraper.scrape_subreddit_comprehensive(subreddit_name)
        
        # Print final statistics
        stats = scraper.get_stats()
        logger.info("=== SCRAPING COMPLETED ===")
        logger.info(f"Total posts collected: {stats['total_posts']}")
        logger.info(f"Total comments collected: {stats['total_comments']}")
        logger.info(f"Posts with comments: {stats['posts_with_comments']}")
        logger.info(f"Date range: {stats['earliest_post']} to {stats['latest_post']}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main() 
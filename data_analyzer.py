#!/usr/bin/env python3
"""
Reddit Data Analyzer and Exporter
=================================

Utility script to analyze and export scraped Reddit data.
Provides insights into the scraped dataset and export capabilities.
"""

import sqlite3
import json
import csv
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re

class RedditDataAnalyzer:
    """Analyze and export scraped Reddit data"""
    
    def __init__(self, db_path: str = "reddit_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
    def get_overview_stats(self) -> Dict:
        """Get overview statistics of the dataset"""
        cursor = self.conn.cursor()
        
        # Basic counts
        cursor.execute('SELECT COUNT(*) FROM posts')
        total_posts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM comments')
        total_comments = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT author) FROM posts WHERE author != "[deleted]"')
        unique_authors = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT post_id) FROM comments')
        posts_with_comments = cursor.fetchone()[0]
        
        # Time range
        cursor.execute('SELECT MIN(created_utc), MAX(created_utc) FROM posts')
        time_range = cursor.fetchone()
        
        # Average stats
        cursor.execute('SELECT AVG(score), AVG(num_comments) FROM posts')
        avg_stats = cursor.fetchone()
        
        # Top scoring post
        cursor.execute('SELECT title, score FROM posts ORDER BY score DESC LIMIT 1')
        top_post = cursor.fetchone()
        
        return {
            'total_posts': total_posts,
            'total_comments': total_comments,
            'unique_authors': unique_authors,
            'posts_with_comments': posts_with_comments,
            'coverage_percentage': (posts_with_comments / total_posts * 100) if total_posts > 0 else 0,
            'earliest_post': datetime.fromtimestamp(time_range[0]) if time_range[0] else None,
            'latest_post': datetime.fromtimestamp(time_range[1]) if time_range[1] else None,
            'avg_score': round(avg_stats[0], 2) if avg_stats[0] else 0,
            'avg_comments': round(avg_stats[1], 2) if avg_stats[1] else 0,
            'top_post_title': top_post[0] if top_post else None,
            'top_post_score': top_post[1] if top_post else 0
        }
    
    def get_temporal_analysis(self) -> Dict:
        """Analyze posting patterns over time"""
        cursor = self.conn.cursor()
        
        # Posts per month
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', datetime(created_utc, 'unixepoch')) as month,
                COUNT(*) as post_count
            FROM posts
            GROUP BY month
            ORDER BY month
        ''')
        monthly_posts = dict(cursor.fetchall())
        
        # Posts per day of week
        cursor.execute('''
            SELECT 
                strftime('%w', datetime(created_utc, 'unixepoch')) as day_of_week,
                COUNT(*) as post_count
            FROM posts
            GROUP BY day_of_week
            ORDER BY day_of_week
        ''')
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        weekly_posts = {day_names[int(row[0])]: row[1] for row in cursor.fetchall()}
        
        # Posts per hour
        cursor.execute('''
            SELECT 
                strftime('%H', datetime(created_utc, 'unixepoch')) as hour,
                COUNT(*) as post_count
            FROM posts
            GROUP BY hour
            ORDER BY hour
        ''')
        hourly_posts = {f"{int(row[0]):02d}:00": row[1] for row in cursor.fetchall()}
        
        return {
            'monthly_posts': monthly_posts,
            'weekly_posts': weekly_posts,
            'hourly_posts': hourly_posts
        }
    
    def get_author_analysis(self) -> Dict:
        """Analyze author activity"""
        cursor = self.conn.cursor()
        
        # Top authors by post count
        cursor.execute('''
            SELECT author, COUNT(*) as post_count
            FROM posts
            WHERE author != "[deleted]"
            GROUP BY author
            ORDER BY post_count DESC
            LIMIT 20
        ''')
        top_authors = dict(cursor.fetchall())
        
        # Top authors by total score
        cursor.execute('''
            SELECT author, SUM(score) as total_score
            FROM posts
            WHERE author != "[deleted]"
            GROUP BY author
            ORDER BY total_score DESC
            LIMIT 20
        ''')
        top_scored_authors = dict(cursor.fetchall())
        
        # Author activity distribution
        cursor.execute('''
            SELECT post_count, COUNT(*) as author_count
            FROM (
                SELECT author, COUNT(*) as post_count
                FROM posts
                WHERE author != "[deleted]"
                GROUP BY author
            )
            GROUP BY post_count
            ORDER BY post_count
        ''')
        activity_distribution = dict(cursor.fetchall())
        
        return {
            'top_authors_by_posts': top_authors,
            'top_authors_by_score': top_scored_authors,
            'activity_distribution': activity_distribution
        }
    
    def get_content_analysis(self) -> Dict:
        """Analyze content patterns"""
        cursor = self.conn.cursor()
        
        # Post type distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN is_self = 1 THEN 'Text Post'
                    ELSE 'Link Post'
                END as post_type,
                COUNT(*) as count
            FROM posts
            GROUP BY is_self
        ''')
        post_types = dict(cursor.fetchall())
        
        # Most common words in titles
        cursor.execute('SELECT title FROM posts')
        titles = [row[0] for row in cursor.fetchall()]
        title_words = []
        for title in titles:
            # Simple word extraction (can be enhanced with NLP)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
            title_words.extend(words)
        
        common_words = dict(Counter(title_words).most_common(30))
        
        # Score distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN score < 0 THEN 'Negative'
                    WHEN score = 0 THEN 'Zero'
                    WHEN score BETWEEN 1 AND 10 THEN '1-10'
                    WHEN score BETWEEN 11 AND 50 THEN '11-50'
                    WHEN score BETWEEN 51 AND 100 THEN '51-100'
                    ELSE '100+'
                END as score_range,
                COUNT(*) as count
            FROM posts
            GROUP BY score_range
        ''')
        score_distribution = dict(cursor.fetchall())
        
        return {
            'post_types': post_types,
            'common_title_words': common_words,
            'score_distribution': score_distribution
        }
    
    def export_to_json(self, filename: str = "reddit_data_export.json"):
        """Export all data to JSON format"""
        cursor = self.conn.cursor()
        
        # Get all posts
        cursor.execute('''
            SELECT id, title, selftext, author, created_utc, score, num_comments,
                   url, permalink, subreddit, upvote_ratio, is_self, 
                   link_flair_text, post_hint
            FROM posts
            ORDER BY created_utc
        ''')
        
        posts = []
        for row in cursor.fetchall():
            post = {
                'id': row[0],
                'title': row[1],
                'selftext': row[2],
                'author': row[3],
                'created_utc': row[4],
                'created_datetime': datetime.fromtimestamp(row[4]).isoformat(),
                'score': row[5],
                'num_comments': row[6],
                'url': row[7],
                'permalink': row[8],
                'subreddit': row[9],
                'upvote_ratio': row[10],
                'is_self': bool(row[11]),
                'link_flair_text': row[12],
                'post_hint': row[13],
                'comments': []
            }
            
            # Get comments for this post
            cursor.execute('''
                SELECT id, parent_id, body, author, created_utc, score,
                       permalink, depth, is_submitter
                FROM comments
                WHERE post_id = ?
                ORDER BY created_utc
            ''', (row[0],))
            
            for comment_row in cursor.fetchall():
                comment = {
                    'id': comment_row[0],
                    'parent_id': comment_row[1],
                    'body': comment_row[2],
                    'author': comment_row[3],
                    'created_utc': comment_row[4],
                    'created_datetime': datetime.fromtimestamp(comment_row[4]).isoformat(),
                    'score': comment_row[5],
                    'permalink': comment_row[6],
                    'depth': comment_row[7],
                    'is_submitter': bool(comment_row[8])
                }
                post['comments'].append(comment)
            
            posts.append(post)
        
        # Export to JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'total_posts': len(posts),
                    'total_comments': sum(len(post['comments']) for post in posts)
                },
                'posts': posts
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(posts)} posts to {filename}")
    
    def export_to_csv(self, posts_filename: str = "posts.csv", comments_filename: str = "comments.csv"):
        """Export data to CSV format"""
        cursor = self.conn.cursor()
        
        # Export posts
        cursor.execute('''
            SELECT id, title, selftext, author, created_utc, score, num_comments,
                   url, permalink, subreddit, upvote_ratio, is_self, 
                   link_flair_text, post_hint
            FROM posts
            ORDER BY created_utc
        ''')
        
        posts_data = []
        for row in cursor.fetchall():
            posts_data.append({
                'id': row[0],
                'title': row[1],
                'selftext': row[2],
                'author': row[3],
                'created_utc': row[4],
                'created_datetime': datetime.fromtimestamp(row[4]).isoformat(),
                'score': row[5],
                'num_comments': row[6],
                'url': row[7],
                'permalink': row[8],
                'subreddit': row[9],
                'upvote_ratio': row[10],
                'is_self': row[11],
                'link_flair_text': row[12],
                'post_hint': row[13]
            })
        
        df_posts = pd.DataFrame(posts_data)
        df_posts.to_csv(posts_filename, index=False)
        print(f"Exported {len(posts_data)} posts to {posts_filename}")
        
        # Export comments
        cursor.execute('''
            SELECT id, post_id, parent_id, body, author, created_utc, score,
                   permalink, depth, is_submitter
            FROM comments
            ORDER BY created_utc
        ''')
        
        comments_data = []
        for row in cursor.fetchall():
            comments_data.append({
                'id': row[0],
                'post_id': row[1],
                'parent_id': row[2],
                'body': row[3],
                'author': row[4],
                'created_utc': row[5],
                'created_datetime': datetime.fromtimestamp(row[5]).isoformat(),
                'score': row[6],
                'permalink': row[7],
                'depth': row[8],
                'is_submitter': row[9]
            })
        
        df_comments = pd.DataFrame(comments_data)
        df_comments.to_csv(comments_filename, index=False)
        print(f"Exported {len(comments_data)} comments to {comments_filename}")
    
    def generate_report(self, filename: str = "scraping_report.txt"):
        """Generate a comprehensive text report"""
        overview = self.get_overview_stats()
        temporal = self.get_temporal_analysis()
        authors = self.get_author_analysis()
        content = self.get_content_analysis()
        
        report = f"""
Reddit Scraping Report
=====================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW STATISTICS
==================
Total Posts: {overview['total_posts']:,}
Total Comments: {overview['total_comments']:,}
Unique Authors: {overview['unique_authors']:,}
Posts with Comments: {overview['posts_with_comments']:,} ({overview['coverage_percentage']:.1f}%)

Date Range: {overview['earliest_post']} to {overview['latest_post']}
Average Score per Post: {overview['avg_score']}
Average Comments per Post: {overview['avg_comments']}

Top Scoring Post: "{overview['top_post_title']}" (Score: {overview['top_post_score']})

TEMPORAL PATTERNS
================
Most Active Months (Top 5):
"""
        
        # Add temporal data
        sorted_months = sorted(temporal['monthly_posts'].items(), key=lambda x: x[1], reverse=True)[:5]
        for month, count in sorted_months:
            report += f"  {month}: {count:,} posts\n"
        
        report += "\nMost Active Days of Week:\n"
        sorted_days = sorted(temporal['weekly_posts'].items(), key=lambda x: x[1], reverse=True)
        for day, count in sorted_days:
            report += f"  {day}: {count:,} posts\n"
        
        # Add author data
        report += "\nTOP AUTHORS\n"
        report += "===========\n"
        report += "Most Active (by post count):\n"
        
        for i, (author, count) in enumerate(list(authors['top_authors_by_posts'].items())[:10], 1):
            report += f"  {i:2d}. {author}: {count} posts\n"
        
        report += "\nHighest Scoring (by total score):\n"
        for i, (author, score) in enumerate(list(authors['top_authors_by_score'].items())[:10], 1):
            report += f"  {i:2d}. {author}: {score:,} total score\n"
        
        # Add content analysis
        report += "\nCONTENT ANALYSIS\n"
        report += "===============\n"
        report += "Post Types:\n"
        for post_type, count in content['post_types'].items():
            percentage = (count / overview['total_posts'] * 100) if overview['total_posts'] > 0 else 0
            report += f"  {post_type}: {count:,} ({percentage:.1f}%)\n"
        
        report += "\nScore Distribution:\n"
        for score_range, count in content['score_distribution'].items():
            percentage = (count / overview['total_posts'] * 100) if overview['total_posts'] > 0 else 0
            report += f"  {score_range}: {count:,} ({percentage:.1f}%)\n"
        
        report += "\nMost Common Title Words (Top 15):\n"
        for i, (word, count) in enumerate(list(content['common_title_words'].items())[:15], 1):
            report += f"  {i:2d}. {word}: {count}\n"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Generated comprehensive report: {filename}")
        print("\nOVERVIEW:")
        print(f"Posts: {overview['total_posts']:,}")
        print(f"Comments: {overview['total_comments']:,}")
        print(f"Coverage: {overview['coverage_percentage']:.1f}%")
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    """Main function for the data analyzer"""
    analyzer = RedditDataAnalyzer()
    
    try:
        # Generate comprehensive report
        print("Generating comprehensive analysis report...")
        analyzer.generate_report()
        
        # Export data in multiple formats
        print("\nExporting data...")
        analyzer.export_to_json()
        analyzer.export_to_csv()
        
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main() 
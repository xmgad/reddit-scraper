#!/usr/bin/env python3
"""
Data Pipeline Orchestrator
=========================
Manages the flow from Reddit scraping → LLM processing → RAG preparation
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any
import logging

class DataPipelineOrchestrator:
    """Orchestrates data flow through the entire pipeline"""
    
    def __init__(self, sqlite_db: str = "reddit_data.db"):
        self.sqlite_db = sqlite_db
        self.logger = logging.getLogger(__name__)
    
    def export_for_llm_processing(self, output_file: str = "llm_input.json") -> Dict:
        """Export scraped data in optimal format for LLM theme analysis"""
        
        conn = sqlite3.connect(self.sqlite_db)
        cursor = conn.cursor()
        
        # Get all posts with their comments in hierarchical structure
        cursor.execute('SELECT * FROM posts ORDER BY created_utc DESC')
        posts = cursor.fetchall()
        
        llm_ready_data = []
        
        for post_row in posts:
            post_data = {
                "post_id": post_row[0],
                "title": post_row[1],
                "content": post_row[2],
                "author": post_row[3],
                "created_utc": post_row[4],
                "score": post_row[5],
                "num_comments": post_row[6],
                "url": post_row[7],
                "subreddit": post_row[9],
                "comment_tree": self._build_comment_tree(post_row[0])
            }
            llm_ready_data.append(post_data)
        
        # Export for LLM processing
        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_posts": len(llm_ready_data),
                "purpose": "LLM_THEME_ANALYSIS"
            },
            "posts": llm_ready_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported {len(llm_ready_data)} posts for LLM processing: {output_file}")
        conn.close()
        return export_data
    
    def _build_comment_tree(self, post_id: str) -> List[Dict]:
        """Build hierarchical comment tree for a post"""
        conn = sqlite3.connect(self.sqlite_db)
        cursor = conn.cursor()
        
        # Get all comments for this post
        cursor.execute('''
            SELECT id, parent_id, body, author, created_utc, score, depth
            FROM comments 
            WHERE post_id = ? 
            ORDER BY created_utc
        ''', (post_id,))
        
        comments = cursor.fetchall()
        comment_dict = {}
        root_comments = []
        
        # Build comment objects
        for comment in comments:
            comment_obj = {
                "id": comment[0],
                "parent_id": comment[1],
                "content": comment[2],
                "author": comment[3],
                "created_utc": comment[4],
                "score": comment[5],
                "depth": comment[6],
                "replies": []
            }
            comment_dict[comment[0]] = comment_obj
        
        # Build hierarchy
        for comment in comments:
            comment_id = comment[0]
            parent_id = comment[1]
            
            if parent_id.startswith('t3_'):  # Top-level comment (parent is post)
                root_comments.append(comment_dict[comment_id])
            else:
                # Find parent comment and add as reply
                parent_comment_id = parent_id.replace('t1_', '')
                if parent_comment_id in comment_dict:
                    comment_dict[parent_comment_id]["replies"].append(comment_dict[comment_id])
        
        conn.close()
        return root_comments
    
    def prepare_for_rag_system(self, llm_results_file: str, output_file: str = "rag_ready.json"):
        """Prepare LLM-analyzed data for RAG system and dashboard"""
        
        with open(llm_results_file, 'r') as f:
            llm_data = json.load(f)
        
        rag_ready_documents = []
        
        for post in llm_data.get("posts", []):
            # Combine post and comments into searchable content
            searchable_content = self._create_searchable_content(post)
            
            document = {
                "doc_id": post["post_id"],
                "title": post["title"],
                "content": searchable_content,
                "metadata": {
                    "post_id": post["post_id"],
                    "author": post["author"],
                    "score": post["score"],
                    "created_date": datetime.fromtimestamp(post["created_utc"]).isoformat(),
                    "subreddit": post["subreddit"],
                    "num_comments": post["num_comments"]
                },
                "llm_analysis": post.get("llm_analysis", {}),  # Results from your LLM processing
                "themes": post.get("llm_analysis", {}).get("themes", []),
                "sentiment": post.get("llm_analysis", {}).get("sentiment", "neutral")
            }
            
            rag_ready_documents.append(document)
        
        # Export for RAG system
        rag_export = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_documents": len(rag_ready_documents),
                "purpose": "RAG_SYSTEM_DASHBOARD"
            },
            "documents": rag_ready_documents
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rag_export, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Prepared {len(rag_ready_documents)} documents for RAG system: {output_file}")
        return rag_export
    
    def _create_searchable_content(self, post: Dict) -> str:
        """Combine post and comments into searchable text"""
        content_parts = [
            f"Title: {post['title']}",
            f"Content: {post['content']}"
        ]
        
        # Add comments
        def extract_comment_text(comments, depth=0):
            text_parts = []
            for comment in comments:
                text_parts.append(f"Comment: {comment['content']}")
                # Recursively add replies
                if comment.get('replies'):
                    text_parts.extend(extract_comment_text(comment['replies'], depth + 1))
            return text_parts
        
        if post.get('comment_tree'):
            content_parts.extend(extract_comment_text(post['comment_tree']))
        
        return "\n".join(content_parts)

def main():
    """Demo the pipeline orchestration"""
    orchestrator = DataPipelineOrchestrator()
    
    # Step 1: Export for LLM processing
    print("🔄 Exporting data for LLM theme analysis...")
    orchestrator.export_for_llm_processing("llm_input.json")
    
    print("📝 Next steps:")
    print("1. Process llm_input.json with your LLM for theme analysis")
    print("2. Save results as llm_results.json") 
    print("3. Run: orchestrator.prepare_for_rag_system('llm_results.json')")
    print("4. Use rag_ready.json for your dashboard and RAG system")

if __name__ == "__main__":
    main() 
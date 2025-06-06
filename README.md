# Reddit Scraper - Free Tier Optimized

A comprehensive Reddit scraping pipeline designed to work within the constraints of Reddit's free tier API, using multiple strategies to maximize data collection while respecting rate limits.

## 🚀 Key Features

- **Multi-Strategy Collection**: 4 different approaches to maximize coverage
- **Rate Limiting & Resilience**: Smart throttling and exponential backoff
- **Comprehensive Data**: Posts + all comments with full metadata
- **Deduplication**: Automatic removal of duplicate posts across strategies
- **Progress Tracking**: Resume scraping from where you left off
- **Multiple Export Formats**: JSON, CSV, and analysis reports
- **LLM-Ready Outputs**: Structured JSON exports optimized for AI/ML processing
- **RAG Pipeline Support**: Clean, hierarchical data structure for retrieval systems
- **Secure Configuration**: Environment-based credential management

## 📋 API Limitations We Work Around

Reddit's free tier has several constraints:
- **Rate Limits**: ~60 requests per minute
- **Pagination Limit**: ~1,000 posts max with `after` parameter
- **Search Limitations**: Limited historical search capabilities
- **No Direct Historical Access**: Can't directly query old posts

## 🏗️ Architecture Overview

### Multi-Strategy Approach

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Sort-Based    │    │  Time-Based     │    │ Search-Based    │
│   Collection    │    │  Segmentation   │    │  Collection     │
│                 │    │                 │    │                 │
│ • hot           │    │ • Monthly       │    │ • Keywords      │
│ • new           │    │   chunks        │    │ • Common terms  │
│ • top (all      │    │ • Date ranges   │    │ • User posts    │
│   time periods) │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Deduplication  │
                    │   & Storage     │
                    │                 │
                    │ • SQLite DB     │
                    │ • Hash-based    │
                    │ • Progress      │
                    │   tracking      │
                    └─────────────────┘
```

### The Four Strategies

1. **Sort-Based Collection** (`hot`, `new`, `top`)
   - Gets the most visible/recent content
   - Uses different time filters for `top` sorting
   - Covers ~1,000 posts per sort method

2. **Time-Based Segmentation**
   - Splits scraping into monthly chunks
   - Uses search with timestamp filters
   - Captures historical content

3. **Search-Based Collection**
   - Uses common keywords to find missed posts
   - Searches for subreddit-specific terms
   - Catches posts that don't appear in other methods

4. **User-Based Collection**
   - Identifies active users from recent posts
   - Scrapes their post history in the subreddit
   - Finds posts that might be missed otherwise

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Fill in the details:
   - **Name**: Your app name (e.g., "My Reddit Scraper")
   - **Description**: Brief description
   - **Redirect URI**: `http://localhost:8080` (required but not used)
5. Copy the `CLIENT_ID` and `CLIENT_SECRET`

### 3. Configure the Scraper

Create a `.env` file in the project root directory with your Reddit API credentials:

```bash
# Reddit API Configuration
CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"
USER_AGENT = "reddit_scraper_v1.0_by_your_reddit_username"
```

**Important**: 
- Replace the placeholder values with your actual Reddit API credentials
- The `.env` file is automatically ignored by git to keep your credentials secure
- Make sure your `USER_AGENT` includes your Reddit username for API compliance

### 4. Run the Scraper

```bash
python reddit_scraper.py
```

## 📊 Data Processing & Export

The pipeline provides multiple ways to access and process your scraped data:

### 1. Direct Database Access
Data is stored in SQLite (`reddit_data.db`) for efficient querying and analysis.

### 2. Export for Further Processing

```bash
python data_analyzer.py
```

This generates multiple output formats:

#### For Data Analysis & Reporting:
- `scraping_report.txt`: Comprehensive analysis with statistics and insights
- `posts.csv` & `comments.csv`: Tabular data for spreadsheet analysis

#### For LLM & AI Processing:
- `reddit_data_export.json`: **Structured JSON optimized for AI/ML workflows**

### 3. LLM-Ready JSON Structure

The JSON export is specifically designed for Large Language Model processing:

```json
{
  "metadata": {
    "total_posts": 150,
    "total_comments": 1247,
    "subreddit": "notebookLLM",
    "export_timestamp": "2024-01-15T10:30:00Z",
    "date_range": ["2023-01-01", "2024-01-15"]
  },
  "posts": [
    {
      "id": "abc123",
      "title": "How to use NotebookLM effectively",
      "content": "Full post text...",
      "metadata": {
        "author": "username",
        "created_utc": 1704123456,
        "score": 45,
        "num_comments": 12
      },
      "comments": [
        {
          "id": "def456",
          "content": "Great question! Here's my approach...",
          "author": "commenter1",
          "score": 8,
          "depth": 0,
          "replies": [...]
        }
      ]
    }
  ]
}
```

### 4. Use Cases for Exported Data

#### Retrieval-Augmented Generation (RAG):
- Clean, hierarchical structure perfect for vector databases
- Full conversation context preserved
- Rich metadata for filtering and ranking

#### LLM Fine-tuning:
- Conversational format ideal for training dialogue models
- Complete threads maintain context relationships
- Quality indicators (scores, timestamps) for data filtering

#### Thematic Analysis:
- Post titles and content ready for topic modeling
- Temporal data for trend analysis
- Community interaction patterns via comment threads

#### Knowledge Base Creation:
- Question-answer pairs from post-comment relationships
- FAQ generation from common discussion patterns
- Expert knowledge extraction from high-scoring content

## 🗄️ Database Schema

The scraper stores data in SQLite with the following structure:

### Posts Table
- `id`: Reddit post ID
- `title`: Post title
- `selftext`: Post content (for text posts)
- `author`: Username of poster
- `created_utc`: Timestamp when posted
- `score`: Upvotes - downvotes
- `num_comments`: Number of comments
- `url`: External URL (for link posts)
- `permalink`: Reddit permalink
- `subreddit`: Subreddit name
- `upvote_ratio`: Ratio of upvotes to total votes
- Additional metadata fields...

### Comments Table
- `id`: Reddit comment ID
- `post_id`: Parent post ID (foreign key)
- `parent_id`: Parent comment ID (for threaded replies)
- `body`: Comment text
- `author`: Username of commenter
- `created_utc`: Timestamp when commented
- `score`: Comment score
- `depth`: Reply depth in thread
- Additional metadata fields...

## 🎯 Optimization Strategies

### Rate Limiting
- Tracks requests per minute
- Automatic throttling when approaching limits
- Exponential backoff on rate limit errors

### Deduplication
- Hash-based duplicate detection
- Cross-strategy validation
- Prevents re-processing of known posts

### Resume Capability
- Progress tracking in database
- Can restart scraping from interruption point
- Intelligent skipping of already-processed content

### Memory Efficiency
- Processes posts one at a time
- Commits to database frequently
- Minimal memory footprint for large subreddits

## 📈 Expected Performance

For a typical subreddit like `notebookLLM`:

- **Coverage**: 80-95% of all posts (depending on subreddit size and age)
- **Time**: 2-4 minutes for small subreddits (~100 posts), 2-6 hours for large ones
- **Rate Compliance**: Stays well within free tier limits (60 requests/minute)
- **Data Quality**: Full post + comment data with all metadata
- **Export Size**: JSON files typically 2-10x larger than CSV due to rich structure

## 🔧 Customization

### For Different Subreddits

1. Change the subreddit name in the `main()` function of `reddit_scraper.py`
2. Customize search terms in `_extract_search_terms()` for subreddit-specific keywords
3. Adjust the start date in `_scrape_by_time_periods()` based on subreddit creation date

### Rate Limit Adjustment

```python
# In reddit_scraper.py, modify the RateLimiter initialization
rate_limiter = RateLimiter(max_requests_per_minute=45)  # More conservative
# or
rate_limiter = RateLimiter(max_requests_per_minute=90)  # More aggressive (use carefully)
```

### Search Terms Optimization

Add domain-specific terms to improve coverage:

```python
# In reddit_scraper.py, modify the _extract_search_terms() method
def _extract_search_terms(self) -> List[str]:
    common_terms = [
        # Add terms specific to your subreddit
        "specific_term_1", "specific_term_2", 
        # Common patterns in post titles
        "weekly thread", "monthly update", "discussion"
    ]
    return common_terms
```

## 🚨 Important Considerations

### Legal and Ethical
- Respect Reddit's Terms of Service
- Use collected data responsibly
- Consider privacy implications
- Don't overwhelm Reddit's servers

### Technical Limitations
- Free tier has hard limits
- Some very old posts might be missed
- Deleted content cannot be recovered
- Real-time scraping has delays

### Best Practices
- Run during off-peak hours when possible
- Monitor logs for errors and rate limiting
- Keep backups of your database
- Test with smaller subreddits first

## 📝 Troubleshooting

### Common Issues

1. **Rate Limited**
   ```
   Solution: The scraper handles this automatically with backoff.
   If persistent, reduce MAX_REQUESTS_PER_MINUTE in config.
   ```

2. **Authentication Errors**
   ```
   Check your .env file exists and contains valid credentials.
   Verify CLIENT_ID and CLIENT_SECRET are correct (no quotes needed in .env).
   Ensure USER_AGENT includes your Reddit username.
   ```

3. **No Posts Found**
   ```
   Verify subreddit name is correct (case-sensitive).
   Check if subreddit is private or restricted.
   ```

4. **Database Errors**
   ```
   Ensure write permissions in the directory.
   Check disk space availability.
   ```

## 🤝 Contributing

Feel free to enhance the scraper with:
- Additional scraping strategies
- Better error handling
- Performance optimizations
- Support for different data formats

## 📄 License

This project is for educational and research purposes. Ensure compliance with Reddit's API terms and your local regulations when using this tool.

---

**Note**: This scraper is designed to be respectful of Reddit's infrastructure while maximizing data collection within free tier constraints. Always prioritize ethical usage and compliance with platform terms of service. 
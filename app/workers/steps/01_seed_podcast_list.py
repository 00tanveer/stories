"""Step 1: Upload pod_urls.csv to R2."""

import os
import csv
import time
import json
import logging
from pathlib import Path
from tqdm import tqdm
from app.services.storage import Storage
from app.workers import dagmatic
from app.api.scrape_itunes import ITunesAPI
import sqlite3

# Environment-based path configuration
def _get_paths():
    """Get paths based on environment (development vs production)."""
    env = os.getenv("APP_ENV", "development").lower()
    
    if env == "production":
        return {
            "pod_urls": Path("/opt/stories/pod_urls.csv"),
            "metadata": Path("/opt/stories/podcasts_metadata.json"),
            "db": Path("/opt/stories/tech_podcasts.db")
        }
    else:
        # Development paths (relative to project root)
        return {
            "pod_urls": Path("data/podcasts/pod_urls.csv"),
            "metadata": Path("data/podcasts/podcasts_metadata.json"),
            "db": Path("data/podcasts/categories/technology/tech_podcasts.db")
        }

PATHS = _get_paths()
LOCAL_PATH = PATHS["pod_urls"]
LOCAL_METADATA_PATH = PATHS["metadata"]
LOCAL_DB_PATH = PATHS["db"]

# R2 storage keys
R2_POD_MANIFEST_KEY = "pod_urls.csv"
R2_POD_METADATA_KEY = "podcasts_metadata.json"

extra_podcasts = [
    ["A Life Engineered","technology","522818",5.0,3,5,11],
    ["The Knowledge Project","technology","522818",4.7,2558,9,260]
]

sql_query = '''
    select * from tech_podcasts_table
    where itunesId != '' 
    and category1 == 'technology'
    and (language == 'en' or language == 'en-us')
    and episodeCount > 10 
    and newestItemPubdate >= strftime('%s','now','-90 days')
    and popularityScore > 3
    and title != ''
    and description != ''
    and dead == 0;
'''

def from_db_sql_filtered(db_path=LOCAL_DB_PATH):
    """Fetch filtered podcasts from SQLite database."""
    import os
    abs_path = os.path.abspath(db_path)
    print(f"[DEBUG] Connecting to SQLite DB at: {abs_path}")
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        records = [dict(row) for row in rows]
        print(f"✅ Fetched {len(records)} podcasts from tech_podcasts.db")
        return records


def scrape_and_rank_podcasts(podcasts, top_n):
    """
    Scrape iTunes ratings for podcasts and rank them using Bayesian average.
    
    Args:
        podcasts: List of podcast dicts from database
        top_n: Number of top podcasts to return
        
    Returns:
        List of top-ranked podcasts with ratings merged
    """
    itunes = ITunesAPI()
    scraped_podcasts = []
    
    # Bayesian parameters
    C = 50  # Confidence threshold
    m = 4.0  # Prior mean rating
    
    print(f"🔍 Scraping iTunes ratings for {len(podcasts)} podcasts...")
    
    # Temporarily suppress iTunes API logging to keep progress bar visible
    itunes_logger = logging.getLogger('app.api.scrape_itunes')
    original_level = itunes_logger.level
    itunes_logger.setLevel(logging.WARNING)
    
    # Use tqdm progress bar for scraping with better formatting
    progress_bar = tqdm(
        total=len(podcasts), 
        desc="🎵 Scraping iTunes", 
        unit=" podcasts",
        position=0,
        leave=True,
        dynamic_ncols=True,
        miniters=1,
        maxinterval=0.5
    )
    
    try:
        for i, pod in enumerate(podcasts):
            itunes_id = pod.get('itunesId')
            if not itunes_id:
                progress_bar.update(1)
                continue
                
            try:
                # Scrape ratings from iTunes
                scraped = itunes.scrape_ratings(str(itunes_id))
                
                if scraped and scraped.get('rating') and scraped.get('numberOfRatings'):
                    # Merge podcast data with scraped ratings
                    merged = {**pod, **scraped}
                    
                    rating = scraped['rating']
                    num_ratings = scraped['numberOfRatings']
                    
                    # Only keep podcasts with rating >= 4.0
                    if rating >= 4.0:
                        # Calculate Bayesian score
                        bayesian_score = (C * m + num_ratings * rating) / (C + num_ratings)
                        
                        # Calculate composite score (50% Bayesian, 50% popularity)
                        normalized_bayesian = (bayesian_score - 4.0) / 1.0
                        normalized_popularity = min(pod.get('popularityScore', 0) / 100, 1.0)
                        composite_score = (0.5 * normalized_bayesian) + (0.5 * normalized_popularity)
                        
                        merged['bayesianScore'] = bayesian_score
                        merged['compositeScore'] = composite_score
                        scraped_podcasts.append(merged)
                        
                        # Update progress bar with cleaner stats
                        progress_bar.set_postfix_str(f"✅ Found: {len(scraped_podcasts)} | ⭐ {rating:.1f} ({num_ratings} reviews)")
                    else:
                        progress_bar.set_postfix_str(f"⚠️ Rating too low: {rating:.1f}")
                else:
                    progress_bar.set_postfix_str(f"❌ No rating data")
                
                # Rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                progress_bar.set_postfix_str(f"🚫 Error: {itunes_id}")
                time.sleep(0.1)  # Brief pause on error
                
            finally:
                progress_bar.update(1)
    
    finally:
        progress_bar.close()
        # Restore original logging level
        itunes_logger.setLevel(original_level)
    
    print(f"✅ Successfully scraped {len(scraped_podcasts)} podcasts with ratings >= 4.0")
    
    # Deduplicate by chash (content hash)
    podcasts_by_chash = {}
    for pod in scraped_podcasts:
        chash = pod.get('chash')
        if chash:
            if chash in podcasts_by_chash:
                existing = podcasts_by_chash[chash]
                existing_num_ratings = existing.get('numberOfRatings', 0)
                # Keep the one with more ratings
                if pod.get('numberOfRatings', 0) > existing_num_ratings:
                    podcasts_by_chash[chash] = pod
            else:
                podcasts_by_chash[chash] = pod
    
    print(f"✅ Deduplicated to {len(podcasts_by_chash)} unique podcasts")
    
    # Sort by composite score and return top N
    ranked_podcasts = list(podcasts_by_chash.values())
    ranked_podcasts.sort(key=lambda x: x['compositeScore'], reverse=True)
    
    top_podcasts = ranked_podcasts[:top_n]
    print(f"✅ Returning top {len(top_podcasts)} podcasts")
    
    return top_podcasts


def generate_pod_urls_csv(podcasts, output_path):
    """Generate CSV file from podcast list."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['title', 'category', 'feedId', 'rating', 'numberOfRatings', 'popularityScore', 'episodeCount'])
        
        for pod in podcasts:
            title = pod.get('title', '')
            category = "technology"
            feed_id = pod.get('id', '')
            rating = pod.get('rating')
            num_ratings = pod.get('numberOfRatings')
            popularity = pod.get('popularityScore')
            episode_count = pod.get('episodeCount')
            
            writer.writerow([title, category, feed_id, rating, num_ratings, popularity, episode_count])
        # add the extra podcasts
        for extra in extra_podcasts:
            writer.writerow(extra)
    print(f"✅ Generated {output_path} with {len(podcasts)} podcasts")

def generate_podcasts_metadata_json(podcasts, output_path):
    """Write full podcast metadata to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(podcasts, f, indent=2)
    print(f"✅ Generated {output_path} with {len(podcasts)} podcasts")


def build_step() -> dagmatic.Step:
    return dagmatic.Step(
        name="step1_seed_podcast_list",
        description="Step 1 - upload podcast list to R2",
        depends_on=(),
        run=_run,
    )


def _run(ctx: dagmatic.StepContext) -> dagmatic.StepResult:  # noqa: ARG001
    """
    Main execution flow:
    1. Query tech_podcasts.db for filtered podcasts
    2. Scrape iTunes ratings for each podcast
    3. Merge data and rank using Bayesian average
    4. Generate pod_urls.csv and podcasts_metadata.json
    5. Upload to R2
    """
    top_n = 1000
    try:
        # Step 1: Query database
        print("📊 Step 1: Querying tech_podcasts.db...")
        filtered_pods = from_db_sql_filtered(LOCAL_DB_PATH)
        
        if not filtered_pods:
            return dagmatic.StepResult.failed("No podcasts found in database")
        
        # Step 2-3: Scrape ratings and rank
        print("\n🔍 Step 2-3: Scraping iTunes ratings and ranking...")
        top_podcasts = scrape_and_rank_podcasts(filtered_pods, top_n)
        
        if not top_podcasts:
            return dagmatic.StepResult.failed("No podcasts with ratings >= 4.0 found")
        
        # Step 4: Generate CSV and JSON
        print("\n📝 Step 4: Generating pod_urls.csv and podcasts_metadata.json...")
        generate_pod_urls_csv(top_podcasts, LOCAL_PATH)
        generate_podcasts_metadata_json(top_podcasts, LOCAL_METADATA_PATH)
        
        if not LOCAL_PATH.exists() or not LOCAL_METADATA_PATH.exists():
            return dagmatic.StepResult.failed(f"Failed to generate output files")
        
        # Step 5: Upload to R2
        print("\n☁️ Step 5: Uploading to R2...")
        storage = Storage()
        if not storage.upload_file(str(LOCAL_PATH), R2_POD_MANIFEST_KEY):
            return dagmatic.StepResult.failed(f"Failed to upload {R2_POD_MANIFEST_KEY} to R2")
        if not storage.upload_file(str(LOCAL_METADATA_PATH), R2_POD_METADATA_KEY):
            return dagmatic.StepResult.failed(f"Failed to upload {R2_POD_METADATA_KEY} to R2")
        
        print(f"\n✅ SUCCESS: Uploaded {len(top_podcasts)} podcasts to R2")
        return dagmatic.StepResult.ok(f"Uploaded {R2_POD_MANIFEST_KEY} and {R2_POD_METADATA_KEY} with {len(top_podcasts)} podcasts to R2")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return dagmatic.StepResult.failed(f"Step failed: {str(e)}")





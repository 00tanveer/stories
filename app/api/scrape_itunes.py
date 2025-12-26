import json
import requests
import time
import functools
import logging
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_version():
    with open("version.json") as f:
        return json.load(f)['version']

VERSION = get_version()

def itunes_handler(max_retries=3, backoff_factor=1.5):
    """
    Decorator to handle iTunes API calls with retries and rate limiting.
    - Implements exponential backoff for retries.
    - Returns consistent JSON responses.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            retries = 0

            while retries <= max_retries:
                try:
                    url = func(self, *args, **kwargs)
                    logger.info(f"🌐 Request: {url}")
                    
                    res = requests.get(url, headers=self.headers)
                    logger.info(f"📡 Response: {res.status_code}")

                    # ✅ If successful, return parsed JSON
                    if res.status_code == 200:
                        try:
                            data = res.json()
                            logger.info(f"✅ Success: Received {len(str(data))} bytes of data")
                            return {
                                "success": True,
                                "status_code": 200,
                                "data": data
                            }
                        except json.JSONDecodeError:
                            logger.error(f"❌ Invalid JSON response: {res.text[:200]}")
                            return {
                                "success": False,
                                "status_code": 200,
                                "error": "Invalid JSON response",
                                "data": None
                            }

                    # ⚠️ Rate limit exceeded (HTTP 429)
                    elif res.status_code == 429:
                        wait_time = backoff_factor ** retries
                        logger.warning(f"⏳ Rate limit hit. Waiting {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        retries += 1
                        continue

                    # ❌ Other errors
                    else:
                        logger.error(f"❌ API Error {res.status_code}: {res.text[:200]}")
                        return {
                            "success": False,
                            "status_code": res.status_code,
                            "error": f"API returned {res.status_code}: {res.text[:200]}",
                            "data": None
                        }

                except requests.exceptions.RequestException as e:
                    wait_time = backoff_factor ** retries
                    logger.warning(f"⚠️ Network error: {str(e)}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    retries += 1
                    continue

            # after all retries failed
            logger.error(f"❌ Max retries ({max_retries}) reached. Request failed.")
            return {
                "success": False,
                "status_code": None,
                "error": f"Max retries ({max_retries}) reached. Request failed.",
                "data": None
            }

        return wrapper
    return decorator


class ITunesAPI:
    def __init__(self):
        self.base_url = "https://itunes.apple.com/lookup"
        self.headers = {
            'User-Agent': f'Stories Pod v{VERSION}'
        }
        logger.info(f"🍎 ITunesAPI initialized")

    @itunes_handler()
    def lookup(self, feed_id):
        """
        Get podcast metadata from iTunes lookup API.
        Returns the collectionViewUrl for further scraping.
        """
        url = f"{self.base_url}?id={feed_id}"
        return url

    def scrape_ratings(self, feed_id):
        """
        Scrape rating and numberOfRatings from iTunes podcast page.
        
        Args:
            feed_id: iTunes ID of the podcast
            
        Returns:
            dict with itunesPageUrl, rating, and numberOfRatings
        """
        try:
            # Step 1: Get collection URL from lookup API
            lookup_response = self.lookup(feed_id)
            
            if not lookup_response["success"]:
                logger.error(f"❌ Lookup failed for {feed_id}: {lookup_response.get('error')}")
                return None
            
            results = lookup_response["data"].get('results', [])
            if not results:
                logger.warning(f"⚠️ No results for id {feed_id}")
                return None
            
            collection_url = results[0].get('collectionViewUrl')
            if not collection_url:
                logger.warning(f"⚠️ No collectionViewUrl found for {feed_id}")
                return None
            
            logger.info(f"🔗 iTunes page: {collection_url}")
            
            # Step 2: Scrape the HTML page for ratings
            html_resp = requests.get(collection_url, headers=self.headers)
            html_resp.raise_for_status()
            
            soup = BeautifulSoup(html_resp.text, 'html.parser')
            
            rating = None
            number_of_ratings = None
            
            # Try new data-testid approach first
            rating_div = soup.find('div', attrs={'data-testid': 'amp-rating__average-rating'})
            count_div = soup.find('div', attrs={'data-testid': 'amp-rating__rating-count-text'})
            
            if rating_div:
                try:
                    rating = float(rating_div.text.strip())
                    logger.info(f"⭐ Rating: {rating}")
                except ValueError:
                    logger.warning(f"⚠️ Could not parse rating from: {rating_div.text}")
            
            if count_div:
                try:
                    count_text = count_div.text.strip()
                    number_of_ratings = int(count_text.split()[0].replace(',', ''))
                    logger.info(f"📊 Number of ratings: {number_of_ratings}")
                except (ValueError, IndexError):
                    logger.warning(f"⚠️ Could not parse rating count from: {count_div.text}")
            
            # Fallback: try aria-label approach if new approach failed
            if rating is None or number_of_ratings is None:
                import re
                ul = soup.find('ul', class_=lambda c: c and c.startswith('metadata'))
                if ul:
                    li = ul.find('li', attrs={'aria-label': re.compile(r'out of 5')})
                    if li and 'aria-label' in li.attrs:
                        m = re.match(r"([\d.]+) out of 5, ([\d,]+) ratings", li['aria-label'])
                        if m:
                            rating = float(m.group(1))
                            number_of_ratings = int(m.group(2).replace(',', ''))
                            logger.info(f"⭐ Rating (fallback): {rating}, 📊 Count: {number_of_ratings}")
            
            result = {
                'itunesPageUrl': collection_url,
                'rating': rating,
                'numberOfRatings': number_of_ratings
            }
            
            if rating is None and number_of_ratings is None:
                logger.warning(f"⚠️ No ratings found for {feed_id}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error scraping {feed_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Error scraping {feed_id}: {str(e)}")
            return None

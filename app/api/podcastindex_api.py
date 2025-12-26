import argparse
from datetime import date
import hashlib
import json
import requests
import time
from dotenv import load_dotenv
import os
import json
import functools
import logging

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

def api_handler(max_retries=3, backoff_factor=1.5):
    """
    Decorator to handle network calls, rate limits, retries, and consistent JSON responses.
    - Respects PodcastIndex 'Retry-After' header.
    - Implements exponential backoff for retries.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            retries = 0

            while retries <= max_retries:
                try:
                    req = func(self, *args, **kwargs)
                    logger.info(f"🌐 Request: {req['url']}")
                    logger.debug(f"Headers: {req['headers']}")
                    
                    res = requests.post(req["url"], headers=req["headers"])
                    logger.info(f"📡 Response: {res.status_code}")

                    # ✅ If successful, return parsed JSON
                    if res.status_code == 200:
                        try:
                            data = res.json()
                            logger.info(f"✅ Success: Received {len(str(data))} bytes of data")
                            logger.debug(f"Response data: {json.dumps(data, indent=2)[:500]}...")
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
                        retry_after = res.headers.get("Retry-After")

                        if retry_after:
                            wait_time = int(retry_after)
                            logger.warning(f"⏳ Rate limit hit. Retrying after {wait_time}s...")
                        else:
                            # fallback exponential backoff
                            wait_time = backoff_factor ** retries
                            logger.warning(f"⚠️ Rate limit (no Retry-After). Waiting {wait_time:.1f}s...")

                        time.sleep(wait_time)
                        retries += 1
                        continue  # retry

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
                    # network-level issue
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

class PDI_API:
    def __init__(self):
        ENV = os.getenv("APP_ENV", "development")  # default to development
        if ENV == "development":
            load_dotenv(".env.development")
        self.api_key = os.getenv('PODCASTINDEX_APIKEY')
        self.api_secret = os.getenv('PODCASTINDEX_SECRET')
        self.base_url = "https://api.podcastindex.org/api/1.0/"
        
        # Log initialization
        if self.api_key and self.api_secret:
            logger.info(f"🔑 PDI_API initialized with credentials (key: {self.api_key[:8]}...)")
        else:
            logger.warning("⚠️ PDI_API initialized WITHOUT valid credentials!")
    def build_request(self, query):
        # we'll need the unix time
        epoch_time = int(time.time())
        # our hash here is the api key + secret + time 
        data_to_hash = self.api_key + self.api_secret + str(epoch_time)
        # which is then sha-1'd
        sha_1 = hashlib.sha1(data_to_hash.encode()).hexdigest()
        # now we build our request headers
        headers = {
            'X-Auth-Date': str(epoch_time),
            'X-Auth-Key': self.api_key,
            'Authorization': sha_1,
            'User-Agent': f'Stories Pod v{VERSION}'
        }
        url = self.base_url + query
        request = {
            'url': url,
            'headers': headers
        }
        return request

    @api_handler()
    def getPodcastByFeedURL(self, feed_url):
        query = f"/podcasts/byfeedurl?url={feed_url}"
        return self.build_request(query)

    @api_handler()
    def getPodcastByFeedId(self, feed_id):
        query = f"/podcasts/byfeedid?id={feed_id}"
        return self.build_request(query)
    @api_handler()
    def getEpisodesByFeedURL(self, feed_url):
        query = f"/episodes/byfeedurl?url={feed_url}"
        return self.build_request(query)
    
    @api_handler()
    def getEpisodesByFeedId(self, feed_id):
        query = f"/episodes/byfeedid?id={feed_id}"
        return self.build_request(query)
    


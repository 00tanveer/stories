from elasticsearch import Elasticsearch
from elasticsearch import helpers
from tqdm import tqdm
from app.services.podcasts import load_all_episode_utterances
from dotenv import load_dotenv
import os 

ENV = os.getenv("APP_ENV", "development")  # default to development

if ENV == "development":
    load_dotenv(".env.development")
class ESIndexer:
    def __init__(self):
        ES_HOST = os.getenv("ES_HOST")
        # Increase client-level timeouts and enable retries to avoid premature read timeouts
        self.es = Elasticsearch(
            ES_HOST,
            request_timeout=60,  # seconds
            retry_on_timeout=True,
            max_retries=3,
        )

    def insert_one_utterance(self, index_name: str, document_id: str, document_body: dict):
        self.es.index(index=index_name, id=document_id, body=document_body)

    def search(self, index_name: str, query: dict):
        return self.es.search(index=index_name, body=query)
    
    def get_client(self):
        return self.es


    def assert_connection(self):
        """Ping the cluster and raise a helpful error if not reachable."""
        try:
            if not self.es.ping(request_timeout=5):
                raise RuntimeError("Elasticsearch ping failed: cluster not reachable at configured HOST")
        except Exception as e:
            raise RuntimeError(f"Elasticsearch connection error: {e}")

    def create_index(self):
        # Fail fast if ES isn't reachable
        self.assert_connection()

        # Delete if exists (ignore 404s) then create
        try:
            self.es.indices.delete(index='utterances', ignore_unavailable=True, timeout='30s')
        except Exception:
            # ignore errors on delete
            pass
        self.es.indices.create(index="utterances", timeout='30s')
    
    def delete_index(self):
        self.es.indices.delete(index='utterances')
    
    async def insert_utterances(self, index_name: str = "utterances", batch_size: int = 500):
        """
        Batch insert utterance documents into Elasticsearch using bulk API.

        - index_name: target ES index
        - batch_size: number of docs per bulk request (tune by payload size)
        """

        # Ensure ES is reachable before attempting bulk operations
        self.assert_connection()
        es_client = self.get_client()

        # Load utterance documents. Expect each item to be a dict with a unique 'id' and fields.
        utterances = await load_all_episode_utterances()
        total = len(utterances)
        print(total, "utterances to index into Elasticsearch.")

        def action_iter():
            for doc in utterances:
                yield {
                    "_index": index_name,
                    "_source": doc,
                }

        print(f"Indexing {total} utterances into Elasticsearch (batch_size={batch_size})…")

        successes = 0
        failures = 0
        iterator = helpers.streaming_bulk(
            es_client,
            action_iter(),
            chunk_size=batch_size,
            request_timeout=120,
            refresh="wait_for",
        )

        progress = tqdm(total=total, unit="docs") if total else None

        for ok, _ in iterator:
            if ok:
                successes += 1
            else:
                failures += 1
            if progress:
                progress.update(1)

        if progress:
            progress.close()

        print(f"Bulk indexing complete. Successes: {successes}, Failures: {failures}")
        return {
            "index": index_name,
            "total": total,
            "successes": successes,
            "failures": failures,
        }
    


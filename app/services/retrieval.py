from app.services.indexing.chroma_indexer import ChromaIndexer
from FlagEmbedding import FlagModel
from collections import Counter
from app.services.indexing.elasticsearch_indexer import ESIndexer
from pydantic import BaseModel
from typing import List, Optional

class SearchResult(BaseModel):
    id: str
    title: str = ''
    podcast_title: str = ''
    episode_description: str = ''
    author: str = ''
    date_published: str = ''
    duration: int = 0
    enclosure_url: str = ''
    start: Optional[int] = None
    end: Optional[int] = None
    episode_image: str = ''
    podcast_url: str = ''
    score: float = 0.0
    # one of the following depending on index
    question: Optional[str] = None
    answer: Optional[str] = None
    utterance: Optional[str] = None
    source: Optional[str] = None

class Retriever:
    """
    Handles semantic search over indexed data.
    Uses ChromaDB for vector search and FlagEmbedding for query embeddings.
    """
    EMBEDDING_MODEL = 'BAAI/bge-base-en-v1.5'
    def __init__(self):
        self.query_emb_model = FlagModel(self.EMBEDDING_MODEL, devices='cpu')
        self.chroma_client = ChromaIndexer()
        self.qa_collection = self.chroma_client.get_collection(name="episode_qa_pairs")
        self.utterances_collection = self.chroma_client.get_collection(name="utterances")
    def chroma_search(self, query_text, top_k=10, threshold=None):
        """
        Search top-k similar questions from both QA and utterances collections.
        Combines results and reranks by distance score.
        """
        print('bad bunny')
        embedding = self.query_emb_model.encode(query_text)

        # Query both collections
        results_qa = self.qa_collection.query(query_embeddings=embedding, n_results=top_k)
        results_utterances = self.utterances_collection.query(query_embeddings=embedding, n_results=top_k)
        
        # Combine results from both collections
        combined_results = []
        
        # Process QA collection results
        if results_qa['ids'] and len(results_qa['ids'][0]) > 0:
            for i in range(len(results_qa['ids'][0])):
                combined_results.append({
                    'id': results_qa['ids'][0][i],
                    'distance': results_qa['distances'][0][i],
                    'metadata': results_qa['metadatas'][0][i],
                    'document': results_qa['documents'][0][i],
                    'source': 'qa_collection'
                })
        
        # Process utterances collection results
        if results_utterances['ids'] and len(results_utterances['ids'][0]) > 0:
            for i in range(len(results_utterances['ids'][0])):
                combined_results.append({
                    'id': results_utterances['ids'][0][i],
                    'distance': results_utterances['distances'][0][i],
                    'metadata': results_utterances['metadatas'][0][i],
                    'document': results_utterances['documents'][0][i],
                    'source': 'utterances_collection'
                })
        
        # Sort by distance (higher is better) and get top 20
        combined_results.sort(key=lambda x: x['distance'], reverse=True)
        top_20_results = combined_results[:20]
        
        # No threshold filtering for now; return top_k combined results
        filtered_results = top_20_results

        # Normalize to SearchResult list
        normalized: List[SearchResult] = []
        for r in filtered_results:
            md = r['metadata'] or {}
            doc = r['document']
            src = r['source']
            base = {
                'id': md.get('id') or r['id'],
                'title': md.get('title', ''),
                'podcast_title': md.get('podcast_title', ''),
                'episode_description': md.get('description', ''),
                'author': md.get('author', ''),
                'date_published': md.get('date_published', ''),
                'duration': md.get('duration', 0) or 0,
                'enclosure_url': md.get('enclosure_url', ''),
                'start': md.get('start'),
                'end': md.get('end'),
                'episode_image': md.get('episode_image', ''),
                'podcast_url': md.get('podcast_url', ''),
                'score': r['distance'],
                'source': src,
            }
            if src == 'qa_collection':
                normalized.append(SearchResult(**{
                    **base,
                    'question': md.get('question', ''),
                    'answer': md.get('answer', ''),
                }))
            else:
                normalized.append(SearchResult(**{
                    **base,
                    'utterance': doc,
                }))

        return normalized
    
    def es_search(self, query_text, top_k=10):
        """
        Placeholder for Elasticsearch search implementation.
        """
        es = ESIndexer().get_client()
        results = es.search(
            index="utterances",
            body={
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["text"]
                    }
                },
                "highlight": {
                    "fields": {
                        "text": {}
                    }
                },
                "size": top_k
            }
        )
        hits = results['hits']['hits']
        # Normalize to SearchResult list
        normalized: List[SearchResult] = []
        for h in hits:
            src = h.get('_source', {})
            base = {
                'id': (src.get('id') or h.get('_id')) or '',
                'title': src.get('title') or '',
                'podcast_title': src.get('podcast_title') or '',
                'episode_description': src.get('description') or '',
                'author': src.get('author') or '',
                'date_published': src.get('date_published') or '',
                'duration': (src.get('duration') or 0) or 0,
                'enclosure_url': src.get('enclosure_url') or '',
                'start': src.get('start'),
                'end': src.get('end'),
                'episode_image': src.get('episode_image') or '',
                'podcast_url': src.get('podcast_url') or '',
                'score': float(h.get('_score', 0.0)),
                'source': 'elasticsearch',
            }
            normalized.append(SearchResult(**{
                **base,
                'utterance': src.get('text') or '',
            }))

        # Normalize scores to [0,1] per result set for fusion
        if normalized:
            max_score = max(r.score for r in normalized)
            min_score = min(r.score for r in normalized)
            span = max_score - min_score
            for r in normalized:
                r.score = (r.score - min_score) / span if span > 0 else 1.0
        return normalized
    def hybrid_search(self, query_text, top_k=20):
        """
        Combines ChromaDB and Elasticsearch search results with an RRF scorer 
        """
        chroma_results = self.chroma_search(query_text, top_k=top_k*2)
        es_results = self.es_search(query_text, top_k=top_k*2)
        # Simple union sorted by score descending (placeholder for RRF)
        combined: List[SearchResult] = sorted(
            chroma_results + es_results,
            key=lambda r: r.score,
            reverse=True
        )[:top_k]
        return combined
    def count_duplicates(self):
        print(self.qa_collection.count())
        res = self.qa_collection.get()
        docs = res["documents"]  # Chroma wraps it inside a list
        counts = Counter(docs)

        duplicates = {doc: count for doc, count in counts.items() if count > 1}

        print("Total docs:", len(docs))
        print("Unique docs:", len(counts))
        print("Duplicate docs:", sum(count - 1 for count in counts.values() if count > 1))
        print("Number of distinct duplicated texts:", len(duplicates))

       


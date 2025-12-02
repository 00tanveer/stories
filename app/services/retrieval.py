from app.services.indexer import Indexer
from FlagEmbedding import FlagModel
from collections import Counter

class Retriever:
    """
    Handles semantic search over indexed data.
    Uses ChromaDB for vector search and FlagEmbedding for query embeddings.
    """
    EMBEDDING_MODEL = 'BAAI/bge-base-en-v1.5'
    def __init__(self):
        self.query_emb_model = FlagModel(self.EMBEDDING_MODEL, devices='cpu')
        self.chroma_client = Indexer()
        self.qa_collection = self.chroma_client.get_collection(name="episode_qa_pairs")
        self.utterances_collection = self.chroma_client.get_collection(name="utterances")

    def search(self, query_text, top_k=10, threshold=0.45):
        """
        Search top-k similar questions from both QA and utterances collections.
        Combines results and reranks by distance score.
        """
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
        
        # Sort by distance (lower is better) and get top 20
        combined_results.sort(key=lambda x: x['distance'])
        top_20_results = combined_results[:20]
        
        # Filter by threshold if needed
        filtered_results = [r for r in top_20_results if r['distance'] <= threshold] if threshold else top_20_results
        
        # Restructure to match original ChromaDB format
        reranked_results = {
            'ids': [[r['id'] for r in filtered_results]],
            'distances': [[r['distance'] for r in filtered_results]],
            'metadatas': [[r['metadata'] for r in filtered_results]],
            'documents': [[r['document'] for r in filtered_results]],
            'sources': [[r['source'] for r in filtered_results]],  # Added source info
            'embeddings': None,
            'uris': None,
            'data': None,
            'included': ['metadatas', 'documents', 'distances']
        }
        
        return reranked_results
    
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

       


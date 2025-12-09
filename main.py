# main.py
import asyncio
# from app.services.retrieval import Retriever
import json
# from app.services.indexing.chroma_indexer import ChromaIndexer
from app.api.podcastindex_api import PDI_API
queries = [
    "good writing tips",
    "biggest regrets in life",
    "working at Meta",
    "funny story"
]
def chroma_search():
    retriever = Retriever()
    retriever.count_duplicates()
    
    for q in queries:
        results = retriever.chroma_search(q)
        file_id = q[:30]
        file_path = "search_results/chroma_search_results/"+str(file_id)+".json"
        dump = {
            "query": q,
            "results": [r.model_dump() for r in results]
        }
        
        with open(file_path, 'w') as json_file:
            json.dump(dump, json_file, indent=4)
def es_search():
    retriever = Retriever()
    
    for q in queries:
        results = retriever.es_search(q)
        file_id = q[:30]
        file_path = "search_results/es_search_results/"+str(file_id)+".json"
        dump = {
            "query": q,
            "results": [r.model_dump() for r in results]
        }
        
        with open(file_path, 'w') as json_file:
            json.dump(dump, json_file, indent=4)
def hybrid_search():
    retriever = Retriever()
    
    for q in queries:
        results = retriever.hybrid_search(q)
        file_id = q[:30]
        file_path = "search_results/hybrid_search_results/hybrid_"+str(file_id)+".json"
        dump = {
            "query": q,
            "results": [r.model_dump() for r in results]
        }
        
        with open(file_path, 'w') as json_file:
            json.dump(dump, json_file, indent=4)

async def update_chroma_metadata():
    indexer = ChromaIndexer()
    await indexer.update_metadata()

def get_pods():
    pdi = PDI_API()
    with open("data/podcasts/pod_urls.csv", "r") as f:
       # read the 3rd column from csv, skip the title
       urls = f.readlines()[1:]
       urls = [line.split(",")[2].strip() for line in urls]
       for url in urls:
           print(url)
       for url in urls[:3]:
           pod_data = pdi.getPodcastByFeedURL(url)
           print(json.dumps(pod_data, indent=4))
if __name__ == "__main__":
    # main()
    # chroma_search()
    # es_search()
    # hybrid_search()
    get_pods()
    # asyncio.run(update_chroma_metadata())

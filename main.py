# main.py
import asyncio
from app.services.retrieval import Retriever
import uuid
import json
from app.services.indexer import Indexer

def main():
    # # Initialize the Indexer
    # indexer = Indexer(
    #     data_dir="data",
    #     subfolder="content_json",
    #     use_remote=False  # use Ollama local embedding endpoint
    # )
    # # Try to load index; if not found, build one
    # try:
    #     questions_index = indexer.load_questions_index()
    #     print("✅ Index loaded successfully.")
    # except FileNotFoundError:
    #     print("⚠️ No existing index found. Building new index...")
    #     indexer.build_questions_index()

    # def cosine(a, b): return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # q1 = "How to get better in writing?"
    # q2 = "When you talk about the individual con contributions, ‘cause you mentioned that was your way of having a lot of impact, do you have a way of thinking about which contributions are more impactful than others? "
    # v1 = indexer.get_embedding(q1)
    # v2 = indexer.get_embedding(q2)
    # print("Cosine:", cosine(v1, v2))
    # Quick test query
    pass
def search():
    retriever = Retriever()
    retriever.count_duplicates()
    queries = [
        "How to get better in writing?",
        "What are some regrets that you have?",
        "What are the challenges of working at Meta?",
        "Tell me a funny story"
    ]
    for q in queries:
        results = retriever.search(q)
        file_id = uuid.uuid4()
        file_path = "search_results/"+str(file_id)+".json"
        dump = {
            "query": q,
            "results": results
        }
        
        with open(file_path, 'w') as json_file:
            json.dump(dump, json_file, indent=4)

async def update_chroma_metadata():
    indexer = Indexer()
    await indexer.update_metadata()
if __name__ == "__main__":
    # main()
    # search()
    asyncio.run(update_chroma_metadata())

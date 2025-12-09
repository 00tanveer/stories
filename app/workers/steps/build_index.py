import chromadb
from app.services.indexing.chroma_indexer import ChromaIndexer
from app.services.indexing.elasticsearch_indexer import ESIndexer
import asyncio

chroma_client = chromadb.HttpClient(host="localhost", port=8000)


async def chroma():
    indexer = ChromaIndexer()
    await indexer.upsert_qa_collection()
    await indexer.upsert_utterances_collection()

    # import pprint
    # pprint.pprint(all_episodes[0])
    # # write all_episodes[0] - a dict to a json file for inspection, encoded in utf-8
    # with open("episode_0_debug.json", "w", encoding="utf-8") as f:
    #     import json
    #     json.dump(all_episodes[0], f, ensure_ascii=False, indent=4, default=str)
    # print(type(all_episodes[0]))
    
    # indexer.delete_collection("episode_qa_pairs")
    # indexer.delete_collection("utterances")

async def elasticsearch():
    es_indexer = ESIndexer()
    es_indexer.create_index()
    print("Elasticsearch Working: \n", es_indexer.get_client().info())
    await es_indexer.insert_utterances()
    # Example usage:
    # es_indexer.index_document(index_name="test_index", document_id="1", document_body={"text": "Hello, Elasticsearch!"})
    # response = es_indexer.search(index_name="test_index", query={"query": {"match_all": {}}})
    # print(response)
if __name__ == "__main__":
    asyncio.run(chroma())
    asyncio.run(elasticsearch())

    
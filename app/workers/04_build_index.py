import chromadb
from app.services.indexer import Indexer
import asyncio

chroma_client = chromadb.HttpClient(host="localhost", port=8000)


async def main():
    indexer = Indexer()
    indexer.init_chroma_collection()
    await indexer.upsert_qa_collection()
    await indexer.upsert_utterances_collection()

    # import pprint
    # pprint.pprint(all_episodes[0])
    # write all_episodes[0] - a dict to a json file for inspection, encoded in utf-8
    # with open("episode_0_debug.json", "w", encoding="utf-8") as f:
    #     import json
    #     json.dump(all_episodes[0], f, ensure_ascii=False, indent=4, default=str)
    # print(type(all_episodes[0]))
    
    # indexer.delete_collection("episode_qa_pairs")
    # indexer.delete_collection("utterances")

if __name__ == "__main__":
    asyncio.run(main())
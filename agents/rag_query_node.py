# rag_query_node.py
import json
#from maestroIQ.maestro_test_agent.lib.chroma_db import get_chroma_collection
from payload_loader_node import *
def retrieve_example_payload(path: str, method: str, wlan_type: str = None) -> dict:
    collection = get_chroma_collection("api_payload")
    query = f"Example payload for {method} {path} {wlan_type or ''}".strip()
    embedding = get_openai_embedding(query)
    filter_dict = {}
    if wlan_type:
        filter_dict = {
            "$and": [
                {"endpoint": path},
                {"method": method},
                {"wlan_type": wlan_type}
            ]
        }

    try:
        results = collection.query(
            query_embeddings=[embedding],
            query_texts=[query],
            n_results=1,
            where=filter_dict if wlan_type else None
        )

        if results["documents"] and results["documents"][0]:
            return json.loads(results["documents"][0][0])
        else:
            print(f"⚠️ No documents found for query: {query}")
            return {}

    except Exception as e:
        print(f"⚠️ Failed to query ChromaDB: {e}")
        return {}

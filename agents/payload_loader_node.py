import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from chromadb import PersistentClient
load_dotenv()
openai = OpenAI()

def get_openai_embedding(text: str):
    response = openai.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def get_chroma_collection(name):
    db_path = os.path.abspath("db")
    print(f"[INFO] Chroma will persist data at: {db_path}")

    client = PersistentClient(path="db")
    collection = client.get_or_create_collection(name=name)
    results = collection.get()
    print(f"✅ Total documents: {len(results['documents'])}")
    return collection

def load_multiple_wlan_payloads(path: dict):
    try:
        collection = get_chroma_collection("api_payload")

        base_path = os.path.abspath(".")
        psk_path = path["wlan_psk"]
        open_path = path["wlan_open"]

        with open(psk_path, 'r') as f:
            wlan_psk = json.load(f)
        with open(open_path, 'r') as f:
            wlan_open = json.load(f)

        psk_str = json.dumps(wlan_psk)
        open_str = json.dumps(wlan_open)

        collection.add(
            documents=[psk_str, open_str],
            metadatas=[
                {"endpoint": "/wifi_enterprise/wlans", "method": "POST", "wlan_type": "wpa2-wpa3-psk"},
                {"endpoint": "/wifi_enterprise/wlans", "method": "POST", "wlan_type": "open"}
            ],
            ids=["wlan_psk_example", "wlan_open_example"],
            embeddings=[
                get_openai_embedding(psk_str),
                get_openai_embedding(open_str)
            ]
        )

        print("[✅] Data added to ChromaDB and automatically persisted to disk.")
        results = collection.get()
        print(f"✅ Total documents: {len(results['documents'])}")
    except Exception as e:
        print(f"[❌] Error initializing ChromaDB: {e}")


from payload_loader_node import *

if __name__ == "__main__":
    wlan_psk = "data/wlan_psk.json"
    wlan_open = "data/wlan_open.json"
    collection = get_chroma_collection("api_payload")
    results = collection.get()
    for meta in results["metadatas"]:
        print(meta)
    #get_chroma_collection()
    load_multiple_wlan_payloads({"wlan_psk": wlan_psk, "wlan_open": wlan_open})
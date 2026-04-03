import os
import chromadb

persist_directory = "Phase_2/chroma_db"
if os.path.exists(persist_directory):
    client = chromadb.PersistentClient(path=persist_directory)
    try:
        collection = client.get_collection(name="mutual_funds")
        count = collection.count()
        print(f"COLLECTION_COUNT: {count}")
    except Exception as e:
        print(f"ERROR: {e}")
else:
    print("DIRECTORY_NOT_FOUND")

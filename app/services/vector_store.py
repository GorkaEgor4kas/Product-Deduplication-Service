'''
work with ChromaDB
'''
import chromadb
from chromadb.config import Settings
from typing import List, Dict

class VectorStore:
    ''''
    ChromaDB wrapper to store and search products embeddings 
    All data is stored inside folder ./chroma_data
    '''
    def __init__(self, collection_name: str = "products"):
        '''
        ChromaDB connection initialization

        Args:
            collection_name: just the name of a specific collection (like table in DB)
        '''

        self.client = chromadb.PersistentClient(path="./chroma_data")

        self.collection = self.client.get_or_create_collection(collection_name)
        print(f"VectorStore ready. Collection: {collection_name}")

    async def search(self, embedding: List[float], limit: int = 100) -> List[Dict]:
        '''
        similar products search
        
        Args:
            embedding: Vector to search 
            limit: maximum amount of candidates 
        
        Return:
            list of dictionaries. Each looks like this:
            candidate = {
                'id': ...,
                'metadata': ..., 
                'name': ...,
                'distance': ...
            }
        '''

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=limit, 
            include=["documents", "metadatas", "distances"]
        )

        candidates = []

        # results contain:
        # - ids[0] — list of ids
        # - documents[0] — list of product names
        # - metadata[0] — list of metadata (brand, model, etc.)
        # - distances[0] — list of distances (the smaller, the more apparent)

        for i in range(len(results['ids'][0])):
            candidates.append({
                'id': results['ids'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'][0][i] is not None else {},
                'name': results['documents'][0][i],
                'distance': results['distances'][0][i]
            })

        return candidates 
    

    async def add(
            self, 
            product_id: str, 
            embedding: List[float],
            product_name: str,
            metadata: Dict
    ):
        '''
        adding a new product

        Args:
            I think I don't need to explain it
        '''

        self.collection.add(
            ids=[product_id],
            embeddings=[embedding],
            documents=[product_name],
            metadatas=[metadata]
        )
        print(f"Added product {product_id}: {product_name}")

    async def count(self):
        '''
        returning the amount of product in the DB
        '''
        return self.collection.count()
'''
this is a main logic of comparsion. I will call all other functions here.
'''
from .embedding_service import EmbeddingService
from .rule_analyzer import DuplicateRules, DuplicateAnalyzer
from .vector_store import VectorStore
from typing import Dict, Optional

class Deduplication:
    '''
    The main deduplication service,
    Combines embeddings, vector search and rules.
    '''

    def __init__(
            self,
            SIMILARITY_THRESHOLD: float = 0.75,
            vector_limit: int = 100,
            rules_path: str = "rules/custom_rules.yaml" #you can choose your own if u want
    ):
        '''
        service initialization 
        '''
        self.similarity_threshold = SIMILARITY_THRESHOLD
        self.vector_limit = vector_limit

        '''
        components initialization
        '''
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.rules_file = DuplicateRules.load_from_yaml(rules_path)
        self.rules_engine = DuplicateAnalyzer(self.rules_file)

    async def check(self, product_name: str) -> Dict:
        
        '''
        the main function 
        Checks if the item is a duplicate.

        Args:
            product_name: name of new product

        Returns:
            {
                'is_duplicate': bool,
                'duplicate_id': int,
                'similarity_score': float | None,
                'matched_name': str | None,
                'candidates_count': int
            }
        '''
        
        #get the embedding of product_name
        embedding = await self.embedding_service.get_embedding(product_name)

        #searching for candidates
        candidates = await self.vector_store.search(embedding, limit = self.vector_limit)

        #threshold filter
        close_candidates = [c for c in candidates if (1 - c["distance"]) >= self.similarity_threshold]

        '''
        checking each candidate
        if check['state'] is True: the new product is duplicate, if check['state'] is False: the new product is unique
        '''
        for candidate in close_candidates:
            check = self.rules_engine.Analyze(product_name, candidate["name"])
            if check['state'] == True: #duplicate
                return {
                    'is_duplicate': True,
                    'duplicate_id': candidate["id"],
                    'similarity_score': (1 - candidate["distance"]),
                    'matched_name': candidate["name"],
                    'candidates_count': len(close_candidates)
                }
        
        return {
            'is_duplicate': False,
            'duplicate_id': None,
            'similarity_score': None,
            'matched_name': None,
            'candidates_count': len(close_candidates)
        }

    async def add_new_product(
        self,
        product_id: str,
        product_name: str,
        metadata: Optional[Dict] = None
    ):
        '''
        Adding new unique product to the Vector DB
        Calls from webhook after main service confirmation

        Args:
            product_id: product's ID from the main DB (this is just to make referencses for products while using this service)
            product_name: product's name (to make comparsions in the second check layer)
            metadata: You can add something here if you want
        '''

        #get embedding for storing
        embedding = await self.embedding_service.get_embedding(product_name)

        #storing to DB
        await self.vector_store.add(
            product_id=product_id,
            embedding=embedding,
            product_name=product_name,
            metadata=metadata
        )

    async def stats(self) -> Dict:
        '''
        returning amount of products inside Vector DB and similarity threshold
        '''
        total = await self.vector_store.count()
        return {
            'total_products': total,
            'similarity_threshold': self.similarity_threshold
        } 

'''
downloading the model, embedding the product's name 
'''
import asyncio
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    '''
    service for embeddings generation
    models is loading once after service initialization
    '''
    def __init__(self, base_model = 'BAAI/bge-m3'): 
        print('Loading embedding model...')
        self.model = SentenceTransformer(base_model)
        print('Model loaded successgfully')

    async def get_embedding(self, text: str) -> list:
        '''
        process of making embeddings

        Args:
            text - input text (product's name)

        Return:
            list - list of 1024-dimensional vector (embedding)
        '''
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            self.model.encode,
            text
        )

        return embedding.tolist()


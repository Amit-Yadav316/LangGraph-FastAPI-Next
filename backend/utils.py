from config import settings
import pinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone


pinecone.init(
    api_key=settings.pinecone_api_key,
    environment=settings.pinecone_env
)

index_name = settings.pinecone_index_name

if index_name not in pinecone.list_indexes():
    pinecone.create_index(index_name, dimension=1536, metric="cosine")

index = pinecone.Index(index_name)

embedding = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)

vectorstore = Pinecone(index, embedding.embed_query, "text")
import os
import requests
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
import json
import streamlit as st
from streamlit.logger import get_logger
from chains import load_embedding_model
from utils import create_constraints, create_vector_index
from PIL import Image

load_dotenv(".env")

url = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
ollama_base_url = os.getenv("OLLAMA_BASE_URL")
embedding_model_name = os.getenv("EMBEDDING_MODEL")
llm_name = os.getenv("LLM")
emb_llm_name = os.getenv("LLM_EMBEDDING")
# Remapping for Langchain Neo4j integration
os.environ["NEO4J_URL"] = url

logger = get_logger(__name__)

so_api_base_url = "https://api.stackexchange.com/2.3/search/advanced"

embeddings, dimension = load_embedding_model(
    embedding_model_name, config={"ollama_base_url": ollama_base_url}, logger=logger, model_name=llm_name
)

# if Neo4j is local, you can go to http://localhost:7474/ to browse the database
neo4j_graph = Neo4jGraph(url=url, username=username, password=password)

create_constraints(neo4j_graph)
create_vector_index(neo4j_graph, dimension)
embeddings_cache = {}

def load_data(UploadedFile) -> None:
    logger.info("Inserting data...")
    jsonObj = json.load(UploadedFile)
    total_records = len(jsonObj)
    batch_size = 24
    total_batches = (total_records + batch_size - 1) // batch_size
    progress_bar = st.progress(0)
    for batch_index in range(total_batches):
        start_index = batch_index * batch_size
        end_index = start_index + batch_size
        batch = jsonObj[start_index:end_index]
        insert_data(batch)
        progress_percentage = (batch_index + 1) / total_batches
        progress_bar.progress(progress_percentage)    
    progress_bar.progress(100)
    embeddings_cache = {}
    st.success("Import successful", icon="✅")

def insert_data(data: dict) -> None:
    # Calculate embedding values
    for r in data:
        # details_text = r["businessDetails"]
        # # Check if embedding already computed
        # if details_text not in embeddings_cache:
        #     # Compute and store embedding if not present
        #     embeddings_cache[details_text] = embeddings.embed_query(details_text)
        # # Retrieve embedding from cache
        # r["embedding"] = embeddings_cache[details_text]
        name  = r["name"]
        # truncated_review = " ".join(review.split()[:250])
        r["embedding"] = embeddings.embed_query(name)
        
        
        
    import_query = """
    UNWIND $data AS r
    MERGE (restaurant:restaurant {name: r.name, embedding: r.embedding})
    ON CREATE SET restaurant.name = r.name, restaurant.businessDetails = r.businessDetails

    // Create and link Review nodes
    MERGE (review:review {text: r.review})
    MERGE (restaurant)-[:HAS_REVIEW]->(review)

    // Create and link City nodes
    MERGE (city:city {name: r.city})
    MERGE (restaurant)-[:LOCATED_IN]->(city)

    // Create and link State nodes
    MERGE (state:state {name: r.state})
    MERGE (city)-[:IN_STATE]->(state)
    """
    neo4j_graph.query(import_query, {"data": data})


# Streamlit

def render_page():
    st.header("Data Loader")
    st.subheader("Choose data to load into Neo4j")
    st.caption("Go to http://localhost:7474/ to explore the graph.")
    json = st.file_uploader("Upload Data JSON", type="json")
    if st.button("Import", type="primary"):
        if json is not None:
            with st.spinner("Loading... This might take a minute or two."):
                try:
                    load_data(json)
                    st.caption("Go to http://localhost:7474/ to interact with the database")
                except Exception as e:
                    st.error(f"Error: {e}", icon="🚨")
render_page()
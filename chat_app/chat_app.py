import streamlit as st
from typing import Any
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.graphs import OntotextGraphDBGraph
from langchain_community.chains.graph_qa.prompts import GRAPHDB_QA_TEMPLATE
from elasticsearch import Elasticsearch

from get_multiple import get_multiple

top_chunks = 3
top_communities = 3
top_outside_relationships = 10
top_inside_relationships = 10
top_entities = 10

# endpoint for GraphDB
graphdb_endpoint = "http://localhost:7200/repositories/msft-graphrag-300"
index_name = "entity_graph_index" 

st.title("GraphRAG Powered Chat")

def get_embedding(text: str, client: Any, model: str="CompendiumLabs/bge-large-en-v1.5-gguf"):
    """Convert the text into an embedding vector using the model provided

    :param text: text to be converted to and embedding vector
    :param client: OpenAI client
    :param model: name of the model to use for encoding
    """
    text = text.replace("\n", " ")
    return client.embeddings.create(input = [text], model=model).data[0].embedding

# set a default elasticsearch password
if "es_password" not in st.session_state:
    st.session_state["es_password"] = "password"

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

llm = ChatOpenAI(
    model="lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key="lm-server",  # if you prefer to pass api key in directly instaed of using env vars
    base_url="http://localhost:1234/v1"
)

qa_prompt = PromptTemplate(
    input_variables=["context", "prompt"], 
    template=GRAPHDB_QA_TEMPLATE
)

qa_chain = qa_prompt | llm | StrOutputParser()

ontology_path = "D:/Data/RDF/msft-graphrag.owl"
graph = OntotextGraphDBGraph(
    query_endpoint=graphdb_endpoint,
    local_file=ontology_path,
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

def get_entity_id_filter(entity_list) -> str:
    entity_id_filter = ""
    first = True
    for entity_id in entity_list:
        if first:
            entity_id_filter += "FILTER("
        else:
            entity_id_filter += " || "
        entity_id_filter += f'?id = "{entity_id}" '
        first = False
    entity_id_filter += ")"
    return entity_id_filter

def do_the_stuff(question_text, client, graph):
    embedding_vector = get_embedding(question_text, client=client)
    es_password = st.session_state["es_password"]
    es = Elasticsearch("http://localhost:9200", 
                       basic_auth=("elastic", es_password), 
                       verify_certs=False)
    query = {
    "field" : "description_embedding" ,
    "query_vector" : embedding_vector,
    "k" : top_entities,
    "num_candidates" : 100 ,
    }
    res = es.search(index=index_name, knn=query, source=["id"])
    search_results = res["hits"]["hits"]
    entity_list = [x['_id'] for x in search_results]
    entity_id_filter = get_entity_id_filter(entity_list=entity_list)
    query_sparql = get_multiple(entity_id_filter, 
                            top_chunks, 
                            top_communities, 
                            top_inside_relationships, 
                            top_outside_relationships)
    query_results = graph.query(query_sparql)
    prompt = {'query': question_text}
    qa_chain_result = qa_chain.invoke(
            {
                "prompt": prompt, 
                "context": query_results  # this is the information we got from our Knowledge Graph
            }
        )
    return qa_chain_result

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("waiting"):
            response = do_the_stuff(prompt, client, graph=graph)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

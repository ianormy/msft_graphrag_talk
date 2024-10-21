import streamlit as st
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

st.title("Chat with no Context")

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

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that answers questions about a book.",
        ),
        ("human", "{input}"),
    ]
)
qa_chain = prompt | llm | StrOutputParser()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

def do_the_stuff(question_text):
    prompt = {'query': question_text}
    qa_chain_result = qa_chain.invoke(
            {
                "input": prompt,
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
            response = do_the_stuff(prompt)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

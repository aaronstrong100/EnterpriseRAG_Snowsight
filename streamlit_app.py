import json
import streamlit as st
from snowflake.snowpark import Session
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

st.title("Enterprise RAG Assistant")
st.write("Ask a question, and the app will search your internal documents to find the answer.")
st.write("The site is currently down for maintenance. Please revisit later tonight if you want to try!")

@st.cache_resource
def get_snowflake_session():
    # 1. Grab the raw private key string from Streamlit secrets
    p_key_string = st.secrets["connections"]["snowflake"]["private_key"]

    # 2. Convert the string into the secure byte format Snowflake requires
    p_key_bytes = p_key_string.encode('utf-8')
    p_key = serialization.load_pem_private_key(
        p_key_bytes,
        password=None,
        backend=default_backend()
    )
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # 3. Build the connection payload manually
    connection_parameters = {
        "account": st.secrets["connections"]["snowflake"]["account"],
        "user": st.secrets["connections"]["snowflake"]["user"],
        "role": st.secrets["connections"]["snowflake"]["role"],
        "warehouse": st.secrets["connections"]["snowflake"]["warehouse"],
        "database": st.secrets["connections"]["snowflake"]["database"],
        "schema": st.secrets["connections"]["snowflake"]["schema"],
        "private_key": pkb  
    }

    # 4. Connect to Snowflake
    return Session.builder.configs(connection_parameters).create()

# Initialize the cached session
session = get_snowflake_session()

if user_question := st.chat_input("Ask about enterprise data..."):
    # Display user prompt
    st.chat_message("user").write(user_question)
    
    with st.spinner("Searching and generating answer..."):
        # 1. Call the updated stored procedure
        raw_response = session.call("RAG_DB.ENTERPRISE_DATA.ASK_RAG", user_question)
        
        # 2. Parse the JSON payload
        try:
            response_data = json.loads(raw_response)
            answer = response_data.get("answer", "No answer generated.")
            contexts = response_data.get("contexts", [])
            doc_ids = response_data.get("doc_ids", [])
        except json.JSONDecodeError:
            # Fallback just in case the SP fails and returns a raw string
            answer = raw_response
            contexts = []
            doc_ids = []

    # 3. Display the clean answer in the chat UI
    with st.chat_message("assistant"):
        st.write(answer)
        
        # 4. Create a collapsible "Sources" section for a better UX!
        if contexts:
            with st.expander("View Retrieved Sources"):
                for doc_id, context in zip(doc_ids, contexts):
                    st.markdown(f"**Source ID: {doc_id}**")
                    st.info(context)

import streamlit as st
from snowflake.snowpark import Session
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

st.title("Enterprise RAG Assistant")
st.write("Ask a question, and the app will search your internal documents to find the answer.")

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
    "private_key": pkb  # Pass the parsed cryptographic bytes, not the string
}

# 4. Connect to Snowflake
session = Session.builder.configs(connection_parameters).create()

user_query = st.text_input("What would you like to know?", placeholder="e.g., What are the recommended metrics?")

if st.button("Ask") and user_query:
    with st.spinner("Searching documents and generating response..."):
        try:
            answer = session.call("ASK_RAG", user_query)
            st.success("Done!")
            st.write("### Answer")
            st.write(answer)
        except Exception as e:
            st.error(f"An error occurred: {e}")

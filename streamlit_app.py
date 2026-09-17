import streamlit as st

st.title("Enterprise RAG Assistant :mag:")
st.write("Ask a question, and the app will search your internal documents to find the answer.")

# Connect using Streamlit's secrets manager
conn = st.connection("snowflake")
session = conn.session()
session.use_database("RAG_DB")
session.use_schema("ENTERPRISE_DATA")

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

import streamlit as st
from chatbot import generate_response

def main():
    st.title("Customer Data Query Assistant")
    st.write("Ask questions about customer data!")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Ask your question about customers"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            response = generate_response(prompt)
            
            # Show the answer
            st.markdown("**Answer:**")
            st.markdown(response['answer'])
            
            # Show the SQL query in an expandable section
            with st.expander("View SQL Query"):
                st.code(response['sql_query'], language='sql')
            
            # Show the raw data in an expandable section
            with st.expander("View Raw Data"):
                st.dataframe(response['results'])
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response['answer']
            })

if __name__ == "__main__":
    main()
import streamlit as st
from chatbot import generate_response, validate_and_update_data
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def check_customer_id(customer_id):
    """Validate customer ID format"""
    import re
    return bool(re.match(r'^C\d{6}$', customer_id))

def main():
    st.title("GeinAI Powered Customer Assistant")
    
    # Initialize session state
    if "customer_id" not in st.session_state:
        st.session_state.customer_id = None
        st.session_state.messages = []
        st.session_state.pending_operation = None

    # Customer ID Login
    if not st.session_state.customer_id:
        with st.form("login_form"):
            customer_id = st.text_input("Please enter your Customer ID (format: CXXXXXX)")
            submit = st.form_submit_button("Login")
            
            if submit:
                if check_customer_id(customer_id):
                    st.session_state.customer_id = customer_id
                    st.session_state.messages.append({
                        "role": "system",
                        "content": f"Logged in as: {customer_id}"
                    })
                    st.rerun()
                else:
                    st.error("Invalid Customer ID format. Please use format: CXXXXXX")
    else:
        # Show logged in status and logout button
        col1, col2 = st.columns([3,1])
        with col1:
            st.info(f"Logged in as: {st.session_state.customer_id}")
        with col2:
            if st.button("Logout"):
                st.session_state.customer_id = None
                st.session_state.messages = []
                st.session_state.pending_operation = None
                st.rerun()

        # Chat interface
        st.write("Thanks for being a valuable customer, How can I help you today!")

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Handle pending operations that require confirmation
        if st.session_state.pending_operation:
            st.warning("⚠️ This operation will modify data. Please confirm:")
            col1, col2 = st.columns([1,3])
            with col1:
                if st.button("✅ Confirm"):
                    response = validate_and_update_data(st.session_state.pending_operation, confirmed=True)
                    st.session_state.pending_operation = None
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response['answer']
                    })
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.pending_operation = None
                    st.rerun()

        # User input
        if prompt := st.chat_input("Ask your question"):
            # Add customer ID context
            if st.session_state.customer_id not in prompt:
                prompt = f"For customer ID {st.session_state.customer_id}, {prompt}"

            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                response = generate_response(prompt)
                
                if response.get('requires_confirmation'):
                    st.session_state.pending_operation = prompt
                    st.rerun()
                
                # Show the answer
                st.markdown("**Answer:**")
                st.markdown(response['answer'])
                
                # Show the SQL query in an expandable section
                with st.expander("View SQL Query"):
                    st.code(response['sql_query'], language='sql')
                
                # Show the raw data in an expandable section
                if not response['results'].empty:
                    with st.expander("View Raw Data"):
                        st.dataframe(response['results'])
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response['answer']
                })

if __name__ == "__main__":
    main()
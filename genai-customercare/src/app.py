import streamlit as st
from chatbot import generate_response

def main():
    st.title("Customer Support Chatbot")
    st.write("Ask me anything!")

    user_input = st.text_input("You: ", "")
    
    if st.button("Send"):
        if user_input:
            response = generate_response(user_input)
            st.text_area("Chatbot:", response, height=200)
        else:
            st.warning("Please enter a question.")

if __name__ == "__main__":
    main()
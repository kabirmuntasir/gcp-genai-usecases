# Streamlit Chatbot

A simple and interactive chatbot application built using Streamlit and integrated with AI capabilities. This chatbot provides a clean, web-based interface for user interactions.

## Project Structure

```
streamlit-chatbot/
├── src/
│   ├── app.py          # Main Streamlit application entry point
│   ├── chatbot.py      # Chatbot logic implementation
│   └── requirements.txt # Project dependencies
├── mak-gcp/
│   └── google-cloud-sdk/ # Google Cloud SDK for deployment
├── Dockerfile          # Docker configuration for containerization
├── .dockerignore       # Specifies files to exclude from Docker builds
├── .gcloudignore      # Specifies files to exclude from GCloud deployments
├── .gitignore         # Specifies files to exclude from version control
├── README.md          # Project documentation
└── setup.sh           # Setup and deployment script
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd streamlit-chatbot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r src/requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run src/app.py
   ```

## Usage

- Launch the application and navigate to `http://localhost:8501` in your web browser
- The interface will present a chat window where you can interact with the chatbot
- Type your message in the input field and press Enter to receive a response

## Deployment

### Local Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t streamlit-chatbot .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8501:8501 streamlit-chatbot
   ```

### Google Cloud Run Deployment

1. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth login
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy --image gcr.io/<your-project-id>/streamlit-chatbot --platform managed
   ```

## Development

- The application is built with Streamlit for the frontend interface
- Main application logic is in `src/app.py`
- Chatbot implementation is contained in `src/chatbot.py`
- Dependencies are managed through `requirements.txt`

## License

This project is licensed under the MIT License. See the LICENSE file for details.
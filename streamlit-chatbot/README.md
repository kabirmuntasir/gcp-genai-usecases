# Streamlit Chatbot

This project is a simple chatbot application built using Streamlit and the Google Generative AI API. The chatbot is designed to answer customer queries in a user-friendly interface.

## Project Structure

```
streamlit-chatbot
├── src
│   ├── app.py          # Main entry point for the Streamlit application
│   ├── chatbot.py      # Contains chatbot logic and response generation
│   └── requirements.txt # Lists Python dependencies
├── Dockerfile           # Instructions to build a Docker image
├── .dockerignore        # Files to ignore when building the Docker image
├── .gcloudignore        # Files to ignore when deploying to Google Cloud
├── README.md            # Project documentation
└── setup.sh             # Shell script for setup and deployment
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd streamlit-chatbot
   ```

2. **Install dependencies:**
   You can install the required Python packages using pip:
   ```bash
   pip install -r src/requirements.txt
   ```

3. **Run the application:**
   Start the Streamlit application by running:
   ```bash
   streamlit run src/app.py
   ```

## Usage

- Open your web browser and navigate to `http://localhost:8501` to interact with the chatbot.
- Type your questions in the input box and receive responses generated by the chatbot.

## Deployment

To deploy the application on Google Cloud Run:

1. **Build the Docker image:**
   ```bash
   docker build -t streamlit-chatbot .
   ```

2. **Deploy to Google Cloud Run:**
   ```bash
   gcloud run deploy --image gcr.io/<your-project-id>/streamlit-chatbot --platform managed
   ```

3. Follow the prompts to complete the deployment.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
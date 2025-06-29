# MCQ Generator from YouTube Video

A robust, containerized web application that generates multiple-choice questions (MCQs) from the transcript of any YouTube video. Powered by Google's Gemini AI, this tool allows users to test their comprehension of video content with an interactive quiz and instant feedback.The application is built with best practices in mind, including a secure, non-root Docker container, health checks for reliability, and detailed error handling.

## Features

-   **Generate MCQs from Video**: Simply provide a YouTube video URL to create a custom quiz.
-   **Automated Transcript Fetching**: Uses the `youtube-transcript-api` to automatically retrieve video captions.
-   **Powered by Google Gemini**: Leverages the `gemini-1.5-flash` model for intelligent and relevant question generation.
-   **Embedded Video Player**: The generated quiz is displayed alongside the embedded YouTube video for easy reference.
-   **Interactive Quiz & Instant Scoring**: Answer questions and immediately receive your score, percentage, and a detailed breakdown of your answers.
-   **Secure & Reliable**: Runs in a security-hardened Docker container as a non-root user and includes a health check endpoint for monitoring.
-   **Robust Error Handling**: Gracefully handles invalid URLs, missing video transcripts, and malformed AI responses.

## Technology Stack

-   **Backend**: Python, Flask
-   **AI Model**: Google Gemini (`gemini-1.5-flash`) via `google-generativeai` SDK
-   **Transcript Service**: `youtube-transcript-api`
-   **WSGI Server**: Waitress
-   **Frontend**: HTML5, Tailwind CSS (via CDN)
-   **Containerization**: Docker, Docker Compose

---

### 1. Configuration

Before you can run the application, you must configure your environment variables.

1.  Clone the repository:
    ```bash
    git clone https://github.com/AnantSom/MCQ-Generator-video-.git
    cd mcq-url
    ```

2.  Create a file named `.env` in the root of the project directory. You can create it manually or by copying the example if one exists.

3.  Add the following content to your new `.env` file and replace the placeholder values with your own information:

    ```ini
    MY_API_KEY="your_google_api_key_here"
    PUBLIC_PORT=10002
    FLASK_RUN_PORT=10000
    ```

### 2. Running the Application (Docker)

1.  Ensure the Docker Desktop application is running on your machine.
2.  From the project's root directory, build and run the container using Docker Compose:
    ```bash
    docker-compose up --build -d
    ```
3.  The application will be available at **http://localhost:10002** (or whatever port you set for `PUBLIC_PORT`). The health check will ensure the container only stays up if the application is running correctly.

4.  To check the logs of the running container:
    ```bash
    docker-compose logs -f
    ```

5.  To stop and remove the container:
    ```bash
    docker-compose down
    ```

---
#### Method B: Running Locally (Without Docker)

If you prefer not to use Docker, you can run the application directly in a local Python environment.

1.  Create and activate a virtual environment. This keeps project dependencies isolated.

    *   **On Linux/macOS:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   **On Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    python app.py
    ```

4.  The application will be available at **http://localhost:10000** (or the port specified by `FLASK_RUN_PORT` in your `.env` file).

---
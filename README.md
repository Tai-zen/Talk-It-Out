# Talk-It-Out

 "Talk-It-Out" project with step-by-step instructions:

Link to hosted app: https://talk-it-out-90fw.onrender.com

# Talk-It-Out
Talk It Out is an innovative mental health chatbot designed specifically for students, aiming to provide accessible support and resources that promote emotional well-being. By harnessing quality data from various sources—such as open datasets, research articles, mental health organizations, and direct survey

## Features

- User authentication (login/signup)
- AI chat companion with memory of past conversations
- Mood tracking
- Community resources section
- Sound lounge for relaxation

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- OpenRouter API key (free account available at [openrouter.ai](https://openrouter.ai))

## Installation Guide

Clone the repository

  git clone https://github.com/your-username/Talk-It-Out.git
  cd Talk-It-Out

Create and activate a virtual environment
  python -m venv venv
  source venv/bin/activate , On Windows use: venv\Scripts\activate

Install dependencies
  pip install -r requirements.txt

Set up environment variables
  Create a .env file in the project root with your OpenRouter API key:
  env
  OPENROUTER_API_KEY=your_api_key_here

Initialize the database
  The application will automatically create the SQLite database when first run.

## Running the Application
Development mode
  python app.py
  The application will be available at: http://localhost:5000

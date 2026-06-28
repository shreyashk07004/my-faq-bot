# ShopEasy FAQ Chatbot

ShopEasy is a smart customer support FAQ chatbot powered by the Groq API (`llama-3.1-8b-instant`). It serves responses directly using a local markdown-based knowledge base.

It comes in two flavors:
1. **Terminal Bot**: An interactive CLI terminal application.
2. **Web App**: A modern Flask-based web chat application with a premium chat bubble interface.

---

## Features

- **Knowledge-Strict**: Answers customer queries strictly based on the content defined in `knowledge_base/faq_bot_prompt_and_knowledge_base.md`.
- **Intelligent Fallback**: If a question is outside the knowledge base, the bot replies politely and prompts the customer to contact support (`support@shopeasy.com`).
- **Interaction History**: Logs all user queries and assistant responses to `logs/chat_history.txt`.
- **Continuous Improvement**: Captures all unanswered questions separately in `logs/unanswered.txt` so administrators can easily update and expand the knowledge base.

---

## Project Structure

```text
├── knowledge_base/
│   └── faq_bot_prompt_and_knowledge_base.md  # System instructions & Q&A knowledge base
├── logs/
│   ├── chat_history.txt                      # Complete interaction log
│   └── unanswered.txt                        # Logs of queries outside the knowledge base
├── src/
│   ├── app.py                                # Flask web application entrypoint
│   ├── faq_bot.py                            # CLI interactive chatbot & common helper functions
│   └── templates/
│       └── index.html                        # Web chatbot frontend template
├── .env.example                              # Template environment variables
├── .gitignore                                # Git ignore file (excludes secrets & logs)
├── requirements.txt                          # Python dependencies list
└── README.md                                 # Project documentation
```

---

## Setup & Installation

### 1. Clone & Navigate to Project
```bash
git clone <your-repo-url>
cd "ai agent"
```

### 2. Set Up a Virtual Environment
```bash
# Create a virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# Activate it (macOS/Linux)
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your actual Groq API key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

---

## Running the Applications

### Option A: Interactive CLI Terminal Bot
Run the terminal interface to chat directly inside the command line:
```bash
python src/faq_bot.py
```
Type `exit`, `quit`, or `q` to terminate the session.

### Option B: Flask Web App
Start the development server:
```bash
python src/app.py
```
Open your browser and navigate to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

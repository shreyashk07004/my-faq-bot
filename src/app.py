import os
import sys
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Ensure we can import from the sibling faq_bot module
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from faq_bot import load_system_prompt_and_kb, log_chat_interaction, is_unanswered_response, log_unanswered_question
except ImportError as e:
    print(f"Error importing functions from faq_bot: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Compile and cache the system prompt and knowledge base once at startup
try:
    system_prompt = load_system_prompt_and_kb()
except Exception as e:
    print(f"Error compiling system prompt & knowledge base: {e}")
    sys.exit(1)

# Retrieve API key
api_key = os.getenv("GROQ_API_KEY")
client = None

if api_key and api_key != "your_groq_api_key_here":
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize Groq client at startup: {e}")
else:
    print("\n[WARNING] GROQ_API_KEY is not set or is still the default placeholder.")
    print("Please configure GROQ_API_KEY in your .env file to enable queries.")

@app.route('/')
def home():
    """Serves the chat interface HTML page."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint to handle customer queries and get answers from the FAQ chatbot."""
    global client
    
    # Lazy initialization or validation of the Groq client if key was added post-startup
    if not client:
        api_key_now = os.getenv("GROQ_API_KEY")
        if api_key_now and api_key_now != "your_groq_api_key_here":
            try:
                from groq import Groq
                client = Groq(api_key=api_key_now)
            except Exception as e:
                return jsonify({
                    "success": False, 
                    "error": f"Failed to initialize Groq client: {str(e)}"
                }), 500
        else:
            return jsonify({
                "success": False, 
                "error": "GROQ_API_KEY is missing or invalid. Please check your .env configuration."
            }), 500

    # Parse JSON body
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({
            "success": False, 
            "error": "Message content cannot be empty."
        }), 400

    try:
        import groq
        model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        # Query Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model=model_name,
            temperature=0.0,
            max_tokens=500
        )
        
        # Get response text
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Log to chat history
        try:
            log_chat_interaction(user_message, response_text)
            if is_unanswered_response(response_text):
                log_unanswered_question(user_message)
        except Exception as e:
            app.logger.warning(f"Failed to log interaction: {e}")

        return jsonify({
            "success": True, 
            "response": response_text
        })

    except groq.AuthenticationError:
        return jsonify({
            "success": False, 
            "error": "Authentication Error: The provided GROQ_API_KEY is invalid. Check your .env file."
        }), 401
    except groq.RateLimitError as e:
        return jsonify({
            "success": False, 
            "error": f"Rate Limit: {str(e)}. Please wait before sending more messages."
        }), 429
    except groq.APIConnectionError:
        return jsonify({
            "success": False, 
            "error": "Connection Error: Failed to connect to Groq API. Check the server internet connection."
        }), 503
    except groq.APIStatusError as e:
        return jsonify({
            "success": False, 
            "error": f"API Error (Status {e.status_code}): {e.message}"
        }), 502
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Run server locally on port 5000
    print("*" * 60)
    print("Starting ShopEasy FAQ Bot Web App...")
    print("Local URL: http://127.0.0.1:5000")
    print("*" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)

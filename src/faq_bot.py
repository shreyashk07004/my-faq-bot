import os
import re
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_system_prompt_and_kb():
    """
    Reads the markdown file, extracts the system prompt template and knowledge base,
    and returns the compiled system prompt.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    kb_path = os.path.join(project_root, 'knowledge_base', 'faq_bot_prompt_and_knowledge_base.md')
    
    if not os.path.exists(kb_path):
        print(f"\n[ERROR] Knowledge base file not found at:\n   {kb_path}")
        print("Please ensure the 'knowledge_base' folder and the markdown file exist.")
        sys.exit(1)
        
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"\n[ERROR] Reading knowledge base file: {e}")
        sys.exit(1)
        
    # Extract the system prompt template
    # Find ## 🤖 SYSTEM PROMPT followed by the first ``` code block
    system_prompt_match = re.search(
        r'##\s*🤖\s*SYSTEM\s*PROMPT.*?\n```[^\n]*\n(.*?)\n```',
        content,
        re.DOTALL | re.IGNORECASE
    )
    if not system_prompt_match:
        print("\n[ERROR] Could not parse the system prompt template from the markdown file.")
        print("Make sure there is a code block (between ``` and ```) under the '## 🤖 SYSTEM PROMPT' heading.")
        sys.exit(1)
        
    system_prompt_template = system_prompt_match.group(1).strip()
    
    # Extract the knowledge base section
    # Search for ## 📚 SAMPLE KNOWLEDGE BASE and locate its content
    kb_header_match = re.search(r'##\s*📚\s*SAMPLE\s*KNOWLEDGE\s*BASE.*?\n', content, re.IGNORECASE)
    if not kb_header_match:
        print("\n[ERROR] Could not find the '## 📚 SAMPLE KNOWLEDGE BASE' header in the markdown file.")
        sys.exit(1)
        
    kb_start_index = kb_header_match.end()
    
    # Find the first Q&A category starting with ###
    kb_content_match = re.search(r'###\s+\S+', content[kb_start_index:])
    if not kb_content_match:
        print("\n[ERROR] Could not find any Q&A categories (starting with '###') in the knowledge base.")
        sys.exit(1)
        
    kb_actual_start = kb_start_index + kb_content_match.start()
    
    # The knowledge base ends at the next main header (e.g. ## ⚙️ HOW TO USE THIS) or end of file
    kb_end_match = re.search(r'\n##\s+\S+', content[kb_actual_start:])
    if kb_end_match:
        kb_content = content[kb_actual_start:kb_actual_start + kb_end_match.start()].strip()
    else:
        kb_content = content[kb_actual_start:].strip()
        
    # Replace the placeholder in the system prompt template
    placeholders = [
        "[Paste your knowledge base here — see the section below]",
        "[Paste your knowledge base here]"
    ]
    
    system_prompt = system_prompt_template
    replaced = False
    for placeholder in placeholders:
        if placeholder in system_prompt:
            system_prompt = system_prompt.replace(placeholder, kb_content)
            replaced = True
            break
            
    if not replaced:
        # Regex fallback for any variation of [Paste your knowledge base here ...]
        system_prompt, count = re.subn(
            r'\[Paste your knowledge base here.*?\]',
            kb_content,
            system_prompt
        )
        if count == 0:
            print("\n[WARNING] Knowledge base placeholder not found in system prompt template.")
            print("Appending the knowledge base content to the end of the system prompt instead.")
            system_prompt += f"\n\n### KNOWLEDGE BASE:\n{kb_content}"
            
    return system_prompt

def log_chat_interaction(question, answer):
    """
    Logs the question and answer with date and time to logs/chat_history.txt.
    Creates the logs/ folder if it doesn't exist.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    logs_dir = os.path.join(project_root, 'logs')
    
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
        
    log_file_path = os.path.join(logs_dir, 'chat_history.txt')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"Date/Time: {timestamp}\n"
        f"Question:  {question}\n"
        f"Answer:    {answer}\n"
        f"----------------------------------------\n"
    )
    
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"\n[WARNING] Failed to write to log file: {e}")

def is_unanswered_response(response_text):
    """
    Checks if the response indicates that the question is outside the knowledge base.
    """
    normalized_text = response_text.lower().strip()
    return "don't have information on that right now" in normalized_text and "support@shopeasy.com" in normalized_text

def log_unanswered_question(question):
    """
    Logs unanswered questions separately to logs/unanswered.txt.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    logs_dir = os.path.join(project_root, 'logs')
    
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
        
    log_file_path = os.path.join(logs_dir, 'unanswered.txt')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"Date/Time: {timestamp}\n"
        f"Question:  {question}\n"
        f"----------------------------------------\n"
    )
    
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"\n[WARNING] Failed to write to unanswered log file: {e}")

def main():
    print("=" * 60)
    print("ShopEasy FAQ Bot - Initializing...")
    print("=" * 60)
    
    # Load and compile the system prompt with the knowledge base
    system_prompt = load_system_prompt_and_kb()
    
    # Import Groq and handle dependencies
    try:
        from groq import Groq
        import groq
    except ImportError:
        print("\n[ERROR] 'groq' package is not installed.")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
        
    # Check for API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        print("\n[ERROR] GROQ_API_KEY is not set or is still the default placeholder.")
        print("Please create a '.env' file in the project root with your key:")
        print("GROQ_API_KEY=gsk_your_actual_key_here")
        sys.exit(1)
        
    # Initialize the Groq client
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"\n[ERROR] Initializing Groq client: {e}")
        sys.exit(1)
        
    print("\n[SUCCESS] System prompt and knowledge base loaded successfully!")
    print("[SUCCESS] Groq client initialized.")
    print("-" * 60)
    print("Ask me anything about orders, shipping, returns, payments, accounts, or offers.")
    print("Type 'exit', 'quit', or 'q' to end the chat.")
    print("-" * 60)
    
    # Interactive chat loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye!")
            break
            
        if not user_input:
            continue
            
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
            
        print("Bot is thinking...", end="\r")
        sys.stdout.flush()
        
        try:
            # Query Groq API
            # We default to llama-3.1-8b-instant with temperature=0.0 to keep answers deterministic and strict
            model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_input,
                    }
                ],
                model=model_name,
                temperature=0.0,
                max_tokens=500
            )
            
            # Print response
            response_text = chat_completion.choices[0].message.content.strip()
            # Clear "Bot is thinking..." line
            print(" " * 20, end="\r")
            print(f"Bot: {response_text}")
            log_chat_interaction(user_input, response_text)
            if is_unanswered_response(response_text):
                log_unanswered_question(user_input)
            
        except groq.AuthenticationError:
            print(" " * 20, end="\r")
            print("\n[ERROR] Authentication Error: The provided GROQ_API_KEY is invalid.")
            print("Please double check your Groq API key in the '.env' file.")
        except groq.RateLimitError as e:
            print(" " * 20, end="\r")
            print(f"\n[ERROR] Rate Limit Error: {e}")
            print("Please wait a bit before asking another question.")
        except groq.APIConnectionError as e:
            print(" " * 20, end="\r")
            print("\n[ERROR] Connection Error: Unable to reach the Groq API.")
            print("Please check your internet connection or try again later.")
        except groq.APIStatusError as e:
            print(" " * 20, end="\r")
            print(f"\n[ERROR] API Error (Status {e.status_code}): {e.message}")
            print("The Groq service might be experiencing issues.")
        except Exception as e:
            print(" " * 20, end="\r")
            print(f"\n[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

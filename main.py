from dotenv import load_dotenv
import os
import json
import chromadb

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# AI Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

from documents import documents  # Import the documents

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize the Google Generative AI model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GEMINI_API_KEY)

# Initialize Chroma client
chroma_client = chromadb.Client()

# Create or get the Chroma collection
collection = chroma_client.get_or_create_collection(name="restaurant_data")

# Add documents to Chroma collection
for doc in documents:
    content = f"Name: {doc['name']}\nMenu: {doc['menu']}\nCity: {doc['city']}\nEvent: {doc['event']}"
    collection.upsert(
        documents=[content],
        metadatas=[{"title": doc["title"], "name": doc["name"], "menu": doc["menu"], "city": doc["city"], "event": doc["event"]}],
        ids=[doc["title"]]
    )

# Define available actions
actions = {
    "show_menu": "Display the menu image."
}

# Define your custom prompt template
prompt_template = PromptTemplate(
    input_variables=["history", "retrieved_info", "question", "actions"],
    template="""
    {history}
    Information about the restaurant: {retrieved_info}
    Actions you can take: {actions}
    In this chat, you are a waiter in a Mexican restaurant. You can only speak Spanish and under no circumstances can you speak English.
    If the customer talks about something unrelated to a restaurant conversation, respond with "No entiendo, por favor hable de algo relacionado con el restaurante."
    Customer: {question}
    If you want to perform an action, include it in the response in this format: [ACTION: action_name].
    """
)


# Function to load conversation history from a file
def load_history(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    return ""

# Function to save conversation history to a file
def save_history(file_path, history):
    with open(file_path, 'w') as file:
        file.write(history)

# Path to the history file
history_file = 'conversation_history.txt'
history = load_history(history_file)

# FastAPI setup
app = FastAPI()

# Serve the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html") as f:
        return f.read()

# Request model for input
class ConversationInput(BaseModel):
    question: str

@app.post("/conversation")
async def conversation(input: ConversationInput):
    global history
    question = input.question
    
    if question.strip() == '\\end':
        return {"response": "Goodbye!", "unrelated": False, "retrieved_info": "", "action": ""}

    # Retrieve relevant information
    results = collection.query(query_texts=[question], n_results=1)
    if results['documents']:
        retrieved_info = results['documents'][0]
    else:
        retrieved_info = "No relevant information found."

    # Create the full prompt with history, retrieved information, actions, and current question
    prompt = prompt_template.format(
        history=history, 
        retrieved_info=retrieved_info, 
        question=question, 
        actions=json.dumps(actions)
    )
    
    # Get the response from the model
    response = llm.invoke(prompt).content
    
    unrelated_input = "No entiendo, por favor hable de algo relacionado con el restaurante." in response
    
    action = ""
    if "[ACTION:" in response:
        action_start = response.find("[ACTION:") + len("[ACTION:")
        action_end = response.find("]", action_start)
        action = response[action_start:action_end].strip()
        response = response[:action_start - len("[ACTION:")].strip()  # Remove action indication from response
    
    if unrelated_input:
        return {"response": "", "unrelated": True, "retrieved_info": retrieved_info, "action": action}

    # Update history
    history += f"Customer: {question}\nWaiter: {response}\n"
    save_history(history_file, history)
    
    return {"response": response, "unrelated": False, "retrieved_info": retrieved_info, "action": action}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

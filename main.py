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
    "show_menu": "Display the menu image.",
    "next_objective": "Move to the next objective."
}

# Define the objectives for the guided conversation
objectives = [
    "Ask for a menu",
    "Pick an order",
    "Call for the waiter to pay for the meal"
]
current_objective_index = 0
phoenix_triggered = False

# Define your custom prompt template
prompt_template = PromptTemplate(
    input_variables=["history", "retrieved_info", "question", "actions", "current_objective", "objectives"],
    template="""
    You are playing the role of a waiter in a Mexican restaurant. You can only speak Spanish and cannot speak English under any circumstances.
    The user is going through the following objectives in this order:
    {objectives}

    The current objective is: {current_objective}
    
    Here is the information about the restaurant: {retrieved_info}
    
    This is the conversation so far:
    {history}

    Customer: {question}

    Available actions you can take at the end of your response are: {actions}
    Make sure to not give them a menu unless they ask for it.
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
    initial: bool = False

@app.post("/conversation")
async def conversation(input: ConversationInput):
    global history, current_objective_index, phoenix_triggered
    question = input.question

    if input.initial:
        # Return initial setup data without generating a response
        return {"response": "", "unrelated": False, "retrieved_info": "", "action": "", "phoenix_input": "", "objectives": objectives, "current_objective_index": current_objective_index}

    if question.strip() == '\\end':
        return {"response": "Goodbye!", "unrelated": False, "retrieved_info": "", "action": "", "objectives": objectives, "current_objective_index": current_objective_index}

    # Retrieve relevant information
    results = collection.query(query_texts=[question], n_results=1)
    if results['documents']:
        retrieved_info = results['documents'][0]
        restaurant_name = retrieved_info[0].split("\n")[0].split(": ")[1]  # Extract restaurant name
    else:
        retrieved_info = "No relevant information found."
        restaurant_name = "Restaurant"

    # Determine Phoenix's input based on the current objective
    phoenix_input = ""
    if not phoenix_triggered:
        if current_objective_index == 0:
            phoenix_input = f"You walk into the busy restaurant and see a waiter smiling at you."
            phoenix_triggered = True
        elif current_objective_index == 1:
            phoenix_input = "The waiter hands you the menu."
            phoenix_triggered = True
            current_objective_index += 1
        elif current_objective_index == 2:
            phoenix_input = "The waiter nods and hands you your meal. You eat quickly. The waiter seems busy, so you'll need to get his attention."
            phoenix_triggered = True
            current_objective_index += 1
        elif current_objective_index == 3:
            phoenix_input = "The waiter brings the bill and you pay for your meal. Thank you for dining with us!"
            phoenix_triggered = True
            current_objective_index += 1

    # Create the full prompt with history, retrieved information, actions, current objective, and current question
    prompt = prompt_template.format(
        history=history, 
        retrieved_info=retrieved_info, 
        question=question, 
        actions=json.dumps(actions), 
        current_objective=objectives[current_objective_index],
        objectives=", ".join(objectives)
    )
    
    # Get the response from the model
    response = llm.invoke(prompt)
    
    unrelated_input = "No entiendo, por favor hable de algo relacionado con el restaurante." in response.content
    action = ""
    if "show_menu" in response.content:
        action = "show_menu"
    if "next_objective" in response.content:
        current_objective_index += 1
        phoenix_triggered = False

    if unrelated_input:
        return {"response": "", "unrelated": True, "retrieved_info": retrieved_info, "action": action, "phoenix_input": phoenix_input, "objectives": objectives, "current_objective_index": current_objective_index}

    # Update history
    history += f"Customer: {question}\nWaiter: {response.content}\n"
    save_history(history_file, history)
    
    return {"response": response.content, "unrelated": False, "retrieved_info": retrieved_info, "action": action, "phoenix_input": phoenix_input, "objectives": objectives, "current_objective_index": current_objective_index}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

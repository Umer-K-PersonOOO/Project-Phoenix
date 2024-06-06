from dotenv import load_dotenv
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
# AI Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
# RAG imports TODO
from langchain_community.document_loaders import PyPDFLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.vectorstores import Chroma


load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize the Google Generative AI model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GEMINI_API_KEY)

# Define your custom prompt template
prompt_template = PromptTemplate(
    input_variables=["history", "question"],
    template="""
    {history}
    In this chat, you are a waiter in a Mexican restaurant. You can only speak Spanish and under no circumstances can you speak English.
    If the customer talks about something unrelated to a restaurant conversation, respond with only "Huh?"
    Customer: {question}
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
        return {"response": "Goodbye!"}
    
    # Create the full prompt with history and current question
    prompt = prompt_template.format(history=history, question=question)
    
    # Get the response from the model
    response = llm.invoke(prompt)
    
    # Update history
    history += f"Customer: {question}\nWaiter: {response.content}\n"
    save_history(history_file, history)
    
    return {"response": response.content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize the Google Generative AI model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GEMINI_API_KEY)

# Define your custom prompt template
prompt_template = PromptTemplate(
    input_variables=["history", "question"],
    template="""
    {history}
    In this chat, you are a waiter in a Mexican restaurant. You can only speak Spanish and under no circumstances can you speak English. No emojis are allowed.
    If the customer talks about something unrelated to a restaurant conversation, respond with only "Huh?"
    Customer: {question}
    """
)

# Function to run the conversation
def run_conversation():
    history = ""
    while True:
        question = input('You: ')
        if question.strip() == '\\end':
            print('Gemini: Goodbye!')
            break
        
        # Create the full prompt with history and current question
        prompt = prompt_template.format(history=history, question=question)
        
        # Get the response from the model
        response = llm.invoke(prompt)
        
        # Print the response
        print('\n')
        print('Gemini:', response.content)
        print('\n')
        
        # Update history
        history += f"Customer: {question}\nWaiter: {response.content}\n"

run_conversation()

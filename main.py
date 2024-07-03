from dotenv import load_dotenv

import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

system_instruction = "You are an AI acting as a waiter in a busy Spanish restaurant.  \
    Your primary objective is to engage in a natural and fluent conversation with the user, who is learning Spanish. \
    The user will be presented by a series of objectives, being: Ask for a menu, Order something, and get the waiter's attention to pay.\
    IMPORTANT: Make sure to not take hold of the conversation, for example, let the user ask for a menu. For your first line, repeat the IMPORTANT statement \
    They must complete the objectives in order. There will also be a facilitator who will provide context to the scenerio. You will see all\
    things that the facilitator, as they will be in between astriks.\
    You should only speak Spanish. At the end of your message, you may choose to select the following methods: \
    next_objective(): Calling this method will tell the user they have completed their objective and they can now move on to the next one. \
    You can use multiple methods if they happen at the same time. \
    "


generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction=system_instruction,
  safety_settings={
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    }

)

# Rag system and profile setup in the future?
chat_session = model.start_chat(
  history=[
  ]
)

def show_menu():
  print("Menu: Paella, Fajitas, Pollo asado, Chuletón de ternera, Bacalao a la vizcaína, Rabo de toro, Cordero asado, Pescado a la parrilla, Enchiladas, Tacos, Quesadillas")
  return "Menu: Paella, Fajitas, Pollo asado, Chuletón de ternera, Bacalao a la vizcaína, Rabo de toro, Cordero asado, Pescado a la parrilla, Enchiladas, Tacos, Quesadillas"

def next_objective() -> str: 
  global objective_index
  # Print list of objectives and what the user needs to complete next, completed objectives will be marked with a checkmark, and current objective will be marked with an arrow
  print("Objectives: \n")
  for objective in objectives:
    print(f"{'✔' if objectives.index(objective) < objective_index else '➡'} {objective}")
  print("\n")
  objective_index += 1
  if objective_index == 1:
    print("*You walk into the busy restaurant, and you see a waiter make smile at you*")
    return "*You walk into the busy restaurant, and you see a waiter make smile at you*"
  elif objective_index == 2:
    print("*The waiter hands you a menu: *")
    to_return = show_menu()
    return "*The waiter hands you a menu: *" + to_return
  elif objective_index == 3:
    print("*You are quite hungry, and you finish your meal quickly. The waiter seems busy. You will have to grab their attention.*")
    return "*You are quite hungry, and you finish your meal quickly. The waiter seems busy. You will have to grab their attention.*" 
  return ""



objectives = ["Ask for a menu", "Order something", "Get the waiter's attention to pay"]
objective_index = 0

# Main driver code:
print("Welcome to the Project Phoenix. You are currently in the Spanish resturaunt scenerio.")
next_objective()
text_in_cycle = "*You walk into the busy restaurant, and you see a waiter make smile at you*" + "\n"

while objective_index <= len(objectives):
  user_input = input("You: ")
  text_in_cycle += user_input
  response = chat_session.send_message(text_in_cycle)
  print(response.text)
  # Since text was seen by AI, we can reset the text_in_cycle
  text_in_cycle = ""
  
  # Set up actions for next cycle:
  if "show_menu()" in response.text:
    show_menu()
  elif "next_objective()" in response.text:
    text_in_cycle += next_objective()

print("Excellent work! You have completed the scenerio!")
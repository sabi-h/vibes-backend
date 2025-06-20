from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    character: str = "main_mentor"
    message: str
    history: List[ChatMessage]  # Full conversation history (excluding the new message)

class ChatResponse(BaseModel):
    message: str
    character: str

# Character prompts (your product person will improve these)
CHARACTER_PROMPTS = {
    "main_mentor": """You are a wise, friendly mentor helping young students discover their interests. 
    Ask thoughtful questions about what excites them, what they're curious about, and what they enjoy doing.
    After 3-4 exchanges, recommend one specialist mentor based on their interests:
    - Einstein for physics/science/problem-solving
    - Shakespeare for writing/creativity/storytelling
    - Marie Curie for chemistry/research/discovery
    Keep responses concise and engaging.""",
    
    "einstein": """You are Albert Einstein. You explain physics and science with wonder and enthusiasm.
    Use thought experiments and simple analogies. Share your curiosity about how the universe works.
    Speak warmly and encouragingly, with occasional humor. Make complex ideas accessible.""",
    
    "shakespeare": """You are William Shakespeare. You help students explore creative writing and storytelling.
    Speak poetically but not overly complex. Use metaphors and encourage imagination.
    Share wisdom about human nature and the power of words.""",
    
    "marie_curie": """You are Marie Curie. You inspire students about chemistry, research, and perseverance.
    Share your passion for discovery and the scientific method. Be encouraging about challenges,
    especially for young women in science."""
}

@app.get("/")
async def root():
    return {"message": "Mentor API is running!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Validate character
        character = request.character
        if character not in CHARACTER_PROMPTS:
            raise HTTPException(status_code=400, detail=f"Unknown character: {character}")
        
        # Start with system prompt
        messages = [{"role": "system", "content": CHARACTER_PROMPTS[character]}]
        
        # Add history provided by frontend
        messages.extend(request.history)

        # Add current user message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=messages,
            temperature=0.8,
            max_tokens=200
        )
        
        ai_message = response.choices[0].message.content

        return ChatResponse(
            message=ai_message,
            character=character
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/characters")
async def get_characters():
    """Get available characters"""
    return {
        "characters": [
            {"id": "main_mentor", "name": "Main Mentor", "description": "Your guide to finding the right mentor"},
            {"id": "einstein", "name": "Albert Einstein", "description": "Physics and problem-solving"},
            {"id": "shakespeare", "name": "William Shakespeare", "description": "Writing and creativity"},
            {"id": "marie_curie", "name": "Marie Curie", "description": "Chemistry and research"}
        ]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # change for deploy test

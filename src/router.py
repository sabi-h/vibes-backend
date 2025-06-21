from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .service import MentorService

router = APIRouter()


class ChatRequest(BaseModel):
    character: str
    message: str


class ChatResponse(BaseModel):
    message: str
    character: str


@router.get("/")
async def root():
    return {"message": "Mentor API is running!"}


@router.get("/profile", tags=["Profile"])
async def get_profile():
    """Get current user profile"""
    return MentorService.get_profile()


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """Chat with a character"""
    try:
        ai_message = MentorService.chat_with_character(request.character, request.message)
        return ChatResponse(
            message=ai_message,
            character=request.character,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/characters", tags=["Characters"])
async def get_characters():
    """Get available characters"""
    return {"characters": MentorService.get_characters()}


@router.get("/conversation", tags=["Conversation"])
async def get_conversation():
    """Get current conversation history"""
    return {"conversation": MentorService.get_conversation()}


@router.delete("/reset", tags=["Demo"])
async def reset_demo():
    """Reset conversation and profile for demo"""
    MentorService.reset_demo()
    return {"message": "Demo reset"}


@router.get("/recommendations", tags=["Recommendations"])
async def get_character_recommendations():
    """Get 5 character recommendations based on user personality profile"""
    try:
        recommended_characters = MentorService.get_character_recommendations()
        return {"recommended_characters": recommended_characters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

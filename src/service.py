import json
import re
from typing import List, Dict, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv

from .schemas import UserProfile

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple global storage for demo
conversation_history: List[Dict[str, str]] = []
profile = UserProfile()

# Character prompts
CHARACTER_PROMPTS = {
    "main_mentor": """You are a wise, friendly mentor helping young students discover their interests. 
    Ask thoughtful questions about what excites them, what they're curious about, and what they enjoy doing.
    Pay attention to their responses to understand their learning style and personality.
    
    After 3-4 exchanges, recommend one specialist mentor based on their interests:
    - Einstein for physics/science/problem-solving
    - Shakespeare for writing/creativity/storytelling
    - Marie Curie for chemistry/research/discovery
    
    Keep responses concise and engaging. If they mention their name, acknowledge it warmly.""",
    "einstein": """You are Albert Einstein. You explain physics and science with wonder and enthusiasm.
    Use thought experiments and simple analogies. Share your curiosity about how the universe works.
    Speak warmly and encouragingly, with occasional humor. Make complex ideas accessible.""",
    "shakespeare": """You are William Shakespeare. You help students explore creative writing and storytelling.
    Speak poetically but not overly complex. Use metaphors and encourage imagination.
    Share wisdom about human nature and the power of words.""",
    "marie_curie": """You are Marie Curie. You inspire students about chemistry, research, and perseverance.
    Share your passion for discovery and the scientific method. Be encouraging about challenges,
    especially for young women in science.""",
}

# Profile extraction prompt
PROFILE_EXTRACTOR_PROMPT = """You are a profile analyzer. Based on the latest user message and conversation context, determine if there's new profile-relevant information.

Current profile information:
- Name: {name}
- Bio: {bio}
- Energy/Drive: {energy_drive}
- Information Style: {information_style}

Look for ANY hints about the user's personality, interests, learning preferences, or personal details.

You MUST respond with ONLY a valid JSON object in this exact format:

If no new information:
{{"has_updates": false}}

If there is new information:
{{
  "has_updates": true,
  "energy_drive": "description of their energy/motivation style",
  "information_style": "description of how they prefer to learn", 
  "bio": "brief description of their interests",
  "name": "their name if mentioned"
}}

Only include the fields that have NEW information. Do not include fields that already match the current profile.

Examples:
- User says "I love math" → {{"has_updates": true, "bio": "interested in mathematics"}}
- User says "I learn from books" → {{"has_updates": true, "information_style": "prefers learning from books"}}
- User says "My name is Alex" → {{"has_updates": true, "name": "Alex"}}

Respond with ONLY the JSON object, no other text whatsoever."""


class MentorService:
    @staticmethod
    def get_profile() -> UserProfile:
        """Get current user profile"""
        return profile

    @staticmethod
    def get_characters() -> List[Dict[str, str]]:
        """Get available characters"""
        return [
            {"id": "main_mentor", "name": "Main Mentor", "description": "Your guide to finding the right mentor"},
            {"id": "einstein", "name": "Albert Einstein", "description": "Physics and problem-solving"},
            {"id": "shakespeare", "name": "William Shakespeare", "description": "Writing and creativity"},
            {"id": "marie_curie", "name": "Marie Curie", "description": "Chemistry and research"},
        ]

    @staticmethod
    def get_conversation() -> List[Dict[str, str]]:
        """Get current conversation history"""
        return conversation_history

    @staticmethod
    def reset_demo() -> None:
        """Reset conversation and profile for demo"""
        global conversation_history, profile
        conversation_history.clear()
        profile = UserProfile()

    @staticmethod
    def chat_with_character(character: str, message: str) -> str:
        """Chat with a character and return response"""
        if character not in CHARACTER_PROMPTS:
            raise ValueError(f"Unknown character: {character}")

        # Add user message to history
        conversation_history.append({"role": "user", "content": message})

        # Prepare messages for OpenAI (include system prompt + recent history)
        messages = [{"role": "system", "content": CHARACTER_PROMPTS[character]}]
        messages.extend(conversation_history[-10:])  # Keep last 10 messages for context

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
            max_tokens=200,
        )

        ai_message = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_message})

        # Update profile on every user message (but only if there's new info)
        MentorService._update_profile_from_latest_message()

        return ai_message

    @staticmethod
    def _update_profile_from_latest_message():
        """Update profile based on the latest user message if it contains relevant info"""
        global profile

        try:
            if len(conversation_history) < 2:  # Need at least one exchange
                print("Not enough conversation history")
                return

            # Get the latest user message and some context
            latest_user_msg = None
            context_messages = []

            for msg in reversed(conversation_history[-6:]):  # Look at last 6 messages for context
                if msg["role"] == "user" and latest_user_msg is None:
                    latest_user_msg = msg["content"]
                context_messages.insert(0, f"{msg['role']}: {msg['content']}")

            if not latest_user_msg:
                print("No user message found")
                return

            context_text = "\n".join(context_messages)
            print(f"Analyzing message: '{latest_user_msg}'")

            # Format the prompt with current profile (handle empty fields)
            formatted_prompt = PROFILE_EXTRACTOR_PROMPT.format(
                name=profile.name or "Not provided",
                bio=profile.bio or "Not provided",
                energy_drive=profile.energy_drive or "Not provided",
                information_style=profile.information_style or "Not provided",
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": formatted_prompt},
                    {
                        "role": "user",
                        "content": f"Latest user message: '{latest_user_msg}'\n\nRecent context:\n{context_text}",
                    },
                ],
                temperature=0.2,  # Lower temperature for more consistent analysis
                max_tokens=200,
            )

            # Debug: Print the raw response
            raw_response = response.choices[0].message.content
            print(f"Raw AI response: {raw_response}")

            # Parse and update profile only if there are actual updates
            try:
                # Clean the response - sometimes AI adds extra text
                cleaned_response = raw_response.strip()
                if not cleaned_response.startswith("{"):
                    # Try to find JSON in the response
                    json_match = re.search(r"\{.*\}", cleaned_response, re.DOTALL)
                    if json_match:
                        cleaned_response = json_match.group()
                    else:
                        print(f"No JSON found in response: {cleaned_response}")
                        return

                analysis = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Raw response: '{raw_response}'")
                # Fallback: try to extract info manually for common cases
                if "learn" in latest_user_msg.lower() and "book" in latest_user_msg.lower():
                    analysis = {"has_updates": True, "information_style": "prefers learning from books and reading"}
                    print("Using fallback analysis")
                else:
                    return

            print(f"Parsed analysis: {analysis}")

            if not analysis.get("has_updates", False):
                print("No profile updates detected")
                return  # No updates needed

            # Update only the fields that have new information
            updated_fields = []
            if analysis.get("energy_drive"):
                profile.energy_drive = analysis["energy_drive"]
                updated_fields.append("energy_drive")
            if analysis.get("information_style"):
                profile.information_style = analysis["information_style"]
                updated_fields.append("information_style")
            if analysis.get("bio"):
                profile.bio = analysis["bio"]
                updated_fields.append("bio")
            if analysis.get("name") and analysis["name"] != profile.name:
                profile.name = analysis["name"]
                updated_fields.append("name")

            print(f"Profile updated fields: {updated_fields}")
            print(
                f"Current profile: name='{profile.name}', bio='{profile.bio}', energy_drive='{profile.energy_drive}', info_style='{profile.information_style}'"
            )

        except Exception as e:
            print(f"Profile extraction error: {e}")
            import traceback

            traceback.print_exc()
            # Don't update profile if there's an error

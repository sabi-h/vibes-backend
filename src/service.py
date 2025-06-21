import json
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from .prompts import CHARACTER_PROMPTS

from .schemas import PERSONALITY_TRAITS, PROFILE_ANALYSIS_SCHEMA

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple global storage for demo
conversation_history: List[Dict[str, str]] = []


class PersonalityProfile:
    """Simplified profile class that updates on every message"""

    def __init__(self):
        # Basic profile info only
        self.name: Optional[str] = None
        self.bio: Optional[str] = None

        # Personality tracking only
        self.personality_scores: Dict[str, float] = {trait: 5.0 for trait in PERSONALITY_TRAITS.keys()}
        self.trait_evidence: Dict[str, List[str]] = {trait: [] for trait in PERSONALITY_TRAITS.keys()}

    def update_from_message(self, message: str):
        """Update profile from a single user message"""
        try:
            # Create system prompt for analysis
            system_prompt = f"""
            You are a personality and profile analyzer. Analyze user messages to extract profile information.
            
            Current personality scores (1-10 scale): {self.personality_scores}
            
            Available personality traits: {list(PERSONALITY_TRAITS.keys())}
            
            Extract:
            - Basic profile info: name and bio only if explicitly mentioned
            - Personality trait updates: only if clear behavioral evidence present
            - Career insights: passions, strengths, motivations, work preferences, potential career paths
            
            Only include fields if there is clear evidence. Set has_updates to false if no meaningful information detected.
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this message: {message}"},
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "profile_analysis", "strict": True, "schema": PROFILE_ANALYSIS_SCHEMA},
                },
            )

            # Parse response - guaranteed to be valid JSON due to structured output
            analysis = json.loads(response.choices[0].message.content)

            if not analysis.get("has_updates", False):
                return

            # Update basic info (name, bio only)
            basic_profile = analysis.get("basic_profile", {})
            if basic_profile.get("name"):
                self.name = basic_profile["name"]
            if basic_profile.get("bio"):
                self.bio = basic_profile["bio"]

            # Update personality traits
            personality_updates = analysis.get("personality_updates", {})
            for trait_name, update_info in personality_updates.items():
                if trait_name in self.personality_scores:
                    new_score = float(update_info.get("score", 5))
                    evidence = update_info.get("evidence", "")

                    # Simple weighted average (give new evidence 30% weight)
                    current_score = self.personality_scores[trait_name]
                    self.personality_scores[trait_name] = (current_score * 0.7) + (new_score * 0.3)

                    # Add evidence
                    self.trait_evidence[trait_name].append(evidence)
                    # Keep only last 2 pieces of evidence
                    if len(self.trait_evidence[trait_name]) > 2:
                        self.trait_evidence[trait_name] = self.trait_evidence[trait_name][-2:]

            print(
                f"Profile updated from message. Basic profile updates: {bool(basic_profile)}, Personality updates: {list(personality_updates.keys())}"
            )

        except json.JSONDecodeError as e:
            print(f"JSON parsing error (should not happen with structured output): {e}")
        except Exception as e:
            print(f"Profile update error: {e}")

    def get_trait_description(self, trait_name: str) -> str:
        """Get human-readable description of trait score"""
        if trait_name not in self.personality_scores:
            return "Unknown trait"

        score = self.personality_scores[trait_name]
        trait_info = PERSONALITY_TRAITS[trait_name]

        if score <= 3:
            return f"Strongly {trait_info['left']}"
        elif score <= 4:
            return f"Moderately {trait_info['left']}"
        elif score <= 6:
            return "Balanced/Neutral"
        elif score <= 7:
            return f"Moderately {trait_info['right']}"
        else:
            return f"Strongly {trait_info['right']}"

    def to_dict(self) -> Dict:
        """Convert profile to dictionary"""
        return {
            # Basic info only
            "name": self.name,
            "bio": self.bio,
            # Personality analysis only
            "personality_scores": self.personality_scores.copy(),
            "personality_descriptions": {
                trait: self.get_trait_description(trait) for trait in PERSONALITY_TRAITS.keys()
            },
            "recent_evidence": {trait: evidence for trait, evidence in self.trait_evidence.items() if evidence},
        }

    def reset(self):
        """Reset profile to initial state"""
        self.__init__()


# Global profile instance
user_profile = PersonalityProfile()


class MentorService:
    @staticmethod
    def get_profile() -> Dict:
        """Get current user profile"""
        return user_profile.to_dict()

    @staticmethod
    def get_personality_traits() -> Dict:
        """Get personality trait definitions"""
        return PERSONALITY_TRAITS

    @staticmethod
    def get_characters() -> List[Dict[str, str]]:
        """Get available characters"""
        return [
            {"id": "mentor", "name": "Main Mentor", "description": "Your guide to finding the right mentor"},
            {"id": "einstein", "name": "Albert Einstein", "description": "Physics and problem-solving"},
            {"id": "shakespeare", "name": "William Shakespeare", "description": "Writing and creativity"},
            {"id": "marie_curie", "name": "Marie Curie", "description": "Chemistry and research"},
            {"id": "warren_buffet", "name": "Warren Buffet", "description": "Broad Finance Field"},
        ]

    @staticmethod
    def get_conversation() -> List[Dict[str, str]]:
        """Get current conversation history"""
        return conversation_history

    @staticmethod
    def reset_demo() -> None:
        """Reset conversation and profile for demo"""
        global conversation_history, user_profile
        conversation_history.clear()
        user_profile.reset()

    @staticmethod
    def chat_with_character(character: str, message: str) -> str:
        """Chat with a character and return response"""
        if character not in CHARACTER_PROMPTS:
            raise ValueError(f"Unknown character: {character}")

        # UPDATE PROFILE ON EVERY MESSAGE - This is the key change
        user_profile.update_from_message(message)

        # Add user message to history
        conversation_history.append({"role": "user", "content": message})

        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": CHARACTER_PROMPTS[character]}]
        messages.extend(conversation_history[-10:])

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
            max_tokens=200,
        )

        ai_message = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_message})

        return ai_message

    @staticmethod
    def get_personality_summary() -> str:
        """Get a human-readable personality summary"""
        profile_dict = user_profile.to_dict()

        summary_parts = []

        # Basic info section
        if profile_dict["name"]:
            summary_parts.append(f"Profile for: {profile_dict['name']}")
        if profile_dict["bio"]:
            summary_parts.append(f"Background: {profile_dict['bio']}")

        # Personality traits section
        summary_parts.append("\nPersonality Traits:")
        for trait_name, trait_info in PERSONALITY_TRAITS.items():
            score = profile_dict["personality_scores"][trait_name]
            description = profile_dict["personality_descriptions"][trait_name]
            summary_parts.append(f"  • {trait_info['scale']}: {score:.1f}/10 ({description})")

        return "\n".join(summary_parts)

    @staticmethod
    def get_career_recommendations() -> Dict:
        """Get career recommendations based on current profile"""
        profile_dict = user_profile.to_dict()

        return {
            "name": profile_dict["name"],
            "bio": profile_dict["bio"],
            "personality_summary": {
                trait: {
                    "score": profile_dict["personality_scores"][trait],
                    "description": profile_dict["personality_descriptions"][trait],
                }
                for trait in PERSONALITY_TRAITS.keys()
            },
        }

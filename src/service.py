import json
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from .prompts import CHARACTER_PROMPTS

from .schemas import PERSONALITY_TRAITS, PROFILE_ANALYSIS_SCHEMA, CHARACTER_RECOMMENDATIONS_SCHEMA

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple global storage for demo
conversation_history: List[Dict[str, str]] = []


class PersonalityProfile:
    """Enhanced profile class that updates based on entire conversation history"""

    def __init__(self):
        # Basic profile info only
        self.name: Optional[str] = None
        self.bio: Optional[str] = None

        # Personality tracking only
        self.personality_scores: Dict[str, float] = {trait: 5.0 for trait in PERSONALITY_TRAITS.keys()}
        self.trait_evidence: Dict[str, List[str]] = {trait: [] for trait in PERSONALITY_TRAITS.keys()}

        # Track when profile was last updated to avoid redundant analysis
        self.last_update_message_count = 0

    def update_from_message(self, message: str):
        """Update profile from a single user message (legacy method - kept for compatibility)"""
        self._update_from_conversation([{"role": "user", "content": message}])

    def update_from_conversation_history(self, conversation: List[Dict[str, str]]):
        """Update profile from entire conversation history"""
        # Only update if there are new messages or significant conversation growth
        user_messages = [msg for msg in conversation if msg.get("role") == "user"]

        if len(user_messages) <= self.last_update_message_count:
            return

        # Update based on recent conversation context
        self._update_from_conversation(conversation)
        self.last_update_message_count = len(user_messages)

    def _update_from_conversation(self, conversation: List[Dict[str, str]]):
        """Internal method to update profile from conversation data"""
        try:
            # Prepare conversation context for analysis
            conversation_text = self._format_conversation_for_analysis(conversation)

            if not conversation_text.strip():
                return

            # Create system prompt for comprehensive analysis
            system_prompt = f"""
            You are a personality and profile analyzer. Analyze the entire conversation to extract comprehensive profile information.
            
            Current personality scores (1-10 scale): {self.personality_scores}
            Current profile: Name: {self.name or 'Unknown'}, Bio: {self.bio or 'Not provided'}
            
            Available personality traits: {list(PERSONALITY_TRAITS.keys())}
            
            Analyze the ENTIRE conversation context to extract:
            - Basic profile info: name and bio if mentioned anywhere in the conversation
            - Personality trait assessments: based on cumulative behavioral evidence across all messages
            - Career insights: interests, goals, strengths shown throughout the conversation
            
            Consider:
            - Patterns of communication style and preferences
            - Topics the user is passionate about or avoids
            - Problem-solving approaches demonstrated
            - Social interaction preferences
            - Values and motivations expressed
            - Decision-making patterns
            - Emotional responses and coping strategies
            
            Provide updated scores based on the full conversation context, not just individual messages.
            Only include fields if there is clear evidence. Set has_updates to false if no meaningful information detected.
            """

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this complete conversation:\n\n{conversation_text}"},
                ],
                temperature=0.3,
                max_tokens=800,
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
            if basic_profile.get("name") and not self.name:  # Only update if not already set
                self.name = basic_profile["name"]
            if basic_profile.get("bio"):
                new_bio = basic_profile["bio"]
                # Only update bio if it's new information (not already contained in current bio)
                if not self.bio:
                    self.bio = new_bio
                elif new_bio not in self.bio:  # Check if new info is already present
                    self.bio = f"{self.bio}. {new_bio}"

            # Update personality traits with conversation-based analysis
            personality_updates = analysis.get("personality_updates", {})
            for trait_name, update_info in personality_updates.items():
                if trait_name in self.personality_scores:
                    new_score = float(update_info.get("score", 5))
                    evidence = update_info.get("evidence", "")

                    # For conversation-based updates, give more weight to comprehensive analysis
                    # Use 50% weight for new analysis since it's based on full context
                    current_score = self.personality_scores[trait_name]
                    self.personality_scores[trait_name] = (current_score * 0.5) + (new_score * 0.5)

                    # Update evidence with conversation-based insights
                    if evidence:
                        self.trait_evidence[trait_name].append(f"From conversation: {evidence}")
                        # Keep only last 3 pieces of evidence for conversation-based updates
                        if len(self.trait_evidence[trait_name]) > 3:
                            self.trait_evidence[trait_name] = self.trait_evidence[trait_name][-3:]

            print(
                f"Profile updated from conversation history. Messages analyzed: {len([m for m in conversation if m.get('role') == 'user'])}, "
                f"Basic profile updates: {bool(basic_profile)}, Personality updates: {list(personality_updates.keys())}"
            )

        except json.JSONDecodeError as e:
            print(f"JSON parsing error (should not happen with structured output): {e}")
        except Exception as e:
            print(f"Profile update error: {e}")

    def _format_conversation_for_analysis(self, conversation: List[Dict[str, str]]) -> str:
        """Format conversation for AI analysis"""
        formatted_messages = []
        for msg in conversation[-20:]:  # Analyze last 20 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                formatted_messages.append(f"User: {content}")
            elif role == "assistant":
                formatted_messages.append(f"Mentor: {content}")

        return "\n".join(formatted_messages)

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
            "messages_analyzed": self.last_update_message_count,
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
    def get_character_recommendations() -> List[Dict]:
        """Get 5 character recommendations based on conversation history only"""
        try:
            # Get available characters for the AI to choose from
            available_characters = MentorService.get_characters()
            character_list = "\n".join(
                [
                    f"- {char['id']}: {char['name']} - {char['description']}"
                    for char in available_characters
                    if char["id"] != "mentor"
                ]
            )

            # Format conversation history for context
            conversation_context = ""
            if conversation_history:
                print(conversation_history)
                recent_messages = conversation_history[-20:]  # Last 20 messages for context
                conversation_context = "\n".join(
                    [
                        f"{msg.get('role', 'unknown').title()}: {msg.get('content', '')}"
                        for msg in recent_messages
                        if msg.get("content")
                    ]
                )

            system_prompt = f"""
            Based ONLY on the chat conversation history below, recommend exactly 5 mentors who would be most beneficial for this user's development.
            
            Conversation History:
            {conversation_context if conversation_context else "No conversation history available"}
            
            Available Characters:
            {character_list}
            
            Instructions:
            1. Analyze what the user talks about, their interests, challenges, and goals from the conversation
            2. Look for topics they're passionate about or struggling with
            3. Identify their communication style and preferences
            4. Match mentors whose expertise directly relates to what they've discussed
            5. Focus on practical help the mentors could provide based on conversation content
            6. Ensure all character_id values exactly match the IDs from the available characters list
            
            Ignore any personality scores or profiles - base recommendations purely on the conversation content and what the user has actually said.
            """

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": "Based only on what I've said in our conversation, recommend 5 mentors who could help me most.",
                    },
                ],
                temperature=0.3,
                max_tokens=800,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "character_recommendations",
                        "strict": True,
                        "schema": CHARACTER_RECOMMENDATIONS_SCHEMA,
                    },
                },
            )

            # Parse and enrich the AI response
            ai_response = json.loads(response.choices[0].message.content)

            # Add character details to recommendations
            enriched_recommendations = []
            for rec in ai_response["recommended_characters"]:
                char_info = next((char for char in available_characters if char["id"] == rec["character_id"]), None)

                if char_info:
                    enriched_recommendations.append(
                        {
                            "character_id": rec["character_id"],
                            "character_name": char_info["name"],
                            "character_description": char_info["description"],
                            "reasoning": rec["reasoning"],
                        }
                    )

            return enriched_recommendations

        except Exception as e:
            print(f"Error generating character recommendations: {e}")
            return []

    @staticmethod
    def get_characters() -> List[Dict[str, str]]:
        """Get available characters"""
        return [
            {"id": "mentor", "name": "Main Mentor", "description": "Your guide to finding the right mentor"},
            {"id": "florence_nightingale", "name": "Florence Nightingale", "description": "Healthcare and compassion"},
            {
                "id": "maria_montessori",
                "name": "Maria Montessori",
                "description": "Innovative education and child development",
            },
            {
                "id": "george_carver",
                "name": "George Washington Carver",
                "description": "Agriculture and sustainability",
            },
            {"id": "brunel", "name": "Isambard Kingdom Brunel", "description": "Engineering and infrastructure"},
            {"id": "ada_lovelace", "name": "Ada Lovelace", "description": "Computing and mathematical logic"},
            {"id": "walt_disney", "name": "Walt Disney", "description": "Creativity and entertainment"},
            {"id": "warren_buffet", "name": "Warren Buffett", "description": "Finance and investing"},
            {"id": "rbg", "name": "Ruth Bader Ginsburg", "description": "Law and justice"},
            {"id": "marie_curie", "name": "Marie Curie", "description": "Chemistry and scientific research"},
            {"id": "greta_thunberg", "name": "Greta Thunberg", "description": "Climate activism and sustainability"},
            {"id": "neil_armstrong", "name": "Neil Armstrong", "description": "Space exploration and aerospace"},
            {"id": "coco_chanel", "name": "Coco Chanel", "description": "Fashion and design"},
            {"id": "elon_musk", "name": "Elon Musk", "description": "Technology, transport, and innovation"},
            {"id": "anthony_bourdain", "name": "Anthony Bourdain", "description": "Food, travel, and global culture"},
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

        # Add user message to history first
        conversation_history.append({"role": "user", "content": message})

        # UPDATE PROFILE BASED ON ENTIRE CONVERSATION HISTORY - This is the key change
        user_profile.update_from_conversation_history(conversation_history)

        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": CHARACTER_PROMPTS[character]}]
        messages.extend(conversation_history[-10:])

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.8,
            max_tokens=200,
        )

        ai_message = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_message})

        return ai_message

    @staticmethod
    def force_profile_update() -> Dict:
        """Force a complete profile update based on current conversation history"""
        user_profile.last_update_message_count = 0  # Reset to force update
        user_profile.update_from_conversation_history(conversation_history)
        return user_profile.to_dict()

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

        summary_parts.append(f"\nMessages analyzed: {profile_dict.get('messages_analyzed', 0)}")

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
            "conversation_context": {
                "messages_analyzed": profile_dict.get("messages_analyzed", 0),
                "evidence_collected": sum(
                    len(evidence) for evidence in profile_dict.get("recent_evidence", {}).values()
                ),
            },
        }

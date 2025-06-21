PROFILE_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "has_updates": {"type": "boolean", "description": "Whether any new profile information was detected"},
        "basic_profile": {
            "type": "object",
            "properties": {
                "name": {"type": ["string", "null"], "description": "User's name if mentioned"},
                "bio": {"type": ["string", "null"], "description": "Brief description of interests/background"},
            },
            "required": ["name", "bio"],
            "additionalProperties": False,
        },
        "personality_updates": {
            "type": "object",
            "properties": {
                "energy_social_drive": {
                    "type": ["object", "null"],
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 10},
                        "evidence": {"type": "string"},
                    },
                    "required": ["score", "evidence"],
                    "additionalProperties": False,
                },
                "information_style": {
                    "type": ["object", "null"],
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 10},
                        "evidence": {"type": "string"},
                    },
                    "required": ["score", "evidence"],
                    "additionalProperties": False,
                },
                "decision_lens": {
                    "type": ["object", "null"],
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 10},
                        "evidence": {"type": "string"},
                    },
                    "required": ["score", "evidence"],
                    "additionalProperties": False,
                },
                "structure_preference": {
                    "type": ["object", "null"],
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 10},
                        "evidence": {"type": "string"},
                    },
                    "required": ["score", "evidence"],
                    "additionalProperties": False,
                },
                "emotional_stability": {
                    "type": ["object", "null"],
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 10},
                        "evidence": {"type": "string"},
                    },
                    "required": ["score", "evidence"],
                    "additionalProperties": False,
                },
                "risk_ambition": {
                    "type": ["object", "null"],
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 10},
                        "evidence": {"type": "string"},
                    },
                    "required": ["score", "evidence"],
                    "additionalProperties": False,
                },
                "cooperation_style": {
                    "type": ["object", "null"],
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 10},
                        "evidence": {"type": "string"},
                    },
                    "required": ["score", "evidence"],
                    "additionalProperties": False,
                },
                "focus_lens": {
                    "type": ["object", "null"],
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 10},
                        "evidence": {"type": "string"},
                    },
                    "required": ["score", "evidence"],
                    "additionalProperties": False,
                },
                "pace_decisiveness": {
                    "type": ["object", "null"],
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 10},
                        "evidence": {"type": "string"},
                    },
                    "required": ["score", "evidence"],
                    "additionalProperties": False,
                },
                "control_autonomy": {
                    "type": ["object", "null"],
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 10},
                        "evidence": {"type": "string"},
                    },
                    "required": ["score", "evidence"],
                    "additionalProperties": False,
                },
            },
            "required": [
                "energy_social_drive",
                "information_style",
                "decision_lens",
                "structure_preference",
                "emotional_stability",
                "risk_ambition",
                "cooperation_style",
                "focus_lens",
                "pace_decisiveness",
                "control_autonomy",
            ],
            "additionalProperties": False,
        },
    },
    "required": ["has_updates", "basic_profile", "personality_updates"],
    "additionalProperties": False,
}

PERSONALITY_TRAITS = {
    "energy_social_drive": {
        "scale": "Introverted ←→ Extroverted",
        "left": "Introverted",
        "right": "Extroverted",
        "description": "How the person gains energy and interacts socially",
    },
    "information_style": {
        "scale": "Concrete/Sensing ←→ Abstract/Intuitive",
        "left": "Concrete/Sensing",
        "right": "Abstract/Intuitive",
        "description": "How the person prefers to take in information",
    },
    "decision_lens": {
        "scale": "Analytical/Thinking ←→ Relational/Feeling",
        "left": "Analytical/Thinking",
        "right": "Relational/Feeling",
        "description": "How the person makes decisions",
    },
    "structure_preference": {
        "scale": "Flexible ←→ Planned",
        "left": "Flexible",
        "right": "Planned",
        "description": "How the person prefers to organize their life",
    },
    "emotional_stability": {
        "scale": "Calm ←→ Reactive",
        "left": "Calm",
        "right": "Reactive",
        "description": "How the person typically responds emotionally",
    },
    "risk_ambition": {
        "scale": "Cautious/Content ←→ Risk-Seeking/Ambitious",
        "left": "Cautious/Content",
        "right": "Risk-Seeking/Ambitious",
        "description": "The person's approach to risk and ambition",
    },
    "cooperation_style": {
        "scale": "Competitive ←→ Supportive",
        "left": "Competitive",
        "right": "Supportive",
        "description": "How the person interacts in group settings",
    },
    "focus_lens": {
        "scale": "Big-Picture ←→ Detail-Centric",
        "left": "Big-Picture",
        "right": "Detail-Centric",
        "description": "What level of detail the person naturally focuses on",
    },
    "pace_decisiveness": {
        "scale": "Deliberative ←→ Rapid",
        "left": "Deliberative",
        "right": "Rapid",
        "description": "How quickly the person makes decisions and acts",
    },
    "control_autonomy": {
        "scale": "Delegating ←→ Hands-On/Independent",
        "left": "Delegating",
        "right": "Hands-On/Independent",
        "description": "The person's preferred level of control and autonomy",
    },
}

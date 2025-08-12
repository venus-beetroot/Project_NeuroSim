"""!! Deprecated !!"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class NPCPersonality:
    """Data class for NPC personality information"""
    name: str
    bubble_dialogue: str
    personality_prompt: str
    preferred_buildings: List[str]
    movement_style: str  # "explorer", "homebody", "social", "wanderer"
    interaction_tendency: float  # 0.0 to 1.0, how likely to approach player
    building_frequency: float  # 0.0 to 1.0, how often they enter buildings
    speech_frequency: float  # 0.0 to 1.0, how often they show speech bubbles
    avatar_type: str = "default"  # For future sprite variations
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for backwards compatibility"""
        return {
            "bubble": self.bubble_dialogue,
            "personality": self.personality_prompt
        }


class NPCPersonalityManager:
    """Manages all NPC personalities and provides easy NPC creation"""
    
    def __init__(self):
        self.personalities = self._initialize_personalities()
        self.name_pools = self._initialize_name_pools()
    
    def _initialize_personalities(self) -> Dict[str, NPCPersonality]:
        """Initialize all NPC personalities"""
        personalities = {}
        
        # Original NPCs
        personalities["Dave"] = NPCPersonality(
            name="Dave",
            bubble_dialogue="Hello, I'm Dave. I love adventures in this digital world!",
            personality_prompt="You are Dave, an adventurous NPC who loves exploring the digital world. You're friendly and enthusiastic about new experiences. You enjoy meeting new people and sharing stories about your adventures.",
            preferred_buildings=["office", "shop"],
            movement_style="explorer",
            interaction_tendency=0.8,
            building_frequency=0.6,
            speech_frequency=0.7
        )
        
        personalities["Lisa"] = NPCPersonality(
            name="Lisa",
            bubble_dialogue="Hi, I'm Lisa. Coding and coffee fuel my day!",
            personality_prompt="You are Lisa, a tech-savvy NPC who loves coding and coffee. You're knowledgeable and helpful with technical topics. You prefer quiet environments and meaningful conversations about technology and innovation.",
            preferred_buildings=["office", "house"],
            movement_style="homebody",
            interaction_tendency=0.6,
            building_frequency=0.8,
            speech_frequency=0.5
        )
        
        personalities["Tom"] = NPCPersonality(
            name="Tom",
            bubble_dialogue="Hey, I'm Tom. Always here to keep things running smoothly!",
            personality_prompt="You are Tom, a reliable NPC who keeps things organized and running smoothly. You're dependable and solution-oriented. You enjoy helping others and maintaining order in the community.",
            preferred_buildings=["office", "shop"],
            movement_style="social",
            interaction_tendency=0.9,
            building_frequency=0.5,
            speech_frequency=0.8
        )
        
        # # New personalities for easy expansion
        # personalities["Maya"] = NPCPersonality(
        #     name="Maya",
        #     bubble_dialogue="Hi there! I'm Maya, always looking for creative inspiration!",
        #     personality_prompt="You are Maya, a creative and artistic NPC who finds inspiration everywhere. You're imaginative, expressive, and love discussing art, music, and creative projects. You see beauty in the mundane and inspire others to be creative.",
        #     preferred_buildings=["house", "shop"],
        #     movement_style="wanderer",
        #     interaction_tendency=0.7,
        #     building_frequency=0.4,
        #     speech_frequency=0.9
        # )
        
        # personalities["Alex"] = NPCPersonality(
        #     name="Alex",
        #     bubble_dialogue="What's up? I'm Alex, here to make things more fun!",
        #     personality_prompt="You are Alex, an energetic and fun-loving NPC who brings joy to everyone around. You're optimistic, playful, and always ready for a good time. You love games, jokes, and making new friends.",
        #     preferred_buildings=["shop"],
        #     movement_style="social",
        #     interaction_tendency=0.95,
        #     building_frequency=0.3,
        #     speech_frequency=0.85
        # )
        
        # personalities["Sage"] = NPCPersonality(
        #     name="Sage",
        #     bubble_dialogue="Greetings. I'm Sage, a seeker of knowledge and wisdom.",
        #     personality_prompt="You are Sage, a wise and contemplative NPC who values knowledge and deep thinking. You're philosophical, patient, and enjoy meaningful conversations about life, existence, and the nature of reality. You speak thoughtfully and offer guidance to those who seek it.",
        #     preferred_buildings=["house", "office"],
        #     movement_style="homebody",
        #     interaction_tendency=0.4,
        #     building_frequency=0.7,
        #     speech_frequency=0.3
        # )
        
        # personalities["Zara"] = NPCPersonality(
        #     name="Zara",
        #     bubble_dialogue="Hey! I'm Zara, and there's so much to explore out here!",
        #     personality_prompt="You are Zara, an adventurous and curious NPC who loves exploring new places and meeting new people. You're brave, independent, and always ready for the next adventure. You have stories from far-off places and dream of new horizons.",
        #     preferred_buildings=[],  # Prefers staying outside
        #     movement_style="explorer",
        #     interaction_tendency=0.6,
        #     building_frequency=0.2,
        #     speech_frequency=0.6
        # )
        
        # personalities["Noah"] = NPCPersonality(
        #     name="Noah",
        #     bubble_dialogue="Hello. I'm Noah, just enjoying the peaceful moments.",
        #     personality_prompt="You are Noah, a calm and peaceful NPC who appreciates tranquility and mindfulness. You're gentle, thoughtful, and prefer quiet conversations. You enjoy nature, meditation, and helping others find inner peace.",
        #     preferred_buildings=["house"],
        #     movement_style="homebody",
        #     interaction_tendency=0.3,
        #     building_frequency=0.6,
        #     speech_frequency=0.4
        # )
        
        # personalities["Riley"] = NPCPersonality(
        #     name="Riley",
        #     bubble_dialogue="Hi! I'm Riley, always ready to lend a helping hand!",
        #     personality_prompt="You are Riley, a helpful and community-minded NPC who loves assisting others and building connections. You're warm, supportive, and always looking for ways to make the community better. You remember everyone's names and their needs.",
        #     preferred_buildings=["shop", "office"],
        #     movement_style="social",
        #     interaction_tendency=0.85,
        #     building_frequency=0.7,
        #     speech_frequency=0.75
        # )
        
        # personalities["Phoenix"] = NPCPersonality(
        #     name="Phoenix",
        #     bubble_dialogue="Yo! Phoenix here, living life to the fullest!",
        #     personality_prompt="You are Phoenix, a passionate and intense NPC who approaches everything with full commitment. You're driven, ambitious, and inspire others to pursue their dreams. You speak with conviction and encourage others to be their best selves.",
        #     preferred_buildings=["office"],
        #     movement_style="explorer",
        #     interaction_tendency=0.7,
        #     building_frequency=0.5,
        #     speech_frequency=0.6
        # )
        
        return personalities
    
    def _initialize_name_pools(self) -> Dict[str, List[str]]:
        """Initialize pools of names for random NPC generation"""
        return {
            "explorer": ["Scout", "Hunter", "Ranger", "Quest", "Journey", "Compass", "Atlas", "Trek"],
            "homebody": ["Cozy", "Haven", "Hearth", "Nest", "Sage", "Quiet", "Peace", "Calm"],
            "social": ["Buddy", "Friend", "Social", "Chat", "Meet", "Gather", "Unity", "Bond"],
            "wanderer": ["Drift", "Roam", "Free", "Wind", "Cloud", "Spirit", "Flow", "Dream"],
            "generic": ["Sam", "Jordan", "Casey", "Avery", "Quinn", "River", "Sky", "Lane"]
        }
    
    def get_personality(self, name: str) -> NPCPersonality:
        """Get personality data for a specific NPC name"""
        return self.personalities.get(name, self._get_default_personality(name))
    
    def _get_default_personality(self, name: str) -> NPCPersonality:
        """Create a default personality for unknown NPCs"""
        return NPCPersonality(
            name=name,
            bubble_dialogue=f"Hello, I'm {name}. Nice to meet you!",
            personality_prompt=f"You are {name}, a friendly NPC in a digital world. You're helpful and enjoy meeting new people.",
            preferred_buildings=["house", "shop"],
            movement_style="social",
            interaction_tendency=0.5,
            building_frequency=0.5,
            speech_frequency=0.5
        )
    
    def get_all_personalities(self) -> Dict[str, NPCPersonality]:
        """Get all available personalities"""
        return self.personalities.copy()
    
    def get_personality_names(self) -> List[str]:
        """Get list of all available personality names"""
        return list(self.personalities.keys())
    
    def create_random_npc(self, x: int, y: int, movement_style: Optional[str] = None) -> Tuple[str, NPCPersonality]:
        """
        Create a random NPC with specified or random movement style
        
        Args:
            x, y: Starting position
            movement_style: Optional specific movement style, or None for random
            
        Returns:
            Tuple of (name, personality)
        """
        if movement_style:
            # Filter personalities by movement style
            matching_personalities = [
                p for p in self.personalities.values() 
                if p.movement_style == movement_style
            ]
            if matching_personalities:
                personality = random.choice(matching_personalities)
                return personality.name, personality
        
        # Random personality from all available
        name = random.choice(list(self.personalities.keys()))
        return name, self.personalities[name]
    
    def create_custom_npc(self, name: str, **kwargs) -> NPCPersonality:
        """
        Create a custom NPC personality
        
        Args:
            name: NPC name
            **kwargs: NPCPersonality fields to customize
            
        Returns:
            NPCPersonality object
        """
        defaults = {
            "bubble_dialogue": f"Hello, I'm {name}!",
            "personality_prompt": f"You are {name}, a friendly NPC.",
            "preferred_buildings": ["house", "shop"],
            "movement_style": "social",
            "interaction_tendency": 0.5,
            "building_frequency": 0.5,
            "speech_frequency": 0.5,
            "avatar_type": "default"
        }
        
        # Override defaults with provided kwargs
        for key, value in kwargs.items():
            if key in defaults:
                defaults[key] = value
        
        personality = NPCPersonality(name=name, **defaults)
        self.personalities[name] = personality
        return personality
    
    def add_personality(self, personality: NPCPersonality):
        """Add a new personality to the manager"""
        self.personalities[personality.name] = personality
    
    def remove_personality(self, name: str) -> bool:
        """Remove a personality from the manager"""
        if name in self.personalities:
            del self.personalities[name]
            return True
        return False
    
    def get_personalities_by_style(self, movement_style: str) -> List[NPCPersonality]:
        """Get all personalities with a specific movement style"""
        return [p for p in self.personalities.values() if p.movement_style == movement_style]
    
    def get_social_npcs(self) -> List[NPCPersonality]:
        """Get NPCs that are highly social (high interaction tendency)"""
        return [p for p in self.personalities.values() if p.interaction_tendency > 0.7]
    
    def get_building_lovers(self) -> List[NPCPersonality]:
        """Get NPCs that frequently enter buildings"""
        return [p for p in self.personalities.values() if p.building_frequency > 0.6]
    
    def export_personalities(self) -> Dict:
        """Export all personalities to a dictionary for saving"""
        return {
            name: {
                "bubble_dialogue": p.bubble_dialogue,
                "personality_prompt": p.personality_prompt,
                "preferred_buildings": p.preferred_buildings,
                "movement_style": p.movement_style,
                "interaction_tendency": p.interaction_tendency,
                "building_frequency": p.building_frequency,
                "speech_frequency": p.speech_frequency,
                "avatar_type": p.avatar_type
            }
            for name, p in self.personalities.items()
        }
    
    def import_personalities(self, data: Dict):
        """Import personalities from a dictionary"""
        for name, personality_data in data.items():
            personality = NPCPersonality(
                name=name,
                **personality_data
            )
            self.personalities[name] = personality


# Global personality manager instance
_personality_manager = None

def get_personality_manager() -> NPCPersonalityManager:
    """Get the global personality manager instance (singleton)"""
    global _personality_manager
    if _personality_manager is None:
        _personality_manager = NPCPersonalityManager()
    return _personality_manager

# Convenience functions
def get_npc_personality(name: str) -> NPCPersonality:
    """Get personality for an NPC by name"""
    return get_personality_manager().get_personality(name)

def create_random_npc_data(x: int, y: int, movement_style: Optional[str] = None) -> Tuple[str, NPCPersonality]:
    """Create random NPC data"""
    return get_personality_manager().create_random_npc(x, y, movement_style)

def get_all_npc_names() -> List[str]:
    """Get all available NPC names"""
    return get_personality_manager().get_personality_names()

def add_custom_npc(name: str, **kwargs) -> NPCPersonality:
    """Add a custom NPC personality"""
    return get_personality_manager().create_custom_npc(name, **kwargs)
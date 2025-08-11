"""
AI Command System for handling player requests to NPCs
"""
import re
from typing import List, Optional, Tuple


class AICommandProcessor:
    """Processes AI commands from chat messages"""
    
    def __init__(self):
        self.follow_commands = [
            r"follow me",
            r"come with me",
            r"follow you",
            r"come along",
            r"join me",
            r"accompany me",
            r"follow",
            r"come",
            r"let's go",
            r"walk with me"
        ]
        
        self.stop_following_commands = [
            r"stop following",
            r"don't follow",
            r"stay here",
            r"wait here",
            r"leave me alone",
            r"stop",
            r"wait",
            r"stay",
            r"don't come",
            r"go away"
        ]
        
        self.rest_commands = [
            r"take a rest",
            r"get some rest",
            r"sit down",
            r"relax",
            r"rest",
            r"take a break",
            r"have a seat",
            r"sit",
            r"rest up",
            r"take it easy"
        ]
    
    def process_message(self, message: str, npc_obedience: int) -> Optional[Tuple[str, float]]:
        """
        Process a message for AI commands
        
        Args:
            message: The message to process
            npc_obedience: NPC's obedience level (1-5)
        
        Returns:
            Tuple of (command_type, success_probability) or None if no command
        """
        message_lower = message.lower()
        
        # Check for follow commands
        for pattern in self.follow_commands:
            if re.search(pattern, message_lower):
                success_prob = self._calculate_success_probability(npc_obedience, "follow")
                return ("follow", success_prob)
        
        # Check for stop following commands
        for pattern in self.stop_following_commands:
            if re.search(pattern, message_lower):
                success_prob = self._calculate_success_probability(npc_obedience, "stop_follow")
                return ("stop_follow", success_prob)
        
        # Check for rest commands
        for pattern in self.rest_commands:
            if re.search(pattern, message_lower):
                success_prob = self._calculate_success_probability(npc_obedience, "rest")
                return ("rest", success_prob)
        
        return None
    
    def _calculate_success_probability(self, obedience: int, command_type: str) -> float:
        """
        Calculate the probability of command success based on obedience
        
        Args:
            obedience: NPC's obedience level (1-5)
            command_type: Type of command being issued
        
        Returns:
            Probability of success (0.0 to 1.0)
        """
        base_probability = obedience / 5.0  # Convert obedience to 0-1 scale
        
        # Adjust based on command type
        if command_type == "follow":
            # Following is moderately difficult
            return base_probability * 0.8
        elif command_type == "stop_follow":
            # Stopping following is easier
            return base_probability * 1.2
        elif command_type == "rest":
            # Resting is natural behavior
            return base_probability * 1.0
        
        return base_probability
    
    def generate_response(self, command_type: str, success: bool, npc_name: str) -> str:
        """
        Generate an appropriate response based on command success
        
        Args:
            command_type: Type of command that was issued
            success: Whether the command was successful
            npc_name: Name of the NPC
        
        Returns:
            Response message
        """
        import random
        
        if command_type == "follow":
            if success:
                responses = [
                    f"Sure, I'll follow you!",
                    f"Alright, I'm coming with you.",
                    f"Lead the way!",
                    f"Okay, I'll tag along.",
                    f"Sure thing, I'll follow you."
                ]
                return random.choice(responses)
            else:
                responses = [
                    f"Sorry, I have other things to do right now.",
                    f"I'd rather stay here for now.",
                    f"Maybe later, I'm busy.",
                    f"I should probably stay put.",
                    f"Not right now, sorry."
                ]
                return random.choice(responses)
        
        elif command_type == "stop_follow":
            if success:
                responses = [
                    f"Alright, I'll stay here.",
                    f"Okay, I'll wait here.",
                    f"Sure, I'll stop following.",
                    f"Got it, I'll stay put.",
                    f"Alright, I'll wait for you here."
                ]
                return random.choice(responses)
            else:
                responses = [
                    f"I wasn't following you anyway.",
                    f"I'm already staying here.",
                    f"I'm not following you.",
                    f"I'm already in place.",
                    f"I'm staying here already."
                ]
                return random.choice(responses)
        
        elif command_type == "rest":
            if success:
                responses = [
                    f"Thanks, I could use a rest.",
                    f"Good idea, I'm feeling tired.",
                    f"Sure, I'll take a break.",
                    f"Thanks, I need to sit down.",
                    f"Good thinking, I could use some rest."
                ]
                return random.choice(responses)
            else:
                responses = [
                    f"I'm not tired right now.",
                    f"I feel pretty energetic actually.",
                    f"I don't need to rest yet.",
                    f"I'm good for now.",
                    f"I'm not feeling tired."
                ]
                return random.choice(responses)
        
        return "I'm not sure what you mean."


class NPCCommandHandler:
    """Handles executing commands on NPCs"""
    
    def __init__(self):
        self.command_processor = AICommandProcessor()
    
    def handle_player_message(self, message: str, npc) -> Optional[str]:
        """
        Handle a player message directed at an NPC
        
        Args:
            message: The player's message
            npc: The NPC to command
        
        Returns:
            NPC's response message or None if no command
        """
        # Process the message for commands
        command_result = self.command_processor.process_message(message, npc.obedience)
        
        if command_result is None:
            return None
        
        command_type, success_probability = command_result
        
        # Determine if command succeeds
        import random
        success = random.random() < success_probability
        
        # Execute the command
        self._execute_command(command_type, success, npc)
        
        # Generate response
        return self.command_processor.generate_response(command_type, success, npc.name)
    
    # TODO！ - Problem is here
    def _execute_command(self, command_type: str, success: bool, npc):
        """Execute a command on an NPC"""
        if not success:
            return
        
        if command_type == "follow":
            npc.behavior.start_following()
            print(f"{npc.name} started following the player")
        
        elif command_type == "stop_follow":
            npc.behavior.stop_following()
            print(f"{npc.name} stopped following the player")
        
        elif command_type == "rest":
            # This will trigger the NPC to seek a chair
            npc.behavior.tiredness = min(npc.behavior.tiredness, 30)  # Make them tired
            print(f"{npc.name} feels tired and will seek rest")
    
    def is_command_message(self, message: str) -> bool:
        """Check if a message contains a command without executing it"""
        return self.command_processor.process_message(message, 1) is not None 
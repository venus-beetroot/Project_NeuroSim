import pygame
import random
import math
from functions import app, ai
from entities.player import Player
from entities.npc import NPC

class CommandProcessor:
    """
    Processes raw player text, asks the AI to classify intent, and executes commands.
    Use process_input(npc, player_input, chat_callback) where chat_callback(msg) prints to UI once.
    """

    @staticmethod
    def _ask_ai_for_command(player_input, npc_name, npc_personality):
        """Use AI to interpret command and decide if NPC should obey based on personality"""
        from functions.ai import get_ai_response
        
        # Get NPC obedience level
        from entities.npc import NPCDialogue
        npc_data = NPCDialogue.get_dialogue(npc_name)
        obedience = npc_data.get("obedience", 3)
        
        prompt = f"""You are {npc_name}, an NPC in a game world. A player has given you a request.

    Character: {npc_name}
    Personality: {npc_personality}
    Obedience Level: {obedience}/5 (1=rebellious, 5=very obedient)

    Player request: "{player_input}"

    IMPORTANT: This is a NEW command that should override any current activity.

    Analyze the request and respond with a JSON object containing:
    {{
        "understands": true/false,
        "will_comply": true/false, 
        "action_type": "follow|move|activity|social|building|stop|none",
        "specific_action": "detailed action to perform",
        "target": "what/where the action targets",
        "location_type": "building|landmark|direction|relative|none",
        "search_terms": ["keywords", "to", "find", "location"],
        "response": "your natural conversational response",
        "parameters": {{"duration": 300, "priority": "high"}}
    }}

    For location_type:
    - "building": Looking for a specific building (store, house, office, etc.)
    - "landmark": Named location (center, park, plaza, etc.)  
    - "direction": Cardinal direction (north, south, east, west)
    - "relative": Relative to something (near player, away from here, etc.)
    - "none": No specific location

    For search_terms, extract keywords that would help identify the location:
    - "go to the red building" → ["red", "building"]
    - "meet me at the coffee shop" → ["coffee", "shop", "cafe"]
    - "head to the store" → ["store", "shop", "market"]
    - "go north" → ["north"]
    - "go home" → ["home", "hangout"]

    Consider your personality and obedience level when deciding whether to comply."""

        try:
            response = get_ai_response(prompt)
            import json
            return json.loads(response.strip())
        except Exception as e:
            print(f"AI command parsing error: {e}")
            return {
                "understands": True,
                "will_comply": obedience >= 3,
                "action_type": "none",
                "specific_action": "acknowledge",
                "target": "player",
                "location_type": "none",
                "search_terms": [],
                "response": "I'm not sure what you mean.",
                "parameters": {}
            }

    @staticmethod
    def process_input(npc: NPC, player_input: str, chat_callback=None, player=None, buildings=None):
        """Process player input and execute appropriate NPC behavior"""
        
        CommandProcessor._interrupt_current_behavior(npc)
        
        decision = CommandProcessor._ask_ai_for_command(player_input, npc.name, npc.dialogue)
        
        if chat_callback and decision.get("response"):
            chat_callback(decision["response"])
        
        if decision.get("will_comply", False):
            # Pass all AI decision data as parameters
            parameters = decision.get("parameters", {})
            parameters.update({
                "buildings": buildings,
                "location_type": decision.get("location_type", "none"),
                "search_terms": decision.get("search_terms", [])
            })
            
            CommandProcessor._execute_npc_action(
                npc, 
                decision.get("action_type", "none"),
                decision.get("specific_action", ""),
                decision.get("target", ""),
                parameters,
                player
            )
        
        return decision

    @staticmethod
    def _interrupt_current_behavior(npc):
        """Stop all current NPC behaviors before executing new command"""
        
        # Stop following
        npc.behavior.stop_following()
        
        # Stop furniture use
        npc.behavior.force_stop_furniture_use()
        
        # Clear custom animation states
        npc.is_dancing = False
        npc.is_waving = False
        npc.is_hugging = False
        
        # Clear building seeking flags
        npc._seeking_building = False
        npc._target_building_type = None
        
        # Reset movement target to current position (stops movement)
        npc.movement.target_x = npc.rect.centerx
        npc.movement.target_y = npc.rect.centery
        
        # Reset movement timer to allow immediate new movement
        npc.movement.movement_timer = 0
        npc.movement.movement_delay = 30  # Short delay before new movement
        
        # Clear any player interaction flags
        npc.is_stopped_by_player = False
        
        # Reset to idle state
        npc.state = "idle"
        
        # Allow movement again
        npc._cannot_move = False
        
        print(f"Interrupted {npc.name}'s current behavior for new command")

    @staticmethod
    def _execute_npc_action(npc, action_type, specific_action, target, parameters, player):
        """Execute the action based on AI decision"""
        
        if action_type != "activity" or "sit" not in specific_action.lower():
            npc._cannot_move = False
        
        if action_type == "follow":
            if player:
                npc.behavior.start_following(player)
        
        elif action_type == "move":
            CommandProcessor._handle_movement(npc, target, parameters)
        
        elif action_type == "activity":
            CommandProcessor._handle_activity(npc, specific_action, parameters)
        
        elif action_type == "social":
            CommandProcessor._handle_social(npc, specific_action, player, parameters)
        
        elif action_type == "building":
            CommandProcessor._handle_building(npc, specific_action, target)
        
        elif action_type == "stop":
            pass

    @staticmethod
    def _handle_movement(npc, target, parameters):
        """Handle movement commands with AI-guided pathfinding"""
        buildings = parameters.get("buildings")
        location_type = parameters.get("location_type", "none")
        search_terms = parameters.get("search_terms", [])
        
        if location_type != "none" and search_terms:
            # Try AI-guided pathfinding
            if npc.movement.find_path_to_location(location_type, search_terms, buildings):
                print(f"{npc.name} pathfinding using terms: {search_terms}")
            else:
                print(f"{npc.name} couldn't find location using '{search_terms}', moving randomly")
                # Fallback to random movement
                npc.movement.target_x = npc.rect.centerx + random.randint(-300, 300)
                npc.movement.target_y = npc.rect.centery + random.randint(-300, 300)
        else:
            # Random movement for unclear commands
            npc.movement.target_x = npc.rect.centerx + random.randint(-300, 300)
            npc.movement.target_y = npc.rect.centery + random.randint(-300, 300)

    @staticmethod
    def _handle_activity(npc, action, parameters):
        """Handle activity commands"""
        if "sit" in action.lower() or "rest" in action.lower():
            npc.behavior.tiredness = max(npc.behavior.exhaustion_threshold + 1, npc.behavior.tiredness)
        elif "dance" in action.lower():
            npc.is_dancing = True
            npc.dance_timer = parameters.get("duration", 300)
            npc.state = "dance" if "dance" in npc.animations else "idle"
        elif "wave" in action.lower():
            npc.is_waving = True
            npc.wave_timer = parameters.get("duration", 60)

    @staticmethod
    def _handle_social(npc, action, player, parameters):
        """Handle social commands"""
        if "hug" in action.lower() and player:
            npc.movement.target_x = player.rect.centerx
            npc.movement.target_y = player.rect.centery
            npc.is_hugging = True
            npc.hug_timer = parameters.get("duration", 120)
            npc.behavior.start_following(player)  # Follow for hug
        elif "look" in action.lower() and player:
            npc._face_player(player)

    @staticmethod
    def _handle_building(npc, action, target):
        """Handle building-related commands"""
        if "enter" in action.lower():
            npc._target_building_type = target
            npc._seeking_building = True
        elif "exit" in action.lower() and npc.building_state.is_inside_building:
            npc.building_state.try_exit_building(npc)

    @staticmethod
    def _handle_stop_all(npc):
        """Stop all NPC activities"""
        npc.behavior.stop_following()
        npc.behavior.force_stop_furniture_use()
        npc.is_dancing = False
        npc.is_waving = False
        npc.is_hugging = False
        npc.movement.target_x = npc.rect.centerx
        npc.movement.target_y = npc.rect.centery
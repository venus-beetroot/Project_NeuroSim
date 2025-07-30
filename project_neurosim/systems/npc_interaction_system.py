import pygame
import random
import math
import threading
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from entities.npc import NPC

# Import AI functions (with fallbacks)
try:
    from functions.ai import get_ai_response
except ImportError:
    def get_ai_response(prompt):
        # Fallback responses if AI not available
        responses = [
            "That's interesting!",
            "I see what you mean.",
            "Tell me more about that.",
            "That sounds nice.",
            "I agree with you."
        ]
        return random.choice(responses)

try:
    from ai.npc_personalities import get_personality_manager
except ImportError:
    # Fallback if personality system not available
    class FallbackPersonality:
        def __init__(self, name):
            self.name = name
            self.interaction_tendency = 0.5
            self.personality_prompt = f"You are {name}, a friendly NPC."
    
    class FallbackPersonalityManager:
        def get_personality(self, name):
            return FallbackPersonality(name)
    
    def get_personality_manager():
        return FallbackPersonalityManager()


@dataclass
class ConversationState:
    """Represents the state of an NPC-to-NPC conversation"""
    npc1: 'NPC'
    npc2: 'NPC'
    start_time: int
    duration: int
    current_speaker: Optional['NPC'] = None
    conversation_topic: str = ""
    conversation_history: List[Tuple[str, str]] = None
    is_active: bool = True
    next_response_time: Optional[float] = None
    conversation_stage: str = "starting"
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []


class NPCInteractionSystem:
    """Manages NPC-to-NPC interactions and conversations - FIXED VERSION"""
    
    def __init__(self):
        self.conversations: List[ConversationState] = []
        self.interaction_radius = 100  # Distance for NPCs to start talking
        self.conversation_duration_range = (1800, 3600)  # 30-60 seconds at 60 FPS
        self.speech_bubble_duration = 360  # 6 seconds at 60 FPS
        self.ai_response_threads: Dict[str, threading.Thread] = {}
        self.ai_responses: Dict[str, str] = {}
        self.conversation_chance = 0.08  # 8% chance per frame when NPCs are close
        
        print("DEBUG: NPCInteractionSystem initialized")
        
    def update(self, npcs: List['NPC'], current_time: int):
        """Update all NPC interactions - FIXED VERSION"""
        # Update existing conversations
        self._update_conversations(current_time)
        
        # Check for new potential interactions
        self._check_for_new_interactions(npcs, current_time)
        
        # Update AI response threads
        self._update_ai_responses()
    
    def _update_conversations(self, current_time: int):
        """Update existing conversations - IMPROVED"""
        active_conversations = []
        
        for conv in self.conversations:
            if not conv.is_active:
                continue
                
            # Check if conversation should end
            if current_time - conv.start_time > conv.duration:
                self._end_conversation(conv)
                continue
            
            # Check if NPCs are still close enough
            distance = self._get_distance_between_npcs(conv.npc1, conv.npc2)
            if distance > self.interaction_radius * 1.5:  # Allow some buffer
                print(f"DEBUG: Ending conversation - NPCs too far apart: {distance}")
                self._end_conversation(conv)
                continue
            
            # CRITICAL: Maintain conversation state
            self._maintain_conversation_state(conv)
            
            active_conversations.append(conv)
            
            # Check if it's time for the next response
            if conv.next_response_time and time.time() >= conv.next_response_time:
                conv.next_response_time = None
                # Generate next response
                other_npc = conv.npc2 if conv.current_speaker == conv.npc1 else conv.npc1
                self._generate_ai_response(conv, conv.current_speaker, other_npc)
        
        self.conversations = active_conversations
    
    def _maintain_conversation_state(self, conversation: ConversationState):
        """Maintain conversation state - FIXED"""
        # Keep both NPCs stopped
        conversation.npc1.is_stopped_by_player = True
        conversation.npc2.is_stopped_by_player = True
        
        # Set state to idle
        conversation.npc1.state = "idle"
        conversation.npc2.state = "idle"
        
        # Mark NPCs as being in conversation
        conversation.npc1._in_npc_conversation = True
        conversation.npc2._in_npc_conversation = True
        conversation.npc1._conversation_partner = conversation.npc2
        conversation.npc2._conversation_partner = conversation.npc1
        
        # Make them face each other
        self._make_npcs_face_each_other(conversation.npc1, conversation.npc2)
    
    def _check_for_new_interactions(self, npcs: List['NPC'], current_time: int):
        """Check for new potential NPC interactions - IMPROVED"""
        for i, npc1 in enumerate(npcs):
            # Skip if NPC is unavailable
            if not self._is_npc_available(npc1):
                continue
                
            for j, npc2 in enumerate(npcs[i+1:], i+1):
                if not self._is_npc_available(npc2):
                    continue
                
                # Skip if they're already in a conversation
                if self._are_npcs_in_conversation(npc1, npc2):
                    continue
                
                # Check distance
                distance = self._get_distance_between_npcs(npc1, npc2)
                if distance <= self.interaction_radius:
                    # Check if they should start talking
                    if self._should_start_conversation(npc1, npc2):
                        print(f"DEBUG: Starting conversation between {npc1.name} and {npc2.name}")
                        self._start_conversation(npc1, npc2, current_time)
    
    def _is_npc_available(self, npc):
        """Check if NPC is available for conversation - IMPROVED"""
        # Not available if already in conversation
        if hasattr(npc, '_in_npc_conversation') and npc._in_npc_conversation:
            return False
        
        # Not available if interacting with player
        if hasattr(npc, '_stopped_by_player_interaction') and npc._stopped_by_player_interaction:
            return False
        
        # Not available if inside building (for now)
        if npc.building_state.is_inside_building:
            return False
        
        return True
    
    def _should_start_conversation(self, npc1: 'NPC', npc2: 'NPC') -> bool:
        """Determine if two NPCs should start a conversation - IMPROVED"""
        try:
            personality_manager = get_personality_manager()
            p1 = personality_manager.get_personality(npc1.name)
            p2 = personality_manager.get_personality(npc2.name)
            base_chance = (p1.interaction_tendency + p2.interaction_tendency) / 2
        except:
            base_chance = 0.5
        
        # Reduce chance if they're moving fast
        if npc1.state == "run" or npc2.state == "run":
            base_chance *= 0.3
        
        final_chance = base_chance * self.conversation_chance
        return random.random() < final_chance
    
    def _start_conversation(self, npc1: 'NPC', npc2: 'NPC', current_time: int):
        """Start a new conversation between two NPCs - FIXED"""
        print(f"Starting conversation between {npc1.name} and {npc2.name}")
        
        # Use NPC's built-in conversation methods if available
        if hasattr(npc1, 'start_conversation_with'):
            npc1.start_conversation_with(npc2)
        else:
            # Fallback: manual setup
            npc1.is_stopped_by_player = True
            npc2.is_stopped_by_player = True
            npc1.state = "idle"
            npc2.state = "idle"
            npc1._in_npc_conversation = True
            npc2._in_npc_conversation = True
        
        # Make them face each other
        self._make_npcs_face_each_other(npc1, npc2)
        
        # Create conversation
        conversation = ConversationState(
            npc1=npc1,
            npc2=npc2,
            start_time=current_time,
            duration=random.randint(*self.conversation_duration_range),
            conversation_stage="starting"
        )
        
        # Generate conversation topic
        conversation.conversation_topic = self._generate_conversation_topic(npc1, npc2)
        
        # Pick random starter
        conversation.current_speaker = random.choice([npc1, npc2])
        other_npc = npc2 if conversation.current_speaker == npc1 else npc1
        
        # Start first response immediately
        self._generate_ai_response(conversation, conversation.current_speaker, other_npc)
        
        self.conversations.append(conversation)
        print(f"Conversation created: Topic='{conversation.conversation_topic}'")
    
    def _generate_conversation_topic(self, npc1: 'NPC', npc2: 'NPC') -> str:
        """Generate a conversation topic"""
        topics = [
            "the weather today",
            "recent events in town", 
            "their daily activities",
            "shared interests",
            "the local community",
            "future plans",
            "technology and progress",
            "adventures and exploration"
        ]
        return random.choice(topics)
    
    def _generate_ai_response(self, conversation: ConversationState, speaker: 'NPC', listener: 'NPC'):
        """Generate AI response for conversation - IMPROVED"""
        try:
            personality_manager = get_personality_manager()
            speaker_personality = personality_manager.get_personality(speaker.name)
            listener_personality = personality_manager.get_personality(listener.name)
            speaker_prompt = speaker_personality.personality_prompt
            listener_prompt = listener_personality.personality_prompt
        except:
            speaker_prompt = f"You are {speaker.name}, a friendly NPC."
            listener_prompt = f"{listener.name} is a friendly NPC."
        
        # Create context
        if len(conversation.conversation_history) == 0:
            # First message
            context = f"""
You are {speaker.name}, starting a casual conversation with {listener.name} about {conversation.conversation_topic}.

Your personality: {speaker_prompt}
{listener.name}'s personality: {listener_prompt}

Generate a friendly greeting and conversation starter about {conversation.conversation_topic}. Keep it brief (1-2 short sentences).
"""
        else:
            # Continuing conversation
            context = f"""
You are {speaker.name}, having a casual conversation with {listener.name} about {conversation.conversation_topic}.

Your personality: {speaker_prompt}
{listener.name}'s personality: {listener_prompt}

Previous conversation:
{self._format_conversation_history(conversation.conversation_history)}

Generate a natural, brief response (1-2 short sentences) that continues the conversation.
"""
        
        # Generate response in thread
        thread_key = f"{speaker.name}_{listener.name}_{conversation.start_time}_{len(conversation.conversation_history)}"
        if thread_key not in self.ai_response_threads:
            thread = threading.Thread(
                target=self._ai_response_worker,
                args=(thread_key, context, speaker.name)
            )
            thread.daemon = True
            thread.start()
            self.ai_response_threads[thread_key] = thread
            print(f"Started AI response generation for {speaker.name}")
    
    def _ai_response_worker(self, thread_key: str, context: str, speaker_name: str):
        """Worker thread for AI response generation - IMPROVED"""
        try:
            print(f"Generating AI response for {speaker_name}")
            response = get_ai_response(context)
            
            # Clean up response
            response = response.strip()
            
            # Remove quotes if AI added them
            if response.startswith('"') and response.endswith('"'):
                response = response[1:-1]
            
            # Limit to first 2 sentences
            sentences = response.split('. ')
            if len(sentences) > 2:
                response = '. '.join(sentences[:2]) + '.'
            elif not response.endswith(('.', '!', '?')):
                response += '.'
            
            # Ensure reasonable length
            if len(response) > 120:
                response = response[:117] + '...'
            
            self.ai_responses[thread_key] = response
            print(f"AI response generated for {speaker_name}: '{response}'")
            
        except Exception as e:
            print(f"Error generating AI response for {speaker_name}: {e}")
            # Fallback responses
            fallbacks = [
                "That's interesting!",
                "I see what you mean.",
                "Tell me more.",
                "That sounds great!",
                "I agree with you."
            ]
            self.ai_responses[thread_key] = random.choice(fallbacks)
    
    def _update_ai_responses(self):
        """Update AI responses and handle conversation flow - FIXED"""
        completed_threads = []
        
        for thread_key, thread in self.ai_response_threads.items():
            if not thread.is_alive():
                completed_threads.append(thread_key)
                
                if thread_key in self.ai_responses:
                    response = self.ai_responses[thread_key]
                    
                    # Parse thread key
                    parts = thread_key.split('_')
                    if len(parts) >= 4:
                        speaker_name = parts[0]
                        listener_name = parts[1] 
                        conv_start_time = int(parts[2])
                        
                        # Find matching conversation
                        for conv in self.conversations:
                            if (conv.is_active and 
                                conv.start_time == conv_start_time and 
                                conv.current_speaker and
                                conv.current_speaker.name == speaker_name):
                                
                                print(f"Processing response from {speaker_name}: '{response}'")
                                
                                # Add to conversation history
                                conv.conversation_history.append((speaker_name, response))
                                
                                # Set speech bubble using the fixed method
                                conv.current_speaker.interaction.set_speech_bubble(
                                    response, 
                                    self.speech_bubble_duration
                                )
                                
                                # Switch speaker
                                conv.current_speaker = conv.npc2 if conv.current_speaker == conv.npc1 else conv.npc1
                                
                                # Schedule next response
                                delay = random.uniform(3.0, 6.0)
                                conv.next_response_time = time.time() + delay
                                
                                print(f"Next speaker: {conv.current_speaker.name} (in {delay:.1f}s)")
                                break
        
        # Clean up completed threads
        for thread_key in completed_threads:
            if thread_key in self.ai_response_threads:
                del self.ai_response_threads[thread_key]
            if thread_key in self.ai_responses:
                del self.ai_responses[thread_key]
    
    def _end_conversation(self, conversation: ConversationState):
        """End a conversation between NPCs - FIXED"""
        print(f"Ending conversation between {conversation.npc1.name} and {conversation.npc2.name}")
        
        conversation.is_active = False
        
        # Use NPC's built-in end method if available
        if hasattr(conversation.npc1, 'end_conversation'):
            conversation.npc1.end_conversation()
        else:
            # Fallback: manual cleanup
            conversation.npc1._in_npc_conversation = False
            conversation.npc2._in_npc_conversation = False
            conversation.npc1._conversation_partner = None
            conversation.npc2._conversation_partner = None
            conversation.npc1.is_stopped_by_player = False
            conversation.npc2.is_stopped_by_player = False
            conversation.npc1.interaction.show_speech_bubble = False
            conversation.npc2.interaction.show_speech_bubble = False
            conversation.npc1.interaction.bubble_text = conversation.npc1.bubble_dialogue
            conversation.npc2.interaction.bubble_text = conversation.npc2.bubble_dialogue
    
    def _are_npcs_in_conversation(self, npc1: 'NPC', npc2: 'NPC') -> bool:
        """Check if two NPCs are already in a conversation"""
        for conv in self.conversations:
            if conv.is_active and (
                (conv.npc1 == npc1 and conv.npc2 == npc2) or
                (conv.npc1 == npc2 and conv.npc2 == npc1)
            ):
                return True
        return False
    
    def _get_distance_between_npcs(self, npc1: 'NPC', npc2: 'NPC') -> float:
        """Calculate distance between two NPCs"""
        if hasattr(npc1, '_get_distance_to_npc'):
            return npc1._get_distance_to_npc(npc2)
        else:
            # Fallback calculation
            dx = npc1.rect.centerx - npc2.rect.centerx
            dy = npc1.rect.centery - npc2.rect.centery
            return math.sqrt(dx * dx + dy * dy)
    
    def _make_npcs_face_each_other(self, npc1: 'NPC', npc2: 'NPC'):
        """Make two NPCs face each other"""
        if hasattr(npc1, '_face_npc'):
            npc1._face_npc(npc2)
            npc2._face_npc(npc1)
        else:
            # Fallback
            npc1.facing_left = npc2.rect.centerx < npc1.rect.centerx
            npc2.facing_left = npc1.rect.centerx < npc2.rect.centerx
    
    def _format_conversation_history(self, history: List[Tuple[str, str]]) -> str:
        """Format conversation history for AI context"""
        if not history:
            return "This is the start of the conversation."
        
        formatted = []
        for speaker, message in history[-3:]:  # Last 3 exchanges
            formatted.append(f"{speaker}: {message}")
        return "\n".join(formatted)
    
    def get_active_conversations(self) -> List[ConversationState]:
        """Get all active conversations"""
        return [conv for conv in self.conversations if conv.is_active]
    
    def debug_conversations(self):
        """Debug active conversations"""
        print(f"=== CONVERSATION DEBUG ===")
        print(f"Active conversations: {len([c for c in self.conversations if c.is_active])}")
        
        for i, conv in enumerate(self.conversations):
            if conv.is_active:
                print(f"  Conversation {i}:")
                print(f"    NPCs: {conv.npc1.name} <-> {conv.npc2.name}")
                print(f"    Topic: {conv.conversation_topic}")  
                print(f"    Current speaker: {conv.current_speaker.name if conv.current_speaker else 'None'}")
                print(f"    History entries: {len(conv.conversation_history)}")
                print(f"    Bubble states: {conv.npc1.name}={conv.npc1.interaction.show_speech_bubble}, {conv.npc2.name}={conv.npc2.interaction.show_speech_bubble}")
                
                distance = self._get_distance_between_npcs(conv.npc1, conv.npc2)
                print(f"    Distance: {distance:.1f}")
        
        print(f"AI threads active: {len(self.ai_response_threads)}")
        print(f"Pending responses: {len(self.ai_responses)}")
        print("=========================")

import pygame
import math
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from config.settings import (
    TIP_DISPLAY_DURATION, TIP_FADE_IN_DURATION, TIP_FADE_OUT_DURATION,
    TIP_POSITION_Y, TIP_MAX_WIDTH, TIP_PADDING, TIP_DURATIONS,
    TIP_TUTORIAL_AUTO_START, TIP_SETTINGS_DELAY, TIP_DEBUG_DELAY
)


class TutorialState(Enum):
    """Tutorial progression states"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class TipDefinition:
    """Definition of a single tip"""
    text: str
    trigger: str
    priority: int
    duration: int
    conditions: Optional[List[str]] = None
    repeatable: bool = False
    

@dataclass
class TutorialStep:
    """Definition of a tutorial step"""
    text: str
    duration: int
    condition: Optional[str] = None
    auto_advance: bool = True


class GameStateTracker:
    """Tracks game state for tip and tutorial system"""
    
    def __init__(self):
        """Initialize game state tracking"""
        self.reset()
    
    def reset(self):
        """Reset all tracked state"""
        self.start_time = pygame.time.get_ticks()
        self.player_moved = False
        self.has_talked_to_npc = False
        self.has_entered_building = False
        self.has_exited_building = False
        self.hit_chat_cooldown = False
        self.opened_settings = False
        self.used_debug_mode = False
    
    def update_from_game_state(self, game_state: Dict[str, Any]):
        """Update tracked state from game state dictionary"""
        self.player_moved = game_state.get("player_moved", self.player_moved)
        self.has_talked_to_npc = game_state.get("talked_to_npc", self.has_talked_to_npc)
        self.hit_chat_cooldown = game_state.get("hit_chat_cooldown", self.hit_chat_cooldown)
        
        # Track building interactions
        if game_state.get("inside_building", False) and not self.has_entered_building:
            self.has_entered_building = True
        
        # Add more state tracking as needed
    
    def get_play_time(self) -> int:
        """Get current play time in milliseconds"""
        return pygame.time.get_ticks() - self.start_time


class TipManager:
    """Manages game tips and tutorials with animations and progress tracking"""
    
    def __init__(self, font_small: pygame.font.Font, font_chat: pygame.font.Font):
        """
        Initialize the tip manager
        
        Args:
            font_small: Small font for tip icons
            font_chat: Chat font for tip text
        """
        self.font_small = font_small
        self.font_chat = font_chat
        
        # Tip display state
        self.current_tip = None
        self.tip_start_time = 0
        self.tip_duration = TIP_DISPLAY_DURATION
        self.tips_shown: Set[str] = set()
        self.tip_queue: List[str] = []
        
        # Tutorial system
        self.tutorial_state = TutorialState.INACTIVE
        self.tutorial_step = 0
        self.tutorial_steps: List[TutorialStep] = []
        
        # Game state tracking
        self.state_tracker = GameStateTracker()
        
        # Initialize tip definitions and tutorial
        self._initialize_tips()
        self._initialize_tutorial()
    
    def _initialize_tips(self):
        """Initialize all tip definitions"""
        self.all_tips: Dict[str, TipDefinition] = {
            "movement": TipDefinition(
                text="Use WASD keys to move around. Hold Shift to run faster!",
                trigger="first_move",
                priority=1,
                duration=TIP_DURATIONS.get("movement", TIP_DISPLAY_DURATION)
            ),
            "interact_npc": TipDefinition(
                text="Press F near NPCs to start a conversation!",
                trigger="near_npc",
                priority=2,
                duration=TIP_DURATIONS.get("interact_npc", TIP_DISPLAY_DURATION)
            ),
            "enter_building": TipDefinition(
                text="Press E near buildings to enter them!",
                trigger="near_building",
                priority=3,
                duration=TIP_DURATIONS.get("enter_building", TIP_DISPLAY_DURATION)
            ),
            "exit_building": TipDefinition(
                text="Press E in the highlighted area to exit the building!",
                trigger="inside_building",
                priority=4,
                duration=TIP_DURATIONS.get("exit_building", TIP_DISPLAY_DURATION)
            ),
            "debug_mode": TipDefinition(
                text="Press F1 to toggle debug mode and see building hitboxes!",
                trigger="played_5min",
                priority=5,
                duration=TIP_DURATIONS.get("debug_mode", TIP_DISPLAY_DURATION)
            ),
            "settings": TipDefinition(
                text="Press Escape to access settings or pause the game!",
                trigger="played_2min",
                priority=6,
                duration=TIP_DURATIONS.get("settings", TIP_DISPLAY_DURATION)
            ),
            "chat_cooldown": TipDefinition(
                text="Wait for the cooldown before sending another message to NPCs!",
                trigger="chat_cooldown",
                priority=7,
                duration=TIP_DURATIONS.get("chat_cooldown", TIP_DISPLAY_DURATION)
            ),
            "arrows": TipDefinition(
                text="Follow the colored arrows to find different buildings!",
                trigger="far_from_buildings",
                priority=8,
                duration=TIP_DURATIONS.get("arrows", TIP_DISPLAY_DURATION)
            )
        }
    
    def _initialize_tutorial(self):
        """Initialize tutorial step sequence"""
        self.tutorial_steps = [
            TutorialStep(
                text="Welcome to Project NeuroSim! Let's learn the basics.",
                duration=3000,
                condition=None
            ),
            TutorialStep(
                text="Use WASD keys to move your character around the world.",
                duration=4000,
                condition="wait_for_movement"
            ),
            TutorialStep(
                text="Great! You can also hold Shift to run faster.",
                duration=3000,
                condition=None
            ),
            TutorialStep(
                text="See those NPCs? Walk up to one and press Enter to chat!",
                duration=4000,
                condition="wait_for_npc_interaction"
            ),
            TutorialStep(
                text="Excellent! You can explore buildings by pressing E near them.",
                duration=4000,
                condition=None
            ),
            TutorialStep(
                text="Follow the colored arrows to find different buildings around town.",
                duration=4000,
                condition=None
            ),
            TutorialStep(
                text="That's the basics! Press Escape for settings. Have fun exploring!",
                duration=5000,
                condition=None
            )
        ]
    
    def start_tutorial(self):
        """Start the tutorial sequence"""
        if self.tutorial_state == TutorialState.COMPLETED:
            return
        
        self.tutorial_state = TutorialState.ACTIVE
        self.tutorial_step = 0
        self.state_tracker.reset()
        self._show_current_tutorial_step()
    
    def skip_tutorial(self):
        """Skip the tutorial"""
        self.tutorial_state = TutorialState.SKIPPED
        self.current_tip = None
    
    def _show_current_tutorial_step(self):
        """Display the current tutorial step"""
        if (self.tutorial_state != TutorialState.ACTIVE or 
            self.tutorial_step >= len(self.tutorial_steps)):
            return
        
        step = self.tutorial_steps[self.tutorial_step]
        self.show_tip(step.text, step.duration)
    
    def _update_tutorial(self, game_state: Dict[str, Any]):
        """Update tutorial progress based on game state"""
        if (self.tutorial_state != TutorialState.ACTIVE or 
            self.tutorial_step >= len(self.tutorial_steps)):
            return
        
        current_step = self.tutorial_steps[self.tutorial_step]
        condition = current_step.condition
        
        # Check if we should advance to next step
        should_advance = False
        
        if condition is None:
            # No condition, advance when tip expires completely
            should_advance = self.current_tip is None
        elif condition == "wait_for_movement":
            should_advance = game_state.get("player_moved", False)
        elif condition == "wait_for_npc_interaction":
            should_advance = game_state.get("talked_to_npc", False)
        
        if should_advance:
            self.tutorial_step += 1
            if self.tutorial_step < len(self.tutorial_steps):
                self._show_current_tutorial_step()
            else:
                self._complete_tutorial()
    
    def _complete_tutorial(self):
        """Complete the tutorial"""
        self.tutorial_state = TutorialState.COMPLETED
        self.show_tip("Tutorial complete! Enjoy the game!", 3000)
    
    def show_tip(self, text: str, duration: Optional[int] = None):
        """
        Display a tip message
        
        Args:
            text: Tip text to display
            duration: Duration in milliseconds (uses default if None)
        """
        self.current_tip = text
        self.tip_start_time = pygame.time.get_ticks()
        self.tip_duration = duration if duration is not None else TIP_DISPLAY_DURATION
    
    def trigger_tip(self, tip_name: str, force: bool = False):
        """
        Trigger a specific tip
        
        Args:
            tip_name: Name of tip to trigger
            force: Force show even if already shown
        """
        if tip_name not in self.all_tips:
            return
        
        tip_def = self.all_tips[tip_name]
        
        # Don't show if already shown (unless forced or repeatable)
        if tip_name in self.tips_shown and not force and not tip_def.repeatable:
            return
        
        # Don't interrupt tutorial unless forced
        if self.tutorial_state == TutorialState.ACTIVE and not force:
            return
        
        # Mark as shown and display
        self.tips_shown.add(tip_name)
        self.show_tip(tip_def.text, tip_def.duration)
    
    def get_tip_alpha(self) -> int:
        """
        Calculate current alpha value for tip display with fade effects
        
        Returns:
            Alpha value (0-255)
        """
        if not self.current_tip:
            return 0
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.tip_start_time
        total_duration = self.tip_duration
        
        # Fade in phase
        if elapsed < TIP_FADE_IN_DURATION:
            fade_progress = elapsed / TIP_FADE_IN_DURATION
            return int(255 * fade_progress)
        
        # Check if we should start fading out
        if elapsed >= total_duration:
            # Fade out phase
            fade_elapsed = elapsed - total_duration
            
            if fade_elapsed >= TIP_FADE_OUT_DURATION:
                return 0  # Completely faded out
            else:
                fade_progress = fade_elapsed / TIP_FADE_OUT_DURATION
                return int(255 * (1.0 - fade_progress))
        
        # Normal display phase
        return 255
    
    def update(self, game_state: Dict[str, Any]):
        """
        Update the tip system
        
        Args:
            game_state: Current game state information
        """
        current_time = pygame.time.get_ticks()
        
        # Update game state tracker
        self.state_tracker.update_from_game_state(game_state)
        
        # Remove tip if completely faded out
        if self.current_tip and self.get_tip_alpha() == 0:
            total_tip_time = self.tip_duration + TIP_FADE_OUT_DURATION
            if current_time >= self.tip_start_time + total_tip_time:
                self.current_tip = None
        
        # Update tutorial
        self._update_tutorial(game_state)
        
        # Check for automatic tip triggers
        self._check_auto_tips(game_state, current_time)
    
    def _check_auto_tips(self, game_state: Dict[str, Any], current_time: int):
        """
        Check for automatic tip triggers based on game state
        
        Args:
            game_state: Current game state
            current_time: Current time in milliseconds
        """
        # Movement tip
        if game_state.get("player_moved") and "movement" not in self.tips_shown:
            self.trigger_tip("movement")
        
        # Near NPC tip
        if game_state.get("near_npc") and "interact_npc" not in self.tips_shown:
            self.trigger_tip("interact_npc")
        
        # Near building tip
        if game_state.get("near_building") and "enter_building" not in self.tips_shown:
            self.trigger_tip("enter_building")
        
        # Inside building tip
        if game_state.get("inside_building") and "exit_building" not in self.tips_shown:
            self.trigger_tip("exit_building")
        
        # Time-based tips
        play_time = self.state_tracker.get_play_time()
        
        if play_time > TIP_SETTINGS_DELAY and "settings" not in self.tips_shown:
            self.trigger_tip("settings")
        
        if play_time > TIP_DEBUG_DELAY and "debug_mode" not in self.tips_shown:
            self.trigger_tip("debug_mode")
        
        # Chat cooldown tip
        if game_state.get("hit_chat_cooldown") and "chat_cooldown" not in self.tips_shown:
            self.trigger_tip("chat_cooldown")
        
        # Far from buildings tip
        if game_state.get("far_from_buildings") and "arrows" not in self.tips_shown:
            self.trigger_tip("arrows")
    
    def _wrap_tip_text(self, text: str, max_width: int) -> List[str]:
        """
        Wrap tip text into multiple lines
        
        Args:
            text: Text to wrap
            max_width: Maximum width in pixels
            
        Returns:
            List of text lines
        """
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surface = self.font_chat.render(test_line, True, (255, 255, 255))
            
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Single word is too long, use it anyway
                    current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _draw_progress_bar(self, surface: pygame.Surface, box_rect: pygame.Rect, alpha: int):
        """
        Draw progress bar for tutorial steps
        
        Args:
            surface: Surface to draw on
            box_rect: Tip box rectangle
            alpha: Current alpha value
        """
        if self.tutorial_state != TutorialState.ACTIVE or not self.current_tip:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = max(0, current_time - self.tip_start_time)
        progress = min(1.0, elapsed / self.tip_duration)
        
        # Progress bar dimensions
        bar_margin = 12
        bar_height = 6
        bar_width = box_rect.width - 2 * bar_margin
        bar_x = box_rect.x + bar_margin
        bar_y = box_rect.bottom - 4 - bar_height
        
        # Progress bar colors based on progress
        if progress > 0.8:
            bar_color = (255, 50, 50, alpha)    # Red
        elif progress > 0.5:
            bar_color = (255, 165, 0, alpha)    # Orange
        else:
            bar_color = (100, 255, 100, alpha)  # Green
        
        # Draw background track
        track_surface = pygame.Surface((bar_width, bar_height))
        track_surface.set_alpha(alpha)
        track_surface.fill((50, 50, 50))
        surface.blit(track_surface, (bar_x, bar_y))
        
        # Draw progress fill
        if progress > 0:
            fill_width = int(bar_width * progress)
            fill_surface = pygame.Surface((fill_width, bar_height))
            fill_surface.set_alpha(alpha)
            fill_surface.fill(bar_color[:3])  # Remove alpha from color tuple
            surface.blit(fill_surface, (bar_x, bar_y))
    
    def draw(self, surface: pygame.Surface):
        """
        Draw the current tip with animations and effects
        
        Args:
            surface: Surface to draw on
        """
        if not self.current_tip:
            return
        
        alpha = self.get_tip_alpha()
        if alpha == 0:
            return
        
        screen_width = surface.get_width()
        
        # Wrap text for display
        max_text_width = min(TIP_MAX_WIDTH, screen_width - 40)
        lines = self._wrap_tip_text(self.current_tip, max_text_width)
        
        # Calculate dimensions
        line_height = self.font_chat.get_height()
        text_height = len(lines) * line_height + (len(lines) - 1) * 2
        
        # Icon setup
        icon_text = "TIP! "
        try:
            icon_surface = self.font_small.render(icon_text, True, (255, 255, 100))
            icon_width = icon_surface.get_width()
            icon_height = icon_surface.get_height()
        except:
            # Fallback if emoji doesn't render
            icon_surface = self.font_small.render("TIP:", True, (255, 255, 100))
            icon_width = icon_surface.get_width()
            icon_height = icon_surface.get_height()
        
        # Calculate box dimensions
        icon_padding = 10
        text_padding = 10
        icon_text_gap = 15
        progress_bar_space = 15  # Extra space for progress bar
        
        box_width = icon_padding + icon_width + icon_text_gap + max_text_width + text_padding
        box_height = max(icon_height + 10, text_height + 10) + 30 + progress_bar_space
        
        # Position at top center
        box_x = (screen_width - box_width) // 2
        box_y = TIP_POSITION_Y
        
        # Create tip surface
        tip_surface = pygame.Surface((box_width, box_height))
        tip_surface = tip_surface.convert_alpha()
        tip_surface.fill((0, 0, 0, 0))
        
        # Animated background
        time_factor = (pygame.time.get_ticks() % 2000) / 2000.0
        base_alpha = int(200 + 30 * math.sin(time_factor * math.pi * 2))
        final_alpha = int((base_alpha * alpha) / 255)
        
        # Draw background
        bg_surface = pygame.Surface((box_width, box_height))
        bg_surface.fill((20, 40, 80))
        bg_surface.set_alpha(final_alpha)
        tip_surface.blit(bg_surface, (0, 0))
        
        # Draw border
        border_surface = pygame.Surface((box_width, box_height))
        border_surface = border_surface.convert_alpha()
        border_surface.fill((0, 0, 0, 0))
        pygame.draw.rect(border_surface, (100, 150, 255), (0, 0, box_width, box_height), 3)
        border_surface.set_alpha(alpha)
        tip_surface.blit(border_surface, (0, 0))
        
        # Draw icon
        icon_surface.set_alpha(alpha)
        icon_x = icon_padding
        icon_y = (box_height - progress_bar_space - icon_height) // 2
        tip_surface.blit(icon_surface, (icon_x, icon_y))
        
        # Draw text lines
        text_start_x = icon_padding + icon_width + icon_text_gap
        text_start_y = (box_height - progress_bar_space - text_height) // 2
        
        for i, line in enumerate(lines):
            line_surface = self.font_chat.render(line, True, (255, 255, 255))
            line_surface.set_alpha(alpha)
            line_y = text_start_y + i * (line_height + 2)
            tip_surface.blit(line_surface, (text_start_x, line_y))
        
        # Draw progress bar for tutorial
        box_rect = pygame.Rect(0, 0, box_width, box_height)
        self._draw_progress_bar(tip_surface, box_rect, alpha)
        
        # Blit final tip box to screen
        surface.blit(tip_surface, (box_x, box_y))
    
    def is_tutorial_active(self) -> bool:
        """Check if tutorial is currently active"""
        return self.tutorial_state == TutorialState.ACTIVE
    
    def is_tutorial_completed(self) -> bool:
        """Check if tutorial has been completed"""
        return self.tutorial_state == TutorialState.COMPLETED
    
    def get_tutorial_progress(self) -> float:
        """Get tutorial progress as a percentage (0.0 to 1.0)"""
        if not self.tutorial_steps:
            return 1.0
        return min(1.0, self.tutorial_step / len(self.tutorial_steps))
    
    def reset_tips(self):
        """Reset all shown tips (for testing/debugging)"""
        self.tips_shown.clear()
        self.current_tip = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tip system statistics for debugging"""
        return {
            "tips_shown_count": len(self.tips_shown),
            "tips_remaining": len(self.all_tips) - len(self.tips_shown),
            "tutorial_state": self.tutorial_state.value,
            "tutorial_progress": self.get_tutorial_progress(),
            "current_tip_active": self.current_tip is not None,
            "play_time": self.state_tracker.get_play_time()
        }
"""
Debug utilities for game development and testing
Provides debugging functions for collision detection, map generation, and building systems
"""
import pygame
from typing import Dict, Any, List, Tuple, Optional
from world.map_generator import TileType


class DebugUtils:
    """Centralized debug utilities for the game"""
    
    def __init__(self, game_instance):
        """
        Initialize debug utils with reference to game instance
        
        Args:
            game_instance: Reference to the main Game class instance
        """
        self.game = game_instance
        self.debug_hitboxes_enabled = False
    
    def toggle_debug_hitboxes(self) -> bool:
        """
        Toggle hitbox visualization with enhanced debugging
        
        Returns:
            bool: Current debug hitbox state after toggle
        """
        self.debug_hitboxes_enabled = not self.debug_hitboxes_enabled
        self.game.debug_hitboxes = self.debug_hitboxes_enabled
        
        status = "ON" if self.debug_hitboxes_enabled else "OFF"
        print(f"Debug hitboxes: {status}")
        
        # Print building system info when debugging is enabled
        if self.debug_hitboxes_enabled:
            self.print_building_system_status()
        
        return self.debug_hitboxes_enabled
    
    def debug_collision_at_position(self, x: int, y: int) -> Dict[str, Any]:
        """
        Debug what's blocking the player at a specific position
        
        Args:
            x: X coordinate to check
            y: Y coordinate to check
            
        Returns:
            Dict containing debug information about the position
        """
        debug_info = {
            'position': (x, y),
            'map_bounds': None,
            'camera_bounds': None,
            'tile_info': None,
            'building_collisions': [],
            'within_bounds': {}
        }
        
        print(f"\n=== Collision Debug at ({x}, {y}) ===")
        
        # Check map bounds
        map_size = self.game.map_size
        debug_info['map_bounds'] = (map_size, map_size)
        within_map = 0 <= x < map_size and 0 <= y < map_size
        debug_info['within_bounds']['map'] = within_map
        
        print(f"Map size: {map_size}x{map_size}")
        print(f"Within map bounds: {within_map}")
        
        # Check camera bounds
        camera = self.game.camera
        if hasattr(camera, 'map_width') and hasattr(camera, 'map_height'):
            camera_bounds = (camera.map_width, camera.map_height)
            debug_info['camera_bounds'] = camera_bounds
            within_camera = 0 <= x < camera.map_width and 0 <= y < camera.map_height
            debug_info['within_bounds']['camera'] = within_camera
            
            print(f"Camera map bounds: {camera_bounds[0]}x{camera_bounds[1]}")
            print(f"Within camera bounds: {within_camera}")
        
        # Check tile grid bounds
        if hasattr(self.game, 'map_generator'):
            tile_x = x // 32  # Assuming 32 pixel tiles
            tile_y = y // 32
            map_gen = self.game.map_generator
            
            debug_info['tile_info'] = {
                'tile_position': (tile_x, tile_y),
                'grid_size': (map_gen.grid_width, map_gen.grid_height),
                'within_grid': 0 <= tile_x < map_gen.grid_width and 0 <= tile_y < map_gen.grid_height
            }
            
            print(f"Tile position: ({tile_x}, {tile_y})")
            print(f"Grid size: {map_gen.grid_width}x{map_gen.grid_height}")
            print(f"Within tile grid: {debug_info['tile_info']['within_grid']}")
            
            try:
                tile_type, city_tile = map_gen.get_tile_info_at_position(x, y)
                debug_info['tile_info']['tile_type'] = tile_type
                debug_info['tile_info']['city_tile'] = city_tile
                print(f"Tile type: {tile_type}, City tile: {city_tile}")
            except Exception as e:
                print(f"Error getting tile info: {e}")
        
        # Check building collisions
        player_rect = pygame.Rect(x - 16, y - 16, 32, 32)  # Approximate player size
        for i, building in enumerate(self.game.buildings):
            if player_rect.colliderect(building.rect):
                collision_info = {
                    'building_index': i,
                    'building_rect': building.rect,
                    'building_type': getattr(building, 'building_type', 'unknown')
                }
                debug_info['building_collisions'].append(collision_info)
                print(f"Colliding with building {i} at {building.rect}")
        
        print("=" * 40)
        return debug_info
    
    def debug_map_info(self) -> Dict[str, Any]:
        """
        Print and return debug information about the generated map
        
        Returns:
            Dict containing map generation debug info
        """
        debug_info = {}
        
        if hasattr(self.game, 'map_generator'):
            debug_info = self.game.map_generator.get_debug_info()
            print("\n=== Map Generation Debug Info ===")
            for key, value in debug_info.items():
                if 'percentage' in key:
                    print(f"{key}: {value:.1f}%")
                else:
                    print(f"{key}: {value}")
            print("=" * 35)
        else:
            print("No map generator available for debugging")
            
        return debug_info
    
    def print_building_system_status(self) -> Dict[str, Any]:
        """
        Print detailed status of the building system
        
        Returns:
            Dict containing building system status information
        """
        print("\n=== Building System Status ===")
        
        # Get system info
        system_info = self.game.building_manager.get_system_info()
        for key, value in system_info.items():
            print(f"{key}: {value}")
        
        # Get individual building info
        building_info = self.game.building_manager.get_building_info()
        print("\n=== Individual Building Info ===")
        for info in building_info:
            print(f"Building: {info}")
        print("=" * 30)
        
        return {
            'system_info': system_info,
            'building_info': building_info
        }
    
    def debug_player_state(self) -> Dict[str, Any]:
        """
        Debug current player state and position
        
        Returns:
            Dict containing player debug information
        """
        player = self.game.player
        
        player_info = {
            'position': (player.rect.centerx, player.rect.centery),
            'rect': player.rect,
            'facing_left': player.facing_left,
            'inside_building': self.game.building_manager.is_inside_building()
        }
        
        print(f"\n=== Player Debug Info ===")
        print(f"Position: {player_info['position']}")
        print(f"Rect: {player_info['rect']}")
        print(f"Facing left: {player_info['facing_left']}")
        print(f"Inside building: {player_info['inside_building']}")
        print("=" * 25)
        
        return player_info
    
    def debug_npc_states(self) -> List[Dict[str, Any]]:
        """
        Debug all NPC states and positions
        
        Returns:
            List of dicts containing NPC debug information
        """
        npc_info_list = []
        
        print(f"\n=== NPC Debug Info ===")
        for i, npc_obj in enumerate(self.game.npcs):
            npc_info = {
                'index': i,
                'name': npc_obj.name,
                'position': (npc_obj.rect.centerx, npc_obj.rect.centery),
                'rect': npc_obj.rect,
                'facing_left': npc_obj.facing_left,
                'inside_building': npc_obj.is_inside_building,
                'current_building': getattr(npc_obj, 'current_building', None),
                'show_speech_bubble': npc_obj.show_speech_bubble
            }
            npc_info_list.append(npc_info)
            
            print(f"NPC {i} ({npc_obj.name}):")
            print(f"  Position: {npc_info['position']}")
            print(f"  Inside building: {npc_info['inside_building']}")
            print(f"  Speech bubble: {npc_info['show_speech_bubble']}")
        
        print("=" * 22)
        return npc_info_list
    
    def debug_camera_state(self) -> Dict[str, Any]:
        """
        Debug camera state and offset information
        
        Returns:
            Dict containing camera debug information
        """
        camera = self.game.camera
        
        camera_info = {
            'offset': (camera.offset.x, camera.offset.y),
            'target': getattr(camera, 'target', None),
            'smooth_follow': getattr(camera, 'smooth_follow', False),
            'smoothing': getattr(camera, 'smoothing', None)
        }
        
        if hasattr(camera, 'map_width') and hasattr(camera, 'map_height'):
            camera_info['map_bounds'] = (camera.map_width, camera.map_height)
        
        print(f"\n=== Camera Debug Info ===")
        print(f"Offset: {camera_info['offset']}")
        print(f"Smooth follow: {camera_info['smooth_follow']}")
        if camera_info['smoothing']:
            print(f"Smoothing: {camera_info['smoothing']}")
        if 'map_bounds' in camera_info:
            print(f"Map bounds: {camera_info['map_bounds']}")
        print("=" * 25)
        
        return camera_info
    
    def debug_game_state(self) -> Dict[str, Any]:
        """
        Debug overall game state information
        
        Returns:
            Dict containing game state debug information
        """
        game_info = {
            'game_state': self.game.game_state,
            'running': self.game.running,
            'game_over': self.game.game_over,
            'current_npc': self.game.current_npc.name if self.game.current_npc else None,
            'chat_cooldown': self.game.chat_manager.chat_cooldown,
            'debug_hitboxes': self.debug_hitboxes_enabled
        }
        
        print(f"\n=== Game State Debug Info ===")
        for key, value in game_info.items():
            print(f"{key}: {value}")
        print("=" * 29)
        
        return game_info
    
    def debug_performance_info(self) -> Dict[str, Any]:
        """
        Debug performance-related information
        
        Returns:
            Dict containing performance debug information
        """
        performance_info = {
            'fps': self.game.clock.get_fps(),
            'frame_time': self.game.clock.get_time(),
            'num_npcs': len(self.game.npcs),
            'num_buildings': len(self.game.buildings)
        }
        
        print(f"\n=== Performance Debug Info ===")
        print(f"FPS: {performance_info['fps']:.1f}")
        print(f"Frame time: {performance_info['frame_time']}ms")
        print(f"NPCs: {performance_info['num_npcs']}")
        print(f"Buildings: {performance_info['num_buildings']}")
        print("=" * 30)
        
        return performance_info
    
    def comprehensive_debug_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive debug report with all available information
        
        Returns:
            Dict containing all debug information
        """
        print("\n" + "=" * 50)
        print("COMPREHENSIVE DEBUG REPORT")
        print("=" * 50)
        
        report = {
            'timestamp': pygame.time.get_ticks(),
            'game_state': self.debug_game_state(),
            'player_state': self.debug_player_state(),
            'npc_states': self.debug_npc_states(),
            'camera_state': self.debug_camera_state(),
            'building_system': self.print_building_system_status(),
            'map_info': self.debug_map_info(),
            'performance': self.debug_performance_info()
        }
        
        print("=" * 50)
        print("END OF COMPREHENSIVE DEBUG REPORT")
        print("=" * 50 + "\n")
        
        return report


# Standalone debug functions for direct use
def debug_tile_at_position(map_generator, x: int, y: int) -> Optional[Tuple]:
    """
    Standalone function to debug tile information at a specific position
    
    Args:
        map_generator: Map generator instance
        x: X coordinate
        y: Y coordinate
        
    Returns:
        Tuple of (tile_type, city_tile) or None if invalid position
    """
    try:
        if hasattr(map_generator, 'get_tile_info_at_position'):
            return map_generator.get_tile_info_at_position(x, y)
        else:
            print("Map generator doesn't have get_tile_info_at_position method")
            return None
    except Exception as e:
        print(f"Error getting tile info at ({x}, {y}): {e}")
        return None


def debug_rect_collision(rect1: pygame.Rect, rect2: pygame.Rect) -> Dict[str, Any]:
    """
    Debug collision between two rectangles
    
    Args:
        rect1: First rectangle
        rect2: Second rectangle
        
    Returns:
        Dict containing collision debug information
    """
    collision_info = {
        'colliding': rect1.colliderect(rect2),
        'rect1': rect1,
        'rect2': rect2,
        'overlap': None,
        'distance': None
    }
    
    if collision_info['colliding']:
        # Calculate overlap area
        overlap_rect = rect1.clip(rect2)
        collision_info['overlap'] = overlap_rect
    else:
        # Calculate distance between centers
        center1 = rect1.center
        center2 = rect2.center
        distance = ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5
        collision_info['distance'] = distance
    
    return collision_info


def log_debug_info(info: Dict[str, Any], filename: str = "debug_log.txt") -> None:
    """
    Log debug information to a file
    
    Args:
        info: Debug information dictionary
        filename: Output filename
    """
    import json
    import datetime
    
    try:
        # Convert pygame.Rect objects to serializable format
        def convert_pygame_objects(obj):
            if isinstance(obj, pygame.Rect):
                return {'x': obj.x, 'y': obj.y, 'width': obj.width, 'height': obj.height}
            elif isinstance(obj, dict):
                return {k: convert_pygame_objects(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_pygame_objects(item) for item in obj]
            else:
                return obj
        
        serializable_info = convert_pygame_objects(info)
        
        with open(filename, 'a') as f:
            timestamp = datetime.datetime.now().isoformat()
            f.write(f"\n=== Debug Log Entry - {timestamp} ===\n")
            f.write(json.dumps(serializable_info, indent=2))
            f.write("\n" + "=" * 50 + "\n")
        
        print(f"Debug info logged to {filename}")
        
    except Exception as e:
        print(f"Error logging debug info: {e}")
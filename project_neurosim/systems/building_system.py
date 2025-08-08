"""
Building system that integrates all building-related components
"""
import pygame
from typing import List, Dict, Optional, Tuple
from .collision_system import CollisionMixin, InteriorWall
from world.interior import InteriorManager
from .interaction_system import BuildingInteractionSystem


class BuildingConfig:
    """Configuration class for different building types"""
    
    BUILDING_CONFIGS = {
        "house": {
            "hitbox_padding": {"width": 20, "height": 10, "x": 10, "y": 5},
            "interaction_padding": 40,
            "max_npcs": 3,
            "interior_size": (800, 600),
            "wall_thickness": 20,
            "door_width": 100
        },
        "shop": {
            "hitbox_padding": {"width": 30, "height": 15, "x": 15, "y": 10},
            "interaction_padding": 40,
            "max_npcs": 4,
            "interior_size": (900, 700),
            "wall_thickness": 25,
            "door_width": 120
        }
    }
    
    DEFAULT_CONFIG = {
        "hitbox_padding": {"width": 0, "height": 0, "x": 0, "y": 0},
        "interaction_padding": 40,
        "max_npcs": 3,
        "interior_size": (800, 600),
        "wall_thickness": 20,
        "door_width": 100
    }
    
    @classmethod
    def get_config(cls, building_type: str) -> Dict:
        """Get configuration for a building type"""
        return cls.BUILDING_CONFIGS.get(building_type, cls.DEFAULT_CONFIG)


class Building(CollisionMixin):
    """Main building class with modular components"""
    
    def __init__(self, x: int, y: int, building_type: str, assets):
        self.x = x
        self.y = y
        self.building_type = building_type
        self.config = BuildingConfig.get_config(building_type)
        
        # Load building image and set up rectangles
        self.image = assets["building"][building_type][0]
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Initialize core properties
        self.can_enter = True
        self.is_solid = True
        self.has_interior = True
        self.interior_size = self.config["interior_size"]
        self.furniture = []  # List of furniture items in this building
        
        # Initialize collision areas
        self._setup_collision_areas()
        
        # Initialize interior manager
        self.interior_manager = InteriorManager(self)
        self.interior_manager.initialize(assets)
        
        # Set up interaction zone (will be handled by BuildingInteractionSystem)
        self.interaction_zone = None

    def get_furniture_list(self):
        return self.furniture 
    
    def _setup_collision_areas(self):
        """Set up hitbox based on configuration"""
        padding = self.config["hitbox_padding"]
        
        # Setup hitbox
        hitbox_width = self.rect.width - padding["width"]
        hitbox_height = self.rect.height - padding["height"]
        hitbox_x = self.rect.x + padding["x"]
        hitbox_y = self.rect.y + padding["y"]
        self.hitbox = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
    
    def update_position(self, x: int, y: int):
        """Update building position and recalculate areas"""
        self.x = x
        self.y = y
        self.rect.topleft = (x, y)
        self._setup_collision_areas()
        
        # Update interaction zone if it exists
        if self.interaction_zone:
            self.interaction_zone.update_position(self.rect)
    
    def get_interior_walls(self) -> List[InteriorWall]:
        """Get collision walls for interior"""
        return self.interior_manager.get_walls()
    
    def get_interior_furniture_collisions(self) -> List:
        """Get collision objects for interior furniture"""
        return self.interior_manager.get_furniture_collisions()
    
    def check_furniture_interaction(self, player_rect: pygame.Rect):
        """Check if player can interact with any furniture in this building"""
        return self.interior_manager.check_furniture_interaction(player_rect)
    
    def get_interactable_furniture(self, player_rect: pygame.Rect):
        """Get all furniture items the player can interact with in this building"""
        return self.interior_manager.get_interactable_furniture(player_rect)
    
    def check_interaction_range(self, other_rect: pygame.Rect) -> bool:
        """Check if another rectangle is in interaction range"""
        if self.interaction_zone:
            return self.interaction_zone.check_interaction_range(other_rect)
        return False
    
    def check_exit_range(self, other_rect: pygame.Rect) -> bool:
        """Check if player is in range to exit the building"""
        return self.interior_manager.check_exit_range(other_rect)
    
    def get_interior_offset(self, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """Get the offset needed to center interior on screen"""
        return self.interior_manager.get_interior_offset(screen_width, screen_height)
    
    def draw(self, surface: pygame.Surface, camera, debug_hitboxes: bool = False):
        """Draw the building and optionally show debug info"""
        # Draw the building image
        draw_rect = camera.apply(self.rect)
        surface.blit(self.image, draw_rect)
        
        if debug_hitboxes:
            self._draw_debug_info(surface, camera)
    
    def _draw_debug_info(self, surface: pygame.Surface, camera):
        """Draw debug hitboxes and information"""
        # Draw collision hitbox in red
        hitbox_screen = camera.apply(self.hitbox)
        pygame.draw.rect(surface, (255, 0, 0), hitbox_screen, 2)
        
        # Draw interaction zone if it exists
        if self.interaction_zone:
            self.interaction_zone.draw_debug(surface, camera)
    
    def draw_interior(self, surface: pygame.Surface, debug_hitboxes: bool = False):
        """Draw the interior of the building"""
        self.interior_manager.draw_interior(surface, debug_hitboxes)
    
    # NPC management methods (delegated to InteriorManager)
    def can_npc_enter(self) -> bool:
        """Check if an NPC can enter this building"""
        return self.interior_manager.can_add_npc()
    
    def add_npc(self, npc) -> bool:
        """Add an NPC to this building"""
        return self.interior_manager.add_npc(npc)
    
    def remove_npc(self, npc) -> bool:
        """Remove an NPC from this building"""
        return self.interior_manager.remove_npc(npc)
    
    def get_npc_count(self) -> int:
        """Get the number of NPCs currently in this building"""
        return self.interior_manager.get_npc_count()
    
    def is_at_npc_capacity(self) -> bool:
        """Check if building is at NPC capacity"""
        return self.interior_manager.is_at_capacity()
    
    # Convenience properties for easier access
    @property
    def entrance_pos(self) -> Tuple[int, int]:
        """Get the entrance position of the building"""
        return self.interior_manager.get_entrance_pos()
    
    @property
    def exit_pos(self) -> Tuple[int, int]:
        """Get the exit position of the building"""
        return self.interior_manager.get_exit_pos()
    
    @property
    def exit_zone(self) -> pygame.Rect:
        """Get the exit zone rectangle"""
        return self.interior_manager.layout.exit_zone
    
    def get_building_info(self) -> Dict:
        """Get comprehensive information about this building"""
        return {
            "type": self.building_type,
            "position": (self.x, self.y),
            "size": (self.rect.width, self.rect.height),
            "interior_size": self.interior_size,
            "can_enter": self.can_enter,
            "has_interior": self.has_interior,
            "npc_count": self.get_npc_count(),
            "max_npcs": self.interior_manager.max_npcs,
            "at_capacity": self.is_at_npc_capacity(),
            "config": self.config
        }


class BuildingManager:
    """Main manager for the entire building system"""
    
    def __init__(self, buildings: List[Building]):
        self.buildings = buildings
        self.interaction_system = BuildingInteractionSystem(buildings)
        
        # Set up callbacks for system integration
        self.interaction_system.add_transition_callback(self._on_transition)
    
    def _on_transition(self, transition_type: str, building=None):
        """Handle transition events between interior/exterior"""
        if transition_type == "enter" and building:
            print(f"Transition: Entered {building.building_type}")
        elif transition_type == "exit" and building:
            print(f"Transition: Exited {building.building_type}")
    
    def check_building_entry(self, player_rect: pygame.Rect) -> Optional[Building]:
        """Check if player can enter any building"""
        return self.interaction_system.check_building_entry(player_rect)
    
    def enter_building(self, building: Building, player) -> bool:
        """Enter a building interior"""
        return self.interaction_system.enter_building(building, player)
    
    def check_building_exit(self, player_rect: pygame.Rect) -> bool:
        """Check if player can exit current building"""
        return self.interaction_system.check_building_exit(player_rect)
    
    def exit_building(self, player) -> bool:
        """Exit current building"""
        return self.interaction_system.exit_building(player)
    
    def get_interior_collision_walls(self) -> List[InteriorWall]:
        """Get collision walls for current interior"""
        current_interior = self.get_current_interior()
        return current_interior.get_interior_walls() if current_interior else []
    
    def get_interior_furniture_collisions(self) -> List:
        """Get furniture collision objects for current interior"""
        current_interior = self.get_current_interior()
        return current_interior.get_interior_furniture_collisions() if current_interior else []
    
    def check_furniture_interaction(self, player_rect: pygame.Rect):
        """Check if player can interact with any furniture in current interior"""
        current_interior = self.get_current_interior()
        return current_interior.check_furniture_interaction(player_rect) if current_interior else None
    
    def get_interactable_furniture(self, player_rect: pygame.Rect):
        """Get all furniture items the player can interact with in current interior"""
        current_interior = self.get_current_interior()
        return current_interior.get_interactable_furniture(player_rect) if current_interior else []
    
    def is_inside_building(self) -> bool:
        """Check if player is currently inside a building"""
        return self.interaction_system.is_inside_building()
    
    def get_current_interior(self) -> Optional[Building]:
        """Get the current interior building"""
        return self.interaction_system.get_current_interior()
    
    def get_building_info(self) -> List[Dict]:
        """Get information about all buildings and their NPC counts"""
        return [
            {
                'type': building.building_type,
                'position': (building.x, building.y),
                'npc_count': building.get_npc_count(),
                'max_npcs': building.interior_manager.max_npcs,
                'can_enter': building.can_enter,
                'has_interior': building.has_interior
            }
            for building in self.buildings
        ]
    
    def add_building(self, building: Building):
        """Add a new building to the system"""
        if building not in self.buildings:
            self.buildings.append(building)
            # Recreate interaction zones to include new building
            self.interaction_system._create_interaction_zones()
    
    def remove_building(self, building: Building) -> bool:
        """Remove a building from the system"""
        if building in self.buildings:
            self.buildings.remove(building)
            # Recreate interaction zones
            self.interaction_system._create_interaction_zones()
            return True
        return False
    
    def update_building_positions(self):
        """Update all building positions (call if buildings move)"""
        self.interaction_system.update_building_positions()
    
    def draw_debug_info(self, surface: pygame.Surface, camera):
        """Draw debug information for all buildings"""
        self.interaction_system.draw_debug_zones(surface, camera)
    
    def get_system_info(self) -> Dict:
        """Get comprehensive information about the building system"""
        interaction_info = self.interaction_system.get_interaction_info()
        
        return {
            "buildings_count": len(self.buildings),
            "building_types": [b.building_type for b in self.buildings],
            "interaction_info": interaction_info,
            "total_npcs_in_buildings": sum(b.get_npc_count() for b in self.buildings),
            "buildings_at_capacity": sum(1 for b in self.buildings if b.is_at_npc_capacity())
        }
    
    def cleanup(self):
        """Clean up the building system"""
        self.interaction_system.cleanup()
        for building in self.buildings:
            # Clean up any building-specific resources if needed
            if hasattr(building, 'interior_manager'):
                building.interior_manager.npcs_inside.clear()
    
    def find_building_by_type(self, building_type: str) -> Optional[Building]:
        """Find the first building of a specific type"""
        for building in self.buildings:
            if building.building_type == building_type:
                return building
        return None
    
    def find_buildings_by_type(self, building_type: str) -> List[Building]:
        """Find all buildings of a specific type"""
        return [b for b in self.buildings if b.building_type == building_type]
    
    def get_building_at_position(self, x: int, y: int) -> Optional[Building]:
        """Find building at a specific position"""
        point = pygame.Rect(x, y, 1, 1)
        for building in self.buildings:
            if building.rect.colliderect(point):
                return building
        return None
    
    def get_nearest_building(self, x: int, y: int) -> Optional[Building]:
        """Get the nearest building to a position"""
        if not self.buildings:
            return None
        
        min_distance = float('inf')
        nearest_building = None
        
        for building in self.buildings:
            # Calculate distance to building center
            dx = building.rect.centerx - x
            dy = building.rect.centery - y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest_building = building
        
        return nearest_building
    
    def validate_system(self) -> Dict[str, List[str]]:
        """Validate the building system and return any issues found"""
        issues = {
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        # Check for overlapping buildings
        for i, building1 in enumerate(self.buildings):
            for j, building2 in enumerate(self.buildings[i+1:], i+1):
                if building1.rect.colliderect(building2.rect):
                    issues["warnings"].append(
                        f"Buildings {i} and {j} are overlapping: "
                        f"{building1.building_type} at {building1.rect} and "
                        f"{building2.building_type} at {building2.rect}"
                    )
        
        # Check for buildings without proper configuration
        for i, building in enumerate(self.buildings):
            if not hasattr(building, 'config') or not building.config:
                issues["errors"].append(f"Building {i} ({building.building_type}) has no config")
            
            if not hasattr(building, 'interior_manager'):
                issues["errors"].append(f"Building {i} ({building.building_type}) has no interior_manager")
            
            if not building.has_interior and building.get_npc_count() > 0:
                issues["warnings"].append(
                    f"Building {i} ({building.building_type}) has no interior but contains NPCs"
                )
        
        # System-wide checks
        total_capacity = sum(b.interior_manager.max_npcs for b in self.buildings)
        total_npcs = sum(b.get_npc_count() for b in self.buildings)
        
        issues["info"].append(f"Total building capacity: {total_capacity}")
        issues["info"].append(f"Total NPCs in buildings: {total_npcs}")
        issues["info"].append(f"System utilization: {(total_npcs/total_capacity)*100:.1f}%")
        
        return issues


# Advanced building factory for different building types
class BuildingFactory:
    """Factory class for creating specialized buildings"""
    
    @staticmethod
    def create_house(x: int, y: int, assets, variant: str = "default") -> Building:
        """Create a house with specific configuration"""
        building = Building(x, y, "house", assets)
        
        # Add house-specific customizations
        if variant == "large":
            building.config["max_npcs"] = 5
            building.config["interior_size"] = (1000, 800)
        elif variant == "small":
            building.config["max_npcs"] = 2
            building.config["interior_size"] = (600, 400)
        
        return building
    
    @staticmethod
    def create_shop(x: int, y: int, assets, shop_type: str = "general") -> Building:
        """Create a shop with specific configuration"""
        building = Building(x, y, "shop", assets)
        
        # Add shop-specific customizations
        if shop_type == "tavern":
            building.config["max_npcs"] = 8
            building.config["interior_size"] = (1200, 900)
        elif shop_type == "blacksmith":
            building.config["max_npcs"] = 2
            building.config["door_width"] = 150  # Wider door for equipment
        
        return building
    
    @staticmethod
    def create_custom_building(x: int, y: int, assets, config: Dict) -> Building:
        """Create a building with completely custom configuration"""
        # Use house as base type but override with custom config
        building = Building(x, y, "house", assets)
        building.config.update(config)
        
        # Reinitialize with new config
        building.interior_size = building.config["interior_size"]
        building.interior_manager = InteriorManager(building)
        building.interior_manager.initialize(assets)
        
        return building


# Utility functions for building management
def create_building_manager(building_data: List[Dict], assets) -> BuildingManager:
    """
    Create a building manager from building data
    
    Args:
        building_data: List of dicts with keys: x, y, building_type, and optional variant/config
        assets: Game assets dictionary
    
    Returns:
        BuildingManager instance
    """
    buildings = []
    factory = BuildingFactory()
    
    for data in building_data:
        building_type = data["building_type"]
        x, y = data["x"], data["y"]
        
        # Check for specialized creation
        if "variant" in data and building_type == "house":
            building = factory.create_house(x, y, assets, data["variant"])
        elif "shop_type" in data and building_type == "shop":
            building = factory.create_shop(x, y, assets, data["shop_type"])
        elif "custom_config" in data:
            building = factory.create_custom_building(x, y, assets, data["custom_config"])
        else:
            # Standard creation
            building = Building(x, y, building_type, assets)
        
        buildings.append(building)
    
    return BuildingManager(buildings)


def create_town_layout(center_x: int, center_y: int, assets, town_size: str = "small") -> BuildingManager:
    """
    Create a pre-designed town layout
    
    Args:
        center_x, center_y: Center coordinates for the town
        assets: Game assets
        town_size: "small", "medium", or "large"
    
    Returns:
        BuildingManager with town layout
    """
    layouts = {
        "small": [
            {"x": center_x - 150, "y": center_y + 100, "building_type": "house"},
            {"x": center_x + 50, "y": center_y + 100, "building_type": "shop"},
            {"x": center_x - 50, "y": center_y + 200, "building_type": "house", "variant": "small"}
        ],
        "medium": [
            {"x": center_x - 200, "y": center_y + 100, "building_type": "house"},
            {"x": center_x, "y": center_y + 100, "building_type": "shop"},
            {"x": center_x + 200, "y": center_y + 100, "building_type": "house"},
            {"x": center_x - 100, "y": center_y + 250, "building_type": "shop", "shop_type": "tavern"},
            {"x": center_x + 100, "y": center_y + 250, "building_type": "house", "variant": "large"}
        ],
        "large": [
            # Main street
            {"x": center_x - 300, "y": center_y + 100, "building_type": "house"},
            {"x": center_x - 150, "y": center_y + 100, "building_type": "shop"},
            {"x": center_x, "y": center_y + 100, "building_type": "shop", "shop_type": "tavern"},
            {"x": center_x + 150, "y": center_y + 100, "building_type": "shop", "shop_type": "blacksmith"},
            {"x": center_x + 300, "y": center_y + 100, "building_type": "house"},
            # Side streets
            {"x": center_x - 200, "y": center_y + 300, "building_type": "house", "variant": "large"},
            {"x": center_x, "y": center_y + 300, "building_type": "house"},
            {"x": center_x + 200, "y": center_y + 300, "building_type": "house", "variant": "small"},
            # Back area
            {"x": center_x - 100, "y": center_y - 100, "building_type": "house", "variant": "large"},
            {"x": center_x + 100, "y": center_y - 100, "building_type": "house"}
        ]
    }
    
    building_data = layouts.get(town_size, layouts["small"])
    return create_building_manager(building_data, assets)
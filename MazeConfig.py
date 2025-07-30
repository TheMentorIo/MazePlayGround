"""
Configuration class for maze generation.
Provides centralized configuration management with validation and presets.
"""

import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

class Direction(Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

class CellType(Enum):
    """Enumeration for maze cell types."""
    UNVISITED = -2
    WALL = -1
    ROOM = 0
    VISITED = 2
    PLAYER = 3
    EXIT = 4


class AlgorithmType(Enum):
    """Enumeration for maze generation algorithms."""
    RECURSIVE_BACKTRACKING = "recursive_backtracking"
    PROBABILISTIC = "probabilistic"
    ELLER = "eller"
    KRUSKAL = "kruskal"


@dataclass
class MazeConfig:
    """
    Configuration class for maze generation.
    
    This class provides centralized configuration management with validation,
    presets, and type safety for maze generation parameters.
    """
    
    # Basic maze dimensions
    maze_width: int = 20
    maze_height: int = 20
    
    # Generation algorithm parameters
    decay_factor: float = 0.25
    base_prob_factor: float = 0.25
    min_room_prob: float = 0.05
    
    # Algorithm selection
    algorithm: AlgorithmType = AlgorithmType.PROBABILISTIC
    
    # Direction weights for generation
    direction_weights: Dict[str, float] = field(default_factory=lambda: {
        'RIGHT': 0.25,
        'DOWN': 0.25,
        'LEFT': 0.25,
        'UP': 0.25,
    })
    
    # Debug and performance options
    enable_debug: bool = False
    enable_statistics: bool = True
    
    # Advanced generation parameters
    room_clustering_factor: float = 0.1
    corridor_width: int = 1
    dead_end_removal_probability: float = 0.0
    
    # Visualization settings
    cell_size: int = 20
    wall_thickness: int = 2
    
    # Export settings
    export_format: str = "both"  # "json", "png", "both"
    image_dpi: int = 300
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate_config()
        self.normalize_direction_weights()
        logging.debug("MazeConfig initialized and validated")

    def validate_config(self) -> None:
        """Validate all configuration parameters."""
        # Validate dimensions
        if self.maze_width < 3:
            raise ValueError("maze_width must be at least 3")
        if self.maze_height < 3:
            raise ValueError("maze_height must be at least 3")
        if self.maze_width > 1000 or self.maze_height > 1000:
            logging.warning("Large maze dimensions may cause performance issues")
        
        # Validate probability factors
        if not 0.0 <= self.decay_factor <= 1.0:
            raise ValueError("decay_factor must be between 0.0 and 1.0")
        if not 0.0 <= self.base_prob_factor <= 1.0:
            raise ValueError("base_prob_factor must be between 0.0 and 1.0")
        if not 0.0 <= self.min_room_prob <= 1.0:
            raise ValueError("min_room_prob must be between 0.0 and 1.0")
        
        # Validate direction weights
        if not self.direction_weights:
            raise ValueError("direction_weights cannot be empty")
        
        required_directions = {'RIGHT', 'DOWN', 'LEFT', 'UP'}
        if not required_directions.issubset(self.direction_weights.keys()):
            raise ValueError(f"direction_weights must contain all directions: {required_directions}")
        
        for direction, weight in self.direction_weights.items():
            if not 0.0 <= weight <= 1.0:
                raise ValueError(f"Weight for {direction} must be between 0.0 and 1.0")
        
        # Validate advanced parameters
        if not 0.0 <= self.room_clustering_factor <= 1.0:
            raise ValueError("room_clustering_factor must be between 0.0 and 1.0")
        if self.corridor_width < 1:
            raise ValueError("corridor_width must be at least 1")
        if not 0.0 <= self.dead_end_removal_probability <= 1.0:
            raise ValueError("dead_end_removal_probability must be between 0.0 and 1.0")

    def normalize_direction_weights(self) -> None:
        """Normalize direction weights to sum to 1.0."""
        total_weight = sum(self.direction_weights.values())
        if total_weight == 0:
            # If all weights are 0, set them to equal
            for direction in self.direction_weights:
                self.direction_weights[direction] = 0.25
        elif abs(total_weight - 1.0) > 1e-6:
            # Normalize weights to sum to 1.0
            for direction in self.direction_weights:
                self.direction_weights[direction] /= total_weight
            logging.debug(f"Normalized direction weights, original sum: {total_weight}")

    @property
    def total_cells(self) -> int:
        """Get total number of cells in the maze."""
        return self.maze_width * self.maze_height

    @property
    def cell_types(self) -> type:
        """Get cell type enumeration for convenience."""
        return CellType

    def get_cell_value(self, cell_type: CellType) -> int:
        """
        Get numeric value for a cell type.
        
        Args:
            cell_type: Cell type enum
            
        Returns:
            Numeric value for the cell type
        """
        return cell_type.value

    def is_valid_position(self, x: int, y: int) -> bool:
        """
        Check if a position is valid within the maze bounds.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if position is valid, False otherwise
        """
        return 0 <= x < self.maze_height and 0 <= y < self.maze_width

    def get_neighbors(self, x: int, y: int) -> list:
        """
        Get valid neighboring positions.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            List of valid neighboring positions
        """
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny):
                neighbors.append((nx, ny))
        
        return neighbors

    def copy(self) -> 'MazeConfig':
        """
        Create a deep copy of the configuration.
        
        Returns:
            New MazeConfig instance with same parameters
        """
        return MazeConfig(
            maze_width=self.maze_width,
            maze_height=self.maze_height,
            decay_factor=self.decay_factor,
            base_prob_factor=self.base_prob_factor,
            min_room_prob=self.min_room_prob,
            algorithm=self.algorithm,
            direction_weights=self.direction_weights.copy(),
            enable_debug=self.enable_debug,
            enable_statistics=self.enable_statistics,
            room_clustering_factor=self.room_clustering_factor,
            corridor_width=self.corridor_width,
            dead_end_removal_probability=self.dead_end_removal_probability,
            cell_size=self.cell_size,
            wall_thickness=self.wall_thickness,
            export_format=self.export_format,
            image_dpi=self.image_dpi
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'maze_width': self.maze_width,
            'maze_height': self.maze_height,
            'decay_factor': self.decay_factor,
            'base_prob_factor': self.base_prob_factor,
            'min_room_prob': self.min_room_prob,
            'algorithm': self.algorithm.value,
            'direction_weights': self.direction_weights,
            'enable_debug': self.enable_debug,
            'enable_statistics': self.enable_statistics,
            'room_clustering_factor': self.room_clustering_factor,
            'corridor_width': self.corridor_width,
            'dead_end_removal_probability': self.dead_end_removal_probability,
            'cell_size': self.cell_size,
            'wall_thickness': self.wall_thickness,
            'export_format': self.export_format,
            'image_dpi': self.image_dpi
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'MazeConfig':
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Dictionary with configuration parameters
            
        Returns:
            New MazeConfig instance
        """
        # Convert algorithm string back to enum if present
        if 'algorithm' in config_dict and isinstance(config_dict['algorithm'], str):
            config_dict['algorithm'] = AlgorithmType(config_dict['algorithm'])
        
        return cls(**config_dict)

    @classmethod
    def get_preset(cls, preset_name: str) -> 'MazeConfig':
        """
        Get a predefined configuration preset.
        
        Args:
            preset_name: Name of the preset
            
        Returns:
            MazeConfig instance with preset parameters
            
        Raises:
            ValueError: If preset name is not found
        """
        presets = {
            "tiny": cls(
                maze_width=5, maze_height=5,
                decay_factor=0.3, base_prob_factor=0.3
            ),
            "small": cls(
                maze_width=10, maze_height=10,
                decay_factor=0.25, base_prob_factor=0.25
            ),
            "medium": cls(
                maze_width=20, maze_height=20,
                decay_factor=0.2, base_prob_factor=0.2
            ),
            "large": cls(
                maze_width=40, maze_height=40,
                decay_factor=0.15, base_prob_factor=0.15
            ),
            "sparse": cls(
                maze_width=20, maze_height=20,
                decay_factor=0.1, base_prob_factor=0.1,
                min_room_prob=0.02
            ),
            "dense": cls(
                maze_width=20, maze_height=20,
                decay_factor=0.4, base_prob_factor=0.4,
                min_room_prob=0.1
            ),
            "linear": cls(
                maze_width=20, maze_height=20,
                direction_weights={'RIGHT': 0.4, 'DOWN': 0.4, 'LEFT': 0.1, 'UP': 0.1}
            ),
            "vertical": cls(
                maze_width=20, maze_height=20,
                direction_weights={'RIGHT': 0.2, 'DOWN': 0.4, 'LEFT': 0.2, 'UP': 0.2}
            ),
            "horizontal": cls(
                maze_width=20, maze_height=20,
                direction_weights={'RIGHT': 0.4, 'DOWN': 0.2, 'LEFT': 0.2, 'UP': 0.2}
            )
        }
        
        if preset_name.lower() not in presets:
            available_presets = ', '.join(presets.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available presets: {available_presets}")
        
        return presets[preset_name.lower()]

    @classmethod
    def get_available_presets(cls) -> list:
        """
        Get list of available preset names.
        
        Returns:
            List of preset names
        """
        return ["tiny", "small", "medium", "large", "sparse", "dense", "linear", "vertical", "horizontal"]

    def apply_preset_modifications(self, modifications: Dict[str, Any]) -> None:
        """
        Apply modifications to current configuration.
        
        Args:
            modifications: Dictionary of parameter modifications
        """
        for key, value in modifications.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logging.warning(f"Unknown configuration parameter: {key}")
        
        # Re-validate and normalize after modifications
        self.validate_config()
        self.normalize_direction_weights()

    def __str__(self) -> str:
        """String representation of configuration."""
        return (f"MazeConfig({self.maze_width}x{self.maze_height}, "
                f"algorithm={self.algorithm.value}, "
                f"decay={self.decay_factor}, "
                f"base_prob={self.base_prob_factor})")

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"MazeConfig({self.to_dict()})"


# Legacy compatibility - maintain old interface
class LegacyMazeConfig:
    """Legacy interface for backward compatibility."""
    
    def __init__(self, **kwargs):
        """Initialize with legacy parameters."""
        logging.warning("LegacyMazeConfig is deprecated. Use MazeConfig instead.")
        self._config = MazeConfig(**kwargs)
    
    def __getattr__(self, name):
        """Delegate attribute access to new config."""
        return getattr(self._config, name)


# Convenience function for quick configuration creation
def create_maze_config(preset: Optional[str] = None, **overrides) -> MazeConfig:
    """
    Create a maze configuration with optional preset and overrides.
    
    Args:
        preset: Optional preset name
        **overrides: Parameter overrides
        
    Returns:
        Configured MazeConfig instance
    """
    if preset:
        config = MazeConfig.get_preset(preset)
        if overrides:
            config.apply_preset_modifications(overrides)
        return config
    else:
        return MazeConfig(**overrides)

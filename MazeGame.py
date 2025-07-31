"""
Maze Game Engine
Interactive maze game with player movement, exit finding, and visualization.
"""

import numpy as np
import random
import logging
from typing import Optional, Tuple, Dict, List, Union
from enum import IntEnum
from dataclasses import dataclass
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
from MazeConfig import Direction,CellType




@dataclass
class GameStats:
    """Data class to track game statistics."""
    moves_count: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    player_path: Optional[List[Tuple[int, int]]] = None
    
    def __post_init__(self):
        if self.player_path is None:
            self.player_path = []
    
    @property
    def game_duration(self) -> Optional[float]:
        """Calculate game duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

class MazeGame:
    """
    Enhanced maze game engine with improved functionality and performance.
    
    Features:
    - Player movement and collision detection
    - Exit generation with strategic placement
    - Game state management
    - Statistics tracking
    - Multiple visualization options
    - Comprehensive error handling
    """
    
    # Direction mappings for player movement
    DIRECTION_MAPPING = {
        'w': (-1, 0),  # Up
        's': (1, 0),   # Down
        'a': (0, -1),  # Left
        'd': (0, 1),   # Right
        Direction.UP: (-1, 0),
        Direction.DOWN: (1, 0),
        Direction.LEFT: (0, -1),
        Direction.RIGHT: (0, 1)
    }
    
    # Visual representation for ASCII display
    CELL_SYMBOLS = {
        CellType.PLAYER: " P ",
        CellType.EXIT: " E ",
        CellType.WALL: " ■ ",
        CellType.UNVISITED: " ░ ",
        CellType.ROOM: " · ",
        CellType.VISITED: " ○ "
    }
    
    def __init__(self, maze: Optional[List[List[int]]] = None):
        """
        Initialize maze game.
        
        Args:
            maze: 2D list representing the maze layout
        """
        self.maze = maze
        self.original_maze = None  # Keep backup for reset
        
        # Player state
        self.player_x: Optional[int] = None
        self.player_y: Optional[int] = None
        self.is_playing = False
        
        # Exit state
        self.exit_x: Optional[int] = None
        self.exit_y: Optional[int] = None
        
        # Game state
        self.game_won = False
        self.game_over = False
        
        # Game statistics
        self.stats = GameStats()
        
        # Configuration
        self.exit_search_radius = 3
        self.min_exit_distance = 5
        
        logging.debug("MazeGame initialized")

    @property
    def maze_dimensions(self) -> Tuple[int, int]:
        """Get maze dimensions (height, width)."""
        if self.maze is None:
            return (0, 0)
        return (len(self.maze), len(self.maze[0]) if self.maze else 0)

    @property
    def player_position(self) -> Optional[Tuple[int, int]]:
        """Get current player position."""
        if self.player_x is not None and self.player_y is not None:
            return (self.player_x, self.player_y)
        return None

    @property
    def exit_position(self) -> Optional[Tuple[int, int]]:
        """Get exit position."""
        if self.exit_x is not None and self.exit_y is not None:
            return (self.exit_x, self.exit_y)
        return None

    def load_maze(self, maze: List[List[int]]) -> bool:
        """
        Load a new maze into the game.
        
        Args:
            maze: 2D list representing the maze
            
        Returns:
            True if maze loaded successfully, False otherwise
        """
        try:
            if not maze or not maze[0]:
                logging.error("Invalid maze provided")
                return False
            
            self.maze = [row[:] for row in maze]  # Deep copy
            self.original_maze = [row[:] for row in maze]  # Backup
            self.reset_game_state()
            
            logging.info(f"Maze loaded successfully: {self.maze_dimensions}")
            return True
            
        except Exception as e:
            logging.error(f"Error loading maze: {e}")
            return False

    def reset_game_state(self) -> None:
        """Reset game state to initial values."""
        self.player_x = None
        self.player_y = None
        self.exit_x = None
        self.exit_y = None
        self.is_playing = False
        self.game_won = False
        self.game_over = False
        self.stats = GameStats()

    def in_bounds(self, x: int, y: int) -> bool:
        """
        Check if coordinates are within maze bounds.
        
        Args:
            x: Row coordinate
            y: Column coordinate
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        if self.maze is None:
            return False
        height, width = self.maze_dimensions
        return 0 <= x < height and 0 <= y < width

    def is_walkable(self, x: int, y: int) -> bool:
        """
        Check if a cell is walkable (not a wall).
        
        Args:
            x: Row coordinate
            y: Column coordinate
            
        Returns:
            True if cell is walkable, False otherwise
        """
        if not self.in_bounds(x, y):
            return False
        
        cell_value = self.maze[x][y]
        return cell_value != CellType.WALL

    def get_available_rooms(self, exclude_player: bool = True) -> List[Tuple[int, int]]:
        """
        Get all available room positions in the maze.
        
        Args:
            exclude_player: Whether to exclude player's current position
            
        Returns:
            List of (x, y) coordinates of available rooms
        """
        if self.maze is None:
            return []
        
        rooms = []
        height, width = self.maze_dimensions
        
        for x in range(height):
            for y in range(width):
                if self.maze[x][y] == CellType.ROOM:
                    if exclude_player and (x == self.player_x and y == self.player_y):
                        continue
                    rooms.append((x, y))
        
        return rooms

    def generate_player(self, position: Optional[Tuple[int, int]] = None) -> bool:
        """
        Place player in the maze.
        
        Args:
            position: Optional specific position (x, y) for player
            
        Returns:
            True if player placed successfully, False otherwise
        """
        try:
            if self.maze is None:
                logging.error("No maze loaded")
                return False
            
            if position:
                x, y = position
                if not self.in_bounds(x, y) or not self.is_walkable(x, y):
                    logging.error(f"Invalid player position: {position}")
                    return False
                self.player_x, self.player_y = x, y
            else:
                room_positions = np.nonzero(np.array(self.maze) == CellType.ROOM.value)
                if len(room_positions[0]) == 0:
                    logging.error("No rooms available for player")
                    return False
                
                # Pick random room
                idx = random.randint(0, len(room_positions[0]) - 1)
                self.player_x = room_positions[0][idx]
                self.player_y = room_positions[1][idx]
            
            # Place player in maze
            self.maze[self.player_x][self.player_y] = CellType.PLAYER.value
            self.is_playing = True
            
            # Initialize stats
            import time
            self.stats.start_time = time.time()
            self.stats.player_path.append((self.player_x, self.player_y))
            
            logging.info(f"Player placed at ({self.player_x}, {self.player_y})")
            return True
            
        except Exception as e:
            logging.error(f"Error generating player: {e}")
            return False
    
    def _calculate_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _get_corner_positions(self) -> List[Tuple[int, int]]:
        """Get the four corner positions of the maze."""
        height, width = self.maze_dimensions
        return [
            (0, 0),                    # Top-left
            (0, width - 1),           # Top-right  
            (height - 1, 0),          # Bottom-left
            (height - 1, width - 1)   # Bottom-right
        ]

    def _find_rooms_near_position(self, center: Tuple[int, int], 
                                 radius: int) -> List[Tuple[int, int]]:
        """
        Find available rooms near a given position.
        
        Args:
            center: Center position (x, y)
            radius: Search radius
            
        Returns:
            List of available room positions
        """
        cx, cy = center
        height, width = self.maze_dimensions
        rooms = []
        
        min_x = max(0, cx - radius)
        max_x = min(height, cx + radius + 1)
        min_y = max(0, cy - radius)
        max_y = min(width, cy + radius + 1)
        
        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                if (self.maze[x][y] == CellType.ROOM.value and 
                    (x != self.player_x or y != self.player_y)):
                    rooms.append((x, y))
        
        return rooms

    def generate_exit(self, min_distance: Optional[int] = None) -> bool:
        """
        Place exit in the maze, preferably far from player.
        
        Args:
            min_distance: Minimum distance from player (optional)
            
        Returns:
            True if exit placed successfully, False otherwise
        """
        try:
            if self.maze is None or not self.is_playing:
                logging.error("Generate maze and player first")
                return False
            
            min_dist = min_distance or self.min_exit_distance
            player_pos = (self.player_x, self.player_y)
            
            # Try corners first (furthest positions)
            corners = self._get_corner_positions()
            corner_distances = [(self._calculate_distance(player_pos, corner), corner) 
                              for corner in corners]
            corner_distances.sort(reverse=True)  # Furthest first
            
            # Search near corners
            for _, corner in corner_distances:
                rooms = self._find_rooms_near_position(corner, self.exit_search_radius)
                if rooms:
                    # Filter by minimum distance
                    valid_rooms = [room for room in rooms 
                                 if self._calculate_distance(player_pos, room) >= min_dist]
                    if valid_rooms:
                        self.exit_x, self.exit_y = random.choice(valid_rooms)
                        self.maze[self.exit_x][self.exit_y] = CellType.EXIT.value
                        distance = self._calculate_distance(player_pos, (self.exit_x, self.exit_y))
                        logging.info(f"Exit placed at ({self.exit_x}, {self.exit_y}) - Distance: {distance}")
                        return True
            
            # Fallback: any available room with minimum distance
            available_rooms = self.get_available_rooms(exclude_player=True)
            valid_rooms = [room for room in available_rooms 
                         if self._calculate_distance(player_pos, room) >= min_dist]
            
            if valid_rooms:
                # Choose the furthest available room
                furthest_room = max(valid_rooms, 
                                  key=lambda room: self._calculate_distance(player_pos, room))
                self.exit_x, self.exit_y = furthest_room
                self.maze[self.exit_x][self.exit_y] = CellType.EXIT.value
                distance = self._calculate_distance(player_pos, (self.exit_x, self.exit_y))
                logging.info(f"Exit placed at ({self.exit_x}, {self.exit_y}) - Distance: {distance}")
                return True
            elif available_rooms:
                # Last resort: any available room
                self.exit_x, self.exit_y = random.choice(available_rooms)
                self.maze[self.exit_x][self.exit_y] = CellType.EXIT.value
                logging.warning("Exit placed without minimum distance constraint")
                return True
            
            logging.error("No available rooms for exit")
            return False
            
        except Exception as e:
            logging.error(f"Error generating exit: {e}")
            return False

    def move_player(self, direction: Union[str, Direction]) -> bool:
        """
        Move player in specified direction.
        
        Args:
            direction: Direction to move ('w', 'a', 's', 'd' or Direction enum)
            
        Returns:
            True if move was successful, False otherwise
        """
        try:
            if not self.is_playing or self.game_over:
                logging.warning("Game not active")
                return False
            
            if direction not in self.DIRECTION_MAPPING:
                logging.error(f"Invalid direction: {direction}")
                return False
            
            dx, dy = self.DIRECTION_MAPPING[direction]
            new_x = self.player_x + dx
            new_y = self.player_y + dy
            
            # Check bounds
            if not self.in_bounds(new_x, new_y):
                logging.debug("Move out of bounds")
                return False
            
            # Check if target cell is walkable
            target_cell = self.maze[new_x][new_y]
            if target_cell == CellType.WALL.value:
                logging.debug("Cannot move into wall")
                return False
            
            # Update stats
            self.stats.moves_count += 1
            
            # Check if player reached the exit
            if target_cell == CellType.EXIT.value:
                self._handle_victory(new_x, new_y)
                return True
            
            # Normal move
            self._execute_move(new_x, new_y)
            return True
            
        except Exception as e:
            logging.error(f"Error moving player: {e}")
            return False

    def _handle_victory(self, new_x: int, new_y: int) -> None:
        """Handle player reaching the exit."""
        # Mark old position as visited
        self.maze[self.player_x][self.player_y] = CellType.VISITED.value

        # Move player to exit
        self.player_x = new_x
        self.player_y = new_y
        self.maze[self.player_x][self.player_y] = CellType.PLAYER.value

        # Update game state
        self.game_won = True
        self.game_over = True
        
        # Update stats
        import time
        self.stats.end_time = time.time()
        self.stats.player_path.append((self.player_x, self.player_y))
        
        logging.info("Player reached the exit! Game won!")

    def _execute_move(self, new_x: int, new_y: int) -> None:
        """Execute a normal player move."""
        # Mark old position as visited
        self.maze[self.player_x][self.player_y] = CellType.VISITED.value

        # Move player to new position
        self.player_x = new_x
        self.player_y = new_y
        self.maze[self.player_x][self.player_y] = CellType.PLAYER.value

        # Update path
        self.stats.player_path.append((self.player_x, self.player_y))
        
        logging.debug(f"Player moved to ({self.player_x}, {self.player_y})")

    def is_valid_move(self, direction: Union[str, Direction]) -> bool:
        """
        Check if a move in the given direction is valid.
        
        Args:
            direction: Direction to check
            
        Returns:
            True if move is valid, False otherwise
        """
        if not self.is_playing or direction not in self.DIRECTION_MAPPING:
            return False
        
        dx, dy = self.DIRECTION_MAPPING[direction]
        new_x = self.player_x + dx
        new_y = self.player_y + dy
        
        return self.in_bounds(new_x, new_y) and self.is_walkable(new_x, new_y)

    def get_game_info(self) -> Dict[str, any]:
        """
        Get comprehensive game information.
        
        Returns:
            Dictionary with game state and statistics
        """
        return {
            "is_playing": self.is_playing,
            "game_won": self.game_won,
            "game_over": self.game_over,
            "player_position": self.player_position,
            "exit_position": self.exit_position,
            "maze_dimensions": self.maze_dimensions,
            "moves_count": self.stats.moves_count,
            "game_duration": self.stats.game_duration,
            "path_length": len(self.stats.player_path)
        }
    def visualize(self, block: bool = True, figsize: Tuple[int, int] = (12, 8)) -> bool:
        """
        Visualize the current maze with matplotlib.
        
        Args:
            block: Whether to block execution until plot is closed
            figsize: Figure size (width, height)
            
        Returns:
            True if visualization successful, False otherwise
        """
        
        if self.maze is None:
            logging.error("No maze to visualize")
            return False
        
        try:
            # Create color mapping
            colors = ['lightgray', 'black', 'white', 'lightblue', 'red', 'lightgreen']
            custom_cmap = ListedColormap(colors)
            
            # Create figure
            plt.figure(figsize=figsize)
            plt.imshow(self.maze, cmap=custom_cmap, origin='upper', vmin=-2, vmax=4)
            
            # Create title
            title = "Maze Game"
            if self.game_won:
                title += " - 🏆 VICTORY! 🏆"
            elif self.is_playing:
                title += f" - Moves: {self.stats.moves_count}"
            
            plt.title(title, fontsize=16, fontweight='bold')
            
            # Create legend
            legend_elements = [
                Rectangle((0, 0), 1, 1, facecolor='lightgray', label='Unvisited'),
                Rectangle((0, 0), 1, 1, facecolor='black', label='Room'),
                Rectangle((0, 0), 1, 1, facecolor='white', label='Wall'),
                Rectangle((0, 0), 1, 1, facecolor='lightgreen', label='Visited'),
                Rectangle((0, 0), 1, 1, facecolor='lightblue', label='Player'),
                Rectangle((0, 0), 1, 1, facecolor='red', label='Exit')
            ]
            
            plt.legend(handles=legend_elements, loc='center left', 
                      bbox_to_anchor=(1, 0.5), fontsize=10)
            
            plt.axis('off')
            plt.tight_layout()
            
            if not block:
                plt.ion()
                plt.show()
                plt.pause(0.1)
            else:
                plt.show()
            
            return True
            
        except Exception as e:
            logging.error(f"Error in visualization: {e}")
            return False

    def print_maze_ascii(self) -> None:
        """Print ASCII representation of the maze."""
        if self.maze is None:
            print("No maze to display!")
            return
        
        self._print_header()
        self._print_maze_grid()
        self._print_footer()

    def _print_header(self) -> None:
        """Print game header."""
        separator = "=" * 60
        print(f"\n{separator}")
        
        if self.game_won:
            print("🏆 CONGRATULATIONS! YOU WON THE GAME! 🏆")
        else:
            title = "MAZE GAME"
            if self.is_playing:
                title += f" - Moves: {self.stats.moves_count}"
            print(title)
        
        print(separator)

    def _print_maze_grid(self) -> None:
        """Print the maze grid."""
        for row in self.maze:
            line = ""
            for cell in row:
                symbol = self.CELL_SYMBOLS.get(cell, " ? ")
                line += symbol
            print(line)

    def _print_footer(self) -> None:
        """Print game footer with status and controls."""
        separator = "=" * 60
        print(separator)
        
        if self.game_won:
            print("🎉 GAME COMPLETED! You reached the exit! 🎉")
            if self.stats.game_duration:
                print(f"⏱️  Time: {self.stats.game_duration:.1f} seconds")
            print(f"📊 Total moves: {self.stats.moves_count}")
        else:
            self._print_game_status()
        
        print("Controls: w(up) a(left) s(down) d(right) v(visual) m(map) q(quit)")
        print(separator)

    def _print_game_status(self) -> None:
        """Print current game status."""
        if self.player_position and self.exit_position:
            print(f"Player: {self.player_position} | Exit: {self.exit_position}")
            distance = self._calculate_distance(self.player_position, self.exit_position)
            print(f"Distance to exit: {distance} steps")
        
        if self.stats.game_duration:
            print(f"Game time: {self.stats.game_duration:.1f} seconds")

    def start_game(self, player_pos: Optional[Tuple[int, int]] = None,
                   min_exit_distance: Optional[int] = None) -> bool:
        """
        Start a new game session.
        
        Args:
            player_pos: Optional starting position for player
            min_exit_distance: Minimum distance between player and exit
            
        Returns:
            True if game started successfully, False otherwise
        """
        try:
            if self.maze is None:
                logging.error("No maze loaded")
                return False
            
            # Reset game state
            if self.original_maze:
                self.maze = [row[:] for row in self.original_maze]
            self.reset_game_state()
            
            # Generate player
            if not self.generate_player(player_pos):
                return False
            
            # Generate exit
            if not self.generate_exit(min_exit_distance):
                return False
            
            logging.info("Game started successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error starting game: {e}")
            return False

    def get_move_suggestions(self) -> List[str]:
        """
        Get list of valid moves from current position.
        
        Returns:
            List of valid direction strings
        """
        valid_moves = []
        for direction in ['w', 'a', 's', 'd']:
            if self.is_valid_move(direction):
                valid_moves.append(direction)
        return valid_moves

    def save_game_state(self) -> Dict[str, any]:
        """
        Save current game state.
        
        Returns:
            Dictionary containing game state
        """
        return {
            "maze": [row[:] for row in self.maze] if self.maze else None,
            "original_maze": [row[:] for row in self.original_maze] if self.original_maze else None,
            "player_position": self.player_position,
            "exit_position": self.exit_position,
            "is_playing": self.is_playing,
            "game_won": self.game_won,
            "game_over": self.game_over,
            "stats": {
                "moves_count": self.stats.moves_count,
                "start_time": self.stats.start_time,
                "end_time": self.stats.end_time,
                "player_path": self.stats.player_path[:]
            }
        }

    def load_game_state(self, state: Dict[str, any]) -> bool:
        """
        Load game state from dictionary.
        
        Args:
            state: Dictionary containing game state
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            self.maze = state.get("maze")
            self.original_maze = state.get("original_maze")
            
            player_pos = state.get("player_position")
            if player_pos:
                self.player_x, self.player_y = player_pos
            
            exit_pos = state.get("exit_position")
            if exit_pos:
                self.exit_x, self.exit_y = exit_pos
            
            self.is_playing = state.get("is_playing", False)
            self.game_won = state.get("game_won", False)
            self.game_over = state.get("game_over", False)
            
            # Load stats
            stats_data = state.get("stats", {})
            self.stats.moves_count = stats_data.get("moves_count", 0)
            self.stats.start_time = stats_data.get("start_time")
            self.stats.end_time = stats_data.get("end_time")
            self.stats.player_path = stats_data.get("player_path", [])
            
            logging.info("Game state loaded successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error loading game state: {e}")
            return False
    def play_interactive(self) -> None:
        """Start an interactive game session with simplified controls."""
        print("=== ENHANCED MAZE GAME ===")
        
        if not self.start_game():
            print("Failed to start game!")
            return
        
        print("🎯 OBJECTIVE: Find the exit (E) to win!")
        self._print_controls()
        self.print_maze_ascii()
        
        self._game_loop()

    def _print_controls(self) -> None:
        """Print game controls."""
        print("\nControls:")
        print("  w/a/s/d - Move (up/left/down/right)")
        print("  m - Show ASCII map")
        print("  v - Show visual plot")
        print("  h - Show hint (valid moves)")
        print("  i - Show game info")
        print("  q - Quit game")

    def _game_loop(self) -> None:
        """Main game loop."""
        while self.is_playing and not self.game_over:
            try:
                command = input("\nEnter command: ").lower().strip()
                
                if not self._process_command(command):
                    break
                    
            except KeyboardInterrupt:
                print("\nGame interrupted!")
                break
            except Exception as e:
                logging.error(f"Error in game loop: {e}")
                print(f"Error: {e}")

    def _process_command(self, command: str) -> bool:
        """
        Process a game command.
        
        Args:
            command: User input command
            
        Returns:
            True to continue game loop, False to exit
        """
        if command == 'q':
            print("Thanks for playing!")
            return False
        
        elif command == 'v':
            self.visualize(block=True)
            
        elif command == 'm':
            self.print_maze_ascii()
            
        elif command == 'h':
            self._show_hint()
            
        elif command == 'i':
            self._show_game_info()
            
        elif command in ['w', 'a', 's', 'd']:
            self._handle_move_command(command)
            
        else:
            print("Invalid command! Use w/a/s/d to move, or h for help.")
        
        return True

    def _handle_move_command(self, direction: str) -> None:
        """Handle movement command."""
        if self.move_player(direction):
            self.print_maze_ascii()
            
            if self.game_won:
                self._handle_game_completion()
        else:
            print("Move blocked! Try a different direction.")

    def _handle_game_completion(self) -> None:
        """Handle game completion."""
        print("\n🎊 GAME OVER - YOU WON! 🎊")
        print("Type 'v' to see the final maze, 'i' for stats, or 'q' to quit.")
        
        while True:
            try:
                final_input = input("Final command (v/i/q): ").lower().strip()
                if final_input == 'v':
                    self.visualize(block=True)
                elif final_input == 'i':
                    self._show_game_info()
                elif final_input == 'q':
                    break
                else:
                    print("Invalid command! Use v/i/q.")
            except KeyboardInterrupt:
                break

    def _show_hint(self) -> None:
        """Show movement hints."""
        valid_moves = self.get_move_suggestions()
        if valid_moves:
            directions = {'w': 'up', 'a': 'left', 's': 'down', 'd': 'right'}
            hints = [f"{move} ({directions[move]})" for move in valid_moves]
            print(f"💡 Valid moves: {', '.join(hints)}")
        else:
            print("❌ No valid moves available!")

    def _show_game_info(self) -> None:
        """Show detailed game information."""
        info = self.get_game_info()
        print("\n📊 GAME STATISTICS:")
        print(f"   Moves: {info['moves_count']}")
        print(f"   Path length: {info['path_length']}")
        
        if info['game_duration']:
            print(f"   Time: {info['game_duration']:.1f} seconds")
        
        if info['player_position'] and info['exit_position']:
            distance = self._calculate_distance(info['player_position'], info['exit_position'])
            print(f"   Distance to exit: {distance} steps")
        
        print(f"   Maze size: {info['maze_dimensions'][0]}x{info['maze_dimensions'][1]}")


# Convenience functions and demo
def create_simple_maze_game(maze: List[List[int]]) -> MazeGame:
    """
    Create a simple maze game instance.
    
    Args:
        maze: 2D list representing the maze
        
    Returns:
        Configured MazeGame instance
    """
    game = MazeGame(maze)
    return game


def demo_game() -> None:
    """Demo the enhanced maze game."""
    # Create a simple test maze
    test_maze = [
        [0, -1, 0, 0, 0],
        [0, -1, 0, -1, 0],
        [0, 0, 0, -1, 0],
        [-1, -1, 0, 0, 0],
        [0, 0, 0, -1, 0]
    ]
    
    game = create_simple_maze_game(test_maze)
    game.play_interactive()


def main() -> None:
    """Main entry point for demonstration."""
    demo_game()


if __name__ == "__main__":
    main()
 
    
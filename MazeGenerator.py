import random
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
from datetime import datetime
import json
from pathlib import Path
from MazeConfig import MazeConfig,Direction

class MazeGenerator():
    """Advanced maze generator using probabilistic algorithms with room generation."""
    
    def __init__(self, config=None):
        self.config = config or MazeConfig()
        # Cache cell values for performance
        self._cell_values = {
            'UNVISITED': self.config.get_cell_value(self.config.cell_types.UNVISITED),
            'ROOM': self.config.get_cell_value(self.config.cell_types.ROOM),
            'WALL': self.config.get_cell_value(self.config.cell_types.WALL)
        }
        
        # Initialize maze with unvisited cells
        unvisited_value = self._cell_values['UNVISITED']
        self.maze = [[unvisited_value for _ in range(self.config.maze_width)] 
                     for _ in range(self.config.maze_height)]
        self.stats = {"rooms": 0, "walls": 0, "room_percentage": 0.0}
        
        # Cache direction values for performance
        self._directions = list(Direction)
        self._direction_weights = [self.config.direction_weights[d.name] for d in self._directions]
        
    def in_bounds(self, x, y):
        """Check if coordinates are within maze bounds."""
        return 0 <= x < self.config.maze_height and 0 <= y < self.config.maze_width

    def weighted_shuffle(self, items, weights):
        """Efficiently shuffle items based on weights using inverse transform sampling."""
        weighted_items = [
            (random.random() ** (1 / weight), item)
            for item, weight in zip(items, weights)
        ]
        weighted_items.sort(key=lambda x: x[0])
        return [item for _, item in weighted_items]

    def get_weighted_directions(self):
        """Get directions shuffled by weights (cached for performance)."""
        shuffled = self.weighted_shuffle(self._directions, self._direction_weights)
        if self.config.enable_debug:
            print(f"  [DIR ORDER] {', '.join(d.name for d in shuffled)}")
        return shuffled

    def get_unvisited_neighbors(self, x, y):
        """Get unvisited neighboring cells in weighted order."""
        ordered_dirs = self.get_weighted_directions()
        neighbors = []
        unvisited_value = self._cell_values['UNVISITED']
        
        for direction in ordered_dirs:
            dx, dy = direction.value
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny) and self.maze[nx][ny] == unvisited_value:
                neighbors.append((nx, ny))
        
        if self.config.enable_debug:
            print(f"  [NEIGHBORS] From ({x}, {y}) found {len(neighbors)} unvisited: {neighbors}")
        return neighbors

    def count_adjacent_rooms(self, x, y):
        """Count adjacent rooms around a cell (optimized)."""
        count = -1
        room_value = self._cell_values['ROOM']
        
        for direction in self._directions:
            dx, dy = direction.value
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny) and self.maze[nx][ny] == room_value:
                count += 1
        return count

    def get_room_neighbors(self, x, y):
        """Get all neighboring room cells (optimized)."""
        room_value = self._cell_values['ROOM']
        neighbors = []
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny) and self.maze[nx][ny] == room_value:
                neighbors.append((nx, ny))
        return neighbors

    def mark_region(self, start, neighbors, seen):
        """Mark connected regions using BFS."""
        queue_bfs = [start]
        seen.add(start)
        while queue_bfs:
            cx, cy = queue_bfs.pop(0)  # Use pop(0) for proper BFS
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                tx, ty = cx + dx, cy + dy
                if (tx, ty) in neighbors and (tx, ty) not in seen:
                    seen.add((tx, ty))
                    queue_bfs.append((tx, ty))

    def count_room_regions_around(self, x, y):
        """Count number of separate room regions around a cell."""
        neighbors = set(self.get_room_neighbors(x, y))
        seen = set()
        regions = 0
        for pos in neighbors:
            if pos not in seen:
                self.mark_region(pos, neighbors, seen)
                regions += 1
        return regions

    def calculate_room_probability(self, x, y, neighbor_index, total_neighbors):
        """Calculate the probability of creating a room at given coordinates."""
        base_prob = (neighbor_index + 1) / total_neighbors if total_neighbors > 0 else self.config.base_prob_factor
        decay = self.config.decay_factor * self.count_adjacent_rooms(x, y)
        return max(self.config.min_room_prob, base_prob - decay)
    
    def should_create_room(self, x, y, room_prob):
        """Determine if a room should be created based on probability and region constraints."""
        rand_val = random.random()
        region_count = self.count_room_regions_around(x, y)
        return region_count <= 1 and rand_val < room_prob
    
    def process_neighbor(self, nx, ny, neighbor_index, total_neighbors, queue):
        """Process a single neighbor during maze generation."""
        room_prob = self.calculate_room_probability(nx, ny, neighbor_index, total_neighbors)
        
        if self.should_create_room(nx, ny, room_prob):
            self.maze[nx][ny] = self._cell_values['ROOM']
            self.stats["rooms"] += 1
            queue.append((nx, ny))
            if self.config.enable_debug:
                print(f"       ✅ Room created at ({nx}, {ny}), added to queue.")
        else:
            self.maze[nx][ny] = self._cell_values['WALL']
            self.stats["walls"] += 1
            if self.config.enable_debug:
                print(f"       ❌ Marked as WALL at ({nx}, {ny})")
    
    def finalize_maze(self):
        """Convert remaining unvisited cells to walls."""
        unvisited_value = self._cell_values['UNVISITED']
        wall_value = self._cell_values['WALL']
        
        for i in range(self.config.maze_height):
            for j in range(self.config.maze_width):
                if self.maze[i][j] == unvisited_value:
                    self.maze[i][j] = wall_value
                    self.stats["walls"] += 1

    def generate(self, start_x=None, start_y=None):
        """Generate the maze using probabilistic algorithm."""
        # Initialize starting position
        if start_x is None:
            start_x = random.randint(0, self.config.maze_height - 1)
        if start_y is None:
            start_y = random.randint(0, self.config.maze_width - 1)
            
        room_value = self._cell_values['ROOM']
        
        self.maze[start_x][start_y] = room_value
        self.stats["rooms"] += 1
        queue = [(start_x, start_y)]
        
        if self.config.enable_debug:
            print(f"[START] Starting maze generation at ({start_x}, {start_y})")

        steps = 0
        while queue:
            x, y = queue.pop(0)
            if self.config.enable_debug:
                print(f"\n[STEP {steps}] Visiting ({x}, {y})")
            steps += 1

            neighbors = self.get_unvisited_neighbors(x, y)
            total_neighbors = len(neighbors)

            for i, (nx, ny) in enumerate(neighbors):
                if self.config.enable_debug:
                    room_prob = self.calculate_room_probability(nx, ny, i, total_neighbors)
                    rand_val = random.random()
                    region_count = self.count_room_regions_around(nx, ny)
                    decay = self.config.decay_factor * self.count_adjacent_rooms(nx, ny)
                    base_prob = (i+1) / total_neighbors if total_neighbors > 0 else self.config.base_prob_factor
                    
                    print(f"    -> Neighbor ({nx}, {ny}): base_prob={base_prob:.2f}, "
                          f"decay={decay:.2f}, room_prob={room_prob:.2f}, "
                          f"rand={rand_val:.2f}, regions={region_count}")
                
                self.process_neighbor(nx, ny, i, total_neighbors, queue)
        
        self.finalize_maze()

    def visualize(self):
        """Create an optimized visualization of the maze."""
        # Use dynamic colormap based on actual cell values
        room_val = self._cell_values['ROOM']
        wall_val = self._cell_values['WALL']
        
        # Create colormap: Room=white, Wall=black
        colors = ['white', 'black']
        custom_cmap = ListedColormap(colors)

        plt.figure(figsize=(12, 8))
        plt.imshow(self.maze, cmap=custom_cmap, origin='upper', 
                  vmin=min(room_val, wall_val), vmax=max(room_val, wall_val))
        
        plt.title("Maze Game", fontsize=16)

        # Create optimized legend
        legend_elements = [
            Rectangle((0, 0), 1, 1, facecolor='white', edgecolor='black', 
                     label=f'Room ({room_val})'),
            Rectangle((0, 0), 1, 1, facecolor='black', edgecolor='black', 
                     label=f'Wall ({wall_val})')
        ]

        plt.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1, 0.5), 
                  fontsize=12, frameon=True, fancybox=True, shadow=True)
        plt.axis('off')
        plt.tight_layout()
        plt.show()

    def save_maze(self, folder_name="mazes"):
        """Save the maze to files with optimized structure."""
        base_path = Path(folder_name)
        base_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        json_path = base_path / "json"
        imgs_path = base_path / "imgs"
        json_path.mkdir(exist_ok=True)
        imgs_path.mkdir(exist_ok=True)
        
        # Generate optimized filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        size_str = f"{self.config.maze_height}x{self.config.maze_width}"
        filename = f"maze_{size_str}_{timestamp}"
        
        # Calculate room percentage for statistics
        total_cells = self.config.maze_height * self.config.maze_width
        self.stats["room_percentage"] = (self.stats["rooms"] / total_cells) * 100 if total_cells > 0 else 0.0
        
        # Optimized maze data structure
        maze_data = {
            "metadata": {
                "timestamp": timestamp,
                "version": "2.0",
                "generator": "MazeGenerator"
            },
            "dimensions": {
                "height": self.config.maze_height, 
                "width": self.config.maze_width
            },
            "config": {
                "decay_factor": self.config.decay_factor,
                "base_prob_factor": self.config.base_prob_factor,
                "min_room_prob": self.config.min_room_prob,
                "direction_weights": self.config.direction_weights
            },
            "maze": self.maze,
            "statistics": self.stats
        }

        # Save JSON with error handling
        json_file = json_path / f"{filename}.json"
        try:
            with json_file.open('w', encoding='utf-8') as f:
                json.dump(maze_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return None
        
        # Save optimized image
        self._save_maze_image(imgs_path, filename)
        
        print("\n[SAVE] Maze saved successfully:")
        print(f"  📄 {json_file} (Data)")
        print(f"  🖼️ {imgs_path / f'{filename}.png'} (Image)")
        print(f"  📊 Room coverage: {self.stats['room_percentage']:.1f}%")

        return filename

    def _save_maze_image(self, folder_path, filename):
        """Save optimized maze visualization as a 200x200 PNG image."""
        room_val = self._cell_values['ROOM']
        wall_val = self._cell_values['WALL']
        unvisited_val = self._cell_values['UNVISITED']
        
        colors = ['gray', 'white', 'black']  # Handles all possible values
        custom_cmap = ListedColormap(colors)

        # Optimized figure creation
        dpi = 100
        figsize_inches = (2, 2)  # 200px at 100dpi

        fig, ax = plt.subplots(figsize=figsize_inches, dpi=dpi)
        
        # Dynamic value range
        min_val = min(room_val, wall_val, unvisited_val)
        max_val = max(room_val, wall_val, unvisited_val)
        
        ax.imshow(self.maze, cmap=custom_cmap, origin='upper', vmin=min_val, vmax=max_val)
        ax.axis('off')
        
        # Remove all padding for clean output
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        # Save with error handling
        output_path = Path(folder_path) / f"{filename}.png"
        try:
            fig.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
        except Exception as e:
            print(f"Error saving image: {e}")
        finally:
            plt.close(fig)



    def print_statistics(self):
        """Print comprehensive maze statistics."""
        total_cells = self.config.maze_height * self.config.maze_width
        room_percentage = (self.stats["rooms"] / total_cells) * 100 if total_cells > 0 else 0.0
        
        print("\n" + "="*50)
        print("           MAZE GENERATION SUMMARY")
        print("="*50)
        print(f"📏 Dimensions:     {self.config.maze_height} × {self.config.maze_width} ({total_cells:,} cells)")
        print(f"🏠 Rooms:          {self.stats['rooms']:,}")
        print(f"🧱 Walls:          {self.stats['walls']:,}")
        print(f"📊 Room Coverage:  {room_percentage:.1f}%")
        print("⚙️  Algorithm:      Probabilistic with region constraints")
        print("="*50)


def main():
    """Optimized main function to demonstrate maze generation."""
    print("🎮 ADVANCED MAZE GENERATOR")
    print("=" * 40)
    
    try:
        # Create and configure the maze generator
        generator = MazeGenerator()
        
        print("🔧 Generating maze...")
        # Generate maze
        generator.generate()
        
        # Show comprehensive statistics
        generator.print_statistics()
        
        # Save the maze with improved feedback
        print("\n💾 Saving maze files...")
        saved_filename = generator.save_maze()
        
        if saved_filename:
            print(f"✅ Maze '{saved_filename}' generated successfully!")
            
            # Show final visualization
            print("\n🖼️  Opening visualization...")
            generator.visualize()
        else:
            print("❌ Failed to save maze.")
            
    except Exception as e:
        print(f"❌ Error during maze generation: {e}")
        raise


if __name__ == "__main__":
    main()

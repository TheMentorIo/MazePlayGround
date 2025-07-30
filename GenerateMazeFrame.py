"""
Generate Maze Frame for the Maze Playground Application.
Provides a comprehensive interface for maze generation with various parameters.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Optional, Callable, Any
import threading
import time

from MazeGenerator import MazeGenerator
from MazeConfig import MazeConfig
from AppConfig import AppConfig
from AppUtilities import validate_input, handle_errors


class GenerateMazeFrame(ttk.Frame):
    """
    Frame for generating mazes with customizable parameters.
    
    Features:
    - Intuitive parameter controls
    - Real-time validation
    - Progress tracking
    - Preset configurations
    - Advanced options
    """
    
    # Direction constants
    DIRECTION_NAMES = ["RIGHT", "LEFT", "UP", "DOWN"]
    DIRECTION_OPPOSITES = {
        "RIGHT": "LEFT",
        "LEFT": "RIGHT",
        "UP": "DOWN",
        "DOWN": "UP"
    }
    
    # Default values
    DEFAULT_VALUES = {
        "width": 20,
        "height": 20,
        "decay_factor": 0.25,
        "base_prob_factor": 0.25,
        "min_room_prob": 0.05,
        "direction_weights": 0.25
    }
    
    # Presets for quick generation
    PRESETS = {
        "Small & Simple": {
            "width": 5, "height": 5,
            "decay_factor": 0.3, "base_prob_factor": 0.3,
            "min_room_prob": 0.1
        },
        "Medium Balanced": {
            "width": 10, "height": 10,
            "decay_factor": 0.25, "base_prob_factor": 0.25,
            "min_room_prob": 0.05
        },
        "Large Complex": {
            "width": 20, "height": 20,
            "decay_factor": 0.2, "base_prob_factor": 0.2,
            "min_room_prob": 0.03
        },
        "Narrow Corridors": {
            "width": 25, "height": 25,
            "decay_factor": 0.15, "base_prob_factor": 0.15,
            "min_room_prob": 0.02
        }
    }

    def __init__(self, parent: tk.Widget, controller):
        """
        Initialize the Generate Maze frame.
        
        Args:
            parent: Parent widget
            controller: Main application controller
        """
        super().__init__(parent, padding=20)
        self.controller = controller
        self.config = AppConfig()
        
        # State variables
        self.updating_weights = False
        self.direction_vars: Dict[str, tk.StringVar] = {}
        self.is_generating = False
        self.current_generator: Optional[MazeGenerator] = None
        
        # Create UI components
        self.create_header()
        self.create_presets_section()
        self.create_basic_parameters()
        self.create_direction_weights()
        self.create_advanced_options()
        self.create_generation_controls()
        self.create_status_section()
        
        # Initialize with default values
        self.load_preset("Medium Balanced")
        
        logging.debug("GenerateMazeFrame initialized successfully")

    def create_header(self) -> None:
        """Create the header section with title and description."""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="🎲 Maze Generator",
            font=("Arial", 18, "bold")
        )
        title_label.pack()
        
        # Description
        desc_label = ttk.Label(
            header_frame,
            text="Create custom mazes with adjustable parameters",
            font=("Arial", 10),
            foreground="gray"
        )
        desc_label.pack(pady=(5, 0))

    def create_presets_section(self) -> None:
        """Create the presets selection section."""
        presets_frame = ttk.LabelFrame(self, text="Quick Presets", padding=10)
        presets_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Preset buttons
        buttons_frame = ttk.Frame(presets_frame)
        buttons_frame.pack(fill=tk.X)
        
        for i, preset_name in enumerate(self.PRESETS.keys()):
            btn = ttk.Button(
                buttons_frame,
                text=preset_name,
                command=lambda name=preset_name: self.load_preset(name)
            )
            btn.grid(row=i//2, column=i%2, padx=5, pady=2, sticky="ew")
        
        # Configure grid weights
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)

    def create_basic_parameters(self) -> None:
        """Create basic parameter controls."""
        basic_frame = ttk.LabelFrame(self, text="Maze Dimensions", padding=10)
        basic_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create grid layout
        params = [
            ("Width:", "width", 5, 100, "cells"),
            ("Height:", "height", 5, 100, "cells")
        ]
        
        for i, (label, key, min_val, max_val, unit) in enumerate(params):
            # Label
            ttk.Label(basic_frame, text=label).grid(row=i, column=0, sticky="w", padx=(0, 10))
            
            # Spinbox
            var = tk.StringVar(value=str(self.DEFAULT_VALUES[key]))
            spinbox = ttk.Spinbox(
                basic_frame,
                from_=min_val,
                to=max_val,
                textvariable=var,
                width=10,
                validate="key",
                validatecommand=(self.register(self._validate_integer), "%P")
            )
            spinbox.grid(row=i, column=1, padx=5)
            setattr(self, f"{key}_var", var)
            
            # Unit label
            ttk.Label(basic_frame, text=unit, foreground="gray").grid(row=i, column=2, sticky="w")

    def create_direction_weights(self) -> None:
        """Create direction weight controls."""
        weights_frame = ttk.LabelFrame(self, text="Direction Weights", padding=10)
        weights_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Info label
        info_label = ttk.Label(
            weights_frame,
            text="Adjust the probability of maze expansion in each direction",
            font=("Arial", 9),
            foreground="gray"
        )
        info_label.pack(pady=(0, 10))
        
        # Direction controls
        directions_grid = ttk.Frame(weights_frame)
        directions_grid.pack()
        
        for i, direction in enumerate(self.DIRECTION_NAMES):
            # Direction label with icon
            icons = {"RIGHT": "→", "DOWN": "↓", "LEFT": "←", "UP": "↑"}
            label_text = f"{icons[direction]} {direction}"
            
            ttk.Label(directions_grid, text=label_text).grid(row=i//2, column=(i%2)*3, sticky="w", padx=5)
            
            # Weight spinbox
            var = tk.StringVar(value=str(self.DEFAULT_VALUES["direction_weights"]))
            spinbox = ttk.Spinbox(
                directions_grid,
                from_=0.01,
                to=0.50,
                increment=0.01,
                textvariable=var,
                width=8,
                validate="key",
                validatecommand=(self.register(self._validate_float), "%P")
            )
            spinbox.grid(row=i//2, column=(i%2)*3+1, padx=5)
            
            # Bind change event
            var.trace_add("write", lambda *args, d=direction: self._on_weight_change(d))
            self.direction_vars[direction] = var
        
        # Balance button
        balance_btn = ttk.Button(
            weights_frame,
            text="⚖️ Auto Balance",
            command=self.balance_weights
        )
        balance_btn.pack(pady=(10, 0))

    def create_advanced_options(self) -> None:
        """Create advanced parameter controls."""
        advanced_frame = ttk.LabelFrame(self, text="Advanced Parameters", padding=10)
        advanced_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Advanced parameters
        params = [
            ("Decay Factor:", "decay_factor", 0.0, 1.0, 0.01, "Controls maze complexity reduction"),
            ("Base Probability:", "base_prob_factor", 0.0, 1.0, 0.01, "Base expansion probability"),
            ("Min Room Probability:", "min_room_prob", 0.0, 0.5, 0.01, "Minimum room generation chance")
        ]
        
        for i, (label, key, min_val, max_val, increment, tooltip) in enumerate(params):
            # Label
            label_widget = ttk.Label(advanced_frame, text=label)
            label_widget.grid(row=i, column=0, sticky="w", padx=(0, 10))
            
            # Spinbox
            var = tk.StringVar(value=str(self.DEFAULT_VALUES[key]))
            spinbox = ttk.Spinbox(
                advanced_frame,
                from_=min_val,
                to=max_val,
                increment=increment,
                textvariable=var,
                width=10,
                validate="key",
                validatecommand=(self.register(self._validate_float), "%P")
            )
            spinbox.grid(row=i, column=1, padx=5)
            setattr(self, f"{key}_var", var)
            
            # Help button with tooltip
            help_btn = ttk.Button(
                advanced_frame,
                text="?",
                width=3,
                command=lambda msg=tooltip: messagebox.showinfo("Parameter Help", msg)
            )
            help_btn.grid(row=i, column=2)

    def create_generation_controls(self) -> None:
        """Create generation control buttons."""
        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Generate button
        self.generate_btn = ttk.Button(
            controls_frame,
            text="🎲 Generate Maze",
            command=self.generate_async,
            style="Large.TButton"
        )
        self.generate_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Additional controls
        additional_frame = ttk.Frame(controls_frame)
        additional_frame.pack(side=tk.RIGHT)
        
        # Preview button
        preview_btn = ttk.Button(
            additional_frame,
            text="👁️ Preview",
            command=self.quick_preview
        )
        preview_btn.pack(side=tk.LEFT, padx=2)
        
        # Save settings button
        save_btn = ttk.Button(
            additional_frame,
            text="💾 Save Settings",
            command=self.save_settings
        )
        save_btn.pack(side=tk.LEFT, padx=2)

    def create_status_section(self) -> None:
        """Create status and result display section."""
        status_frame = ttk.LabelFrame(self, text="Status", padding=10)
        status_frame.pack(fill=tk.X)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=300
        )
        
        # Status label
        self.status_label = ttk.Label(
            status_frame,
            text="Ready to generate maze",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=(0, 5))
        
        # Result label
        self.result_label = ttk.Label(
            status_frame,
            text="Configure parameters and click Generate Maze",
            font=("Arial", 9),
            foreground="gray"
        )
        self.result_label.pack()

    def _validate_integer(self, value: str) -> bool:
        """Validate integer input."""
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False

    def _validate_float(self, value: str) -> bool:
        """Validate float input."""
        if value == "" or value == ".":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _on_weight_change(self, direction: str) -> None:
        """Handle direction weight changes with auto-balancing."""
        if self.updating_weights:
            return
        
        try:
            # Get opposite direction
            opposite = self.DIRECTION_OPPOSITES[direction]
            
            # Calculate current total
            current_total = sum(
                float(self.direction_vars[d].get()) 
                for d in self.DIRECTION_NAMES
            )
            
            # If total exceeds 1.0, adjust opposite direction
            if current_total > 1.0:
                overflow = current_total - 1.0
                opposite_value = float(self.direction_vars[opposite].get())
                new_opposite_value = max(0.01, opposite_value - overflow)
                
                self.updating_weights = True
                self.direction_vars[opposite].set(f"{new_opposite_value:.2f}")
                self.updating_weights = False
                
        except (ValueError, KeyError) as e:
            logging.warning(f"Error in weight change handling: {e}")

    def balance_weights(self) -> None:
        """Auto-balance all direction weights to sum to 1.0."""
        try:
            self.updating_weights = True
            balanced_value = 1.0 / len(self.DIRECTION_NAMES)
            
            for direction in self.DIRECTION_NAMES:
                self.direction_vars[direction].set(f"{balanced_value:.2f}")
                
        finally:
            self.updating_weights = False

    def load_preset(self, preset_name: str) -> None:
        """
        Load a preset configuration.
        
        Args:
            preset_name: Name of the preset to load
        """
        if preset_name not in self.PRESETS:
            return
        
        preset = self.PRESETS[preset_name]
        
        # Load basic parameters
        for key, value in preset.items():
            if hasattr(self, f"{key}_var"):
                getattr(self, f"{key}_var").set(str(value))
        
        # Balance direction weights
        self.balance_weights()
        
        self.status_label.config(text=f"Loaded preset: {preset_name}")

    @handle_errors(show_dialog=True)
    def generate_async(self) -> None:
        """Generate maze asynchronously to prevent UI blocking."""
        if self.is_generating:
            messagebox.showwarning("Warning", "Maze generation already in progress!")
            return
        
        # Validate inputs
        if not self.validate_all_inputs():
            return
        
        # Start generation in background thread
        thread = threading.Thread(target=self.generate_maze_background, daemon=True)
        thread.start()

    def generate_maze_background(self) -> None:
        """Background maze generation process."""
        try:
            self.is_generating = True
            self.update_ui_generating(True)
            
            # Create configuration
            config = self.create_maze_config()
            
            # Update status
            self.after(0, lambda: self.status_label.config(text="Initializing generator..."))
            
            # Create generator
            self.current_generator = MazeGenerator(config)
            
            # Generate maze
            self.after(0, lambda: self.status_label.config(text="Generating maze..."))
            start_time = time.time()
            
            self.current_generator.generate()
            
            generation_time = time.time() - start_time
            
            # Save maze
            self.after(0, lambda: self.status_label.config(text="Saving maze..."))
            filename = self.current_generator.save_maze()
            
            # Update UI on main thread
            self.after(0, lambda: self.on_generation_complete(filename, generation_time))
            
        except Exception as e:
            logging.error(f"Error in maze generation: {e}")
            self.after(0, lambda: self.on_generation_error(str(e)))
        finally:
            self.is_generating = False
            self.after(0, lambda: self.update_ui_generating(False))

    def create_maze_config(self) -> MazeConfig:
        """Create MazeConfig from current UI values."""
        return MazeConfig(
            decay_factor=float(self.decay_factor_var.get()),
            base_prob_factor=float(self.base_prob_factor_var.get()),
            min_room_prob=float(self.min_room_prob_var.get()),
            maze_width=int(self.width_var.get()),
            maze_height=int(self.height_var.get()),
            direction_weights={
                d: float(self.direction_vars[d].get()) 
                for d in self.DIRECTION_NAMES
            },
            enable_debug=False
        )

    def validate_all_inputs(self) -> bool:
        """Validate all input parameters."""
        try:
            # Check basic parameters
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            
            if width < 5 or height < 5:
                messagebox.showerror("Invalid Input", "Maze dimensions must be at least 5x5")
                return False
            
            if width > 100 or height > 100:
                messagebox.showerror("Invalid Input", "Maze dimensions cannot exceed 100x100")
                return False
            
            # Check direction weights
            total_weight = sum(float(self.direction_vars[d].get()) for d in self.DIRECTION_NAMES)
            if abs(total_weight - 1.0) > 0.01:
                messagebox.showwarning("Weight Warning", f"Direction weights sum to {total_weight:.2f}, should sum to 1.0")
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your input values: {e}")
            return False

    def update_ui_generating(self, generating: bool) -> None:
        """Update UI state during generation."""
        if generating:
            self.generate_btn.config(text="🔄 Generating...", state="disabled")
            self.progress_bar.pack(pady=(5, 0))
            self.progress_bar.start(10)
        else:
            self.generate_btn.config(text="🎲 Generate Maze", state="normal")
            self.progress_bar.stop()
            self.progress_bar.pack_forget()

    def on_generation_complete(self, filename: str, generation_time: float) -> None:
        """Handle successful maze generation."""
        self.status_label.config(text=f"Maze generated successfully! ({generation_time:.2f}s)")
        self.controller.frame_manager.frames["ViewMazesPage"].refresh()  # Refresh the view frame to show new maze
        self.result_label.config(
            text=f"✅ Saved as: {filename}",
            foreground="green"
        )
        
        # Show success message with options
        result = messagebox.askyesno(
            "Maze Generated",
            f"Maze generated successfully in {generation_time:.2f} seconds!\n\n"
            f"File: {filename}\n\n"
            "Would you like to view the saved mazes?"
        )
        
        if result:
            self.controller.show_frame("ViewMazesPage")

    def on_generation_error(self, error_message: str) -> None:
        """Handle maze generation errors."""
        self.status_label.config(text="Generation failed!")
        self.result_label.config(
            text=f"❌ Error: {error_message}",
            foreground="red"
        )
        messagebox.showerror("Generation Error", f"Failed to generate maze:\n{error_message}")

    def quick_preview(self) -> None:
        """Generate a quick preview of the maze parameters."""
        try:
            config = self.create_maze_config()
            preview_info = f"""
Maze Preview Settings:
━━━━━━━━━━━━━━━━━━━━━

📏 Dimensions: {config.maze_width} × {config.maze_height}
📊 Total Cells: {config.maze_width * config.maze_height:,}

🎛️ Parameters:
• Decay Factor: {config.decay_factor}
• Base Probability: {config.base_prob_factor}  
• Min Room Probability: {config.min_room_prob}

🧭 Direction Weights:
• Right: {config.direction_weights['RIGHT']:.2f}
• Down: {config.direction_weights['DOWN']:.2f}
• Left: {config.direction_weights['LEFT']:.2f}
• Up: {config.direction_weights['UP']:.2f}

Estimated generation time: {self.estimate_generation_time(config)} seconds
"""
            messagebox.showinfo("Maze Preview", preview_info)
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error creating preview: {e}")

    def estimate_generation_time(self, config: MazeConfig) -> str:
        """Estimate maze generation time based on parameters."""
        cells = config.maze_width * config.maze_height
        if cells < 500:
            return "< 1"
        elif cells < 2000:
            return "1-3"
        elif cells < 5000:
            return "3-10"
        else:
            return "10+"

    def save_settings(self) -> None:
        """Save current settings as a custom preset."""
        # This could be implemented to save settings to a file
        messagebox.showinfo("Save Settings", "Settings save functionality coming soon!")

    def refresh(self) -> None:
        """Refresh the frame (called when shown)."""
        if not self.is_generating:
            self.status_label.config(text="Ready to generate maze")
        logging.debug("GenerateMazeFrame refreshed")

    def on_show(self, **kwargs) -> None:
        """Called when the frame is shown."""
        self.refresh()
        logging.debug("GenerateMazeFrame shown")


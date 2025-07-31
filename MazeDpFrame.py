import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional
import logging
from GameArea import GameArea
from MazeDP import MazeDP


class MazeDpFrame(ttk.Frame):
    """
    Dynamic Programming frame for maze solving algorithms.
    Provides UI for running value iteration and policy iteration with visualization.
    """
    
    # Constants
    DEFAULT_REWARD_INFO = "Default: Encourage shortest path"
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # DP algorithm instance
        self.maze_dp: Optional[MazeDP] = None
        self.current_maze: Optional[np.ndarray] = None
        
        # Algorithm parameters
        self.gamma = tk.DoubleVar(value=0.9)
        self.max_iterations = tk.IntVar(value=100)
        self.theta = tk.DoubleVar(value=0.0001)
        
        # Reward parameters
        self.step_reward = tk.DoubleVar(value=-0.04)
        self.goal_reward = tk.DoubleVar(value=10.0)
        self.wall_reward = tk.DoubleVar(value=0.0)
        self.custom_rewards = {}  # For custom cell rewards
        
        # Algorithm state
        self.is_running = False
        self.current_iteration = 0
        
        # UI components
        self.game_area: Optional[GameArea] = None
        self.result_text: Optional[tk.Text] = None
        self.convergence_plot = None
        
        # Build UI
        self._create_header()
        self._create_parameters()
        self._create_rewards()
        self._create_controls()
        self._create_game_area()
        self._create_results()
        
        logging.debug("MazeDpFrame initialized successfully")
    
    def _create_header(self) -> None:
        """Create the header with title and info."""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="🧠 Dynamic Programming Solver",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Info
        info_label = ttk.Label(
            header_frame,
            text="Solve mazes using Value Iteration and Policy Iteration",
            font=("Arial", 10),
            foreground="gray"
        )
        info_label.pack(side=tk.RIGHT)
    
    def _create_parameters(self) -> None:
        """Create parameter configuration controls."""
        params_frame = ttk.LabelFrame(self, text="Algorithm Parameters", padding=10)
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Gamma (discount factor)
        ttk.Label(params_frame, text="Discount Factor (γ):").grid(row=0, column=0, sticky="w", padx=(0, 5))
        gamma_spin = ttk.Spinbox(
            params_frame,
            from_=0.1, to=1.0, increment=0.1,
            textvariable=self.gamma,
            width=10, format="%.1f"
        )
        gamma_spin.grid(row=0, column=1, padx=(0, 15))
        
        # Max iterations
        ttk.Label(params_frame, text="Max Iterations:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        iter_spin = ttk.Spinbox(
            params_frame,
            from_=10, to=1000, increment=10,
            textvariable=self.max_iterations,
            width=10
        )
        iter_spin.grid(row=0, column=3, padx=(0, 15))
        
        # Convergence threshold
        ttk.Label(params_frame, text="Convergence Threshold (θ):").grid(row=0, column=4, sticky="w", padx=(0, 5))
        theta_spin = ttk.Spinbox(
            params_frame,
            from_=0.0001, to=0.1, increment=0.0001,
            textvariable=self.theta,
            width=10, format="%.4f"
        )
        theta_spin.grid(row=0, column=5)
    
    def _create_rewards(self) -> None:
        """Create reward configuration controls."""
        rewards_frame = ttk.LabelFrame(self, text="Reward Configuration", padding=10)
        rewards_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Basic rewards row 1
        row1_frame = ttk.Frame(rewards_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Step reward
        ttk.Label(row1_frame, text="Step Reward:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        step_spin = ttk.Spinbox(
            row1_frame,
            from_=-1.0, to=0.0, increment=0.01,
            textvariable=self.step_reward,
            width=10, format="%.3f"
        )
        step_spin.grid(row=0, column=1, padx=(0, 15))
        
        # Goal reward
        ttk.Label(row1_frame, text="Goal Reward:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        goal_spin = ttk.Spinbox(
            row1_frame,
            from_=1.0, to=100.0, increment=1.0,
            textvariable=self.goal_reward,
            width=10, format="%.1f"
        )
        goal_spin.grid(row=0, column=3, padx=(0, 15))
        
        # Wall reward
        ttk.Label(row1_frame, text="Wall Reward:").grid(row=0, column=4, sticky="w", padx=(0, 5))
        wall_spin = ttk.Spinbox(
            row1_frame,
            from_=-10.0, to=10.0, increment=0.1,
            textvariable=self.wall_reward,
            width=10, format="%.1f"
        )
        wall_spin.grid(row=0, column=5)
        
        # Reward presets row 2
        row2_frame = ttk.Frame(rewards_frame)
        row2_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(row2_frame, text="Presets:").pack(side=tk.LEFT, padx=(0, 10))
        
        # Preset buttons
        presets = [
            ("🚀 Fast Path", self._preset_fast_path),
            ("🐌 Careful", self._preset_careful),
            ("⚖️ Balanced", self._preset_balanced),
            ("🎯 Goal Focused", self._preset_goal_focused),
            ("💥 Risky", self._preset_risky)
        ]
        
        for text, command in presets:
            ttk.Button(
                row2_frame,
                text=text,
                command=command,
                width=12
            ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Custom reward modification
        row3_frame = ttk.Frame(rewards_frame)
        row3_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            row3_frame,
            text="🎨 Custom Rewards",
            command=self._open_custom_rewards,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            row3_frame,
            text="🔄 Reset Rewards",
            command=self._reset_rewards,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Reward info
        self.reward_info_label = ttk.Label(
            row3_frame,
            text=self.DEFAULT_REWARD_INFO,
            foreground="gray",
            font=("Arial", 9)
        )
        self.reward_info_label.pack(side=tk.RIGHT)
    
    def _create_controls(self) -> None:
        """Create algorithm control buttons."""
        controls_frame = ttk.LabelFrame(self, text="Algorithm Controls", padding=10)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Primary algorithm buttons
        primary_frame = ttk.Frame(controls_frame)
        primary_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.value_iter_btn = ttk.Button(
            primary_frame,
            text="🔄 Value Iteration",
            command=self._run_value_iteration,
            state="disabled"
        )
        self.value_iter_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.policy_iter_btn = ttk.Button(
            primary_frame,
            text="🎯 Policy Iteration",
            command=self._run_policy_iteration,
            state="disabled"
        )
        self.policy_iter_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.step_btn = ttk.Button(
            primary_frame,
            text="👣 Step by Step",
            command=self._step_algorithm,
            state="disabled"
        )
        self.step_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.reset_btn = ttk.Button(
            primary_frame,
            text="🔄 Reset",
            command=self._reset_algorithm,
            state="disabled"
        )
        self.reset_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.generate_exit_btn = ttk.Button(
            primary_frame,
            text="🚪 New Exit",
            command=self._generate_new_exit,
            state="disabled"
        )
        self.generate_exit_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add refresh button
        self.refresh_btn = ttk.Button(
            primary_frame,
            text="🔄 Refresh All",
            command=self.refresh,
            state="normal"
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add tooltip for the generate exit button
        self._create_tooltip(self.generate_exit_btn, "Generate a new random exit position")
        
        # Add tooltip for the refresh button
        self._create_tooltip(self.refresh_btn, "Reset all parameters and clear results")
        
        # Visualization controls
        viz_frame = ttk.Frame(controls_frame)
        viz_frame.pack(fill=tk.X)
        
        self.show_values_var = tk.BooleanVar()
        self.show_policy_var = tk.BooleanVar()
        
        ttk.Checkbutton(
            viz_frame,
            text="Show Values",
            variable=self.show_values_var,
            command=self._toggle_values
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Checkbutton(
            viz_frame,
            text="Show Policy",
            variable=self.show_policy_var,
            command=self._toggle_policy
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(
            viz_frame,
            text="No maze loaded",
            foreground="gray"
        )
        self.status_label.pack(side=tk.RIGHT)
    
    def _create_game_area(self) -> None:
        """Create the game area for visualization."""
        viz_frame = ttk.LabelFrame(self, text="Visualization", padding=5)
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create GameArea
        self.game_area = GameArea(
            viz_frame,
            width=600,
            height=400
        )
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(viz_frame, orient=tk.VERTICAL, command=self.game_area.yview)
        h_scrollbar = ttk.Scrollbar(viz_frame, orient=tk.HORIZONTAL, command=self.game_area.xview)
        
        self.game_area.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.game_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def _create_results(self) -> None:
        """Create results display area."""
        results_frame = ttk.LabelFrame(self, text="Results & Convergence", padding=5)
        results_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(results_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Results text tab
        text_frame = ttk.Frame(notebook)
        notebook.add(text_frame, text="Statistics")
        
        # Text area with scrollbar
        text_scroll_frame = ttk.Frame(text_frame)
        text_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = tk.Text(
            text_scroll_frame,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        
        text_scrollbar = ttk.Scrollbar(text_scroll_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=text_scrollbar.set)
        
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Convergence plot tab
        plot_frame = ttk.Frame(notebook)
        notebook.add(plot_frame, text="Convergence Plot")
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.convergence_plot = FigureCanvasTkAgg(self.fig, plot_frame)
        self.convergence_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _run_value_iteration(self) -> None:
        """Run value iteration algorithm."""
        if not self._check_maze_loaded():
            return
        
        self._set_running_state(True)
        self.status_label.config(text="Running Value Iteration...")
        
        try:
            # Create DP instance with current parameters
            self.maze_dp = MazeDP(self.current_maze, self.gamma.get())
            
            # Apply custom reward structure
            self._apply_custom_rewards()
            
            # Run algorithm
            result = self.maze_dp.value_iteration(
                max_iterations=self.max_iterations.get(),
                theta=self.theta.get()
            )
            
            # Update visualization
            self._update_visualization()
            
            # Display results
            self._display_results("Value Iteration", result)
            
            # Plot convergence
            self._plot_convergence(result['convergence_history'], "Value Iteration")
            
            self.status_label.config(
                text=f"Value Iteration: {result['iterations']} iterations, "
                     f"{'Converged' if result['converged'] else 'Max iterations reached'}"
            )
            
        except Exception as e:
            logging.error(f"Error in value iteration: {e}")
            messagebox.showerror("Error", f"Value iteration failed: {e}")
            self.status_label.config(text="Error in Value Iteration")
        
        finally:
            self._set_running_state(False)
    
    def _run_policy_iteration(self) -> None:
        """Run policy iteration algorithm."""
        if not self._check_maze_loaded():
            return
        
        self._set_running_state(True)
        self.status_label.config(text="Running Policy Iteration...")
        
        try:
            # Create DP instance with current parameters
            self.maze_dp = MazeDP(self.current_maze, self.gamma.get())
            
            # Apply custom reward structure
            self._apply_custom_rewards()
            
            # Run algorithm
            result = self.maze_dp.policy_iteration(
                max_iterations=self.max_iterations.get()
            )
            
            # Update visualization
            self._update_visualization()
            
            # Display results
            self._display_results("Policy Iteration", result)
            
            # Plot convergence
            self._plot_convergence(result['convergence_history'], "Policy Iteration")
            
            self.status_label.config(
                text=f"Policy Iteration: {result['iterations']} iterations, "
                     f"{'Converged' if result['converged'] else 'Max iterations reached'}"
            )
            
        except Exception as e:
            logging.error(f"Error in policy iteration: {e}")
            messagebox.showerror("Error", f"Policy iteration failed: {e}")
            self.status_label.config(text="Error in Policy Iteration")
        
        finally:
            self._set_running_state(False)
    
    def _preset_fast_path(self) -> None:
        """Set rewards for encouraging fast path finding."""
        self.step_reward.set(-0.1)
        self.goal_reward.set(10.0)
        self.wall_reward.set(0.0)
        self.custom_rewards.clear()
        self.reward_info_label.config(text="Fast Path: High step penalty, encourages speed")
        self._update_reward_display()
    
    def _preset_careful(self) -> None:
        """Set rewards for encouraging careful exploration."""
        self.step_reward.set(-0.01)
        self.goal_reward.set(5.0)
        self.wall_reward.set(0.0)
        self.custom_rewards.clear()
        self.reward_info_label.config(text="Careful: Low step penalty, allows exploration")
        self._update_reward_display()
    
    def _preset_balanced(self) -> None:
        """Set balanced reward structure."""
        self.step_reward.set(-0.04)
        self.goal_reward.set(10.0)
        self.wall_reward.set(0.0)
        self.custom_rewards.clear()
        self.reward_info_label.config(text="Balanced: Standard RL reward structure")
        self._update_reward_display()
    
    def _preset_goal_focused(self) -> None:
        """Set rewards that heavily focus on reaching the goal."""
        self.step_reward.set(-0.02)
        self.goal_reward.set(50.0)
        self.wall_reward.set(0.0)
        self.custom_rewards.clear()
        self.reward_info_label.config(text="Goal Focused: Very high goal reward")
        self._update_reward_display()
    
    def _preset_risky(self) -> None:
        """Set risky reward structure with penalties for walls."""
        self.step_reward.set(-0.05)
        self.goal_reward.set(15.0)
        self.wall_reward.set(-5.0)
        self.custom_rewards.clear()
        self.reward_info_label.config(text="Risky: Wall penalties, high goal reward")
        self._update_reward_display()
    
    def _reset_rewards(self) -> None:
        """Reset rewards to default values."""
        self.step_reward.set(-0.04)
        self.goal_reward.set(10.0)
        self.wall_reward.set(0.0)
        self.custom_rewards.clear()
        self.reward_info_label.config(text=self.DEFAULT_REWARD_INFO)
        self._update_reward_display()
    
    def _update_reward_display(self) -> None:
        """Update visualization if algorithm has been run."""
        if self.maze_dp and self.current_maze is not None:
            # Re-run algorithm with new rewards if it was already run
            if hasattr(self.maze_dp, 'value_function') and np.any(self.maze_dp.value_function != 0):
                # Automatically re-run the last algorithm
                messagebox.showinfo(
                    "Rewards Updated", 
                    "Rewards have been updated. Click 'Value Iteration' or 'Policy Iteration' to see the effect."
                )
    
    def _open_custom_rewards(self) -> None:
        """Open custom reward configuration dialog."""
        if self.current_maze is None:
            messagebox.showwarning("Warning", "Please load a maze first.")
            return
        
        # Custom reward dialog (simplified for now)
        messagebox.showinfo("Custom Rewards", "Custom reward dialog coming soon!\n\nFor now, use the preset buttons to modify reward structure.")
    
    def _apply_custom_rewards(self) -> None:
        """Apply custom reward structure to the DP instance."""
        if not self.maze_dp:
            return
        
        # Update the DP instance's reward matrix using the new method
        self.maze_dp.update_rewards(
            step_reward=self.step_reward.get(),
            goal_reward=self.goal_reward.get(),
            wall_reward=self.wall_reward.get(),
            custom_rewards=self.custom_rewards
        )
    
    def _generate_new_exit(self) -> None:
        """Generate a new exit in the current maze."""
        if not self._check_maze_loaded():
            return
        
        try:
            # Reset existing exits and get available positions
            maze_copy, old_exit_count = self._reset_exits()
            room_positions = self._find_room_positions(maze_copy)
            
            if not room_positions:
                messagebox.showwarning("Warning", "No available room positions for exit!")
                return
            
            # Generate new exit
            new_exit_pos = self._place_random_exit(maze_copy, room_positions)
            
            # Update maze and UI
            self._update_maze_with_new_exit(maze_copy, new_exit_pos, old_exit_count)
            
        except Exception as e:
            logging.error(f"Error generating new exit: {e}")
            messagebox.showerror("Error", f"Failed to generate new exit: {e}")
    
    def _reset_exits(self) -> tuple:
        """Reset existing exits in maze and return copy with exit count."""
        from MazeConfig import CellType
        
        maze_copy = self.current_maze.copy()
        exit_count = 0
        
        for i in range(maze_copy.shape[0]):
            for j in range(maze_copy.shape[1]):
                if maze_copy[i, j] == CellType.EXIT.value:
                    maze_copy[i, j] = CellType.ROOM.value
                    exit_count += 1
        
        return maze_copy, exit_count
    
    def _find_room_positions(self, maze: np.ndarray) -> list:
        """Find all available room positions in the maze."""
        from MazeConfig import CellType
        
        room_positions = []
        for i in range(maze.shape[0]):
            for j in range(maze.shape[1]):
                if maze[i, j] == CellType.ROOM.value:
                    room_positions.append((i, j))
        
        return room_positions
    
    def _place_random_exit(self, maze: np.ndarray, room_positions: list) -> tuple:
        """Place a random exit in the maze and return its position."""
        import random
        from MazeConfig import CellType
        
        # For better variety, prefer corner or edge positions when available
        edge_positions = []
        corner_positions = []
        
        for pos in room_positions:
            row, col = pos
            is_edge = (row == 0 or row == maze.shape[0]-1 or 
                      col == 0 or col == maze.shape[1]-1)
            is_corner = ((row == 0 or row == maze.shape[0]-1) and 
                        (col == 0 or col == maze.shape[1]-1))
            
            if is_corner:
                corner_positions.append(pos)
            elif is_edge:
                edge_positions.append(pos)
        
        # Prefer corners, then edges, then any room
        if corner_positions and random.random() < 0.4:  # 40% chance for corner
            new_exit_pos = random.choice(corner_positions)
        elif edge_positions and random.random() < 0.6:   # 60% chance for edge
            new_exit_pos = random.choice(edge_positions)
        else:
            new_exit_pos = random.choice(room_positions)
        
        maze[new_exit_pos[0], new_exit_pos[1]] = CellType.EXIT.value
        return new_exit_pos
    
    def _update_maze_with_new_exit(self, maze_copy: np.ndarray, new_exit_pos: tuple, old_exit_count: int) -> None:
        """Update the current maze and UI with the new exit."""
        # Update the current maze
        self.current_maze = maze_copy
        
        # Reload maze into game area
        if self.game_area:
            self.game_area.load_maze(maze_copy)
        
        # Reset DP results and visualization (but keep parameters)
        self.maze_dp = None
        self._clear_visualization()
        
        # Clear results and plots
        if self.result_text:
            self.result_text.delete(1.0, tk.END)
        if hasattr(self, 'ax'):
            self.ax.clear()
            self.convergence_plot.draw()
        
        # Calculate some statistics for better feedback
        total_rooms = np.sum(maze_copy == 1)  # CellType.ROOM.value
        
        # Update status with more informative message
        self.status_label.config(
            text=f"Exit: ({new_exit_pos[0]}, {new_exit_pos[1]}) | "
                 f"Replaced: {old_exit_count} exit(s) | "
                 f"Available positions: {total_rooms}"
        )
        
        logging.info(f"Generated new exit at position {new_exit_pos}, {total_rooms} total room positions available")
    
    def _create_tooltip(self, widget, text: str) -> None:
        """Create a simple tooltip for a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg="black")
            
            label = tk.Label(
                tooltip, 
                text=text, 
                bg="black", 
                fg="white", 
                font=("Arial", 8),
                padx=4,
                pady=2
            )
            label.pack()
            
            # Position tooltip near the widget
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() - 25
            tooltip.geometry(f"+{x}+{y}")
            
            # Store tooltip reference to destroy it later
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _step_algorithm(self) -> None:
        messagebox.showinfo("Step by Step", "Step-by-step functionality coming soon!")
    
    def _reset_algorithm(self) -> None:
        """Reset algorithm state."""
        if self.maze_dp:
            self.maze_dp.reset()
        
        # Clear visualization
        self._clear_visualization()
        
        # Clear results
        if self.result_text:
            self.result_text.delete(1.0, tk.END)
        
        # Clear convergence plot
        if hasattr(self, 'ax'):
            self.ax.clear()
            self.convergence_plot.draw()
        
        # Reset checkboxes
        self.show_values_var.set(False)
        self.show_policy_var.set(False)
        
        self.status_label.config(text="Algorithm reset")
    
    def _clear_visualization(self) -> None:
        """Clear all visualization overlays."""
        if self.game_area:
            # Clear value function and policy displays
            self.game_area.set_show_values(False)
            self.game_area.set_show_policy(False)
            
            # Clear any loaded DP data
            self.game_area.value_function = None
            self.game_area.policy = None
    
    def _reset_all_parameters(self) -> None:
        """Reset all parameters to default values."""
        # Reset algorithm parameters
        self.gamma.set(0.9)
        self.max_iterations.set(100)
        self.theta.set(0.0001)
        
        # Reset reward parameters
        self.step_reward.set(-0.04)
        self.goal_reward.set(10.0)
        self.wall_reward.set(0.0)
        self.custom_rewards.clear()
        
        # Reset reward info label
        self.reward_info_label.config(text=self.DEFAULT_REWARD_INFO)
        
        # Reset algorithm state
        self.is_running = False
        self.current_iteration = 0
        self.maze_dp = None
    
    def _check_maze_loaded(self) -> bool:
        """Check if maze is loaded."""
        if self.current_maze is None:
            messagebox.showwarning("Warning", "No maze loaded. Please load a maze first.")
            return False
        return True
    
    def _set_running_state(self, running: bool) -> None:
        """Set UI state for running algorithm."""
        self.is_running = running
        state = "disabled" if running else "normal"
        
        self.value_iter_btn.config(state=state)
        self.policy_iter_btn.config(state=state)
        self.step_btn.config(state=state)
        self.generate_exit_btn.config(state=state)
        self.reset_btn.config(state="normal")  # Reset always available
    
    def _update_visualization(self) -> None:
        """Update game area visualization."""
        if self.maze_dp and self.game_area:
            # Load value function and policy
            self.game_area.load_value_function(self.maze_dp.get_value_function())
            self.game_area.load_policy(self.maze_dp.get_policy())
            
            # Update display based on checkboxes
            self.game_area.set_show_values(self.show_values_var.get())
            self.game_area.set_show_policy(self.show_policy_var.get())
    
    def _toggle_values(self) -> None:
        """Toggle value function display."""
        if self.game_area:
            self.game_area.set_show_values(self.show_values_var.get())
    
    def _toggle_policy(self) -> None:
        """Toggle policy display."""
        if self.game_area:
            self.game_area.set_show_policy(self.show_policy_var.get())
    
    def _display_results(self, algorithm: str, result: dict) -> None:
        """Display algorithm results."""
        self.result_text.delete(1.0, tk.END)
        
        stats = self.maze_dp.get_stats() if self.maze_dp else {}
        
        output = f"{algorithm} Results:\n"
        output += "=" * 50 + "\n\n"
        output += f"Iterations: {result['iterations']}\n"
        output += f"Converged: {result['converged']}\n"
        
        if 'final_delta' in result:
            output += f"Final Delta: {result['final_delta']:.6f}\n"
        
        output += "\nMaze Statistics:\n"
        output += f"Size: {stats.get('maze_shape', 'N/A')}\n"
        output += f"Discount Factor: {stats.get('gamma', 'N/A')}\n"
        output += f"Terminal States: {stats.get('terminal_states', 'N/A')}\n"
        output += f"Valid States: {stats.get('valid_states', 'N/A')}\n"
        
        output += "\nReward Configuration:\n"
        output += f"Step Reward: {self.step_reward.get():.3f}\n"
        output += f"Goal Reward: {self.goal_reward.get():.1f}\n"
        output += f"Wall Reward: {self.wall_reward.get():.1f}\n"
        if self.custom_rewards:
            output += f"Custom Rewards: {len(self.custom_rewards)} cells\n"
        
        output += "\nValue Function Statistics:\n"
        output += f"Max Value: {stats.get('max_value', 0):.4f}\n"
        output += f"Min Value: {stats.get('min_value', 0):.4f}\n"
        output += f"Avg Value: {stats.get('avg_value', 0):.4f}\n"
        
        self.result_text.insert(tk.END, output)
    
    def _plot_convergence(self, history: list, algorithm: str) -> None:
        """Plot convergence history."""
        self.ax.clear()
        
        if history:
            self.ax.plot(history, 'b-', linewidth=2)
            self.ax.set_xlabel('Iteration')
            self.ax.set_ylabel('Delta / Policy Changes')
            self.ax.set_title(f'{algorithm} Convergence')
            self.ax.grid(True, alpha=0.3)
            self.ax.set_yscale('log' if max(history) > 0 else 'linear')
        
        self.fig.tight_layout()
        self.convergence_plot.draw()
    
    def set_maze(self, maze: np.ndarray) -> None:
        """
        Set the maze for DP algorithms.
        
        Args:
            maze: 2D numpy array representing the maze
        """
        try:
            self.current_maze = maze.copy()
            
            # Perform comprehensive reset when loading new maze
            self._reset_all_parameters()
            
            # Load maze into game area
            if self.game_area:
                self.game_area.load_maze(maze)
            
            # Clear any previous visualization
            self._clear_visualization()
            
            # Enable controls
            self.value_iter_btn.config(state="normal")
            self.policy_iter_btn.config(state="normal")
            self.step_btn.config(state="normal")
            self.reset_btn.config(state="normal")
            self.generate_exit_btn.config(state="normal")
            
            self.status_label.config(text=f"Maze loaded: {maze.shape}")
            
            # Clear previous results
            if self.result_text:
                self.result_text.delete(1.0, tk.END)
            if hasattr(self, 'ax'):
                self.ax.clear()
                self.convergence_plot.draw()
            
            logging.info("Maze loaded successfully in DP frame with complete reset")
            
        except Exception as e:
            logging.error(f"Error loading maze in DP frame: {e}")
            messagebox.showerror("Error", f"Failed to load maze: {e}")
    
    def refresh(self) -> None:
        """
        Refresh the DP frame with comprehensive reset.
        Resets all parameters, visualization, and algorithm state.
        """
        if self.current_maze is not None:
            # Perform complete reset
            self._reset_all_parameters()
            
            # Clear visualization
            self._clear_visualization()
            
            # Reload maze to ensure clean state
            if self.game_area:
                self.game_area.load_maze(self.current_maze)
            
            # Clear results and plots
            if self.result_text:
                self.result_text.delete(1.0, tk.END)
            if hasattr(self, 'ax'):
                self.ax.clear()
                self.convergence_plot.draw()
            
            # Update status
            self.status_label.config(text=f"Refreshed: {self.current_maze.shape}")
            
            logging.info("DP frame refreshed with complete reset")
        else:
            # No maze loaded, just clear everything
            self._reset_all_parameters()
            self._clear_visualization()
            
            if self.result_text:
                self.result_text.delete(1.0, tk.END)
            if hasattr(self, 'ax'):
                self.ax.clear()
                self.convergence_plot.draw()
            
            self.status_label.config(text="No maze loaded")
            logging.info("DP frame refreshed (no maze loaded)")
    
    def on_show(self, **kwargs) -> None:
        """Called when the frame is shown."""
        if 'maze' in kwargs:
            self.set_maze(kwargs['maze'])
        
        logging.debug("MazeDpFrame shown")
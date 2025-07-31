"""
Dynamic Programming algorithms for maze solving.
Implements Value Iteration and Policy Iteration for MDP-based maze solving.
"""

import numpy as np
from typing import Tuple, List, Optional
from MazeConfig import CellType


class MazeDP:
    """
    Dynamic Programming solver for maze environments.
    Implements value iteration and policy iteration algorithms.
    """
    
    def __init__(self, maze: np.ndarray, gamma: float = 0.9):
        """
        Initialize the DP solver.
        
        Args:
            maze: 2D numpy array representing the maze
            gamma: Discount factor for future rewards
        """
        self.maze = maze.copy()
        self.gamma = gamma
        self.rows, self.cols = maze.shape
        
        # Actions: 0=up, 1=right, 2=down, 3=left
        self.actions = [0, 1, 2, 3]
        self.action_names = ['UP', 'RIGHT', 'DOWN', 'LEFT']
        self.action_deltas = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        
        # Initialize value function and policy
        self.value_function = np.zeros((self.rows, self.cols))
        self.policy = np.zeros((self.rows, self.cols), dtype=int)
        
        # Find terminal states
        self.terminal_states = self._find_terminal_states()
        
        # Set up rewards
        self.rewards = self._setup_rewards()
        
        # Track convergence
        self.convergence_history = []
        
    def _find_terminal_states(self) -> List[Tuple[int, int]]:
        """Find terminal states (exits) in the maze."""
        terminals = []
        for i in range(self.rows):
            for j in range(self.cols):
                if self.maze[i, j] == CellType.EXIT.value:
                    terminals.append((i, j))
        return terminals
    
    def _setup_rewards(self) -> np.ndarray:
        """Setup reward function for the maze."""
        rewards = np.full((self.rows, self.cols), -0.04)  # Small negative reward for each step
        
        # Set rewards for different cell types
        for i in range(self.rows):
            for j in range(self.cols):
                if self.maze[i, j] == CellType.WALL.value:
                    rewards[i, j] = 0  # No reward for walls (unreachable)
                elif self.maze[i, j] == CellType.EXIT.value:
                    rewards[i, j] = 10  # High reward for reaching exit
        
        return rewards
    
    def update_rewards(self, step_reward: float = -0.04, goal_reward: float = 10.0, wall_reward: float = 0.0, custom_rewards: dict = None) -> None:
        """
        Update the reward structure.
        
        Args:
            step_reward: Reward for each step (usually negative)
            goal_reward: Reward for reaching the goal
            wall_reward: Reward for walls (usually 0 or negative)
            custom_rewards: Dictionary of {(row, col): reward} for custom cell rewards
        """
        # Create new reward matrix
        self.rewards = np.full((self.rows, self.cols), step_reward)
        
        # Set rewards for different cell types
        for i in range(self.rows):
            for j in range(self.cols):
                if self.maze[i, j] == CellType.WALL.value:
                    self.rewards[i, j] = wall_reward
                elif self.maze[i, j] == CellType.EXIT.value:
                    self.rewards[i, j] = goal_reward
        
        # Apply custom rewards if provided
        if custom_rewards:
            for (row, col), reward in custom_rewards.items():
                if 0 <= row < self.rows and 0 <= col < self.cols:
                    self.rewards[row, col] = reward
    
    def _is_valid_state(self, row: int, col: int) -> bool:
        """Check if a state is valid (within bounds and not a wall)."""
        return (0 <= row < self.rows and 
                0 <= col < self.cols and 
                self.maze[row, col] != CellType.WALL.value)
    
    def _get_next_state(self, row: int, col: int, action: int) -> Tuple[int, int]:
        """Get next state given current state and action."""
        dr, dc = self.action_deltas[action]
        new_row, new_col = row + dr, col + dc
        
        # If next state is invalid, stay in current state
        if not self._is_valid_state(new_row, new_col):
            return row, col
        
        return new_row, new_col
    
    def _is_terminal(self, row: int, col: int) -> bool:
        """Check if state is terminal."""
        return (row, col) in self.terminal_states
    
    def value_iteration(self, max_iterations: int = 100, theta: float = 1e-4) -> dict:
        """
        Perform value iteration algorithm.
        
        Args:
            max_iterations: Maximum number of iterations
            theta: Convergence threshold
            
        Returns:
            Dictionary with results and convergence info
        """
        self.convergence_history = []
        
        for iteration in range(max_iterations):
            old_values = self.value_function.copy()
            max_delta = 0
            
            # Update value function for each state
            for i in range(self.rows):
                for j in range(self.cols):
                    if not self._is_valid_state(i, j) or self._is_terminal(i, j):
                        continue
                    
                    # Calculate value for each action
                    action_values = []
                    for action in self.actions:
                        next_i, next_j = self._get_next_state(i, j, action)
                        value = self.rewards[i, j] + self.gamma * old_values[next_i, next_j]
                        action_values.append(value)
                    
                    # Take maximum value
                    self.value_function[i, j] = max(action_values)
                    
                    # Track maximum change
                    delta = abs(self.value_function[i, j] - old_values[i, j])
                    max_delta = max(max_delta, delta)
            
            # Record convergence
            self.convergence_history.append(max_delta)
            
            # Check for convergence
            if max_delta < theta:
                break
        
        # Extract policy
        self._extract_policy()
        
        return {
            'iterations': iteration + 1,
            'converged': max_delta < theta,
            'final_delta': max_delta,
            'convergence_history': self.convergence_history.copy()
        }
    
    def _extract_policy(self) -> None:
        """Extract policy from value function."""
        for i in range(self.rows):
            for j in range(self.cols):
                if not self._is_valid_state(i, j) or self._is_terminal(i, j):
                    continue
                
                # Find best action
                action_values = []
                for action in self.actions:
                    next_i, next_j = self._get_next_state(i, j, action)
                    value = self.rewards[i, j] + self.gamma * self.value_function[next_i, next_j]
                    action_values.append(value)
                
                # Set policy to best action
                self.policy[i, j] = np.argmax(action_values)
    
    def policy_iteration(self, max_iterations: int = 100) -> dict:
        """
        Perform policy iteration algorithm.
        
        Args:
            max_iterations: Maximum number of iterations
            
        Returns:
            Dictionary with results and convergence info
        """
        self.convergence_history = []
        
        # Initialize random policy
        for i in range(self.rows):
            for j in range(self.cols):
                if self._is_valid_state(i, j) and not self._is_terminal(i, j):
                    self.policy[i, j] = np.random.default_rng(42).choice(self.actions)
        
        for iteration in range(max_iterations):
            # Policy evaluation
            self._policy_evaluation()
            
            # Policy improvement
            policy_stable = self._policy_improvement()
            
            # Record convergence
            self.convergence_history.append(0 if policy_stable else 1)
            
            if policy_stable:
                break
        
        return {
            'iterations': iteration + 1,
            'converged': policy_stable,
            'convergence_history': self.convergence_history.copy()
        }
    
    def _policy_evaluation(self, theta: float = 1e-4, max_eval_iterations: int = 100) -> None:
        """Evaluate current policy."""
        for _ in range(max_eval_iterations):
            old_values = self.value_function.copy()
            max_delta = 0
            
            for i in range(self.rows):
                for j in range(self.cols):
                    if not self._is_valid_state(i, j) or self._is_terminal(i, j):
                        continue
                    
                    action = self.policy[i, j]
                    next_i, next_j = self._get_next_state(i, j, action)
                    self.value_function[i, j] = self.rewards[i, j] + self.gamma * old_values[next_i, next_j]
                    
                    delta = abs(self.value_function[i, j] - old_values[i, j])
                    max_delta = max(max_delta, delta)
            
            if max_delta < theta:
                break
    
    def _policy_improvement(self) -> bool:
        """Improve policy based on current value function."""
        policy_stable = True
        
        for i in range(self.rows):
            for j in range(self.cols):
                if not self._is_valid_state(i, j) or self._is_terminal(i, j):
                    continue
                
                old_action = self.policy[i, j]
                
                # Find best action
                action_values = []
                for action in self.actions:
                    next_i, next_j = self._get_next_state(i, j, action)
                    value = self.rewards[i, j] + self.gamma * self.value_function[next_i, next_j]
                    action_values.append(value)
                
                self.policy[i, j] = np.argmax(action_values)
                
                if old_action != self.policy[i, j]:
                    policy_stable = False
        
        return policy_stable
    
    def get_value_function(self) -> np.ndarray:
        """Get current value function."""
        return self.value_function.copy()
    
    def get_policy(self) -> np.ndarray:
        """Get current policy."""
        return self.policy.copy()
    
    def get_policy_string(self, row: int, col: int) -> str:
        """Get policy action as string for a given state."""
        if not self._is_valid_state(row, col) or self._is_terminal(row, col):
            return ""
        return self.action_names[self.policy[row, col]]
    
    def reset(self) -> None:
        """Reset value function and policy."""
        self.value_function = np.zeros((self.rows, self.cols))
        self.policy = np.zeros((self.rows, self.cols), dtype=int)
        self.convergence_history = []
    
    def get_stats(self) -> dict:
        """Get algorithm statistics."""
        return {
            'maze_shape': (self.rows, self.cols),
            'gamma': self.gamma,
            'terminal_states': len(self.terminal_states),
            'valid_states': np.sum(self.maze != CellType.WALL.value),
            'max_value': np.max(self.value_function),
            'min_value': np.min(self.value_function),
            'avg_value': np.mean(self.value_function[self.maze != CellType.WALL.value])
        }

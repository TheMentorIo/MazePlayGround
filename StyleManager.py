"""
Style manager for the Maze Playground application.
Handles ttk styling and theme management.
"""

from tkinter import ttk
import logging
from typing import Dict, Any


class StyleManager:
    """Manager for application styles and themes."""
    
    def __init__(self, root):
        """
        Initialize the style manager.
        
        Args:
            root: Root tkinter window
        """
        self.root = root
        self.style = ttk.Style(root)
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Setup custom button and widget styles."""
        try:
            # Configure button styles
            self._configure_button_styles()
            self._configure_frame_styles()
            self._configure_label_styles()
            
            logging.debug("Custom styles configured successfully")
        except Exception as e:
            logging.error(f"Failed to configure styles: {e}")

    def _configure_button_styles(self) -> None:
        """Configure custom button styles."""
        # Primary button style (for main actions)
        self.style.configure(
            "Primary.TButton",
            font=("Arial", 11, "bold"),
            padding=(10, 8)
        )
        
        # Success button style (for positive actions)
        self.style.configure(
            "Success.TButton",
            font=("Arial", 11, "bold"),
            padding=(10, 8)
        )
        
        # Info button style (for informational actions)
        self.style.configure(
            "Info.TButton",
            font=("Arial", 11, "bold"),
            padding=(10, 8)
        )
        
        # Large button style
        self.style.configure(
            "Large.TButton",
            font=("Arial", 14, "bold"),
            padding=(15, 12)
        )

    def _configure_frame_styles(self) -> None:
        """Configure custom frame styles."""
        self.style.configure(
            "Card.TFrame",
            relief="solid",
            borderwidth=1,
            padding=10
        )

    def _configure_label_styles(self) -> None:
        """Configure custom label styles."""
        self.style.configure(
            "Title.TLabel",
            font=("Arial", 16, "bold")
        )
        
        self.style.configure(
            "Subtitle.TLabel",
            font=("Arial", 10),
            foreground="gray"
        )
        
        self.style.configure(
            "Heading.TLabel",
            font=("Arial", 12, "bold")
        )

    def apply_theme(self, theme_name: str) -> None:
        """
        Apply a theme to the application.
        
        Args:
            theme_name: Name of the theme to apply
        """
        try:
            if theme_name == "dark":
                self._apply_dark_theme()
            elif theme_name == "light":
                self._apply_light_theme()
            else:
                self._apply_default_theme()
            
            logging.info(f"Applied theme: {theme_name}")
        except Exception as e:
            logging.error(f"Failed to apply theme {theme_name}: {e}")

    def _apply_dark_theme(self) -> None:
        """Apply dark theme."""
        self.style.theme_use("clam")
        
        # Configure colors for dark theme
        self.style.configure(".", background="#2d2d2d", foreground="#ffffff")
        self.style.configure("TButton", background="#404040", foreground="#ffffff")
        self.style.configure("TFrame", background="#2d2d2d")
        self.style.configure("TLabel", background="#2d2d2d", foreground="#ffffff")

    def _apply_light_theme(self) -> None:
        """Apply light theme."""
        self.style.theme_use("default")
        
        # Configure colors for light theme
        self.style.configure(".", background="#ffffff", foreground="#000000")
        self.style.configure("TButton", background="#f0f0f0", foreground="#000000")

    def _apply_default_theme(self) -> None:
        """Apply default theme."""
        self.style.theme_use("default")

    def get_available_themes(self) -> list:
        """Get list of available tkinter themes."""
        return self.style.theme_names()

    def configure_style(self, style_name: str, **options) -> None:
        """
        Configure a custom style.
        
        Args:
            style_name: Name of the style
            **options: Style options
        """
        try:
            self.style.configure(style_name, **options)
        except Exception as e:
            logging.error(f"Failed to configure style {style_name}: {e}")

    def create_button_style(self, name: str, font_size: int = 11, 
                           padding: tuple = (10, 8), **kwargs) -> str:
        """
        Create a custom button style.
        
        Args:
            name: Style name
            font_size: Font size
            padding: Button padding
            **kwargs: Additional style options
            
        Returns:
            Full style name
        """
        style_name = f"{name}.TButton"
        
        options = {
            "font": ("Arial", font_size, "bold"),
            "padding": padding,
            **kwargs
        }
        
        self.configure_style(style_name, **options)
        return style_name

"""
Interactive TUI application.

Uses basic terminal for now - textual integration would be next.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class TUIConfig:
    """Configuration for TUI."""
    
    db: Any = None               # InceptionDB
    query_layer: Any = None      # QueryLayer
    theme: str = "dark"
    show_gaps: bool = True
    refresh_interval: float = 1.0


class InceptionTUI:
    """
    Interactive terminal UI for exploring knowledge graphs.
    
    Features (when fully implemented with textual):
    - Entity/claim/procedure browsing
    - Search across all content
    - Graph navigation (follow edges)
    - Evidence chain inspection
    - Real-time gap alerts
    - Sync status display
    
    Current: Basic CLI interface
    """
    
    def __init__(self, config: TUIConfig | None = None):
        """Initialize TUI."""
        self.config = config or TUIConfig()
        self._running = False
    
    def run(self) -> None:
        """Run the TUI application."""
        self._running = True
        
        print("\n" + "=" * 60)
        print("  INCEPTION - Knowledge Graph Explorer")
        print("=" * 60 + "\n")
        
        while self._running:
            self._show_menu()
            choice = input("\nEnter choice (q to quit): ").strip().lower()
            
            if choice == "q":
                self._running = False
            elif choice == "1":
                self._browse_entities()
            elif choice == "2":
                self._search()
            elif choice == "3":
                self._show_stats()
            elif choice == "4":
                self._show_gaps()
            else:
                print("Invalid choice")
        
        print("\nGoodbye!")
    
    def _show_menu(self) -> None:
        """Show main menu."""
        print("\n--- Main Menu ---")
        print("1. Browse Entities")
        print("2. Search")
        print("3. Statistics")
        print("4. Show Gaps")
        print("q. Quit")
    
    def _browse_entities(self) -> None:
        """Browse entities."""
        print("\n--- Entity Browser ---")
        
        if not self.config.db:
            print("No database connected")
            return
        
        # Would list entities from DB
        print("(Entity listing would appear here)")
    
    def _search(self) -> None:
        """Search across content."""
        query = input("\nSearch query: ").strip()
        
        if not query:
            return
        
        print(f"\nSearching for: {query}")
        
        if not self.config.query_layer:
            print("No query layer connected")
            return
        
        # Would execute search
        print("(Search results would appear here)")
    
    def _show_stats(self) -> None:
        """Show knowledge base statistics."""
        print("\n--- Statistics ---")
        
        if not self.config.db:
            print("No database connected")
            return
        
        # Would show DB stats
        print("(Statistics would appear here)")
    
    def _show_gaps(self) -> None:
        """Show detected knowledge gaps."""
        print("\n--- Knowledge Gaps ---")
        
        if not self.config.db:
            print("No database connected")
            return
        
        # Would list gaps
        print("(Gaps would appear here)")
    
    def stop(self) -> None:
        """Stop the TUI."""
        self._running = False


def main():
    """CLI entry point."""
    tui = InceptionTUI()
    tui.run()


if __name__ == "__main__":
    main()

"""
Safety configuration for autonomous exploration.

Design by OPUS-3: Safety is paramount. All autonomous
actions are constrained by these configs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ExplorationConfig:
    """
    Configuration for autonomous gap exploration.
    
    All defaults are conservative to ensure safety.
    """
    
    # Rate limiting
    max_requests_per_minute: int = 10
    max_concurrent_requests: int = 2
    
    # Budget limits
    budget_cap_usd: float = 0.50
    max_tokens_per_session: int = 50000
    
    # Depth limits
    max_exploration_depth: int = 2  # How many hops from original gap
    max_gaps_per_session: int = 10
    max_sources_per_gap: int = 3
    
    # Domain filtering
    domain_allowlist: list[str] | None = None  # None = allow all
    domain_blocklist: list[str] = field(default_factory=lambda: [
        "reddit.com",
        "twitter.com",
        "x.com",
        "facebook.com",
        "tiktok.com",
        "instagram.com",
    ])
    
    # Content filtering
    min_content_length: int = 200
    max_content_length: int = 50000
    require_https: bool = True
    
    # Human-in-the-loop
    require_confirmation: bool = True
    confirmation_callback: Callable[[str], bool] | None = None
    
    # Audit and logging
    log_all_requests: bool = True
    audit_log_path: str | None = None
    
    # Offline mode
    offline: bool = False  # If True, only use cached results
    
    def is_domain_allowed(self, domain: str) -> bool:
        """Check if a domain is allowed for exploration."""
        domain = domain.lower().strip()
        
        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Check blocklist first
        for blocked in self.domain_blocklist:
            if domain == blocked or domain.endswith(f".{blocked}"):
                return False
        
        # If allowlist exists, only allow those
        if self.domain_allowlist is not None:
            for allowed in self.domain_allowlist:
                if domain == allowed or domain.endswith(f".{allowed}"):
                    return True
            return False
        
        return True
    
    def confirm(self, action: str) -> bool:
        """Request confirmation for an action."""
        if not self.require_confirmation:
            return True
        
        if self.confirmation_callback:
            return self.confirmation_callback(action)
        
        # Default: return False (require explicit callback)
        return False


# Preset configurations
STRICT_CONFIG = ExplorationConfig(
    max_requests_per_minute=5,
    budget_cap_usd=0.10,
    max_exploration_depth=1,
    require_confirmation=True,
)

BALANCED_CONFIG = ExplorationConfig(
    max_requests_per_minute=10,
    budget_cap_usd=0.50,
    max_exploration_depth=2,
    require_confirmation=True,
)

AUTONOMOUS_CONFIG = ExplorationConfig(
    max_requests_per_minute=20,
    budget_cap_usd=2.00,
    max_exploration_depth=3,
    require_confirmation=False,  # ⚠️ Use with caution
    domain_allowlist=[  # Restrict to trusted domains
        "wikipedia.org",
        "docs.python.org",
        "developer.mozilla.org",
        "stackoverflow.com",
    ],
)

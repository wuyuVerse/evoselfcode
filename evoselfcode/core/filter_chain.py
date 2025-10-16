from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional

from .config_manager import ConfigManager


FilterFunc = Callable[[Any], bool]


class FilterChain:
    """
    Chain of filters for processing candidates.
    Supports composable filtering with statistics.
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.filters: List[tuple[str, FilterFunc]] = []
        self.stats: Dict[str, int] = {}
    
    def add_filter(self, name: str, filter_func: FilterFunc) -> "FilterChain":
        """Add a filter to the chain"""
        self.filters.append((name, filter_func))
        self.stats[name] = 0
        return self
    
    def filter_funcname_regex(self, name: str) -> bool:
        """
        Filter function name by regex.
        Empty names are rejected (failed extraction).
        """
        # First check if name is empty (extraction failed)
        if not name or not name.strip():
            return False  # Reject empty names
        
        # Then check regex pattern
        pattern = self.config.get("filters.name_regex", r"^[a-z_][a-z0-9_]{2,64}$")
        if not pattern or pattern == "":
            return True  # No regex filtering, accept all non-empty names
        
        return bool(re.match(pattern, name.strip()))
    
    def filter_funcname_weaklist(self, name: str) -> bool:
        """Filter function name by weaklist"""
        weaklist = self.config.get("namegen.weaklist", [])
        if not weaklist or weaklist is None:
            return True  # No weaklist configured, accept all
        return name.lower() not in [w.lower() for w in weaklist]
    
    def filter_code_length(self, code: str) -> bool:
        """Filter code by minimum length"""
        min_len = self.config.get("filters.min_code_len", 16)
        return len(code.strip()) >= min_len
    
    def apply(self, items: List[Any], extract_key: Optional[Callable] = None) -> List[Any]:
        """
        Apply all filters in the chain.
        
        Args:
            items: List of items to filter
            extract_key: Function to extract value from item for filtering
        
        Returns:
            Filtered list of items
        """
        self.stats = {name: 0 for name, _ in self.filters}
        filtered = items
        
        for filter_name, filter_func in self.filters:
            before_count = len(filtered)
            
            if extract_key:
                filtered = [item for item in filtered if filter_func(extract_key(item))]
            else:
                filtered = [item for item in filtered if filter_func(item)]
            
            removed = before_count - len(filtered)
            self.stats[filter_name] = removed
        
        return filtered
    
    def get_stats(self) -> Dict[str, int]:
        """Get filtering statistics"""
        return dict(self.stats)
    
    @classmethod
    def for_funcname(cls, config: ConfigManager) -> "FilterChain":
        """Create filter chain for function names"""
        chain = cls(config)
        chain.add_filter("regex", chain.filter_funcname_regex)
        chain.add_filter("weaklist", chain.filter_funcname_weaklist)
        return chain
    
    @classmethod
    def for_code(cls, config: ConfigManager) -> "FilterChain":
        """Create filter chain for code"""
        chain = cls(config)
        chain.add_filter("min_length", chain.filter_code_length)
        # Can add more: AST check, ruff, etc.
        return chain


"""
Temporal expression parser.

Parses natural language temporal expressions into structured dates/times.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TemporalExpression:
    """A parsed temporal expression."""
    
    original: str
    expression_type: str  # "point", "interval", "relative", "duration"
    
    # Parsed values
    start: datetime | None = None
    end: datetime | None = None
    duration: timedelta | None = None
    
    # For relative expressions
    anchor: str | None = None  # "now", "event_X"
    offset: timedelta | None = None
    
    # Confidence
    confidence: float = 1.0
    
    @property
    def is_point(self) -> bool:
        """Check if this is a point in time."""
        return self.expression_type == "point"
    
    @property
    def is_interval(self) -> bool:
        """Check if this is an interval."""
        return self.expression_type == "interval" or (self.start and self.end)


class TemporalParser:
    """
    Parses temporal expressions from text.
    
    Handles:
    - Absolute dates: "January 15, 2024", "2024-01-15"
    - Relative expressions: "yesterday", "last week", "3 days ago"
    - Durations: "for 2 hours", "lasting 3 weeks"
    - Ranges: "from 2020 to 2024", "between March and June"
    """
    
    # Patterns for date extraction
    ISO_DATE = r"\d{4}-\d{2}-\d{2}"
    US_DATE = r"\d{1,2}/\d{1,2}/\d{4}"
    MONTH_DAY_YEAR = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}"
    YEAR_ONLY = r"\b(19|20)\d{2}\b"
    
    # Relative patterns
    RELATIVE_PAST = r"(\d+)\s+(days?|weeks?|months?|years?)\s+ago"
    RELATIVE_FUTURE = r"in\s+(\d+)\s+(days?|weeks?|months?|years?)"
    
    def __init__(self, reference_time: datetime | None = None):
        """Initialize parser with reference time."""
        self.reference_time = reference_time or datetime.now()
    
    def parse(self, text: str) -> list[TemporalExpression]:
        """
        Parse temporal expressions from text.
        
        Args:
            text: Text containing temporal expressions
        
        Returns:
            List of parsed expressions
        """
        expressions = []
        
        # Try ISO dates
        for match in re.finditer(self.ISO_DATE, text):
            try:
                dt = datetime.strptime(match.group(), "%Y-%m-%d")
                expressions.append(TemporalExpression(
                    original=match.group(),
                    expression_type="point",
                    start=dt,
                    confidence=1.0,
                ))
            except ValueError:
                pass
        
        # Try Month Day, Year format
        for match in re.finditer(self.MONTH_DAY_YEAR, text, re.IGNORECASE):
            try:
                # Normalize the match
                date_str = match.group().replace(",", "")
                dt = datetime.strptime(date_str, "%B %d %Y")
                expressions.append(TemporalExpression(
                    original=match.group(),
                    expression_type="point",
                    start=dt,
                    confidence=0.95,
                ))
            except ValueError:
                pass
        
        # Try year only
        for match in re.finditer(self.YEAR_ONLY, text):
            year = int(match.group())
            expressions.append(TemporalExpression(
                original=match.group(),
                expression_type="interval",
                start=datetime(year, 1, 1),
                end=datetime(year, 12, 31),
                confidence=0.8,
            ))
        
        # Try relative past expressions
        for match in re.finditer(self.RELATIVE_PAST, text, re.IGNORECASE):
            amount = int(match.group(1))
            unit = match.group(2).lower().rstrip("s")
            
            delta = self._make_timedelta(amount, unit)
            dt = self.reference_time - delta
            
            expressions.append(TemporalExpression(
                original=match.group(),
                expression_type="relative",
                start=dt,
                anchor="now",
                offset=-delta,
                confidence=0.9,
            ))
        
        # Try relative future expressions
        for match in re.finditer(self.RELATIVE_FUTURE, text, re.IGNORECASE):
            amount = int(match.group(1))
            unit = match.group(2).lower().rstrip("s")
            
            delta = self._make_timedelta(amount, unit)
            dt = self.reference_time + delta
            
            expressions.append(TemporalExpression(
                original=match.group(),
                expression_type="relative",
                start=dt,
                anchor="now",
                offset=delta,
                confidence=0.9,
            ))
        
        # Named relative expressions
        named_relatives = {
            "yesterday": -1,
            "today": 0,
            "tomorrow": 1,
            "last week": -7,
            "next week": 7,
            "last month": -30,
            "next month": 30,
            "last year": -365,
            "next year": 365,
        }
        
        text_lower = text.lower()
        for phrase, days in named_relatives.items():
            if phrase in text_lower:
                delta = timedelta(days=days)
                dt = self.reference_time + delta
                
                expressions.append(TemporalExpression(
                    original=phrase,
                    expression_type="relative",
                    start=dt,
                    anchor="now",
                    offset=delta,
                    confidence=0.95,
                ))
        
        # Remove duplicates (same start time)
        seen = set()
        unique = []
        for expr in expressions:
            key = (expr.start, expr.end, expr.original)
            if key not in seen:
                seen.add(key)
                unique.append(expr)
        
        return unique
    
    def _make_timedelta(self, amount: int, unit: str) -> timedelta:
        """Create timedelta from amount and unit."""
        if unit == "day":
            return timedelta(days=amount)
        elif unit == "week":
            return timedelta(weeks=amount)
        elif unit == "month":
            return timedelta(days=amount * 30)  # Approximate
        elif unit == "year":
            return timedelta(days=amount * 365)  # Approximate
        else:
            return timedelta(days=amount)
    
    def normalize(self, text: str) -> str:
        """
        Normalize temporal expressions in text.
        
        Converts relative expressions to absolute dates.
        """
        expressions = self.parse(text)
        
        result = text
        for expr in sorted(expressions, key=lambda e: len(e.original), reverse=True):
            if expr.start:
                date_str = expr.start.strftime("%Y-%m-%d")
                result = result.replace(expr.original, date_str)
        
        return result
    
    def extract_range(self, text: str) -> tuple[datetime | None, datetime | None]:
        """
        Extract a date range from text.
        
        Handles: "from X to Y", "between X and Y", "X - Y"
        """
        # Pattern: from X to Y
        pattern = r"from\s+(.+?)\s+to\s+(.+?)(?:\.|,|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            start_exprs = self.parse(match.group(1))
            end_exprs = self.parse(match.group(2))
            
            start = start_exprs[0].start if start_exprs else None
            end = end_exprs[0].start if end_exprs else None
            
            return (start, end)
        
        # Pattern: between X and Y
        pattern = r"between\s+(.+?)\s+and\s+(.+?)(?:\.|,|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            start_exprs = self.parse(match.group(1))
            end_exprs = self.parse(match.group(2))
            
            start = start_exprs[0].start if start_exprs else None
            end = end_exprs[0].start if end_exprs else None
            
            return (start, end)
        
        return (None, None)

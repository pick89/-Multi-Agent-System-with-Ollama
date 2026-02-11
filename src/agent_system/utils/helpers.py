"""
Helper utilities for the agent system
"""

import re
from typing import List, Optional
from datetime import datetime, timedelta


def extract_code_blocks(text: str) -> List[str]:
    """Extract code blocks from markdown text"""
    pattern = r'```(?:\w+)?\n(.*?)```'
    return re.findall(pattern, text, re.DOTALL)


def detect_language(code: str) -> Optional[str]:
    """Detect programming language from code"""
    # Simple heuristic detection
    patterns = {
        'python': r'def |import |from |class |if __name__|print\(',
        'javascript': r'function |const |let |var |=>|console\.log',
        'typescript': r'interface |type |: string|: number|: any',
        'java': r'public class|private void|System\.out|@Override',
        'go': r'func |package main|import \(',
        'rust': r'fn |let mut|println!|impl ',
        'c': r'#include <|int main\(\)|printf\(',
        'cpp': r'#include <iostream>|std::|cout <<|using namespace',
    }

    for lang, pattern in patterns.items():
        if re.search(pattern, code, re.IGNORECASE):
            return lang

    return None


def parse_time_expression(text: str) -> Optional[datetime]:
    """Parse natural language time expressions"""
    now = datetime.now()
    text = text.lower()

    # Relative times
    if 'in ' in text:
        if 'minute' in text:
            minutes = int(re.search(r'(\d+)\s*minute', text).group(1))
            return now + timedelta(minutes=minutes)
        elif 'hour' in text:
            hours = int(re.search(r'(\d+)\s*hour', text).group(1))
            return now + timedelta(hours=hours)

    # Specific times
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)',
        r'(\d{1,2})\s*(am|pm)',
        r'at (\d{1,2})',
    ]

    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            # Parse time and return datetime
            pass

    return None


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
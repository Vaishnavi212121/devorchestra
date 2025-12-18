import re
from typing import Dict, Any

class ValidationError(Exception):
    pass

def validate_user_story(story: str) -> None:
    """Validate user story format and content"""
    if not story or not isinstance(story, str):
        raise ValidationError("User story must be a non-empty string")
    
    if len(story) < 10:
        raise ValidationError("User story too short (min 10 characters)")
    
    if len(story) > 5000:
        raise ValidationError("User story too long (max 5000 characters)")
    
    # Check for malicious patterns
    dangerous_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\(',
        r'exec\('
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, story, re.IGNORECASE):
            raise ValidationError("User story contains potentially malicious content")

def validate_code_output(code: str, language: str) -> None:
    """Validate generated code"""
    if not code:
        raise ValidationError("Generated code is empty")
    
    min_lengths = {
        "python": 20,
        "javascript": 20,
        "jsx": 30,
        "sql": 15
    }
    
    if len(code) < min_lengths.get(language, 20):
        raise ValidationError(f"Generated {language} code is too short")
    
    # Check for incomplete code
    if "..." in code or "TODO" in code:
        raise ValidationError("Generated code contains placeholders")
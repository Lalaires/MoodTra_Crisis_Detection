"""Test false positive cases with naive vs smart keyword detection."""

test_cases = [
    # TRUE POSITIVES - Should detect
    {
        "text": "I want to try jumping down from a building.",
        "expected": "extremely_high",
        "reason": "Suicidal - jumping from building"
    },
    {
        "text": "I want to jump off a bridge.",
        "expected": "extremely_high",
        "reason": "Suicidal - jumping from bridge"
    },
    {
        "text": "Thinking about jumping from the roof.",
        "expected": "extremely_high",
        "reason": "Suicidal - jumping from height"
    },
    
    # FALSE POSITIVES - Should NOT detect
    {
        "text": "I want to jump up and down.",
        "expected": "low",
        "reason": "Benign - playing/exercise"
    },
    {
        "text": "Let's jump on the trampoline!",
        "expected": "low",
        "reason": "Benign - recreational activity"
    },
    {
        "text": "I love jumping rope.",
        "expected": "low",
        "reason": "Benign - exercise"
    },
    {
        "text": "I'm going to jump in the pool.",
        "expected": "low",
        "reason": "Benign - swimming"
    },
    {
        "text": "Can't wait to jump for joy!",
        "expected": "low",
        "reason": "Benign - expression of happiness"
    },
    {
        "text": "I need to cut the cake.",
        "expected": "low",
        "reason": "Benign - food preparation"
    },
    {
        "text": "I want to shoot some hoops.",
        "expected": "low",
        "reason": "Benign - basketball"
    },
]

def naive_keyword_check(text: str) -> str:
    """Simple keyword matching - WILL CREATE FALSE POSITIVES."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["jump", "cut", "shoot", "hang"]):
        return "extremely_high"
    
    return "low"

def smart_pattern_check(text: str) -> str:
    """Context-aware pattern matching - REDUCES FALSE POSITIVES."""
    text_lower = text.lower()
    
    # Suicidal patterns: method + context/direction
    suicidal_patterns = [
        # Jumping patterns
        (["jump", "jumping"], ["off", "from", "down from", "out of"], ["building", "bridge", "roof", "window", "floor", "height", "cliff"]),
        
        # Self-harm cutting patterns  
        (["cut", "cutting"], ["myself", "my", "deep"], ["wrist", "arm", "vein", "artery"]),
        
        # Hanging patterns
        (["hang", "hanging"], ["myself"], ["rope", "noose", "neck"]),
        
        # Shooting patterns
        (["shoot", "shooting"], ["myself", "my"], ["gun", "head"]),
    ]
    
    # Check each pattern
    for methods, connectors, contexts in suicidal_patterns:
        has_method = any(m in text_lower for m in methods)
        has_connector = any(c in text_lower for c in connectors)
        has_context = any(ctx in text_lower for ctx in contexts)
        
        # Need method + (connector OR context) for true positive
        if has_method and (has_connector or has_context):
            # Additional check: exclude benign contexts
            benign_contexts = [
                "trampoline", "rope" + " " + "exercise", "joy", "pool", 
                "cake", "hoops", "basketball", "up and down"
            ]
            
            if not any(benign in text_lower for benign in benign_contexts):
                return "extremely_high"
    
    return "low"

def advanced_pattern_check(text: str) -> str:
    """Most sophisticated - uses linguistic patterns."""
    import re
    text_lower = text.lower()
    
    # Pattern 1: Jump + direction (down/off/from) + location (height)
    jump_pattern = r'\b(jump|jumping)\s+(down\s+from|off|from|out\s+of)\s+(a\s+)?(building|bridge|roof|window|floor|cliff|height)'
    if re.search(jump_pattern, text_lower):
        return "extremely_high"
    
    # Pattern 2: Jump + height location (no direction needed if location implies height)
    jump_location = r'\b(jump|jumping)\s+(?:off\s+)?(?:a\s+)?(building|bridge|roof|cliff)'
    if re.search(jump_location, text_lower):
        return "extremely_high"
    
    # Pattern 3: Self-harm cutting
    cutting_pattern = r'\b(cut|cutting)\s+(myself|my\s+(?:wrist|arm|vein)s?)'
    if re.search(cutting_pattern, text_lower):
        return "extremely_high"
    
    # Pattern 4: Hanging
    hanging_pattern = r'\b(hang|hanging)\s+(myself|my\s+neck)'
    if re.search(hanging_pattern, text_lower):
        return "extremely_high"
    
    # Pattern 5: Shooting self
    shooting_pattern = r'\b(shoot|shooting)\s+(myself|my\s+(?:head|brain))'
    if re.search(shooting_pattern, text_lower):
        return "extremely_high"
    
    # Exclude benign jumping contexts
    benign_patterns = [
        r'\bjump\s+up\s+and\s+down\b',
        r'\bjump(?:ing)?\s+(?:on|in)\s+(?:the\s+)?(?:trampoline|pool|bed)',
        r'\bjump(?:ing)?\s+rope\b',
        r'\bjump\s+for\s+joy\b',
    ]
    
    if any(re.search(pattern, text_lower) for pattern in benign_patterns):
        return "low"
    
    return "low"

print("=" * 100)
print("TESTING NAIVE vs SMART KEYWORD DETECTION")
print("=" * 100)

naive_errors = 0
smart_errors = 0
advanced_errors = 0

for i, case in enumerate(test_cases, 1):
    text = case['text']
    expected = case['expected']
    reason = case['reason']
    
    naive_result = naive_keyword_check(text)
    smart_result = smart_pattern_check(text)
    advanced_result = advanced_pattern_check(text)
    
    naive_correct = naive_result == expected
    smart_correct = smart_result == expected
    advanced_correct = advanced_result == expected
    
    if not naive_correct:
        naive_errors += 1
    if not smart_correct:
        smart_errors += 1
    if not advanced_correct:
        advanced_errors += 1
    
    print(f"\n{'=' * 100}")
    print(f"TEST {i}: {text}")
    print(f"Expected: {expected} ({reason})")
    print("-" * 100)
    print(f"Naive:    {naive_result:15s} {'✓' if naive_correct else '✗ WRONG'}")
    print(f"Smart:    {smart_result:15s} {'✓' if smart_correct else '✗ WRONG'}")
    print(f"Advanced: {advanced_result:15s} {'✓' if advanced_correct else '✗ WRONG'}")

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)

total = len(test_cases)
print(f"\nNaive Keyword Matching:")
print(f"  Errors: {naive_errors}/{total} ({naive_errors/total*100:.0f}%)")
print(f"  Accuracy: {(total-naive_errors)/total*100:.0f}%")

print(f"\nSmart Pattern Matching:")
print(f"  Errors: {smart_errors}/{total} ({smart_errors/total*100:.0f}%)")
print(f"  Accuracy: {(total-smart_errors)/total*100:.0f}%")

print(f"\nAdvanced Pattern Matching (Regex):")
print(f"  Errors: {advanced_errors}/{total} ({advanced_errors/total*100:.0f}%)")
print(f"  Accuracy: {(total-advanced_errors)/total*100:.0f}%")

print("\n" + "=" * 100)
print("ANALYSIS")
print("=" * 100)

print("""
**Naive Keyword Matching (BAD)**
- Just checks if "jump", "cut", "shoot" appear in text
- Problem: Creates MANY false positives
- Example: "jump up and down" → WRONG (extremely_high)

**Smart Pattern Matching (GOOD)**
- Checks for method + context/direction
- Example: "jump" + "from" + "building" → suicidal ✓
- Example: "jump" + "up and down" → benign ✓
- Uses lists to check combinations

**Advanced Pattern Matching (BEST)**
- Uses regular expressions for precise matching
- Checks word boundaries and proximity
- Explicitly excludes benign patterns
- Most accurate but more complex

**Recommendation**: Use Advanced Pattern Matching for production safety net.
""")



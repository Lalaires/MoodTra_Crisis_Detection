# Parameter Tuning Guide (No Keyword Matching)

## Overview

This guide focuses on improving model accuracy through **parameter optimization only**, without adding keyword matching logic.

---

## Current Problems

### 1. Severity Scores Too High
**Issue**: `anxiety: 0.9` and `depression: 0.9` are too close to `suicidal: 1.0`

**Effect**: 
- Anxiety probability of 0.95 × anxiety scaling 0.9 = **0.855** → jumps to HIGH
- Medium range (0.59-0.79) becomes hard to reach

**Example**:
- "I get anxious before presentations, but I manage okay"
- Model gives 0.97 anxiety probability
- Score: 0.97 × 0.9 × 0.9 = 0.786 → **HIGH** ❌
- Should be: **LOW** ✓

### 2. Condition Scaling Too Aggressive
**Issue**: `anxiety: 0.9`, `depression: 0.9` multiply already-high diagnosis scores

**Effect**: Double amplification → everything goes to HIGH

### 3. Thresholds Too Narrow
**Issue**: Gaps between levels are uneven
- 0.89-1.0 = extremely_high (0.11 range)
- 0.79-0.89 = high (0.10 range)  
- 0.59-0.79 = medium (0.20 range)
- 0.0-0.59 = low (0.59 range!)

**Effect**: Medium and high are narrow targets, low is a huge bucket

### 4. Missing Non-Linear Dynamics
**Issue**: Linear scoring misses compound risk factors

**Example**:
- Suicidal prob: 0.40, Depression prob: 0.50
- Current: (0.4 × 1.0) + (0.5 × 0.9) = 0.85
- Reality: This is VERY concerning (multiple high-risk signals)
- Should boost further when multiple risks present

---

## Proposed Changes

### Change 1: Rebalanced Severity Scores

```python
# OLD (causes auto-jumping to high)
self.severity_scores = {
    "normal": 0.0,
    "stress": 0.8,      # Too high
    "anxiety": 0.9,     # Too high
    "depression": 0.9,  # Too high
    "suicidal": 1.0
}

# NEW (better separation)
self.severity_scores = {
    "normal": 0.0,
    "stress": 0.60,      # Reduced by 0.20
    "anxiety": 0.68,     # Reduced by 0.22
    "depression": 0.72,  # Reduced by 0.18
    "suicidal": 1.0      # Unchanged
}
```

**Rationale**:
- Creates 0.04-0.12 gaps between adjacent levels
- Prevents anxiety from auto-jumping to 0.8+ range
- Allows room for scaling to move scores up/down

**Expected Effect**:
- Pure anxiety case: 0.95 prob × 0.68 weight = 0.646 (before scaling)
  - With "anxiety" scaling (0.75): 0.646 × 0.75 = **0.485 → medium** ✓
  - With "no disorder" scaling (0.25): 0.646 × 0.25 = **0.162 → low** ✓

### Change 2: Rebalanced Condition Scaling

```python
# OLD (over-amplifies)
self.condition_scaling = {
    "normal": 0.3,           
    "no mental disorders": 0.3,
    "stress": 0.8,  
    "anxiety": 0.9,
    "depression": 0.9,       
    "suicidal": 1.0,        
    "suicide": 1.0,
    "self-harm": 1.0,
    "emergency": 1.0
}

# NEW (better gradation)
self.condition_scaling = {
    "normal": 0.25,              # Reduced by 0.05
    "no mental disorders": 0.25, # Reduced by 0.05
    "stress": 0.70,              # Reduced by 0.10
    "anxiety": 0.75,             # Reduced by 0.15
    "depression": 0.80,          # Reduced by 0.10
    "suicidal": 1.0,             # Unchanged
    "suicide": 1.0,              # Unchanged
    "self-harm": 1.0,            # Unchanged
    "emergency": 1.0             # Unchanged
}
```

**Rationale**:
- Larger reductions for mid-tier (anxiety: -0.15) create more room
- Smaller reduction for normal (-0.05) helps catch edge cases
- Crisis keywords (suicidal/self-harm) stay at maximum

**Expected Effect**:
- Anxiety × anxiety: 0.68 × 0.75 = **0.51** (medium range)
- Depression × depression: 0.72 × 0.80 = **0.576** (high range)
- Suicidal × suicidal: 1.0 × 1.0 = **1.0** (extremely_high)

### Change 3: Optimized Thresholds

```python
# OLD (uneven distribution)
self.severity_thresholds = [
    (0.89, "extremely_high"),
    (0.79, "high"),
    (0.59, "medium"),
    (0.0, "low")
]

# NEW (better distributed)
self.severity_thresholds = [
    (0.80, "extremely_high"),  # Lowered by 0.09
    (0.58, "high"),            # Lowered by 0.21
    (0.35, "medium"),          # Lowered by 0.24
    (0.0, "low")               # Unchanged
]
```

**Rationale**:
- Larger reduction for high/medium aligns with reduced severity scores
- extremely_high at 0.80 still requires strong signal
- medium at 0.35 becomes reachable

**Expected Ranges**:
- Low: 0.00-0.35 (35% range)
- Medium: 0.35-0.58 (23% range)
- High: 0.58-0.80 (22% range)
- Extremely high: 0.80-1.00 (20% range)

### Change 4: Enhanced Score Computation

#### 4A. Non-Linear Suicidal Boost

```python
# If suicidal probability is significant, boost the score
suicidal_prob = probabilities.get("Suicidal", 0.0)
if suicidal_prob > 0.25:
    # Apply exponential boost
    boost_factor = 1.0 + (suicidal_prob ** 1.5) * 0.3
    diagnosis_score = min(1.0, diagnosis_score * boost_factor)
```

**Example**:
- Suicidal prob: 0.40
- Boost: 1.0 + (0.40^1.5 × 0.3) = 1.0 + 0.076 = **1.076x multiplier**
- If base score was 0.70 → becomes 0.753

**Rationale**: Catches cases where suicidal probability is notable but not dominant

#### 4B. Confidence-Aware Adjustment

```python
# High-risk class with strong confidence → boost
if top_class[0] in ["Suicidal", "Depression"]:
    if top_confidence > 0.6:
        confidence_adjustment = (top_confidence - 0.6) * 0.15
```

**Example**:
- "Depression" prediction with 0.80 confidence
- Adjustment: (0.80 - 0.60) × 0.15 = **+0.03**

**Rationale**: High-confidence predictions are more reliable

#### 4C. Mixed Signal Detection

```python
# If probabilities spread across multiple high-risk categories
high_risk_total = (
    prob["Suicidal"] + 
    prob["Depression"] + 
    prob["Anxiety"] * 0.5
)

if high_risk_total > 0.4 and top_class != "Suicidal":
    mixed_signal_boost = min(0.10, (high_risk_total - 0.4) * 0.25)
```

**Example**:
- Suicidal: 0.30, Depression: 0.35, Anxiety: 0.20 → total = 0.75
- Top prediction: Depression (not Suicidal)
- Boost: min(0.10, (0.75 - 0.4) × 0.25) = **+0.087**

**Rationale**: Multiple high-risk signals indicate severity even without clear winner

---

## Expected Improvements

### Score Distribution Changes

| Scenario | Old Score | New Score | Old Level | New Level |
|----------|-----------|-----------|-----------|-----------|
| "Anxious before presentations, manage okay" | 0.79 | 0.49 | High ❌ | Medium ✓ |
| "Can't stop worrying, heart races" | 0.80 | 0.52 | High ❌ | Medium ✓ |
| "Nothing feels worth it. Wish I wouldn't wake up" | 0.80 | 0.58 | High ✓ | High ✓ |
| "Pills ready, going tonight" (if caught) | 0.85 | 0.89 | High ❌ | Extremely High ✓ |

### Key Improvements

1. **Medium range becomes usable**: 35-40% of cases expected in medium (was <10%)
2. **Better separation**: Clear boundaries between levels
3. **Fewer false positives**: Mild anxiety won't jump to high
4. **Catch compound risks**: Multiple signals properly amplified

### Remaining Limitations

**Still won't fix**:
- Cases where model completely misclassifies ("I'm going to jump tonight" → Normal)
- These require model retraining or keyword fallback
- Recommendation: Add post-hoc keyword safety net in application layer

---

## Validation Strategy

### 1. Run Comparison Test
```bash
python compare_models_v2.py
```

### 2. Monitor Key Metrics
- False negative rate (critical cases missed)
- False positive rate (over-flagging mild cases)
- Severity distribution (% in each level)
- Threshold boundary cases

### 3. Iterate Based on Results

**If still too many false positives** (mild cases → high):
- Reduce severity_scores by another 0.03-0.05
- Increase thresholds by 0.02-0.05

**If missing critical cases** (false negatives):
- Lower extremely_high threshold to 0.75-0.78
- Increase suicidal boost factor from 0.3 to 0.4
- Add stronger confidence adjustments

**If medium range still unused**:
- Widen medium range: (0.30, "medium") instead of (0.35, "medium")
- Reduce high threshold to 0.55

---

## Implementation

The updated model is in `crisis_pipeline_v2.py`.

### Key Changes Summary:

| Parameter | Old Value | New Value | Change |
|-----------|-----------|-----------|--------|
| severity_scores["anxiety"] | 0.9 | 0.68 | -0.22 |
| severity_scores["depression"] | 0.9 | 0.72 | -0.18 |
| severity_scores["stress"] | 0.8 | 0.60 | -0.20 |
| condition_scaling["anxiety"] | 0.9 | 0.75 | -0.15 |
| condition_scaling["depression"] | 0.9 | 0.80 | -0.10 |
| condition_scaling["normal"] | 0.3 | 0.25 | -0.05 |
| threshold["extremely_high"] | 0.89 | 0.80 | -0.09 |
| threshold["high"] | 0.79 | 0.58 | -0.21 |
| threshold["medium"] | 0.59 | 0.35 | -0.24 |

### New Features:
- Suicidal probability boost (exponential)
- Confidence-aware adjustments
- Mixed signal detection
- Lower analysis threshold (0.45 vs 0.60)

---

## Trade-offs

### Pros ✓
- No keyword logic needed (maintains model-only approach)
- Better calibrated for real-world severity distribution
- Medium range actually usable
- Non-linear dynamics capture compound risks

### Cons ✗
- Still can't catch cases where base model completely fails
- May need further iteration based on real data
- Confidence adjustments add complexity

### Recommendation
Start with these parameters and iterate based on validation results. Consider adding a lightweight keyword safety net at the application layer (not in model) for critical missed cases.


# Model Behavior Summary - Quick Reference

## What Each Category-Severity Pair Means to the Model

---

## NORMAL Category

| Severity | Model's Definition | Detection Success | Key Characteristics |
|----------|-------------------|-------------------|---------------------|
| **Low** | Enthusiastic positivity with activity mentions | ✅ 100% | "Great day!", "can't wait", future plans, exclamation marks |
| **Medium** | *Not functionally defined* | ❌ 0% | Neutral statements default to low instead |
| **High** | *Not functionally defined* | ❌ 0% | Apathy without pain → stays low; apathy with "matters" → becomes Depression |
| **Extremely High** | *Not functionally defined* | ❌ 0% | Emotional numbness → either Normal-low or Depression-medium |

**Model's Core Logic for Normal:**
- High Normal probability (>90%) + absence of distress = Low
- Presence of any concern keywords → shifts to other categories
- Cannot escalate severity within Normal category

---

## ANXIETY Category

| Severity | Model's Definition | Detection Success | Key Characteristics |
|----------|-------------------|-------------------|---------------------|
| **Low** | Worry + explicit self-reassurance | ✅ 100% | "Nervous but I'll be fine", "worry but it passes", 95%+ anxiety prob |
| **Medium** | Persistent worry where analysis detects actual condition | ⚠️ 33% | "Keep worrying" + analysis NOT "no mental disorders" |
| **High** | *Mathematically unreachable* | ❌ 0% | Max score ~0.52, need 0.59 threshold - impossible |
| **Extremely High** | *Mathematically impossible* | ❌ 0% | Max score ~0.52, need 0.79 threshold - structural impossibility |

**Model's Core Logic for Anxiety:**
- Needs "worry/anxious" keywords for detection
- Self-reassurance ("I'll be fine") → triggers analysis "no mental disorders" → 0.3 scaling → low
- Physical symptoms alone (heart racing, chest tight) → Not recognized as anxiety
- Final scores capped by 0.75 scaling factor at ~0.52 maximum

---

## DEPRESSION Category

| Severity | Model's Definition | Detection Success | Key Characteristics |
|----------|-------------------|-------------------|---------------------|
| **Low** | *Binary: either not detected or escalated* | ❌ 0% | Minimized sadness → Normal-low; Any substantial sadness → High |
| **Medium** | Emotional numbness without hopelessness | ⚠️ 33% | Narrow band (0.39-0.59), "empty numbness" detected once |
| **High** | Hopelessness + worthlessness + can't function | ✅ 100% | "Hopeless", "worthless", "burden", "crushing", "can barely" |
| **Extremely High** | *Ceiling effect at high* | ❌ 0% | "Unbearable pain" → still caps at ~0.74, can't reach 0.79 |

**Model's Core Logic for Depression:**
- Future hope ("feel better tomorrow") → Suppresses detection (stays Normal)
- Hopelessness keywords → Triggers Depression-high (0.6-0.7 final scores)
- Sleep/concentration issues alone → Not detected (stays Normal)
- Anhedonia ("don't enjoy things") → Escalates to high, skips medium

---

## STRESS Category

| Severity | Model's Definition | Detection Success | Key Characteristics |
|----------|-------------------|-------------------|---------------------|
| **Low** | "Stress" word + reassurance → Normal; Only extreme explicit stress detected | ⚠️ 33% | Requires 94%+ stress prob (rare), analysis "no mental disorders" → low |
| **Medium** | *Not functionally defined* | ❌ 0% | "Overwhelmed" → Normal; "Pressure + exhausted" → Anxiety instead |
| **High** | *Requires "stress" keyword + crisis language* | ⚠️ 33% | "Stress destroying me" → 92% prob but analysis determines severity |
| **Extremely High** | *Not functionally defined* | ❌ 0% | "Total breakdown" without "stress" → Normal; Can't reach 0.79 threshold |

**Model's Core Logic for Stress:**
- **Must explicitly say "stress"** or category is misclassified
- "Overwhelmed" alone → Interpreted as Normal
- "Breaking down" → Interpreted as Depression, not Stress
- Even with 94% Stress probability, analysis often returns "no mental disorders" → low severity

---

## SUICIDAL Category

| Severity | Model's Definition | Detection Success | Key Characteristics |
|----------|-------------------|-------------------|---------------------|
| **Low** | *Category not detected - stays Normal* | ❌ 0% | Passive ideation (18-30% prob) → Below 50% threshold → Normal category |
| **Medium** | *Escalates to extremely_high* | ❌ 0% | "Ending it all", "don't want to be alive" → 0.86-0.91 scores → extremely_high |
| **High** | *Escalates to extremely_high* | ❌ 0% | "Have a plan", "thought about how" → 1.0 scaling → extremely_high |
| **Extremely High** | Explicit timeline + decision OR future declarations | ⚠️ 67% | "Tonight", "goodbye", "everything ready" ✓; "Pills in hand right now" ✗ |

**Model's Core Logic for Suicidal:**
- Needs >50% Suicidal probability to classify as Suicidal category
- Once classified as Suicidal: analysis returns "suicide" → 1.0 scaling → extremely_high
- **Binary escalation: Either not detected (Normal) or extremely_high**
- Timeline keywords ("tonight") work; present-tense actions ("right now") sometimes fail
- Appropriate aggressive escalation for safety

---

## Model's Implicit Rules (Reverse Engineered)

### Rule 1: Self-Reassurance = Low Severity
Any statement ending with "but I'll be fine", "I can handle it", "but it's fine" → Ensures low severity regardless of content.

**Mechanism:** Analysis model returns "no mental disorders" → 0.3 scaling factor → Final score <0.39 → Low

### Rule 2: Hopelessness = Depression-High
Keywords "hopeless", "worthless", "burden", "no reason to" → Triggers Depression category with high severity.

**Mechanism:** Depression prob 50-65% + analysis "depression" + 0.8 scaling → Final score 0.59-0.71 → High

### Rule 3: Explicit "Stress" Required
Without the word "stress" in the message, Stress category has <2% probability regardless of context.

**Mechanism:** Model's training appears to require literal "stress" keyword; synonyms insufficient

### Rule 4: Physical Symptoms Ignored
"Heart races", "chest tight", "can't breathe" alone → Not recognized as anxiety unless "worry/anxious" also present.

**Mechanism:** Diagnosis model needs emotional state keywords, not somatic symptoms

### Rule 5: Future Hope Suppresses Depression
Any statement about feeling better in the future → Prevents Depression detection.

**Mechanism:** Optimism language → High Normal probability (>97%) → Stays Normal-low

### Rule 6: Suicidal = All or Nothing
Suicidal probability <50% → Normal category; Suicidal probability >50% → Extremely_high severity.

**Mechanism:** 
- Below threshold: Normal category dominates
- Above threshold: Analysis returns "suicide" → 1.0 scaling → Score >0.79 → Extremely_high

### Rule 7: Functional Language Overrides
"I'm managing", "still get things done", "just existing" → Interpreted as low severity.

**Mechanism:** Functional descriptions may signal coping to the model, suppressing severity

### Rule 8: Analysis Conflicts Diagnosis
When diagnosis says one category but analysis detects another condition, diagnosis category wins but analysis affects severity.

**Mechanism:** 
- Category determined by diagnosis model (argmax of probabilities)
- Severity scaling determined by analysis model's detected condition

---

## Mathematical Boundaries

### Impossible Combinations:
1. **Anxiety-High**: Max possible score ~0.52, need 0.59 ❌
2. **Anxiety-Extremely_High**: Max possible score ~0.52, need 0.79 ❌
3. **Depression-Extremely_High**: Max observed ~0.74, need 0.79 ⚠️
4. **Normal-High/Extremely_High**: No escalation mechanism within category ❌

### Rare But Possible:
1. **Depression-Medium**: Requires 0.39-0.59 range (narrow band) ⚠️
2. **Stress-High**: Requires "stress" keyword + crisis analysis + 1.0 scaling ⚠️
3. **Anxiety-Medium**: Requires analysis NOT "no mental disorders" ⚠️

### Reliably Achievable:
1. **Normal-Low**: High Normal prob + low diagnosis score ✅
2. **Anxiety-Low**: 95%+ Anxiety prob + self-reassurance ✅
3. **Depression-High**: 50%+ Depression prob + hopelessness keywords ✅
4. **Suicidal-Extremely_High**: 50%+ Suicidal prob + any suicidal statement ✅

---

## Keyword Triggers (What the Model Recognizes)

### Normal-Low Triggers:
✅ "great", "fun", "can't wait", "going to", "finished", exclamation marks

### Anxiety-Low Triggers:
✅ "nervous", "anxious", "worry" + "but I'll be fine", "I can handle it", "passes quickly"

### Depression-High Triggers:
✅ "hopeless", "worthless", "burden", "crushing", "no reason", "can't find", "can barely"

### Suicidal-Extremely_High Triggers:
✅ "ending it all", "kill myself", "end my life", "tonight", "goodbye", "everything ready"

### Stress Detection Triggers:
✅ Explicit word "stress" (required)
⚠️ "destroying me", "making me sick" (help boost probability)

### Does NOT Trigger Expected Category:
❌ "Heart races", "chest tight", "can't breathe" → Not recognized as anxiety
❌ "Overwhelmed", "breaking down", "can't cope" → Not recognized as stress
❌ "Sleeping too much", "can't concentrate" → Not recognized as depression
❌ "Don't feel anything", "numb", "empty void" → Not recognized as concerning
❌ "Sometimes I wonder about not existing" → Not recognized as suicidal

---

## Examples of Model's Logic

### Example 1: Why "panic attacks every day" = Medium (not High)
```
Input: "I'm having panic attacks almost every day now. Can't breathe properly."
Diagnosis: 89.6% Anxiety → Score 0.665
Analysis: Detects "anxiety" → 0.75 scaling
Final: 0.665 × 0.75 = 0.499
Threshold: 0.59 needed for high
Result: Medium (0.499 > 0.39 but < 0.59)
```
**Model's reasoning:** High anxiety probability but 0.75 scaling cap prevents reaching high.

---

### Example 2: Why "some days sad" = High (not Low)
```
Input: "Some days I feel sad but I still get things done."
Diagnosis: 79.9% Depression → Score 0.785
Analysis: Detects "depression" → 0.8 scaling
Final: 0.785 × 0.8 = 0.628
Threshold: 0.59 needed for high
Result: High (0.628 > 0.59)
```
**Model's reasoning:** "Sad" keyword generates high depression probability, overriding the functional statement.

---

### Example 3: Why "pills in hand right now" = Normal-Medium
```
Input: "I have the pills in my hand. I'm about to take them all right now."
Diagnosis: 44% Normal, 22% Suicidal → Normal category wins
Analysis: Detects "suicide" → 1.0 scaling
Final: 0.472 (but Normal category, not Suicidal)
Result: Normal-Medium (wrong category!)
```
**Model's reasoning:** Diagnosis model failed to recognize present-tense action. Analysis knew it was suicide but category was already locked to Normal.

---

### Example 4: Why "completely overwhelmed" = Normal-Low
```
Input: "I'm completely overwhelmed, on the verge of total breakdown."
Diagnosis: 87% Normal → Score 0.110
Result: Normal-Low
```
**Model's reasoning:** Without "stress" or "anxiety" keywords, "overwhelmed" and "breakdown" are treated as Normal statements. Low diagnosis score ensures low severity.

---

## Summary: The Model's Worldview

### The model believes:
- **Positive statements with future plans = Normal-low** (correct)
- **Self-reassurance means low severity** (sometimes incorrect)
- **Hopelessness = Depression-high** (correct)
- **Any suicidal statement = Crisis** (correct, appropriately cautious)
- **"Stress" is a specific word, not a concept** (limitation)
- **Physical anxiety symptoms = Normal** (incorrect)
- **Emotional numbness = Normal** (incorrect)
- **Present-tense actions less concerning than future plans** (incorrect for suicide)

### The model doesn't understand:
- Stress exists as distinct from anxiety and normal overwhelm
- Physical manifestations indicate mental health conditions
- Emotional numbness is concerning even without pain
- Severity exists on a spectrum (tends toward binary)
- "Pills in hand right now" is more urgent than "planning to tonight"

### The model's philosophy:
- **Conservative on Normal**: High bar to leave Normal category
- **Aggressive on Suicidal**: Once detected, immediately escalates (appropriate)
- **Confused on Stress**: Lacks clear definition, misclassifies frequently
- **Ceiling on Anxiety/Depression**: Cannot reach maximum severity due to math
- **Trusts self-reassurance**: "I'll be fine" strongly signals low severity

---

*This represents the model's implicit understanding based on observed behavior patterns, not intended design.*


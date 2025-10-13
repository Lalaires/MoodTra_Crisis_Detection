# Crisis Detection Model: Behavioral Definitions
## Understanding What the Model Actually Detects (crisis_pipeline.py)

This document describes what the model **actually detects** for each category-severity pair, based on observed behavior during comprehensive testing. These are the model's implicit definitions derived from its detection patterns, not prescriptive clinical definitions.

---

## 1. NORMAL Category

### Normal-Low (What the Model Detects)

**Model's Implicit Definition:** Positive statements about activities, explicit expressions of happiness or anticipation, and mentions of future plans with enthusiastic language.

**Successfully Detected Examples:**
- "I had a great day at school today! Math class was fun."
- "Just finished my homework. Now I'm going to play some video games."
- "Can't wait for the weekend! Going to the beach with my family."

**Model Detection Pattern:**
- Exclamation marks or enthusiastic punctuation
- Words like "great," "fun," "can't wait"
- Completion of tasks followed by leisure activities
- Future-oriented statements with positive framing
- Social or family activity mentions

**What Triggers This Classification:**
The model assigns Normal-low when it detects high confidence in the "Normal" category (>90%) and the diagnosis score is very low (<0.10). The combination of positive keywords and absence of distress signals creates this classification.

---

### Normal-Medium (What the Model Attempts to Detect)

**Model's Implicit Definition:** The model does not have a working definition for this level - it defaults neutral or slightly negative statements to Normal-low instead.

**What the Model Actually Does:**
- "School is okay I guess. Nothing special happening." → Classified as Normal-**low**
- "Sometimes I feel bored but it's fine." → Classified as Normal-**low**  
- "Life is just meh right now, not bad though." → Classified as Suicidal-low (confused!)

**Model Detection Pattern:**
The model does not distinguish between enthusiastically positive and neutrally okay statements. Both are processed as "Normal" category with low severity. The word "meh" particularly confuses the model, triggering suicidal classification.

**What This Reveals:**
The model appears to operate in binary mode for Normal: either clearly positive (low) or concerning enough to shift to another category. There's no middle ground for "neutral but unremarkable."

---

### Normal-High (What the Model Cannot Detect)

**Model's Implicit Definition:** The model does not recognize high-severity "normal" states (emotional detachment/apathy).

**What the Model Actually Does:**
- "I feel neutral about everything. Nothing really matters much." → Classified as Depression-low
- "Just going through the motions every day." → Classified as Normal-low
- "Everything feels flat and colorless but I'm managing." → Classified as Normal-low

**Model Detection Pattern:**
When apathy or emotional flatness is described:
- If combined with "nothing matters," it shifts to Depression category
- If describing routine without emotion, it stays Normal-low
- The model doesn't escalate severity within Normal category for detachment

**What This Reveals:**
The model cannot conceive of "high-severity normalcy." Emotional detachment either remains low-severity Normal (if functional language is present) or shifts to Depression (if existential language appears).

---

### Normal-Extremely_High (What the Model Cannot Detect)

**Model's Implicit Definition:** The model does not recognize severe dissociation or emotional numbness as a high-severity state within the Normal category.

**What the Model Actually Does:**
- "I don't feel anything anymore, just empty numbness." → Classified as Depression-medium
- "Complete emotional flatness, like I'm just existing." → Classified as Normal-low
- "Numb to everything around me, total emotional void." → Classified as Normal-low

**Model Detection Pattern:**
- "Empty numbness" + "don't feel anything" → Triggers Depression category (medium severity)
- "Just existing" → Remains Normal-low (functional language overrides concern)
- "Emotional void" → Remains Normal-low (model doesn't process "void" as critical)

**What This Reveals:**
The model requires emotional distress keywords ("empty," "numbness") to shift from Normal to Depression. Mere descriptions of flatness or existing without emotion don't trigger concern. The model seems to need pain or suffering language, not just absence of feeling.

---

## 2. ANXIETY Category

### Anxiety-Low (What the Model Detects)

**Model's Implicit Definition:** Statements about worry or nervousness that include explicit self-reassurance, temporary concerns, or minimizing language paired with high Anxiety probability (>95%).

**Successfully Detected Examples:**
- "I'm a little nervous about the test tomorrow but I'll be fine."
- "Sometimes I worry about things but it passes quickly."
- "Feeling a bit anxious about the presentation but I can handle it."

**Model Detection Pattern:**
- "A little nervous/anxious" + "but I'll be fine/I can handle it"
- "Sometimes" + "but it passes quickly"
- Specific event mentioned + self-reassurance
- Anxiety probability >95% with low diagnosis score (0.68-0.69)
- Analysis model returns "no mental disorders"

**What Triggers This Classification:**
The model detects very high probability of Anxiety category (95-97%) but the analysis component returns "no mental disorders," which applies a 0.3 scaling factor, resulting in low final severity. The self-reassurance language appears to suppress severity escalation.

---

### Anxiety-Medium (What the Model Attempts to Detect)

**Model's Implicit Definition:** Persistent worry statements where the analysis model detects an actual mental health concern (not "no mental disorders").

**Successfully Detected Example:**
- "I keep worrying about my grades and what people think of me." → Detected correctly as Anxiety-medium

**What the Model Missed:**
- "My heart races sometimes when I think about school stuff." → Classified as Normal-low
- "Can't stop thinking about all the things that could go wrong." → Classified as Normal-low

**Model Detection Pattern:**
For the successful detection:
- "Keep worrying" (persistence language)
- Multiple worry domains (grades + social perception)
- Anxiety probability 94%
- Analysis returned "depression" (not "no mental disorders"), applying 0.8 scaling
- Final score reached 0.545 → medium threshold

For the failures:
- Physical symptoms alone ("heart races") → Only 1.9% anxiety probability
- Rumination description ("can't stop thinking") → Only 1.6% anxiety probability

**What This Reveals:**
The diagnosis model doesn't recognize physical anxiety symptoms or rumination as anxiety unless the word "worry/anxious" is explicitly present. The analysis model needs to detect an actual condition (not return "no mental disorders") for medium severity to be reached.

---

### Anxiety-High (What the Model Cannot Detect)

**Model's Implicit Definition:** The model does not have a working pathway to reach high severity for anxiety.

**What the Model Actually Does:**
- "I can't sleep because my mind won't stop racing with worries." → Anxiety-low
- "My chest feels tight all the time and I'm constantly on edge." → Normal-low
- "I'm having panic attacks almost every day now. Can't breathe properly." → Anxiety-medium

**Model Detection Pattern:**
Even explicit mentions of "panic attacks almost every day":
- Anxiety probability: 89.6%
- Diagnosis score: 0.665
- Analysis returned "anxiety" (0.75 scaling)
- Final score: 0.499 → Just barely medium (0.39 threshold)

For "chest feels tight":
- Only 19.8% anxiety probability (diagnosis model failure)
- Classified as Normal instead

**What This Reveals:**
The model's final scores cap around 0.50-0.52 for anxiety, never reaching the 0.59 threshold for "high." Even with 90%+ anxiety probability and "anxiety" analysis result, the scaling math prevents high severity. The diagnosis model also fails to recognize physical manifestations as anxiety.

---

### Anxiety-Extremely_High (What the Model Cannot Detect)

**Model's Implicit Definition:** The model has no functional pathway to reach extremely_high for anxiety. This level is theoretically impossible with current parameters.

**What the Model Actually Does:**
- "I'm completely paralyzed by fear, can't leave my room anymore." → Anxiety-medium
- "Constant panic attacks, heart pounding so hard I think I'm dying." → Anxiety-medium  
- "Overwhelming terror that never stops, I'm trapped in endless anxiety." → Anxiety-low

**Model Detection Pattern:**
Best case scenario:
- 95% anxiety probability
- Analysis returns "anxiety" (0.75 scaling)
- Diagnosis score ~0.68
- Final score = 0.68 × 0.75 = 0.51 (far below 0.79 threshold)

Worst case:
- "Overwhelming terror" → Analysis returns "no mental disorders"
- 0.691 × 0.3 = 0.207 final score → Low severity

**What This Reveals:**
Mathematical impossibility: Even perfect anxiety detection (100% probability, score 0.7) with "anxiety" scaling (0.75) yields 0.525 final score, which cannot reach the 0.79 extremely_high threshold. The parameters are fundamentally incompatible with detecting severe anxiety. The analysis model also frequently returns "no mental disorders" for extreme anxiety descriptions.

---

## 3. DEPRESSION Category

### Depression-Low (What the Model Cannot Detect)

**Model's Implicit Definition:** The model does not recognize mild, temporary sadness as low-severity depression.

**What the Model Actually Does:**
- "I've been feeling a bit down lately but it's not too bad." → Normal-low
- "Some days I feel sad but I still get things done." → Depression-**high** (escalated!)
- "Feeling a little blue today but I'll probably feel better tomorrow." → Normal-low

**Model Detection Pattern:**
For Normal-low classifications:
- "A bit down" + "not too bad" → 89% Normal probability
- "A little blue" + "feel better tomorrow" → 97% Normal probability
- Minimizing language prevents Depression detection

For the escalation:
- "Sad" + "still get things done" → 79.9% Depression probability
- High diagnosis score: 0.785
- Analysis detected "depression" (0.8 scaling)
- Final score: 0.628 → High severity

**What This Reveals:**
The model can't find middle ground. Either sadness is minimized enough to be Normal-low, or it's substantial enough to be Depression-high. The word "sad" paired with Depression probability >79% triggers high severity, bypassing low/medium entirely. Future-oriented hope ("feel better tomorrow") suppresses Depression detection.

---

### Depression-Medium (What the Model Rarely Detects)

**Model's Implicit Definition:** A narrow range where depression is detected but hopelessness language is absent.

**What the Model Actually Does:**
- "I don't enjoy things I used to like anymore. Everything feels hard." → Depression-high
- "I've been sleeping too much and don't want to get out of bed." → Normal-low
- "I feel really sad most days and it's hard to concentrate." → Normal-low

**One Successful Medium Detection:**
- "I don't feel anything anymore, just empty numbness." → Depression-medium
- Depression probability: 42.3%
- Diagnosis score: 0.570
- Analysis: "depression" (0.8 scaling)
- Final score: 0.456 → Medium

**Model Detection Pattern:**
For Depression-medium to occur:
- Depression probability 40-60% (not dominant)
- Analysis must return "depression"
- Score must land in narrow 0.39-0.59 range
- Cannot include hopelessness language (triggers high)

**What This Reveals:**
Medium depression requires a perfect storm: enough depression signal to trigger the category, but not enough to escalate to high. Anhedonia ("don't enjoy things") paradoxically triggers high severity. Sleep/concentration issues alone don't trigger Depression at all (stay Normal).

---

### Depression-High (What the Model Reliably Detects)

**Model's Implicit Definition:** Clear expressions of hopelessness, worthlessness, or inability to function, combined with depression probability >50%.

**Successfully Detected Examples:**
- "I can't find any reason to get up in the morning. Everything is hopeless."
- "I feel completely worthless and like a burden to everyone around me."
- "The sadness is crushing me. I can barely function anymore."

**Model Detection Pattern:**
Common elements:
- Keywords: "hopeless," "worthless," "burden," "crushing," "can barely function"
- Depression probability: 50-65%
- Often includes significant Suicidal probability (18-47%)
- Diagnosis scores: 0.74-0.88
- Analysis consistently returns "depression"
- Final scores: 0.59-0.71 (solidly above 0.59 high threshold)

**What Triggers This Classification:**
The combination of existential despair language ("no reason," "hopeless") plus functional impairment ("can barely function") generates:
1. Strong Depression probability
2. "Depression" analysis result (0.8 scaling)
3. Final scores that consistently exceed 0.59 threshold

**What This Reveals:**
This is the model's sweet spot. It reliably detects severe depression when both emotional pain (hopelessness/worthlessness) AND functional impact are explicitly stated. The model needs clear language about both suffering and inability to cope.

---

### Depression-Extremely_High (What the Model Caps At High)

**Model's Implicit Definition:** The model treats all extreme depression descriptions as high severity, unable to distinguish a beyond-high level.

**What the Model Actually Does:**
- "I see no point in continuing. The pain is unbearable and endless." → Depression-high
- "Complete despair, no light at the end of the tunnel, just darkness." → Depression-high
- "I'm drowning in hopelessness. Nothing will ever get better." → Depression-high

**Model Detection Pattern:**
Even with extreme language:
- Depression probabilities: 46-84%
- Suicidal probabilities: 31-41% (significant)
- Diagnosis scores: 0.80-0.92
- Analysis: "depression" (0.8 scaling)
- Final scores: 0.64-0.74 (above 0.59 but below 0.79)

**What This Reveals:**
The model's math creates a ceiling effect. Even with:
- "Unbearable pain"
- "Nothing will ever get better" (permanent hopelessness)
- High suicidal probabilities

The final scores plateau at 0.70-0.74, never reaching the 0.79 extremely_high threshold. The model cannot distinguish between severe and catastrophic depression - both land in "high" range.

---

## 4. STRESS Category

### Stress-Low (What the Model Rarely Detects)

**Model's Implicit Definition:** The model does not recognize manageable stress descriptions as Stress category - it classifies them as Normal.

**What the Model Actually Does:**
- "I have a lot of homework this week but I'll manage." → Normal-low
- "Things are a bit busy but nothing I can't handle." → Normal-low
- "Feeling a little stressed about the upcoming deadline." → Normal-low

**Model Detection Pattern:**
For these examples:
- Normal probability: 95-98%
- Stress probability: 0.2-1.8%
- The word "stress" + "but I'll manage" → Interpreted as Normal

**One Successful Stress-Low Detection:**
- "The stress is making me physically sick. I can't handle this." → Stress-low
- Stress probability: 94%
- Diagnosis score: 0.587
- Analysis: "no mental disorders" (0.3 scaling)
- Final score: 0.176 → Low

**What This Reveals:**
The diagnosis model only recognizes "stress" as Stress category when stress probability is extremely high (94%+), which happens when "stress" is explicitly stated in dramatic terms ("destroying me," "making me sick"). Manageable stress + reassurance language → Always classified as Normal. Even when Stress is detected, the analysis returning "no mental disorders" ensures low severity.

---

### Stress-Medium (What the Model Cannot Detect)

**Model's Implicit Definition:** The model has no working pattern for medium-severity stress.

**What the Model Actually Does:**
- "I'm overwhelmed with all the tests and assignments piling up." → Normal-low
- "So much pressure from school and parents, I'm exhausted." → Anxiety-medium
- "I can't keep up with everything. It's all too much right now." → Normal-low

**Model Detection Pattern:**
"Overwhelmed" scenarios:
- Normal probability: 87%
- Stress probability: 1.9%
- The word "overwhelmed" alone doesn't trigger Stress detection

"Pressure + exhausted":
- Anxiety probability: 85%
- Classified as Anxiety instead of Stress

**What This Reveals:**
The model cannot distinguish between stress, anxiety, and normal overwhelm. "Overwhelmed" is interpreted as Normal-low unless anxiety symptoms are prominent (then it becomes Anxiety). "Pressure" and "exhausted" language shifts to Anxiety category rather than Stress. The model appears to lack training data differentiating stress from anxiety.

---

### Stress-High (What the Model Cannot Detect)

**Model's Implicit Definition:** The model interprets breaking-down language as Depression, not high-severity Stress.

**What the Model Actually Does:**
- "I'm breaking down from all the pressure. Can't cope anymore." → Depression-high
- "Everything is crashing down on me. I'm at my breaking point." → Normal-low
- "The stress is making me physically sick. I can't handle this." → Stress-low

**Model Detection Pattern:**
"Breaking down + can't cope":
- Depression probability: 56%
- Suicidal probability: 22%
- Classified as Depression-high due to "breaking down" language

"Breaking point":
- Normal probability: 87%
- Stays Normal-low despite dramatic language

"Physically sick + can't handle":
- Stress probability: 94% (high recognition!)
- But analysis returns "no mental disorders"
- Final score: 0.176 → Low severity

**What This Reveals:**
The model interprets crisis language as Depression rather than Stress. "Breaking down" triggers Depression category. Even when Stress is correctly identified (94% probability), the scaling prevents reaching high severity. The model lacks a pathway to high-severity Stress.

---

### Stress-Extremely_High (What the Model Cannot Detect)

**Model's Implicit Definition:** The model has only one successful Stress detection pattern: explicit use of "stress" + extreme language, but caps at high severity at best.

**What the Model Actually Does:**
- "I'm completely overwhelmed, on the verge of total breakdown." → Normal-low
- "The pressure is crushing me, I feel like I'm going to explode." → Normal-low
- "I can't take it anymore, the stress is destroying me completely." → Stress-high

**Model Detection Pattern:**
For the successful detection:
- "Stress" explicitly mentioned + "destroying me"
- Stress probability: 92%
- Diagnosis score: 0.595
- Analysis: "suicide" (1.0 scaling factor!)
- Final score: 0.595 → High severity

For the failures:
- "Total breakdown" without "stress" keyword → 87% Normal probability
- "Crushing me, going to explode" → 72% Normal probability

**What This Reveals:**
The model requires the explicit word "stress" to classify Stress category. Metaphors like "crushing," "breakdown," "explode" are insufficient. When "stress" appears with destructive language, the analysis model may interpret it as suicidal crisis, applying 1.0 scaling. This is the only pathway to high Stress severity, but even then it doesn't reach extremely_high (0.79 threshold).

---

## 5. SUICIDAL Category

### Suicidal-Low (What the Model Struggles to Detect as Suicidal)

**Model's Implicit Definition:** The model doesn't reliably recognize passive suicidal ideation as belonging to Suicidal category - it often stays in Normal.

**What the Model Actually Does:**
- "Sometimes I wonder what it would be like to not exist." → Normal with medium severity (but analysis detects suicide!)
- "I've had passing thoughts that maybe things would be easier if I wasn't here." → Normal-low  
- "Occasionally I think about not being around but it's just a fleeting thought." → Normal-low

**Model Detection Pattern:**
For first example:
- Suicidal probability: 30.3%
- Normal probability: 53.8% (dominant)
- But analysis returned "suicide or self-harm tendency"
- This created a conflict: Normal category, suicide analysis

For others:
- Suicidal probability: 18-21%
- Normal probability: 60-90%
- "Passing thoughts" and "fleeting" language → Interpreted as Normal

**What This Reveals:**
The model needs >50% Suicidal probability to classify as Suicidal category. Passive ideation language ("wonder," "sometimes," "passing thoughts") generates 18-30% Suicidal probability, which is below the classification threshold. The category stays Normal even when analysis detects suicidal ideation. This creates a disconnect between diagnosis and analysis components.

---

### Suicidal-Medium (What the Model Escalates)

**Model's Implicit Definition:** The model does not have a "medium" suicidal ideation concept - any clear suicidal language triggers extremely_high.

**What the Model Actually Does:**
- "I keep thinking about ending it all. The thoughts are getting stronger." → Suicidal-extremely_high
- "I don't want to be alive anymore. I think about death often." → Depression-extremely_high
- "Life feels meaningless and I wish I could just disappear." → Suicidal-extremely_high

**Model Detection Pattern:**
For "ending it all":
- Suicidal probability: 67.6%
- Diagnosis score: 0.914
- Analysis: "suicide or self-harm tendency" (1.0 scaling)
- Final score: 0.914 → Extremely_high

For "don't want to be alive":
- Depression probability: 46.6%
- Suicidal probability: 44.2%
- Classified as Depression (narrowly)
- Still escalated to extremely_high

For "wish I could disappear":
- Suicidal probability: 55.6%
- Diagnosis score: 0.865
- Analysis: "suicide or self-harm tendency"
- Final score: 0.865 → Extremely_high

**What This Reveals:**
Once suicidal probability exceeds ~45-50%, the model escalates to extremely_high. The analysis model consistently detects "suicide or self-harm tendency" for any explicit death wishes, applying 1.0 scaling factor. This bypasses medium and high levels entirely. This is appropriate clinical behavior - active suicidal ideation should trigger maximum response.

---

### Suicidal-High (What the Model Escalates Beyond)

**Model's Implicit Definition:** The model treats planning/intent language as extremely_high, not stopping at high.

**What the Model Actually Does:**
- "I've been researching ways to end my life. I have a plan." → Suicidal-extremely_high
- "I want to kill myself. I've thought about how I would do it." → Suicidal-extremely_high
- "I'm planning to end my life soon. I can't see any other way out." → Suicidal-extremely_high

**Model Detection Pattern:**
Common elements across all:
- Suicidal probability: 55-77%
- Keywords: "plan," "researching ways," "how I would do it"
- Diagnosis scores: 0.86-0.93
- Analysis always returns "suicide" or "suicide/self-harm tendency"
- 1.0 scaling factor applied
- Final scores: 0.86-0.93 (well above 0.79 threshold)

**What This Reveals:**
The model has no distinction between planning (high) and imminent action (extremely_high). All explicit suicidal intent with method consideration generates:
- High Suicidal probability (55%+)
- "Suicide" analysis result
- Maximum scaling (1.0)
- Extremely_high severity

This aggressive escalation is clinically appropriate. The model correctly treats planning as a crisis requiring immediate intervention.

---

### Suicidal-Extremely_High (What the Model Sometimes Detects)

**Model's Implicit Definition:** Explicit statements of imminent action with means available and final decision language.

**Successfully Detected Examples:**
- "I'm going to kill myself tonight. I have everything ready." (✓ Detected)
- "This is my goodbye. I'm ending my life and I've made my decision." (✓ Detected)

**Critical Failure:**
- "I have the pills in my hand. I'm about to take them all right now." (✗ Missed - Normal-medium!)

**Model Detection Pattern:**
For successful detections:
- Suicidal probability: 46-48%
- Keywords: "tonight," "goodbye," "made my decision"
- Analysis: "suicide" or "suicide/self-harm tendency"
- Final scores: 0.865-0.870 → Extremely_high

For the critical failure:
- Suicidal probability: Only 22%
- Normal probability: 44% (dominant)
- "Pills in my hand, about to take" → Not recognized as imminent crisis
- Analysis DID detect "suicide" but Normal category dominated
- Final score: 0.472 → Medium

**What This Reveals:**
The model reliably detects extremely_high when:
1. Timeline keywords ("tonight," "goodbye")
2. Decision finality language
3. Suicidal probability >45%

But it catastrophically fails when specific means are described without timeline keywords. "Pills in my hand" should be maximum urgency, but the model's diagnosis component classified it as 44% Normal, 22% Suicidal. This suggests the model may interpret present-tense action descriptions differently than future statements. The analysis component correctly detected suicide, but the diagnosis dominated.

---

## Key Model Behavior Patterns

### Pattern 1: Binary Thinking
The model tends to operate in binary mode:
- Normal: Either clearly positive (low) or shifts to another category
- Depression: Either not detected (Normal-low) or high severity - rare medium
- Anxiety: Either low (with reassurance) or misclassified
- Suicidal: Either not detected (Normal) or extremely_high - no middle ground

### Pattern 2: Keyword Dependency
The model heavily relies on specific keywords:
- "Stress" must be explicitly stated or category is misclassified
- "Worry/anxious" must be present for Anxiety detection
- "Hopeless" or "worthless" triggers Depression-high
- Physical symptoms alone don't trigger appropriate categories

### Pattern 3: Scaling Math Creates Ceilings
Mathematical barriers prevent reaching certain levels:
- Anxiety effectively capped at medium (max ~0.52 final score)
- Depression capped at high (max ~0.74 final score)
- Stress can barely reach high even with 1.0 scaling

### Pattern 4: Analysis Model Conflicts
The analysis component sometimes conflicts with diagnosis:
- Diagnosis: 53% Normal, Analysis: "suicide tendency" → Normal category wins
- Diagnosis: Anxiety, Analysis: "no mental disorders" → Low severity
- Analysis frequently returns "no mental disorders" for clear anxiety/stress

### Pattern 5: Self-Reassurance Suppression
Any self-reassurance language prevents escalation:
- "But I'll be fine" → Ensures low severity
- "I can handle it" → Prevents escalation
- "But it's fine" → Keeps severity low
- This works even for concerning content

### Pattern 6: Appropriate Suicidal Escalation
When Suicidal category IS detected:
- Almost always escalates to extremely_high
- Analysis applies 1.0 scaling factor
- This aggressive response is clinically appropriate
- Better to over-detect than miss suicidal risk

### Pattern 7: Future vs Present Tense
Temporal framing affects detection:
- "Tonight" / "goodbye" → Detected as extremely_high
- "Right now" / "in my hand" → Missed (classified as Normal)
- Future declarations may be better recognized than present-tense actions

### Pattern 8: Functional Language Override
Statements of continued function suppress severity:
- "But I still get things done" → Can paradoxically escalate or suppress
- "I'm managing" → Keeps severity low
- "Just existing" → Interpreted as functional, stays low
- Model may interpret functionality as low risk

---

## Understanding the Model's "Mind"

### What the Model Is Good At:
1. **Detecting enthusiastic positivity** (Normal-low)
2. **Detecting explicit hopelessness** (Depression-high)
3. **Detecting active suicidal statements** (Suicidal-extremely_high)
4. **Recognizing self-reassurance** (keeps severity low)

### What the Model Struggles With:
1. **Distinguishing stress from anxiety from normal overwhelm**
2. **Recognizing physical manifestations** without emotional keywords
3. **Detecting emotional numbness/dissociation** (lacks pain language)
4. **Finding middle severity levels** (poor gradation)
5. **Recognizing present-tense crisis** ("pills in hand")

### What the Model Cannot Do:
1. **Reach high+ anxiety severity** (mathematical impossibility)
2. **Detect medium depression consistently** (too narrow a band)
3. **Recognize stress without "stress" keyword**
4. **Distinguish passive from active suicidal ideation**
5. **Reach extremely_high depression** (ceiling effect)

---

*This document describes observed model behavior, not clinical standards. The model's definitions are implicit in its detection patterns and may not align with clinical definitions.*

*Test Date: October 3, 2025*  
*Model: crisis_pipeline.py*  
*Methodology: 60 test cases with systematic analysis of detection patterns*


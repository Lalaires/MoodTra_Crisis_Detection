import os
from typing import Dict, Tuple
from google import genai
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class CrisisDetector:
    def __init__(self):
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        if not GOOGLE_API_KEY:
            raise RuntimeError("Missing GOOGLE_API_KEY in environment variables.")

        self.model = "gemini-2.5-flash-lite"
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.analysis_tokenizer = AutoTokenizer.from_pretrained("Tianlin668/MentalBART")
        self.analysis_model = AutoModelForSeq2SeqLM.from_pretrained("Tianlin668/MentalBART")
        self.diagnosis_tokenizer = AutoTokenizer.from_pretrained("ethandavey/mental-health-diagnosis-bert")
        self.diagnosis_model = AutoModelForSequenceClassification.from_pretrained("ethandavey/mental-health-diagnosis-bert")
        self.label_mapping = {0: "Anxiety", 1: "Normal", 2: "Depression", 3: "Suicidal", 4: "Stress"}

    def crisis_diagnosis(self, text: str) -> Tuple[Dict[str, float], str]:

        inputs = self.diagnosis_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
        
        with torch.no_grad():  
            outputs = self.diagnosis_model(**inputs)
            probabilities = F.softmax(outputs.logits, dim=1)

        all_probs = {}
        
        for i, prob in enumerate(probabilities[0]):
            all_probs[self.label_mapping[i]] = prob.item()
        
        print(f"Full probabilities: {all_probs}")
        
        return all_probs

    def severity_rating_agent(
        self,
        text: str,
        diagnosis: dict
    ) -> Dict[str, str]:

        prompt = f"""
        You are a crisis-detection agent. You are given:
        - latest chat messages from a 13–15 year-old Australian teen (text),
        - a diagnosis probability distribution (keys: 'Anxiety', 'Normal', 'Depression', 'Suicidal', 'Stress'),

        Goal:
        Determine the teen's current severity level for immediate mental-health or crisis risk.
        Base your assessment on both the chat content and the diagnosis probabilities.

        ---

        ### Severity Level Definitions

        **Low**
        - No distress, or mild and situational distress (e.g., “I’m a bit tired”, “I feel sad”).
        - No suicidal or self-harm thoughts.
        - Able to cope or seek support when needed.
        - May include normal emotional variation or healthy reflection.
        - Examples: “Today was fine”, “Feeling better”, “Just stressed about homework.”

        **Medium**
        - Noticeable emotional distress or anxiety.
        - Some functional impact (trouble sleeping, fatigue, school avoidance).
        - Mentions of hopelessness or sadness but **no suicidal or self-harm intent**.
        - Might express mild thoughts like “I don’t see the point” but without plan or means.
        - Requires monitoring and support, but not immediate intervention.
        - Examples: “I’m so tired of everything”, “I can’t focus anymore.”

        **High**
        - Strong distress, hopelessness, or depressive symptoms with **functional impairment** such as: “Can’t get out of bed”, “Stopped eating or sleeping”, “Nothing feels worth doing”
        - Mentions of suicidal ideation **without specific plan, means, or timeframe**.
        - Includes **self-harm without suicidal intent** (e.g., “I cut to feel better”).
        - Needs urgent mental-health referral or caregiver involvement.
        - Examples: “I wish I could disappear”, “I hurt myself to feel something.”

        **Extremely High**
        - Evidence of **imminent suicide risk**:
        - Has a **plan**, **intent**, **means**, and/or **timeframe**.
        - Expresses readiness or preparation (e.g., “I have pills ready”, “I’ll do it tonight”).
        - Expresses clear intent to die or inability to ensure own safety.
        - Requires **immediate emergency response**.
        - Examples: “I’m going to end it tonight”, “I have the knife ready.”

        ---

        ### Protective Factors (Down-Weighting Cue)
        If the teen expresses any of the following **and there are no active suicidal indicators**, reduce severity by one level:
        - Mentions of **support systems**: “I talked to my mum”, “My friends help me.”
        - **Hopeful or coping statements**: “I’m feeling better now”, “I’ll try to stay positive.”
        - **Help-seeking behaviors**: “I want to talk to someone”, “I think I need help.”

        ---

        ### Decision Procedure (Follow in Order)

        1. **Baseline Check**
        - If there is no distress or mild and situational distress or all messages are positive/neutral → “low severity” (baseline mood).

        2. **Imminent Suicide Markers**
        - Explicit plan, means, timeframe, or preparation → “extremely high”.

        3. **Active Suicidal Ideation**
        - Mentions wanting to die, but no clear plan/timeframe → “high”.
        - Escalate to “extremely high” if plan or timeframe appears.

        4. **Context Re-evaluation (False-Positive Control)**
        - Before labeling as 'high' or 'extremely high', verify that the message clearly implies intent to die or self-harm.
        - If the statement includes **non-suicidal context or safety modifiers** (e.g., "with a parachute", "for a stunt", "for a game", "as a joke", "skydiving"), classify as **low severity**.
        - If intent is ambiguous, analyze surrounding context and history before escalating.

        5. **Non-Suicidal Self-Harm (NSSI)**
        - If self-harm without suicidal intent → “high”.

        6. **Functional Impairment**
        - If unable to perform daily activities (sleeping, eating, school) or shows severe hopelessness → at least “high”.

        7. **Depression, Anxiety, or Stress (No Suicidality)**
        - Mild or situational → “low”
        - Moderate or recurring → “medium”
        - Severe impairment or hopelessness → “high”

        8. **Protective Factors**
        - If support systems, hope, or coping are present and no active suicidal risk → reduce severity by one level.

        9. **Diagnosis Probability Weighting**
        - Use diagnosis probabilities as a secondary signal:
            - If Depression or Suicidal > 0.7 → increase severity by one level (unless protective factors reduce it).
            - If “Normal” is highest, severity remains based on message evidence.
        - Message content always overrides diagnosis probabilities.

        10. **Output Formatting**
        - Output **only valid JSON** with:
            {{
            "crisis_name": "<Anxiety|Normal|Depression|Suicidal|Stress>",
            "crisis_note": "<one-sentence explanation>",
            "severity": "<low|medium|high|extremely high>"
            }}

        ---

        ### Input Variables
        - Diagnosis probabilities: {diagnosis}
        - Conversation messages: {text}

        Rules:
        - Always double-check for plan, intent, means, or timeframe.
        - Be conservative — if in doubt, choose the higher severity.
        - Do not include any commentary outside the JSON.

        Begin analysis now.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model, contents=prompt
            )
        except Exception as e:
            print(f"[WARN] Failed to generate response: {e}")
            return "I'm sorry, I'm having trouble generating a response. Please try again later."

        return response.text

    def detect_crisis(self, text: str) -> Dict[str, str]:

        # Get full probability distribution
        all_probs = self.crisis_diagnosis(text)

        result = self.severity_rating_agent(text, all_probs)

        return result

"""
IMPROVED Model-backed crisis detection pipeline (Parameter Tuning Only).

Key improvements:
1. Adjusted severity_scores to create better gradation
2. Rebalanced condition_scaling (original keywords only)
3. Optimized severity_thresholds for real-world cases
4. Enhanced final score computation with probability-aware scaling
5. Added non-linearity to capture extreme cases better

No keyword expansion - only parameter optimization.
"""
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
import string
from typing import Dict, Tuple
import logging
import math

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class CrisisDetector:
    """End-to-end crisis detection using diagnosis + analysis models."""

    def __init__(self):
        """Load tokenizers/models and precompute mappings and thresholds."""
        self.analysis_tokenizer = AutoTokenizer.from_pretrained("Tianlin668/MentalBART")
        self.analysis_model = AutoModelForSeq2SeqLM.from_pretrained("Tianlin668/MentalBART")
        self.diagnosis_tokenizer = AutoTokenizer.from_pretrained("ethandavey/mental-health-diagnosis-bert")
        self.diagnosis_model = AutoModelForSequenceClassification.from_pretrained("ethandavey/mental-health-diagnosis-bert")

        # Pre-compute mappings
        self.label_mapping = {0: "Anxiety", 1: "Normal", 2: "Depression", 3: "Suicidal", 4: "Stress"}
        
        # IMPROVED: Rebalanced severity scores
        # Goal: Create better separation and prevent auto-jumping to high
        # - Reduced anxiety/depression to allow medium range
        # - Kept suicidal at maximum
        # - Adjusted stress to be more proportional
        self.severity_scores = {
            "normal": 0.0,
            "stress": 0.60,      # Reduced from 0.8 (was too high)
            "anxiety": 0.68,     # Reduced from 0.9 (prevent auto-high)
            "depression": 0.72,  # Reduced from 0.9 (allow medium range)
            "suicidal": 1.0      # Unchanged - maximum severity
        }
        
        # IMPROVED: Rebalanced condition_scaling (original keywords only)
        # Goal: Better calibration between risk levels
        # - Lowered normal/no disorders to reduce false negatives
        # - Adjusted middle range (stress/anxiety/depression) for better gradation
        # - Kept high-risk conditions at maximum
        self.condition_scaling = {
            "normal": 0.25,              # Reduced from 0.3 (too conservative)
            "no mental disorders": 0.25, # Reduced from 0.3
            "stress": 0.70,              # Reduced from 0.8 (better separation)
            "anxiety": 0.75,             # Reduced from 0.9 (prevent over-scaling)
            "depression": 0.80,          # Reduced from 0.9 (allow medium)
            "suicidal": 1.0,             # Unchanged - maximum
            "suicide": 1.0,              # Unchanged - maximum
            "self-harm": 1.0,            # Unchanged - maximum
            "emergency": 1.0             # Unchanged - maximum
        }
        
        # IMPROVED: Optimized severity thresholds
        # Goal: Make medium range accessible and improve overall distribution
        # Old: 0.89, 0.79, 0.59 (medium was hard to reach, gaps were uneven)
        # New: Better calibrated based on expected score distributions
        self.severity_thresholds = [
            (0.80, "extremely_high"),  # Lowered from 0.89 - catch more critical cases
            (0.58, "high"),            # Lowered from 0.79 - better separation
            (0.35, "medium"),          # Lowered from 0.59 - actually reachable
            (0.0, "low")               # Unchanged
        ]

    def crisis_diagnosis(self, text: str) -> Tuple[Dict[str, float], str]:
        """Classify text and return full class probabilities and top label."""
        inputs = self.diagnosis_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
        
        with torch.no_grad():
            outputs = self.diagnosis_model(**inputs)
            probabilities = F.softmax(outputs.logits, dim=1)

        all_probs = {}
        
        for i, prob in enumerate(probabilities[0]):
            all_probs[self.label_mapping[i]] = prob.item()
        
        # Get top prediction
        predicted_class = torch.argmax(probabilities, dim=1).item()
        top_prediction = self.label_mapping[predicted_class]
        top_confidence = probabilities[0][predicted_class].item()
        
        print(f"Full probabilities: {all_probs}")
        print(f"Top prediction: {top_prediction} (confidence: {top_confidence:.2f})")
        
        return all_probs, top_prediction

    def crisis_analysis(self, text: str) -> Tuple[str, str]:
        """Generate an inferred condition and reasoning for the given text."""
        prompt = f"""
        Analyse the following teen's chat message and provide a possible mental health condition and reasoning.
        Teen's chat message: {text} 
        """
        inputs = self.analysis_tokenizer(prompt, return_tensors="pt")
        outputs = self.analysis_model.generate(**inputs, max_new_tokens=100, temperature=0.9, top_p=0.9, do_sample=True)
        completion = self.analysis_tokenizer.decode(outputs[0], skip_special_tokens=True)
          
        # Parse condition and reasoning
        if "Reasoning:" in completion:
            condition = completion.split("Reasoning:")[0].strip().translate(str.maketrans("", "", string.punctuation)).lower()
            reasoning = completion.split("Reasoning:")[1].strip()
        else:
            condition = completion.strip().translate(str.maketrans("", "", string.punctuation)).lower()
            reasoning = ""
        
        print(f"Analysis condition: {condition}")
        print(f"Analysis reasoning: {reasoning}")
        
        return condition, completion

    def severity_score(self, probabilities: Dict[str, float]) -> float:
        """Compute weighted severity score from class probability distribution.
        
        IMPROVED: Added non-linear scaling to better capture extreme cases.
        When suicidal probability is high, we amplify the signal.
        """
        # Standard weighted sum
        diagnosis_score = sum(
            prob * self.severity_scores.get(class_name.lower(), 0.0)
            for class_name, prob in probabilities.items()
        )
        
        # NEW: Non-linear amplification for high-risk signals
        # If suicidal probability is significant, boost the score
        suicidal_prob = probabilities.get("Suicidal", 0.0)
        if suicidal_prob > 0.25:
            # Apply exponential boost for high suicidal probability
            # This helps catch cases where suicidal intent is present but not dominant
            boost_factor = 1.0 + (suicidal_prob ** 1.5) * 0.3
            diagnosis_score = min(1.0, diagnosis_score * boost_factor)
            print(f"Suicidal probability boost: {suicidal_prob:.3f} -> factor {boost_factor:.3f}")
        
        print(f"Diagnosis score: {diagnosis_score:.3f}")
        
        return diagnosis_score

    def severity_scaling(self, diagnosis_score: float, condition: str, diagnosis_probs: Dict[str, float]) -> str:
        """Scale diagnosis score by inferred condition and map to severity level.
        
        IMPROVED: Enhanced scaling with probability-aware adjustments.
        """
        # Find matching condition scaling factor
        scaling_factor = next(
            (scale for cond_key, scale in self.condition_scaling.items() 
             if cond_key in condition), 0.5
        )
        
        # Calculate base score
        base_score = diagnosis_score * scaling_factor
        
        # NEW: Confidence-aware adjustment
        # When the top prediction has very high confidence AND matches high-risk,
        # we should boost the score. When it's uncertain, we should be more conservative.
        top_class = max(diagnosis_probs.items(), key=lambda x: x[1])
        top_confidence = top_class[1]
        
        confidence_adjustment = 0.0
        
        # If high-risk class (Suicidal/Depression) has strong confidence, boost
        if top_class[0] in ["Suicidal", "Depression"]:
            if top_confidence > 0.6:
                # Strong signal for high-risk class
                confidence_adjustment = (top_confidence - 0.6) * 0.15
                print(f"High-risk confidence boost: +{confidence_adjustment:.3f}")
            elif top_confidence < 0.4:
                # Uncertain high-risk signal, be slightly conservative
                confidence_adjustment = -0.05
                print(f"Uncertainty penalty: {confidence_adjustment:.3f}")
        
        # If Normal class has very high confidence, reduce score
        elif top_class[0] == "Normal":
            if top_confidence > 0.85:
                confidence_adjustment = -0.10
                print(f"Normal confidence reduction: {confidence_adjustment:.3f}")
        
        # NEW: Probability distribution diversity check
        # If probabilities are spread across multiple high-risk categories,
        # this indicates mixed signals - we should err on the side of caution
        high_risk_total = (
            diagnosis_probs.get("Suicidal", 0) + 
            diagnosis_probs.get("Depression", 0) + 
            diagnosis_probs.get("Anxiety", 0) * 0.5  # Anxiety counts partially
        )
        
        if high_risk_total > 0.4 and top_class[0] != "Suicidal":
            # Significant high-risk signal distributed across categories
            mixed_signal_boost = min(0.10, (high_risk_total - 0.4) * 0.25)
            confidence_adjustment += mixed_signal_boost
            print(f"Mixed high-risk signals boost: +{mixed_signal_boost:.3f}")
        
        # Apply adjustments and clamp
        final_score = max(0.0, min(1.0, base_score + confidence_adjustment))
        
        # Map to severity level using thresholds
        for threshold, severity_level in self.severity_thresholds:
            if final_score >= threshold:
                print(f"Condition: '{condition}'")
                print(f"Scaling factor: {scaling_factor}")
                print(f"Base score: {base_score:.3f}")
                if confidence_adjustment != 0:
                    print(f"Confidence adjustment: {confidence_adjustment:+.3f}")
                print(f"Final score: {final_score:.3f}")
                print(f"Severity level: {severity_level}")
                return severity_level

        return "low"

    def detect_crisis(self, text: str) -> Dict[str, str]:
        """Detect crisis severity from chat context.
        
        IMPROVED: Lower analysis threshold to catch more edge cases.
        """
        # Get full probability distribution
        all_probs, top_prediction = self.crisis_diagnosis(text)

        score = self.severity_score(all_probs)
        
        # IMPROVED: Lowered threshold from 0.6 to 0.45
        # This ensures we run detailed analysis on more borderline cases
        if score >= 0.45:
            # Get detailed analysis
            condition, completion = self.crisis_analysis(text)
            severity = self.severity_scaling(score, condition, all_probs)
            
            if severity != "low":
                return {
                    "crisis_name": top_prediction,
                    "crisis_note": completion,
                    "severity": severity,
                }
            else:
                return {
                    "crisis_name": top_prediction,
                    "crisis_note": None, 
                    "severity": severity
                }
        else:
            return {
                "crisis_name": top_prediction,
                "crisis_note": None, 
                "severity": "low"
            }


# Complete implementation for full probability distribution severity mapping
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
import string
from typing import Dict, Tuple
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class CrisisDetector:
    def __init__(self):
        self.analysis_tokenizer = AutoTokenizer.from_pretrained("Tianlin668/MentalBART")
        self.analysis_model = AutoModelForSeq2SeqLM.from_pretrained("Tianlin668/MentalBART")
        self.diagnosis_tokenizer = AutoTokenizer.from_pretrained("ethandavey/mental-health-diagnosis-bert")
        self.diagnosis_model = AutoModelForSequenceClassification.from_pretrained("ethandavey/mental-health-diagnosis-bert")

        # Pre-compute mappings ONCE during initialization
        self.label_mapping = {0: "Anxiety", 1: "Normal", 2: "Depression", 3: "Suicidal", 4: "Stress"}
        self.severity_scores = {
            "normal": 0.0,
            "stress": 0.8,
            "anxiety": 0.9,
            "depression": 0.9,
            "suicidal": 1.0
        }
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
        # Pre-compute severity level thresholds
        self.severity_thresholds = [
            (0.89, "extremely_high"),
            (0.79, "high"),
            (0.59, "medium"),
            (0.0, "low")
        ]

    def crisis_diagnosis(self, text: str) -> Tuple[Dict[str, float], str]:

        inputs = self.diagnosis_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
        
        with torch.no_grad():
            outputs = self.diagnosis_model(**inputs)
            probabilities = F.softmax(outputs.logits, dim=1)

        all_probs = {}
        
        for i, prob in enumerate(probabilities[0]):
            all_probs[self.label_mapping[i]] = prob.item()
        
        # Get top prediction for compatibility
        predicted_class = torch.argmax(probabilities, dim=1).item()
        top_prediction = self.label_mapping[predicted_class]
        top_confidence = probabilities[0][predicted_class].item()
        
        print(f"Full probabilities: {all_probs}")
        print(f"Top prediction: {top_prediction} (confidence: {top_confidence:.2f})")
        
        return all_probs, top_prediction

    def crisis_analysis(self, text: str) -> Tuple[str, str]:

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

    def severity_score(self, probabilities: Dict[str, float]) -> str:
        
        # Calculate weighted severity score from all probabilities
        diagnosis_score = sum(
            prob * self.severity_scores.get(class_name.lower(), 0.0)
            for class_name, prob in probabilities.items()
        )
        
        print(f"Diagnosis score: {diagnosis_score:.3f}")
        
        return diagnosis_score

    def severity_scaling(self, diagnosis_score: float, condition: str) -> str:

        scaling_factor = next(
            (scale for cond_key, scale in self.condition_scaling.items() 
             if cond_key in condition), 0.5
        )
        
        final_score = max(0.0, min(1.0, diagnosis_score * scaling_factor))
        
        # Use pre-computed thresholds
        for threshold, severity_level in self.severity_thresholds:
            if final_score >= threshold:
                print(f"Condition: '{condition}'")
                print(f"Scaling factor: {scaling_factor}")
                print(f"Final score: {final_score:.3f}")
                print(f"Severity level: {severity_level}")
                return severity_level

        return "low"

    def detect_crisis(self, text: str) -> Dict[str, str]:

        # Get full probability distribution
        all_probs, top_prediction = self.crisis_diagnosis(text)

        score = self.severity_score(all_probs)
        if score >= 0.6:
            # Get detailed analysis
            condition, completion = self.crisis_analysis(text)
            severity = self.severity_scaling(score, condition)
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

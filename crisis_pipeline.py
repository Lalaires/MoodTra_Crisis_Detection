# Complete implementation for full probability distribution severity mapping
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
import string
from typing import Dict, Tuple

class CrisisDetector:
    def __init__(self):
        self.analysis_tokenizer = AutoTokenizer.from_pretrained("Tianlin668/MentalBART")
        self.analysis_model = AutoModelForSeq2SeqLM.from_pretrained("Tianlin668/MentalBART")
        self.diagnosis_tokenizer = AutoTokenizer.from_pretrained("ethandavey/mental-health-diagnosis-bert")
        self.diagnosis_model = AutoModelForSequenceClassification.from_pretrained("ethandavey/mental-health-diagnosis-bert")

    def crisis_diagnosis(self, text: str) -> Tuple[Dict[str, float], str]:

        inputs = self.diagnosis_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
        
        with torch.no_grad():
            outputs = self.diagnosis_model(**inputs)
            probabilities = F.softmax(outputs.logits, dim=1)

        # Map all predictions to labels
        label_mapping = {0: "Anxiety", 1: "Normal", 2: "Depression", 3: "Suicidal", 4: "Stress"}
        all_probs = {}
        
        for i, prob in enumerate(probabilities[0]):
            all_probs[label_mapping[i]] = prob.item()
        
        # Get top prediction for compatibility
        predicted_class = torch.argmax(probabilities, dim=1).item()
        top_prediction = label_mapping[predicted_class]
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

    def severity(self, probabilities: Dict[str, float], condition: str) -> str:
        # Base severity scores for each condition
        severity_scores = {
            "normal": 0.0,
            "stress": 0.8,
            "anxiety": 0.9,
            "depression": 0.9,
            "suicidal": 1.0
        }
        
        # Calculate weighted severity score from all probabilities
        diagnosis_score = 0.0
        
        for class_name, prob in probabilities.items():
            class_lower = class_name.lower()
            if class_lower in severity_scores:
                diagnosis_score += prob * severity_scores[class_lower]
        
        # Use condition to scale the diagnosis score
        condition_scaling = {
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
        
        # Get scaling factor for the condition
        scaling_factor = 0.5  # Default neutral scaling
        for cond_key, scale in condition_scaling.items():
            if cond_key in condition:
                scaling_factor = scale
                break
        
        # Apply scaling: diagnosis_score * scaling_factor
        final_score = diagnosis_score * scaling_factor
        
        # Ensure bounds
        final_score = max(0.0, min(1.0, final_score))
        
        # Map to severity levels
        if final_score >= 0.8:
            severity_level = "extremely_high"
        elif final_score >= 0.7:
            severity_level = "high"
        elif final_score >= 0.5:
            severity_level = "medium"
        else:
            severity_level = "low"
        
        print(f"Diagnosis score: {diagnosis_score:.3f}")
        print(f"Condition: '{condition}'")
        print(f"Scaling factor: {scaling_factor}")
        print(f"Final score: {final_score:.3f}")
        print(f"Severity level: {severity_level}")
        
        return severity_level

    def detect_crisis(self, text: str) -> Dict[str, str]:

        # Get full probability distribution
        all_probs, top_prediction = self.crisis_diagnosis(text)
        
        # Get detailed analysis
        condition, completion = self.crisis_analysis(text)
        
        # Calculate severity
        severity = self.severity(all_probs, condition)

        return {
            "crisis_name": top_prediction,
            "crisis_note": completion,
            "severity": severity,
        }

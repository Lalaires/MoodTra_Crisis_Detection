"""
Comprehensive Testing Suite for Crisis Detection Pipeline
Tests all diagnosis categories at each severity level with carefully crafted examples
"""
from crisis_pipeline import CrisisDetector
import json
from typing import Dict, List
from datetime import datetime

# Test examples for each diagnosis category at each severity level
TEST_CASES = {
    "Normal": {
        "low": [
            "I had a great day at school today! Math class was fun.",
            "Just finished my homework. Now I'm going to play some video games.",
            "Can't wait for the weekend! Going to the beach with my family."
        ],
        "medium": [
            "School is okay I guess. Nothing special happening.",
            "Sometimes I feel bored but it's fine.",
            "Life is just meh right now, not bad though."
        ],
        "high": [
            "I feel neutral about everything. Nothing really matters much.",
            "Just going through the motions every day.",
            "Everything feels flat and colorless but I'm managing."
        ],
        "extremely_high": [
            "I don't feel anything anymore, just empty numbness.",
            "Complete emotional flatness, like I'm just existing.",
            "Numb to everything around me, total emotional void."
        ]
    },
    "Anxiety": {
        "low": [
            "I'm a little nervous about the test tomorrow but I'll be fine.",
            "Sometimes I worry about things but it passes quickly.",
            "Feeling a bit anxious about the presentation but I can handle it."
        ],
        "medium": [
            "I keep worrying about my grades and what people think of me.",
            "My heart races sometimes when I think about school stuff.",
            "Can't stop thinking about all the things that could go wrong."
        ],
        "high": [
            "I can't sleep because my mind won't stop racing with worries.",
            "My chest feels tight all the time and I'm constantly on edge.",
            "I'm having panic attacks almost every day now. Can't breathe properly."
        ],
        "extremely_high": [
            "I'm completely paralyzed by fear, can't leave my room anymore.",
            "Constant panic attacks, heart pounding so hard I think I'm dying.",
            "Overwhelming terror that never stops, I'm trapped in endless anxiety."
        ]
    },
    "Depression": {
        "low": [
            "I've been feeling a bit down lately but it's not too bad.",
            "Some days I feel sad but I still get things done.",
            "Feeling a little blue today but I'll probably feel better tomorrow."
        ],
        "medium": [
            "I don't enjoy things I used to like anymore. Everything feels hard.",
            "I've been sleeping too much and don't want to get out of bed.",
            "I feel really sad most days and it's hard to concentrate."
        ],
        "high": [
            "I can't find any reason to get up in the morning. Everything is hopeless.",
            "I feel completely worthless and like a burden to everyone around me.",
            "The sadness is crushing me. I can barely function anymore."
        ],
        "extremely_high": [
            "I see no point in continuing. The pain is unbearable and endless.",
            "Complete despair, no light at the end of the tunnel, just darkness.",
            "I'm drowning in hopelessness. Nothing will ever get better."
        ]
    },
    "Stress": {
        "low": [
            "I have a lot of homework this week but I'll manage.",
            "Things are a bit busy but nothing I can't handle.",
            "Feeling a little stressed about the upcoming deadline."
        ],
        "medium": [
            "I'm overwhelmed with all the tests and assignments piling up.",
            "So much pressure from school and parents, I'm exhausted.",
            "I can't keep up with everything. It's all too much right now."
        ],
        "high": [
            "I'm breaking down from all the pressure. Can't cope anymore.",
            "Everything is crashing down on me. I'm at my breaking point.",
            "The stress is making me physically sick. I can't handle this."
        ],
        "extremely_high": [
            "I'm completely overwhelmed, on the verge of total breakdown.",
            "The pressure is crushing me, I feel like I'm going to explode.",
            "I can't take it anymore, the stress is destroying me completely."
        ]
    },
    "Suicidal": {
        "low": [
            "Sometimes I wonder what it would be like to not exist.",
            "I've had passing thoughts that maybe things would be easier if I wasn't here.",
            "Occasionally I think about not being around but it's just a fleeting thought."
        ],
        "medium": [
            "I keep thinking about ending it all. The thoughts are getting stronger.",
            "I don't want to be alive anymore. I think about death often.",
            "Life feels meaningless and I wish I could just disappear."
        ],
        "high": [
            "I've been researching ways to end my life. I have a plan.",
            "I want to kill myself. I've thought about how I would do it.",
            "I'm planning to end my life soon. I can't see any other way out."
        ],
        "extremely_high": [
            "I'm going to kill myself tonight. I have everything ready.",
            "This is my goodbye. I'm ending my life and I've made my decision.",
            "I have the pills in my hand. I'm about to take them all right now."
        ]
    }
}

def run_comprehensive_test():
    """Run comprehensive tests across all categories and severity levels"""
    print("=" * 80)
    print("COMPREHENSIVE CRISIS DETECTION TEST")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    detector = CrisisDetector()
    results = {}
    
    total_tests = sum(len(examples) for category in TEST_CASES.values() 
                     for examples in category.values())
    current_test = 0
    
    for category, severity_levels in TEST_CASES.items():
        results[category] = {}
        
        for target_severity, examples in severity_levels.items():
            results[category][target_severity] = []
            
            for example_idx, text in enumerate(examples):
                current_test += 1
                print(f"\n{'='*80}")
                print(f"TEST {current_test}/{total_tests}")
                print(f"Category: {category} | Target Severity: {target_severity}")
                print(f"Example {example_idx + 1}: \"{text}\"")
                print(f"{'='*80}")
                
                try:
                    result = detector.detect_crisis(text)
                    
                    test_result = {
                        "example": text,
                        "target_severity": target_severity,
                        "detected_category": result["crisis_name"],
                        "detected_severity": result["severity"],
                        "crisis_note": result["crisis_note"],
                        "category_match": result["crisis_name"] == category,
                        "severity_match": result["severity"] == target_severity,
                    }
                    
                    results[category][target_severity].append(test_result)
                    
                    print(f"\n📊 RESULT:")
                    print(f"  Detected Category: {result['crisis_name']} {'✓' if test_result['category_match'] else '✗'}")
                    print(f"  Detected Severity: {result['severity']} {'✓' if test_result['severity_match'] else '✗'}")
                    if result["crisis_note"]:
                        print(f"  Crisis Note: {result['crisis_note']}")
                    
                except Exception as e:
                    print(f"\n❌ ERROR: {str(e)}")
                    results[category][target_severity].append({
                        "example": text,
                        "target_severity": target_severity,
                        "error": str(e)
                    })
    
    return results

def analyze_results(results: Dict) -> Dict:
    """Analyze test results and generate statistics"""
    analysis = {
        "summary": {},
        "category_accuracy": {},
        "severity_accuracy": {},
        "definitions": {}
    }
    
    total_tests = 0
    category_correct = 0
    severity_correct = 0
    both_correct = 0
    
    # Calculate overall statistics
    for category, severity_levels in results.items():
        cat_total = 0
        cat_correct = 0
        sev_correct = 0
        
        for target_severity, test_results in severity_levels.items():
            for result in test_results:
                if "error" not in result:
                    total_tests += 1
                    cat_total += 1
                    
                    if result.get("category_match", False):
                        category_correct += 1
                        cat_correct += 1
                    
                    if result.get("severity_match", False):
                        severity_correct += 1
                        sev_correct += 1
                    
                    if result.get("category_match", False) and result.get("severity_match", False):
                        both_correct += 1
        
        if cat_total > 0:
            analysis["category_accuracy"][category] = {
                "correct": cat_correct,
                "total": cat_total,
                "percentage": round(cat_correct / cat_total * 100, 2)
            }
    
    # Overall summary
    analysis["summary"] = {
        "total_tests": total_tests,
        "category_accuracy": round(category_correct / total_tests * 100, 2) if total_tests > 0 else 0,
        "severity_accuracy": round(severity_correct / total_tests * 100, 2) if total_tests > 0 else 0,
        "both_correct": round(both_correct / total_tests * 100, 2) if total_tests > 0 else 0,
    }
    
    return analysis

def generate_definitions(results: Dict) -> Dict:
    """Generate concise definitions for each category-severity pair based on test results"""
    definitions = {}
    
    for category, severity_levels in results.items():
        definitions[category] = {}
        
        for severity, test_results in severity_levels.items():
            # Collect examples that matched both category and severity
            matched_examples = [
                r["example"] for r in test_results 
                if r.get("category_match", False) and r.get("severity_match", False)
            ]
            
            # Collect all tested examples
            all_examples = [r["example"] for r in test_results if "error" not in r]
            
            # Create definition based on the category-severity combination
            definition = create_definition(category, severity, matched_examples, all_examples)
            
            definitions[category][severity] = {
                "definition": definition,
                "tested_examples": all_examples,
                "successfully_detected": matched_examples,
                "accuracy": f"{len(matched_examples)}/{len(all_examples)}" if all_examples else "0/0"
            }
    
    return definitions

def create_definition(category: str, severity: str, matched: List[str], all_examples: List[str]) -> str:
    """Create a concise definition for each category-severity pair"""
    
    definitions_map = {
        ("Normal", "low"): "Positive emotional state with no concerning symptoms. Individual expresses contentment, engagement in activities, and healthy social functioning.",
        
        ("Normal", "medium"): "Neutral emotional state with mild disengagement. May express boredom or lack of excitement but no distress or dysfunction.",
        
        ("Normal", "high"): "Emotional detachment with concerning apathy. Individual experiences significant lack of emotional response while maintaining basic functioning.",
        
        ("Normal", "extremely_high"): "Severe emotional numbness and dissociation. Complete absence of emotional response indicating possible depersonalization or severe detachment.",
        
        ("Anxiety", "low"): "Mild worry or nervousness about specific situations. Concerns are manageable and don't significantly impair daily functioning.",
        
        ("Anxiety", "medium"): "Persistent worry with physical symptoms. Individual experiences frequent anxious thoughts, increased heart rate, and difficulty controlling worry.",
        
        ("Anxiety", "high"): "Severe anxiety with panic symptoms. Individual experiences panic attacks, sleep disruption, chest tightness, and significant functional impairment.",
        
        ("Anxiety", "extremely_high"): "Debilitating panic and terror. Individual is paralyzed by fear, experiencing constant severe panic attacks, and unable to perform basic activities.",
        
        ("Depression", "low"): "Mild sadness or low mood. Individual feels down occasionally but maintains daily activities and expects improvement.",
        
        ("Depression", "medium"): "Persistent depressive symptoms with anhedonia. Individual has lost interest in activities, experiences sleep changes, difficulty concentrating, and pervasive sadness.",
        
        ("Depression", "high"): "Severe depression with hopelessness. Individual feels worthless, sees no purpose in daily activities, experiences crushing sadness, and significant functional impairment.",
        
        ("Depression", "extremely_high"): "Profound despair with complete hopelessness. Individual experiences unbearable emotional pain, sees no possibility of improvement, and is in severe distress.",
        
        ("Stress", "low"): "Manageable pressure from daily demands. Individual acknowledges stress but feels capable of handling current responsibilities.",
        
        ("Stress", "medium"): "Overwhelming demands with exhaustion. Individual struggles to keep up with responsibilities, feels pressured from multiple sources, and experiences fatigue.",
        
        ("Stress", "high"): "Extreme pressure causing breakdown. Individual is at breaking point, experiencing physical symptoms from stress, and unable to cope effectively.",
        
        ("Stress", "extremely_high"): "Critical stress overload with imminent collapse. Individual is completely overwhelmed, on verge of total breakdown, and experiencing crisis-level pressure.",
        
        ("Suicidal", "low"): "Passive suicidal ideation without intent. Individual has fleeting thoughts about non-existence but no plans or strong desire to act.",
        
        ("Suicidal", "medium"): "Active suicidal thoughts with increasing frequency. Individual frequently thinks about death, expresses wish to die, but hasn't formulated concrete plans.",
        
        ("Suicidal", "high"): "Suicidal intent with planning. Individual has developed methods for suicide, is actively planning, and expresses clear intention to end their life.",
        
        ("Suicidal", "extremely_high"): "Immediate suicide risk with imminent action. Individual has decided to attempt suicide, has means available, and is communicating final intentions. REQUIRES IMMEDIATE INTERVENTION.",
    }
    
    return definitions_map.get((category, severity), f"{category} at {severity} severity level.")

def print_analysis(analysis: Dict, definitions: Dict):
    """Print formatted analysis and definitions"""
    print("\n\n" + "=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    
    # Print summary
    print("\n📊 OVERALL SUMMARY:")
    print(f"  Total Tests: {analysis['summary']['total_tests']}")
    print(f"  Category Accuracy: {analysis['summary']['category_accuracy']}%")
    print(f"  Severity Accuracy: {analysis['summary']['severity_accuracy']}%")
    print(f"  Both Correct: {analysis['summary']['both_correct']}%")
    
    # Print category-specific accuracy
    print("\n📈 CATEGORY-SPECIFIC ACCURACY:")
    for category, stats in analysis['category_accuracy'].items():
        print(f"  {category}: {stats['percentage']}% ({stats['correct']}/{stats['total']})")
    
    # Print definitions
    print("\n\n" + "=" * 80)
    print("DEFINITIONS FOR EACH CATEGORY-SEVERITY PAIR")
    print("=" * 80)
    
    for category in ["Normal", "Anxiety", "Depression", "Stress", "Suicidal"]:
        print(f"\n{'='*80}")
        print(f"CATEGORY: {category.upper()}")
        print(f"{'='*80}")
        
        for severity in ["low", "medium", "high", "extremely_high"]:
            if category in definitions and severity in definitions[category]:
                data = definitions[category][severity]
                print(f"\n🔹 {category} - {severity.upper()}:")
                print(f"   Definition: {data['definition']}")
                print(f"   Detection Rate: {data['accuracy']}")
                print(f"   Tested Examples:")
                for i, example in enumerate(data['tested_examples'], 1):
                    marker = "✓" if example in data['successfully_detected'] else "✗"
                    print(f"     {marker} {i}. \"{example}\"")

def save_results(results: Dict, analysis: Dict, definitions: Dict):
    """Save all results to JSON file"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "detailed_results": results,
        "analysis": analysis,
        "definitions": definitions
    }
    
    with open("comprehensive_test_results_v1.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n\n💾 Results saved to: comprehensive_test_results_v1.json")

if __name__ == "__main__":
    # Run tests
    results = run_comprehensive_test()
    
    # Analyze results
    analysis = analyze_results(results)
    definitions = generate_definitions(results)
    
    # Print analysis
    print_analysis(analysis, definitions)
    
    # Save results
    save_results(results, analysis, definitions)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


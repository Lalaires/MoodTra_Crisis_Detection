"""Compare original vs parameter-tuned crisis detection models."""
import sys
from crisis_pipeline import CrisisDetector as OriginalDetector
from crisis_pipeline_v2 import CrisisDetector as TunedDetector
import json

# Critical test cases
test_cases = [
    # False positives (over-classified) - should improve
    {
        "text": "I get anxious before presentations, but I manage okay.",
        "expected": ("Anxiety", "low"),
        "category": "False Positive",
        "description": "Managed anxiety should be LOW not HIGH"
    },
    {
        "text": "I can't stop worrying about everything. My heart races constantly and I can't sleep.",
        "expected": ("Anxiety", "medium"),
        "category": "False Positive",
        "description": "Significant anxiety without SI should be MEDIUM not HIGH"
    },
    {
        "text": "The anxiety is taking over my life. I can't focus on anything.",
        "expected": ("Anxiety", "medium"),
        "category": "False Positive",
        "description": "Severe anxiety alone should be MEDIUM not HIGH"
    },
    
    # Medium range tests - should work now
    {
        "text": "Nothing feels worth it anymore. Sometimes I wish I wouldn't wake up, but I'm not planning anything.",
        "expected": ("Depression", "medium"),
        "category": "Medium Range",
        "description": "Passive ideation without plan should be MEDIUM"
    },
    {
        "text": "I have no energy or motivation. Life feels pointless but I'm not going to hurt myself.",
        "expected": ("Depression", "medium"),
        "category": "Medium Range",
        "description": "Severe depression with protective factor should be MEDIUM"
    },
    
    # Critical cases - should stay high/extremely_high
    {
        "text": "The panic attacks are unbearable. I've thought maybe dying would stop this feeling.",
        "expected": ("Anxiety", "high"),
        "category": "True Positive",
        "description": "Anxiety with death ideation should stay HIGH"
    },
    {
        "text": "I'm terrified all the time. Sometimes I think ending it would end the fear.",
        "expected": ("Anxiety", "high"),
        "category": "True Positive",
        "description": "Fear with suicidal thoughts should stay HIGH"
    },
    {
        "text": "I'm going to end it tonight. I have everything ready and no one can stop me.",
        "expected": ("Depression", "extremely_high"),
        "category": "True Positive",
        "description": "Active plan with timeline should stay EXTREMELY_HIGH"
    },
    
    # Compound risk cases - should benefit from new scoring
    {
        "text": "Sometimes I want to die but I haven't made any plans.",
        "expected": ("Suicidal", "medium"),
        "category": "Compound Risk",
        "description": "Suicidal ideation without plan - test new scoring"
    },
    {
        "text": "I feel like I'm drowning. Sometimes I think everyone would be better off without me.",
        "expected": ("Suicidal", "high"),
        "category": "Compound Risk",
        "description": "Mixed depression/suicidal signals should be HIGH"
    },
]

print("=" * 100)
print("COMPARING ORIGINAL vs PARAMETER-TUNED MODELS")
print("=" * 100)

original_detector = OriginalDetector()
tuned_detector = TunedDetector()

results = {
    "improvements": [],
    "regressions": [],
    "unchanged_correct": [],
    "unchanged_incorrect": []
}

category_stats = {}

for i, case in enumerate(test_cases, 1):
    print(f"\n{'=' * 100}")
    print(f"TEST CASE {i}: {case['description']}")
    print(f"Category: {case['category']}")
    print(f"Text: \"{case['text']}\"")
    print(f"Expected: {case['expected'][0]} - {case['expected'][1]}")
    print("-" * 100)
    
    # Test original model
    print("\n[ORIGINAL MODEL]")
    try:
        orig_result = original_detector.detect_crisis(case['text'])
        orig_prediction = (orig_result['crisis_name'], orig_result['severity'])
        orig_match = orig_prediction == case['expected']
        print(f"Result: {orig_result['crisis_name']} - {orig_result['severity']}")
        print(f"Match: {'✓' if orig_match else '✗'}")
    except Exception as e:
        print(f"ERROR: {e}")
        orig_match = False
        orig_prediction = ("ERROR", "ERROR")
    
    print("\n" + "-" * 100)
    
    # Test tuned model
    print("\n[TUNED MODEL]")
    try:
        tuned_result = tuned_detector.detect_crisis(case['text'])
        tuned_prediction = (tuned_result['crisis_name'], tuned_result['severity'])
        tuned_match = tuned_prediction == case['expected']
        print(f"Result: {tuned_result['crisis_name']} - {tuned_result['severity']}")
        print(f"Match: {'✓' if tuned_match else '✗'}")
    except Exception as e:
        print(f"ERROR: {e}")
        tuned_match = False
        tuned_prediction = ("ERROR", "ERROR")
    
    # Compare
    print("\n" + "-" * 100)
    
    result_entry = {
        "case": case['description'],
        "category": case['category'],
        "expected": case['expected'],
        "original": orig_prediction,
        "tuned": tuned_prediction,
        "original_match": orig_match,
        "tuned_match": tuned_match
    }
    
    if tuned_match and not orig_match:
        print("✓ IMPROVEMENT: Fixed by tuned model!")
        results["improvements"].append(result_entry)
    elif orig_match and not tuned_match:
        print("✗ REGRESSION: Broken by tuned model!")
        results["regressions"].append(result_entry)
    elif tuned_match and orig_match:
        print("= UNCHANGED: Both correct")
        results["unchanged_correct"].append(result_entry)
    else:
        print("= UNCHANGED: Both incorrect")
        results["unchanged_incorrect"].append(result_entry)
    
    # Track by category
    if case['category'] not in category_stats:
        category_stats[case['category']] = {
            "total": 0,
            "original_correct": 0,
            "tuned_correct": 0
        }
    category_stats[case['category']]["total"] += 1
    if orig_match:
        category_stats[case['category']]["original_correct"] += 1
    if tuned_match:
        category_stats[case['category']]["tuned_correct"] += 1

# Print summary
print("\n" + "=" * 100)
print("OVERALL SUMMARY")
print("=" * 100)
print(f"Improvements: {len(results['improvements'])}/{len(test_cases)}")
print(f"Regressions: {len(results['regressions'])}/{len(test_cases)}")
print(f"Unchanged Correct: {len(results['unchanged_correct'])}/{len(test_cases)}")
print(f"Unchanged Incorrect: {len(results['unchanged_incorrect'])}/{len(test_cases)}")
print(f"\nNet improvement: {len(results['improvements']) - len(results['regressions'])} cases")

orig_accuracy = (len(results['improvements']) - len(results['improvements']) + len(results['unchanged_correct'])) / len(test_cases)
tuned_accuracy = (len(results['improvements']) + len(results['unchanged_correct'])) / len(test_cases)

print(f"\nOriginal accuracy: {orig_accuracy * 100:.1f}%")
print(f"Tuned accuracy: {tuned_accuracy * 100:.1f}%")
print(f"Improvement: {(tuned_accuracy - orig_accuracy) * 100:+.1f}%")

print("\n" + "=" * 100)
print("CATEGORY BREAKDOWN")
print("=" * 100)
for category, stats in category_stats.items():
    orig_pct = stats['original_correct'] / stats['total'] * 100
    tuned_pct = stats['tuned_correct'] / stats['total'] * 100
    print(f"\n{category}:")
    print(f"  Original: {stats['original_correct']}/{stats['total']} ({orig_pct:.0f}%)")
    print(f"  Tuned:    {stats['tuned_correct']}/{stats['total']} ({tuned_pct:.0f}%)")
    print(f"  Change:   {tuned_pct - orig_pct:+.0f}%")

if results['improvements']:
    print("\n" + "=" * 100)
    print("IMPROVEMENTS DETAIL")
    print("=" * 100)
    for imp in results['improvements']:
        print(f"\n✓ {imp['case']}")
        print(f"  Expected: {imp['expected']}")
        print(f"  Original: {imp['original']} ✗")
        print(f"  Tuned:    {imp['tuned']} ✓")

if results['regressions']:
    print("\n" + "=" * 100)
    print("REGRESSIONS DETAIL")
    print("=" * 100)
    for reg in results['regressions']:
        print(f"\n✗ {reg['case']}")
        print(f"  Expected: {reg['expected']}")
        print(f"  Original: {reg['original']} ✓")
        print(f"  Tuned:    {reg['tuned']} ✗")

print("\n" + "=" * 100)
print("RECOMMENDATION")
print("=" * 100)

if len(results['improvements']) > len(results['regressions']) + 1:
    print("✓ RECOMMENDED: Adopt tuned model (clear improvement)")
elif len(results['improvements']) > len(results['regressions']):
    print("✓ SUGGESTED: Consider adopting tuned model (slight improvement)")
elif len(results['improvements']) == len(results['regressions']):
    print("= NEUTRAL: No clear winner, consider other factors")
else:
    print("✗ NOT RECOMMENDED: Needs further tuning")

# Save detailed results
with open('model_comparison_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nDetailed results saved to model_comparison_results.json")


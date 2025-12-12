"""
Test Iroha AI Study Buddy
Quick demo of Isshiki Iroha persona
"""
from ai_core import ai_service
import sys

print("-" * 60)
print("   IROHA ISSHIKI - STUDENT COUNCIL PRESIDENT AI")
print("-" * 60)

# Check API Key
try:
    ai_service.client
except Exception as e:
    print("Error: API Key not found or invalid.")
    sys.exit(1)

# Test scenarios
test_cases = [
    {
        "title": "Request: Calculus Help",
        "message": "Iroha, can you help me understand derivatives?"
    },
    {
        "title": "Status: Low Motivation",
        "message": "This math problem is too hard... I don't think I can do it."
    },
    {
        "title": "Status: Problem Solved",
        "message": "I finally solved it! Thanks to your explanation!"
    },
    {
        "title": "Status: Fatigue Detected",
        "message": "I've been studying for 3 hours straight... I'm so tired."
    },
    {
        "title": "Request: Study Strategy",
        "message": "Do you have any tips for preparing for tomorrow's exam?"
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\nExample {i}: {test['title']}")
    print("-" * 30)
    print(f"Senpai: {test['message']}")
    
    try:
        result = ai_service.get_response(
            message=test['message'],
            persona_key="iroha"
        )
        
        print(f"\n{result['persona']['name']}:")
        print(f"{result['response']}")
        print(f"\n[Time: {result['metadata']['duration_seconds']}s]")
        
    except Exception as e:
        print(f"\nError: {e}")

print(f"\n{'-'*60}")
print("Demo session ended. Good luck, Senpai.")
print("-" * 60)

"""Test script for questions API."""

import requests
import json
import sys


def test_ask_question():
    """Test the POST /api/v1/collections/{id}/questions endpoint."""
    base_url = "http://localhost:8001"
    
    # Test 1: Ask a question
    print("Test 1: Ask a question")
    print("-" * 50)
    
    response = requests.post(
        f"{base_url}/api/v1/collections/1/questions",
        headers={"Content-Type": "application/json"},
        json={"question": "What happened in January 2026?"}
    )
    
    print(f"Status: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    print()
    
    # Test 2: Ask with options
    print("Test 2: Ask with custom options")
    print("-" * 50)
    
    response = requests.post(
        f"{base_url}/api/v1/collections/1/questions",
        headers={"Content-Type": "application/json"},
        json={
            "question": "Where was I on January 1 2026?",
            "options": {
                "include_evidence": True,
                "include_trace": True,
                "max_evidence_items": 5
            }
        }
    )
    
    print(f"Status: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    print()
    
    # Test 3: Collection not found
    print("Test 3: Collection not found")
    print("-" * 50)
    
    response = requests.post(
        f"{base_url}/api/v1/collections/999/questions",
        headers={"Content-Type": "application/json"},
        json={"question": "Test question?"}
    )
    
    print(f"Status: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    print()
    
    # Test 4: Health check
    print("Test 4: Health check")
    print("-" * 50)
    
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    test_ask_question()
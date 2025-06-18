#!/usr/bin/env python3
"""
Script to verify if an OpenRouter API key for Llama 4 Maverick is working correctly.
This sends a simple test request to the OpenRouter API and checks the response.
"""

import os
import sys
import json
import requests
from typing import Dict, Any, Optional, List
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API endpoint and headers
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_available_models(api_key: str) -> List[str]:
    """
    Get a list of available models from OpenRouter.
    
    Args:
        api_key: The OpenRouter API key
        
    Returns:
        List of available model IDs
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return [model.get("id") for model in data.get("data", [])]
    except requests.exceptions.RequestException as e:
        print(f"Error getting models: {e}")
        return []


def test_openrouter_key(api_key: str, model: str = "meta-llama/llama-3-70b-instruct") -> bool:
    """
    Test if the provided OpenRouter API key is working.
    
    Args:
        api_key: The OpenRouter API key to test
        model: The model name to use for testing
        
    Returns:
        bool: True if the test was successful, False otherwise
    """
    if not api_key:
        print("❌ No API key provided")
        return False
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test payload
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, world!'"}
        ]
    }
    
    try:
        print(f"\nTesting connection to OpenRouter API with model: {model}")
        print("-" * 60)
        
        # Test API key by listing available models
        print("Fetching available models...")
        models = get_available_models(api_key)
        if not models:
            print("❌ Failed to fetch available models. Please check your API key.")
            return False
            
        print(f"✅ Success! Found {len(models)} available models.")
        
        # Test a simple completion
        print("\nTesting text completion...")
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        print("✅ Success! Received response from the API.")
        print("\nResponse sample:")
        print(json.dumps(result, indent=2)[:500] + "...")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response is not None:
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False


def main():
    """Main function to run the OpenRouter API key test."""
    # Get API key from environment variable or command line argument
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if len(sys.argv) > 1 and not api_key:
        api_key = sys.argv[1]
    
    if not api_key:
        print("\n❌ No API key provided.")
        print("Please set the OPENROUTER_API_KEY environment variable or provide it as a command-line argument.")
        print("Example: python test_openrouter_key.py your_api_key_here")
        return
    
    # Hide the API key in the output
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "*" * len(api_key)
    print(f"\nTesting OpenRouter API key: {masked_key}")
    
    # Test the API key
    success = test_openrouter_key(api_key)
    
    if success:
        print("\n✅ OpenRouter API key is working correctly!")
    else:
        print("\n❌ Failed to verify OpenRouter API key. Please check your key and try again.")


if __name__ == "__main__":
    main()

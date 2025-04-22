#!/usr/bin/env python3
"""
Script to verify if an OpenRouter API key for Llama 4 Maverick is working correctly.
This sends a simple test request to the OpenRouter API and checks the response.
"""

import os
import sys
import json
import requests
from typing import Dict, Any, Optional
import time

# The OpenRouter API key to test
OPENROUTER_API_KEY = "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"

# API endpoint and headers
API_URL = "https://openrouter.ai/api/v1/chat/completions"

def get_available_models(api_key: str) -> list:
    """
    Get a list of available models from OpenRouter.
    
    Args:
        api_key (str): The OpenRouter API key
        
    Returns:
        list: List of available model IDs
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
        if response.status_code == 200:
            data = response.json()
            models = [model.get("id") for model in data.get("data", [])]
            return models
        else:
            print(f"Error getting models: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"Exception getting models: {e}")
        return []

def test_openrouter_key(api_key: str, model: str) -> None:
    """
    Test if the provided OpenRouter API key is working.
    
    Args:
        api_key (str): The OpenRouter API key to test
        model (str): The model name to use for testing
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",  # Required for OpenRouter
        "X-Title": "API Key Verification Test"  # Optional but good practice
    }
    
    # Simple test message
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Can you confirm that you're Llama 4 Maverick and that my API connection is working?"}
        ],
        "max_tokens": 150
    }
    
    print(f"Testing OpenRouter API key with model: {model}")
    print("Sending test request...")
    
    try:
        start_time = time.time()
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        end_time = time.time()
        
        if response.status_code == 200:
            response_data = response.json()
            model_used = response_data.get("model", "unknown")
            response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "No content returned")
            
            print("\n✅ Success! The API key is working correctly.")
            print(f"Model used: {model_used}")
            print(f"Response time: {end_time - start_time:.2f} seconds")
            print("\nModel response:")
            print("-------------")
            print(response_text)
            print("-------------")
            
            return True
        else:
            print(f"\n❌ Error: API returned status code {response.status_code}")
            print("Response content:")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Connection Error: {e}")
        return False
    except json.JSONDecodeError:
        print("\n❌ Error: Received invalid JSON response")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    # Use command line argument as API key if provided, otherwise use the default
    api_key = sys.argv[1] if len(sys.argv) > 1 else OPENROUTER_API_KEY
    
    print("OpenRouter API Key Test for Llama 4 Maverick")
    print("===========================================")
    
    # First, let's get a list of available models
    print("Fetching available models from OpenRouter...")
    available_models = get_available_models(api_key)
    
    if available_models:
        print("\nAvailable models on OpenRouter:")
        for model in available_models:
            print(f"- {model}")
        
        # Look for Llama 4 models
        llama4_models = [m for m in available_models if "llama-4" in m.lower() or "llama4" in m.lower()]
        
        if llama4_models:
            print("\nFound Llama 4 models:")
            for model in llama4_models:
                print(f"- {model}")
            
            # Try each Llama 4 model until one works
            for model in llama4_models:
                print(f"\nTrying model: {model}")
                if test_openrouter_key(api_key, model):
                    break
        else:
            print("\nNo Llama 4 models found. Trying with default models...")
            # Try with some common model IDs
            model_ids = [
                "meta/llama-4-maverick",
                "meta/llama-4",
                "meta/llama-4-open-8b",
                "llama-4-maverick",
                "llama-4"
            ]
            
            for model in model_ids:
                if test_openrouter_key(api_key, model):
                    break
    else:
        print("\nCould not fetch available models. Trying with default model IDs...")
        # Try with some common model IDs
        model_ids = [
            "meta/llama-4-maverick",
            "meta/llama-4",
            "meta/llama-4-open-8b",
            "llama-4-maverick",
            "llama-4"
        ]
        
        for model in model_ids:
            if test_openrouter_key(api_key, model):
                break
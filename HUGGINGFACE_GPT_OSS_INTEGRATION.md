# HuggingFace GPT-OSS-120B Integration Guide

## Overview

This document describes how to integrate OpenAI's GPT-OSS-120B model through HuggingFace's router endpoint for AI-powered app opportunity analysis in Trend Scout.

## Model Details

- **Model**: `openai/gpt-oss-120b`
- **Parameters**: 120B (117B with 5.1B active)
- **License**: Apache 2.0 (permissive, commercial use allowed)
- **Capabilities**: Reasoning, function calling, tool use, configurable reasoning levels
- **Provider**: OpenAI (open-source release)

## API Endpoint

**HuggingFace Router Endpoint**: `https://router.huggingface.co/v1/chat/completions`

This is an OpenAI-compatible chat completions API that provides access to the GPT-OSS-120B model without requiring local deployment.

## Authentication

Requires a HuggingFace API token with access to the router service.

```bash
# Set your HuggingFace API key
export HUGGING_FACE_API_KEY=hf_your_token_here
```

## Implementation

### Basic Usage Example

```python
import requests
import os

# Configuration
ROUTER_ENDPOINT = "https://router.huggingface.co/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-120b"
API_KEY = os.getenv("HUGGING_FACE_API_KEY")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": MODEL_NAME,
    "messages": [
        {"role": "user", "content": "Analyze this app opportunity: Calculator Pro"}
    ],
    "max_tokens": 400,
    "temperature": 0.7,
    "top_p": 0.9
}

response = requests.post(ROUTER_ENDPOINT, headers=headers, json=payload)
result = response.json()

# Extract response
ai_response = result["choices"][0]["message"]["content"]
```

### Integration in Trend Scout

The model is integrated in `trendscout/ai_recommender.py`:

```python
class AIRecommender:
    def __init__(self, hf_api_key: Optional[str] = None):
        self.hf_api_key = hf_api_key or os.getenv("HUGGING_FACE_API_KEY")
        self.router_endpoint = "https://router.huggingface.co/v1/chat/completions"
        self.model_name = "openai/gpt-oss-120b"
        
        self.headers = {
            "Authorization": f"Bearer {self.hf_api_key}",
            "Content-Type": "application/json"
        }
    
    def _query_hugging_face(self, prompt: str, max_retries: int = 3) -> str:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        response = requests.post(self.router_endpoint, headers=self.headers, json=payload, timeout=60)
        result = response.json()
        
        return result["choices"][0]["message"]["content"].strip()
```

## Request Format

The API uses OpenAI-compatible chat completions format:

```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [
    {"role": "user", "content": "Your prompt here"}
  ],
  "max_tokens": 400,
  "temperature": 0.7,
  "top_p": 0.9
}
```

## Response Format

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "AI-generated response text"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 150,
    "total_tokens": 175
  }
}
```

## Key Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `max_tokens` | Maximum tokens to generate | 400 | 1-4096 |
| `temperature` | Creativity/randomness | 0.7 | 0.0-2.0 |
| `top_p` | Nucleus sampling | 0.9 | 0.0-1.0 |
| `timeout` | Request timeout | 60s | 10-120s |

## Use Cases in Trend Scout

### 1. App Opportunity Analysis
```python
prompt = f"""
Analyze this app opportunity:
Name: {app_name}
Category: {category}
Rating: {rating}/5 ({rating_count} reviews)
Clone Score: {clone_score}

Provide specific improvement suggestions, monetization strategies, and build estimates.
"""
```

### 2. Market Gap Identification
```python
prompt = f"""
Identify market gaps for this app category: {category}
Current top apps: {top_apps}
Suggest innovative features or approaches that are currently missing.
"""
```

### 3. Technical Implementation Guidance
```python
prompt = f"""
For app "{app_name}" in {category} category:
1. Estimate development time
2. Identify key technical challenges
3. Suggest iOS-specific features
4. Recommend monetization approach
"""
```

## Advantages Over Other Solutions

✅ **High-Quality Reasoning**: 120B parameter model with advanced reasoning capabilities  
✅ **No Local Deployment**: Runs on HuggingFace infrastructure  
✅ **OpenAI Compatible**: Standard chat completions format  
✅ **Cost Effective**: More affordable than OpenAI API  
✅ **Open Source**: Apache 2.0 license allows commercial use  
✅ **Configurable**: Support for different reasoning levels  

## Error Handling

```python
try:
    response = requests.post(router_endpoint, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()
    
    if "choices" in result and len(result["choices"]) > 0:
        return result["choices"][0]["message"]["content"].strip()
    else:
        raise ValueError(f"Unexpected response format: {result}")
        
except requests.exceptions.RequestException as e:
    logger.error(f"API request failed: {e}")
    # Fallback to default recommendations
    
except KeyError as e:
    logger.error(f"Response parsing failed: {e}")
    # Handle malformed response
```

## Rate Limits & Best Practices

- **Timeout**: Use 60+ second timeout for large model responses
- **Retry Logic**: Implement exponential backoff for failed requests
- **Fallback**: Always have default recommendations when AI fails
- **Caching**: Cache responses to reduce API calls
- **Batch Processing**: Group similar requests when possible

## Configuration

Add to your `.env` file:

```bash
# HuggingFace API Configuration
HUGGING_FACE_API_KEY=hf_your_token_here

# AI Recommender Settings (optional)
AI_MAX_TOKENS=400
AI_TEMPERATURE=0.7
AI_TOP_P=0.9
AI_TIMEOUT=60
```

## Testing

```bash
# Test the integration
cd "/Users/billyjo182/Desktop/DevOps/Trend Scout"
source venv/bin/activate

python -c "
from trendscout.ai_recommender import AIRecommender

recommender = AIRecommender()
sample_app = {
    'name': 'Calculator Pro',
    'category': 'Utilities',
    'rating_avg': 4.5,
    'total': 2.5
}

recommendation = recommender.generate_recommendation(sample_app)
print(f'Generated: {recommendation.improvement_summary}')
"
```

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify `HUGGING_FACE_API_KEY` is set correctly
2. **Timeout**: Increase timeout for large responses (60+ seconds)
3. **Rate Limits**: Implement retry logic with exponential backoff
4. **Response Format**: Ensure you're parsing the OpenAI-compatible response structure

### Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed API request/response information
```

## Model Alternatives

If GPT-OSS-120B is unavailable, the system can fallback to:

- `meta-llama/Llama-2-7b-chat-hf`
- `microsoft/DialoGPT-medium`
- Default rule-based recommendations

## Performance

- **Response Time**: 5-15 seconds for 400 token responses
- **Quality**: High-quality, contextual recommendations
- **Reliability**: Robust error handling with fallback mechanisms
- **Cost**: Significantly lower than OpenAI's hosted API

## Future Enhancements

- **Reasoning Levels**: Configure low/medium/high reasoning for different use cases
- **Function Calling**: Leverage tool use capabilities for data integration
- **Fine-tuning**: Customize model for app-specific recommendations
- **Streaming**: Implement streaming responses for real-time updates

---

**Last Updated**: August 19, 2025  
**Model Version**: openai/gpt-oss-120b  
**Integration Status**: ✅ Active and Working
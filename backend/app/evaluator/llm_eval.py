"""
LLM-based evaluation using Groq API with fallback to mock responses
"""
import logging
import json
import os
from typing import Dict, Any, Optional
import httpx
import asyncio
from app.config import settings

logger = logging.getLogger(__name__)

class LLMEvaluator:
    """Handles LLM-based evaluation of Excel answers"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "https://api.groq.com/openai/v1"
        
    async def evaluate_answer(
        self,
        question: Dict[str, Any],
        answer_text: str,
        deterministic_summary: Dict[str, Any],
        artifact_summary: str = ""
    ) -> Dict[str, Any]:
        """Evaluate answer using LLM with structured JSON output"""
        
        if settings.mock_mode or not settings.groq_api_key:
            return self._mock_llm_response(deterministic_summary)
        
        try:
            prompt = self._build_evaluation_prompt(
                question, answer_text, deterministic_summary, artifact_summary
            )
            
            response = await self._call_groq_api(prompt)
            return self._parse_llm_response(response)
            
        except Exception as e:
            logger.error(f"LLM evaluation error: {e}")
            return self._fallback_response(deterministic_summary)
    
    def _build_evaluation_prompt(
        self,
        question: Dict[str, Any],
        answer_text: str,
        deterministic_summary: Dict[str, Any],
        artifact_summary: str
    ) -> str:
        """Build the evaluation prompt with all context"""
        
        golden_answer = question.get("golden_answer", "No specific golden answer provided")
        if isinstance(golden_answer, dict):
            golden_answer = json.dumps(golden_answer, indent=2)
        
        system_prompt = """You are an objective Excel interviewer evaluator. You must return ONLY valid JSON with exactly these keys:
{ "correctness": float (0-4), "explanation": float (0-4), "efficiency": float (0-4), "robustness": float (0-4), "verdict": "pass"|"fail"|"flag", "confidence": float (0.0-1.0), "notes": "short string" }"""
        
        user_prompt = f"""Question: {question.get('text', '')}
GoldenAnswerOrTests: {golden_answer}
DeterministicSummary: {json.dumps(deterministic_summary, indent=2)}
CandidateAnswer: {answer_text}
ArtifactSummary: {artifact_summary}

Rubric:
 - Correctness (0-4): how correct the result is
 - Explanation (0-4): clarity of reasoning & edge-case handling
 - Efficiency (0-4): formula elegance, computational efficiency
 - Robustness (0-4): handles edge-cases and invalid inputs

Instructions:
1) Score each rubric 0-4 (use one decimal if needed).
2) Provide 'verdict' = "pass" if overall_score >= 2.5 AND confidence >= 0.6, "flag" if confidence < 0.45, else "fail".
3) Keep notes concise (<= 40 words).
4) Output ONLY the JSON object, nothing else."""
        
        return {"system": system_prompt, "user": user_prompt}
    
    async def _call_groq_api(self, prompt: Dict[str, str]) -> str:
        """Make API call to Groq"""
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mixtral-8x7b-32768",  # Groq's free tier model
            "messages": [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]}
            ],
            "temperature": 0.1,
            "max_tokens": 500,
            "top_p": 0.9
        }
        
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate LLM JSON response"""
        try:
            # Extract JSON from response (in case there's extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[json_start:json_end]
            parsed = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["correctness", "explanation", "efficiency", "robustness", "verdict", "confidence", "notes"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate ranges
            for score_field in ["correctness", "explanation", "efficiency", "robustness"]:
                if not (0 <= parsed[score_field] <= 4):
                    parsed[score_field] = max(0, min(4, parsed[score_field]))
            
            if not (0 <= parsed["confidence"] <= 1):
                parsed["confidence"] = max(0, min(1, parsed["confidence"]))
            
            if parsed["verdict"] not in ["pass", "fail", "flag"]:
                parsed["verdict"] = "fail"
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Response was: {response_text}")
            return self._fallback_response({})
    
    def _mock_llm_response(self, deterministic_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock LLM response for testing"""
        # Base scores on deterministic results
        det_score = deterministic_summary.get("score", 0.0)
        
        return {
            "correctness": min(4.0, det_score * 4 + 0.5),
            "explanation": min(4.0, det_score * 3 + 1.0),
            "efficiency": min(4.0, det_score * 3.5 + 0.5),
            "robustness": min(4.0, det_score * 3 + 0.8),
            "verdict": "pass" if det_score >= 0.7 else "fail",
            "confidence": 0.8,
            "notes": f"Mock evaluation based on {deterministic_summary.get('passed_tests', 0)} passed tests"
        }
    
    def _fallback_response(self, deterministic_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback response when LLM fails"""
        det_score = deterministic_summary.get("score", 0.0)
        
        return {
            "correctness": det_score * 2,  # Scale to 0-2 range for safety
            "explanation": 2.0,  # Neutral score
            "efficiency": 2.0,
            "robustness": 2.0,
            "verdict": "flag",  # Always flag when LLM fails
            "confidence": 0.3,
            "notes": "LLM evaluation failed, using deterministic only"
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

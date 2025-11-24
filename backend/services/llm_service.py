"""
LLM Service for analyzing transcripts and generating summaries and tags
"""
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI


class LLMService:
    """Service for analyzing transcripts using OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the LLM service
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
    
    def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze a transcript and generate summary, tags, roles, emotions, intent, and insights
        
        Args:
            transcript: The transcript text to analyze
            
        Returns:
            Dict with 'summary', 'tags', 'roles', 'emotions', 'intent', 'mood', and 'insights' keys
        """
        if not transcript or not transcript.strip():
            return {
                "summary": "No transcript available.",
                "tags": ["no-transcript"],
                "roles": {},
                "emotions": [],
                "intent": "unknown",
                "mood": "neutral",
                "insights": []
            }
        
        # Simplified prompt for faster processing - truncate transcript in prompt
        transcript_truncated = transcript[:1000] if len(transcript) > 1000 else transcript
        prompt = f"""Analyze this phone call transcript. Return ONLY valid JSON:

{{
    "summary": "2-3 sentence summary",
    "tags": ["tag1", "tag2"],
    "roles": {{"speaker1": "agent/customer", "speaker2": "agent/customer"}},
    "emotions": ["emotion1", "emotion2"],
    "intent": "purchase/complaint/information/support/cancel/other",
    "mood": "positive/negative/neutral/mixed",
    "insights": ["insight1", "insight2"]
}}

Available tags: "client wants to buy", "wrong number", "needs follow-up", "voicemail", "complaint", "inquiry", "sale", "support", "other"
Available emotions: "happy", "frustrated", "angry", "satisfied", "confused", "neutral"

Transcript:
{transcript_truncated}

JSON:"""

        try:
            print(f"[LLM] Analyzing transcript ({len(transcript)} characters)...")
            # Optimize for speed: use faster model, reduce tokens, lower temperature
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert assistant that analyzes phone call transcripts. Always respond with valid JSON only. Be thorough in detecting roles, emotions, intent, and extracting insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Very low temperature for fastest, most deterministic responses
                max_tokens=500,  # Further reduced for faster responses
                timeout=15.0,  # Shorter timeout to prevent hanging
                stream=False,  # Explicitly disable streaming for faster response
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON from response
            import json
            try:
                # Remove markdown code blocks if present
                if result_text.startswith("```"):
                    result_text = result_text.split("```")[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]
                    result_text = result_text.strip()
                
                result = json.loads(result_text)
                
                # Validate and extract all fields
                summary = result.get("summary", "Unable to generate summary.")
                tags = result.get("tags", [])
                roles = result.get("roles", {})
                emotions = result.get("emotions", [])
                intent = result.get("intent", "unknown")
                mood = result.get("mood", "neutral")
                insights = result.get("insights", [])
                
                if not isinstance(tags, list):
                    tags = [tags] if tags else []
                if not isinstance(emotions, list):
                    emotions = [emotions] if emotions else []
                if not isinstance(insights, list):
                    insights = [insights] if insights else []
                if not isinstance(roles, dict):
                    roles = {}
                
                print(f"[LLM] ✅ Analysis completed: {len(tags)} tags, {len(emotions)} emotions, intent: {intent}")
                return {
                    "summary": summary,
                    "tags": tags,
                    "roles": roles,
                    "emotions": emotions,
                    "intent": intent,
                    "mood": mood,
                    "insights": insights
                }
            except json.JSONDecodeError as e:
                print(f"[LLM] ⚠️ Failed to parse JSON response: {e}")
                print(f"[LLM] Raw response: {result_text[:200]}")
                # Fallback: try to extract summary and tags manually
                return self._fallback_parse(result_text)
                
        except Exception as e:
            print(f"[LLM] ❌ Error analyzing transcript: {e}")
            return {
                "summary": f"Error analyzing transcript: {str(e)}",
                "tags": ["analysis-error"],
                "roles": {},
                "emotions": [],
                "intent": "unknown",
                "mood": "neutral",
                "insights": []
            }
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parser if JSON parsing fails"""
        # Try to extract summary and tags from text
        summary = text.split("summary")[-1].split("tags")[0].strip(":,\"") if "summary" in text else "Unable to parse summary."
        tags = []
        
        # Look for common tag patterns
        tag_keywords = ["client wants to buy", "wrong number", "needs follow-up", "voicemail", "complaint", "inquiry", "sale", "support"]
        for keyword in tag_keywords:
            if keyword.lower() in text.lower():
                tags.append(keyword)
        
        if not tags:
            tags = ["other"]
        
        return {
            "summary": summary[:200],  # Limit summary length
            "tags": tags,
            "roles": {},
            "emotions": [],
            "intent": "unknown",
            "mood": "neutral",
            "insights": []
        }


# Global instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        # Default to gpt-4o-mini for faster and cheaper processing
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        _llm_service = LLMService(model=model)
    return _llm_service


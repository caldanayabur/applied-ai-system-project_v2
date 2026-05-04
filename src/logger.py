"""
Structured logging for the music recommender system.

This module provides logging utilities to track system decisions, LLM interactions,
errors, and performance metrics.
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredLogger:
    """
    A structured logging wrapper that logs events as JSON for better tracking
    and analysis of system behavior.
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Create console handler if it doesn't exist
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            
            # Format: [TIMESTAMP] LEVEL: MESSAGE
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _format_event(self, event_type: str, details: Dict[str, Any]) -> str:
        """Format an event as JSON."""
        from datetime import datetime, timezone
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **details
        }
        return json.dumps(event)
    
    def log_recommendation_request(
        self,
        user_prefs: Dict[str, Any],
        num_songs: int,
        k: int
    ) -> None:
        """Log when a recommendation request is received."""
        details = {
            "user_prefs": str(user_prefs),
            "num_songs": num_songs,
            "k": k
        }
        self.logger.info(self._format_event("recommendation_request", details))
    
    def log_scoring_complete(
        self,
        num_songs: int,
        top_k: int,
        scores: Optional[list] = None
    ) -> None:
        """Log when scoring is complete."""
        details = {
            "num_songs_scored": num_songs,
            "top_k_returned": top_k,
            "top_scores": scores[:top_k] if scores else None
        }
        self.logger.info(self._format_event("scoring_complete", details))
    
    def log_llm_call_start(
        self,
        prompt_tokens: int,
        model: str
    ) -> None:
        """Log when an LLM call is about to be made."""
        details = {
            "prompt_tokens": prompt_tokens,
            "model": model
        }
        self.logger.info(self._format_event("llm_call_start", details))
    
    def log_llm_call_end(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Log the result of an LLM call."""
        details = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "success": success,
            "error": error
        }
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, self._format_event("llm_call_end", details))
    
    def log_explanation_generated(
        self,
        song_title: str,
        source: str,
        explanation_length: int
    ) -> None:
        """Log when an explanation is generated (LLM or fallback)."""
        details = {
            "song_title": song_title,
            "source": source,  # "llm" or "fallback"
            "explanation_length": explanation_length
        }
        self.logger.info(self._format_event("explanation_generated", details))
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an error with context."""
        details = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        self.logger.error(self._format_event("error", details))
    
    def info(self, message: str) -> None:
        """Log an info-level message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning-level message."""
        self.logger.warning(message)
    
    def debug(self, message: str) -> None:
        """Log a debug-level message."""
        self.logger.debug(message)


# Global logger instance
recommender_logger = StructuredLogger("music_recommender")

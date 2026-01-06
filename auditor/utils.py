import os
import time
import logging
import json

# Logger initialization for structured JSON telemetry.
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Logger:
    """Helper for structured JSON logging compatible with CloudWatch Insights (SRP)."""
    @staticmethod
    def log(message, level="INFO", **kwargs):
        log_data = {
            "message": message,
            "level": level.upper(),
            "timestamp": time.time(),
            "stage": os.environ.get('SLS_STAGE', 'unknown'),
            **kwargs
        }
        logger.info(json.dumps(log_data))

class Poller:
    """Utility for exponential backoff state polling with execution guardrails."""
    @staticmethod
    def wait(action_name, check_fn, success_states, failure_states=None, 
             initial_delay=2, max_delay=30, backoff_factor=1.5, max_attempts=20):
        delay = initial_delay
        attempts = 0
        while attempts < max_attempts:
            state = check_fn()
            if state in success_states:
                Logger.log(f"{action_name} completed successfully", state=state, attempts=attempts)
                return state
            if failure_states and state in failure_states:
                Logger.log(f"{action_name} failed", level="ERROR", state=state, attempts=attempts)
                return state
                
            attempts += 1
            Logger.log(f"{action_name} still in progress", state=state, next_wait=delay, attempt=attempts)
            time.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)
        
        raise TimeoutError(f"{action_name} timed out after {max_attempts} attempts")

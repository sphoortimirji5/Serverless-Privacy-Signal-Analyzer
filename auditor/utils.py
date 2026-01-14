import os
import time
import json
from aws_lambda_powertools import Logger as PTLogger
from aws_lambda_powertools import Metrics as PTMetrics
from aws_lambda_powertools import Tracer as PTTracer
from aws_lambda_powertools.metrics import MetricUnit

# Core Observability instances
# service="privacy-auditor" can be overridden by POWERTOOLS_SERVICE_NAME env var
tracer = PTTracer()
logger = PTLogger()
metrics = PTMetrics(namespace="PrivacySignalAnalyzer")

class Logger:
    """
    Helper for structured JSON logging compatible with CloudWatch Insights.
    Refactored to use AWS Lambda Powertools for production-grade telemetry.
    """
    @staticmethod
    def log(message, level="INFO", **kwargs):
        """
        Maintains backward compatibility with original log() method
        while routing through Powertools Logger.
        """
        lvl = level.upper()
        if lvl == "DEBUG":
            logger.debug(message, **kwargs)
        elif lvl == "WARNING":
            logger.warning(message, **kwargs)
        elif lvl == "ERROR":
            logger.error(message, **kwargs)
        elif lvl == "CRITICAL":
            logger.critical(message, **kwargs)
        else:
            logger.info(message, **kwargs)

    @staticmethod
    def metric(name, unit, value, **dimensions):
        """Emits a custom metric using CloudWatch EMF."""
        metrics.add_metric(name=name, unit=unit, value=value)
        for d_name, d_val in dimensions.items():
            metrics.add_dimension(name=d_name, value=str(d_val))

class Poller:
    """Utility for exponential backoff state polling with execution guardrails."""
    @staticmethod
    @tracer.capture_method
    def wait(action_name, check_fn, success_states, failure_states=None, 
             initial_delay=2, max_delay=30, backoff_factor=1.5, max_attempts=20):
        delay = initial_delay
        attempts = 0
        start_time = time.time()
        
        while attempts < max_attempts:
            state = check_fn()
            if state in success_states:
                duration = time.time() - start_time
                Logger.log(f"{action_name} completed successfully", state=state, attempts=attempts, duration=duration)
                return state
            if failure_states and state in failure_states:
                Logger.log(f"{action_name} failed", level="ERROR", state=state, attempts=attempts)
                return state
                
            attempts += 1
            Logger.log(f"{action_name} still in progress", state=state, next_wait=delay, attempt=attempts)
            time.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)
        
        raise TimeoutError(f"{action_name} timed out after {max_attempts} attempts")

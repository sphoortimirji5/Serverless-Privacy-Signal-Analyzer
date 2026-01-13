# Local Development Guide

## Purpose
The local environment is designed for rapid logic verification and stress testing without requiring AWS credentials or infrastructure. It uses **Python Protocols** to mock AWS SDK (Boto3) interactions.

## Prerequisites
- **Python:** 3.9 or higher.
- **Dependencies:** Install via `pip install -r requirements.txt`.

## Core Logic Verification
Run the standard orchestration suite to verify the end-to-end flow from snapshot trigger to audit completion.
```bash
python3 mock_local_test.py
```

## Stress & Concurrency Testing
Simulate high-concurrency environments to verify backpressure handling and logic resilience.
```bash
python3 mock_stress_test.py
```

## Philosophy: Zero-AWS Dependency
All business logic in `auditor/` and `snapshot/` is decoupled from concrete AWS implementations. This allows for:
1. **Instant Feedback:** No waiting for cloud deployments.
2. **Deterministic Testing:** Mocked responses ensure tests are repeatable.
3. **CI/CD Integration:** Tests can run in any standard containerized environment.

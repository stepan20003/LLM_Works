# Project Overview

> **prime_checker.py**
```python
def is_prime(n: int) -> bool:
    """
    Checks if a number is prime.

    Args:
    n (int): The number to check.

    Returns:
    bool: True if the number is prime, False otherwise.
    """
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
```

**test_prime_c

## Original Request
Create a fast prime number checker utility in Python with unit tests.

## Quick Start / Run Instructions
```bash
# 1. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run test suite
pytest

# 3. Run application
python main.py
```

## Generated Artifacts & Structure
- `REQUIREMENTS.md`: Detailed functional requirements & acceptance criteria
- `ARCHITECTURE.md`: System design and component layout
- `TEST_REPORT.md`: Automated test execution findings
- `PROJECT_REPORT.md`: Comprehensive executive project report
- `CHANGELOG.md`: Full version history and iteration log

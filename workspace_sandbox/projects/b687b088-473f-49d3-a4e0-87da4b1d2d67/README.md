# Project Overview

> Here's a Python calculator package with the requested features.

**calculator.py**
```python
import math

def add(a, b):
    """
    Adds two numbers.

    Args:
        a (float): The first number.
        b (float): The second number.

    Returns:
        float: The sum of a and b.

    Raises:
        TypeError: If a or b is not a number.
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both inputs must be numbers")
    return a + b


## Original Request
Create a Python calculator package with add, subtract, multiply and divide functions. Include input validation, unit tests, README documentation and a simple CLI. Run all tests and return the completed project as a ZIP archive

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

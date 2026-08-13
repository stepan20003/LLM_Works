# System Architecture & Design Specification

## High-Level Architecture
Use a static class with method-based implementation for math operations.

## Subtask Decomposition Graph
- **Implement add method** (DEVELOPER): Implement the add method using the + operator.
- **Implement subtract method** (DEVELOPER): Implement the subtract method using the - operator.
- **Implement multiply method** (DEVELOPER): Implement the multiply method using the * operator.
- **Implement divide method** (DEVELOPER): Implement the divide method using the / operator and handle division by zero.
- **Implement square root method** (DEVELOPER): Implement the square root method using the ** operator and handle negative inputs.
- **Write unit tests for math operations** (DEVELOPER): Write unit tests for all math operations using the unittest framework.

## Execution Pipeline Workflow
```
MANAGER -> ARCHITECT -> DEVELOPER -> REVIEWER -> TESTER -> DEBUGGER -> APPROVED
```

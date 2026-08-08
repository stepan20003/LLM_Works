# AI Development Team (MVP)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

An autonomous multi-agent software engineering platform where specialized AI agents cooperate like a real software engineering company to build production-ready applications from a single natural language prompt.

## Architecture

```mermaid
graph TD
    User([User Prompt]) --> CLI[Typer CLI / Core Engine]
    CLI --> Manager[Manager Agent]
    Manager --> Developer[Developer Agent]
    Developer --> Reviewer[Reviewer Agent]
    Reviewer --> Tester[Tester Agent]
    Tester -->|Test Failure| Debugger[Debugger Agent]
    Debugger --> Developer
    Tester -->|Test Pass| Done([Approved Project DONE])
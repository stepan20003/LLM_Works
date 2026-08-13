"""Requirement coverage tracking for autonomous project validation."""

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Maps common technology keywords to file patterns and content markers
TECH_SIGNATURES = {
    "fastapi": {
        "file_patterns": ["*.py"],
        "content_keywords": ["fastapi", "FastAPI"],
        "description": "FastAPI web framework",
    },
    "jwt": {
        "file_patterns": ["*.py"],
        "content_keywords": ["jwt", "JWT", "jose", "PyJWT", "access_token", "token"],
        "description": "JWT authentication",
    },
    "authentication": {
        "file_patterns": ["*.py"],
        "content_keywords": ["authenticate", "login", "password", "hash", "verify_password", "bcrypt", "passlib"],
        "description": "Authentication system",
    },
    "postgresql": {
        "file_patterns": ["*.py", "*.sql", "*.yml", "*.yaml", "*.toml", "*.cfg", "*.env*"],
        "content_keywords": ["postgresql", "postgres", "psycopg", "DATABASE_URL", "sqlalchemy", "SQLAlchemy"],
        "description": "PostgreSQL database",
    },
    "docker": {
        "file_patterns": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        "content_keywords": [],
        "file_required": ["Dockerfile"],
        "description": "Docker containerization",
    },
    "docker-compose": {
        "file_patterns": ["docker-compose.yml", "docker-compose.yaml"],
        "content_keywords": [],
        "file_required": ["docker-compose.yml", "docker-compose.yaml"],
        "description": "Docker Compose orchestration",
    },
    "tests": {
        "file_patterns": ["test_*.py", "*_test.py"],
        "content_keywords": ["def test_", "pytest", "unittest", "assert"],
        "description": "Unit/integration tests",
    },
    "crud": {
        "file_patterns": ["*.py"],
        "content_keywords": ["create", "read", "update", "delete", "CRUD", "get_", "create_", "update_", "delete_"],
        "description": "CRUD operations",
    },
    "openapi": {
        "file_patterns": ["*.py"],
        "content_keywords": ["openapi", "swagger", "docs", "FastAPI", "APIRouter"],
        "description": "OpenAPI documentation",
    },
    "orm": {
        "file_patterns": ["*.py"],
        "content_keywords": ["sqlalchemy", "SQLAlchemy", "SQLModel", "sqlmodel", "Base", "Column", "Integer", "String", "ForeignKey", "declarative_base", "mapped_column"],
        "description": "ORM / Database models",
    },
    "pydantic": {
        "file_patterns": ["*.py"],
        "content_keywords": ["BaseModel", "pydantic", "Field", "validator"],
        "description": "Pydantic schemas/validation",
    },
    "environment": {
        "file_patterns": [".env.example", ".env", "*.py"],
        "content_keywords": ["environ", "getenv", "dotenv", "settings", "config"],
        "description": "Environment configuration",
    },
}


def extract_requirements_from_prompt(prompt: str) -> list[dict]:
    """Extract technology requirements from a project prompt using keyword matching.
    
    Returns a list of dicts with keys: name, description, tech_key
    """
    prompt_lower = prompt.lower()
    requirements = []
    seen = set()
    
    # Direct keyword matching
    keyword_map = {
        "fastapi": "fastapi",
        "fast api": "fastapi",
        "flask": "fastapi",  # Similar web framework
        "jwt": "jwt",
        "json web token": "jwt",
        "authentication": "authentication",
        "auth": "authentication",
        "login": "authentication",
        "password": "authentication",
        "postgresql": "postgresql",
        "postgres": "postgresql",
        "database": "postgresql",  # Default DB assumption
        "docker compose": "docker-compose",
        "docker-compose": "docker-compose",
        "dockerfile": "docker",
        "docker": "docker",
        "container": "docker",
        "test": "tests",
        "pytest": "tests",
        "unit test": "tests",
        "integration test": "tests",
        "crud": "crud",
        "user crud": "crud",
        "endpoints": "crud",
        "openapi": "openapi",
        "swagger": "openapi",
        "api documentation": "openapi",
        "orm": "orm",
        "sqlalchemy": "orm",
        "sqlmodel": "orm",
        "pydantic": "pydantic",
        "schema": "pydantic",
        "validation": "pydantic",
        "environment": "environment",
        ".env": "environment",
    }
    
    for keyword, tech_key in keyword_map.items():
        if keyword in prompt_lower and tech_key not in seen:
            seen.add(tech_key)
            sig = TECH_SIGNATURES.get(tech_key, {})
            requirements.append({
                "name": sig.get("description", tech_key),
                "tech_key": tech_key,
                "description": sig.get("description", tech_key),
            })
    
    # Always require tests if not explicitly found
    if "tests" not in seen:
        sig = TECH_SIGNATURES["tests"]
        requirements.append({
            "name": sig["description"],
            "tech_key": "tests",
            "description": sig["description"],
        })
    
    return requirements


def check_requirement_coverage(
    requirements: list[dict],
    workspace_path: str,
) -> dict:
    """Check which requirements are satisfied by the workspace files.
    
    Returns a coverage report dict with:
    - requirements: list of {name, satisfied, evidence}
    - satisfied_count: int
    - total_count: int  
    - coverage_pct: float
    - missing: list of requirement names not satisfied
    """
    ws = Path(workspace_path)
    if not ws.exists():
        return {
            "requirements": [],
            "satisfied_count": 0,
            "total_count": len(requirements),
            "coverage_pct": 0.0,
            "missing": [r["name"] for r in requirements],
        }
    
    # Collect all files in workspace
    all_files = []
    for f in ws.rglob("*"):
        if f.is_file() and "__pycache__" not in str(f) and ".pyc" not in str(f):
            all_files.append(f)
    
    # Build filename list for pattern matching
    file_names = [f.name for f in all_files]
    rel_paths = []
    for f in all_files:
        try:
            rel_paths.append(str(f.relative_to(ws)))
        except ValueError:
            rel_paths.append(f.name)
    
    # Read file contents for keyword matching (limit to text files)
    text_extensions = {".py", ".js", ".ts", ".go", ".java", ".rs", ".toml", ".yml", ".yaml",
                       ".json", ".cfg", ".ini", ".env", ".md", ".txt", ".sql", ".sh"}
    file_contents = {}
    for f in all_files:
        if f.suffix.lower() in text_extensions or f.name in {"Dockerfile", ".env.example", "Makefile"}:
            try:
                file_contents[str(f.relative_to(ws))] = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass
    
    results = []
    satisfied_count = 0
    missing = []
    
    for req in requirements:
        tech_key = req.get("tech_key", "")
        sig = TECH_SIGNATURES.get(tech_key, {})
        satisfied = False
        evidence = []
        
        # Check for required files (exact match)
        required_files = sig.get("file_required", [])
        if required_files:
            for rf in required_files:
                matching = [rp for rp in rel_paths if rp.endswith(rf) or Path(rp).name == rf]
                if matching:
                    satisfied = True
                    evidence.append(f"File found: {matching[0]}")
                    break
        
        # Check for file pattern matches
        file_patterns = sig.get("file_patterns", [])
        for pattern in file_patterns:
            if pattern.startswith("*."):
                ext = pattern[1:]  # e.g., ".py"
                matching = [rp for rp in rel_paths if rp.endswith(ext)]
            else:
                matching = [rp for rp in rel_paths if Path(rp).name == pattern or rp.endswith(pattern)]
            if matching:
                # Check content keywords in matching files
                content_keywords = sig.get("content_keywords", [])
                if not content_keywords:
                    # No content check needed, file existence is enough
                    if required_files:  # Already handled above
                        pass
                    else:
                        satisfied = True
                        evidence.append(f"File pattern match: {matching[0]}")
                else:
                    for fp in matching:
                        content = file_contents.get(fp, "")
                        for kw in content_keywords:
                            if kw in content:
                                satisfied = True
                                evidence.append(f"Keyword '{kw}' found in {fp}")
                                break
                        if satisfied:
                            break
            if satisfied:
                break
        
        if satisfied:
            satisfied_count += 1
        else:
            missing.append(req["name"])
        
        results.append({
            "name": req["name"],
            "tech_key": tech_key,
            "satisfied": satisfied,
            "evidence": evidence,
        })
    
    total = len(requirements)
    coverage_pct = round((satisfied_count / total) * 100.0, 1) if total > 0 else 100.0
    
    return {
        "requirements": results,
        "satisfied_count": satisfied_count,
        "total_count": total,
        "coverage_pct": coverage_pct,
        "missing": missing,
    }

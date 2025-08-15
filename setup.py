#!/usr/bin/env python3

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")
else:
    long_description = "🐕‍🦺 Comprehensive validation and accountability framework for AI assistants"

# Define requirements directly
requirements = [
    "click>=8.0.0",
    "rich>=12.0.0",
    "pyyaml>=6.0",
    "requests>=2.28.0",
    "watchdog>=2.1.0",
    "gitpython>=3.1.0",
    "jsonschema>=4.0.0",
    "jinja2>=3.1.0",
    "colorama>=0.4.0",
    "python-dateutil>=2.8.0",
    "pathspec>=0.10.0"
]

setup(
    name="claude-guardrail-system",
    version="1.0.0",
    author="Ole Magnus Kikut",
    author_email="your.email@example.com",
    description="🐕‍🦺 Comprehensive validation and accountability framework for AI assistants",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/claude-guardrail-system",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/claude-guardrail-system/issues",
        "Documentation": "https://github.com/yourusername/claude-guardrail-system/blob/main/docs/",
        "Source Code": "https://github.com/yourusername/claude-guardrail-system",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "pre-commit>=2.20.0",
            "isort>=5.10.0",
        ],
        "visual": [
            "playwright>=1.40.0",
            "pillow>=9.0.0",
        ],
        "web": [
            "fastapi>=0.95.0",
            "uvicorn>=0.20.0",
            "jinja2>=3.1.0",
        ],
        "all": [
            "playwright>=1.40.0",
            "pillow>=9.0.0", 
            "fastapi>=0.95.0",
            "uvicorn>=0.20.0",
            "jinja2>=3.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "claude-guard=claude_guardrail.cli.main:main",
            "claude-validate=claude_guardrail.validation.pipeline:main",
            "claude-mcp=claude_guardrail.mcp.tool_guardian:main",
        ],
    },
    include_package_data=True,
    package_data={
        "claude_guardrail": [
            "config/*.yaml",
            "templates/*.j2",
            "../assets/logos/*.svg",
        ],
    },
    zip_safe=False,
    keywords=[
        "ai", "claude", "validation", "accountability", "testing", 
        "automation", "quality-assurance", "mcp", "playwright"
    ],
)
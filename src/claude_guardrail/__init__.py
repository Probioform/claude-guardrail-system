"""
Claude Guardrail System
Comprehensive validation and accountability framework for AI assistants

🐕‍🦺 Stop babysitting AI - Make Claude accountable for its work
"""

__version__ = "1.0.0"
__author__ = "Ole Magnus Kikut"
__description__ = "Comprehensive validation and accountability framework for AI assistants"

from .validation.pipeline import ValidationPipeline
from .mcp.tool_guardian import MCPToolGuardian  
from .visual.playwright_validator import PlaywrightMCPValidator
from .cli.main import main as cli_main

__all__ = [
    "ValidationPipeline", 
    "MCPToolGuardian", 
    "PlaywrightMCPValidator",
    "cli_main"
]

# ASCII Art Guard Dog
GUARD_DOG_ASCII = """
    🐕‍🦺 Claude Guardrail System
    ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
    █ ACCOUNTABILITY • VALIDATION • PROOF █
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
"""

def show_banner():
    """Display the guard dog banner"""
    print(GUARD_DOG_ASCII)

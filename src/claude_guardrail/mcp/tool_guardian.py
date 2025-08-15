#!/usr/bin/env python3
"""
MCP Tool Guardian
Validates Claude's tool usage claims against actual tool execution
"""

import json
import re
import subprocess
import os
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class MCPTool:
    name: str
    description: str
    required_params: List[str]
    optional_params: List[str]
    usage_examples: List[str]
    common_mistakes: List[str]

@dataclass
class ToolUsageViolation:
    violation_type: str
    tool_name: str
    description: str
    severity: str
    suggested_fix: str

class MCPToolGuardian:
    """Validates MCP tool usage against claims"""
    
    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.available_tools = self.discover_available_tools()
        self.violation_history = []
    
    def load_config(self, config_path: str) -> Dict:
        """Load MCP tool configuration"""
        default_config = {
            "tool_discovery": {
                "auto_scan": True,
                "mcp_config_paths": [
                    "~/.config/claude-desktop/claude_desktop_config.json",
                    "./mcp_config.json",
                    "./.claude/mcp_tools.json"
                ]
            },
            "validation": {
                "require_tool_usage_for_claims": True,
                "block_fake_tool_claims": True,
                "suggest_missing_tools": True
            }
        }
        
        if config_path and Path(config_path).exists():
            import yaml
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
                self._deep_merge(default_config, user_config)
        
        return default_config
    
    def discover_available_tools(self) -> Dict[str, MCPTool]:
        """Discover all available MCP tools"""
        tools = {}
        
        # Add common MCP tools
        tools.update(self._get_common_mcp_tools())
        
        # Scan configuration files
        for config_path in self.config["tool_discovery"]["mcp_config_paths"]:
            expanded_path = Path(config_path).expanduser()
            if expanded_path.exists():
                tools.update(self._parse_mcp_config(expanded_path))
        
        return tools
    
    def _get_common_mcp_tools(self) -> Dict[str, MCPTool]:
        """Define common MCP tools"""
        return {
            "filesystem": MCPTool(
                name="filesystem",
                description="Read, write, and manage files and directories",
                required_params=["path"],
                optional_params=["encoding", "create_parents"],
                usage_examples=[
                    "Read file: filesystem.read_file(path='src/app/page.tsx')",
                    "Write file: filesystem.write_file(path='output.txt', content='data')"
                ],
                common_mistakes=[
                    "Claiming to modify files without using filesystem tool",
                    "Reading files with generic descriptions instead of actual content"
                ]
            ),
            "web_search": MCPTool(
                name="web_search",
                description="Search the web for current information",
                required_params=["query"],
                optional_params=["num_results"],
                usage_examples=[
                    "web_search.search(query='Next.js 14 features')"
                ],
                common_mistakes=[
                    "Claiming to search without using the tool",
                    "Providing outdated information when search tool is available"
                ]
            ),
            "ken_you_remember": MCPTool(
                name="ken_you_remember",
                description="Store and retrieve persistent memory",
                required_params=["content"],
                optional_params=["tags", "context"],
                usage_examples=[
                    "ken_you_remember.remember(content='User prefers React hooks')"
                ],
                common_mistakes=[
                    "Forgetting user preferences when memory tool is available"
                ]
            )
        }
    
    def validate_tool_usage(self, claude_response: str, user_request: str) -> Dict[str, Any]:
        """Validate Claude's tool usage against claims"""
        violations = []
        
        # Extract tool usage claims
        tool_claims = self._extract_tool_claims(claude_response)
        actual_tool_usage = self._extract_actual_tool_usage(claude_response)
        
        # Check for claimed but not used tools
        violations.extend(self._check_fake_tool_claims(tool_claims, actual_tool_usage))
        
        # Check for missing tool usage when needed
        violations.extend(self._check_missing_tool_usage(user_request, claude_response, actual_tool_usage))
        
        # Check for incorrect tool usage
        violations.extend(self._check_incorrect_tool_usage(actual_tool_usage))
        
        return {
            "valid": len(violations) == 0,
            "violations": [violation.__dict__ for violation in violations],
            "tool_claims": tool_claims,
            "actual_usage": list(actual_tool_usage),
            "available_tools": list(self.available_tools.keys())
        }
    
    def _extract_tool_claims(self, response: str) -> List[str]:
        """Extract claims about tool usage"""
        claims = []
        
        patterns = [
            r"I'll (?:use|run|execute|search|check|read|write) (\w+)",
            r"(?:Using|Running|Executing) (\w+)",
            r"Let me (?:search|check|read|write|run) (?:with |using )?(\w+)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            claims.extend(matches)
        
        return claims
    
    def _extract_actual_tool_usage(self, response: str) -> Set[str]:
        """Extract actual tool usage from function calls"""
        actual_usage = set()
        
        # Look for function call blocks
        function_blocks = re.findall(r'<function_calls>.*?</function_calls>', response, re.DOTALL)
        
        for block in function_blocks:
            # Extract tool names from invoke blocks
            tool_names = re.findall(r'<invoke name="([^"]+)">', block)
            actual_usage.update(tool_names)
        
        return actual_usage
    
    def _check_fake_tool_claims(self, claims: List[str], actual_usage: Set[str]) -> List[ToolUsageViolation]:
        """Check for claimed but not used tools"""
        violations = []
        
        for claim in claims:
            if claim.lower() not in [tool.lower() for tool in actual_usage]:
                violations.append(ToolUsageViolation(
                    violation_type="FAKE_TOOL_CLAIM",
                    tool_name=claim,
                    description=f"Claimed to use '{claim}' but no function calls found",
                    severity="error",
                    suggested_fix=f"Actually use the {claim} tool or remove the claim"
                ))
        
        return violations
    
    def _check_missing_tool_usage(self, user_request: str, response: str, actual_usage: Set[str]) -> List[ToolUsageViolation]:
        """Check for missing tool usage when needed"""
        violations = []
        
        # Check if user request suggests tool usage
        if "search" in user_request.lower() and "web_search" not in actual_usage:
            if "web_search" in self.available_tools:
                violations.append(ToolUsageViolation(
                    violation_type="MISSING_TOOL_USAGE",
                    tool_name="web_search",
                    description="User requested search but web_search tool not used",
                    severity="warning",
                    suggested_fix="Use web_search tool for current information"
                ))
        
        # Check for file operations without filesystem tool
        file_operations = re.findall(r"(?:read|write|modify|create|update) .+\.(?:js|ts|tsx|jsx|py|css|html)", response, re.IGNORECASE)
        if file_operations and "filesystem" not in actual_usage:
            violations.append(ToolUsageViolation(
                violation_type="MISSING_FILESYSTEM_USAGE",
                tool_name="filesystem",
                description="Claims file operations but filesystem tool not used",
                severity="error",
                suggested_fix="Use filesystem tool for file operations"
            ))
        
        return violations
    
    def _check_incorrect_tool_usage(self, actual_usage: Set[str]) -> List[ToolUsageViolation]:
        """Check for incorrect tool usage patterns"""
        violations = []
        
        # This would check for improper parameter usage, etc.
        # For now, just validate that used tools are available
        
        for tool_name in actual_usage:
            if tool_name not in self.available_tools:
                violations.append(ToolUsageViolation(
                    violation_type="UNKNOWN_TOOL",
                    tool_name=tool_name,
                    description=f"Used unknown tool '{tool_name}'",
                    severity="warning",
                    suggested_fix=f"Verify tool '{tool_name}' is correctly configured"
                ))
        
        return violations
    
    def _parse_mcp_config(self, config_path: Path) -> Dict[str, MCPTool]:
        """Parse MCP configuration file"""
        tools = {}
        
        try:
            with open(config_path) as f:
                config = json.load(f)
            
            # Parse Claude Desktop config format
            if "mcpServers" in config:
                for server_name, server_config in config["mcpServers"].items():
                    # Extract basic server info as tool
                    tools[server_name] = MCPTool(
                        name=server_name,
                        description=server_config.get("description", f"MCP Server: {server_name}"),
                        required_params=[],
                        optional_params=[],
                        usage_examples=[],
                        common_mistakes=[]
                    )
        except Exception as e:
            print(f"Warning: Could not parse MCP config {config_path}: {e}")
        
        return tools
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

def main():
    """CLI interface for MCP tool guardian"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python tool_guardian.py <claude_response_file> <user_request>")
        return
    
    with open(sys.argv[1]) as f:
        claude_response = f.read()
    
    user_request = sys.argv[2]
    
    guardian = MCPToolGuardian()
    result = guardian.validate_tool_usage(claude_response, user_request)
    
    print("🔧 MCP TOOL VALIDATION")
    print("=" * 30)
    print(f"Valid: {'✅' if result['valid'] else '❌'}")
    print(f"Tool Claims: {result['tool_claims']}")
    print(f"Actual Usage: {result['actual_usage']}")
    
    if result['violations']:
        print("\n🚨 VIOLATIONS:")
        for violation in result['violations']:
            print(f"  - {violation['violation_type']}: {violation['description']}")
            print(f"    Fix: {violation['suggested_fix']}")

if __name__ == "__main__":
    main()
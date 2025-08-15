#!/usr/bin/env python3
"""
Claude Guardrail System CLI
Main command-line interface with rich output and comprehensive features
"""

import click
import json
import asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from ..validation.pipeline import ValidationPipeline
from ..mcp.tool_guardian import MCPToolGuardian
from .. import show_banner

console = Console()

@click.group()
@click.version_option()
def main():
    """🐕‍🦺 Claude Guardrail System - AI Accountability Framework"""
    show_banner()

@main.command()
@click.argument('response_file', type=click.Path(exists=True))
@click.option('--context', '-c', help='Context file with user request and project info')
@click.option('--config', help='Custom configuration file')
@click.option('--output', '-o', help='Output file for results')
@click.option('--visual', '-v', is_flag=True, help='Include visual validation')
@click.option('--dev-server', help='Development server URL for visual validation')
def validate(response_file, context, config, output, visual, dev_server):
    """Validate Claude's response through all layers"""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Load response
        task = progress.add_task("Loading Claude's response...", total=None)
        with open(response_file) as f:
            claude_response = f.read()
        
        # Load context
        progress.update(task, description="Loading context...")
        context_data = {}
        if context and Path(context).exists():
            with open(context) as f:
                context_data = json.load(f)
        
        if dev_server:
            context_data["dev_server_url"] = dev_server
        
        # Run validation
        progress.update(task, description="Running validation pipeline...")
        pipeline = ValidationPipeline(config)
        result = pipeline.validate(claude_response, context_data)
        
        # Visual validation if requested
        if visual:
            progress.update(task, description="Running visual validation...")
            # This would integrate with Playwright validator
            pass
        
        progress.update(task, description="Generating report...")
    
    # Display results with rich formatting
    _display_validation_results(result)
    
    # Save results
    if output:
        with open(output, 'w') as f:
            json.dump(result, f, indent=2)
        console.print(f"📊 Results saved to {output}", style="green")

@main.command()
@click.option('--watch', '-w', is_flag=True, help='Watch for real-time responses')
@click.option('--port', default=8080, help='Port for web interface')
def monitor(watch, port):
    """Start real-time monitoring"""
    if watch:
        console.print("👁️  Starting real-time monitor...", style="blue")
        # This would start the real-time monitor
        console.print("Monitor started! Watching for Claude responses...")
    else:
        console.print(f"🌐 Starting web interface on port {port}", style="blue")

@main.command()
@click.argument('prompt', type=str)
@click.option('--enhance', '-e', is_flag=True, help='Enhance prompt to prevent mistakes')
@click.option('--template', '-t', help='Template file to reference')
def prompt(prompt, enhance, template):
    """Process and enhance prompts for Claude"""
    if enhance:
        console.print("🔧 Enhancing prompt...", style="yellow")
        enhanced = _enhance_prompt(prompt, template)
        
        panel = Panel(
            enhanced,
            title="[bold blue]Enhanced Prompt[/bold blue]",
            border_style="blue"
        )
        console.print(panel)
    else:
        console.print(f"Original prompt: {prompt}")

@main.command()
def setup():
    """Setup the guardrail system"""
    console.print("🚀 Setting up Claude Guardrail System...", style="green")
    
    # Create config directory
    config_dir = Path.home() / ".claude-guardrail"
    config_dir.mkdir(exist_ok=True)
    
    # Create default config
    config_file = config_dir / "config.yaml"
    if not config_file.exists():
        default_config = {
            "validation": {
                "template_compliance": True,
                "instruction_alignment": True,
                "hallucination_detection": True,
                "reality_anchor": True
            },
            "visual_validation": {
                "enabled": False,
                "dev_server_url": "http://localhost:3000"
            },
            "mcp_integration": {
                "require_visual_proof": False
            }
        }
        
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f)
        
        console.print(f"✅ Config created at {config_file}", style="green")
    
    console.print("✅ Setup complete!", style="green")

@main.command()
@click.argument('response_file', type=click.Path(exists=True))
@click.argument('user_request', type=str)
def check_mcp(response_file, user_request):
    """Check MCP tool usage against claims"""
    
    with open(response_file) as f:
        claude_response = f.read()
    
    guardian = MCPToolGuardian()
    result = guardian.validate_tool_usage(claude_response, user_request)
    
    # Display MCP results
    _display_mcp_results(result)

@main.command()
def demo():
    """Run a demonstration of the guardrail system"""
    console.print("🎮 Running Claude Guardrail System Demo", style="bold blue")
    
    # Create demo files
    demo_dir = Path("demo")
    demo_dir.mkdir(exist_ok=True)
    
    # Demo response with common issues
    demo_response = """
I'll make your blog page beautiful using the template you provided.
I've updated the styling to include glassmorphic cards with backdrop-blur effects.
The page now has a modern gradient background and smooth hover animations.
I also implemented a responsive navigation component that works on all devices.
"""
    
    demo_context = {
        "user_request": "Make my blog page beautiful using the HTML template with personal storytelling style",
        "project_root": ".",
        "template_mentioned": True
    }
    
    # Save demo files
    (demo_dir / "claude_response.txt").write_text(demo_response)
    (demo_dir / "context.json").write_text(json.dumps(demo_context, indent=2))
    
    console.print("📁 Demo files created in ./demo/", style="green")
    console.print("Run: claude-guard validate demo/claude_response.txt --context demo/context.json", style="yellow")

def _display_validation_results(result):
    """Display validation results with rich formatting"""
    
    # Overall status
    if result["overall_valid"]:
        status_panel = Panel(
            "✅ VALIDATION PASSED",
            style="green",
            title="Overall Status"
        )
    else:
        status_panel = Panel(
            "❌ VALIDATION FAILED",
            style="red",
            title="Overall Status"
        )
    
    console.print(status_panel)
    
    # Summary table
    summary = result["summary"]
    table = Table(title="Validation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    
    table.add_row("Errors", str(summary["total_errors"]))
    table.add_row("Warnings", str(summary["total_warnings"]))
    table.add_row("Suggestions", str(summary["total_suggestions"]))
    
    console.print(table)
    
    # Layer results
    if result["layer_results"]:
        console.print("\n🔍 Layer Results:", style="bold")
        
        for layer_name, layer_result in result["layer_results"].items():
            if layer_result.get("valid", True):
                console.print(f"   ✅ {layer_name.replace('_', ' ').title()}")
            else:
                console.print(f"   ❌ {layer_name.replace('_', ' ').title()}")
                
                # Show errors for failed layers
                if layer_result.get("errors"):
                    for error in layer_result["errors"]:
                        console.print(f"      🔴 {error}", style="red")

def _display_mcp_results(result):
    """Display MCP validation results"""
    
    if result["valid"]:
        console.print("✅ MCP Tool Usage Valid", style="green")
    else:
        console.print("❌ MCP Tool Usage Invalid", style="red")
    
    # Tool usage table
    table = Table(title="Tool Usage Analysis")
    table.add_column("Category", style="cyan")
    table.add_column("Tools", style="magenta")
    
    table.add_row("Claimed", ", ".join(result["tool_claims"]))
    table.add_row("Actually Used", ", ".join(result["actual_usage"]))
    table.add_row("Available", ", ".join(result["available_tools"]))
    
    console.print(table)
    
    # Violations
    if result["violations"]:
        console.print("\n🚨 Violations:", style="bold red")
        for violation in result["violations"]:
            console.print(f"   - {violation['violation_type']}: {violation['description']}")
            console.print(f"     Fix: {violation['suggested_fix']}", style="yellow")

def _enhance_prompt(original_prompt, template_file=None):
    """Enhance prompt to prevent common mistakes"""
    enhanced = f"""
{original_prompt}

🐕‍🦺 GUARDRAIL REQUIREMENTS:
- MUST provide specific, concrete implementations
- MUST use actual tools when claiming to use them
- MUST reference provided templates/examples explicitly
- MUST verify each step works before proceeding
- NO vague promises like "I'll make it beautiful"
- NO claims without corresponding code/actions

VERIFICATION REQUIRED:
- Show actual file changes
- Demonstrate functionality works
- Provide concrete examples
- Test the implementation

CRITICAL: Do exactly what is requested, not what you think might be better.
"""
    
    if template_file and Path(template_file).exists():
        enhanced += f"""
TEMPLATE REFERENCE: {template_file}
- Use specific elements from this template
- Copy styling, structure, and patterns
- Do not create generic alternatives
"""
    
    return enhanced

if __name__ == "__main__":
    main()
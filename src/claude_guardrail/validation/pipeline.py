#!/usr/bin/env python3
"""
Comprehensive Validation Pipeline
Multi-layer validation with template compliance, hallucination detection, and reality anchoring
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import difflib

@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    blocking: bool = False
    evidence: Dict[str, Any] = None

    def __post_init__(self):
        if self.evidence is None:
            self.evidence = {}

class ValidationPipeline:
    """Comprehensive validation pipeline for Claude responses"""
    
    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.violation_history = []
        
    def load_config(self, config_path: str) -> Dict:
        """Load validation configuration"""
        default_config = {
            "layers": {
                "template_compliance": {"enabled": True, "blocking": True},
                "instruction_alignment": {"enabled": True, "blocking": True},
                "hallucination_detection": {"enabled": True, "blocking": True},
                "reality_anchor": {"enabled": True, "blocking": False}
            },
            "evidence_collection": {
                "save_screenshots": True,
                "save_reports": True,
                "retention_days": 30
            },
            "strict_mode": False
        }
        
        if config_path and Path(config_path).exists():
            import yaml
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
                self._deep_merge(default_config, user_config)
        
        return default_config
    
    def validate(self, claude_response: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run comprehensive validation pipeline"""
        if context is None:
            context = {}
            
        results = {}
        all_errors = []
        all_warnings = []
        all_suggestions = []
        blocking_failures = []
        
        # Template Compliance Validation
        if self.config["layers"]["template_compliance"]["enabled"]:
            template_result = self._validate_template_compliance(claude_response, context)
            results["template_compliance"] = asdict(template_result)
            all_errors.extend(template_result.errors)
            all_warnings.extend(template_result.warnings)
            all_suggestions.extend(template_result.suggestions)
            
            if template_result.blocking and not template_result.valid:
                blocking_failures.append("template_compliance")
        
        # Instruction Alignment Validation
        if self.config["layers"]["instruction_alignment"]["enabled"]:
            alignment_result = self._validate_instruction_alignment(claude_response, context)
            results["instruction_alignment"] = asdict(alignment_result)
            all_errors.extend(alignment_result.errors)
            all_warnings.extend(alignment_result.warnings)
            all_suggestions.extend(alignment_result.suggestions)
            
            if alignment_result.blocking and not alignment_result.valid:
                blocking_failures.append("instruction_alignment")
        
        # Hallucination Detection
        if self.config["layers"]["hallucination_detection"]["enabled"]:
            hallucination_result = self._validate_hallucination(claude_response, context)
            results["hallucination_detection"] = asdict(hallucination_result)
            all_errors.extend(hallucination_result.errors)
            all_warnings.extend(hallucination_result.warnings)
            all_suggestions.extend(hallucination_result.suggestions)
            
            if hallucination_result.blocking and not hallucination_result.valid:
                blocking_failures.append("hallucination_detection")
        
        # Reality Anchor Validation
        if self.config["layers"]["reality_anchor"]["enabled"]:
            reality_result = self._validate_reality_anchor(claude_response, context)
            results["reality_anchor"] = asdict(reality_result)
            all_errors.extend(reality_result.errors)
            all_warnings.extend(reality_result.warnings)
            all_suggestions.extend(reality_result.suggestions)
            
            if reality_result.blocking and not reality_result.valid:
                blocking_failures.append("reality_anchor")
        
        # Compile final result
        overall_valid = len(all_errors) == 0 and len(blocking_failures) == 0
        
        final_result = {
            "timestamp": datetime.now().isoformat(),
            "overall_valid": overall_valid,
            "blocking_failures": blocking_failures,
            "summary": {
                "total_errors": len(all_errors),
                "total_warnings": len(all_warnings),
                "total_suggestions": len(all_suggestions)
            },
            "errors": all_errors,
            "warnings": all_warnings,
            "suggestions": all_suggestions,
            "layer_results": results,
            "config_used": self.config
        }
        
        # Store violation history
        self.violation_history.append(final_result)
        
        return final_result
    
    def _validate_template_compliance(self, claude_response: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate compliance with provided templates"""
        errors = []
        warnings = []
        suggestions = []
        
        user_request = context.get("user_request", "")
        template_mentioned = "template" in user_request.lower()
        
        if template_mentioned:
            template_referenced = any(phrase in claude_response.lower() for phrase in [
                "template", "provided example", "your example", "following the"
            ])
            
            if not template_referenced:
                errors.append("User mentioned template but Claude didn't reference it")
                suggestions.append("Explicitly reference the provided template in your response")
            
            # Check for template deviation indicators
            deviation_patterns = [
                r"(?:instead|rather than|different from)",
                r"(?:better|improved) (?:version|approach)",
                r"(?:custom|unique|original) (?:design|implementation)"
            ]
            
            for pattern in deviation_patterns:
                if re.search(pattern, claude_response, re.IGNORECASE):
                    warnings.append(f"Potential template deviation detected: {pattern}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, suggestions, blocking=True)
    
    def _validate_instruction_alignment(self, claude_response: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate alignment with specific user instructions"""
        errors = []
        warnings = []
        suggestions = []
        
        user_request = context.get("user_request", "")
        
        # Critical instruction words that must be addressed
        critical_words = ["exactly", "specifically", "must", "required", "essential"]
        for word in critical_words:
            if word.lower() in user_request.lower() and word.lower() not in claude_response.lower():
                errors.append(f"Critical instruction word '{word}' not addressed in response")
        
        # Check for vague responses to specific requests
        if any(specific in user_request.lower() for specific in ["exactly", "specifically"]):
            vague_responses = [
                "I'll make it better", "I'll improve", "I'll enhance",
                "I'll create a nice", "I'll add some styling"
            ]
            
            for vague in vague_responses:
                if vague.lower() in claude_response.lower():
                    errors.append(f"Vague response '{vague}' to specific instruction")
                    suggestions.append("Provide specific implementation details instead of generic promises")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, suggestions, blocking=True)
    
    def _validate_hallucination(self, claude_response: str, context: Dict[str, Any]) -> ValidationResult:
        """Detect hallucinated or false claims"""
        errors = []
        warnings = []
        suggestions = []
        
        # Check for implementation claims without evidence
        implementation_claims = re.findall(
            r"I (?:created|implemented|added|built|made) (.+)",
            claude_response, re.IGNORECASE
        )
        
        has_function_calls = "<function_calls>" in claude_response
        has_code_blocks = "```" in claude_response
        has_evidence = has_function_calls or has_code_blocks
        
        if implementation_claims and not has_evidence:
            for claim in implementation_claims:
                errors.append(f"Claims to have implemented '{claim}' but no code/tools shown")
                suggestions.append("Show actual implementation with code blocks or function calls")
        
        # Check for file modification claims
        file_claims = re.findall(
            r"(?:updated|modified|changed) (.+\.(?:tsx?|jsx?|css|html|py|js))",
            claude_response, re.IGNORECASE
        )
        
        if file_claims and not has_evidence:
            warnings.append("Claims file modifications but no evidence provided")
            suggestions.append("Show actual file changes or use file modification tools")
        
        # Check for feature claims without verification
        feature_claims = re.findall(
            r"(?:The|This) (.+) (?:now|will) (?:work|function|display|show) (.+)",
            claude_response, re.IGNORECASE
        )
        
        if feature_claims and "test" not in claude_response.lower() and "verify" not in claude_response.lower():
            warnings.append("Claims about functionality without verification steps")
            suggestions.append("Include testing or verification steps for claimed functionality")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, suggestions, blocking=True)
    
    def _validate_reality_anchor(self, claude_response: str, context: Dict[str, Any]) -> ValidationResult:
        """Ground responses in actual project reality"""
        errors = []
        warnings = []
        suggestions = []
        
        project_root = context.get("project_root", ".")
        
        # Check file references against actual files
        file_references = re.findall(r'([^/\s]+\.(?:tsx?|jsx?|css|html|py|js|json))', claude_response)
        
        if Path(project_root).exists():
            project_files = []
            for root, dirs, files in os.walk(project_root):
                # Skip common build/dependency directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'dist', 'build']]
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), project_root)
                    project_files.append(rel_path)
            
            for file_ref in set(file_references):
                if file_ref not in project_files:
                    # Find similar files
                    similar_files = difflib.get_close_matches(
                        file_ref, project_files, n=3, cutoff=0.6
                    )
                    
                    if similar_files:
                        warnings.append(f"References '{file_ref}' - did you mean: {', '.join(similar_files)}?")
                    else:
                        warnings.append(f"References potentially non-existent file: {file_ref}")
        
        # Check for dependency/framework consistency
        package_json_path = Path(project_root) / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path) as f:
                    package_data = json.load(f)
                    dependencies = package_data.get("dependencies", {})
                    
                    # Check framework alignment
                    if "next" in dependencies and "next" not in claude_response.lower():
                        if any(term in claude_response.lower() for term in ["react", "component", "jsx"]):
                            suggestions.append("Consider using Next.js specific patterns for this project")
                    
                    if "react" in dependencies and "react" not in claude_response.lower():
                        if any(term in claude_response.lower() for term in ["component", "jsx", "hook"]):
                            suggestions.append("Consider using React patterns for this project")
                            
            except Exception as e:
                warnings.append(f"Could not parse package.json: {e}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, suggestions, blocking=False)
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def generate_feedback(self, validation_result: Dict[str, Any]) -> str:
        """Generate human-readable feedback"""
        feedback = []
        
        if validation_result["overall_valid"]:
            feedback.append("✅ VALIDATION PASSED!")
        else:
            feedback.append("❌ VALIDATION FAILED!")
            
            if validation_result["blocking_failures"]:
                feedback.append(f"🚫 Blocking failures: {', '.join(validation_result['blocking_failures'])}")
        
        # Summary
        summary = validation_result["summary"]
        feedback.append(f"\n📊 SUMMARY:")
        feedback.append(f"   Errors: {summary['total_errors']}")
        feedback.append(f"   Warnings: {summary['total_warnings']}")
        feedback.append(f"   Suggestions: {summary['total_suggestions']}")
        
        # Errors
        if validation_result["errors"]:
            feedback.append("\n🔴 ERRORS:")
            for error in validation_result["errors"]:
                feedback.append(f"  - {error}")
        
        # Warnings
        if validation_result["warnings"]:
            feedback.append("\n🟡 WARNINGS:")
            for warning in validation_result["warnings"]:
                feedback.append(f"  - {warning}")
        
        # Suggestions
        if validation_result["suggestions"]:
            feedback.append("\n💡 SUGGESTIONS:")
            for suggestion in validation_result["suggestions"]:
                feedback.append(f"  - {suggestion}")
        
        return "\n".join(feedback)

def main():
    """CLI interface for validation pipeline"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <claude_response_file> [context_file]")
        return
    
    response_file = sys.argv[1]
    context_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Load Claude's response
    with open(response_file) as f:
        claude_response = f.read()
    
    # Load context
    context = {}
    if context_file and Path(context_file).exists():
        with open(context_file) as f:
            context = json.load(f)
    
    # Run validation
    pipeline = ValidationPipeline()
    result = pipeline.validate(claude_response, context)
    
    # Display feedback
    feedback = pipeline.generate_feedback(result)
    print(feedback)

if __name__ == "__main__":
    main()
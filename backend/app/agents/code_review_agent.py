"""Advanced code review agent with specialized analysis capabilities."""

import ast
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from ..services.groq_service import create_groq_completion


class CodeReviewAgent:
    """Advanced AI agent for comprehensive code review and analysis."""
    
    def __init__(self):
        self.model = "llama-3.3-70b-versatile"
        self.security_patterns = self._load_security_patterns()
        self.performance_patterns = self._load_performance_patterns()
        
    async def comprehensive_review(
        self,
        code: str,
        language: str,
        focus_areas: List[str] = None,
        severity_filter: str = "all"
    ) -> Dict[str, Any]:
        """Perform comprehensive code review with multiple analysis layers."""
        
        if focus_areas is None:
            focus_areas = ["security", "performance", "readability", "maintainability", "bugs"]
        
        # Layer 1: Static analysis
        static_issues = await self._static_analysis(code, language)
        
        # Layer 2: AI-powered review
        ai_review = await self._ai_review(code, language, focus_areas)
        
        # Layer 3: Security-specific analysis
        security_issues = await self._security_analysis(code, language) if "security" in focus_areas else []
        
        # Layer 4: Performance analysis
        performance_issues = await self._performance_analysis(code, language) if "performance" in focus_areas else []
        
        # Combine and deduplicate issues
        all_issues = self._merge_issues(static_issues, ai_review.get("issues", []), security_issues, performance_issues)
        
        # Filter by severity
        filtered_issues = self._filter_by_severity(all_issues, severity_filter)
        
        # Generate overall assessment
        overall_score = self._calculate_overall_score(filtered_issues, len(code.split('\n')))
        
        return {
            "review_id": f"review_{datetime.utcnow().timestamp()}",
            "overall_score": overall_score,
            "summary": ai_review.get("summary", ""),
            "issues": filtered_issues,
            "suggestions": ai_review.get("suggestions", []),
            "strengths": ai_review.get("strengths", []),
            "metrics": {
                "total_issues": len(filtered_issues),
                "critical_issues": len([i for i in filtered_issues if i["severity"] == "critical"]),
                "high_issues": len([i for i in filtered_issues if i["severity"] == "high"]),
                "medium_issues": len([i for i in filtered_issues if i["severity"] == "medium"]),
                "low_issues": len([i for i in filtered_issues if i["severity"] == "low"]),
                "lines_of_code": len(code.split('\n')),
                "cyclomatic_complexity": self._calculate_complexity(code, language)
            },
            "metadata": {
                "language": language,
                "focus_areas": focus_areas,
                "severity_filter": severity_filter,
                "reviewed_at": datetime.utcnow().isoformat(),
                "agent_version": "1.0.0"
            }
        }
    
    async def security_audit(self, code: str, language: str) -> Dict[str, Any]:
        """Specialized security audit of code."""
        
        security_prompt = f"""You are a cybersecurity expert conducting a thorough security audit of {language} code.

Analyze the following code for security vulnerabilities and provide a detailed security assessment:

FOCUS ON:
1. Injection vulnerabilities (SQL, NoSQL, Command, LDAP, etc.)
2. Authentication and authorization flaws
3. Sensitive data exposure
4. Security misconfiguration
5. Broken access control
6. Cross-site scripting (XSS) if web-related
7. Insecure deserialization
8. Using components with known vulnerabilities
9. Insufficient logging and monitoring
10. Server-side request forgery (SSRF)

For each vulnerability found, provide:
- Severity level (Critical/High/Medium/Low)
- CWE (Common Weakness Enumeration) ID if applicable
- Detailed description
- Attack scenario
- Remediation steps
- Code example of the fix

Return your analysis in JSON format:
{{
    "security_score": <0-100>,
    "vulnerabilities": [
        {{
            "type": "vulnerability_type",
            "severity": "critical|high|medium|low",
            "cwe_id": "CWE-XXX",
            "line": <line_number>,
            "description": "Detailed description",
            "attack_scenario": "How this could be exploited",
            "remediation": "How to fix this",
            "code_example": "Fixed code example"
        }}
    ],
    "security_recommendations": ["General security recommendations"],
    "compliance_notes": "Notes about compliance standards"
}}"""
        
        messages = [
            {"role": "system", "content": security_prompt},
            {"role": "user", "content": f"```{language}\n{code}\n```"}
        ]
        
        try:
            response = await create_groq_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=3000
            )
            
            content = response["choices"][0]["message"]["content"]
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"security_score": 50, "vulnerabilities": [], "error": "Failed to parse security analysis"}
                
        except Exception as e:
            return {"error": f"Security audit failed: {str(e)}"}
    
    async def performance_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code for performance issues and optimization opportunities."""
        
        performance_prompt = f"""You are a performance optimization expert analyzing {language} code.

Analyze the following code for performance issues and optimization opportunities:

ANALYZE FOR:
1. Time complexity issues
2. Space complexity problems
3. Inefficient algorithms
4. Memory leaks
5. Unnecessary computations
6. Database query optimization (if applicable)
7. Caching opportunities
8. Parallel processing potential
9. I/O optimization
10. Resource management

For each issue, provide:
- Performance impact (Critical/High/Medium/Low)
- Current complexity (if measurable)
- Optimized complexity
- Expected performance gain
- Optimization technique
- Code example of improvement

Return analysis in JSON format:
{{
    "performance_score": <0-100>,
    "issues": [
        {{
            "type": "performance_issue_type",
            "impact": "critical|high|medium|low",
            "line": <line_number>,
            "current_complexity": "O(n²)",
            "optimized_complexity": "O(n log n)",
            "performance_gain": "estimated percentage",
            "description": "Detailed description",
            "optimization": "How to optimize",
            "code_example": "Optimized code"
        }}
    ],
    "optimization_opportunities": ["List of optimization suggestions"],
    "bottlenecks": ["Identified performance bottlenecks"]
}}"""
        
        messages = [
            {"role": "system", "content": performance_prompt},
            {"role": "user", "content": f"```{language}\n{code}\n```"}
        ]
        
        try:
            response = await create_groq_completion(
                messages=messages,
                temperature=0.2,
                max_tokens=3000
            )
            
            content = response["choices"][0]["message"]["content"]
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"performance_score": 50, "issues": [], "error": "Failed to parse performance analysis"}
                
        except Exception as e:
            return {"error": f"Performance analysis failed: {str(e)}"}
    
    async def code_quality_assessment(self, code: str, language: str) -> Dict[str, Any]:
        """Assess overall code quality including maintainability and readability."""
        
        quality_prompt = f"""You are a senior software architect assessing {language} code quality.

Evaluate the following code for:

QUALITY METRICS:
1. Readability and clarity
2. Maintainability
3. Code organization and structure
4. Naming conventions
5. Documentation and comments
6. Error handling
7. Code reusability
8. SOLID principles adherence (if OOP)
9. Design patterns usage
10. Test coverage potential

Provide detailed assessment with specific examples and improvement suggestions.

Return assessment in JSON format:
{{
    "quality_score": <0-100>,
    "readability_score": <0-100>,
    "maintainability_score": <0-100>,
    "structure_score": <0-100>,
    "documentation_score": <0-100>,
    "areas_for_improvement": [
        {{
            "category": "readability|maintainability|structure|documentation",
            "issue": "Specific issue description",
            "suggestion": "How to improve",
            "priority": "high|medium|low",
            "code_example": "Example of improvement"
        }}
    ],
    "strengths": ["Code strengths"],
    "refactoring_suggestions": ["Major refactoring suggestions"],
    "best_practices": ["Best practices recommendations"]
}}"""
        
        messages = [
            {"role": "system", "content": quality_prompt},
            {"role": "user", "content": f"```{language}\n{code}\n```"}
        ]
        
        try:
            response = await create_groq_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=3000
            )
            
            content = response["choices"][0]["message"]["content"]
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"quality_score": 50, "areas_for_improvement": [], "error": "Failed to parse quality assessment"}
                
        except Exception as e:
            return {"error": f"Code quality assessment failed: {str(e)}"}
    
    async def _static_analysis(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Perform static analysis to detect common issues."""
        issues = []
        
        if language == "python":
            issues.extend(self._python_static_analysis(code))
        elif language == "javascript":
            issues.extend(self._javascript_static_analysis(code))
        
        # Language-agnostic checks
        issues.extend(self._generic_static_analysis(code))
        
        return issues
    
    def _python_static_analysis(self, code: str) -> List[Dict[str, Any]]:
        """Python-specific static analysis."""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            # Check for unused imports
            # Check for undefined variables
            # Check for unreachable code
            # etc.
            
        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "severity": "critical",
                "line": e.lineno,
                "description": f"Syntax error: {e.msg}",
                "suggestion": "Fix syntax error"
            })
        
        return issues
    
    def _javascript_static_analysis(self, code: str) -> List[Dict[str, Any]]:
        """JavaScript-specific static analysis."""
        issues = []
        
        # Check for common JavaScript issues
        if "eval(" in code:
            issues.append({
                "type": "security",
                "severity": "high",
                "line": self._find_line_number(code, "eval("),
                "description": "Use of eval() is dangerous and should be avoided",
                "suggestion": "Replace eval() with safer alternatives"
            })
        
        return issues
    
    def _generic_static_analysis(self, code: str) -> List[Dict[str, Any]]:
        """Language-agnostic static analysis."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for hardcoded passwords/secrets
            if re.search(r'(password|secret|key)\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                issues.append({
                    "type": "security",
                    "severity": "high",
                    "line": i,
                    "description": "Hardcoded credentials detected",
                    "suggestion": "Use environment variables or secure configuration"
                })
            
            # Check for TODO/FIXME comments
            if re.search(r'(TODO|FIXME|HACK)', line, re.IGNORECASE):
                issues.append({
                    "type": "maintainability",
                    "severity": "low",
                    "line": i,
                    "description": "Unresolved TODO/FIXME comment",
                    "suggestion": "Address the TODO/FIXME comment"
                })
        
        return issues
    
    async def _ai_review(self, code: str, language: str, focus_areas: List[str]) -> Dict[str, Any]:
        """AI-powered comprehensive code review."""
        
        system_prompt = f"""You are an expert {language} code reviewer. Analyze the provided code focusing on: {', '.join(focus_areas)}.

Provide a comprehensive review in JSON format:
{{
    "summary": "Brief overall assessment",
    "issues": [
        {{
            "type": "bug|security|performance|readability|maintainability",
            "severity": "critical|high|medium|low",
            "line": <line_number>,
            "description": "Issue description",
            "suggestion": "How to fix it",
            "code_example": "Fixed code example if applicable"
        }}
    ],
    "suggestions": [
        {{
            "type": "improvement|optimization|refactor",
            "description": "Suggestion description",
            "benefit": "Expected benefit",
            "priority": "high|medium|low"
        }}
    ],
    "strengths": ["Positive aspects of the code"]
}}

Be thorough but constructive in your feedback."""
        
        user_prompt = f"""Review this {language} code:

```{language}
{code}
```

Focus areas: {', '.join(focus_areas)}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await create_groq_completion(
                messages=messages,
                temperature=0.2,
                max_tokens=3000
            )
            
            content = response["choices"][0]["message"]["content"]
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"summary": content, "issues": [], "suggestions": [], "strengths": []}
                
        except Exception as e:
            return {"summary": f"AI review failed: {str(e)}", "issues": [], "suggestions": [], "strengths": []}
    
    async def _security_analysis(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Specialized security analysis."""
        issues = []
        
        # Check against security patterns
        for pattern in self.security_patterns.get(language, []):
            if re.search(pattern["regex"], code, re.IGNORECASE | re.MULTILINE):
                issues.append({
                    "type": "security",
                    "severity": pattern["severity"],
                    "line": self._find_line_number(code, pattern["regex"]),
                    "description": pattern["description"],
                    "suggestion": pattern["suggestion"]
                })
        
        return issues
    
    async def _performance_analysis(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Specialized performance analysis."""
        issues = []
        
        # Check against performance patterns
        for pattern in self.performance_patterns.get(language, []):
            if re.search(pattern["regex"], code, re.IGNORECASE | re.MULTILINE):
                issues.append({
                    "type": "performance",
                    "severity": pattern["severity"],
                    "line": self._find_line_number(code, pattern["regex"]),
                    "description": pattern["description"],
                    "suggestion": pattern["suggestion"]
                })
        
        return issues
    
    def _merge_issues(self, *issue_lists) -> List[Dict[str, Any]]:
        """Merge and deduplicate issues from multiple sources."""
        all_issues = []
        seen_issues = set()
        
        for issues in issue_lists:
            for issue in issues:
                issue_key = f"{issue.get('type')}_{issue.get('line')}_{issue.get('description', '')[:50]}"
                if issue_key not in seen_issues:
                    seen_issues.add(issue_key)
                    all_issues.append(issue)
        
        return sorted(all_issues, key=lambda x: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity", "low"), 3),
            x.get("line", 0)
        ))
    
    def _filter_by_severity(self, issues: List[Dict[str, Any]], severity_filter: str) -> List[Dict[str, Any]]:
        """Filter issues by minimum severity level."""
        if severity_filter == "all":
            return issues
        
        severity_levels = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        min_level = severity_levels.get(severity_filter, 3)
        
        return [issue for issue in issues 
                if severity_levels.get(issue.get("severity", "low"), 3) <= min_level]
    
    def _calculate_overall_score(self, issues: List[Dict[str, Any]], lines_of_code: int) -> int:
        """Calculate overall code quality score."""
        if not issues:
            return 95
        
        penalty_weights = {"critical": 20, "high": 10, "medium": 5, "low": 2}
        total_penalty = sum(penalty_weights.get(issue.get("severity", "low"), 2) for issue in issues)
        
        # Normalize by lines of code
        penalty_per_line = total_penalty / max(lines_of_code, 1) * 100
        
        score = max(0, 100 - min(penalty_per_line, 95))
        return int(score)
    
    def _calculate_complexity(self, code: str, language: str) -> int:
        """Calculate cyclomatic complexity."""
        # Simplified complexity calculation
        complexity_keywords = {
            "python": ["if", "elif", "while", "for", "except", "and", "or"],
            "javascript": ["if", "else if", "while", "for", "catch", "&&", "||", "?"],
            "java": ["if", "else if", "while", "for", "catch", "&&", "||", "?"]
        }
        
        keywords = complexity_keywords.get(language, ["if", "while", "for"])
        complexity = 1  # Base complexity
        
        for keyword in keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', code, re.IGNORECASE))
        
        return complexity
    
    def _find_line_number(self, code: str, pattern: str) -> int:
        """Find line number for a given pattern."""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line, re.IGNORECASE):
                return i
        return 1
    
    def _load_security_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load security patterns for different languages."""
        return {
            "python": [
                {
                    "regex": r"eval\s*\(",
                    "severity": "critical",
                    "description": "Use of eval() can lead to code injection",
                    "suggestion": "Use ast.literal_eval() or safer alternatives"
                },
                {
                    "regex": r"pickle\.loads?\s*\(",
                    "severity": "high",
                    "description": "Pickle deserialization can be unsafe",
                    "suggestion": "Use JSON or other safe serialization formats"
                }
            ],
            "javascript": [
                {
                    "regex": r"innerHTML\s*=",
                    "severity": "medium",
                    "description": "innerHTML can lead to XSS vulnerabilities",
                    "suggestion": "Use textContent or properly sanitize input"
                }
            ]
        }
    
    def _load_performance_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load performance patterns for different languages."""
        return {
            "python": [
                {
                    "regex": r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(",
                    "severity": "medium",
                    "description": "Using range(len()) is inefficient",
                    "suggestion": "Use enumerate() or iterate directly"
                }
            ],
            "javascript": [
                {
                    "regex": r"document\.getElementById",
                    "severity": "low",
                    "description": "Frequent DOM queries can impact performance",
                    "suggestion": "Cache DOM elements or use query selectors efficiently"
                }
            ]
        }
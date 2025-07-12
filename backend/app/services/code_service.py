"""Code generation service using Groq llama-3.3-70b-versatile model."""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from .groq_service import create_groq_completion


class CodeGenerationService:
    """Service for AI-powered code generation, review, and optimization."""
    
    def __init__(self):
        self.model = "llama-3.3-70b-versatile"
    
    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        framework: Optional[str] = None,
        complexity: str = "intermediate",
        include_comments: bool = True,
        include_tests: bool = False,
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Generate code based on user prompt."""
        
        # Build comprehensive system prompt
        system_prompt = self._build_code_generation_prompt(
            language, framework, complexity, include_comments, include_tests
        )
        
        # Create user prompt
        user_prompt = f"""
Generate {language} code for the following requirement:

{prompt}

Please provide:
1. Clean, well-structured code
2. Appropriate error handling
3. {"Detailed comments explaining the logic" if include_comments else "Minimal comments"}
4. {"Unit tests for the main functionality" if include_tests else ""}

Follow best practices for {language} development.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            import asyncio
            # Add timeout to prevent hanging
            response = await asyncio.wait_for(
                create_groq_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=0.9
                ),
                timeout=60.0  # 60 second timeout for code generation
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Extract code and explanation
            code, explanation = self._parse_code_response(content, language)
            
            return {
                "id": str(uuid.uuid4()),
                "code": code,
                "explanation": explanation,
                "language": language,
                "created_at": datetime.utcnow().isoformat(),
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                "metadata": {
                    "framework": framework,
                    "complexity": complexity,
                    "include_comments": include_comments,
                    "include_tests": include_tests,
                    "model": self.model
                }
            }
            
        except asyncio.TimeoutError:
            raise Exception("Code generation timeout - request took too long")
        except Exception as e:
            raise Exception(f"Code generation failed: {str(e)}")
    
    async def review_code(
        self,
        code: str,
        language: str,
        focus_areas: List[str] = None,
        severity_level: str = "all"
    ) -> Dict[str, Any]:
        """Review code for issues and improvements."""
        
        if focus_areas is None:
            focus_areas = ["security", "performance", "readability", "maintainability"]
        
        system_prompt = f"""You are an expert {language} code reviewer. Analyze the provided code and provide a comprehensive review focusing on: {', '.join(focus_areas)}.

Provide your review in this JSON format:
{{
    "overall_score": <0-100>,
    "summary": "Brief overall assessment",
    "issues": [
        {{
            "type": "security|performance|readability|maintainability|bug",
            "severity": "critical|high|medium|low",
            "line": <line_number>,
            "description": "Description of the issue",
            "suggestion": "How to fix it"
        }}
    ],
    "suggestions": [
        {{
            "type": "improvement|optimization|refactor",
            "description": "Suggestion description",
            "benefit": "Expected benefit"
        }}
    ],
    "strengths": ["List of good practices found"]
}}

Be thorough but constructive in your feedback."""
        
        user_prompt = f"""Review this {language} code:

```{language}
{code}
```

Focus areas: {', '.join(focus_areas)}
Minimum severity to report: {severity_level}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            import asyncio
            # Add timeout to prevent hanging
            response = await asyncio.wait_for(
                create_groq_completion(
                    messages=messages,
                    temperature=0.2,
                    max_tokens=2048
                ),
                timeout=45.0  # 45 second timeout for code review
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Try to parse JSON response
            try:
                review_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback to text parsing
                review_data = self._parse_review_response(content)
            
            return {
                "id": str(uuid.uuid4()),
                "issues": review_data.get("issues", []),
                "suggestions": review_data.get("suggestions", []),
                "score": review_data.get("overall_score", 0),
                "summary": review_data.get("summary", ""),
                "strengths": review_data.get("strengths", []),
                "metadata": {
                    "language": language,
                    "focus_areas": focus_areas,
                    "severity_level": severity_level,
                    "model": self.model,
                    "reviewed_at": datetime.utcnow().isoformat()
                }
            }
            
        except asyncio.TimeoutError:
            raise Exception("Code review timeout - request took too long")
        except Exception as e:
            raise Exception(f"Code review failed: {str(e)}")
    
    async def optimize_code(
        self,
        code: str,
        language: str,
        optimization_goals: List[str] = None,
        preserve_functionality: bool = True
    ) -> Dict[str, Any]:
        """Optimize code for performance and efficiency."""
        
        if optimization_goals is None:
            optimization_goals = ["performance", "memory_usage", "readability"]
        
        system_prompt = f"""You are an expert {language} developer specializing in code optimization. 
Optimize the provided code focusing on: {', '.join(optimization_goals)}.

{"CRITICAL: Preserve the exact same functionality and behavior." if preserve_functionality else "You may modify functionality if it leads to better optimization."}

Provide your response in this format:
```{language}
[OPTIMIZED CODE HERE]
```

EXPLANATION:
- List specific optimizations made
- Explain performance improvements
- Note any trade-offs
- Estimate performance gain percentage

IMPROVEMENTS:
1. [Improvement 1]: [Description]
2. [Improvement 2]: [Description]
..."""
        
        user_prompt = f"""Optimize this {language} code:

```{language}
{code}
```

Optimization goals: {', '.join(optimization_goals)}
Preserve functionality: {preserve_functionality}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            import asyncio
            # Add timeout to prevent hanging
            response = await asyncio.wait_for(
                create_groq_completion(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=2048
                ),
                timeout=45.0  # 45 second timeout for code optimization
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Parse optimized code and explanation
            optimized_code, explanation, improvements = self._parse_optimization_response(content, language)
            
            return {
                "id": str(uuid.uuid4()),
                "optimized_code": optimized_code,
                "explanation": explanation,
                "improvements": improvements,
                "performance_gain": self._estimate_performance_gain(improvements),
                "metadata": {
                    "language": language,
                    "optimization_goals": optimization_goals,
                    "preserve_functionality": preserve_functionality,
                    "model": self.model,
                    "optimized_at": datetime.utcnow().isoformat()
                }
            }
            
        except asyncio.TimeoutError:
            raise Exception("Code optimization timeout - request took too long")
        except Exception as e:
            raise Exception(f"Code optimization failed: {str(e)}")
    
    async def explain_code(
        self,
        code: str,
        language: str,
        detail_level: str = "intermediate",
        include_examples: bool = True
    ) -> Dict[str, Any]:
        """Explain how code works."""
        
        detail_prompts = {
            "beginner": "Explain in simple terms suitable for programming beginners",
            "intermediate": "Provide a balanced explanation with technical details",
            "advanced": "Give a deep technical analysis suitable for experienced developers"
        }
        
        system_prompt = f"""You are an expert {language} instructor. {detail_prompts.get(detail_level, detail_prompts['intermediate'])}.

Structure your explanation as:

OVERVIEW:
[Brief description of what the code does]

STEP-BY-STEP BREAKDOWN:
[Go through the code section by section]

KEY CONCEPTS:
[Important programming concepts used]

COMPLEXITY ANALYSIS:
- Time Complexity: O(...)
- Space Complexity: O(...)

{"USAGE EXAMPLES:" if include_examples else ""}
{"[Provide examples of how to use this code]" if include_examples else ""}

Make the explanation clear, educational, and appropriate for the {detail_level} level."""
        
        user_prompt = f"""Explain this {language} code:

```{language}
{code}
```

Detail level: {detail_level}
Include examples: {include_examples}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            import asyncio
            # Add timeout to prevent hanging
            response = await asyncio.wait_for(
                create_groq_completion(
                    messages=messages,
                    temperature=0.4,
                    max_tokens=2048
                ),
                timeout=45.0  # 45 second timeout for code explanation
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Parse explanation components
            explanation_data = self._parse_explanation_response(content)
            
            return {
                "id": str(uuid.uuid4()),
                "explanation": explanation_data["explanation"],
                "key_concepts": explanation_data["key_concepts"],
                "examples": explanation_data["examples"] if include_examples else [],
                "complexity_analysis": explanation_data["complexity_analysis"],
                "metadata": {
                    "language": language,
                    "detail_level": detail_level,
                    "include_examples": include_examples,
                    "model": self.model,
                    "explained_at": datetime.utcnow().isoformat()
                }
            }
            
        except asyncio.TimeoutError:
            raise Exception("Code explanation timeout - request took too long")
        except Exception as e:
            raise Exception(f"Code explanation failed: {str(e)}")
    
    def _build_code_generation_prompt(
        self, 
        language: str, 
        framework: Optional[str], 
        complexity: str, 
        include_comments: bool, 
        include_tests: bool
    ) -> str:
        """Build system prompt for code generation."""
        
        framework_text = f" using {framework}" if framework else ""
        complexity_levels = {
            "beginner": "simple and easy to understand",
            "intermediate": "well-structured with moderate complexity",
            "advanced": "sophisticated with advanced patterns and optimizations"
        }
        
        return f"""You are an expert {language} developer. Generate high-quality, production-ready {language} code{framework_text}.

Requirements:
- Code complexity: {complexity_levels.get(complexity, 'intermediate')}
- Follow {language} best practices and conventions
- Include proper error handling
- {'Add detailed comments explaining the logic' if include_comments else 'Keep comments minimal'}
- {'Include comprehensive unit tests' if include_tests else 'Focus only on the main implementation'}
- Make code modular and reusable
- Ensure code is secure and efficient

Format your response as:
```{language}
[CODE HERE]
```

{f"```{language}" if include_tests else ""}
{f"# TESTS" if include_tests else ""}
{f"[TEST CODE HERE]" if include_tests else ""}
{f"```" if include_tests else ""}

EXPLANATION:
[Brief explanation of the implementation approach and key decisions]"""
    
    def _parse_code_response(self, content: str, language: str) -> tuple[str, str]:
        """Parse code and explanation from AI response."""
        lines = content.split('\n')
        code_lines = []
        explanation_lines = []
        
        in_code_block = False
        in_explanation = False
        
        for line in lines:
            if line.strip().startswith(f'```{language}') or line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            elif line.strip().upper().startswith('EXPLANATION:'):
                in_explanation = True
                continue
            
            if in_code_block:
                code_lines.append(line)
            elif in_explanation:
                explanation_lines.append(line)
        
        # If no code block found, try to extract code differently
        if not code_lines:
            code_lines = [line for line in lines if not line.strip().upper().startswith(('EXPLANATION:', 'NOTE:', 'USAGE:'))]
        
        code = '\n'.join(code_lines).strip()
        explanation = '\n'.join(explanation_lines).strip()
        
        return code, explanation
    
    def _parse_review_response(self, content: str) -> Dict[str, Any]:
        """Parse code review response when JSON parsing fails."""
        # Basic parsing fallback
        return {
            "overall_score": 75,  # Default score
            "summary": content[:200] + "..." if len(content) > 200 else content,
            "issues": [],
            "suggestions": [],
            "strengths": []
        }
    
    def _parse_optimization_response(self, content: str, language: str) -> tuple[str, str, List[str]]:
        """Parse optimization response."""
        lines = content.split('\n')
        code_lines = []
        explanation_lines = []
        improvement_lines = []
        
        current_section = None
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith(f'```{language}') or line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            elif line.strip().upper().startswith('EXPLANATION:'):
                current_section = 'explanation'
                continue
            elif line.strip().upper().startswith('IMPROVEMENTS:'):
                current_section = 'improvements'
                continue
            
            if in_code_block:
                code_lines.append(line)
            elif current_section == 'explanation':
                explanation_lines.append(line)
            elif current_section == 'improvements':
                if line.strip() and (line.strip().startswith(('1.', '2.', '3.', '-', '*'))):
                    improvement_lines.append(line.strip())
        
        code = '\n'.join(code_lines).strip()
        explanation = '\n'.join(explanation_lines).strip()
        improvements = improvement_lines
        
        return code, explanation, improvements
    
    def _parse_explanation_response(self, content: str) -> Dict[str, Any]:
        """Parse explanation response."""
        sections = {
            "explanation": content,
            "key_concepts": [],
            "examples": [],
            "complexity_analysis": ""
        }
        
        # Try to extract structured sections
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line_upper = line.strip().upper()
            if line_upper.startswith('KEY CONCEPTS:'):
                current_section = 'key_concepts'
                continue
            elif line_upper.startswith('USAGE EXAMPLES:'):
                current_section = 'examples'
                continue
            elif line_upper.startswith('COMPLEXITY ANALYSIS:'):
                current_section = 'complexity'
                continue
            
            if current_section == 'key_concepts' and line.strip():
                if line.strip().startswith(('-', '*', '"')):
                    sections["key_concepts"].append(line.strip()[1:].strip())
            elif current_section == 'complexity' and line.strip():
                sections["complexity_analysis"] += line + '\n'
        
        return sections
    
    def _estimate_performance_gain(self, improvements: List[str]) -> str:
        """Estimate performance gain based on improvements."""
        if not improvements:
            return "0-5%"
        
        gain_keywords = {
            "algorithm": 20,
            "cache": 15,
            "loop": 10,
            "memory": 8,
            "database": 25,
            "async": 30,
            "parallel": 40
        }
        
        total_gain = 0
        for improvement in improvements:
            for keyword, gain in gain_keywords.items():
                if keyword.lower() in improvement.lower():
                    total_gain += gain
                    break
        
        if total_gain >= 50:
            return "50%+"
        elif total_gain >= 30:
            return "30-50%"
        elif total_gain >= 15:
            return "15-30%"
        elif total_gain >= 5:
            return "5-15%"
        else:
            return "0-5%"
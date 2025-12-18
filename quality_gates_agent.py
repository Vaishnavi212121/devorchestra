"""
QUALITY GATES AGENT
Implements SonarQube-style quality checks for generated code
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import re
import ast

class QualityGatesAgent(BaseAgent):
    def __init__(self):
        super().__init__("quality_gates")
        
        # Quality thresholds
        self.THRESHOLDS = {
            "maintainability": 80,
            "reliability": 85,
            "security": 90,
            "code_coverage": 80,
            "duplication": 3,  # Max 3% duplication
            "complexity": 10   # Max cyclomatic complexity per function
        }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive quality analysis"""
        frontend_code = task.get("frontend_code", "")
        backend_code = task.get("backend_code", "")
        database_code = task.get("database_code", "")
        
        results = {
            "frontend": self._analyze_frontend(frontend_code) if frontend_code else {},
            "backend": self._analyze_backend(backend_code) if backend_code else {},
            "database": self._analyze_database(database_code) if database_code else {}
        }
        
        # Calculate overall quality score
        overall = self._calculate_overall_quality(results)
        
        return {
            "quality_analysis": results,
            "overall_quality": overall,
            "passed_quality_gates": overall["quality_gate_passed"],
            "recommendations": overall["recommendations"]
        }
    
    def _analyze_backend(self, code: str) -> Dict[str, Any]:
        """Analyze Python backend code"""
        issues = []
        metrics = {
            "lines_of_code": len(code.split('\n')),
            "complexity_score": 0,
            "maintainability_index": 100
        }
        
        try:
            tree = ast.parse(code)
            
            # Check 1: Function complexity
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    if complexity > self.THRESHOLDS["complexity"]:
                        issues.append({
                            "type": "complexity",
                            "severity": "major",
                            "function": node.name,
                            "complexity": complexity,
                            "message": f"Function {node.name} has complexity {complexity} (max {self.THRESHOLDS['complexity']})"
                        })
                    metrics["complexity_score"] = max(metrics["complexity_score"], complexity)
            
            # Check 2: Missing docstrings
            functions_without_docs = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not ast.get_docstring(node):
                        functions_without_docs.append(node.name)
            
            if functions_without_docs:
                issues.append({
                    "type": "documentation",
                    "severity": "minor",
                    "message": f"{len(functions_without_docs)} functions missing docstrings",
                    "functions": functions_without_docs[:5]
                })
            
            # Check 3: Security issues
            security_issues = self._check_security(code)
            issues.extend(security_issues)
            
            # Check 4: Code smells
            smells = self._detect_code_smells(code)
            issues.extend(smells)
            
            # Calculate maintainability index
            metrics["maintainability_index"] = self._calculate_maintainability(
                metrics["lines_of_code"],
                metrics["complexity_score"],
                len(issues)
            )
            
        except SyntaxError as e:
            issues.append({
                "type": "syntax",
                "severity": "blocker",
                "message": f"Syntax error: {e}"
            })
            metrics["maintainability_index"] = 0
        
        # Categorize issues by severity
        blocker = len([i for i in issues if i.get("severity") == "blocker"])
        critical = len([i for i in issues if i.get("severity") == "critical"])
        major = len([i for i in issues if i.get("severity") == "major"])
        minor = len([i for i in issues if i.get("severity") == "minor"])
        
        return {
            "metrics": metrics,
            "issues": issues[:20],  # Top 20 issues
            "issue_summary": {
                "blocker": blocker,
                "critical": critical,
                "major": major,
                "minor": minor,
                "total": len(issues)
            },
            "quality_score": max(0, 100 - (blocker * 20 + critical * 10 + major * 5 + minor * 1))
        }
    
    def _analyze_frontend(self, code: str) -> Dict[str, Any]:
        """Analyze React frontend code"""
        issues = []
        
        # Check 1: Missing key props in lists
        if ".map(" in code and "key=" not in code:
            issues.append({
                "type": "react",
                "severity": "major",
                "message": "Missing 'key' prop in list rendering"
            })
        
        # Check 2: useState without proper naming
        state_hooks = re.findall(r'useState\(([^)]*)\)', code)
        if len(state_hooks) > 10:
            issues.append({
                "type": "performance",
                "severity": "minor",
                "message": f"Too many useState hooks ({len(state_hooks)}), consider useReducer"
            })
        
        # Check 3: Inline functions in JSX (performance)
        inline_functions = len(re.findall(r'onClick=\{.*=>', code))
        if inline_functions > 5:
            issues.append({
                "type": "performance",
                "severity": "minor",
                "message": f"{inline_functions} inline functions in JSX, consider useCallback"
            })
        
        # Check 4: Missing error boundaries
        if "ErrorBoundary" not in code and "componentDidCatch" not in code:
            issues.append({
                "type": "reliability",
                "severity": "major",
                "message": "No error boundary implemented"
            })
        
        # Check 5: Accessibility issues
        if "className" in code and "aria-" not in code:
            issues.append({
                "type": "accessibility",
                "severity": "minor",
                "message": "Missing ARIA attributes for accessibility"
            })
        
        return {
            "metrics": {
                "lines_of_code": len(code.split('\n')),
                "components": len(re.findall(r'function \w+\(', code))
            },
            "issues": issues,
            "quality_score": max(0, 100 - len(issues) * 5)
        }
    
    def _analyze_database(self, sql: str) -> Dict[str, Any]:
        """Analyze SQL schema"""
        issues = []
        
        # Check 1: Missing primary keys
        tables = re.findall(r'CREATE TABLE\s+(\w+)', sql, re.IGNORECASE)
        for table in tables:
            table_def = re.search(rf'CREATE TABLE\s+{table}\s*\((.*?)\);', sql, re.IGNORECASE | re.DOTALL)
            if table_def and "PRIMARY KEY" not in table_def.group(0).upper():
                issues.append({
                    "type": "schema",
                    "severity": "major",
                    "table": table,
                    "message": f"Table {table} missing PRIMARY KEY"
                })
        
        # Check 2: Missing indexes
        if "CREATE INDEX" not in sql.upper() and len(tables) > 1:
            issues.append({
                "type": "performance",
                "severity": "minor",
                "message": "No indexes defined for multi-table schema"
            })
        
        # Check 3: No foreign key constraints
        if "FOREIGN KEY" not in sql.upper() and "REFERENCES" not in sql.upper() and len(tables) > 1:
            issues.append({
                "type": "schema",
                "severity": "major",
                "message": "No foreign key relationships defined"
            })
        
        # Check 4: VARCHAR without length
        if re.search(r'VARCHAR\s*\(', sql, re.IGNORECASE) is None and "VARCHAR" in sql.upper():
            issues.append({
                "type": "schema",
                "severity": "minor",
                "message": "VARCHAR without explicit length"
            })
        
        return {
            "metrics": {
                "tables": len(tables),
                "constraints": sql.upper().count("CONSTRAINT")
            },
            "issues": issues,
            "quality_score": max(0, 100 - len(issues) * 10)
        }
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_security(self, code: str) -> List[Dict]:
        """Check for common security issues"""
        issues = []
        
        # SQL Injection risks
        if "execute(" in code and "f\"" in code:
            issues.append({
                "type": "security",
                "severity": "critical",
                "message": "Possible SQL injection: f-string in execute()"
            })
        
        # Hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret")
        ]
        
        for pattern, message in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    "type": "security",
                    "severity": "critical",
                    "message": message
                })
        
        # Unsafe eval/exec
        if "eval(" in code or "exec(" in code:
            issues.append({
                "type": "security",
                "severity": "blocker",
                "message": "Unsafe use of eval() or exec()"
            })
        
        return issues
    
    def _detect_code_smells(self, code: str) -> List[Dict]:
        """Detect code smells"""
        smells = []
        
        # Long functions
        functions = re.findall(r'def \w+\([^)]*\):(.*?)(?=\ndef |\nclass |\Z)', code, re.DOTALL)
        for i, func in enumerate(functions):
            lines = len(func.split('\n'))
            if lines > 50:
                smells.append({
                    "type": "code_smell",
                    "severity": "major",
                    "message": f"Function #{i+1} too long ({lines} lines)"
                })
        
        # Too many parameters
        params = re.findall(r'def \w+\(([^)]*)\)', code)
        for i, param_list in enumerate(params):
            param_count = len([p for p in param_list.split(',') if p.strip()])
            if param_count > 5:
                smells.append({
                    "type": "code_smell",
                    "severity": "minor",
                    "message": f"Function #{i+1} has {param_count} parameters (max 5)"
                })
        
        return smells
    
    def _calculate_maintainability(self, loc: int, complexity: int, issues: int) -> int:
        """Calculate maintainability index (0-100)"""
        # Simplified maintainability index
        base_score = 100
        
        # Penalize for size
        base_score -= min(20, loc / 50)
        
        # Penalize for complexity
        base_score -= min(30, complexity * 2)
        
        # Penalize for issues
        base_score -= min(30, issues * 3)
        
        return max(0, int(base_score))
    
    def _calculate_overall_quality(self, results: Dict) -> Dict[str, Any]:
        """Calculate overall quality metrics"""
        scores = []
        all_issues = []
        
        for component, data in results.items():
            if data and "quality_score" in data:
                scores.append(data["quality_score"])
            if data and "issues" in data:
                all_issues.extend(data["issues"])
        
        overall_score = sum(scores) / len(scores) if scores else 0
        quality_gate_passed = overall_score >= self.THRESHOLDS["maintainability"]
        
        # Generate recommendations
        recommendations = []
        if overall_score < 60:
            recommendations.append("Critical: Immediate refactoring required")
        elif overall_score < 80:
            recommendations.append("Address major issues before deployment")
        else:
            recommendations.append("Code quality meets standards")
        
        # Issue-specific recommendations
        blocker_count = len([i for i in all_issues if i.get("severity") == "blocker"])
        if blocker_count > 0:
            recommendations.append(f"Fix {blocker_count} blocker issues immediately")
        
        return {
            "overall_score": round(overall_score, 1),
            "quality_gate_passed": quality_gate_passed,
            "total_issues": len(all_issues),
            "recommendations": recommendations,
            "rating": self._get_rating(overall_score)
        }
    
    def _get_rating(self, score: float) -> str:
        """Convert score to letter rating"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
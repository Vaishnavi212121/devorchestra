"""
PRODUCTION-READY LEGACY CODE AGENT
- Real 4-phase AST analysis
- Safe code integration
- Backward compatibility checks
- Minimal diff generation
"""
from agents.base_agent import BaseAgent
import ast
from typing import Dict, Any, List, Set
import re
import difflib

class LegacyCodeAgent(BaseAgent):
    def __init__(self):
        super().__init__("legacy_agent")
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        4-PHASE LEGACY INTEGRATION:
        Phase 1: AST Analysis (Static)
        Phase 2: LLM Understanding (Semantic)
        Phase 3: Integration Planning (Strategic)
        Phase 4: Safe Modifications (Tactical)
        """
        legacy_code = task.get("legacy_code", "")
        new_feature = task.get("requirements", "")
        integration_type = task.get("integration_type", "add_endpoint")
        
        if not legacy_code:
            return {"error": "No legacy code provided"}
        
        print(f"🔍 Starting 4-phase legacy integration...")
        
        # ==========================================
        # PHASE 1: AST ANALYSIS (Static Analysis)
        # ==========================================
        print("📊 Phase 1: AST Analysis...")
        ast_analysis = self._analyze_with_ast(legacy_code)
        
        # ==========================================
        # PHASE 2: LLM UNDERSTANDING (Semantic)
        # ==========================================
        print("🧠 Phase 2: LLM Understanding...")
        understanding = await self._understand_with_llm(legacy_code, ast_analysis)
        
        # ==========================================
        # PHASE 3: INTEGRATION PLANNING (Strategic)
        # ==========================================
        print("📋 Phase 3: Integration Planning...")
        integration_plan = await self._create_integration_plan(
            legacy_code, ast_analysis, understanding, new_feature, integration_type
        )
        
        # ==========================================
        # PHASE 4: SAFE MODIFICATIONS (Tactical)
        # ==========================================
        print("✏️ Phase 4: Safe Modifications...")
        modifications = await self._generate_safe_modifications(
            legacy_code, integration_plan, new_feature
        )
        
        # ==========================================
        # VALIDATION & COMPATIBILITY CHECK
        # ==========================================
        compatibility = self._check_compatibility(legacy_code, modifications, ast_analysis)
        
        return {
            "phase1_ast_analysis": ast_analysis,
            "phase2_understanding": understanding,
            "phase3_integration_plan": integration_plan,
            "phase4_modifications": modifications,
            "compatibility_report": compatibility,
            "backward_compatible": compatibility["is_compatible"],
            "risk_assessment": self._assess_risks(ast_analysis, modifications),
            "diff": self._generate_diff(legacy_code, modifications.get("modified_code", ""))
        }
    
    def _analyze_with_ast(self, code: str) -> Dict[str, Any]:
        """Phase 1: Deep AST analysis"""
        try:
            tree = ast.parse(code)
            
            analysis = {
                "classes": [],
                "functions": [],
                "endpoints": [],
                "imports": [],
                "dependencies": set(),
                "complexity_score": 0,
                "global_variables": [],
                "decorators": [],
                "frameworks_detected": set()
            }
            
            for node in ast.walk(tree):
                # Classes
                if isinstance(node, ast.ClassDef):
                    methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    analysis["classes"].append({
                        "name": node.name,
                        "methods": methods,
                        "line": node.lineno
                    })
                
                # Functions
                elif isinstance(node, ast.FunctionDef):
                    # Detect API endpoints
                    decorators = [d.id if isinstance(d, ast.Name) else 
                                 getattr(d.func, 'attr', '') if isinstance(d, ast.Call) else ''
                                 for d in node.decorator_list]
                    
                    analysis["functions"].append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": decorators,
                        "line": node.lineno
                    })
                    
                    # Detect Flask/FastAPI endpoints
                    for dec in decorators:
                        if dec in ['route', 'get', 'post', 'put', 'delete', 'patch']:
                            analysis["endpoints"].append({
                                "method": dec.upper() if dec != 'route' else 'GET',
                                "function": node.name,
                                "line": node.lineno
                            })
                
                # Imports
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis["imports"].append(alias.name)
                            analysis["dependencies"].add(alias.name.split('.')[0])
                    else:
                        if node.module:
                            analysis["imports"].append(node.module)
                            analysis["dependencies"].add(node.module.split('.')[0])
                            
                            # Framework detection
                            if 'flask' in node.module.lower():
                                analysis["frameworks_detected"].add('Flask')
                            elif 'fastapi' in node.module.lower():
                                analysis["frameworks_detected"].add('FastAPI')
                            elif 'django' in node.module.lower():
                                analysis["frameworks_detected"].add('Django')
                
                # Global variables
                elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            analysis["global_variables"].append(target.id)
            
            # Calculate complexity
            analysis["complexity_score"] = (
                len(analysis["classes"]) * 3 +
                len(analysis["functions"]) * 2 +
                len(analysis["endpoints"]) * 5
            )
            
            # Convert sets to lists for JSON serialization
            analysis["dependencies"] = sorted(list(analysis["dependencies"]))
            analysis["frameworks_detected"] = list(analysis["frameworks_detected"])
            
            return analysis
            
        except SyntaxError as e:
            return {
                "error": f"AST parsing failed: {e}",
                "parse_error": True
            }
    
    async def _understand_with_llm(self, code: str, ast_analysis: Dict) -> str:
        """Phase 2: Semantic understanding"""
        prompt = f"""Analyze this Python codebase and explain its architecture:

CODE:
{code[:3000]}

AST ANALYSIS:
- Classes: {len(ast_analysis.get('classes', []))}
- Functions: {len(ast_analysis.get('functions', []))}
- Endpoints: {len(ast_analysis.get('endpoints', []))}
- Frameworks: {ast_analysis.get('frameworks_detected', [])}

Provide a brief summary (3-4 sentences) covering:
1. What this code does (business purpose)
2. Architecture pattern used
3. Key dependencies and design choices
4. Integration points for new features

Keep response concise and technical."""
        
        try:
            response = await self.generate_response(prompt)
            return response.strip()
        except Exception as e:
            return f"Understanding failed: {str(e)}"
    
    async def _create_integration_plan(self, code: str, ast: Dict, 
                                       understanding: str, new_feature: str,
                                       integration_type: str) -> str:
        """Phase 3: Strategic integration planning"""
        endpoints = ast.get("endpoints", [])
        functions = ast.get("functions", [])
        
        prompt = f"""Create an integration plan for adding this feature to existing code:

NEW FEATURE: {new_feature}
INTEGRATION TYPE: {integration_type}

EXISTING CODEBASE:
{understanding}

EXISTING ENDPOINTS: {[e['function'] for e in endpoints]}
EXISTING FUNCTIONS: {[f['name'] for f in functions[:10]]}

Create a plan that:
1. Identifies WHERE to add the new code (specific line numbers if possible)
2. Lists what needs modification vs what's new
3. Ensures no conflicts with existing endpoints
4. Maintains backward compatibility
5. Minimizes code changes

Format as a numbered action plan."""
        
        try:
            response = await self.generate_response(prompt)
            return response.strip()
        except Exception as e:
            return f"Planning failed: {str(e)}"
    
    async def _generate_safe_modifications(self, legacy_code: str, 
                                          plan: str, new_feature: str) -> Dict[str, Any]:
        """Phase 4: Generate minimal safe modifications"""
        prompt = f"""Given this legacy code and integration plan, generate the MODIFIED code:

INTEGRATION PLAN:
{plan}

NEW FEATURE TO ADD:
{new_feature}

LEGACY CODE:
{legacy_code}

Generate the COMPLETE modified code that:
1. Adds the new feature
2. Keeps ALL existing functionality
3. Uses minimal changes
4. Maintains code style consistency
5. Adds necessary imports only

Return ONLY the complete modified Python code, no explanations."""
        
        try:
            response = await self.generate_response(prompt)
            modified_code = response.replace("```python", "").replace("```", "").strip()
            
            return {
                "modified_code": modified_code,
                "changes_made": self._identify_changes(legacy_code, modified_code),
                "new_lines": len(modified_code.split('\n')) - len(legacy_code.split('\n'))
            }
        except Exception as e:
            return {
                "error": f"Modification generation failed: {str(e)}",
                "modified_code": legacy_code  # Return original on error
            }
    
    def _check_compatibility(self, original: str, modifications: Dict, 
                            ast_analysis: Dict) -> Dict[str, Any]:
        """Verify backward compatibility"""
        modified_code = modifications.get("modified_code", "")
        
        # Re-analyze modified code
        try:
            modified_ast = self._analyze_with_ast(modified_code)
        except:
            return {
                "is_compatible": False,
                "error": "Modified code has syntax errors"
            }
        
        # Check 1: All original endpoints still exist
        original_endpoints = {e['function'] for e in ast_analysis.get('endpoints', [])}
        modified_endpoints = {e['function'] for e in modified_ast.get('endpoints', [])}
        
        missing_endpoints = original_endpoints - modified_endpoints
        new_endpoints = modified_endpoints - original_endpoints
        
        # Check 2: All original functions still exist
        original_functions = {f['name'] for f in ast_analysis.get('functions', [])}
        modified_functions = {f['name'] for f in modified_ast.get('functions', [])}
        
        missing_functions = original_functions - modified_functions
        new_functions = modified_functions - original_functions
        
        is_compatible = len(missing_endpoints) == 0 and len(missing_functions) == 0
        
        return {
            "is_compatible": is_compatible,
            "missing_endpoints": list(missing_endpoints),
            "new_endpoints": list(new_endpoints),
            "missing_functions": list(missing_functions),
            "new_functions": list(new_functions),
            "compatibility_score": 100 if is_compatible else 50
        }
    
    def _identify_changes(self, original: str, modified: str) -> List[str]:
        """Identify what changed"""
        changes = []
        
        orig_lines = original.split('\n')
        mod_lines = modified.split('\n')
        
        diff = difflib.unified_diff(orig_lines, mod_lines, lineterm='')
        
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                changes.append(f"Added: {line[1:].strip()}")
            elif line.startswith('-') and not line.startswith('---'):
                changes.append(f"Removed: {line[1:].strip()}")
        
        return changes[:10]  # First 10 changes
    
    def _generate_diff(self, original: str, modified: str) -> str:
        """Generate unified diff"""
        diff = difflib.unified_diff(
            original.split('\n'),
            modified.split('\n'),
            lineterm='',
            fromfile='original.py',
            tofile='modified.py'
        )
        return '\n'.join(list(diff)[:50])  # First 50 lines
    
    def _assess_risks(self, ast: Dict, mods: Dict) -> Dict[str, Any]:
        """Risk assessment"""
        risk_score = 0
        concerns = []
        
        # High complexity = higher risk
        if ast.get("complexity_score", 0) > 50:
            risk_score += 30
            concerns.append("High codebase complexity")
        
        # Many changes = higher risk
        new_lines = mods.get("new_lines", 0)
        if new_lines > 50:
            risk_score += 20
            concerns.append(f"Large modification ({new_lines} lines)")
        
        # Missing compatibility check
        if mods.get("error"):
            risk_score += 50
            concerns.append("Modification generation had errors")
        
        risk_level = "low" if risk_score < 30 else "medium" if risk_score < 60 else "high"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "concerns": concerns,
            "recommendation": "Proceed with testing" if risk_level == "low" else "Review carefully"
        }
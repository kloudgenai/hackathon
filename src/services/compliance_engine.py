import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class ComplianceLevel(Enum):
    """Compliance assessment levels."""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"

class RiskLevel(Enum):
    """Risk assessment levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

@dataclass
class ComplianceRule:
    """Represents a compliance rule for a specific standard."""
    rule_id: str
    standard: str
    title: str
    description: str
    requirement_patterns: List[str]
    test_case_patterns: List[str]
    mandatory: bool
    risk_level: RiskLevel
    validation_criteria: Dict[str, Any]

@dataclass
class ComplianceResult:
    """Result of compliance assessment."""
    rule_id: str
    standard: str
    compliance_level: ComplianceLevel
    score: float  # 0.0 to 1.0
    findings: List[str]
    recommendations: List[str]
    evidence: List[str]
    risk_assessment: RiskLevel

class ComplianceEngine:
    """
    Engine for validating compliance with healthcare regulatory standards.
    """
    
    def __init__(self):
        self.compliance_rules = self._initialize_compliance_rules()
        self.standards = [
            "FDA 21 CFR Part 820",
            "IEC 62304",
            "ISO 13485",
            "ISO 9001",
            "ISO 27001",
            "HIPAA",
            "GDPR"
        ]
    
    def _initialize_compliance_rules(self) -> Dict[str, ComplianceRule]:
        """Initialize compliance rules for various healthcare standards."""
        rules = {}
        
        # FDA 21 CFR Part 820 Rules
        rules["FDA_820_001"] = ComplianceRule(
            rule_id="FDA_820_001",
            standard="FDA 21 CFR Part 820",
            title="Design Controls",
            description="Software development must follow design control procedures",
            requirement_patterns=[
                r"design\s+control",
                r"design\s+input",
                r"design\s+output",
                r"design\s+review",
                r"design\s+verification",
                r"design\s+validation"
            ],
            test_case_patterns=[
                r"verify\s+design",
                r"validate\s+design",
                r"design\s+review",
                r"traceability"
            ],
            mandatory=True,
            risk_level=RiskLevel.HIGH,
            validation_criteria={
                "requires_traceability": True,
                "requires_verification": True,
                "requires_validation": True
            }
        )
        
        rules["FDA_820_002"] = ComplianceRule(
            rule_id="FDA_820_002",
            standard="FDA 21 CFR Part 820",
            title="Risk Management",
            description="Risk analysis and management throughout development",
            requirement_patterns=[
                r"risk\s+analysis",
                r"risk\s+management",
                r"hazard\s+analysis",
                r"failure\s+mode"
            ],
            test_case_patterns=[
                r"risk\s+test",
                r"safety\s+test",
                r"hazard\s+test",
                r"failure\s+test"
            ],
            mandatory=True,
            risk_level=RiskLevel.HIGH,
            validation_criteria={
                "requires_risk_analysis": True,
                "requires_mitigation": True
            }
        )
        
        # IEC 62304 Rules
        rules["IEC_62304_001"] = ComplianceRule(
            rule_id="IEC_62304_001",
            standard="IEC 62304",
            title="Software Safety Classification",
            description="Software must be classified according to safety requirements",
            requirement_patterns=[
                r"safety\s+class",
                r"class\s+[abc]",
                r"safety\s+classification",
                r"medical\s+device\s+software"
            ],
            test_case_patterns=[
                r"safety\s+test",
                r"class\s+[abc]\s+test",
                r"safety\s+verification"
            ],
            mandatory=True,
            risk_level=RiskLevel.HIGH,
            validation_criteria={
                "requires_classification": True,
                "requires_safety_analysis": True
            }
        )
        
        rules["IEC_62304_002"] = ComplianceRule(
            rule_id="IEC_62304_002",
            standard="IEC 62304",
            title="Software Development Lifecycle",
            description="Structured software development process",
            requirement_patterns=[
                r"software\s+development\s+plan",
                r"development\s+lifecycle",
                r"software\s+architecture",
                r"software\s+design"
            ],
            test_case_patterns=[
                r"integration\s+test",
                r"system\s+test",
                r"software\s+test",
                r"unit\s+test"
            ],
            mandatory=True,
            risk_level=RiskLevel.MEDIUM,
            validation_criteria={
                "requires_documentation": True,
                "requires_testing": True
            }
        )
        
        # ISO 13485 Rules
        rules["ISO_13485_001"] = ComplianceRule(
            rule_id="ISO_13485_001",
            standard="ISO 13485",
            title="Quality Management System",
            description="Quality management system for medical devices",
            requirement_patterns=[
                r"quality\s+management",
                r"qms",
                r"quality\s+system",
                r"quality\s+control"
            ],
            test_case_patterns=[
                r"quality\s+test",
                r"qms\s+test",
                r"quality\s+verification"
            ],
            mandatory=True,
            risk_level=RiskLevel.MEDIUM,
            validation_criteria={
                "requires_documentation": True,
                "requires_procedures": True
            }
        )
        
        # ISO 27001 Rules
        rules["ISO_27001_001"] = ComplianceRule(
            rule_id="ISO_27001_001",
            standard="ISO 27001",
            title="Information Security Management",
            description="Information security controls and management",
            requirement_patterns=[
                r"information\s+security",
                r"data\s+security",
                r"security\s+control",
                r"access\s+control",
                r"encryption",
                r"authentication"
            ],
            test_case_patterns=[
                r"security\s+test",
                r"access\s+control\s+test",
                r"authentication\s+test",
                r"encryption\s+test",
                r"penetration\s+test"
            ],
            mandatory=True,
            risk_level=RiskLevel.HIGH,
            validation_criteria={
                "requires_security_testing": True,
                "requires_access_control": True
            }
        )
        
        # HIPAA Rules
        rules["HIPAA_001"] = ComplianceRule(
            rule_id="HIPAA_001",
            standard="HIPAA",
            title="Protected Health Information",
            description="Protection of patient health information",
            requirement_patterns=[
                r"protected\s+health\s+information",
                r"phi",
                r"patient\s+data",
                r"health\s+information",
                r"privacy",
                r"confidentiality"
            ],
            test_case_patterns=[
                r"privacy\s+test",
                r"phi\s+test",
                r"data\s+protection\s+test",
                r"confidentiality\s+test"
            ],
            mandatory=True,
            risk_level=RiskLevel.HIGH,
            validation_criteria={
                "requires_privacy_protection": True,
                "requires_audit_trail": True
            }
        )
        
        # GDPR Rules
        rules["GDPR_001"] = ComplianceRule(
            rule_id="GDPR_001",
            standard="GDPR",
            title="Data Protection and Privacy",
            description="General Data Protection Regulation compliance",
            requirement_patterns=[
                r"data\s+protection",
                r"gdpr",
                r"personal\s+data",
                r"data\s+subject\s+rights",
                r"consent",
                r"data\s+processing"
            ],
            test_case_patterns=[
                r"gdpr\s+test",
                r"data\s+protection\s+test",
                r"consent\s+test",
                r"data\s+subject\s+test",
                r"privacy\s+test"
            ],
            mandatory=True,
            risk_level=RiskLevel.HIGH,
            validation_criteria={
                "requires_consent_management": True,
                "requires_data_subject_rights": True
            }
        )
        
        return rules
    
    def assess_requirement_compliance(self, requirement: Dict[str, Any]) -> List[ComplianceResult]:
        """
        Assess compliance of a requirement against all applicable standards.
        """
        results = []
        requirement_text = f"{requirement.get('title', '')} {requirement.get('description', '')}".lower()
        
        for rule in self.compliance_rules.values():
            compliance_result = self._evaluate_requirement_against_rule(requirement_text, requirement, rule)
            if compliance_result.compliance_level != ComplianceLevel.UNKNOWN:
                results.append(compliance_result)
        
        return results
    
    def assess_test_case_compliance(self, test_case: Dict[str, Any], requirement: Dict[str, Any] = None) -> List[ComplianceResult]:
        """
        Assess compliance of a test case against all applicable standards.
        """
        results = []
        test_case_text = f"{test_case.get('title', '')} {test_case.get('description', '')}".lower()
        test_steps_text = " ".join(test_case.get('test_steps', [])).lower()
        full_text = f"{test_case_text} {test_steps_text}"
        
        for rule in self.compliance_rules.values():
            compliance_result = self._evaluate_test_case_against_rule(full_text, test_case, rule, requirement)
            if compliance_result.compliance_level != ComplianceLevel.UNKNOWN:
                results.append(compliance_result)
        
        return results
    
    def _evaluate_requirement_against_rule(self, requirement_text: str, requirement: Dict[str, Any], rule: ComplianceRule) -> ComplianceResult:
        """
        Evaluate a requirement against a specific compliance rule.
        """
        findings = []
        recommendations = []
        evidence = []
        score = 0.0
        
        # Check if requirement patterns match
        pattern_matches = 0
        for pattern in rule.requirement_patterns:
            if re.search(pattern, requirement_text, re.IGNORECASE):
                pattern_matches += 1
                evidence.append(f"Found pattern: {pattern}")
        
        if pattern_matches == 0:
            return ComplianceResult(
                rule_id=rule.rule_id,
                standard=rule.standard,
                compliance_level=ComplianceLevel.UNKNOWN,
                score=0.0,
                findings=[],
                recommendations=[],
                evidence=[],
                risk_assessment=RiskLevel.UNKNOWN
            )
        
        # Calculate base score based on pattern matches
        pattern_score = min(pattern_matches / len(rule.requirement_patterns), 1.0)
        score += pattern_score * 0.6
        
        # Check validation criteria
        criteria_score = self._check_validation_criteria(requirement, rule.validation_criteria)
        score += criteria_score * 0.4
        
        # Determine compliance level
        if score >= 0.8:
            compliance_level = ComplianceLevel.COMPLIANT
        elif score >= 0.5:
            compliance_level = ComplianceLevel.PARTIALLY_COMPLIANT
            findings.append("Requirement partially meets compliance criteria")
            recommendations.append(f"Enhance requirement to fully comply with {rule.standard}")
        else:
            compliance_level = ComplianceLevel.NON_COMPLIANT
            findings.append("Requirement does not meet compliance criteria")
            recommendations.append(f"Revise requirement to comply with {rule.standard}")
        
        # Add specific recommendations based on rule
        if rule.validation_criteria.get("requires_traceability") and "traceability" not in requirement_text:
            recommendations.append("Add traceability requirements")
        
        if rule.validation_criteria.get("requires_risk_analysis") and "risk" not in requirement_text:
            recommendations.append("Include risk analysis requirements")
        
        return ComplianceResult(
            rule_id=rule.rule_id,
            standard=rule.standard,
            compliance_level=compliance_level,
            score=score,
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_assessment=rule.risk_level
        )
    
    def _evaluate_test_case_against_rule(self, test_case_text: str, test_case: Dict[str, Any], rule: ComplianceRule, requirement: Dict[str, Any] = None) -> ComplianceResult:
        """
        Evaluate a test case against a specific compliance rule.
        """
        findings = []
        recommendations = []
        evidence = []
        score = 0.0
        
        # Check if test case patterns match
        pattern_matches = 0
        for pattern in rule.test_case_patterns:
            if re.search(pattern, test_case_text, re.IGNORECASE):
                pattern_matches += 1
                evidence.append(f"Found test pattern: {pattern}")
        
        # Also check if requirement patterns are addressed in test case
        req_pattern_matches = 0
        if requirement:
            requirement_text = f"{requirement.get('title', '')} {requirement.get('description', '')}".lower()
            for pattern in rule.requirement_patterns:
                if re.search(pattern, requirement_text, re.IGNORECASE):
                    req_pattern_matches += 1
        
        if pattern_matches == 0 and req_pattern_matches == 0:
            return ComplianceResult(
                rule_id=rule.rule_id,
                standard=rule.standard,
                compliance_level=ComplianceLevel.UNKNOWN,
                score=0.0,
                findings=[],
                recommendations=[],
                evidence=[],
                risk_assessment=RiskLevel.UNKNOWN
            )
        
        # Calculate score
        if len(rule.test_case_patterns) > 0:
            pattern_score = min(pattern_matches / len(rule.test_case_patterns), 1.0)
        else:
            pattern_score = 0.5  # Default score if no specific test patterns
        
        score += pattern_score * 0.7
        
        # Check if test case covers requirement compliance aspects
        if req_pattern_matches > 0:
            score += 0.3
            evidence.append("Test case addresses compliance-related requirements")
        
        # Check test case completeness
        completeness_score = self._assess_test_case_completeness(test_case)
        score = (score + completeness_score) / 2
        
        # Determine compliance level
        if score >= 0.8:
            compliance_level = ComplianceLevel.COMPLIANT
        elif score >= 0.5:
            compliance_level = ComplianceLevel.PARTIALLY_COMPLIANT
            findings.append("Test case partially covers compliance requirements")
            recommendations.append(f"Enhance test case to fully verify {rule.standard} compliance")
        else:
            compliance_level = ComplianceLevel.NON_COMPLIANT
            findings.append("Test case does not adequately verify compliance")
            recommendations.append(f"Add test steps to verify {rule.standard} compliance")
        
        # Add specific recommendations
        if rule.validation_criteria.get("requires_security_testing") and "security" not in test_case_text:
            recommendations.append("Add security testing steps")
        
        if rule.validation_criteria.get("requires_verification") and "verify" not in test_case_text:
            recommendations.append("Add verification steps")
        
        return ComplianceResult(
            rule_id=rule.rule_id,
            standard=rule.standard,
            compliance_level=compliance_level,
            score=score,
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_assessment=rule.risk_level
        )
    
    def _check_validation_criteria(self, item: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """
        Check validation criteria against an item (requirement or test case).
        """
        score = 0.0
        total_criteria = len(criteria)
        
        if total_criteria == 0:
            return 1.0
        
        item_text = f"{item.get('title', '')} {item.get('description', '')}".lower()
        
        for criterion, required in criteria.items():
            if not required:
                continue
                
            if criterion == "requires_traceability":
                if "traceability" in item_text or "trace" in item_text:
                    score += 1.0
            elif criterion == "requires_verification":
                if "verify" in item_text or "verification" in item_text:
                    score += 1.0
            elif criterion == "requires_validation":
                if "validate" in item_text or "validation" in item_text:
                    score += 1.0
            elif criterion == "requires_risk_analysis":
                if "risk" in item_text or "hazard" in item_text:
                    score += 1.0
            elif criterion == "requires_security_testing":
                if "security" in item_text or "secure" in item_text:
                    score += 1.0
            elif criterion == "requires_documentation":
                if "document" in item_text or "record" in item_text:
                    score += 1.0
            # Add more criteria as needed
        
        return score / total_criteria
    
    def _assess_test_case_completeness(self, test_case: Dict[str, Any]) -> float:
        """
        Assess the completeness of a test case.
        """
        score = 0.0
        
        # Check for required fields
        if test_case.get('title'):
            score += 0.1
        if test_case.get('description'):
            score += 0.1
        if test_case.get('preconditions'):
            score += 0.1
        if test_case.get('test_steps') and len(test_case['test_steps']) > 0:
            score += 0.3
        if test_case.get('expected_results'):
            score += 0.2
        if test_case.get('postconditions'):
            score += 0.1
        if test_case.get('priority'):
            score += 0.1
        
        return score
    
    def generate_compliance_report(self, requirements: List[Dict[str, Any]], test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive compliance report.
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_requirements": len(requirements),
                "total_test_cases": len(test_cases),
                "standards_assessed": self.standards
            },
            "requirement_compliance": [],
            "test_case_compliance": [],
            "overall_compliance": {},
            "recommendations": []
        }
        
        # Assess requirements
        all_req_results = []
        for req in requirements:
            req_results = self.assess_requirement_compliance(req)
            all_req_results.extend(req_results)
            report["requirement_compliance"].append({
                "requirement_id": req.get('requirement_id', 'Unknown'),
                "compliance_results": [self._compliance_result_to_dict(r) for r in req_results]
            })
        
        # Assess test cases
        all_tc_results = []
        for tc in test_cases:
            # Find related requirement
            related_req = None
            req_id = tc.get('requirement_id')
            if req_id:
                related_req = next((r for r in requirements if r.get('id') == req_id), None)
            
            tc_results = self.assess_test_case_compliance(tc, related_req)
            all_tc_results.extend(tc_results)
            report["test_case_compliance"].append({
                "test_case_id": tc.get('test_case_id', 'Unknown'),
                "compliance_results": [self._compliance_result_to_dict(r) for r in tc_results]
            })
        
        # Calculate overall compliance
        report["overall_compliance"] = self._calculate_overall_compliance(all_req_results, all_tc_results)
        
        # Generate recommendations
        report["recommendations"] = self._generate_overall_recommendations(all_req_results, all_tc_results)
        
        return report
    
    def _compliance_result_to_dict(self, result: ComplianceResult) -> Dict[str, Any]:
        """Convert ComplianceResult to dictionary."""
        return {
            "rule_id": result.rule_id,
            "standard": result.standard,
            "compliance_level": result.compliance_level.value,
            "score": result.score,
            "findings": result.findings,
            "recommendations": result.recommendations,
            "evidence": result.evidence,
            "risk_assessment": result.risk_assessment.value
        }
    
    def _calculate_overall_compliance(self, req_results: List[ComplianceResult], tc_results: List[ComplianceResult]) -> Dict[str, Any]:
        """Calculate overall compliance metrics."""
        overall = {}
        
        # Group by standard
        for standard in self.standards:
            standard_req_results = [r for r in req_results if r.standard == standard]
            standard_tc_results = [r for r in tc_results if r.standard == standard]
            
            if not standard_req_results and not standard_tc_results:
                continue
            
            # Calculate average scores
            req_scores = [r.score for r in standard_req_results]
            tc_scores = [r.score for r in standard_tc_results]
            
            avg_req_score = sum(req_scores) / len(req_scores) if req_scores else 0
            avg_tc_score = sum(tc_scores) / len(tc_scores) if tc_scores else 0
            
            overall_score = (avg_req_score + avg_tc_score) / 2 if req_scores and tc_scores else (avg_req_score or avg_tc_score)
            
            # Determine overall compliance level
            if overall_score >= 0.8:
                compliance_level = ComplianceLevel.COMPLIANT
            elif overall_score >= 0.5:
                compliance_level = ComplianceLevel.PARTIALLY_COMPLIANT
            else:
                compliance_level = ComplianceLevel.NON_COMPLIANT
            
            overall[standard] = {
                "score": overall_score,
                "compliance_level": compliance_level.value,
                "requirement_count": len(standard_req_results),
                "test_case_count": len(standard_tc_results)
            }
        
        return overall
    
    def _generate_overall_recommendations(self, req_results: List[ComplianceResult], tc_results: List[ComplianceResult]) -> List[str]:
        """Generate overall recommendations based on compliance results."""
        recommendations = []
        
        # Collect all recommendations
        all_recommendations = []
        for result in req_results + tc_results:
            all_recommendations.extend(result.recommendations)
        
        # Count frequency and prioritize
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        # Sort by frequency and take top recommendations
        sorted_recommendations = sorted(recommendation_counts.items(), key=lambda x: x[1], reverse=True)
        
        for rec, count in sorted_recommendations[:10]:  # Top 10 recommendations
            recommendations.append(f"{rec} (mentioned {count} times)")
        
        return recommendations
    
    def get_compliance_standards(self) -> List[Dict[str, Any]]:
        """Get information about supported compliance standards."""
        standards_info = []
        
        for standard in self.standards:
            rules = [rule for rule in self.compliance_rules.values() if rule.standard == standard]
            standards_info.append({
                "name": standard,
                "rules_count": len(rules),
                "mandatory_rules": len([r for r in rules if r.mandatory]),
                "high_risk_rules": len([r for r in rules if r.risk_level == RiskLevel.HIGH])
            })
        
        return standards_info


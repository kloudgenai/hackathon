import os
import json
import re
from typing import List, Dict, Any, Tuple
from openai import OpenAI

class AIProcessor:
    """
    AI-powered processor for interpreting healthcare software requirements
    and generating test cases using OpenAI's API.
    """
    
    def __init__(self):
        self.client = OpenAI()
        self.healthcare_standards = [
            "FDA 21 CFR Part 820",
            "IEC 62304",
            "ISO 13485",
            "ISO 9001",
            "ISO 27001",
            "HIPAA",
            "GDPR"
        ]
        
    def extract_requirements_from_text(self, text: str, source_document: str = None) -> List[Dict[str, Any]]:
        """
        Extract structured requirements from natural language text.
        """
        prompt = f"""
        You are an expert in healthcare software requirements analysis. 
        Extract individual requirements from the following text and structure them as JSON.
        
        For each requirement, identify:
        1. A unique requirement ID (generate if not present)
        2. Title (brief summary)
        3. Description (detailed requirement text)
        4. Type (functional, non-functional, regulatory, security, performance, usability)
        5. Priority (high, medium, low)
        6. Applicable regulatory standards from: {', '.join(self.healthcare_standards)}
        
        Text to analyze:
        {text}
        
        Return a JSON array of requirements. Each requirement should have the structure:
        {{
            "requirement_id": "REQ-001",
            "title": "Brief title",
            "description": "Detailed description",
            "type": "functional|non-functional|regulatory|security|performance|usability",
            "priority": "high|medium|low",
            "regulatory_standards": ["FDA 21 CFR Part 820", "IEC 62304"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert healthcare software requirements analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            # Extract JSON from the response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                requirements_data = json.loads(json_match.group())
                return requirements_data
            else:
                return []
                
        except Exception as e:
            print(f"Error in requirement extraction: {str(e)}")
            return []
    
    def analyze_requirement_compliance(self, requirement_text: str) -> Dict[str, Any]:
        """
        Analyze a requirement for regulatory compliance and identify applicable standards.
        """
        prompt = f"""
        Analyze the following healthcare software requirement for regulatory compliance.
        
        Requirement: {requirement_text}
        
        Identify:
        1. Which regulatory standards apply: {', '.join(self.healthcare_standards)}
        2. Specific compliance considerations
        3. Risk level (high, medium, low)
        4. Required documentation
        5. Testing implications
        
        Return as JSON:
        {{
            "applicable_standards": ["standard1", "standard2"],
            "compliance_considerations": ["consideration1", "consideration2"],
            "risk_level": "high|medium|low",
            "required_documentation": ["doc1", "doc2"],
            "testing_implications": ["implication1", "implication2"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a healthcare regulatory compliance expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
                
        except Exception as e:
            print(f"Error in compliance analysis: {str(e)}")
            return {}
    
    def generate_test_cases(self, requirement: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate comprehensive test cases for a given requirement.
        """
        prompt = f"""
        Generate comprehensive test cases for the following healthcare software requirement:
        
        Requirement ID: {requirement.get('requirement_id', 'N/A')}
        Title: {requirement.get('title', 'N/A')}
        Description: {requirement.get('description', 'N/A')}
        Type: {requirement.get('type', 'N/A')}
        Priority: {requirement.get('priority', 'N/A')}
        Regulatory Standards: {', '.join(requirement.get('regulatory_standards', []))}
        
        Generate test cases that cover:
        1. Positive test scenarios
        2. Negative test scenarios
        3. Edge cases
        4. Regulatory compliance verification
        5. Data validation (considering healthcare data formats like HL7, FHIR)
        6. Security testing (if applicable)
        7. Performance testing (if applicable)
        
        For each test case, provide:
        - Test case ID
        - Title
        - Description
        - Preconditions
        - Test steps (as an array)
        - Expected results
        - Postconditions
        - Priority
        - Test data requirements
        - Compliance tags
        
        Return as JSON array:
        [{{
            "test_case_id": "TC-001",
            "title": "Test case title",
            "description": "Detailed description",
            "preconditions": "Prerequisites",
            "test_steps": ["Step 1", "Step 2", "Step 3"],
            "expected_results": "Expected outcome",
            "postconditions": "Post-test state",
            "priority": "high|medium|low",
            "test_data": {{"data_type": "HL7", "sample_data": "example"}},
            "compliance_tags": ["FDA", "IEC 62304"]
        }}]
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert healthcare software test engineer with deep knowledge of medical device testing and regulatory compliance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                test_cases_data = json.loads(json_match.group())
                return test_cases_data
            else:
                return []
                
        except Exception as e:
            print(f"Error in test case generation: {str(e)}")
            return []
    
    def validate_test_case_coverage(self, requirement: Dict[str, Any], test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that generated test cases provide adequate coverage for the requirement.
        """
        prompt = f"""
        Analyze the test coverage for the following requirement and test cases:
        
        Requirement: {requirement.get('description', 'N/A')}
        Type: {requirement.get('type', 'N/A')}
        Regulatory Standards: {', '.join(requirement.get('regulatory_standards', []))}
        
        Test Cases:
        {json.dumps(test_cases, indent=2)}
        
        Evaluate:
        1. Coverage completeness (0-100%)
        2. Missing test scenarios
        3. Regulatory compliance coverage
        4. Risk coverage assessment
        5. Recommendations for improvement
        
        Return as JSON:
        {{
            "coverage_percentage": 85,
            "missing_scenarios": ["scenario1", "scenario2"],
            "compliance_coverage": {{"FDA": true, "IEC 62304": false}},
            "risk_coverage": "adequate|insufficient|comprehensive",
            "recommendations": ["recommendation1", "recommendation2"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a healthcare software quality assurance expert specializing in test coverage analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
                
        except Exception as e:
            print(f"Error in coverage validation: {str(e)}")
            return {}
    
    def identify_healthcare_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Identify healthcare-specific entities in the requirement text.
        """
        prompt = f"""
        Identify healthcare-specific entities in the following text:
        
        Text: {text}
        
        Extract:
        1. Medical procedures
        2. Patient data types
        3. Medical devices
        4. Healthcare standards/protocols
        5. Clinical workflows
        6. Data formats (HL7, FHIR, DICOM, etc.)
        7. Regulatory terms
        
        Return as JSON:
        {{
            "medical_procedures": ["procedure1", "procedure2"],
            "patient_data_types": ["data_type1", "data_type2"],
            "medical_devices": ["device1", "device2"],
            "healthcare_standards": ["standard1", "standard2"],
            "clinical_workflows": ["workflow1", "workflow2"],
            "data_formats": ["format1", "format2"],
            "regulatory_terms": ["term1", "term2"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a healthcare informatics expert with deep knowledge of medical terminology and healthcare data standards."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
                
        except Exception as e:
            print(f"Error in entity identification: {str(e)}")
            return {}


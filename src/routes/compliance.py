from flask import Blueprint, request, jsonify, current_app
from src.models.requirement import db, Requirement, TestCase, TraceabilityLink
from src.services.compliance_engine import ComplianceEngine
import json

compliance_bp = Blueprint('compliance', __name__)

# Initialize compliance engine
compliance_engine = ComplianceEngine()

@compliance_bp.route('/compliance/standards', methods=['GET'])
def get_compliance_standards():
    """Get information about supported compliance standards."""
    try:
        standards = compliance_engine.get_compliance_standards()
        return jsonify({
            'standards': standards,
            'total_standards': len(standards)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error fetching compliance standards: {str(e)}'}), 500

@compliance_bp.route('/compliance/assess-requirement/<int:req_id>', methods=['POST'])
def assess_requirement_compliance(req_id):
    """Assess compliance of a specific requirement."""
    try:
        requirement = Requirement.query.get_or_404(req_id)
        
        # Assess compliance
        compliance_results = compliance_engine.assess_requirement_compliance(requirement.to_dict())
        
        # Convert results to JSON-serializable format
        results_data = []
        for result in compliance_results:
            results_data.append({
                'rule_id': result.rule_id,
                'standard': result.standard,
                'compliance_level': result.compliance_level.value,
                'score': result.score,
                'findings': result.findings,
                'recommendations': result.recommendations,
                'evidence': result.evidence,
                'risk_assessment': result.risk_assessment.value
            })
        
        return jsonify({
            'requirement_id': requirement.requirement_id,
            'compliance_results': results_data,
            'total_assessments': len(results_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error assessing requirement compliance: {str(e)}'}), 500

@compliance_bp.route('/compliance/assess-test-case/<int:tc_id>', methods=['POST'])
def assess_test_case_compliance(tc_id):
    """Assess compliance of a specific test case."""
    try:
        test_case = TestCase.query.get_or_404(tc_id)
        
        # Get related requirement
        requirement = None
        if test_case.requirement_id:
            requirement = Requirement.query.get(test_case.requirement_id)
        
        # Assess compliance
        compliance_results = compliance_engine.assess_test_case_compliance(
            test_case.to_dict(), 
            requirement.to_dict() if requirement else None
        )
        
        # Convert results to JSON-serializable format
        results_data = []
        for result in compliance_results:
            results_data.append({
                'rule_id': result.rule_id,
                'standard': result.standard,
                'compliance_level': result.compliance_level.value,
                'score': result.score,
                'findings': result.findings,
                'recommendations': result.recommendations,
                'evidence': result.evidence,
                'risk_assessment': result.risk_assessment.value
            })
        
        return jsonify({
            'test_case_id': test_case.test_case_id,
            'compliance_results': results_data,
            'total_assessments': len(results_data),
            'related_requirement': requirement.requirement_id if requirement else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error assessing test case compliance: {str(e)}'}), 500

@compliance_bp.route('/compliance/generate-report', methods=['POST'])
def generate_compliance_report():
    """Generate a comprehensive compliance report for all requirements and test cases."""
    try:
        # Get filter parameters
        data = request.get_json() or {}
        requirement_ids = data.get('requirement_ids', [])
        test_case_ids = data.get('test_case_ids', [])
        standards_filter = data.get('standards', [])
        
        # Get requirements
        if requirement_ids:
            requirements = Requirement.query.filter(Requirement.id.in_(requirement_ids)).all()
        else:
            requirements = Requirement.query.all()
        
        # Get test cases
        if test_case_ids:
            test_cases = TestCase.query.filter(TestCase.id.in_(test_case_ids)).all()
        else:
            test_cases = TestCase.query.all()
        
        # Convert to dictionaries
        req_dicts = [req.to_dict() for req in requirements]
        tc_dicts = [tc.to_dict() for tc in test_cases]
        
        # Generate compliance report
        report = compliance_engine.generate_compliance_report(req_dicts, tc_dicts)
        
        # Filter by standards if specified
        if standards_filter:
            # Filter requirement compliance results
            filtered_req_compliance = []
            for req_comp in report['requirement_compliance']:
                filtered_results = [
                    result for result in req_comp['compliance_results']
                    if result['standard'] in standards_filter
                ]
                if filtered_results:
                    req_comp['compliance_results'] = filtered_results
                    filtered_req_compliance.append(req_comp)
            report['requirement_compliance'] = filtered_req_compliance
            
            # Filter test case compliance results
            filtered_tc_compliance = []
            for tc_comp in report['test_case_compliance']:
                filtered_results = [
                    result for result in tc_comp['compliance_results']
                    if result['standard'] in standards_filter
                ]
                if filtered_results:
                    tc_comp['compliance_results'] = filtered_results
                    filtered_tc_compliance.append(tc_comp)
            report['test_case_compliance'] = filtered_tc_compliance
            
            # Filter overall compliance
            filtered_overall = {
                standard: compliance for standard, compliance in report['overall_compliance'].items()
                if standard in standards_filter
            }
            report['overall_compliance'] = filtered_overall
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': f'Error generating compliance report: {str(e)}'}), 500

@compliance_bp.route('/traceability/matrix', methods=['GET'])
def get_traceability_matrix():
    """Get the complete traceability matrix."""
    try:
        # Get all requirements and test cases
        requirements = Requirement.query.all()
        test_cases = TestCase.query.all()
        traceability_links = TraceabilityLink.query.all()
        
        # Build traceability matrix
        matrix = {
            'requirements': [],
            'test_cases': [],
            'links': [],
            'coverage_analysis': {}
        }
        
        # Add requirements
        for req in requirements:
            matrix['requirements'].append({
                'id': req.id,
                'requirement_id': req.requirement_id,
                'title': req.title,
                'type': req.type,
                'priority': req.priority,
                'regulatory_standards': req.get_regulatory_standards()
            })
        
        # Add test cases
        for tc in test_cases:
            matrix['test_cases'].append({
                'id': tc.id,
                'test_case_id': tc.test_case_id,
                'title': tc.title,
                'priority': tc.priority,
                'requirement_id': tc.requirement_id,
                'compliance_tags': tc.get_compliance_tags()
            })
        
        # Add traceability links
        for link in traceability_links:
            matrix['links'].append({
                'id': link.id,
                'source_type': link.source_type,
                'source_id': link.source_id,
                'target_type': link.target_type,
                'target_id': link.target_id,
                'link_type': link.link_type,
                'created_at': link.created_at.isoformat()
            })
        
        # Calculate coverage analysis
        req_with_tests = set()
        tests_with_reqs = set()
        
        for link in traceability_links:
            if link.source_type == 'requirement' and link.target_type == 'test_case':
                req_with_tests.add(link.source_id)
                tests_with_reqs.add(link.target_id)
            elif link.source_type == 'test_case' and link.target_type == 'requirement':
                tests_with_reqs.add(link.source_id)
                req_with_tests.add(link.target_id)
        
        total_requirements = len(requirements)
        total_test_cases = len(test_cases)
        
        matrix['coverage_analysis'] = {
            'total_requirements': total_requirements,
            'requirements_with_tests': len(req_with_tests),
            'requirements_coverage_percentage': (len(req_with_tests) / total_requirements * 100) if total_requirements > 0 else 0,
            'total_test_cases': total_test_cases,
            'test_cases_with_requirements': len(tests_with_reqs),
            'test_cases_coverage_percentage': (len(tests_with_reqs) / total_test_cases * 100) if total_test_cases > 0 else 0,
            'orphaned_requirements': total_requirements - len(req_with_tests),
            'orphaned_test_cases': total_test_cases - len(tests_with_reqs)
        }
        
        return jsonify(matrix), 200
        
    except Exception as e:
        return jsonify({'error': f'Error generating traceability matrix: {str(e)}'}), 500

@compliance_bp.route('/traceability/create-link', methods=['POST'])
def create_traceability_link():
    """Create a new traceability link."""
    try:
        data = request.get_json()
        
        required_fields = ['source_type', 'source_id', 'target_type', 'target_id', 'link_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate source and target exist
        if data['source_type'] == 'requirement':
            source = Requirement.query.get(data['source_id'])
            if not source:
                return jsonify({'error': 'Source requirement not found'}), 404
        elif data['source_type'] == 'test_case':
            source = TestCase.query.get(data['source_id'])
            if not source:
                return jsonify({'error': 'Source test case not found'}), 404
        
        if data['target_type'] == 'requirement':
            target = Requirement.query.get(data['target_id'])
            if not target:
                return jsonify({'error': 'Target requirement not found'}), 404
        elif data['target_type'] == 'test_case':
            target = TestCase.query.get(data['target_id'])
            if not target:
                return jsonify({'error': 'Target test case not found'}), 404
        
        # Check if link already exists
        existing_link = TraceabilityLink.query.filter_by(
            source_type=data['source_type'],
            source_id=data['source_id'],
            target_type=data['target_type'],
            target_id=data['target_id'],
            link_type=data['link_type']
        ).first()
        
        if existing_link:
            return jsonify({'error': 'Traceability link already exists'}), 409
        
        # Create new traceability link
        new_link = TraceabilityLink(
            source_type=data['source_type'],
            source_id=data['source_id'],
            target_type=data['target_type'],
            target_id=data['target_id'],
            link_type=data['link_type']
        )
        
        db.session.add(new_link)
        db.session.commit()
        
        return jsonify({
            'message': 'Traceability link created successfully',
            'link': new_link.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error creating traceability link: {str(e)}'}), 500

@compliance_bp.route('/traceability/links/<int:link_id>', methods=['DELETE'])
def delete_traceability_link(link_id):
    """Delete a traceability link."""
    try:
        link = TraceabilityLink.query.get_or_404(link_id)
        
        db.session.delete(link)
        db.session.commit()
        
        return jsonify({
            'message': 'Traceability link deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting traceability link: {str(e)}'}), 500

@compliance_bp.route('/traceability/requirement/<int:req_id>/links', methods=['GET'])
def get_requirement_traceability_links(req_id):
    """Get all traceability links for a specific requirement."""
    try:
        requirement = Requirement.query.get_or_404(req_id)
        
        # Get links where this requirement is source or target
        links = TraceabilityLink.query.filter(
            ((TraceabilityLink.source_type == 'requirement') & (TraceabilityLink.source_id == req_id)) |
            ((TraceabilityLink.target_type == 'requirement') & (TraceabilityLink.target_id == req_id))
        ).all()
        
        # Get related test cases
        related_test_cases = []
        for link in links:
            if link.source_type == 'test_case' and link.target_type == 'requirement' and link.target_id == req_id:
                tc = TestCase.query.get(link.source_id)
                if tc:
                    related_test_cases.append(tc.to_dict())
            elif link.target_type == 'test_case' and link.source_type == 'requirement' and link.source_id == req_id:
                tc = TestCase.query.get(link.target_id)
                if tc:
                    related_test_cases.append(tc.to_dict())
        
        return jsonify({
            'requirement': requirement.to_dict(),
            'traceability_links': [link.to_dict() for link in links],
            'related_test_cases': related_test_cases,
            'total_links': len(links)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching requirement traceability: {str(e)}'}), 500

@compliance_bp.route('/traceability/test-case/<int:tc_id>/links', methods=['GET'])
def get_test_case_traceability_links(tc_id):
    """Get all traceability links for a specific test case."""
    try:
        test_case = TestCase.query.get_or_404(tc_id)
        
        # Get links where this test case is source or target
        links = TraceabilityLink.query.filter(
            ((TraceabilityLink.source_type == 'test_case') & (TraceabilityLink.source_id == tc_id)) |
            ((TraceabilityLink.target_type == 'test_case') & (TraceabilityLink.target_id == tc_id))
        ).all()
        
        # Get related requirements
        related_requirements = []
        for link in links:
            if link.source_type == 'requirement' and link.target_type == 'test_case' and link.target_id == tc_id:
                req = Requirement.query.get(link.source_id)
                if req:
                    related_requirements.append(req.to_dict())
            elif link.target_type == 'requirement' and link.source_type == 'test_case' and link.source_id == tc_id:
                req = Requirement.query.get(link.target_id)
                if req:
                    related_requirements.append(req.to_dict())
        
        return jsonify({
            'test_case': test_case.to_dict(),
            'traceability_links': [link.to_dict() for link in links],
            'related_requirements': related_requirements,
            'total_links': len(links)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching test case traceability: {str(e)}'}), 500

@compliance_bp.route('/compliance/validate-coverage', methods=['POST'])
def validate_test_coverage():
    """Validate test coverage for compliance requirements."""
    try:
        data = request.get_json() or {}
        standard = data.get('standard')
        
        # Get all requirements and test cases
        requirements = Requirement.query.all()
        test_cases = TestCase.query.all()
        
        coverage_report = {
            'standard': standard,
            'total_requirements': len(requirements),
            'total_test_cases': len(test_cases),
            'coverage_gaps': [],
            'recommendations': []
        }
        
        # Analyze coverage for each requirement
        for req in requirements:
            req_dict = req.to_dict()
            
            # Check if requirement is relevant to the standard
            if standard and standard not in req.get_regulatory_standards():
                continue
            
            # Get test cases for this requirement
            related_test_cases = TestCase.query.filter_by(requirement_id=req.id).all()
            
            if not related_test_cases:
                coverage_report['coverage_gaps'].append({
                    'requirement_id': req.requirement_id,
                    'title': req.title,
                    'issue': 'No test cases found',
                    'recommendation': 'Create test cases to verify this requirement'
                })
                continue
            
            # Assess compliance of test cases
            for tc in related_test_cases:
                compliance_results = compliance_engine.assess_test_case_compliance(tc.to_dict(), req_dict)
                
                # Check for compliance gaps
                for result in compliance_results:
                    if standard and result.standard != standard:
                        continue
                    
                    if result.compliance_level.value in ['non_compliant', 'partially_compliant']:
                        coverage_report['coverage_gaps'].append({
                            'requirement_id': req.requirement_id,
                            'test_case_id': tc.test_case_id,
                            'standard': result.standard,
                            'compliance_level': result.compliance_level.value,
                            'issue': ', '.join(result.findings),
                            'recommendation': ', '.join(result.recommendations)
                        })
        
        # Generate overall recommendations
        if coverage_report['coverage_gaps']:
            coverage_report['recommendations'] = [
                'Review and enhance test cases for requirements with compliance gaps',
                'Ensure all regulatory requirements have adequate test coverage',
                'Consider adding specific compliance verification steps to test cases'
            ]
        else:
            coverage_report['recommendations'] = [
                'Test coverage appears adequate for compliance requirements',
                'Continue monitoring and updating test cases as requirements evolve'
            ]
        
        return jsonify(coverage_report), 200
        
    except Exception as e:
        return jsonify({'error': f'Error validating test coverage: {str(e)}'}), 500


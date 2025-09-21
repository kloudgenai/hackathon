from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import tempfile
from src.models.requirement import db, Requirement, TestCase, TraceabilityLink
from src.services.ai_processor import AIProcessor
from src.services.document_parser import DocumentParser

requirements_bp = Blueprint('requirements', __name__)

# Initialize services
ai_processor = AIProcessor()
document_parser = DocumentParser()

@requirements_bp.route('/upload', methods=['POST'])
def upload_requirements_document():
    """Upload and process a requirements document."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not document_parser.is_supported_format(file.filename):
            return jsonify({
                'error': f'Unsupported file format. Supported formats: {document_parser.get_supported_formats()}'
            }), 400
        
        # Parse the document
        file_content = file.read()
        parsed_result = document_parser.parse_document(file.filename, file_content)
        
        if 'error' in parsed_result:
            return jsonify({'error': parsed_result['error']}), 400
        
        # Extract requirements using AI
        requirements_data = ai_processor.extract_requirements_from_text(
            parsed_result['content'], 
            source_document=file.filename
        )
        
        # Save requirements to database
        saved_requirements = []
        for req_data in requirements_data:
            requirement = Requirement(
                requirement_id=req_data.get('requirement_id', f'REQ-{len(saved_requirements)+1:03d}'),
                title=req_data.get('title', 'Untitled Requirement'),
                description=req_data.get('description', ''),
                type=req_data.get('type', 'functional'),
                priority=req_data.get('priority', 'medium'),
                source_document=file.filename
            )
            requirement.set_regulatory_standards(req_data.get('regulatory_standards', []))
            
            db.session.add(requirement)
            db.session.flush()  # Get the ID
            saved_requirements.append(requirement.to_dict())
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully processed {len(saved_requirements)} requirements',
            'requirements': saved_requirements,
            'document_metadata': parsed_result.get('metadata', {})
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error processing document: {str(e)}'}), 500

@requirements_bp.route('/requirements', methods=['GET'])
def get_requirements():
    """Get all requirements with optional filtering."""
    try:
        # Query parameters
        req_type = request.args.get('type')
        priority = request.args.get('priority')
        source_document = request.args.get('source_document')
        
        # Build query
        query = Requirement.query
        
        if req_type:
            query = query.filter(Requirement.type == req_type)
        if priority:
            query = query.filter(Requirement.priority == priority)
        if source_document:
            query = query.filter(Requirement.source_document == source_document)
        
        requirements = query.all()
        
        return jsonify({
            'requirements': [req.to_dict() for req in requirements],
            'total': len(requirements)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching requirements: {str(e)}'}), 500

@requirements_bp.route('/requirements/<int:req_id>', methods=['GET'])
def get_requirement(req_id):
    """Get a specific requirement by ID."""
    try:
        requirement = Requirement.query.get_or_404(req_id)
        return jsonify(requirement.to_dict()), 200
    except Exception as e:
        return jsonify({'error': f'Error fetching requirement: {str(e)}'}), 500

@requirements_bp.route('/requirements/<int:req_id>/generate-tests', methods=['POST'])
def generate_test_cases(req_id):
    """Generate test cases for a specific requirement."""
    try:
        requirement = Requirement.query.get_or_404(req_id)
        
        # Generate test cases using AI
        test_cases_data = ai_processor.generate_test_cases(requirement.to_dict())
        
        # Save test cases to database
        saved_test_cases = []
        for tc_data in test_cases_data:
            test_case = TestCase(
                test_case_id=tc_data.get('test_case_id', f'TC-{req_id}-{len(saved_test_cases)+1:03d}'),
                title=tc_data.get('title', 'Untitled Test Case'),
                description=tc_data.get('description', ''),
                preconditions=tc_data.get('preconditions', ''),
                expected_results=tc_data.get('expected_results', ''),
                postconditions=tc_data.get('postconditions', ''),
                priority=tc_data.get('priority', 'medium'),
                requirement_id=requirement.id
            )
            
            test_case.set_test_steps(tc_data.get('test_steps', []))
            test_case.set_test_data(tc_data.get('test_data', {}))
            test_case.set_compliance_tags(tc_data.get('compliance_tags', []))
            
            db.session.add(test_case)
            db.session.flush()
            
            # Create traceability link
            traceability_link = TraceabilityLink(
                source_type='requirement',
                source_id=requirement.id,
                target_type='test_case',
                target_id=test_case.id,
                link_type='covers'
            )
            db.session.add(traceability_link)
            
            saved_test_cases.append(test_case.to_dict())
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully generated {len(saved_test_cases)} test cases',
            'test_cases': saved_test_cases
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error generating test cases: {str(e)}'}), 500

@requirements_bp.route('/requirements/<int:req_id>/test-cases', methods=['GET'])
def get_requirement_test_cases(req_id):
    """Get all test cases for a specific requirement."""
    try:
        requirement = Requirement.query.get_or_404(req_id)
        test_cases = TestCase.query.filter_by(requirement_id=req_id).all()
        
        return jsonify({
            'requirement': requirement.to_dict(),
            'test_cases': [tc.to_dict() for tc in test_cases],
            'total_test_cases': len(test_cases)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching test cases: {str(e)}'}), 500

@requirements_bp.route('/test-cases', methods=['GET'])
def get_all_test_cases():
    """Get all test cases with optional filtering."""
    try:
        priority = request.args.get('priority')
        requirement_id = request.args.get('requirement_id')
        
        query = TestCase.query
        
        if priority:
            query = query.filter(TestCase.priority == priority)
        if requirement_id:
            query = query.filter(TestCase.requirement_id == requirement_id)
        
        test_cases = query.all()
        
        return jsonify({
            'test_cases': [tc.to_dict() for tc in test_cases],
            'total': len(test_cases)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching test cases: {str(e)}'}), 500

@requirements_bp.route('/test-cases/<int:tc_id>', methods=['GET'])
def get_test_case(tc_id):
    """Get a specific test case by ID."""
    try:
        test_case = TestCase.query.get_or_404(tc_id)
        return jsonify(test_case.to_dict()), 200
    except Exception as e:
        return jsonify({'error': f'Error fetching test case: {str(e)}'}), 500

@requirements_bp.route('/analyze-compliance/<int:req_id>', methods=['POST'])
def analyze_requirement_compliance(req_id):
    """Analyze compliance for a specific requirement."""
    try:
        requirement = Requirement.query.get_or_404(req_id)
        
        # Analyze compliance using AI
        compliance_analysis = ai_processor.analyze_requirement_compliance(requirement.description)
        
        return jsonify({
            'requirement_id': requirement.requirement_id,
            'compliance_analysis': compliance_analysis
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing compliance: {str(e)}'}), 500

@requirements_bp.route('/traceability/<int:req_id>', methods=['GET'])
def get_requirement_traceability(req_id):
    """Get traceability information for a requirement."""
    try:
        requirement = Requirement.query.get_or_404(req_id)
        
        # Get all traceability links for this requirement
        links = TraceabilityLink.query.filter(
            (TraceabilityLink.source_id == req_id) | 
            (TraceabilityLink.target_id == req_id)
        ).all()
        
        return jsonify({
            'requirement': requirement.to_dict(),
            'traceability_links': [link.to_dict() for link in links]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching traceability: {str(e)}'}), 500

@requirements_bp.route('/coverage-analysis/<int:req_id>', methods=['POST'])
def analyze_test_coverage(req_id):
    """Analyze test coverage for a requirement."""
    try:
        requirement = Requirement.query.get_or_404(req_id)
        test_cases = TestCase.query.filter_by(requirement_id=req_id).all()
        
        if not test_cases:
            return jsonify({'error': 'No test cases found for this requirement'}), 404
        
        # Analyze coverage using AI
        test_cases_data = [tc.to_dict() for tc in test_cases]
        coverage_analysis = ai_processor.validate_test_case_coverage(
            requirement.to_dict(), 
            test_cases_data
        )
        
        return jsonify({
            'requirement_id': requirement.requirement_id,
            'test_cases_count': len(test_cases),
            'coverage_analysis': coverage_analysis
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing coverage: {str(e)}'}), 500

@requirements_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Test Case Generator',
        'supported_formats': document_parser.get_supported_formats()
    }), 200


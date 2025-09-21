from flask import Blueprint, request, jsonify, current_app
from src.services.alm_integrations import ALMIntegrationFactory
from src.models.requirement import db, Requirement, TestCase
import json

integrations_bp = Blueprint('integrations', __name__)

# Store ALM configurations (in production, this should be in a secure database)
alm_configurations = {}

@integrations_bp.route('/alm/configure', methods=['POST'])
def configure_alm_integration():
    """Configure ALM platform integration."""
    try:
        data = request.get_json()
        
        required_fields = ['platform', 'base_url', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        platform = data['platform'].lower()
        if platform not in ['jira', 'azure_devops', 'azuredevops', 'azure', 'polarion']:
            return jsonify({'error': f'Unsupported platform: {platform}'}), 400
        
        # Store configuration (in production, encrypt sensitive data)
        config_id = f"{platform}_{data.get('project_key', 'default')}"
        alm_configurations[config_id] = {
            'platform': platform,
            'base_url': data['base_url'],
            'username': data['username'],
            'password': data['password'],  # Should be encrypted in production
            'project_key': data.get('project_key'),
            'enabled': True
        }
        
        # Test the connection
        try:
            integration = ALMIntegrationFactory.create_integration(
                platform=platform,
                base_url=data['base_url'],
                username=data['username'],
                password=data['password'],
                project_key=data.get('project_key')
            )
            
            # Try to get requirements to test connection
            test_requirements = integration.get_requirements()
            connection_status = 'success'
            
        except Exception as e:
            connection_status = f'connection_failed: {str(e)}'
        
        return jsonify({
            'message': 'ALM integration configured successfully',
            'config_id': config_id,
            'connection_status': connection_status,
            'platform': platform
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error configuring ALM integration: {str(e)}'}), 500

@integrations_bp.route('/alm/configurations', methods=['GET'])
def get_alm_configurations():
    """Get all configured ALM integrations."""
    try:
        # Return configurations without sensitive data
        safe_configs = {}
        for config_id, config in alm_configurations.items():
            safe_configs[config_id] = {
                'platform': config['platform'],
                'base_url': config['base_url'],
                'username': config['username'],
                'project_key': config.get('project_key'),
                'enabled': config.get('enabled', True)
            }
        
        return jsonify({
            'configurations': safe_configs,
            'total': len(safe_configs)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching ALM configurations: {str(e)}'}), 500

@integrations_bp.route('/alm/<config_id>/sync-requirements', methods=['POST'])
def sync_requirements_from_alm(config_id):
    """Sync requirements from ALM platform to local database."""
    try:
        if config_id not in alm_configurations:
            return jsonify({'error': 'ALM configuration not found'}), 404
        
        config = alm_configurations[config_id]
        
        # Create ALM integration instance
        integration = ALMIntegrationFactory.create_integration(
            platform=config['platform'],
            base_url=config['base_url'],
            username=config['username'],
            password=config['password'],
            project_key=config.get('project_key')
        )
        
        # Get requirements from ALM platform
        alm_requirements = integration.get_requirements()
        
        # Sync to local database
        synced_count = 0
        for alm_req in alm_requirements:
            # Check if requirement already exists
            existing_req = Requirement.query.filter_by(requirement_id=alm_req['id']).first()
            
            if existing_req:
                # Update existing requirement
                existing_req.title = alm_req['title']
                existing_req.description = alm_req['description']
                existing_req.priority = alm_req.get('priority', 'medium')
                existing_req.source_document = f"ALM_{config['platform']}"
                if 'tags' in alm_req:
                    existing_req.set_regulatory_standards(alm_req['tags'])
            else:
                # Create new requirement
                new_req = Requirement(
                    requirement_id=alm_req['id'],
                    title=alm_req['title'],
                    description=alm_req['description'],
                    type='functional',  # Default type
                    priority=alm_req.get('priority', 'medium'),
                    source_document=f"ALM_{config['platform']}"
                )
                if 'tags' in alm_req:
                    new_req.set_regulatory_standards(alm_req['tags'])
                
                db.session.add(new_req)
            
            synced_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully synced {synced_count} requirements from {config["platform"]}',
            'synced_count': synced_count,
            'platform': config['platform']
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error syncing requirements: {str(e)}'}), 500

@integrations_bp.route('/alm/<config_id>/sync-test-cases', methods=['POST'])
def sync_test_cases_from_alm(config_id):
    """Sync test cases from ALM platform to local database."""
    try:
        if config_id not in alm_configurations:
            return jsonify({'error': 'ALM configuration not found'}), 404
        
        config = alm_configurations[config_id]
        
        # Create ALM integration instance
        integration = ALMIntegrationFactory.create_integration(
            platform=config['platform'],
            base_url=config['base_url'],
            username=config['username'],
            password=config['password'],
            project_key=config.get('project_key')
        )
        
        # Get test cases from ALM platform
        alm_test_cases = integration.get_test_cases()
        
        # Sync to local database
        synced_count = 0
        for alm_tc in alm_test_cases:
            # Check if test case already exists
            existing_tc = TestCase.query.filter_by(test_case_id=alm_tc['id']).first()
            
            if existing_tc:
                # Update existing test case
                existing_tc.title = alm_tc['title']
                existing_tc.description = alm_tc['description']
                existing_tc.priority = alm_tc.get('priority', 'medium')
                if 'tags' in alm_tc:
                    existing_tc.set_compliance_tags(alm_tc['tags'])
            else:
                # Create new test case (need to find or create a requirement to link to)
                # For now, create without requirement link
                new_tc = TestCase(
                    test_case_id=alm_tc['id'],
                    title=alm_tc['title'],
                    description=alm_tc['description'],
                    preconditions='',
                    expected_results='',
                    postconditions='',
                    priority=alm_tc.get('priority', 'medium'),
                    requirement_id=1  # Placeholder - should be properly linked
                )
                new_tc.set_test_steps([])
                new_tc.set_test_data({})
                if 'tags' in alm_tc:
                    new_tc.set_compliance_tags(alm_tc['tags'])
                
                db.session.add(new_tc)
            
            synced_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully synced {synced_count} test cases from {config["platform"]}',
            'synced_count': synced_count,
            'platform': config['platform']
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error syncing test cases: {str(e)}'}), 500

@integrations_bp.route('/alm/<config_id>/export-requirement/<int:req_id>', methods=['POST'])
def export_requirement_to_alm(config_id, req_id):
    """Export a requirement from local database to ALM platform."""
    try:
        if config_id not in alm_configurations:
            return jsonify({'error': 'ALM configuration not found'}), 404
        
        requirement = Requirement.query.get_or_404(req_id)
        config = alm_configurations[config_id]
        
        # Create ALM integration instance
        integration = ALMIntegrationFactory.create_integration(
            platform=config['platform'],
            base_url=config['base_url'],
            username=config['username'],
            password=config['password'],
            project_key=config.get('project_key')
        )
        
        # Export requirement to ALM platform
        result = integration.create_requirement(requirement.to_dict())
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'message': f'Successfully exported requirement to {config["platform"]}',
            'alm_result': result,
            'requirement_id': requirement.requirement_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error exporting requirement: {str(e)}'}), 500

@integrations_bp.route('/alm/<config_id>/export-test-case/<int:tc_id>', methods=['POST'])
def export_test_case_to_alm(config_id, tc_id):
    """Export a test case from local database to ALM platform."""
    try:
        if config_id not in alm_configurations:
            return jsonify({'error': 'ALM configuration not found'}), 404
        
        test_case = TestCase.query.get_or_404(tc_id)
        config = alm_configurations[config_id]
        
        # Create ALM integration instance
        integration = ALMIntegrationFactory.create_integration(
            platform=config['platform'],
            base_url=config['base_url'],
            username=config['username'],
            password=config['password'],
            project_key=config.get('project_key')
        )
        
        # Export test case to ALM platform
        result = integration.create_test_case(test_case.to_dict())
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'message': f'Successfully exported test case to {config["platform"]}',
            'alm_result': result,
            'test_case_id': test_case.test_case_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error exporting test case: {str(e)}'}), 500

@integrations_bp.route('/alm/<config_id>/export-all', methods=['POST'])
def export_all_to_alm(config_id):
    """Export all requirements and test cases to ALM platform."""
    try:
        if config_id not in alm_configurations:
            return jsonify({'error': 'ALM configuration not found'}), 404
        
        config = alm_configurations[config_id]
        
        # Create ALM integration instance
        integration = ALMIntegrationFactory.create_integration(
            platform=config['platform'],
            base_url=config['base_url'],
            username=config['username'],
            password=config['password'],
            project_key=config.get('project_key')
        )
        
        # Export all requirements
        requirements = Requirement.query.all()
        exported_requirements = 0
        requirement_errors = []
        
        for req in requirements:
            try:
                result = integration.create_requirement(req.to_dict())
                if 'error' not in result:
                    exported_requirements += 1
                else:
                    requirement_errors.append(f"REQ {req.requirement_id}: {result['error']}")
            except Exception as e:
                requirement_errors.append(f"REQ {req.requirement_id}: {str(e)}")
        
        # Export all test cases
        test_cases = TestCase.query.all()
        exported_test_cases = 0
        test_case_errors = []
        
        for tc in test_cases:
            try:
                result = integration.create_test_case(tc.to_dict())
                if 'error' not in result:
                    exported_test_cases += 1
                else:
                    test_case_errors.append(f"TC {tc.test_case_id}: {result['error']}")
            except Exception as e:
                test_case_errors.append(f"TC {tc.test_case_id}: {str(e)}")
        
        return jsonify({
            'message': f'Export completed to {config["platform"]}',
            'exported_requirements': exported_requirements,
            'exported_test_cases': exported_test_cases,
            'requirement_errors': requirement_errors,
            'test_case_errors': test_case_errors,
            'platform': config['platform']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error during bulk export: {str(e)}'}), 500

@integrations_bp.route('/alm/<config_id>/test-connection', methods=['POST'])
def test_alm_connection(config_id):
    """Test connection to ALM platform."""
    try:
        if config_id not in alm_configurations:
            return jsonify({'error': 'ALM configuration not found'}), 404
        
        config = alm_configurations[config_id]
        
        # Create ALM integration instance
        integration = ALMIntegrationFactory.create_integration(
            platform=config['platform'],
            base_url=config['base_url'],
            username=config['username'],
            password=config['password'],
            project_key=config.get('project_key')
        )
        
        # Test connection by trying to get requirements
        requirements = integration.get_requirements()
        test_cases = integration.get_test_cases()
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully connected to {config["platform"]}',
            'requirements_count': len(requirements),
            'test_cases_count': len(test_cases),
            'platform': config['platform']
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'failed',
            'error': f'Connection test failed: {str(e)}',
            'platform': config.get('platform', 'unknown')
        }), 500

@integrations_bp.route('/alm/<config_id>/disable', methods=['POST'])
def disable_alm_integration(config_id):
    """Disable ALM integration."""
    try:
        if config_id not in alm_configurations:
            return jsonify({'error': 'ALM configuration not found'}), 404
        
        alm_configurations[config_id]['enabled'] = False
        
        return jsonify({
            'message': f'ALM integration {config_id} disabled successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error disabling ALM integration: {str(e)}'}), 500

@integrations_bp.route('/alm/<config_id>/enable', methods=['POST'])
def enable_alm_integration(config_id):
    """Enable ALM integration."""
    try:
        if config_id not in alm_configurations:
            return jsonify({'error': 'ALM configuration not found'}), 404
        
        alm_configurations[config_id]['enabled'] = True
        
        return jsonify({
            'message': f'ALM integration {config_id} enabled successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error enabling ALM integration: {str(e)}'}), 500

@integrations_bp.route('/alm/supported-platforms', methods=['GET'])
def get_supported_platforms():
    """Get list of supported ALM platforms."""
    return jsonify({
        'supported_platforms': [
            {
                'id': 'jira',
                'name': 'Atlassian Jira',
                'description': 'Popular issue tracking and project management tool'
            },
            {
                'id': 'azure_devops',
                'name': 'Microsoft Azure DevOps',
                'description': 'Comprehensive DevOps platform with work item tracking'
            },
            {
                'id': 'polarion',
                'name': 'Siemens Polarion ALM',
                'description': 'Enterprise Application Lifecycle Management platform'
            }
        ]
    }), 200


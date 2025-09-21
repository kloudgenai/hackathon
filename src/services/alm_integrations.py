import json
import requests
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import base64
from urllib.parse import urljoin

class ALMIntegration(ABC):
    """
    Abstract base class for Application Lifecycle Management (ALM) platform integrations.
    """
    
    def __init__(self, base_url: str, username: str, password: str, project_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.project_key = project_key
        self.session = requests.Session()
        self._setup_authentication()
    
    @abstractmethod
    def _setup_authentication(self):
        """Setup authentication for the ALM platform."""
        pass
    
    @abstractmethod
    def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a requirement in the ALM platform."""
        pass
    
    @abstractmethod
    def create_test_case(self, test_case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test case in the ALM platform."""
        pass
    
    @abstractmethod
    def link_requirement_to_test_case(self, requirement_id: str, test_case_id: str) -> bool:
        """Create a traceability link between requirement and test case."""
        pass
    
    @abstractmethod
    def get_requirements(self) -> List[Dict[str, Any]]:
        """Get all requirements from the ALM platform."""
        pass
    
    @abstractmethod
    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases from the ALM platform."""
        pass


class JiraIntegration(ALMIntegration):
    """
    Integration with Atlassian Jira for requirements and test case management.
    """
    
    def _setup_authentication(self):
        """Setup basic authentication for Jira."""
        auth_string = f"{self.username}:{self.password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.session.headers.update({
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a requirement as a Jira issue."""
        url = f"{self.base_url}/rest/api/2/issue"
        
        jira_issue = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": requirement_data.get('title', 'Untitled Requirement'),
                "description": requirement_data.get('description', ''),
                "issuetype": {"name": "Story"},  # or "Requirement" if custom issue type exists
                "priority": {"name": self._map_priority(requirement_data.get('priority', 'medium'))},
                "labels": requirement_data.get('regulatory_standards', [])
            }
        }
        
        # Add custom fields if available
        if 'requirement_id' in requirement_data:
            # Assuming a custom field for requirement ID exists
            jira_issue["fields"]["customfield_10001"] = requirement_data['requirement_id']
        
        try:
            response = self.session.post(url, json=jira_issue)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to create requirement in Jira: {str(e)}"}
    
    def create_test_case(self, test_case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test case as a Jira issue."""
        url = f"{self.base_url}/rest/api/2/issue"
        
        # Format test steps for Jira description
        test_steps = test_case_data.get('test_steps', [])
        formatted_steps = "\\n".join([f"{i+1}. {step}" for i, step in enumerate(test_steps)])
        
        description = f"""
        {test_case_data.get('description', '')}
        
        *Preconditions:*
        {test_case_data.get('preconditions', 'None')}
        
        *Test Steps:*
        {formatted_steps}
        
        *Expected Results:*
        {test_case_data.get('expected_results', '')}
        
        *Postconditions:*
        {test_case_data.get('postconditions', 'None')}
        """
        
        jira_issue = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": test_case_data.get('title', 'Untitled Test Case'),
                "description": description.strip(),
                "issuetype": {"name": "Test"},  # or "Test Case" if custom issue type exists
                "priority": {"name": self._map_priority(test_case_data.get('priority', 'medium'))},
                "labels": test_case_data.get('compliance_tags', [])
            }
        }
        
        try:
            response = self.session.post(url, json=jira_issue)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to create test case in Jira: {str(e)}"}
    
    def link_requirement_to_test_case(self, requirement_id: str, test_case_id: str) -> bool:
        """Create an issue link between requirement and test case."""
        url = f"{self.base_url}/rest/api/2/issueLink"
        
        link_data = {
            "type": {"name": "Tests"},  # Link type - may need to be configured in Jira
            "inwardIssue": {"key": test_case_id},
            "outwardIssue": {"key": requirement_id}
        }
        
        try:
            response = self.session.post(url, json=link_data)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to link requirement to test case in Jira: {str(e)}")
            return False
    
    def get_requirements(self) -> List[Dict[str, Any]]:
        """Get all requirements (stories) from Jira project."""
        url = f"{self.base_url}/rest/api/2/search"
        
        jql = f"project = {self.project_key} AND issuetype = Story"
        params = {
            "jql": jql,
            "maxResults": 1000,
            "fields": "summary,description,priority,labels,status,created,updated"
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            requirements = []
            for issue in data.get('issues', []):
                requirements.append({
                    'id': issue['key'],
                    'title': issue['fields']['summary'],
                    'description': issue['fields']['description'] or '',
                    'priority': issue['fields']['priority']['name'].lower(),
                    'status': issue['fields']['status']['name'],
                    'labels': issue['fields']['labels'],
                    'created': issue['fields']['created'],
                    'updated': issue['fields']['updated']
                })
            
            return requirements
        except requests.exceptions.RequestException as e:
            return []
    
    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases from Jira project."""
        url = f"{self.base_url}/rest/api/2/search"
        
        jql = f"project = {self.project_key} AND issuetype = Test"
        params = {
            "jql": jql,
            "maxResults": 1000,
            "fields": "summary,description,priority,labels,status,created,updated"
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            test_cases = []
            for issue in data.get('issues', []):
                test_cases.append({
                    'id': issue['key'],
                    'title': issue['fields']['summary'],
                    'description': issue['fields']['description'] or '',
                    'priority': issue['fields']['priority']['name'].lower(),
                    'status': issue['fields']['status']['name'],
                    'labels': issue['fields']['labels'],
                    'created': issue['fields']['created'],
                    'updated': issue['fields']['updated']
                })
            
            return test_cases
        except requests.exceptions.RequestException as e:
            return []
    
    def _map_priority(self, priority: str) -> str:
        """Map internal priority to Jira priority."""
        priority_mapping = {
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low'
        }
        return priority_mapping.get(priority.lower(), 'Medium')


class AzureDevOpsIntegration(ALMIntegration):
    """
    Integration with Microsoft Azure DevOps for requirements and test case management.
    """
    
    def _setup_authentication(self):
        """Setup authentication for Azure DevOps (using Personal Access Token)."""
        # For Azure DevOps, password should be a Personal Access Token
        auth_string = f":{self.password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.session.headers.update({
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a requirement as a work item in Azure DevOps."""
        url = f"{self.base_url}/{self.project_key}/_apis/wit/workitems/$User Story?api-version=6.0"
        
        work_item = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": requirement_data.get('title', 'Untitled Requirement')
            },
            {
                "op": "add",
                "path": "/fields/System.Description",
                "value": requirement_data.get('description', '')
            },
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Priority",
                "value": self._map_priority_to_number(requirement_data.get('priority', 'medium'))
            }
        ]
        
        # Add tags for regulatory standards
        if requirement_data.get('regulatory_standards'):
            tags = "; ".join(requirement_data['regulatory_standards'])
            work_item.append({
                "op": "add",
                "path": "/fields/System.Tags",
                "value": tags
            })
        
        try:
            self.session.headers['Content-Type'] = 'application/json-patch+json'
            response = self.session.post(url, json=work_item)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to create requirement in Azure DevOps: {str(e)}"}
        finally:
            self.session.headers['Content-Type'] = 'application/json'
    
    def create_test_case(self, test_case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test case as a work item in Azure DevOps."""
        url = f"{self.base_url}/{self.project_key}/_apis/wit/workitems/$Test Case?api-version=6.0"
        
        # Format test steps for Azure DevOps
        test_steps = test_case_data.get('test_steps', [])
        formatted_steps = "<steps>"
        for i, step in enumerate(test_steps):
            formatted_steps += f"<step id='{i+1}' type='ActionStep'><parameterizedString isformatted='true'><DIV><P>{step}</P></DIV></parameterizedString><parameterizedString isformatted='true'><DIV><P>Expected result for step {i+1}</P></DIV></parameterizedString><description/></step>"
        formatted_steps += "</steps>"
        
        work_item = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": test_case_data.get('title', 'Untitled Test Case')
            },
            {
                "op": "add",
                "path": "/fields/System.Description",
                "value": test_case_data.get('description', '')
            },
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.TCM.Steps",
                "value": formatted_steps
            },
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Priority",
                "value": self._map_priority_to_number(test_case_data.get('priority', 'medium'))
            }
        ]
        
        # Add tags for compliance
        if test_case_data.get('compliance_tags'):
            tags = "; ".join(test_case_data['compliance_tags'])
            work_item.append({
                "op": "add",
                "path": "/fields/System.Tags",
                "value": tags
            })
        
        try:
            self.session.headers['Content-Type'] = 'application/json-patch+json'
            response = self.session.post(url, json=work_item)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to create test case in Azure DevOps: {str(e)}"}
        finally:
            self.session.headers['Content-Type'] = 'application/json'
    
    def link_requirement_to_test_case(self, requirement_id: str, test_case_id: str) -> bool:
        """Create a work item link between requirement and test case."""
        url = f"{self.base_url}/{self.project_key}/_apis/wit/workitems/{test_case_id}?api-version=6.0"
        
        link_data = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "Microsoft.VSTS.Common.TestedBy-Reverse",
                    "url": f"{self.base_url}/{self.project_key}/_apis/wit/workItems/{requirement_id}"
                }
            }
        ]
        
        try:
            self.session.headers['Content-Type'] = 'application/json-patch+json'
            response = self.session.patch(url, json=link_data)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to link requirement to test case in Azure DevOps: {str(e)}")
            return False
        finally:
            self.session.headers['Content-Type'] = 'application/json'
    
    def get_requirements(self) -> List[Dict[str, Any]]:
        """Get all requirements (user stories) from Azure DevOps project."""
        url = f"{self.base_url}/{self.project_key}/_apis/wit/wiql?api-version=6.0"
        
        wiql_query = {
            "query": f"SELECT [System.Id], [System.Title], [System.Description], [Microsoft.VSTS.Common.Priority], [System.Tags], [System.State], [System.CreatedDate], [System.ChangedDate] FROM WorkItems WHERE [System.TeamProject] = '{self.project_key}' AND [System.WorkItemType] = 'User Story'"
        }
        
        try:
            response = self.session.post(url, json=wiql_query)
            response.raise_for_status()
            query_result = response.json()
            
            requirements = []
            for work_item in query_result.get('workItems', []):
                # Get detailed work item information
                item_url = f"{self.base_url}/{self.project_key}/_apis/wit/workitems/{work_item['id']}?api-version=6.0"
                item_response = self.session.get(item_url)
                if item_response.status_code == 200:
                    item_data = item_response.json()
                    fields = item_data.get('fields', {})
                    
                    requirements.append({
                        'id': str(work_item['id']),
                        'title': fields.get('System.Title', ''),
                        'description': fields.get('System.Description', ''),
                        'priority': self._map_number_to_priority(fields.get('Microsoft.VSTS.Common.Priority', 2)),
                        'status': fields.get('System.State', ''),
                        'tags': fields.get('System.Tags', '').split('; ') if fields.get('System.Tags') else [],
                        'created': fields.get('System.CreatedDate', ''),
                        'updated': fields.get('System.ChangedDate', '')
                    })
            
            return requirements
        except requests.exceptions.RequestException as e:
            return []
    
    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases from Azure DevOps project."""
        url = f"{self.base_url}/{self.project_key}/_apis/wit/wiql?api-version=6.0"
        
        wiql_query = {
            "query": f"SELECT [System.Id], [System.Title], [System.Description], [Microsoft.VSTS.Common.Priority], [System.Tags], [System.State], [System.CreatedDate], [System.ChangedDate] FROM WorkItems WHERE [System.TeamProject] = '{self.project_key}' AND [System.WorkItemType] = 'Test Case'"
        }
        
        try:
            response = self.session.post(url, json=wiql_query)
            response.raise_for_status()
            query_result = response.json()
            
            test_cases = []
            for work_item in query_result.get('workItems', []):
                # Get detailed work item information
                item_url = f"{self.base_url}/{self.project_key}/_apis/wit/workitems/{work_item['id']}?api-version=6.0"
                item_response = self.session.get(item_url)
                if item_response.status_code == 200:
                    item_data = item_response.json()
                    fields = item_data.get('fields', {})
                    
                    test_cases.append({
                        'id': str(work_item['id']),
                        'title': fields.get('System.Title', ''),
                        'description': fields.get('System.Description', ''),
                        'priority': self._map_number_to_priority(fields.get('Microsoft.VSTS.Common.Priority', 2)),
                        'status': fields.get('System.State', ''),
                        'tags': fields.get('System.Tags', '').split('; ') if fields.get('System.Tags') else [],
                        'created': fields.get('System.CreatedDate', ''),
                        'updated': fields.get('System.ChangedDate', '')
                    })
            
            return test_cases
        except requests.exceptions.RequestException as e:
            return []
    
    def _map_priority_to_number(self, priority: str) -> int:
        """Map internal priority to Azure DevOps priority number."""
        priority_mapping = {
            'high': 1,
            'medium': 2,
            'low': 3
        }
        return priority_mapping.get(priority.lower(), 2)
    
    def _map_number_to_priority(self, priority_number: int) -> str:
        """Map Azure DevOps priority number to internal priority."""
        number_mapping = {
            1: 'high',
            2: 'medium',
            3: 'low'
        }
        return number_mapping.get(priority_number, 'medium')


class PolarionIntegration(ALMIntegration):
    """
    Integration with Siemens Polarion ALM for requirements and test case management.
    """
    
    def _setup_authentication(self):
        """Setup authentication for Polarion."""
        # Polarion typically uses basic authentication
        auth_string = f"{self.username}:{self.password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.session.headers.update({
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a requirement in Polarion."""
        # Note: This is a simplified implementation
        # Actual Polarion integration would require specific API endpoints and data structures
        url = f"{self.base_url}/polarion/rest/v1/projects/{self.project_key}/workitems"
        
        polarion_workitem = {
            "type": "requirement",
            "title": requirement_data.get('title', 'Untitled Requirement'),
            "description": {
                "type": "text/html",
                "content": requirement_data.get('description', '')
            },
            "priority": self._map_priority(requirement_data.get('priority', 'medium')),
            "customFields": {
                "regulatoryStandards": requirement_data.get('regulatory_standards', [])
            }
        }
        
        try:
            response = self.session.post(url, json=polarion_workitem)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to create requirement in Polarion: {str(e)}"}
    
    def create_test_case(self, test_case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test case in Polarion."""
        url = f"{self.base_url}/polarion/rest/v1/projects/{self.project_key}/workitems"
        
        # Format test steps for Polarion
        test_steps = test_case_data.get('test_steps', [])
        formatted_steps = "<ol>"
        for step in test_steps:
            formatted_steps += f"<li>{step}</li>"
        formatted_steps += "</ol>"
        
        polarion_workitem = {
            "type": "testcase",
            "title": test_case_data.get('title', 'Untitled Test Case'),
            "description": {
                "type": "text/html",
                "content": test_case_data.get('description', '')
            },
            "testSteps": {
                "type": "text/html",
                "content": formatted_steps
            },
            "expectedResult": {
                "type": "text/html",
                "content": test_case_data.get('expected_results', '')
            },
            "priority": self._map_priority(test_case_data.get('priority', 'medium')),
            "customFields": {
                "complianceTags": test_case_data.get('compliance_tags', [])
            }
        }
        
        try:
            response = self.session.post(url, json=polarion_workitem)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to create test case in Polarion: {str(e)}"}
    
    def link_requirement_to_test_case(self, requirement_id: str, test_case_id: str) -> bool:
        """Create a link between requirement and test case in Polarion."""
        url = f"{self.base_url}/polarion/rest/v1/projects/{self.project_key}/workitems/{test_case_id}/links"
        
        link_data = {
            "role": "verifies",
            "workItem": {
                "id": requirement_id
            }
        }
        
        try:
            response = self.session.post(url, json=link_data)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to link requirement to test case in Polarion: {str(e)}")
            return False
    
    def get_requirements(self) -> List[Dict[str, Any]]:
        """Get all requirements from Polarion project."""
        url = f"{self.base_url}/polarion/rest/v1/projects/{self.project_key}/workitems"
        params = {"query": "type:requirement"}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            requirements = []
            for item in data.get('data', []):
                requirements.append({
                    'id': item.get('id', ''),
                    'title': item.get('title', ''),
                    'description': item.get('description', {}).get('content', ''),
                    'priority': item.get('priority', 'medium').lower(),
                    'status': item.get('status', ''),
                    'created': item.get('created', ''),
                    'updated': item.get('updated', '')
                })
            
            return requirements
        except requests.exceptions.RequestException as e:
            return []
    
    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases from Polarion project."""
        url = f"{self.base_url}/polarion/rest/v1/projects/{self.project_key}/workitems"
        params = {"query": "type:testcase"}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            test_cases = []
            for item in data.get('data', []):
                test_cases.append({
                    'id': item.get('id', ''),
                    'title': item.get('title', ''),
                    'description': item.get('description', {}).get('content', ''),
                    'priority': item.get('priority', 'medium').lower(),
                    'status': item.get('status', ''),
                    'created': item.get('created', ''),
                    'updated': item.get('updated', '')
                })
            
            return test_cases
        except requests.exceptions.RequestException as e:
            return []
    
    def _map_priority(self, priority: str) -> str:
        """Map internal priority to Polarion priority."""
        priority_mapping = {
            'high': 'high',
            'medium': 'normal',
            'low': 'low'
        }
        return priority_mapping.get(priority.lower(), 'normal')


class ALMIntegrationFactory:
    """
    Factory class for creating ALM integration instances.
    """
    
    @staticmethod
    def create_integration(platform: str, base_url: str, username: str, password: str, project_key: str = None) -> ALMIntegration:
        """
        Create an ALM integration instance based on the platform type.
        
        Args:
            platform: The ALM platform type ('jira', 'azure_devops', 'polarion')
            base_url: Base URL of the ALM platform
            username: Username for authentication
            password: Password or token for authentication
            project_key: Project key or identifier
        
        Returns:
            ALMIntegration instance
        """
        platform = platform.lower()
        
        if platform == 'jira':
            return JiraIntegration(base_url, username, password, project_key)
        elif platform in ['azure_devops', 'azuredevops', 'azure']:
            return AzureDevOpsIntegration(base_url, username, password, project_key)
        elif platform == 'polarion':
            return PolarionIntegration(base_url, username, password, project_key)
        else:
            raise ValueError(f"Unsupported ALM platform: {platform}")


# Example usage and testing functions
def test_alm_integration(platform: str, config: Dict[str, str]):
    """
    Test ALM integration with sample data.
    """
    try:
        integration = ALMIntegrationFactory.create_integration(
            platform=platform,
            base_url=config['base_url'],
            username=config['username'],
            password=config['password'],
            project_key=config.get('project_key')
        )
        
        # Test creating a requirement
        sample_requirement = {
            'requirement_id': 'REQ-001',
            'title': 'Sample Healthcare Requirement',
            'description': 'This is a sample requirement for testing ALM integration.',
            'type': 'functional',
            'priority': 'high',
            'regulatory_standards': ['FDA 21 CFR Part 820', 'IEC 62304']
        }
        
        req_result = integration.create_requirement(sample_requirement)
        print(f"Created requirement: {req_result}")
        
        # Test creating a test case
        sample_test_case = {
            'test_case_id': 'TC-001',
            'title': 'Sample Test Case',
            'description': 'This is a sample test case for testing ALM integration.',
            'preconditions': 'System is running',
            'test_steps': ['Step 1: Login to system', 'Step 2: Navigate to feature', 'Step 3: Verify functionality'],
            'expected_results': 'Feature works as expected',
            'postconditions': 'System remains stable',
            'priority': 'high',
            'compliance_tags': ['FDA', 'IEC 62304']
        }
        
        tc_result = integration.create_test_case(sample_test_case)
        print(f"Created test case: {tc_result}")
        
        return True
        
    except Exception as e:
        print(f"ALM integration test failed: {str(e)}")
        return False


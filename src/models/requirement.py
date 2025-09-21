from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Requirement(db.Model):
    __tablename__ = 'requirements'
    
    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # functional, non-functional, regulatory
    priority = db.Column(db.String(20), nullable=False)  # high, medium, low
    source_document = db.Column(db.String(200))
    regulatory_standards = db.Column(db.Text)  # JSON string of applicable standards
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    test_cases = db.relationship('TestCase', backref='requirement', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'requirement_id': self.requirement_id,
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'priority': self.priority,
            'source_document': self.source_document,
            'regulatory_standards': json.loads(self.regulatory_standards) if self.regulatory_standards else [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def set_regulatory_standards(self, standards_list):
        self.regulatory_standards = json.dumps(standards_list)
    
    def get_regulatory_standards(self):
        return json.loads(self.regulatory_standards) if self.regulatory_standards else []


class TestCase(db.Model):
    __tablename__ = 'test_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    preconditions = db.Column(db.Text)
    test_steps = db.Column(db.Text, nullable=False)  # JSON string of test steps
    expected_results = db.Column(db.Text, nullable=False)
    postconditions = db.Column(db.Text)
    priority = db.Column(db.String(20), nullable=False)
    test_data = db.Column(db.Text)  # JSON string of test data
    compliance_tags = db.Column(db.Text)  # JSON string of compliance tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'test_case_id': self.test_case_id,
            'title': self.title,
            'description': self.description,
            'preconditions': self.preconditions,
            'test_steps': json.loads(self.test_steps) if self.test_steps else [],
            'expected_results': self.expected_results,
            'postconditions': self.postconditions,
            'priority': self.priority,
            'test_data': json.loads(self.test_data) if self.test_data else {},
            'compliance_tags': json.loads(self.compliance_tags) if self.compliance_tags else [],
            'requirement_id': self.requirement_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def set_test_steps(self, steps_list):
        self.test_steps = json.dumps(steps_list)
    
    def get_test_steps(self):
        return json.loads(self.test_steps) if self.test_steps else []
    
    def set_test_data(self, data_dict):
        self.test_data = json.dumps(data_dict)
    
    def get_test_data(self):
        return json.loads(self.test_data) if self.test_data else {}
    
    def set_compliance_tags(self, tags_list):
        self.compliance_tags = json.dumps(tags_list)
    
    def get_compliance_tags(self):
        return json.loads(self.compliance_tags) if self.compliance_tags else []


class TraceabilityLink(db.Model):
    __tablename__ = 'traceability_links'
    
    id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(50), nullable=False)  # requirement, test_case, defect
    source_id = db.Column(db.Integer, nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    link_type = db.Column(db.String(50), nullable=False)  # covers, derives_from, validates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'link_type': self.link_type,
            'created_at': self.created_at.isoformat()
        }


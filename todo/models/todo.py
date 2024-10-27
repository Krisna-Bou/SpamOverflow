from datetime import datetime
from . import db
from enum import  Enum, auto

class Todo(db.Model):
    __tablename__ = 'todos'

    id = db.Column(db.String(80), primary_key=True)
    cid = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now(), onupdate=datetime.now())

    sender = db.Column(db.String(80), nullable=False)
    recipient = db.Column(db.String(80), nullable=False)
    subject = db.Column(db.String(80), nullable=False)
    body = db.Column(db.String(300), nullable=False)
    
    status = db.Column(db.String(80), default='pending', nullable=False)

    malicious = db.Column(db.Boolean, default=False, nullable=False)

    domains = db.Column(db.String(200), default="[]", nullable=False)

    spamhammer = db.Column(db.String(80), default="0|8",nullable=False)

    def get(self, var):
        if var =='id':
            return self.id
        if var =='cid':
            return self.cid
        if var == 'created_at':
            return self.created_at
        if var == 'updated_at':
            return self.updated_at
        if var == 'sender':
            return self.sender
        if var =='recipient':
            return self.recipient
        if var == 'subject':
            return self.subject
        if var =='body':
            return self.body
        if var == 'malicious':
            return self.malicious
        if var == 'domains':
            return self.domains.split(", ")
        if var == 'metadata':
            return self.spamhammer
        if var == 'status':
            return self.status

    def to_dict(self):
        return {
        'id': self.id,
        'created_at': self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if self.created_at else None,
        'updated_at': self.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if self.updated_at else None,
        'contents': {
            'to': self.recipient,
            'from': self.sender,
            'subject': self.subject,
        },
        'status':self.status,
        'malicious': self.malicious,
        'domains': self.domains.split(", "),
        'metadata': {
            'spamhammer': self.spamhammer,
        },
        }



    def __repr__(self):
        return f'<Todo {self.id} {self.subject}>'

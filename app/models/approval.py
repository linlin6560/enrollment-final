from app import db
from datetime import datetime

class Approval(db.Model):
    __tablename__ = 'approvals'
    
    approval_id = db.Column(db.Integer, primary_key=True)
    approval_type = db.Column(db.String(50), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.seller_id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(50), default='待审批', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    reason = db.Column(db.Text)
    
    # 关联
    applicant = db.relationship('User', foreign_keys=[applicant_id], backref='submitted_approvals')
    approver = db.relationship('User', foreign_keys=[approver_id], backref='handled_approvals')
    
    def __repr__(self):
        return f'<Approval {self.approval_id}>'
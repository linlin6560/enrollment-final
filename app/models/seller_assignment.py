from app import db
from datetime import datetime

class SellerAssignment(db.Model):
    __tablename__ = 'seller_assignments'
    
    assignment_id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.seller_id'), nullable=False)
    am_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='待分配')
    
    # 关联
    am = db.relationship('User', foreign_keys=[am_user_id], backref='assigned_sellers')
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref='assigned_operations')
    
    def __repr__(self):
        return f'<SellerAssignment {self.assignment_id}>'
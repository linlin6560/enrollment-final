from app import db
from datetime import datetime
from app.models.seller_assignment import SellerAssignment
from app.models.approval import Approval

class Seller(db.Model):
    __tablename__ = 'sellers'
    
    seller_id = db.Column(db.Integer, primary_key=True)
    seller_name = db.Column(db.String(255), nullable=False)
    contact_info = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50))
    
    # Add these relationships to your Seller model if they don't exist
    assignments = db.relationship('SellerAssignment', backref='seller', lazy='dynamic')
    approvals = db.relationship('Approval', backref='seller', lazy='dynamic')
    
    def __repr__(self):
        return f'<Seller {self.seller_name}>'
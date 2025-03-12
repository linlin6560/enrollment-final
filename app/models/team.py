from app import db

class Team(db.Model):
    __tablename__ = 'teams'
    
    team_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # 修改关联定义，移除 backref
    users = db.relationship('User', backref='team', lazy='dynamic')
    
    def __repr__(self):
        return f'<Team {self.name}>'
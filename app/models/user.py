from app import db, login_manager  # 添加 login_manager 导入
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# 用户-角色关联表
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """检查用户是否拥有指定角色"""
        if not self.roles:
            return False
        
        # 如果 roles 是字符串字段
        if isinstance(self.roles, str):
            role_list = self.roles.split(',')
            return role_name in role_list
        
        # 如果 roles 是关系字段
        return any(role.name == role_name for role in self.roles)

# 自定义匿名用户类
class AnonymousUser(AnonymousUserMixin):
    def has_role(self, role_name):
        return False

# 设置匿名用户类
login_manager.anonymous_user = AnonymousUser

# 添加用户加载器
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
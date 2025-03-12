# 添加用户角色脚本
from app import db, create_app
from app.models.user import User, Role

def check_user_roles(username):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            roles = [role.name for role in user.roles]
            print(f"用户 {user.username} 的角色: {roles}")
            return roles
        else:
            print(f"未找到用户: {username}")
            return None

def add_role_to_user(username, role_name):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"未找到用户: {username}")
            return False
            
        # 查找或创建角色
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=f"{role_name} 角色")
            db.session.add(role)
            
        # 检查用户是否已有该角色
        if role in user.roles:
            print(f"用户 {user.username} 已拥有 {role_name} 角色")
            return True
            
        # 添加角色到用户
        user.roles.append(role)
        db.session.commit()
        print(f"已为用户 {user.username} 添加 {role_name} 角色")
        return True

if __name__ == '__main__':
    username = 'linlin6560@sina.com'  # 替换为实际用户名
    # 先检查当前角色
    current_roles = check_user_roles(username)
    print(f"当前角色: {current_roles}")
    
    # 添加角色 - 修改为 from_team_approve_poc
    add_role_to_user(username, 'from_team_approve_poc')
    
    # 再次检查角色
    updated_roles = check_user_roles(username)
    print(f"更新后角色: {updated_roles}")
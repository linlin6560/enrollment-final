from app import create_app, db
from app.models.user import User, Role

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='linlin6560@gmail.com').first()
    if user:
        # 修改角色名称为 from_team_assignment_poc
        role = Role.query.filter_by(name='from_team_assignment_poc').first()
        if not role:
            role = Role(name='from_team_assignment_poc', description='From-team AM Assignment POC')
            db.session.add(role)
        
        if role not in user.roles:
            user.roles.append(role)
            db.session.commit()
            print(f"已成功为用户 {user.email} 添加 from_team_assignment_poc 角色")
        else:
            print("用户已拥有该角色")
    else:
        print("未找到指定用户")
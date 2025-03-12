from app import create_app, db
from app.models import User, Team
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 检查是否已存在测试团队
    test_team = Team.query.filter_by(name='测试团队').first()
    if not test_team:
        # 创建测试团队
        test_team = Team(name='测试团队', description='用于测试的团队')
        db.session.add(test_team)
        db.session.commit()
        print(f"已创建测试团队: {test_team.name}")
    else:
        print(f"测试团队已存在: {test_team.name}")
    
    # 获取团队ID（查看Team模型的主键属性名）
    # 打印Team对象的所有属性，以便找出主键名称
    print("团队对象属性:", dir(test_team))
    
    # 尝试使用可能的主键名称
    team_id = getattr(test_team, 'team_id', None)
    if team_id is None:
        # 如果team_id不存在，尝试其他可能的主键名称
        for possible_id in ['id', 'team_id', 'tid']:
            if hasattr(test_team, possible_id):
                team_id = getattr(test_team, possible_id)
                print(f"找到团队ID: {team_id}，使用属性: {possible_id}")
                break
    
    if team_id is None:
        print("警告: 无法确定团队ID，请检查Team模型的主键名称")
        # 打印团队对象，查看其属性
        print("团队对象:", test_team.__dict__)
        exit(1)
    
    # 创建测试AM用户
    test_users = [
        {'username': '测试AM1', 'email': 'am1@test.com', 'password': 'password123'},
        {'username': '测试AM2', 'email': 'am2@test.com', 'password': 'password123'},
        {'username': '测试AM3', 'email': 'am3@test.com', 'password': 'password123'}
    ]
    
    for user_data in test_users:
        # 检查用户是否已存在
        user = User.query.filter_by(email=user_data['email']).first()
        if not user:
            # 创建新用户
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                team_id=team_id
            )
            db.session.add(user)
            print(f"已创建测试用户: {user.username}")
        else:
            # 更新现有用户的团队
            user.team_id = team_id
            print(f"已更新测试用户: {user.username}")
    
    # 提交所有更改
    db.session.commit()
    print("测试数据添加完成！")
from app import create_app, db
from app.models.seller import Seller
from app.models.user import User
from app.models.team import Team
from app.models.seller_assignment import SellerAssignment
from app.models.approval import Approval
from datetime import datetime, timedelta
import random

def init_test_data():
    app = create_app()
    with app.app_context():
        # 清除现有数据
        SellerAssignment.query.delete()
        Approval.query.delete()
        Seller.query.delete()
        
        # 确保已有团队数据
        teams = Team.query.all()
        if not teams:
            teams = [
                Team(name='销售一组'),
                Team(name='销售二组'),
                Team(name='销售三组')
            ]
            for team in teams:
                db.session.add(team)
            db.session.commit()
            teams = Team.query.all()
        
        # 创建测试卖家数据
        sellers = []
        statuses = ['待分配', '已分配', '已拒绝']
        for i in range(20):
            created_date = datetime.now() - timedelta(days=random.randint(0, 30))
            # 修改 seller_id 为整数类型
            seller = Seller(
                seller_id=2025000+i,  # 移除 'S' 前缀，使用纯数字
                seller_name=f'测试店铺{i+1}',
                contact_info=f'联系人{i+1}: 1380000{i:04d}',
                created_at=created_date,
                status=random.choice(statuses)
            )
            sellers.append(seller)
            db.session.add(seller)
        db.session.commit()
        
        # 获取用户列表
        users = User.query.all()
        if not users:
            print("警告：没有用户数据，请先创建用户")
            return
        
        # 创建分配记录和审批记录
        for seller in sellers:
            if seller.status == '已分配':
                # 创建分配记录
                assignment_date = seller.created_at + timedelta(days=random.randint(1, 5))
                assignment = SellerAssignment(
                    seller_id=seller.seller_id,
                    am_user_id=random.choice(users).id,
                    assigned_at=assignment_date,
                    assigned_by=random.choice(users).id
                )
                db.session.add(assignment)
            
            elif seller.status == '已拒绝':
                # 创建审批记录
                approval_date = seller.created_at + timedelta(days=random.randint(1, 3))
                approval = Approval(
                    seller_id=seller.seller_id,
                    approval_type='Cross team special approval',
                    applicant_id=random.choice(users).id,
                    approver_id=random.choice(users).id,
                    status='已拒绝',
                    reason='类目不匹配或信息不完整',
                    created_at=approval_date
                )
                db.session.add(approval)
        
        db.session.commit()
        print(f"测试数据初始化完成！已创建 {len(sellers)} 个卖家记录")

if __name__ == '__main__':
    init_test_data()
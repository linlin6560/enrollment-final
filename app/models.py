from datetime import datetime
from app import db
from enum import Enum

class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.String(50), unique=True, nullable=False)
    store_name = db.Column(db.String(100), nullable=False)
    current_team = db.Column(db.String(50))
    current_am = db.Column(db.Integer, db.ForeignKey('am.id'))
    assignment_status = db.Column(db.String(20))  # pending, accepted, rejected
    rejection_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pending_reasons = db.Column(db.JSON, default=list)  # 存储待分配原因列表
    
    def update_pending_reasons(self):
        """更新待分配原因"""
        reasons = []
        
        # 检查 AM team 是否为空
        if not self.current_team:
            reasons.append({
                'type': 'no_team',
                'message': 'RPA匹配规则对应不到AM team',
                'handler': 'ops'
            })
        
        # 检查 team slot 是否已满
        if self.current_team and is_team_slot_full(self.current_team):
            reasons.append({
                'type': 'slot_full',
                'message': '对应Team的slot已满',
                'handler': 'slot_poc'
            })
        
        # 检查 GMS tag
        if self.gms_tag == 'Y':
            reasons.append({
                'type': 'gms_tag',
                'message': 'GMS tag = Y',
                'handler': 'bd'
            })
        
        # 检查 Rejoin tag
        if self.rejoin_tag == 'Y':
            reasons.append({
                'type': 'rejoin_tag',
                'message': 'Rejoin tag = Y',
                'handler': 'bd'
            })
        
        self.pending_reasons = reasons
        return bool(reasons)  # 返回是否有待处理原因

class AM(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    team = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50))
    total_slots = db.Column(db.Integer, default=0)
    used_slots = db.Column(db.Integer, default=0)
    is_poc = db.Column(db.Boolean, default=False)

class CrossTeamApproval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'))
    from_team = db.Column(db.String(50))
    to_team = db.Column(db.String(50))
    reason = db.Column(db.Text)
    status = db.Column(db.String(20))  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ThreeWayMeeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'))
    
    # BD Hard-No assessment
    bd_reporting_country = db.Column(db.String(2))
    bd_account_status = db.Column(db.String(1))
    bd_ttm_gms = db.Column(db.String(1))
    bd_not_part_time = db.Column(db.String(1))
    bd_hard_no_result = db.Column(db.String(10))  # Pass/Reject
    
    # BD None Hard-No assessment
    bd_brand_status = db.Column(db.String(1))
    bd_no_block_history = db.Column(db.String(1))
    bd_health_rating = db.Column(db.String(1))
    bd_not_blacklist = db.Column(db.String(1))
    bd_none_hard_no_result = db.Column(db.String(20))  # Low Risk/Account Block Risk
    bd_model_seller_tag = db.Column(db.String(50))
    
    # AM Hard-No assessment
    am_unreasonable_expectation = db.Column(db.String(1))
    am_trial_period = db.Column(db.String(1))
    am_sales_growth = db.Column(db.String(1))
    am_absolute_data = db.Column(db.String(1))
    am_competitor_info = db.Column(db.String(1))
    am_extra_traffic = db.Column(db.String(1))
    am_compliance = db.Column(db.String(1))
    am_case_driven = db.Column(db.String(1))
    am_hands_on = db.Column(db.String(1))
    am_hard_no_result = db.Column(db.String(10))  # Pass/Reject
    
    # AM None Hard-No assessment
    am_service_frequency = db.Column(db.String(1))
    am_service_timeline = db.Column(db.String(1))
    am_deal_expectation = db.Column(db.String(1))
    am_other_requests = db.Column(db.String(1))
    am_none_hard_no_result = db.Column(db.String(20))  # Low Risk/Misalignment Risk
    
    # Seller Tags
    seller_risk_tags = db.Column(db.String(200))  # 存储多选标签，用逗号分隔
    seller_segmentation = db.Column(db.String(50))
    qualified_for_service = db.Column(db.String(1))
    service_start_date = db.Column(db.Date)
    
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def calculate_bd_hard_no(self):
        """计算BD Hard-No assessment结果"""
        conditions = [
            self.bd_reporting_country == 'Y',
            self.bd_account_status == 'Y',
            self.bd_ttm_gms == 'Y',
            self.bd_not_part_time == 'Y'
        ]
        self.bd_hard_no_result = 'Pass' if all(conditions) else 'Reject'
        return self.bd_hard_no_result

    def calculate_bd_none_hard_no(self):
        """计算BD None Hard-No assessment结果"""
        conditions = [
            self.bd_brand_status == 'Y',
            self.bd_no_block_history == 'Y',
            self.bd_health_rating == 'Y',
            self.bd_not_blacklist == 'Y'
        ]
        self.bd_none_hard_no_result = 'Low Risk' if all(conditions) else 'Account Block Risk'
        return self.bd_none_hard_no_result

    def calculate_am_hard_no(self):
        """计算AM Hard-No assessment结果"""
        conditions = [
            self.am_unreasonable_expectation == 'Y',
            self.am_trial_period == 'Y',
            self.am_sales_growth == 'Y',
            self.am_absolute_data == 'Y',
            self.am_competitor_info == 'Y',
            self.am_extra_traffic == 'Y',
            self.am_compliance == 'Y',
            self.am_case_driven == 'Y',
            self.am_hands_on == 'Y'
        ]
        self.am_hard_no_result = 'Pass' if all(conditions) else 'Reject'
        return self.am_hard_no_result

    def calculate_am_none_hard_no(self):
        """计算AM None Hard-No assessment结果"""
        conditions = [
            self.am_service_frequency == 'Y',
            self.am_service_timeline == 'Y',
            self.am_deal_expectation == 'Y',
            self.am_other_requests == 'Y'
        ]
        self.am_none_hard_no_result = 'Low Risk' if all(conditions) else 'Misalignment Risk'
        return self.am_none_hard_no_result
    bd_content = db.Column(db.Text)
    bd_hard_no = db.Column(db.Boolean, default=False)
    am_content = db.Column(db.Text)
    service_start_date = db.Column(db.Date)
    status = db.Column(db.String(20))  # pending_bd, pending_am, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EarlyAttrition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'))
    reason = db.Column(db.Text)
    initiator = db.Column(db.String(20))  # BD or AM
    status = db.Column(db.String(20))  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ApprovalGMSRejoin(db.Model):
    """GMS和Rejoin审批信息"""
    id = db.Column(db.Integer, primary_key=True)
    approval_id = db.Column(db.Integer, db.ForeignKey('approval.id'))
    bd_name = db.Column(db.String(100), nullable=False)
    cid_to_enroll = db.Column(db.String(50), nullable=False)
    related_mature_cid = db.Column(db.String(50))
    account_change_cid = db.Column(db.String(50))
    gms_band = db.Column(db.String(50), nullable=False)
    ttm_gms = db.Column(db.Numeric(10, 2))
    product = db.Column(db.String(100), nullable=False)
    channel = db.Column(db.String(50), nullable=False)
    special_case = db.Column(db.String(200), nullable=False)
    detailed_reason = db.Column(db.Text, nullable=False)
    referral_am = db.Column(db.String(100))
    referral_am_team = db.Column(db.String(100))
    am_team_to_serve = db.Column(db.String(100), nullable=False)
    am_team_approver = db.Column(db.String(100), nullable=False)
    bd_team = db.Column(db.String(100), nullable=False)
    bd_team_approver = db.Column(db.String(100), nullable=False)

class ApprovalCrossTeam(db.Model):
    """Cross Team审批信息"""
    id = db.Column(db.Integer, primary_key=True)
    approval_id = db.Column(db.Integer, db.ForeignKey('approval.id'))
    bd_name = db.Column(db.String(100), nullable=False)
    cid = db.Column(db.String(50), nullable=False)
    product = db.Column(db.String(100), nullable=False)
    pg_gl_category = db.Column(db.String(200))
    from_team = db.Column(db.String(100), nullable=False)
    from_team_approver = db.Column(db.String(100), nullable=False)
    to_team = db.Column(db.String(100), nullable=False)
    to_team_approver = db.Column(db.String(100), nullable=False)
    cross_team_scenario = db.Column(db.String(200), nullable=False)
    case_reason_type = db.Column(db.String(100), nullable=False)
    detailed_reason = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    referral_am = db.Column(db.String(100))
    additional_details = db.Column(db.Text)

class ApprovalEarlyAttrition(db.Model):
    """Early Attrition审批信息"""
    id = db.Column(db.Integer, primary_key=True)
    approval_id = db.Column(db.Integer, db.ForeignKey('approval.id'))
    cid = db.Column(db.String(50), nullable=False)
    opportunity_id = db.Column(db.String(50), nullable=False)
    opportunity_product_link = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    opportunity_create_date = db.Column(db.Date, nullable=False)
    account_name = db.Column(db.String(200), nullable=False)
    marketplace = db.Column(db.String(50), nullable=False)
    bd_approver = db.Column(db.String(100), nullable=False)
    am_approver = db.Column(db.String(100), nullable=False)
    bd_decision = db.Column(db.String(20), nullable=False)
    team_head_description = db.Column(db.Text)
    contract_sign_date = db.Column(db.Date)
    closed_lost_reason = db.Column(db.String(200), nullable=False)
    detailed_closed_reason = db.Column(db.Text)
    bd_login = db.Column(db.String(100), nullable=False)
    am_login = db.Column(db.String(100), nullable=False)
    disagreed_reason = db.Column(db.Text)

class Approval(db.Model):
    """审批主表"""
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联具体审批信息
    gms_rejoin_info = db.relationship('ApprovalGMSRejoin', backref='approval', uselist=False)
    cross_team_info = db.relationship('ApprovalCrossTeam', backref='approval', uselist=False)
    early_attrition_info = db.relationship('ApprovalEarlyAttrition', backref='approval', uselist=False)

class RoleType(Enum):
    TEAM_LEADER = 'team_leader'
    SLOT_POC = 'slot_poc'
    ASSIGNMENT_POC = 'assignment_poc'
    APPROVAL_POC = 'approval_poc'
    AM = 'am'
    BD = 'bd'

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    team_type = db.Column(db.String(20))  # AM_TEAM or BD_TEAM
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 团队POC
    slot_poc_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assignment_poc_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approval_poc_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 团队统计
    total_max_slots = db.Column(db.Integer, default=0)
    total_in_service = db.Column(db.Integer, default=0)
    total_pending_assignment = db.Column(db.Integer, default=0)
    total_pending_meeting = db.Column(db.Integer, default=0)

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    roles = db.Column(db.JSON)  # 存储用户在团队中的角色列表
    max_slots = db.Column(db.Integer, default=0)  # 仅对AM有效
    in_service_slots = db.Column(db.Integer, default=0)
    pending_assignment = db.Column(db.Integer, default=0)
    pending_meeting = db.Column(db.Integer, default=0)
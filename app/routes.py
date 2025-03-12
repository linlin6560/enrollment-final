from flask import jsonify, request
from app import db
from app.models import Seller, AM, CrossTeamApproval, ThreeWayMeeting, EarlyAttrition
from app.notifications import send_notification
from datetime import datetime, date

@app.route('/api/assignment-poc/sellers', methods=['GET'])
def get_team_sellers():
    """获取团队待分配的卖家列表"""
    team = request.args.get('team')
    search = request.args.get('search')
    status = request.args.get('status')
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    
    query = Seller.query.filter_by(current_team=team)
    
    # 搜索条件
    if search:
        query = query.filter(
            db.or_(
                Seller.seller_id.ilike(f'%{search}%'),
                Seller.store_name.ilike(f'%{search}%')
            )
        )
    
    # 状态筛选
    if status:
        query = query.filter(Seller.assignment_status == status)
    
    # 排序
    if hasattr(Seller, sort):
        order_column = getattr(Seller, sort)
        if order == 'desc':
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    
    sellers = query.all()
    
    # 获取统计信息
    total_count = len(sellers)
    assigned_this_month = Seller.query.filter(
        Seller.current_team == team,
        Seller.assigned_at >= datetime.now().replace(day=1),
        Seller.assignment_status == 'assigned'
    ).count()
    rejected_this_month = Seller.query.filter(
        Seller.current_team == team,
        Seller.rejected_at >= datetime.now().replace(day=1),
        Seller.rejection_count > 0
    ).count()
    
    return jsonify({
        'statistics': {
            'total_pending': total_count,
            'assigned_this_month': assigned_this_month,
            'rejected_this_month': rejected_this_month
        },
        'sellers': [{
            'id': s.id,
            'seller_id': s.seller_id,
            'store_name': s.store_name,
            'status': s.assignment_status,
            'gms_data': s.gms_data,
            'main_category': s.main_category,
            'marketplace': s.marketplace,
            'created_at': s.created_at.isoformat(),
            'waiting_time': (datetime.now() - s.created_at).days,
            'deadline': s.deadline.isoformat() if s.deadline else None
        } for s in sellers]
    })

@app.route('/api/assignment-poc/reject-seller', methods=['POST'])
def reject_seller():
    """拒绝卖家分配并发起cross team审批"""
    data = request.json
    seller = Seller.query.get(data['seller_id'])
    
    if seller.rejection_count > 0:
        return jsonify({'error': '该卖家已被拒绝过'}), 400
    
    seller.rejection_count += 1
    seller.rejected_at = datetime.now()
    
    # 创建Cross Team审批
    approval = CrossTeamApproval(
        seller_id=seller.id,
        from_team=seller.current_team,
        to_team=data['to_team'],
        reason_type=data['reason_type'],
        reason=data['reason'],
        description=data.get('description'),
        attachments=data.get('attachments', []),
        status='pending'
    )
    
    db.session.add(approval)
    db.session.commit()
    
    # 发送通知
    send_notification('cross_team_approval', data['to_team'])
    return jsonify({'message': '已发起cross team审批'})

@app.route('/api/assignment-poc/teams', methods=['GET'])
def get_available_teams():
    """获取可选的目标团队列表"""
    current_team = request.args.get('current_team')
    teams = Team.query.filter(Team.id != current_team).all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'frequently_used': t.frequently_used
    } for t in teams])

@app.route('/api/assignment-poc/reason-types', methods=['GET'])
def get_reason_types():
    """获取拒绝原因类型列表"""
    return jsonify([
        {'id': 'wrong_category', 'name': '品类不符'},
        {'id': 'wrong_marketplace', 'name': '市场不符'},
        {'id': 'special_case', 'name': '特殊案例'},
        {'id': 'other', 'name': '其他原因'}
    ])

@app.route('/api/assignment-poc/assign-am', methods=['POST'])
def assign_to_am():
    """分配卖家给AM"""
    data = request.json
    seller = Seller.query.get(data['seller_id'])
    am = AM.query.get(data['am_id'])
    
    if am.used_slots >= am.total_slots:
        return jsonify({'error': 'AM没有可用名额'}), 400
    
    seller.current_am = am.id
    seller.assignment_status = 'assigned'
    am.used_slots += 1
    
    db.session.commit()
    
    # 发送通知给BD开始三方会议
    send_notification('three_way_meeting_bd', seller.id)
    return jsonify({'message': '分配成功'})

@app.route('/api/three-way-meeting/bd-submit', methods=['POST'])
def bd_submit_meeting():
    """BD提交三方会议记录"""
    data = request.json
    meeting = ThreeWayMeeting.query.get(data['meeting_id'])
    
    # 更新BD Hard-No assessment
    meeting.bd_reporting_country = data['reporting_country']
    meeting.bd_account_status = data['account_status']
    meeting.bd_ttm_gms = data['ttm_gms']
    meeting.bd_not_part_time = data['not_part_time']
    
    # 更新BD None Hard-No assessment
    meeting.bd_brand_status = data['brand_status']
    meeting.bd_no_block_history = data['no_block_history']
    meeting.bd_health_rating = data['health_rating']
    meeting.bd_not_blacklist = data['not_blacklist']
    meeting.bd_model_seller_tag = data['model_seller_tag']
    
    # 计算结果
    hard_no_result = meeting.calculate_bd_hard_no()
    none_hard_no_result = meeting.calculate_bd_none_hard_no()
    
    if hard_no_result == 'Reject':
        # 发起early attrition审批
        create_early_attrition(meeting.seller_id, 'BD Hard No Reject')
    else:
        meeting.status = 'pending_am'
        # 通知AM填写
        send_notification('three_way_meeting_am', meeting.seller_id)
    
    db.session.commit()
    return jsonify({'message': '提交成功'})

@app.route('/api/three-way-meeting/am-submit', methods=['POST'])
def am_submit_meeting():
    """AM提交三方会议记录"""
    data = request.json
    meeting = ThreeWayMeeting.query.get(data['meeting_id'])
    
    # 更新AM Hard-No assessment
    meeting.am_unreasonable_expectation = data['unreasonable_expectation']
    meeting.am_trial_period = data['trial_period']
    meeting.am_sales_growth = data['sales_growth']
    meeting.am_absolute_data = data['absolute_data']
    meeting.am_competitor_info = data['competitor_info']
    meeting.am_extra_traffic = data['extra_traffic']
    meeting.am_compliance = data['compliance']
    meeting.am_case_driven = data['case_driven']
    meeting.am_hands_on = data['hands_on']
    
    # 更新AM None Hard-No assessment
    meeting.am_service_frequency = data['service_frequency']
    meeting.am_service_timeline = data['service_timeline']
    meeting.am_deal_expectation = data['deal_expectation']
    meeting.am_other_requests = data['other_requests']
    
    # 验证并更新 Seller Tags
    if meeting.am_none_hard_no_result != 'Low Risk' and not data.get('risk_tags'):
        return jsonify({'error': '非 Low Risk 状态必须选择风险标签'}), 400
        
    valid_risk_tags = ['brandabnormal', 'casetedency', 'misalignmentrisk', 'accountasinblockrisk']
    if data.get('risk_tags'):
        if not all(tag in valid_risk_tags for tag in data['risk_tags']):
            return jsonify({'error': '包含无效的风险标签'}), 400
        meeting.seller_risk_tags = ','.join(data['risk_tags'])
    
    # 验证 Segmentation Tag
    valid_segments = ['New Seller', 'Emerging Seller', 'Mature Seller']
    if data['segmentation'] not in valid_segments:
        return jsonify({'error': '无效的 Segmentation Tag'}), 400
    meeting.seller_segmentation = data['segmentation']
    
    # 验证服务资格和开始时间
    if 'qualified' not in data:
        return jsonify({'error': '必须指定是否符合开始服务资格'}), 400
    meeting.qualified_for_service = data['qualified']
    
    if data['qualified'] == 'Y':
        if 'service_start_date' not in data:
            return jsonify({'error': '必须指定服务开始时间'}), 400
            
        try:
            start_date = datetime.strptime(data['service_start_date'], '%Y-%m-%d').date()
            # 验证月底不能将服务开始时间设为下月1日
            today = date.today()
            if today.day == today.replace(day=1).day and start_date.day == 1:
                return jsonify({'error': '月底不能将服务开始时间设为下月1日'}), 400
            
            meeting.service_start_date = start_date
            meeting.status = 'completed'
        except ValueError:
            return jsonify({'error': '无效的日期格式'}), 400
    else:
        # 发起 early attrition 审批
        create_early_attrition(meeting.seller_id, 'AM Rejection')
    
    # 计算结果
    meeting.calculate_am_hard_no()
    meeting.calculate_am_none_hard_no()
    
    db.session.commit()
    return jsonify({'message': '提交成功'})

@app.route('/api/approvals/create', methods=['POST'])
def create_approval():
    """创建审批"""
    data = request.json
    approval = Approval(
        type=data['type'],
        status='pending_first'
    )
    db.session.add(approval)
    
    # 根据审批类型创建详细信息
    if data['type'] in ['GMS', 'Rejoin']:
        approval_info = ApprovalGMSRejoin(
            approval=approval,
            bd_name=data['bd_name'],
            cid_to_enroll=data['cid_to_enroll'],
            related_mature_cid=data.get('related_mature_cid'),
            account_change_cid=data.get('account_change_cid'),
            gms_band=data['gms_band'],
            ttm_gms=data.get('ttm_gms'),
            product=data['product'],
            channel=data['channel'],
            special_case=data['special_case'],
            detailed_reason=data['detailed_reason'],
            referral_am=data.get('referral_am'),
            referral_am_team=data.get('referral_am_team'),
            am_team_to_serve=data['am_team_to_serve'],
            am_team_approver=data['am_team_approver'],
            bd_team=data['bd_team'],
            bd_team_approver=data['bd_team_approver']
        )
    elif data['type'] == 'CrossTeam':
        approval_info = ApprovalCrossTeam(
            approval=approval,
            bd_name=data['bd_name'],
            cid=data['cid'],
            product=data['product'],
            pg_gl_category=data.get('pg_gl_category'),
            from_team=data['from_team'],
            from_team_approver=data['from_team_approver'],
            to_team=data['to_team'],
            to_team_approver=data['to_team_approver'],
            cross_team_scenario=data['cross_team_scenario'],
            case_reason_type=data['case_reason_type'],
            detailed_reason=data['detailed_reason'],
            description=data.get('description'),
            referral_am=data.get('referral_am'),
            additional_details=data.get('additional_details')
        )
    elif data['type'] in ['AMEarlyAttrition', 'BDEarlyAttrition']:
        approval_info = ApprovalEarlyAttrition(
            approval=approval,
            cid=data['cid'],
            opportunity_id=data['opportunity_id'],
            opportunity_product_link=data['opportunity_product_link'],
            description=data.get('description'),
            opportunity_create_date=datetime.strptime(data['opportunity_create_date'], '%Y-%m-%d').date(),
            account_name=data['account_name'],
            marketplace=data['marketplace'],
            bd_approver=data['bd_approver'],
            am_approver=data['am_approver'],
            bd_decision=data['bd_decision'],
            team_head_description=data.get('team_head_description'),
            contract_sign_date=datetime.strptime(data['contract_sign_date'], '%Y-%m-%d').date() if data.get('contract_sign_date') else None,
            closed_lost_reason=data['closed_lost_reason'],
            detailed_closed_reason=data.get('detailed_closed_reason'),
            bd_login=data['bd_login'],
            am_login=data['am_login'],
            disagreed_reason=data.get('disagreed_reason')
        )
    
    db.session.add(approval_info)
    db.session.commit()
    
    # 发送审批通知
    notify_approvers(approval)
    return jsonify({'message': '审批已创建', 'approval_id': approval.id})

@app.route('/api/approvals/process', methods=['POST'])
def process_approval():
    """处理审批"""
    data = request.json
    approval = Approval.query.get(data['approval_id'])
    
    # 更新审批结果
    if approval.status == 'pending_first':
        if data['approver_role'] == 'bd_poc':
            approval.bd_poc_result = data['result']
            approval.bd_poc_comment = data['comment']
        else:
            approval.am_poc_result = data['result']
            approval.am_poc_comment = data['comment']
    else:
        if data['approver_role'] == 'bd_leader':
            approval.bd_leader_result = data['result']
            approval.bd_leader_comment = data['comment']
        else:
            approval.am_leader_result = data['result']
            approval.am_leader_comment = data['comment']
    
    # 计算审批结果
    new_status = approval.calculate_result()
    if new_status != approval.status:
        approval.status = new_status
        handle_approval_result(approval)
    
    db.session.commit()
    
    # 发送结果通知
    notify_approval_result(approval)
    return jsonify({'message': '审批已处理'})

def handle_approval_result(approval):
    """处理审批结果"""
    seller = Seller.query.get(approval.seller_id)
    
    if approval.status == 'approved':
        if approval.type == 'CrossTeam':
            # 更新卖家所属团队
            seller.current_team = approval.to_team
            if not has_pending_issues(seller):
                assign_to_poc(seller, approval.to_team)
        elif approval.type in ['GMS', 'Rejoin']:
            if not has_pending_issues(seller):
                assign_to_poc(seller, seller.current_team)
        elif approval.type in ['AMEarlyAttrition', 'BDHardNo', 'BDEarlyAttrition']:
            seller.status = 'closedlost'
    elif approval.status == 'rejected':
        if approval.type in ['GMS', 'Rejoin']:
            seller.status = 'closedlost'
        elif approval.type == 'AMEarlyAttrition':
            # AM必须填写服务开始时间
            meeting = ThreeWayMeeting.query.filter_by(seller_id=seller.id).first()
            meeting.status = 'pending_am_resubmit'
            send_notification('am_resubmit_required', seller.id)

def notify_approvers(approval):
    """通知审批人"""
    if approval.status == 'pending_first':
        send_notification('approval_request', 'bd_poc', approval.id)
        send_notification('approval_request', 'am_poc', approval.id)
    else:
        send_notification('approval_request', 'bd_leader', approval.id)
        send_notification('approval_request', 'am_leader', approval.id)

def notify_approval_result(approval):
    """通知审批结果"""
    send_notification('approval_result', 'initiator', approval.id)
    if approval.type == 'CrossTeam' and approval.status in ['approved', 'rejected']:
        send_notification('cross_team_result', 'previous_poc', approval.id)
        send_notification('cross_team_result', 'previous_am', approval.id)


@app.route('/api/ops/pending-sellers', methods=['GET'])
def get_pending_sellers():
    """获取待分配卖家列表"""
    sellers = Seller.query.filter(Seller.pending_reasons != None).all()
    return jsonify([{
        'id': s.id,
        'seller_id': s.seller_id,
        'store_name': s.store_name,
        'current_team': s.current_team,
        'pending_reasons': s.pending_reasons,
        'gms_tag': s.gms_tag,
        'rejoin_tag': s.rejoin_tag
    } for s in sellers])

@app.route('/api/ops/update-team', methods=['POST'])
def update_seller_team():
    """Ops手动更新卖家的AM team"""
    data = request.json
    seller = Seller.query.get(data['seller_id'])
    
    if not seller:
        return jsonify({'error': '卖家不存在'}), 404
        
    seller.current_team = data['team']
    
    # 更新待处理原因
    if seller.update_pending_reasons():
        # 如果还有其他待处理原因，保持在待处理状态
        db.session.commit()
        return jsonify({'message': '更新成功，但还有其他待处理原因'})
    else:
        # 如果没有其他待处理原因，分配给Assignment POC
        assign_to_poc(seller, seller.current_team)
        db.session.commit()
        return jsonify({'message': '更新成功并已分配给Assignment POC'})

def check_and_auto_assign():
    """检查并自动分配卖家（由定时任务调用）"""
    # 获取所有因slot满而待处理的卖家
    sellers = Seller.query.filter(
        Seller.pending_reasons.contains([{'type': 'slot_full'}])
    ).all()
    
    for seller in sellers:
        if not is_team_slot_full(seller.current_team):
            # 更新待处理原因
            if seller.update_pending_reasons():
                continue  # 如果还有其他待处理原因，跳过分配
            
            # 分配给Assignment POC
            assign_to_poc(seller, seller.current_team)
            
            # 发送通知
            send_notification('seller_assigned', seller.id)

def is_team_slot_full(team):
    """检查team的slot是否已满"""
    # TODO: 实现slot检查逻辑
    pass

def assign_to_poc(seller, team):
    """分配卖家给Assignment POC"""
    seller.assignment_status = 'pending_assignment'
    seller.pending_reasons = None  # 清除待处理原因
    
    # 发送通知给Assignment POC
    send_notification('new_seller_assignment', team)

@app.route('/api/team/members', methods=['GET', 'POST', 'DELETE'])
def manage_team_members():
    """管理团队成员"""
    if request.method == 'GET':
        team_id = request.args.get('team_id')
        members = TeamMember.query.filter_by(team_id=team_id).all()
        return jsonify([{
            'id': m.id,
            'user_id': m.user_id,
            'roles': m.roles,
            'max_slots': m.max_slots,
            'in_service_slots': m.in_service_slots,
            'pending_assignment': m.pending_assignment,
            'pending_meeting': m.pending_meeting
        } for m in members])
        
    elif request.method == 'POST':
        data = request.json
        # 验证当前用户是否为团队leader
        if not is_team_leader(current_user.id, data['team_id']):
            return jsonify({'error': '只有团队leader可以添加成员'}), 403
            
        member = TeamMember(
            team_id=data['team_id'],
            user_id=data['user_id'],
            roles=data['roles'],
            max_slots=data.get('max_slots', 0)
        )
        db.session.add(member)
        db.session.commit()
        return jsonify({'message': '添加成功'})
        
    elif request.method == 'DELETE':
        data = request.json
        if not is_team_leader(current_user.id, data['team_id']):
            return jsonify({'error': '只有团队leader可以删除成员'}), 403
            
        TeamMember.query.filter_by(
            team_id=data['team_id'], 
            user_id=data['user_id']
        ).delete()
        db.session.commit()
        return jsonify({'message': '删除成功'})

@app.route('/api/team/poc', methods=['PUT'])
def update_team_poc():
    """更新团队POC"""
    data = request.json
    team = Team.query.get(data['team_id'])
    
    if not is_team_leader(current_user.id, team.id):
        return jsonify({'error': '只有团队leader可以更新POC'}), 403
    
    if 'slot_poc_id' in data:
        team.slot_poc_id = data['slot_poc_id'] or team.leader_id
    if 'assignment_poc_id' in data:
        team.assignment_poc_id = data['assignment_poc_id'] or team.leader_id
    if 'approval_poc_id' in data:
        team.approval_poc_id = data['approval_poc_id'] or team.leader_id
    
    db.session.commit()
    return jsonify({'message': '更新成功'})

@app.route('/api/team/slots', methods=['GET', 'PUT'])
def manage_slots():
    """管理AM slots"""
    if request.method == 'GET':
        team_id = request.args.get('team_id')
        if is_ops(current_user.id):
            # Ops可以查看所有团队
            teams = Team.query.all()
            return jsonify([{
                'team_name': t.name,
                'total_max_slots': t.total_max_slots,
                'total_in_service': t.total_in_service,
                'total_pending_assignment': t.total_pending_assignment,
                'total_pending_meeting': t.total_pending_meeting,
                'total_remaining': (t.total_max_slots - t.total_in_service 
                                  - t.total_pending_assignment - t.total_pending_meeting)
            } for t in teams])
        else:
            # 团队成员只能查看本团队
            team = Team.query.get(team_id)
            members = TeamMember.query.filter_by(team_id=team_id).all()
            return jsonify({
                'team_summary': {
                    'total_max_slots': team.total_max_slots,
                    'total_in_service': team.total_in_service,
                    'total_pending_assignment': team.total_pending_assignment,
                    'total_pending_meeting': team.total_pending_meeting,
                    'total_remaining': (team.total_max_slots - team.total_in_service 
                                      - team.total_pending_assignment - team.total_pending_meeting)
                },
                'member_details': [{
                    'user_id': m.user_id,
                    'max_slots': m.max_slots,
                    'in_service_slots': m.in_service_slots,
                    'pending_assignment': m.pending_assignment,
                    'pending_meeting': m.pending_meeting,
                    'remaining_slots': (m.max_slots - m.in_service_slots 
                                      - m.pending_assignment - m.pending_meeting)
                } for m in members if 'AM' in m.roles]
            })
    
    elif request.method == 'PUT':
        data = request.json
        if not is_slot_poc(current_user.id, data['team_id']):
            return jsonify({'error': '只有Slot POC可以更新slot数量'}), 403
            
        member = TeamMember.query.filter_by(
            team_id=data['team_id'],
            user_id=data['user_id']
        ).first()
        
        old_max_slots = member.max_slots
        member.max_slots = data['max_slots']
        
        # 更新团队总数
        team = Team.query.get(data['team_id'])
        team.total_max_slots += (data['max_slots'] - old_max_slots)
        
        db.session.commit()
        return jsonify({'message': '更新成功'})

@app.route('/api/approval-poc/pending-approvals', methods=['GET'])
def get_pending_approvals():
    """获取待处理的审批列表"""
    team = request.args.get('team')
    approvals = CrossTeamApproval.query.filter_by(
        from_team=team,
        status='pending'
    ).all()
    
    return jsonify([{
        'id': a.id,
        'seller_id': a.seller_id,
        'store_name': Seller.query.get(a.seller_id).store_name,
        'to_team': a.to_team,
        'reason_type': a.reason_type,
        'reason': a.reason,
        'created_at': a.created_at.isoformat(),
        'status': a.status
    } for a in approvals])

@app.route('/api/approval-poc/approve', methods=['POST'])
def approve_cross_team():
    """审批Cross Team申请"""
    data = request.json
    approval = CrossTeamApproval.query.get(data['approval_id'])
    
    approval.from_team_result = data['result']
    approval.from_team_comment = data.get('comment')
    
    if data['result'] == 'approved':
        approval.status = 'pending_to_team'
        # 通知目标团队的Approval POC
        send_notification('cross_team_approval', approval.to_team)
    else:
        approval.status = 'rejected'
        # 通知发起人
        send_notification('cross_team_rejected', approval.seller_id)
    
    db.session.commit()
    return jsonify({'message': '审批完成'})


# 删除这两个路由函数
# @app.route('/assignment-poc')
# def assignment_poc():
#     """分配管理页面"""
#     return render_template('assignment_poc.html')

# @app.route('/approval-poc')
# def approval_poc():
#     """审批管理页面"""
#     return render_template('approval_poc.html')

@app.route('/api/approval-poc/approval-details/<approval_id>')
def get_approval_details(approval_id):
    """获取审批详情"""
    approval = CrossTeamApproval.query.get(approval_id)
    seller = Seller.query.get(approval.seller_id)
    
    return jsonify({
        'seller_id': seller.seller_id,
        'store_name': seller.store_name,
        'reason': approval.reason,
        'reason_type': approval.reason_type,
        'description': approval.description,
        'attachments': approval.attachments,
        'created_at': approval.created_at.isoformat(),
        'status': approval.status
    })

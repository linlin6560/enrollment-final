def send_notification(notification_type, target_id, **kwargs):
    notification_types.update({
        'pending_seller_no_team': 'Ops：有新的待分配卖家（无AM team）',
        'pending_seller_slot_full': 'Slot POC：有新的待分配卖家（slot已满）',
        'pending_seller_gms': 'BD：有新的待分配卖家（需GMS审批）',
        'pending_seller_rejoin': 'BD：有新的待分配卖家（需Rejoin审批）',
    })
    """
    发送通知
    notification_type: 通知类型
    target_id: 目标ID（可能是seller_id, team_id等）
    """
    # TODO: 实现具体的通知发送逻辑
    notification_types = {
        'cross_team_approval': '有新的cross team审批请求',
        'three_way_meeting_bd': '请填写三方会议BD部分',
        'three_way_meeting_am': '请填写三方会议AM部分',
    }
    
    message = notification_types.get(notification_type, '')
    # 发送企业微信通知
    send_wecom_notification(message, target_id)
    # 发送邮件通知
    send_email_notification(message, target_id)
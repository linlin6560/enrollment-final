from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.admin import admin
from app.models.user import User, Role
from app.admin.forms import UserRoleForm

@admin.route('/dashboard')
@login_required
def dashboard():
    # 检查是否是管理员
    if current_user.username != 'admin':
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取所有用户
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)

@admin.route('/user/<int:user_id>/roles', methods=['GET', 'POST'])
@login_required
def user_roles(user_id):
    # 检查是否是管理员
    if current_user.username != 'admin':
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    form = UserRoleForm()
    
    # 获取所有可用角色
    all_roles = Role.query.all()
    form.roles.choices = [(role.id, role.name) for role in all_roles]
    
    # 设置用户当前拥有的角色
    if request.method == 'GET':
        form.user_id.data = user.id
        form.roles.data = [role.id for role in user.roles]
    
    if form.validate_on_submit():
        # 清除用户当前所有角色
        user.roles = []
        
        # 添加选中的角色
        for role_id in form.roles.data:
            role = Role.query.get(role_id)
            if role:
                user.roles.append(role)
        
        db.session.commit()
        flash(f'已成功更新用户 {user.username} 的角色', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/user_roles.html', form=form, user=user)

# 添加初始化角色的路由
@admin.route('/init-roles')
@login_required
def init_roles():
    # 检查是否是管理员
    if current_user.username != 'admin':
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 预定义角色
    roles = [
        {'name': 'assignment_poc', 'description': '分配POC权限'},
        {'name': 'approval_poc', 'description': '审批POC权限'},
        {'name': 'create_assignment_poc', 'description': '创建分配POC权限'},
        {'name': 'create_approval_poc', 'description': '创建审批POC权限'}
    ]
    
    # 添加角色到数据库
    for role_data in roles:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(name=role_data['name'], description=role_data['description'])
            db.session.add(role)
    
    db.session.commit()
    flash('角色初始化成功', 'success')
    return redirect(url_for('admin.dashboard'))
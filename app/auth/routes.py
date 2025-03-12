from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.auth import auth
from app.auth.forms import LoginForm, RegistrationForm
from app.models.user import User

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        # 管理员特殊处理
        if form.username.data == 'admin' and form.password.data == '1':
            # 查找或创建管理员用户
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(username='admin')
                admin_user.set_password('1')
                db.session.add(admin_user)
                db.session.commit()
            login_user(admin_user)
            return redirect(url_for('admin.dashboard'))
        
        # 普通用户处理
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        flash('用户名或密码错误', 'danger')
    return render_template('auth/login.html', title='登录', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('auth.login'))  # 修改这里，从 'main.index' 改为 'auth.login'

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # 修改这里，处理邮箱可能为空的情况
        email = form.email.data if form.email.data else None
        user = User(username=form.username.data, email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='注册', form=form)

# 在文件顶部添加必要的导入
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.auth.forms import ProfileForm
from app.auth.utils import save_avatar

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        if form.avatar.data:
            avatar_file = save_avatar(form.avatar.data)
            current_user.avatar = avatar_file
        
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('个人资料已更新!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.bio.data = current_user.bio
    
    return render_template('auth/profile.html', form=form)
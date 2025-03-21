from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFError
from app import db
from app.main import bp
from app.models.post import Post, Category
from app.main.forms import PostForm
from app.services.ai_service import AIService
from flask import Response, stream_with_context
from app.decorators import role_required
from datetime import datetime
from app.models.seller import Seller
from app.models import User
from app.models import Team  # 添加这行导入

# 在文件顶部添加这些导入（如果尚未存在）
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models.seller import Seller
from app.models.seller_assignment import SellerAssignment
from datetime import datetime

@bp.route('/')  # 修改所有的 @main 为 @bp
def index():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    
    query = Post.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    # 添加首页需要的变量
    now = datetime.now()
    
    # 这些是示例数据，实际应用中应该从数据库获取
    pending_tasks = 5
    completed_tasks = 12
    total_sellers = 150
    recent_activities_count = 8
    
    # 示例待办事项列表
    todo_list = [
        {
            'id': 1,
            'type': 'approval',
            'title': '新卖家审批',
            'seller_id': 'S12345',
            'seller_name': '北京科技有限公司',
            'created_at': '2025-03-10',
            'due_date': '2025-03-15',
            'priority': 'high'
        },
        {
            'id': 2,
            'type': 'assignment',
            'title': 'AM分配任务',
            'seller_id': 'S12346',
            'seller_name': '上海贸易有限公司',
            'created_at': '2025-03-11',
            'due_date': '2025-03-16',
            'priority': 'medium'
        }
    ]
    
    # 示例最近活动列表
    recent_activities_list = [
        {
            'title': '完成卖家审批',
            'description': '已审批通过 S12340 上海电子科技',
            'time': '1小时前',
            'user': '管理员'
        },
        {
            'title': '分配AM',
            'description': '将 S12338 分配给 张经理',
            'time': '3小时前',
            'user': '系统'
        }
    ]
    
    return render_template('main/index.html', 
                          posts=posts,
                          now=now,
                          pending_tasks=pending_tasks,
                          completed_tasks=completed_tasks,
                          total_sellers=total_sellers,
                          recent_activities=recent_activities_count,
                          todo_list=todo_list,
                          recent_activities_list=recent_activities_list)

@bp.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('main/post.html', post=post)

# 添加图片上传处理函数
import os
import secrets
from PIL import Image
from flask import current_app

def save_image(file, folder='post_images', size=(800, 600)):
    """保存上传的图片并返回文件名"""
    if not file:
        return None
        
    # 创建随机文件名，避免文件名冲突
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(file.filename)
    file_name = random_hex + file_ext
    
    # 确保目标文件夹存在
    upload_folder = os.path.join(current_app.root_path, 'static', folder)
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    file_path = os.path.join(upload_folder, file_name)
    
    # 使用Pillow调整图片大小并保存
    i = Image.open(file)
    i.thumbnail(size)
    i.save(file_path)
    
    # 返回相对路径，确保使用正斜杠
    return folder + '/' + file_name

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    form.category.choices = [(0, '无分类')]
    # 添加数据库中的分类选项
    categories = Category.query.all()
    for category in categories:
        form.category.choices.append((category.id, category.name))
    
    if form.validate_on_submit():
        # 处理图片上传
        image_file = None
        if form.image.data:
            current_app.logger.info(f"正在处理图片上传: {form.image.data.filename}")
            image_file = save_image(form.image.data)
            current_app.logger.info(f"图片已保存，路径为: {image_file}")
            
        # Create the post object after handling the image
        post = Post(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            author=current_user,
            image=image_file  # 保存图片路径
        )
        
        if form.category.data > 0:
            post.category_id = form.category.data
            
        db.session.add(post)
        db.session.commit()
        flash('文章发布成功!', 'success')
        return redirect(url_for('main.post', post_id=post.id))  # 使用 'main.post' 而不是 'bp.post'
        
    return render_template('main/create_post.html', form=form)

@bp.route('/chat')
def chat():
    return render_template('chat.html')

@bp.errorhandler(CSRFError)
def handle_csrf_error(e):
    current_app.logger.error(f"CSRF错误: {str(e)}")
    return jsonify({'error': 'CSRF验证失败'}), 400

@bp.route('/api/chat', methods=['POST'])
@bp.route('/chat_api', methods=['POST'])
def chat_api():
    try:
        data = request.get_json()
        current_app.logger.info(f"解析后的JSON数据: {data}")
        
        if not data or 'message' not in data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        message = data['message']
        
        messages = [
            {"role": "system", "content": "你是一个友好、专业的AI助手，可以帮助用户解答各种问题。"},
            {"role": "user", "content": message}
        ]

        current_app.logger.info(f"发送到AI服务的消息: {messages}")
        
        # 不使用流式响应，改为普通响应
        ai_service = AIService()
        response = ai_service.get_chat_response(messages)
        
        return jsonify({'response': response})
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"处理请求时发生错误: {str(e)}")
        current_app.logger.error(f"错误堆栈: {traceback.format_exc()}")
        return jsonify({'error': '服务器内部错误'}), 500

@bp.route('/stream_chat')
def stream_chat():
    message = request.args.get('message', '')
    if not message:
        return "数据不能为空", 400
    
    # 创建应用上下文
    from app import create_app
    app = create_app()
    
    def generate():
        with app.app_context():
            messages = [
                {"role": "system", "content": "你是一个友好、专业的AI助手，可以帮助用户解答各种问题。"},
                {"role": "user", "content": message}
            ]
            
            ai_service = AIService()
            
            yield "data: 正在思考...\n\n"
            
            try:
                for chunk in ai_service.get_chat_response_stream(messages):
                    if chunk:
                        yield f"data: {chunk}\n\n"
                
                yield "data: [DONE]\n\n"
            except Exception as e:
                current_app.logger.error(f"生成响应时出错: {str(e)}")
                yield f"data: 抱歉，生成回复时出错: {str(e)}\n\n"
                yield "data: [DONE]\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
# 添加删除文章的路由
@bp.route('/post/<int:post_id>/delete')
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 检查当前用户是否是文章作者
    if post.user_id != current_user.id:
        flash('您没有权限删除这篇文章！', 'danger')
        return redirect(url_for('main.post', post_id=post_id))  # 使用 'main.post' 而不是 'bp.post'
    
    # 删除文章关联的图片文件
    if post.image:
        try:
            image_path = os.path.join(current_app.root_path, 'static', post.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            current_app.logger.error(f"删除图片文件失败: {str(e)}")
    
    # 删除文章
    db.session.delete(post)
    db.session.commit()
    
    flash('文章已成功删除！', 'success')
    return redirect(url_for('main.index'))  # 使用 'main.index' 而不是 'bp.index'


@bp.route('/approval_poc')
@login_required
def approval_poc():
    # 检查用户是否有权限访问此页面
    if not current_user.has_role('from_team_approve_poc'):
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 这里添加处理逻辑
    return render_template('main/approval_poc.html', title='From AM Approval POC')

@bp.route('/assignment-poc')
@login_required
@role_required('assignment_poc')
def assignment_poc():
    """分配管理页面"""
    return render_template('main/assignment_poc.html')

# 删除 ApplicationForm 类和 create_application 路由
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class ApplicationForm(FlaskForm):
    seller_id = StringField('卖家记号', validators=[DataRequired()])
    shop_name = StringField('签约账户店铺名称', validators=[DataRequired()])
    gms_tag = StringField('GMS tag')
    rejoin_tag = StringField('Rejoin tag')
    primary_category = StringField('Primary Category')
    key_contact = StringField('关键联系人')
    leads_source = StringField('Leads/Opp Source')
    bd = StringField('BD')
    am_team = StringField('AM Team')

@bp.route('/create-application', methods=['GET', 'POST'])
@login_required
def create_application():
    """创建新申请"""
    form = ApplicationForm()
    if form.validate_on_submit():
        # TODO: 处理表单提交
        flash('申请已提交', 'success')
        return redirect(url_for('main.index'))
    return render_template('main/create_application.html', form=form)

@bp.route('/from_team_assignment')
@login_required
@role_required('from_team_assignment_poc')
def from_team_assignment():
    """From-team AM Assignment POC 页面"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = Seller.query
    
    # 应用状态筛选
    if status:
        query = query.filter(Seller.status == status)
    
    # 应用搜索条件
    if search:
        query = query.filter(
            (Seller.seller_id.like(f'%{search}%')) | 
            (Seller.seller_name.like(f'%{search}%'))
        )
    
    # 获取分页数据
    sellers = query.order_by(Seller.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # 获取团队和AM用户列表（用于分配表单）
    teams = Team.query.all()
    am_users = User.query.filter(User.team_id.isnot(None)).all()
    
    # 统计数据
    stats = {
        'pending_count': Seller.query.filter_by(status='待分配').count(),
        'assigned_count': Seller.query.filter_by(status='已分配').count(),
        'rejected_count': Seller.query.filter_by(status='已拒绝').count()
    }
    
    return render_template(
        'main/from_team_assignment.html',
        sellers=sellers,
        teams=teams,
        am_users=am_users,
        stats=stats
    )

@bp.route('/assign_seller/<string:seller_id>', methods=['POST'])
@login_required
@role_required('from_team_assignment_poc')
def assign_seller(seller_id):
    """分配卖家给AM"""
    seller = Seller.query.filter_by(seller_id=seller_id).first_or_404()
    am_id = request.form.get('am_id', type=int)
    note = request.form.get('note', '')
    
    if not am_id:
        flash('请选择AM', 'danger')
        return redirect(url_for('main.from_team_assignment'))
    
    # 创建分配记录
    assignment = SellerAssignment(
        seller_id=seller_id,
        am_user_id=am_id,
        assigned_at=datetime.now(),
        assigned_by=current_user.id
    )
    
    # 更新卖家状态
    seller.status = '已分配'
    seller.updated_at = datetime.now()
    
    db.session.add(assignment)
    db.session.commit()
    
    flash(f'卖家 {seller.seller_name} 已成功分配', 'success')
    return redirect(url_for('main.from_team_assignment'))

@bp.route('/reject_seller/<string:seller_id>', methods=['POST'])
@login_required
@role_required('from_team_assignment_poc')
def reject_seller(seller_id):
    """拒绝分配卖家"""
    seller = Seller.query.filter_by(seller_id=seller_id).first_or_404()
    team_id = request.form.get('team_id', type=int)
    note = request.form.get('note', '')
    
    # 获取选择的团队
    team = Team.query.get(team_id)
    
    # 创建审批记录
    from app.models.approval import Approval  # 确保导入Approval模型
    
    approval = Approval(
        seller_id=seller_id,
        approval_type='Cross team special approval',
        applicant_id=current_user.id,
        status='已拒绝',
        reason=note,  # 直接使用备注作为拒绝原因
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 更新卖家状态
    seller.status = '已拒绝'
    seller.updated_at = datetime.now()
    
    db.session.add(approval)
    db.session.commit()
    
    flash(f'卖家 {seller.seller_name} 已拒绝分配并转交给团队 {team.name if team else "未知团队"}', 'success')
    return redirect(url_for('main.from_team_assignment'))

@bp.route('/from-am-approval-poc')
@role_required('from_team_approve_poc')
def from_am_approval_poc():
    return render_template('main/from_am_approval_poc.html', title='From AM Approval POC')


@bp.route('/accept_seller/<int:seller_id>', methods=['POST'])
@login_required
def accept_seller(seller_id):
    seller = Seller.query.get_or_404(seller_id)
    am_id = request.form.get('am_id', type=int)
    # 移除notes变量，因为表中没有对应字段
    
    # 验证AM选择
    if not am_id:
        flash('请选择AM', 'danger')
        return redirect(url_for('main.from_team_assignment'))
    
    # 获取选择的AM用户
    am_user = User.query.get(am_id)
    if not am_user:
        flash('选择的AM不存在', 'danger')
        return redirect(url_for('main.from_team_assignment'))
    
    # 更新卖家状态
    seller.status = '已分配'
    
    # 创建分配记录 - 移除notes参数
    assignment = SellerAssignment(
        seller_id=seller.seller_id,
        am_user_id=am_id,  # 使用选择的AM ID
        assigned_at=datetime.utcnow(),
        assigned_by=current_user.id  # 当前用户作为分配者
    )
    
    db.session.add(assignment)
    db.session.commit()
    
    flash(f'已成功将卖家 {seller.seller_name} 分配给 {am_user.username}', 'success')
    return redirect(url_for('main.from_team_assignment'))

import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from flask_ckeditor import CKEditor
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
moment = Moment()
ckeditor = CKEditor()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    moment.init_app(app)
    ckeditor.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import auth as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 在create_app函数中添加
    from app.admin import admin as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp)
    
    # 删除这行，因为已经在 api/__init__.py 中导入了路由
    # from app.api import routes
    
    # 配置日志系统
    if app.debug:
        # 设置应用日志级别为DEBUG
        app.logger.setLevel(logging.DEBUG)
        
        # 创建控制台处理器，使用stdout而不是stderr以确保所有输出都显示在同一个控制台
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        console_handler.setFormatter(formatter)
        
        # 清除现有处理器并添加新的
        for handler in app.logger.handlers:
            app.logger.removeHandler(handler)
        app.logger.addHandler(console_handler)
        
        # 确保Werkzeug日志也显示在控制台
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.DEBUG)
        
        # 添加错误处理器
        @app.errorhandler(Exception)
        def handle_exception(e):
            app.logger.error(f'未捕获的异常: {str(e)}', exc_info=True)
            # 继续抛出异常，以便显示详细的错误页面
            raise e
    
    # 添加调试信息，显示所有路由
    @app.before_request
    def log_request_info():
        if app.debug:
            app.logger.debug(f'请求路径: {request.path}')
    
    return app

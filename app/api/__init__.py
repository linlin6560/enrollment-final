from flask import Blueprint

bp = Blueprint('api', __name__, url_prefix='/api')

# 在创建蓝图后导入路由
from . import routes
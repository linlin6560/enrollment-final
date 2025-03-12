from flask import jsonify, request
from app.api import bp
from app import db
# 导入其他需要的模块

# 这里添加API路由
@bp.route('/test', methods=['GET'])
def test_api():
    return jsonify({"message": "API 测试成功"})

# 后续可以添加更多API路由
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')  # 注意这里改为 instance 目录
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 硅基流动API配置
    SILICONFLOW_API_KEY = os.environ.get('SILICONFLOW_API_KEY') or "sk-lfqrjuvlcjlibudqjknvjhjzhqaobphpfquokxbqcsvadjmo"
    SILICONFLOW_API_URL = os.environ.get('SILICONFLOW_API_URL') or "https://api.siliconflow.cn/v1/chat/completions"
    SILICONFLOW_MODEL = os.environ.get('SILICONFLOW_MODEL') or "Pro/deepseek-ai/DeepSeek-R1"
    # 对话相关配置
    MAX_TOKENS = 5000  # 每次请求的最大令牌数
    
    # 日志配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    SYSTEM_PROMPT = """你是一个会逐步展示思考过程的助手。
请用以下格式回答：
【思考过程】
1. 首先分析问题的关键点...
2. 然后考虑可能的解决方案...
3. 最后综合得出结论...
【最终答案】
"""
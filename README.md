# Flask 博客应用

一个使用 Flask 框架开发的博客系统，支持文章管理、用户认证等功能。

## 功能特点

- 文章的创建、编辑和删除
- 用户注册和登录系统
- SQLite 数据库支持
- 响应式界面设计
- Docker 容器化部署

## 技术栈

- Flask 2.3.3
- Flask-SQLAlchemy 3.1.1
- Flask-Login 0.6.3
- Flask-WTF 1.2.1
- Gunicorn 21.2.0
- Nginx
- Docker & Docker Compose

## 快速开始

1. 克隆项目：
```bash
git clone <repository-url>
cd blog-app-flask

2. 配置环境变量：
   创建 .env 文件并设置必要的环境变量：
```properties
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///data/blog.db
FLASK_ENV=production
 ```

3. 构建和启动容器：
```bash
# 停止现有容器
docker-compose down

# 重新构建容器（不使用缓存）
docker-compose build --no-cache

# 启动容器
docker-compose up -d
 ```

4. 访问应用：
   打开浏览器访问 http://localhost:8080
## 项目结构
```plaintext
blog-app-flask/
├── app.py              # 应用主文件
├── requirements.txt    # Python 依赖
├── Dockerfile         # Docker 配置文件
├── docker-compose.yml # Docker Compose 配置
├── nginx.conf        # Nginx 配置
├── .env              # 环境变量配置
├── data/             # 数据文件目录
└── templates/        # HTML 模板目录
 ```

## 开发环境设置
1. 创建虚拟环境：
```bash
python -m venv venv
.\venv\Scripts\activate
 ```

2. 安装依赖：
```bash
pip install -r requirements.txt
 ```

3. 运行开发服务器：
```bash
python app.py
 ```

## 部署说明
1. 确保安装了 Docker 和 Docker Compose
2. 修改 .env 文件中的配置
3. 使用 docker-compose 启动服务
4. 配置反向代理（如需要）
## 环境变量配置
项目使用 .env 文件管理环境变量，主要配置项包括：

- SECRET_KEY : 应用密钥
- DATABASE_URL : 数据库连接 URL
- FLASK_ENV : 运行环境（development/production）
## 注意事项
- 确保 data 目录具有适当的写入权限
- 生产环境中请修改 SECRET_KEY
- 定期备份数据库文件
- 首次部署后需要重新构建容器以确保环境变量正确加载
## 许可证
MIT License

## 贡献指南
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request
```plaintext

主要更新：
1. 添加了环境变量配置部分
2. 补充了容器构建和启动的详细步骤
3. 在项目结构中添加了 .env 文件
4. 在注意事项中添加了环境变量相关的提示
 ```
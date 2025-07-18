# Tail Trading Backend

基于FastAPI的股票交易系统后端服务。

## 功能特性

- 用户认证和管理
- JWT令牌认证
- 股票数据更新
- 股票选择策略执行
- 定时任务调度
- 完整的REST API

## 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

## 运行服务

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API文档

服务启动后访问 http://localhost:8000/docs 查看交互式API文档。

## 默认用户

系统初始化时会创建默认管理员用户：
- 用户名: admin
- 密码: admin000

请在生产环境中及时修改密码。

## API端点

### 认证
- POST `/api/auth/login` - 用户登录
- GET `/api/auth/me` - 获取当前用户信息

### 用户管理
- GET `/api/users` - 获取所有用户
- POST `/api/users` - 创建用户
- PUT `/api/users/{username}` - 更新用户
- DELETE `/api/users/{username}` - 删除用户

### 股票数据
- POST `/api/stock/update` - 更新股票数据
- POST `/api/stock/select` - 执行选股策略

### 定时任务
- GET `/api/scheduler/status` - 获取任务状态
- POST `/api/scheduler/start` - 启动定时任务
- POST `/api/scheduler/stop` - 停止定时任务
- GET `/api/scheduler/logs` - 获取任务日志

### 系统
- GET `/api/health` - 健康检查

## 配置

环境变量：
- `JWT_SECRET_KEY`: JWT签名密钥（默认随机生成）
- `JWT_ALGORITHM`: JWT算法（默认HS256）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 令牌过期时间（默认30分钟）

## 数据存储

用户数据存储在 `data/users.json` 文件中，支持：
- 用户创建、更新、删除
- 密码bcrypt加密
- 最后登录时间记录

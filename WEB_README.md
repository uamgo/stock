# Tail Trading 股票交易系统

一个完整的股票交易系统，包含前端界面、后端API、用户认证、定时任务等功能。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (Nginx)   │    │  后端 (FastAPI)  │    │   股票数据源     │
│                 │    │                 │    │                 │
│ - Bootstrap UI  │◄──►│ - JWT认证       │◄──►│ - 东方财富      │
│ - 响应式设计    │    │ - RESTful API   │    │ - 数据缓存      │
│ - 实时更新      │    │ - 定时任务      │    │ - 策略计算      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 功能特性

### 🔐 用户认证
- JWT令牌认证
- 用户管理（创建、更新、删除）
- 默认管理员账户
- 安全的密码加密

### 📊 股票数据
- 东方财富数据源集成
- 实时数据更新
- 数据缓存机制
- 多种选股策略

### ⏰ 定时任务
- 可配置的Cron表达式
- 自动数据更新
- 任务状态监控
- 详细执行日志

### 🖥️ 用户界面
- 现代化响应式设计
- 实时操作反馈
- 数据可视化
- 结果导出功能

## 快速开始

### 方式一：Docker部署（推荐）

```bash
# 克隆项目
git clone <repository>
cd stock

# 启动系统
./start_system.sh
```

访问地址：
- 前端界面: http://localhost
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 方式二：开发环境

```bash
# 启动开发环境
./start_dev.sh
```

访问地址：
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8000

## 默认登录

- 用户名: `admin`
- 密码: `admin000`

⚠️ **生产环境请及时修改默认密码**

## 项目结构

```
stock/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── main.py         # FastAPI主应用
│   │   ├── auth.py         # 用户认证
│   │   ├── jwt_auth.py     # JWT处理
│   │   └── scheduler.py    # 定时任务
│   ├── requirements.txt    # Python依赖
│   └── start.sh           # 后端启动脚本
├── frontend/               # 前端代码
│   ├── index.html         # 主页面
│   ├── app.js            # JavaScript逻辑
│   └── nginx.conf        # Nginx配置
├── tail_trading/          # 核心交易逻辑
├── data/                  # 数据目录
├── docker-compose.yml     # Docker编排
├── Dockerfile.backend     # 后端Docker镜像
├── Dockerfile.frontend    # 前端Docker镜像
├── start_system.sh       # 系统启动脚本
└── start_dev.sh          # 开发环境启动脚本
```

## API文档

### 认证端点
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 用户管理
- `GET /api/users` - 获取所有用户
- `POST /api/users` - 创建用户
- `PUT /api/users/{username}` - 更新用户
- `DELETE /api/users/{username}` - 删除用户

### 股票数据
- `POST /api/stock/update` - 更新股票数据
- `POST /api/stock/select` - 执行选股策略

### 定时任务
- `GET /api/scheduler/status` - 获取任务状态
- `POST /api/scheduler/start` - 启动定时任务
- `POST /api/scheduler/stop` - 停止定时任务
- `GET /api/scheduler/logs` - 获取任务日志

## 配置说明

### 环境变量
- `JWT_SECRET_KEY`: JWT签名密钥
- `JWT_ALGORITHM`: JWT算法（默认HS256）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 令牌过期时间（默认30分钟）

### 定时任务配置
默认每工作日上午9点执行数据更新：
```
0 9 * * 1-5
```

可以通过前端界面修改Cron表达式。

## 使用说明

### 1. 登录系统
使用默认用户名密码登录系统。

### 2. 更新数据
在"数据更新"面板中设置要更新的股票数量，点击"更新数据"。

### 3. 选择股票
在"股票选择"面板中：
- 选择策略（保守型/平衡型/激进型）
- 设置选择数量
- 可选择详细输出
- 点击"开始选股"

### 4. 查看结果
选股结果会显示在右侧表格中，包含：
- 股票代码和名称
- 概率分数
- 风险评级
- 建议操作

### 5. 设置定时任务
在"定时任务"面板中：
- 设置Cron表达式
- 启动/停止任务
- 查看执行日志

### 6. 导出数据
点击"导出"按钮可将选股结果导出为CSV文件。

## 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 清理数据（谨慎使用）
docker-compose down -v
```

## 故障排除

### 1. 端口冲突
如果80或8000端口被占用，可以修改`docker-compose.yml`中的端口映射。

### 2. 权限问题
确保data和logs目录有正确的权限：
```bash
chmod -R 755 data logs
```

### 3. Docker问题
确保Docker和docker-compose已正确安装并运行。

### 4. 网络问题
检查防火墙设置，确保相关端口可访问。

## 开发说明

### 后端开发
后端使用FastAPI框架，支持：
- 自动API文档生成
- 类型检查
- 异步处理
- 中间件支持

### 前端开发
前端使用原生JavaScript + Bootstrap，特点：
- 无需构建步骤
- 响应式设计
- 模块化结构
- 易于维护

### 数据库
目前使用文件存储用户数据，生产环境建议迁移到：
- PostgreSQL
- MySQL
- SQLite

## 安全考虑

1. **修改默认密码**：生产环境必须修改默认管理员密码
2. **JWT密钥**：设置强随机JWT密钥
3. **HTTPS**：生产环境启用HTTPS
4. **防火墙**：配置适当的防火墙规则
5. **日志监控**：监控系统访问日志

## 许可证

[请根据实际情况添加许可证信息]

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

[请根据实际情况添加联系方式]

# 股票项目部署文档

## 服务器信息
- 服务器地址: ssh root@login.uamgo.com
- 域名: stock.uamgo.com
- 项目目录: /home/uamgo/stock
- Nginx配置目录: /home/uamgo/nginx/conf
- 前端文件目录: /home/uamgo/nginx/www/stock

## 部署步骤

### 1. 首次部署
```bash
# 给脚本执行权限
chmod +x deploy.sh quick_deploy.sh check_status.sh

# 执行完整部署
./deploy.sh
```

### 2. 日常更新
```bash
# 快速更新（仅更新代码）
./quick_deploy.sh
```

### 3. 检查状态
```bash
# 检查服务器和应用状态
./check_status.sh
```

## 架构说明

### 后端服务
- 运行在Docker容器中
- 容器名: `stock-backend`
- 端口映射: 8000:8000
- 数据卷: 
  - `/home/uamgo/stock/data:/app/data`
  - `/home/uamgo/stock/logs:/app/logs`

### 前端服务
- 静态文件部署在nginx目录
- 路径: `/home/uamgo/nginx/www/stock`
- 通过现有nginx容器提供服务

### Nginx配置
- 配置文件: `/home/uamgo/nginx/conf/nginx-stock.conf`
- 域名: stock.uamgo.com
- API代理: `/api/` → `http://localhost:8000/api/`

## 目录结构

```
/home/uamgo/stock/          # 项目根目录
├── backend/                # 后端代码
├── tail_trading/           # 交易模块
├── data/                   # 数据目录（持久化）
├── logs/                   # 日志目录（持久化）
└── Dockerfile.backend      # 后端Docker文件

/home/uamgo/nginx/
├── conf/
│   └── nginx-stock.conf    # nginx配置
└── www/
    └── stock/              # 前端静态文件
        ├── index.html
        └── app.js
```

## 常用命令

### 服务器上的操作

```bash
# 连接服务器
ssh root@login.uamgo.com

# 查看容器状态
docker ps | grep stock

# 查看容器日志
docker logs stock-backend

# 重启容器
docker restart stock-backend

# 进入容器
docker exec -it stock-backend bash

# 重新加载nginx配置
docker exec nginx nginx -s reload

# 查看nginx日志
docker logs nginx
```

### 本地开发

```bash
# 本地测试后端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 本地构建测试
docker build -f Dockerfile.backend -t stock-backend-test .
docker run -p 8000:8000 stock-backend-test
```

## 故障排除

### 1. 容器启动失败
```bash
# 查看详细错误
docker logs stock-backend

# 检查镜像构建
docker build -f Dockerfile.backend -t stock-backend:latest .
```

### 2. API访问失败
- 检查容器是否运行: `docker ps | grep stock`
- 检查端口映射: `netstat -tlnp | grep 8000`
- 检查nginx配置: `docker exec nginx nginx -t`

### 3. 前端访问失败
- 检查文件是否存在: `ls -la /home/uamgo/nginx/www/stock/`
- 检查nginx配置: `/home/uamgo/nginx/conf/nginx-stock.conf`

## 安全注意事项

1. 修改JWT密钥: 编辑部署脚本中的 `JWT_SECRET_KEY`
2. 定期备份数据目录: `/home/uamgo/stock/data`
3. 监控日志文件大小: `/home/uamgo/stock/logs`

## 访问地址

- 前端应用: http://stock.uamgo.com
- API文档: http://stock.uamgo.com/api/docs
- API健康检查: http://stock.uamgo.com/api/health

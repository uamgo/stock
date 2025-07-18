# 股票项目手动部署指南

## 第一步：上传文件到服务器

在本地运行以下命令：

```bash
# 1. 创建压缩包
cd /Users/kevin/workspace/stock
tar -czf stock-deploy.tar.gz \
    backend/ \
    tail_trading/ \
    frontend/ \
    data/ \
    Dockerfile.backend \
    deploy/nginx-stock.conf \
    tail_trading.py \
    requirements.txt

# 2. 上传到服务器
scp stock-deploy.tar.gz root@login.uamgo.com:/tmp/
```

## 第二步：在服务器上解压和部署

连接到服务器：
```bash
ssh root@login.uamgo.com
```

在服务器上执行：
```bash
# 解压项目文件
mkdir -p /home/uamgo/stock
cd /home/uamgo/stock
tar -xzf /tmp/stock-deploy.tar.gz
rm /tmp/stock-deploy.tar.gz

# 停止现有容器（如果存在）
docker stop stock-backend 2>/dev/null || true
docker rm stock-backend 2>/dev/null || true

# 构建Docker镜像
docker build -f Dockerfile.backend -t stock-backend:latest .

# 创建必要目录
mkdir -p /home/uamgo/stock/data
mkdir -p /home/uamgo/stock/logs
mkdir -p /home/uamgo/nginx/www/stock

# 复制前端文件
cp -r frontend/* /home/uamgo/nginx/www/stock/

# 复制nginx配置
cp deploy/nginx-stock.conf /home/uamgo/nginx/conf/

# 启动后端容器
docker run -d \
    --name stock-backend \
    --restart unless-stopped \
    -p 8000:8000 \
    -v /home/uamgo/stock/data:/app/data \
    -v /home/uamgo/stock/logs:/app/logs \
    -e PYTHONPATH=/app \
    -e JWT_SECRET_KEY=stock-secret-prod-2025 \
    stock-backend:latest

# 重新加载nginx配置
docker exec nginx nginx -s reload

# 检查服务状态
docker ps | grep stock
docker logs --tail 20 stock-backend
```

## 第三步：验证部署

1. 检查容器状态：
```bash
docker ps | grep stock-backend
```

2. 检查容器日志：
```bash
docker logs stock-backend
```

3. 测试API：
```bash
curl http://localhost:8000/api/health
```

4. 访问网站：
http://stock.uamgo.com

## 文件位置说明

- 项目代码：`/home/uamgo/stock/`
- 数据目录：`/home/uamgo/stock/data/`
- 日志目录：`/home/uamgo/stock/logs/`
- 前端文件：`/home/uamgo/nginx/www/stock/`
- Nginx配置：`/home/uamgo/nginx/conf/nginx-stock.conf`

## 常见问题

### 1. 如果容器无法启动
```bash
docker logs stock-backend
```

### 2. 如果nginx配置有问题
```bash
docker exec nginx nginx -t
```

### 3. 重启服务
```bash
docker restart stock-backend
docker exec nginx nginx -s reload
```

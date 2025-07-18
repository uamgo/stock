# 🎉 股票交易系统部署成功

## 🌐 访问地址
- **前端应用**: http://stock.uamgo.com
- **API文档**: http://stock.uamgo.com/api/docs  
- **健康检查**: http://stock.uamgo.com/api/health

## 🔐 默认登录信息
- **用户名**: `admin`
- **密码**: `admin000`

## ⚠️ 首次使用必读

### 1. 初始化概念数据
系统首次使用需要下载概念板块数据，有两种方式：

#### 方式一：前端操作（推荐）
1. 访问 http://stock.uamgo.com
2. 使用 admin/admin000 登录
3. 点击 "初始化概念数据" 按钮
4. 等待初始化完成（约5-10分钟）

#### 方式二：API调用
```bash
# 运行初始化脚本
bash init_concepts.sh
```

### 2. 开始使用
初始化完成后，可以：
- 更新股票数据（TOP 10板块）
- 查询股票信息
- 设置定时任务

## 🔧 系统架构

### 服务组件
- **前端**: 静态HTML/JS，nginx提供服务
- **后端**: FastAPI，systemd服务管理
- **数据库**: 文件系统存储（/tmp/stock/）
- **代理**: nginx Docker容器

### 网络配置
- nginx容器网络：172.19.0.0/16
- nginx容器IP：172.19.0.2  
- 宿主机网关：172.19.0.1
- 后端服务端口：8000

## 📋 功能说明

### 股票数据更新
- **TOP N板块**: 获取涨幅最高的N个概念板块
- **成员股票**: 获取板块内所有股票信息
- **数据存储**: 保存为pickle格式文件

### API接口
- `POST /api/auth/login` - 用户登录
- `POST /api/stock/update` - 更新股票数据
- `POST /api/stock/select` - 查询股票
- `POST /api/stock/init-concepts` - 初始化概念数据
- `GET /api/health` - 健康检查

## 🛠️ 维护命令

### 服务管理
```bash
# 查看后端服务状态
systemctl status stock-backend

# 重启后端服务  
systemctl restart stock-backend

# 查看服务日志
journalctl -u stock-backend -f
```

### nginx管理
```bash
# 重载nginx配置
docker exec nginx nginx -s reload

# 查看nginx日志
docker exec nginx tail -f /var/log/nginx/access.log
```

### 数据管理
```bash
# 查看数据目录
ls -la /tmp/stock/

# 清理缓存数据
rm -rf /tmp/stock/concept/*
rm -rf /tmp/stock/daily/*
```

## 🐛 故障排查

### 常见问题

#### 1. 数据更新失败
**现象**: 提示"概念文件不存在"
**解决**: 先运行概念数据初始化

#### 2. API无法访问
**检查**: 后端服务状态、nginx配置、网络连接

#### 3. 登录失败
**检查**: 用户名密码、JWT配置、bcrypt版本

### 日志位置
- **后端日志**: `journalctl -u stock-backend`
- **nginx日志**: docker容器内 `/var/log/nginx/`
- **系统日志**: `/var/log/syslog`

## 📈 性能优化

### 建议配置
- **并发数**: 默认20，可根据网络情况调整
- **超时时间**: API调用30分钟超时
- **缓存策略**: 概念数据按天缓存

### 监控指标
- CPU使用率
- 内存占用
- 磁盘空间
- 网络延迟

---

**部署完成时间**: 2025-07-18 14:23  
**版本**: v1.0.0  
**状态**: ✅ 运行正常

需要支持请联系系统管理员。

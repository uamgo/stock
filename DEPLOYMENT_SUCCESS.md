# 股票项目部署成功！

## 🎉 部署状态

✅ **后端API服务**: 运行正常 (端口8000)  
✅ **前端Web界面**: 部署成功  
✅ **Nginx代理**: 配置完成  
✅ **数据存储**: 目录已创建  

## 🌐 访问信息

- **前端应用**: http://stock.uamgo.com
- **API文档**: http://stock.uamgo.com/api/docs  
- **API健康检查**: http://stock.uamgo.com/api/health

## 🔐 默认登录信息

- **用户名**: `admin`
- **密码**: `admin000`

> ⚠️ **重要**: 首次登录后请立即修改默认密码！

## 📋 服务管理命令

在服务器上(`ssh root@login.uamgo.com`)执行：

```bash
# 查看服务状态
systemctl status stock-backend

# 重启服务
systemctl restart stock-backend

# 查看服务日志
journalctl -u stock-backend -f

# 停止服务
systemctl stop stock-backend

# 启动服务
systemctl start stock-backend
```

## 🗂️ 文件位置

- **项目代码**: `/home/uamgo/stock/`
- **数据目录**: `/home/uamgo/stock/data/`
- **日志目录**: `/home/uamgo/stock/logs/`
- **前端文件**: `/home/uamgo/nginx/www/stock/`
- **Nginx配置**: `/home/uamgo/nginx/conf/nginx-stock.conf`

## 🔧 故障排除

### 如果服务无法启动：
```bash
# 检查日志
journalctl -u stock-backend --no-pager -n 50

# 检查端口占用
ss -tlnp | grep :8000

# 手动启动测试
cd /home/uamgo/stock
source venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 如果前端无法访问：
```bash
# 检查nginx容器状态
docker ps | grep nginx

# 检查前端文件
ls -la /home/uamgo/nginx/www/stock/

# 重新加载nginx配置
docker exec nginx nginx -s reload
```

## 📈 下一步

1. 登录系统: http://stock.uamgo.com
2. 使用默认账户 `admin` / `admin000` 登录
3. 修改默认密码
4. 配置股票数据源
5. 设置交易策略
6. 启动自动化任务

## 🛠️ 技术架构

- **后端**: FastAPI + Python 3.11
- **前端**: HTML + JavaScript + Bootstrap
- **反向代理**: Nginx (Docker容器)
- **部署方式**: systemd服务 (非Docker容器)
- **数据存储**: JSON文件
- **认证**: JWT Token

---

🎊 **恭喜！股票交易系统已成功部署！**

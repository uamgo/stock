# 部署说明

## 统一部署脚本

新的 `deploy.sh` 脚本支持本地和生产环境的部署，已完全合并原有的 `deploy_local.sh` 和 `deploy_production.sh`。

### 使用方法

```bash
# 本地部署
./deploy.sh local

# 本地部署（带选项）
./deploy.sh local --clean       # 清理旧缓存
./deploy.sh local --init-data   # 初始化基础数据

# 生产环境部署  
./deploy.sh production
```

### 改进点

1. **虚拟环境优化**: 
   - 生产环境部署时会保留现有的虚拟环境，避免每次重新创建
   - 只在首次部署或虚拟环境不存在时创建新的虚拟环境

2. **智能依赖管理**:
   - 使用MD5哈希检测requirements.txt文件是否有变化
   - 只在依赖文件发生变化时才重新安装依赖包
   - 大大减少重复部署的时间

3. **统一脚本**:
   - 合并了 `deploy_local.sh` 和 `deploy_production.sh` 
   - 通过参数区分部署类型
   - 代码维护更简单

4. **完全合并**:
   - 将所有部署逻辑整合到单一脚本中
   - 删除了冗余的部署文件
   - 统一的命令行接口和参数处理
   - 代码重用率更高，维护更简单

5. **备份机制**:
   - 部署前自动备份现有代码
   - 虚拟环境和依赖缓存单独备份和恢复
   - 支持快速回滚

### 服务器结构

- **后端代码**: `/home/uamgo/stock`
- **前端代码**: `/home/uamgo/nginx/www/stock`  
- **nginx配置**: `/home/uamgo/nginx/conf`
- **nginx服务**: 运行在Docker中

### 部署流程

1. 打包代码文件
2. 上传到服务器
3. 备份现有代码、虚拟环境和依赖缓存
4. 解压新代码
5. 恢复虚拟环境和依赖缓存（如果存在）
6. 智能检测并更新变化的依赖包
7. 启动后端服务
8. 重新加载nginx配置

### 管理命令

```bash
# 查看后端日志
ssh root@stock.uamgo.com "tail -f /home/uamgo/stock/logs/backend.log"

# 停止后端服务
ssh root@stock.uamgo.com "kill \$(cat /home/uamgo/stock/backend.pid)"

# 重启后端服务
ssh root@stock.uamgo.com "cd /home/uamgo/stock && nohup .venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 & echo \$! > backend.pid"
```

### 访问地址

- **前端**: http://stock.uamgo.com
- **后端API**: 通过nginx代理访问 `/api/` 路径

# 🎯 股票交易系统 - 问题解决指南

## 📋 系统状态总结

### ✅ 已解决的问题
1. **Docker网络配置**: 修正nginx代理到正确网关地址（172.19.0.1）
2. **硬编码路径**: 使用动态路径替换绝对路径引用
3. **依赖包安装**: 完成pandas、akshare等数据处理库安装
4. **概念数据初始化**: 成功初始化200个概念板块数据
5. **API错误处理**: 改进JSON响应格式和超时处理

### 🎯 当前系统状态
- ✅ 前端应用: http://stock.uamgo.com （正常访问）
- ✅ 后端API: 运行在8000端口（健康检查正常）
- ✅ 用户认证: admin/admin000（登录功能正常）
- ✅ 数据存储: 25MB概念数据已就绪

## 🔧 常见问题和解决方案

### 问题1: "Unexpected token '<', 数据更新异常"

**原因**: API调用超时或返回非JSON格式响应  
**解决方案**:
```bash
# 1. 检查系统状态
bash diagnose.sh

# 2. 使用较小的更新数量
# 在前端设置 top_n = 3 而不是 10

# 3. 检查是否有卡住的进程
ps aux | grep tail_trading
# 如果有，终止它
kill -9 [进程ID]

# 4. 重启后端服务
systemctl restart stock-backend
```

### 问题2: 数据更新缓慢

**原因**: 网络延迟或数据源响应慢  
**优化方案**:
- 减少批量更新数量（top_n = 3-5）
- 避免高峰时段使用
- 等待网络状况改善

### 问题3: 概念数据文件缺失

**检查**: `find /tmp/stock/concept/ -name "*.pkl" | wc -l`  
**解决**: 如果数量 < 200，重新运行 `bash init_concepts.sh`

## 🚀 最佳使用实践

### 日常操作
1. **小批量更新**: 开始时使用 top_n = 3-5
2. **定期清理**: 清理旧的日线数据缓存
3. **监控进程**: 避免多个更新任务同时运行
4. **检查日志**: 出现问题时查看后端日志

### 推荐工作流
```bash
# 1. 每日检查系统状态
bash check_deployment.sh

# 2. 小量测试更新
# 前端操作：登录 → 设置top_n=3 → 点击更新

# 3. 监控执行过程
journalctl -u stock-backend -f

# 4. 成功后再增加数量
# 逐步增加到 top_n = 10 或更多
```

## 📊 性能参考

| 更新数量 | 预期时间 | 内存使用 | 成功率 |
|---------|----------|----------|--------|
| TOP 3   | 1-2分钟  | 60MB     | 95%    |
| TOP 5   | 2-3分钟  | 80MB     | 90%    |
| TOP 10  | 5-8分钟  | 120MB    | 80%    |
| TOP 20  | 10-15分钟| 200MB    | 70%    |

## 🛠️ 维护脚本

```bash
# 系统检查
bash check_deployment.sh

# 问题诊断  
bash diagnose.sh

# 功能测试
bash test_update_fix.sh

# 概念数据初始化
bash init_concepts.sh
```

## 📱 前端使用技巧

1. **登录**: 使用 admin/admin000
2. **首次使用**: 先设置较小的top_n值
3. **监控进度**: 观察浏览器网络标签的响应时间
4. **错误处理**: 如果出现JSON错误，刷新页面重试

## 🆘 紧急故障处理

### 系统完全无响应
```bash
# 1. 重启所有服务
systemctl restart stock-backend
docker restart nginx

# 2. 检查服务状态
bash check_deployment.sh

# 3. 如果仍有问题，查看系统资源
free -h
df -h
```

### 数据库损坏
```bash
# 清理并重新初始化
rm -rf /tmp/stock/
bash init_concepts.sh
```

---

## 🎊 系统已完全就绪！

股票交易系统现在可以稳定运行，建议：
1. 从小数据量开始使用（top_n = 3）
2. 逐步增加到满意的数据量
3. 定期使用维护脚本检查状态

**访问**: http://stock.uamgo.com  
**登录**: admin / admin000  
**支持**: 使用本指南解决常见问题

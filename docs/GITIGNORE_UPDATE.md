# .gitignore 更新说明

## 新增忽略规则

为了保持代码仓库的整洁，已添加以下忽略规则：

### 1. 日志文件
```
/logs/
*.log
```
- 忽略所有日志文件和日志目录
- 避免提交运行时生成的日志信息

### 2. 数据文件
```
/data/cache/
/data/backups/
/data/exports/
/data/positions/
/data/backtest/
/tmp/
*.pkl
*.parquet
*.csv
*.json
```
- 忽略缓存数据、备份数据、导出数据
- 忽略持仓数据和回测数据
- 忽略临时数据文件

### 3. 配置文件
```
/config/trading_config.json
/config/user_config.json
.env
.env.local
```
- 忽略用户个人配置文件
- 忽略环境变量文件
- 保护敏感配置信息

### 4. 输出文件
```
/Users/kevin/Downloads/selected_stocks*.txt
/Users/kevin/Downloads/stock_analysis_report*.txt
/Users/kevin/Downloads/up_up_*.txt
/Users/kevin/Downloads/tail_trading_*.txt
```
- 忽略选股结果文件
- 忽略分析报告文件
- 忽略各种输出文件

### 5. 临时文件
```
*.tmp
*.temp
*.bak
*.swp
*.swo
*~
```
- 忽略各种临时文件
- 忽略编辑器临时文件
- 忽略备份文件

### 6. 操作系统文件
```
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
```
- 忽略macOS系统文件
- 忽略Windows系统文件
- 忽略系统缓存文件

### 7. 编辑器文件
```
.vscode/
.vs/
*.sublime-project
*.sublime-workspace
```
- 忽略编辑器配置文件
- 忽略编辑器工作区文件

### 8. Python相关
```
*.egg-info/
dist/
build/
.coverage
.pytest_cache/
.mypy_cache/
.tox/
```
- 忽略Python构建文件
- 忽略测试缓存文件
- 忽略包分发文件

### 9. 数据库文件
```
*.db
*.sqlite
*.sqlite3
```
- 忽略本地数据库文件
- 避免提交数据库实例

### 10. 压缩文件和报告
```
*.zip
*.tar.gz
*.rar
*.html
*.pdf
```
- 忽略压缩文件
- 忽略生成的报告文件

## 保留的重要文件

以下文件仍会被版本控制：
- Python源代码文件 (*.py)
- 配置模板文件
- 文档文件 (*.md)
- 需求文件 (requirements.txt)
- Docker配置文件
- 项目结构文件

## 注意事项

1. **个人配置**: 用户个人的配置文件不会被提交
2. **敏感信息**: 包含敏感信息的文件已被忽略
3. **数据保护**: 交易数据和选股结果不会被提交
4. **环境独立**: 不同环境的配置文件被分别处理

如需提交特定被忽略的文件，可以使用：
```bash
git add -f <filename>
```

# 选股结果文件名优化报告

## 功能改进

为了更好地区分不同预设配置的选股结果，已优化文件命名机制，在文件名中包含预设配置类型。

## 修改内容

### 1. 股票代码文件命名规则
- **默认配置**: `selected_stocks.txt`
- **保守型配置**: `selected_stocks_conservative.txt`
- **平衡型配置**: `selected_stocks_balanced.txt`
- **激进型配置**: `selected_stocks_aggressive.txt`

### 2. 详细报告文件命名规则
- **默认配置**: `stock_analysis_report.txt`
- **保守型配置**: `stock_analysis_report_conservative.txt`
- **平衡型配置**: `stock_analysis_report_balanced.txt`
- **激进型配置**: `stock_analysis_report_aggressive.txt`

## 技术实现

### 修改的文件
- `tail_trading/cli/commands/select.py`

### 修改的代码逻辑
```python
# 修改前
output_path = str(Settings.DEFAULT_OUTPUT_DIR / "selected_stocks.txt")

# 修改后
preset_suffix = f"_{args.preset}" if args.preset else ""
output_path = str(Settings.DEFAULT_OUTPUT_DIR / f"selected_stocks{preset_suffix}.txt")
```

## 使用示例

### 1. 不同预设配置的选股
```bash
# 保守型配置
python tail_trading.py select --preset conservative
# 生成: selected_stocks_conservative.txt

# 平衡型配置
python tail_trading.py select --preset balanced
# 生成: selected_stocks_balanced.txt

# 激进型配置
python tail_trading.py select --preset aggressive
# 生成: selected_stocks_aggressive.txt

# 默认配置
python tail_trading.py select
# 生成: selected_stocks.txt
```

### 2. 自定义输出文件
```bash
# 仍可使用自定义文件名
python tail_trading.py select --output my_stocks.txt
# 生成: my_stocks.txt（忽略预设后缀）
```

## 实际测试结果

### 测试命令及结果
1. **保守型配置**:
   ```bash
   python tail_trading.py select --preset conservative --limit 3
   ```
   输出: `📁 股票代码已保存到: /Users/kevin/Downloads/selected_stocks_conservative.txt`

2. **激进型配置**:
   ```bash
   python tail_trading.py select --preset aggressive --limit 3
   ```
   输出: `📁 股票代码已保存到: /Users/kevin/Downloads/selected_stocks_aggressive.txt`

3. **默认配置**:
   ```bash
   python tail_trading.py select --limit 3
   ```
   输出: `📁 股票代码已保存到: /Users/kevin/Downloads/selected_stocks.txt`

### 生成的文件
```
/Users/kevin/Downloads/selected_stocks_conservative.txt
/Users/kevin/Downloads/selected_stocks_aggressive.txt
/Users/kevin/Downloads/selected_stocks.txt
/Users/kevin/Downloads/stock_analysis_report_conservative.txt
/Users/kevin/Downloads/stock_analysis_report_aggressive.txt
/Users/kevin/Downloads/stock_analysis_report.txt
```

## 优势

1. **清晰区分**: 不同预设配置的结果文件名不同，避免混淆
2. **历史追踪**: 可以保存和比较不同配置的选股结果
3. **向后兼容**: 默认配置仍使用原始文件名，保持兼容性
4. **用户友好**: 文件名直观反映了使用的配置类型

## 注意事项

1. **文件覆盖**: 相同预设配置的多次运行会覆盖之前的结果
2. **自定义优先**: 使用 `--output` 参数时，自定义文件名优先级更高
3. **目录位置**: 所有文件默认保存在 `/Users/kevin/Downloads/` 目录

这个改进让用户能够更好地管理和区分不同交易策略配置的选股结果。

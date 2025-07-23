// Tail Trading 前端应用

class TailTradingApp {
    constructor() {
        // 自动检测API地址
        this.apiBase = window.location.hostname === 'localhost' && window.location.port === '3000' 
            ? 'http://localhost:8000/api'  // 开发环境
            : '/api';  // 生产环境（通过nginx代理）
        this.token = localStorage.getItem('token');
        this.username = localStorage.getItem('username');
        this.hasNewSelection = false; // 标记是否有新的选股结果
        this.init();
    }

    init() {
        if (this.token) {
            this.showMainPage();
            this.updateSchedulerStatus();
        } else {
            this.showLoginPage();
        }
        this.bindEvents();
    }

    bindEvents() {
        // 登录表单
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });

        // 数据更新表单
        document.getElementById('updateForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateData();
        });

        // 选股表单
        document.getElementById('selectForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.selectStocks();
        });

        // 策略选择变化事件
        document.getElementById('strategy').addEventListener('change', (e) => {
            this.updateStrategyDescription(e.target.value);
        });
    }

    // 更新策略描述
    updateStrategyDescription(strategy) {
        const descriptions = {
            'smart': '智能选股：根据市场环境自动调整策略，适应性强，推荐使用',
            'enhanced': '增强选股：结合放量回调和涨停逻辑，适合追求更高收益的投资者',
            'select': '传统选股：基础选股策略，稳定可靠，适合保守投资者'
        };
        
        const descElement = document.getElementById('strategyDescription');
        if (descElement) {
            descElement.textContent = descriptions[strategy] || '';
        }
    }

    // 页面切换
    showLoginPage() {
        document.getElementById('loginPage').classList.remove('hidden');
        document.getElementById('mainPage').classList.add('hidden');
        
        // 隐藏个人设置下拉菜单
        const userSettingsDropdown = document.getElementById('userSettingsDropdown');
        if (userSettingsDropdown) {
            userSettingsDropdown.style.display = 'none';
        }
    }

    showMainPage() {
        document.getElementById('loginPage').classList.add('hidden');
        document.getElementById('mainPage').classList.remove('hidden');
        
        // 显示个人设置下拉菜单
        const userSettingsDropdown = document.getElementById('userSettingsDropdown');
        if (userSettingsDropdown) {
            userSettingsDropdown.style.display = 'block';
        }
        
        if (this.username) {
            const nickname = localStorage.getItem('nickname') || this.username;
            document.getElementById('userInfo').textContent = `欢迎，${nickname}`;
        }
        // 页面加载时检查已存在的选股结果和概念股数据（只在首次加载时）
        if (!this.hasNewSelection) {
            this.loadExistingStockResults();
            this.loadTopConcepts(true); // 静默加载概念股数据，不显示日志
        }
    }

    // API请求封装
    async apiRequest(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API请求失败:', error);
            if (error.message.includes('401') || error.message.includes('authentication credentials')) {
                this.addLog('⚠️ 登录已过期，请重新登录');
                this.logout();
                throw new Error('登录已过期，请重新登录');
            }
            throw error;
        }
    }

    // 用户认证
    async login() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const submitBtn = document.querySelector('#loginForm button[type="submit"]');
        const loading = submitBtn.querySelector('.loading');
        const errorDiv = document.getElementById('loginError');

        try {
            loading.classList.add('show');
            submitBtn.disabled = true;
            errorDiv.classList.add('hidden');

            const data = await this.apiRequest('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });

            this.token = data.access_token;
            this.username = data.username;
            localStorage.setItem('token', this.token);
            localStorage.setItem('username', this.username);
            
            // 保存昵称信息
            if (data.nickname) {
                localStorage.setItem('nickname', data.nickname);
            }

            this.showMainPage();
            const displayName = data.nickname || this.username;
            this.addLog(`登录成功，欢迎 ${displayName}！`);
            this.updateSchedulerStatus();

        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.classList.remove('hidden');
        } finally {
            loading.classList.remove('show');
            submitBtn.disabled = false;
        }
    }

    logout() {
        this.token = null;
        this.username = null;
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        localStorage.removeItem('nickname');
        
        // 清空用户信息显示
        const userInfo = document.getElementById('userInfo');
        if (userInfo) {
            userInfo.textContent = '';
        }
        
        // 隐藏个人设置下拉菜单
        const userSettingsDropdown = document.getElementById('userSettingsDropdown');
        if (userSettingsDropdown) {
            userSettingsDropdown.style.display = 'none';
        }
        
        this.showLoginPage();
        this.addLog('已退出登录');
    }

    // 数据更新
    async updateData() {
        const topN = parseInt(document.getElementById('topN').value);
        const submitBtn = document.querySelector('#updateForm button[type="submit"]');
        const loading = submitBtn.querySelector('.loading');

        loading.classList.add('show');
        submitBtn.disabled = true;
        this.addLog(`🚀 开始更新股票数据（TOP ${topN}）...`);
        this.addLog(`📡 正在连接数据源，请耐心等待...`);

        // 构造SSE请求，带鉴权
        const url = `${this.apiBase}/stock/update-stream?top_n=${topN}`;
        
        // 关闭已有流
        if (this._eventSource) {
            this._eventSource.close();
        }
        
        // 添加超时处理
        const timeoutId = setTimeout(() => {
            this.addLog('⚠️ 数据更新超时，请检查网络连接或稍后重试');
            loading.classList.remove('show');
            submitBtn.disabled = false;
        }, 300000); // 5分钟超时
        
        // 通过 fetch + ReadableStream 实现带 Authorization 的 SSE
        fetch(url, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        }).then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            if (!response.body) {
                throw new Error('SSE响应无内容');
            }
            
            this.addLog('✅ 已连接到数据流，开始接收更新日志...');
            
            const reader = response.body.getReader();
            let buffer = '';
            const utf8Decoder = new TextDecoder('utf-8');
            let logCount = 0;
            
            const processStream = () => reader.read().then(({done, value}) => {
                if (done) {
                    clearTimeout(timeoutId);
                    this.addLog('📡 数据流结束');
                    loading.classList.remove('show');
                    submitBtn.disabled = false;
                    return;
                }
                
                buffer += utf8Decoder.decode(value);
                let lines = buffer.split('\n');
                buffer = lines.pop();
                
                for (const line of lines) {
                    if (line.startsWith('data:')) {
                        try {
                            const data = JSON.parse(line.slice(5));
                            logCount++;
                            
                            if (data.type === 'start') {
                                this.addLog(`🏁 ${data.message}`);
                            } else if (data.type === 'log') {
                                // 添加日志计数器和更好的格式化
                                const formattedMessage = data.message.replace(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/, '');
                                this.addLog(`📊 [${logCount}] ${formattedMessage || data.message}`);
                            } else if (data.type === 'success') {
                                this.addLog(`🎉 ${data.message}`);
                                clearTimeout(timeoutId);
                                loading.classList.remove('show');
                                submitBtn.disabled = false;
                                reader.cancel();
                                
                                // 数据更新成功后，自动加载概念股数据
                                setTimeout(() => {
                                    this.loadTopConcepts();
                                }, 1000); // 延迟1秒确保数据文件生成完成
                                
                                // 自动执行三种选股策略
                                this.addLog('🤖 数据更新完成，开始自动执行三种选股策略...');
                                setTimeout(() => {
                                    this.autoExecuteAllStrategies();
                                }, 2000); // 延迟2秒确保数据更新完全完成
                            } else if (data.type === 'error') {
                                this.addLog(`❌ ${data.message}`);
                                clearTimeout(timeoutId);
                                loading.classList.remove('show');
                                submitBtn.disabled = false;
                                reader.cancel();
                            }
                        } catch (e) {
                            this.addLog(`⚠️ 日志解析异常: ${e.message}`);
                        }
                    }
                }
                processStream();
            }).catch(err => {
                clearTimeout(timeoutId);
                this.addLog(`❌ 读取数据流异常: ${err.message}`);
                loading.classList.remove('show');
                submitBtn.disabled = false;
            });
            
            processStream();
        }).catch(err => {
            clearTimeout(timeoutId);
            this.addLog(`❌ SSE连接异常: ${err.message}`);
            loading.classList.remove('show');
            submitBtn.disabled = false;
        });
    }

    // 清理缓存
    async clearCache() {
        try {
            this.addLog('🧹 开始清理缓存...');
            
            const data = await this.apiRequest('/stock/clear-cache', {
                method: 'POST'
            });
            
            if (data.success) {
                this.addLog(data.message);
            } else {
                this.addLog(`❌ 缓存清理失败: ${data.message}`);
            }
        } catch (error) {
            this.addLog(`❌ 缓存清理异常: ${error.message}`);
        }
    }

    // 清理磁盘数据
    async clearDiskData() {
        // 添加确认对话框
        if (!confirm('⚠️ 确定要清理磁盘数据吗？\n\n这将删除：\n• 历史数据文件\n• 导出文件\n• 日志文件（保留最近3天）\n• 临时输出目录\n\n此操作不可恢复！')) {
            return;
        }
        
        try {
            this.addLog('🗂️ 开始清理磁盘数据...');
            
            const data = await this.apiRequest('/stock/clear-disk-data', {
                method: 'POST'
            });
            
            if (data.success) {
                this.addLog(data.message);
            } else {
                this.addLog(`❌ 磁盘数据清理失败: ${data.message}`);
            }
        } catch (error) {
            this.addLog(`❌ 磁盘数据清理异常: ${error.message}`);
        }
    }

    // 获取和显示Top N概念股
    async loadTopConcepts(silent = false) {
        try {
            const topN = parseInt(document.getElementById('topN').value) || 20;
            if (!silent) {
                this.addLog(`📊 正在获取Top ${topN}概念股数据...`);
            }
            
            const data = await this.apiRequest(`/stock/top-concepts?n=${topN}`, {
                method: 'GET'
            });
            
            if (data.success && data.data.length > 0) {
                this.displayConceptStocks(data.data, data.update_time);
                if (!silent) {
                    this.addLog(`✅ ${data.message}，更新时间: ${data.update_time}`);
                }
            } else {
                if (!silent) {
                    this.addLog(`⚠️ ${data.message}`);
                }
                this.hideConceptStocks();
            }
        } catch (error) {
            if (!silent) {
                this.addLog(`❌ 获取概念股数据异常: ${error.message}`);
            }
            this.hideConceptStocks();
        }
    }

    // 显示概念股数据
    displayConceptStocks(concepts, updateTime) {
        const card = document.getElementById('conceptStocksCard');
        const tbody = document.querySelector('#conceptStocksTable tbody');
        const countBadge = document.getElementById('conceptStocksCount');
        
        // 清空现有数据
        tbody.innerHTML = '';
        
        // 填充数据
        concepts.forEach(concept => {
            const row = document.createElement('tr');
            
            // 根据热度分数设置行的颜色
            let rowClass = '';
            if (concept.heat_score >= 80) {
                rowClass = 'table-danger'; // 红色 - 极热
            } else if (concept.heat_score >= 60) {
                rowClass = 'table-warning'; // 黄色 - 热门
            } else if (concept.heat_score >= 40) {
                rowClass = 'table-info'; // 蓝色 - 温和
            }
            
            if (rowClass) {
                row.className = rowClass;
            }
            
            row.innerHTML = `
                <td class="text-center fw-bold">${concept.rank}</td>
                <td title="${concept.concept}">${concept.concept}</td>
                <td class="text-center">
                    <span class="badge bg-primary">${concept.heat_score}</span>
                </td>
                <td class="text-center ${parseFloat(concept.change_pct) >= 0 ? 'text-rise' : 'text-fall'}">
                    ${concept.change_pct}
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
        // 更新计数
        countBadge.textContent = concepts.length;
        
        // 卡片始终显示，不需要控制显示/隐藏
        
        // 更新卡片标题时间戳
        const header = card.querySelector('.card-header span:first-child');
        header.innerHTML = `<i class="bi bi-bar-chart-line"></i> Top N 概念股 <small class="text-muted">(${updateTime})</small>`;
    }

    // 重置概念股显示
    hideConceptStocks() {
        const tbody = document.querySelector('#conceptStocksTable tbody');
        const countBadge = document.getElementById('conceptStocksCount');
        
        // 重置为初始状态，但保持卡片可见
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">暂无数据，请先更新数据</td></tr>';
        countBadge.textContent = '0';
        
        // 重置卡片标题
        const card = document.getElementById('conceptStocksCard');
        const header = card.querySelector('.card-header span:first-child');
        header.innerHTML = '<i class="bi bi-bar-chart-line"></i> Top N 概念股';
    }

    // 股票选择
    async selectStocks() {
        const strategy = document.getElementById('strategy').value;
        const preset = document.getElementById('preset').value;
        const limit = parseInt(document.getElementById('limit').value);
        const verbose = document.getElementById('verbose').checked;
        const submitBtn = document.querySelector('#selectForm button[type="submit"]');
        const loading = submitBtn.querySelector('.loading');

        try {
            loading.classList.add('show');
            submitBtn.disabled = true;

            // 根据策略类型显示不同的日志信息
            const strategyNames = {
                'smart': '智能选股',
                'enhanced': '增强选股',
                'select': '传统选股'
            };

            this.addLog(`🚀 开始${strategyNames[strategy]}（风险偏好：${preset}，数量：${limit}）...`);

            // 根据策略选择不同的API端点
            let apiEndpoint;
            let requestBody;

            switch (strategy) {
                case 'smart':
                    apiEndpoint = '/stock/smart-select';
                    requestBody = { preset, limit, verbose };
                    break;
                case 'enhanced':
                    apiEndpoint = '/stock/enhanced-select';
                    requestBody = { preset, limit, verbose };
                    break;
                case 'select':
                default:
                    apiEndpoint = '/stock/select';
                    requestBody = { preset, limit, verbose };
                    break;
            }

            const data = await this.apiRequest(apiEndpoint, {
                method: 'POST',
                body: JSON.stringify(requestBody)
            });

            if (data.success) {
                this.addLog('选股完成！');
                this.hasNewSelection = true; // 标记有新的选股结果
                
                // 添加调试信息
                console.log('选股API返回数据:', data);
                this.addLog(`API返回数据结构: success=${data.success}, data长度=${data.data ? data.data.length : 0}`);
                
                if (data.data && data.data.length > 0) {
                    this.addLog(`准备显示 ${data.data.length} 只股票`);
                    // 传递策略参数给displayStocks方法
                    this.displayStocks(data.data, strategy);
                    
                    // 结果已由后端自动保存到对应的策略文件
                    this.addLog(`💾 ${strategyNames[strategy]}结果已保存到文件`);
                } else {
                    this.addLog('⚠️ 没有返回股票数据或数据为空');
                    console.log('data字段:', data.data);
                }
                
                if (data.log) {
                    this.addLog(data.log);
                }
            } else {
                this.addLog(`选股失败: ${data.message}`);
                if (data.error) {
                    this.addLog(data.error);
                }
            }

        } catch (error) {
            this.addLog(`选股异常: ${error.message}`);
        } finally {
            loading.classList.remove('show');
            submitBtn.disabled = false;
        }
    }

    // 加载已存在的选股结果
    async loadExistingStockResults() {
        try {
            // 加载分策略的结果
            const data = await this.apiRequest('/stock/strategy-results');
            if (data.success && data.data) {
                let totalLoaded = 0;
                
                // 加载智能选股结果
                if (data.data.smart && data.data.smart.data.length > 0) {
                    this.displayStocks(data.data.smart.data, 'smart');
                    totalLoaded += data.data.smart.count;
                    this.addLog(`📊 加载智能选股结果: ${data.data.smart.count} 只股票`);
                }
                
                // 加载增强选股结果
                if (data.data.enhanced && data.data.enhanced.data.length > 0) {
                    this.displayStocks(data.data.enhanced.data, 'enhanced');
                    totalLoaded += data.data.enhanced.count;
                    this.addLog(`📊 加载增强选股结果: ${data.data.enhanced.count} 只股票`);
                }
                
                // 加载传统选股结果
                if (data.data.select && data.data.select.data.length > 0) {
                    this.displayStocks(data.data.select.data, 'select');
                    totalLoaded += data.data.select.count;
                    this.addLog(`📊 加载传统选股结果: ${data.data.select.count} 只股票`);
                }
                
                if (totalLoaded > 0) {
                    this.addLog(`✅ 已加载所有策略的历史结果，共 ${totalLoaded} 只股票`);
                } else {
                    this.addLog('暂无已保存的策略结果');
                }
            } else {
                this.addLog('暂无已存在的选股结果');
            }
        } catch (error) {
            console.log('加载已存在选股结果失败:', error.message);
            // 不显示错误信息，因为可能是首次使用
        }
    }

    // 显示股票结果 - 支持三个tab
    displayStocks(stocks, strategy = null) {
        console.log('=== displayStocks 开始执行 ===');
        console.log('displayStocks被调用，股票数据:', stocks);
        console.log('策略类型:', strategy);
        console.log('stocks类型:', typeof stocks);
        console.log('stocks是否为数组:', Array.isArray(stocks));
        this.addLog(`🔍 开始显示股票数据，共 ${stocks ? stocks.length : 0} 只`);
        
        // 如果没有指定策略，则根据当前选择的策略来确定
        if (!strategy) {
            const strategySelect = document.getElementById('strategy');
            strategy = strategySelect ? strategySelect.value : 'smart';
        }
        
        // 根据策略选择对应的表格
        let tableId;
        let tabId;
        let countId;
        
        switch(strategy) {
            case 'enhanced':
                tableId = 'enhancedStockTable';
                tabId = 'enhanced-tab';
                countId = 'enhancedCount';
                break;
            case 'select':
                tableId = 'traditionalStockTable';
                tabId = 'traditional-tab';
                countId = 'traditionalCount';
                break;
            case 'smart':
            default:
                tableId = 'smartStockTable';
                tabId = 'smart-tab';
                countId = 'smartCount';
                break;
        }
        
        const tbody = document.querySelector(`#${tableId} tbody`);
        
        // 强制清空之前的内容
        console.log(`清空${tableId}的tbody内容...`);
        tbody.innerHTML = '';
        
        // 添加一个短暂延迟确保DOM更新
        setTimeout(() => {
            console.log('tbody已清空，开始填充新数据...');
            
            if (!stocks || stocks.length === 0) {
                console.log('股票数据为空，显示暂无数据消息');
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">暂无数据</td></tr>';
                this.addLog('❌ 股票数据为空，显示暂无数据');
                // 更新数量徽章
                const countElement = document.getElementById(countId);
                if (countElement) countElement.textContent = '0';
                return;
            }

            // 清空现有数据的确认
            this.addLog(`🗑️ 已清空旧数据，准备显示 ${stocks.length} 只新股票`);

            stocks.forEach((stock, index) => {
                console.log(`处理第${index + 1}只股票:`, stock);
                console.log(`股票对象的所有键:`, Object.keys(stock));
                
                const row = document.createElement('tr');
                // 适配后端返回的中文字段名 - 增加更多可能的字段名
                const code = stock.代码 || stock.code || stock.股票代码 || stock.symbol || '-';
                const name = stock.名称 || stock.name || stock.股票名称 || '-';
                const probability = stock.次日补涨概率 || stock.probability_score || stock.概率分数 || stock.score || stock.技术评分 || stock.适应性评分 || stock.增强评分 || '-';
                const risk = stock.风险评分 || stock.risk_level || stock.风险等级 || stock.risk || '-';
                const action = stock.操作建议 || stock.action || stock.建议 || stock.选股类型 || '买入';
                
                this.addLog(`📊 股票${index + 1}: ${code} ${name} 评分:${probability} 类型:${action}`);
                
                // 生成东方财富链接
                const eastmoneyUrl = this.generateEastmoneyUrl(code);
                
                row.innerHTML = `
                    <td><a href="${eastmoneyUrl}" target="_blank" class="stock-code-link">${code}</a></td>
                    <td>${name}</td>
                    <td>${typeof probability === 'number' ? probability.toFixed(2) + '%' : probability}</td>
                    <td>${typeof risk === 'number' ? risk.toFixed(2) : risk}</td>
                    <td>${action}</td>
                `;
                row.setAttribute('data-stock-code', code); // 添加股票代码属性用于重复检查
                tbody.appendChild(row);
            });

            // 更新数量徽章
            const countElement = document.getElementById(countId);
            if (countElement) countElement.textContent = stocks.length.toString();

            // 检查重复股票并设置背景色
            this.checkDuplicateStocks();

            this.addLog(`✅ 成功显示 ${stocks.length} 只股票的${this.getStrategyName(strategy)}结果`);
            console.log('=== displayStocks 执行完成 ===');
        }, 100); // 100ms延迟确保DOM清空
    }

    // 获取策略名称
    getStrategyName(strategy) {
        switch(strategy) {
            case 'enhanced': return '增强选股';
            case 'select': return '传统选股';
            case 'smart': 
            default: return '智能选股';
        }
    }

    // 检查重复股票并设置背景色
    checkDuplicateStocks() {
        // 收集所有股票代码
        const allStocks = new Map(); // code -> array of table elements
        
        ['smartStockTable', 'enhancedStockTable', 'traditionalStockTable'].forEach(tableId => {
            const table = document.getElementById(tableId);
            if (table) {
                const rows = table.querySelectorAll('tbody tr[data-stock-code]');
                rows.forEach(row => {
                    const code = row.getAttribute('data-stock-code');
                    if (code && code !== '-') {
                        if (!allStocks.has(code)) {
                            allStocks.set(code, []);
                        }
                        allStocks.get(code).push({
                            row: row,
                            table: tableId
                        });
                    }
                });
            }
        });

        // 清除之前的样式
        document.querySelectorAll('.stock-duplicate-2, .stock-duplicate-3').forEach(row => {
            row.classList.remove('stock-duplicate-2', 'stock-duplicate-3');
        });

        // 设置重复股票的背景色
        allStocks.forEach((tables, code) => {
            if (tables.length === 2) {
                // 命中2个tab
                tables.forEach(item => {
                    item.row.classList.add('stock-duplicate-2');
                });
            } else if (tables.length === 3) {
                // 命中3个tab
                tables.forEach(item => {
                    item.row.classList.add('stock-duplicate-3');
                });
            }
        });
    }

    // 生成东方财富股票链接
    generateEastmoneyUrl(stockCode) {
        if (!stockCode || stockCode === '-') {
            return '#';
        }
        
        // 判断股票市场并生成正确格式的链接
        const code = stockCode.toString();
        let marketPrefix = '';
        
        if (code.startsWith('6')) {
            // 上海证券交易所
            marketPrefix = 'sh';
        } else if (code.startsWith('0') || code.startsWith('3')) {
            // 深圳证券交易所
            marketPrefix = 'sz';
        } else {
            // 默认深圳
            marketPrefix = 'sz';
        }
        
        return `https://quote.eastmoney.com/concept/${marketPrefix}${code}.html`;
    }

    // 定时任务管理
    async updateSchedulerStatus() {
        try {
            const data = await this.apiRequest('/scheduler/status');
            console.log('调度器状态数据:', data); // 添加调试信息
            
            const statusDiv = document.getElementById('schedulerStatus');
            const toggleBtn = document.getElementById('toggleSchedulerBtn');
            
            // 检查running状态（兼容旧的is_running字段）
            const isRunning = data.running || data.is_running || false;
            
            if (isRunning) {
                statusDiv.innerHTML = '<span class="status-running"><i class="bi bi-play-circle"></i> 运行中</span>';
                if (data.next_run) {
                    statusDiv.innerHTML += `<br><small>下次执行: ${new Date(data.next_run).toLocaleString()}</small>`;
                }
                // 更新按钮为停止状态
                if (toggleBtn) {
                    toggleBtn.textContent = '停止定时任务';
                    toggleBtn.className = 'btn btn-danger';
                    toggleBtn.onclick = () => this.stopScheduler();
                }
                this.addLog(`🔄 定时任务状态已更新: 运行中`);
            } else {
                statusDiv.innerHTML = '<span class="status-stopped"><i class="bi bi-stop-circle"></i> 已停止</span>';
                // 更新按钮为启动状态
                if (toggleBtn) {
                    toggleBtn.textContent = '启动定时任务';
                    toggleBtn.className = 'btn btn-info';
                    toggleBtn.onclick = () => this.startScheduler();
                }
                this.addLog(`🔄 定时任务状态已更新: 已停止`);
            }
        } catch (error) {
            console.error('获取定时任务状态失败:', error);
            this.addLog(`⚠️ 获取定时任务状态失败: ${error.message}`);
        }
    }

    async startScheduler() {
        const cronExpression = document.getElementById('cronExpression').value;
        
        try {
            await this.apiRequest('/scheduler/start', {
                method: 'POST',
                body: JSON.stringify({ 
                    enabled: true, 
                    cron_expression: cronExpression 
                })
            });
            
            this.addLog('定时任务启动成功');
            // 延迟一下再更新状态，确保后端状态已更新
            setTimeout(() => {
                this.updateSchedulerStatus();
            }, 1000);
        } catch (error) {
            this.addLog(`定时任务启动失败: ${error.message}`);
        }
    }

    async stopScheduler() {
        try {
            await this.apiRequest('/scheduler/stop', {
                method: 'POST'
            });
            
            this.addLog('定时任务停止成功');
            // 延迟一下再更新状态，确保后端状态已更新
            setTimeout(() => {
                this.updateSchedulerStatus();
            }, 1000);
        } catch (error) {
            this.addLog(`定时任务停止失败: ${error.message}`);
        }
    }

    async getSchedulerLogs() {
        try {
            const data = await this.apiRequest('/scheduler/logs?lines=50');
            this.addLog('=== 定时任务日志 ===');
            this.addLog(data.logs.join('\n'));
        } catch (error) {
            this.addLog(`获取定时任务日志失败: ${error.message}`);
        }
    }

    // 日志管理
    addLog(message) {
        const logOutput = document.getElementById('logOutput');
        const timestamp = new Date().toLocaleString();
        
        // 优化性能：限制日志行数，避免过多日志导致页面卡顿
        const maxLines = 1000;
        const lines = logOutput.textContent.split('\n');
        if (lines.length > maxLines) {
            // 保留最新的 800 行
            logOutput.textContent = lines.slice(-800).join('\n') + '\n';
        }
        
        // 添加新日志
        logOutput.textContent += `[${timestamp}] ${message}\n`;
        
        // 自动滚动到底部
        logOutput.scrollTop = logOutput.scrollHeight;
        
        // 同时输出到控制台，便于调试
        console.log(`[${timestamp}] ${message}`);
    }

    clearLogs() {
        document.getElementById('logOutput').textContent = '日志已清空\n';
    }

    // 导出结果
    exportResults() {
        // 收集所有tab的股票代码
        const allStockCodes = [];
        const tabData = {};
        
        const tables = [
            { id: 'smartStockTable', name: '智能选股' },
            { id: 'enhancedStockTable', name: '增强选股' },
            { id: 'traditionalStockTable', name: '传统选股' }
        ];
        
        tables.forEach(tableInfo => {
            const table = document.getElementById(tableInfo.id);
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                const codes = [];
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length === 5 && !row.textContent.includes('暂无数据')) {
                        const codeCell = cells[0];
                        const code = codeCell.textContent.trim();
                        if (code && code !== '-') {
                            codes.push(code);
                            if (!allStockCodes.includes(code)) {
                                allStockCodes.push(code);
                            }
                        }
                    }
                });
                
                if (codes.length > 0) {
                    tabData[tableInfo.name] = codes;
                }
            }
        });
        
        if (allStockCodes.length === 0) {
            this.addLog('暂无数据可导出');
            return;
        }

        // 生成导出内容
        let exportContent = '';
        
        // 添加各个策略的股票代码
        Object.keys(tabData).forEach(strategyName => {
            exportContent += `${strategyName}: ${tabData[strategyName].join(',')}\n`;
        });
        
        exportContent += `\n所有股票代码（去重）: ${allStockCodes.join(',')}\n`;
        
        // 创建下载
        const blob = new Blob([exportContent], { type: 'text/plain;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        
        // 使用当前日期作为文件名
        const today = new Date().toISOString().split('T')[0];
        link.download = `selected_stocks_${today}.txt`;
        link.click();

        this.addLog(`已导出 ${allStockCodes.length} 个股票代码（总计），包含${Object.keys(tabData).length}个策略的结果`);
    }

    // 自动执行所有选股策略
    async autoExecuteAllStrategies() {
        const strategies = [
            { key: 'smart', name: '智能选股' },
            { key: 'enhanced', name: '增强选股' },
            { key: 'select', name: '传统选股' }
        ];

        // 获取当前设置的参数
        const preset = document.getElementById('preset').value;
        const limit = parseInt(document.getElementById('limit').value);
        const verbose = document.getElementById('verbose').checked;

        this.addLog(`⚙️ 将使用以下参数执行选股: 风险偏好=${preset}, 数量=${limit}, 详细输出=${verbose}`);

        for (const strategy of strategies) {
            try {
                this.addLog(`🎯 开始执行${strategy.name}...`);
                await this.executeStrategy(strategy.key, preset, limit, verbose);
                this.addLog(`✅ ${strategy.name}完成`);
                
                // 在策略之间添加短暂延迟，避免服务器压力过大
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                this.addLog(`❌ ${strategy.name}执行失败: ${error.message}`);
            }
        }

        this.addLog('🎊 所有选股策略执行完成！');
    }

    // 执行单个选股策略
    async executeStrategy(strategy, preset, limit, verbose) {
        // 根据策略选择不同的API端点
        let apiEndpoint;
        let requestBody;

        switch (strategy) {
            case 'smart':
                apiEndpoint = '/stock/smart-select';
                requestBody = { preset, limit, verbose };
                break;
            case 'enhanced':
                apiEndpoint = '/stock/enhanced-select';
                requestBody = { preset, limit, verbose };
                break;
            case 'select':
            default:
                apiEndpoint = '/stock/select';
                requestBody = { preset, limit, verbose };
                break;
        }

        const data = await this.apiRequest(apiEndpoint, {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });

        if (data.success) {
            if (data.data && data.data.length > 0) {
                this.addLog(`📊 ${this.getStrategyName(strategy)}返回 ${data.data.length} 只股票`);
                // 传递策略参数给displayStocks方法，立即显示结果
                this.displayStocks(data.data, strategy);
                
                // 结果已由后端自动保存到对应的策略文件
                this.addLog(`💾 ${this.getStrategyName(strategy)}结果已保存到文件`);
            } else {
                this.addLog(`⚠️ ${this.getStrategyName(strategy)}没有返回股票数据`);
            }
            
            if (data.log) {
                // 将后端日志以较轻的格式输出
                const logLines = data.log.split('\n').filter(line => line.trim());
                if (logLines.length > 0) {
                    this.addLog(`📋 ${this.getStrategyName(strategy)}详细日志:`);
                    logLines.slice(0, 3).forEach(line => { // 只显示前3行，避免日志过多
                        this.addLog(`   ${line.trim()}`);
                    });
                    if (logLines.length > 3) {
                        this.addLog(`   ... (共${logLines.length}行日志)`);
                    }
                }
            }
        } else {
            throw new Error(data.message || '未知错误');
        }
    }
}

// 全局函数（供HTML调用）
let app;

document.addEventListener('DOMContentLoaded', () => {
    app = new TailTradingApp();
});

function logout() {
    app.logout();
}

function startScheduler() {
    app.startScheduler();
}

function stopScheduler() {
    app.stopScheduler();
}

function getSchedulerLogs() {
    app.getSchedulerLogs();
}

function exportResults() {
    app.exportResults();
}

function clearLogs() {
    app.clearLogs();
}

// 个人设置相关函数
function showUserSettings() {
    const nickname = localStorage.getItem('nickname') || '';
    const username = localStorage.getItem('username') || '';
    
    document.getElementById('userNickname').value = nickname;
    document.getElementById('currentUsername').value = username;
    
    const modal = new bootstrap.Modal(document.getElementById('userSettingsModal'));
    modal.show();
}

function showChangePassword() {
    // 清空表单
    document.getElementById('changePasswordForm').reset();
    
    const modal = new bootstrap.Modal(document.getElementById('changePasswordModal'));
    modal.show();
}

async function updateUserSettings() {
    const nickname = document.getElementById('userNickname').value.trim();
    const username = app.username;
    
    try {
        // 调用后端API更新用户信息
        await app.apiRequest(`/users/${username}`, {
            method: 'PUT',
            body: JSON.stringify({
                nickname: nickname
            })
        });
        
        // 保存到localStorage
        if (nickname) {
            localStorage.setItem('nickname', nickname);
        } else {
            localStorage.removeItem('nickname');
        }
        
        // 更新显示
        const displayName = nickname || username;
        document.getElementById('userInfo').textContent = `欢迎，${displayName}`;
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('userSettingsModal'));
        modal.hide();
        
        app.addLog('个人设置更新成功');
    } catch (error) {
        app.addLog(`个人设置更新失败: ${error.message}`);
    }
}

async function changePassword() {
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (!oldPassword || !newPassword || !confirmPassword) {
        app.addLog('请填写所有密码字段');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        app.addLog('新密码两次输入不一致');
        return;
    }
    
    if (newPassword.length < 6) {
        app.addLog('新密码长度至少6位');
        return;
    }
    
    try {
        // 调用后端API修改密码
        await app.apiRequest(`/users/${app.username}`, {
            method: 'PUT',
            body: JSON.stringify({
                password: newPassword
            })
        });
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('changePasswordModal'));
        modal.hide();
        
        app.addLog('密码修改成功');
        
        // 清空表单
        document.getElementById('changePasswordForm').reset();
    } catch (error) {
        app.addLog(`密码修改失败: ${error.message}`);
    }
}

// 全局函数 - 清理缓存
async function clearCache() {
    if (app) {
        await app.clearCache();
    }
}

// 全局函数 - 清理磁盘数据
async function clearDiskData() {
    if (app) {
        await app.clearDiskData();
    }
}

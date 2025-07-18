// Tail Trading 前端应用

class TailTradingApp {
    constructor() {
        // 自动检测API地址
        this.apiBase = window.location.hostname === 'localhost' && window.location.port === '3000' 
            ? 'http://localhost:8000/api'  // 开发环境
            : '/api';  // 生产环境（通过nginx代理）
        this.token = localStorage.getItem('token');
        this.username = localStorage.getItem('username');
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
        // 页面加载时检查已存在的选股结果
        this.loadExistingStockResults();
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
        this.addLog(`开始更新股票数据（TOP ${topN}）...`);

        // 构造SSE请求，带鉴权
        const url = `${this.apiBase}/stock/update-stream?top_n=${topN}`;
        // 关闭已有流
        if (this._eventSource) {
            this._eventSource.close();
        }
        // 通过 fetch + ReadableStream 实现带 Authorization 的 SSE
        fetch(url, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        }).then(response => {
            if (!response.body) throw new Error('SSE响应无内容');
            const reader = response.body.getReader();
            let buffer = '';
            const utf8Decoder = new TextDecoder('utf-8');
            const processStream = () => reader.read().then(({done, value}) => {
                if (done) return;
                buffer += utf8Decoder.decode(value);
                let lines = buffer.split('\n');
                buffer = lines.pop();
                for (const line of lines) {
                    if (line.startsWith('data:')) {
                        try {
                            const data = JSON.parse(line.slice(5));
                            if (data.type === 'start') {
                                this.addLog(data.message);
                            } else if (data.type === 'log') {
                                this.addLog(data.message);
                            } else if (data.type === 'success') {
                                this.addLog(data.message);
                                loading.classList.remove('show');
                                submitBtn.disabled = false;
                                reader.cancel();
                            } else if (data.type === 'error') {
                                this.addLog(data.message);
                                loading.classList.remove('show');
                                submitBtn.disabled = false;
                                reader.cancel();
                            }
                        } catch (e) {
                            this.addLog('日志解析异常: ' + e.message);
                        }
                    }
                }
                processStream();
            });
            processStream();
        }).catch(err => {
            this.addLog('SSE连接异常: ' + err.message);
            loading.classList.remove('show');
            submitBtn.disabled = false;
        });
    }

    // 股票选择
    async selectStocks() {
        const preset = document.getElementById('preset').value;
        const limit = parseInt(document.getElementById('limit').value);
        const verbose = document.getElementById('verbose').checked;
        const submitBtn = document.querySelector('#selectForm button[type="submit"]');
        const loading = submitBtn.querySelector('.loading');

        try {
            loading.classList.add('show');
            submitBtn.disabled = true;

            this.addLog(`开始选股（策略：${preset}，数量：${limit}）...`);

            const data = await this.apiRequest('/stock/select', {
                method: 'POST',
                body: JSON.stringify({ preset, limit, verbose })
            });

            if (data.success) {
                this.addLog('选股完成！');
                
                // 添加调试信息
                console.log('选股API返回数据:', data);
                this.addLog(`API返回数据结构: success=${data.success}, data长度=${data.data ? data.data.length : 0}`);
                
                if (data.data && data.data.length > 0) {
                    this.addLog(`准备显示 ${data.data.length} 只股票`);
                    this.displayStocks(data.data);
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
            const data = await this.apiRequest('/stock/existing-results');
            if (data.success && data.data && data.data.length > 0) {
                this.addLog(`发现已存在的选股结果，共 ${data.data.length} 只股票`);
                this.displayStocks(data.data);
            } else {
                this.addLog('暂无已存在的选股结果');
            }
        } catch (error) {
            console.log('加载已存在选股结果失败:', error.message);
            // 不显示错误信息，因为可能是首次使用
        }
    }

    // 显示股票结果
    displayStocks(stocks) {
        console.log('displayStocks被调用，股票数据:', stocks);
        this.addLog(`🔍 开始显示股票数据，共 ${stocks ? stocks.length : 0} 只`);
        
        const tbody = document.querySelector('#stockTable tbody');
        tbody.innerHTML = '';

        if (!stocks || stocks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">暂无数据</td></tr>';
            this.addLog('❌ 股票数据为空，显示暂无数据');
            return;
        }

        stocks.forEach((stock, index) => {
            console.log(`处理第${index + 1}只股票:`, stock);
            
            const row = document.createElement('tr');
            // 适配后端返回的中文字段名
            const code = stock.代码 || stock.code || '-';
            const name = stock.名称 || stock.name || '-';
            const probability = stock.次日补涨概率 || stock.probability_score || '-';
            const risk = stock.风险评分 || stock.risk_level || '-';
            const action = stock.操作建议 || stock.action || '买入';
            
            this.addLog(`📊 股票${index + 1}: ${code} ${name}`);
            
            // 生成东方财富链接
            const eastmoneyUrl = this.generateEastmoneyUrl(code);
            
            row.innerHTML = `
                <td><a href="${eastmoneyUrl}" target="_blank" class="stock-code-link">${code}</a></td>
                <td>${name}</td>
                <td>${typeof probability === 'number' ? probability.toFixed(2) + '%' : probability}</td>
                <td>${typeof risk === 'number' ? risk.toFixed(2) : risk}</td>
                <td>${action}</td>
            `;
            tbody.appendChild(row);
        });

        this.addLog(`✅ 成功显示 ${stocks.length} 只股票的选择结果`);
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
                    toggleBtn.className = 'btn btn-success';
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
        logOutput.textContent += `[${timestamp}] ${message}\n`;
        logOutput.scrollTop = logOutput.scrollHeight;
    }

    clearLogs() {
        document.getElementById('logOutput').textContent = '日志已清空\n';
    }

    // 导出结果
    exportResults() {
        const table = document.getElementById('stockTable');
        const rows = table.querySelectorAll('tbody tr');
        
        if (rows.length === 1 && rows[0].textContent.includes('暂无数据')) {
            this.addLog('暂无数据可导出');
            return;
        }

        // 提取股票代码
        const stockCodes = [];
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length === 5) {
                // 第一列是股票代码链接，提取文本内容
                const codeCell = cells[0];
                const code = codeCell.textContent.trim();
                if (code && code !== '-') {
                    stockCodes.push(code);
                }
            }
        });

        if (stockCodes.length === 0) {
            this.addLog('没有找到有效的股票代码');
            return;
        }

        // 生成逗号分隔的股票代码文件
        const codesText = stockCodes.join(',');
        const blob = new Blob([codesText], { type: 'text/plain;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        
        // 使用当前日期作为文件名
        const today = new Date().toISOString().split('T')[0];
        link.download = `selected_stocks_${today}.txt`;
        link.click();

        this.addLog(`已导出 ${stockCodes.length} 个股票代码: ${codesText}`);
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

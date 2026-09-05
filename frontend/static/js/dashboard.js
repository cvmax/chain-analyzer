/**
 * 区块链活跃度分析仪表盘 - JavaScript
 */
const API_BASE = "/api";
let currentChain = "uni";
let charts = {};
let fullData = {};

// ========== 初始化 ==========
document.addEventListener("DOMContentLoaded", () => {
    initChainSelector();
    loadChainData(currentChain);
});

function initChainSelector() {
    document.querySelectorAll(".chain-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".chain-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const chain = btn.dataset.chain;
            if (chain === "compare") {
                currentChain = "compare";
                loadCompareData();
            } else {
                currentChain = chain;
                loadChainData(chain);
            }
        });
    });
}

// ========== 数据加载 ==========
async function loadChainData(chainId) {
    showLoading();
    setStatus(`加载 ${chainId.toUpperCase()} 数据中...`);

    try {
        const resp = await fetch(`${API_BASE}/chain/${chainId}/full`);
        const json = await resp.json();
        if (json.status !== "ok") {
            showError(json.message);
            return;
        }
        fullData = json.data;
        renderAll(json.data);
        setStatus("数据已更新");
    } catch (err) {
        showError("无法连接服务器: " + err.message);
    }
}

async function loadCompareData() {
    showLoading();
    setStatus("加载对比数据中...");

    document.getElementById("metric-cards").innerHTML = "";
    document.getElementById("chart-tvl-section").style.display = "none";
    document.getElementById("chart-dev-section").style.display = "none";
    document.getElementById("developer-section-container").innerHTML = "";
    document.getElementById("news-section").style.display = "none";

    try {
        const resp = await fetch(`${API_BASE}/compare`);
        const json = await resp.json();
        if (json.status !== "ok") {
            showError(json.message);
            return;
        }
        renderCompareTable(json.data);
        setStatus("对比数据已加载");
    } catch (err) {
        showError("无法连接服务器: " + err.message);
    }
}

// ========== 渲染函数 ==========
function renderAll(data) {
    document.getElementById("chart-tvl-section").style.display = "";
    document.getElementById("chart-dev-section").style.display = "";
    document.getElementById("news-section").style.display = "";

    renderMetricCards(data);
    renderCharts(data);
    renderDeveloperSection(data.developer);
    renderNewsSection(data.news);
}

function renderMetricCards(data) {
    const summary = data.summary || {};
    const market = summary.market || {};
    const defi = summary.defi || {};
    const onchain = summary.onchain || {};
    const dev = data.developer || {};

    const cards = [
        {
            label: "当前价格",
            value: formatUSD(market.price_usd),
            change: market.price_change_24h,
            changeLabel: "24h"
        },
        {
            label: "市值",
            value: formatLargeNum(market.market_cap),
            change: null,
            changeLabel: ""
        },
        {
            label: "24h 交易量",
            value: formatLargeNum(market.volume_24h),
            change: null,
            changeLabel: ""
        },
        {
            label: "TVL (锁仓量)",
            value: formatLargeNum(defi.tvl),
            change: defi.tvl_change_24h,
            changeLabel: "24h"
        },
        {
            label: "开发者活跃度",
            value: dev.activity_score || "N/A",
            change: dev.activity_level || "",
            changeLabel: "",
            isScore: true
        },
        {
            label: "GitHub Stars",
            value: formatNum(dev.total_stars),
            change: null,
            changeLabel: ""
        },
        {
            label: "12周提交数",
            value: formatNum(dev.total_commits_12w),
            change: null,
            changeLabel: ""
        },
        {
            label: "新闻情绪",
            value: (data.news || {}).overall_sentiment || "N/A",
            change: null,
            changeLabel: "",
            isSentiment: true
        },
    ];

    const container = document.getElementById("metric-cards");
    container.innerHTML = cards.map(c => `
        <div class="metric-card">
            <div class="metric-label">${c.label}</div>
            <div class="metric-value">${c.value}</div>
            ${c.change != null && typeof c.change === 'number' ? `
                <div class="metric-change ${c.change > 0 ? 'positive' : c.change < 0 ? 'negative' : 'neutral'}">
                    ${c.change > 0 ? '▲' : c.change < 0 ? '▼' : ''} ${c.change.toFixed(2)}% ${c.changeLabel}
                </div>
            ` : ''}
            ${c.isScore ? `<div class="metric-change neutral">${c.change}</div>` : ''}
        </div>
    `).join("");
}

function renderCharts(data) {
    const dev = data.developer || {};
    const defi = (data.summary || {}).defi || {};
    const market = (data.summary || {}).market || {};

    // Chart 1: TVL / 市值对比
    const chartTvl = document.getElementById("chart-tvl");
    if (chartTvl) {
        if (charts.tvl) charts.tvl.destroy();
        charts.tvl = new Chart(chartTvl, {
            type: "bar",
            data: {
                labels: ["TVL", "市值", "24h 交易量"],
                datasets: [{
                    label: "USD",
                    data: [
                        defi.tvl || 0,
                        market.market_cap || 0,
                        market.volume_24h || 0
                    ],
                    backgroundColor: [
                        "rgba(139, 92, 246, 0.7)",
                        "rgba(59, 130, 246, 0.7)",
                        "rgba(16, 185, 129, 0.7)",
                    ],
                    borderColor: [
                        "rgba(139, 92, 246, 1)",
                        "rgba(59, 130, 246, 1)",
                        "rgba(16, 185, 129, 1)",
                    ],
                    borderWidth: 1,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: ctx => formatLargeNum(ctx.raw)
                        }
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            color: "#9ca3af",
                            callback: v => formatLargeNum(v)
                        },
                        grid: { color: "rgba(42, 49, 66, 0.5)" }
                    },
                    x: {
                        ticks: { color: "#9ca3af" },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // Chart 2: 开发者提交活动
    const chartDev = document.getElementById("chart-dev");
    const weeklyData = dev.weekly_commits || {};
    const weeks = Object.keys(weeklyData).sort();
    const commits = weeks.map(w => weeklyData[w]);

    if (chartDev) {
        if (charts.dev) charts.dev.destroy();
        charts.dev = new Chart(chartDev, {
            type: "line",
            data: {
                labels: weeks.map(w => {
                    const d = new Date(w * 1000);
                    return `${d.getMonth() + 1}/${d.getDate()}`;
                }),
                datasets: [{
                    label: "周提交数",
                    data: commits,
                    borderColor: "rgba(139, 92, 246, 1)",
                    backgroundColor: "rgba(139, 92, 246, 0.1)",
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointBackgroundColor: "rgba(139, 92, 246, 1)",
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        ticks: { color: "#9ca3af" },
                        grid: { color: "rgba(42, 49, 66, 0.5)" },
                        beginAtZero: true,
                    },
                    x: {
                        ticks: { color: "#9ca3af", maxTicksLimit: 6 },
                        grid: { display: false }
                    }
                }
            }
        });
    }
}

function renderDeveloperSection(devData) {
    if (!devData || devData.error) {
        document.getElementById("developer-section-container").innerHTML = `
            <div class="section empty-state">暂无开发者数据</div>
        `;
        return;
    }

    const repos = devData.repos || [];
    const container = document.getElementById("developer-section-container");
    container.innerHTML = `
        <div class="section">
            <div class="section-header">
                <span class="section-title">GitHub 仓库活跃度</span>
                <span class="score-badge ${devData.activity_level === '高' ? 'high' : devData.activity_level === '中' ? 'medium' : 'low'}">
                    活跃度: ${devData.activity_level} (${devData.activity_score}/100)
                </span>
            </div>
            ${devData.rate_limited ? `<div style="color: var(--yellow); font-size: 0.8rem; margin-bottom: 12px; padding: 8px 12px; background: rgba(245,158,11,0.1); border-radius: 6px;">${devData.note || 'GitHub API 限流中，配置 GITHUB_TOKEN 环境变量获取实时数据'}</div>` : ""}
            ${repos.map(r => `
                <div class="repo-card">
                    <div class="repo-name">${r.repo}</div>
                    <div class="repo-stats">
                        <span>⭐ ${formatNum(r.stars)}</span>
                        <span>🍴 ${formatNum(r.forks)}</span>
                        <span>📋 ${formatNum(r.open_issues)} Issues</span>
                        <span>🕐 ${r.updated_at ? new Date(r.updated_at).toLocaleDateString("zh-CN") : "N/A"}</span>
                        ${r.language ? `<span>📝 ${r.language}</span>` : ""}
                    </div>
                </div>
            `).join("")}
        </div>

        <div class="section">
            <div class="section-header">
                <span class="section-title">持有者分布</span>
            </div>
            <div id="holder-data">
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <div>加载中...</div>
                </div>
            </div>
        </div>
    `;

    // 加载持有者数据
    loadHolderData();
}

async function loadHolderData() {
    try {
        const resp = await fetch(`${API_BASE}/chain/${currentChain}/holders`);
        const json = await resp.json();
        const data = json.data || {};

        const container = document.getElementById("holder-data");
        if (!data.total_holders && !data.total_addresses) {
            container.innerHTML = `<div class="empty-state">暂无持有者分布数据</div>`;
            return;
        }

        if (data.total_holders !== undefined) {
            // ERC-20
            const topHolders = data.top_holders || [];
            container.innerHTML = `
                <div class="grid-3" style="margin-bottom: 16px;">
                    <div class="metric-card">
                        <div class="metric-label">总持有者</div>
                        <div class="metric-value">${formatNum(data.total_holders)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">集中度</div>
                        <div class="metric-value">${data.concentration?.level || "未知"}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">代币名称</div>
                        <div class="metric-value">${data.token_name || "N/A"}</div>
                    </div>
                </div>
                ${topHolders.length > 0 ? `
                    <div class="section-header" style="border-bottom: none; padding-bottom: 0; margin-bottom: 8px;">
                        <span class="section-title" style="font-size: 0.9rem;">前 10 大持有者</span>
                    </div>
                    ${topHolders.map(h => `
                        <div class="repo-card" style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.8rem; color: var(--text-muted);">${h.address}</span>
                            <span style="font-size: 0.85rem; font-weight: 600;">
                                ${formatNum(h.balance)} ${currentChain.toUpperCase()}
                                <span style="color: var(--text-muted); font-weight: 400;">(${h.share_pct}%)</span>
                            </span>
                        </div>
                    `).join("")}
                ` : ""}
            `;
        } else if (data.total_addresses !== undefined) {
            // PoW chain
            container.innerHTML = `
                <div class="grid-3">
                    <div class="metric-card">
                        <div class="metric-label">总地址数</div>
                        <div class="metric-value">${formatNum(data.total_addresses)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">24h 活跃地址</div>
                        <div class="metric-value">${formatNum(data.active_addresses_24h)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">24h 交易数</div>
                        <div class="metric-value">${formatNum(data.transactions_24h)}</div>
                    </div>
                </div>
            `;
        }
    } catch (err) {
        document.getElementById("holder-data").innerHTML = `<div class="empty-state">加载失败</div>`;
    }
}

function renderNewsSection(newsData) {
    if (!newsData) {
        document.getElementById("news-section").innerHTML = "";
        return;
    }

    const articles = newsData.articles || [];
    const breakdown = newsData.sentiment_breakdown || { positive: 0, negative: 0, neutral: 0 };
    const total = articles.length || 1;

    // Sentiment overview
    document.getElementById("sentiment-overview").innerHTML = `
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
            <span style="font-size: 0.85rem; color: var(--text-secondary);">
                共 <strong>${articles.length}</strong> 条新闻
            </span>
            <span style="font-size: 0.85rem; color: var(--green);">
                利好: ${breakdown.positive}
            </span>
            <span style="font-size: 0.85rem; color: var(--red);">
                利空: ${breakdown.negative}
            </span>
            <span style="font-size: 0.85rem; color: var(--text-muted);">
                中性: ${breakdown.neutral}
            </span>
            <span style="font-size: 0.85rem; color: var(--text-secondary); margin-left: auto;">
                综合情绪: <strong>${newsData.overall_sentiment || "N/A"}</strong>
            </span>
        </div>
        <div class="sentiment-bar">
            <div class="pos" style="width: ${(breakdown.positive / total * 100).toFixed(1)}%;"></div>
            <div class="neu" style="width: ${(breakdown.neutral / total * 100).toFixed(1)}%;"></div>
            <div class="neg" style="width: ${(breakdown.negative / total * 100).toFixed(1)}%;"></div>
        </div>
    `;

    // News list
    renderNewsList(articles);

    // News tabs
    document.querySelectorAll("#news-tabs .tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll("#news-tabs .tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            const filter = tab.dataset.tab;
            if (filter === "all") {
                renderNewsList(articles);
            } else {
                renderNewsList(articles.filter(a => a.sentiment === filter));
            }
        });
    });
}

function renderNewsList(articles) {
    const container = document.getElementById("news-list");
    if (!articles.length) {
        container.innerHTML = `<div class="empty-state">暂无相关新闻</div>`;
        return;
    }

    container.innerHTML = articles.map(a => {
        const date = a.date ? new Date(a.date).toLocaleDateString("zh-CN") : "";
        return `
            <div class="news-item">
                <div class="news-title">
                    <a href="${a.url || '#'}" target="_blank" rel="noopener">${a.title}</a>
                </div>
                <div class="news-meta">
                    <span>${a.source || ""}</span>
                    <span>${date}</span>
                    <span class="sentiment-tag ${a.sentiment}">${a.sentiment === "positive" ? "利好" : a.sentiment === "negative" ? "利空" : "中性"}</span>
                    ${a.votes ? `<span>👍 ${a.votes}</span>` : ""}
                </div>
            </div>
        `;
    }).join("");
}

function renderCompareTable(data) {
    const chains = Object.keys(data);
    const chainNames = {};
    chains.forEach(c => {
        chainNames[c] = (data[c].summary || {}).name || c.toUpperCase();
    });

    // 构建对比数据行
    const rows = [
        { label: "价格 (USD)", key: ["summary", "market", "price_usd"], fmt: formatUSD },
        { label: "市值", key: ["summary", "market", "market_cap"], fmt: formatLargeNum },
        { label: "24h 交易量", key: ["summary", "market", "volume_24h"], fmt: formatLargeNum },
        { label: "TVL", key: ["summary", "defi", "tvl"], fmt: formatLargeNum },
        { label: "开发者活跃度", key: ["developer", "activity_score"], fmt: v => v || "N/A" },
        { label: "GitHub Stars", key: ["developer", "total_stars"], fmt: formatNum },
        { label: "12周提交数", key: ["developer", "total_commits_12w"], fmt: formatNum },
    ];

    // 对每个指标排名
    function getValue(d, key) {
        let obj = d;
        for (const k of key) {
            obj = (obj || {})[k];
        }
        return obj || 0;
    }

    const mainContent = document.getElementById("main-content");
    mainContent.innerHTML = `
        <div class="section">
            <div class="section-header">
                <span class="section-title">横向对比: ${chains.map(c => chainNames[c]).join(" vs ")}</span>
            </div>
            <div style="overflow-x: auto;">
                <table class="compare-table">
                    <thead>
                        <tr>
                            <th>指标</th>
                            ${chains.map(c => `<th>${chainNames[c]}</th>`).join("")}
                        </tr>
                    </thead>
                    <tbody>
                        ${rows.map(row => {
                            const values = chains.map(c => getValue(data[c], row.key));
                            // 排名 (数值越大越好，除价格外)
                            const sorted = [...values].sort((a, b) => b - a);
                            const ranks = values.map(v => sorted.indexOf(v) + 1);

                            return `
                                <tr>
                                    <td>${row.label}</td>
                                    ${values.map((v, i) => {
                                        const rankClass = ranks[i] === 1 ? "rank-1" : ranks[i] === 2 ? "rank-2" : "rank-3";
                                        return `
                                            <td>
                                                <span class="rank-badge ${rankClass}">${ranks[i]}</span>
                                                ${row.fmt(v)}
                                            </td>
                                        `;
                                    }).join("")}
                                </tr>
                            `;
                        }).join("")}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// ========== 工具函数 ==========
function formatUSD(v) {
    if (v == null || isNaN(v)) return "N/A";
    return "$" + v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 6 });
}

function formatLargeNum(v) {
    if (v == null || isNaN(v)) return "N/A";
    if (v >= 1e9) return "$" + (v / 1e9).toFixed(2) + "B";
    if (v >= 1e6) return "$" + (v / 1e6).toFixed(2) + "M";
    if (v >= 1e3) return "$" + (v / 1e3).toFixed(2) + "K";
    return "$" + v.toFixed(2);
}

function formatNum(v) {
    if (v == null || isNaN(v)) return "N/A";
    if (v >= 1e9) return (v / 1e9).toFixed(2) + "B";
    if (v >= 1e6) return (v / 1e6).toFixed(2) + "M";
    if (v >= 1e3) return (v / 1e3).toFixed(2) + "K";
    return v.toLocaleString("en-US");
}

function showLoading() {
    document.getElementById("metric-cards").innerHTML = `
        <div class="loading" style="grid-column: 1/-1;">
            <div class="loading-spinner"></div>
            <div>加载数据中...</div>
        </div>
    `;
}

function showError(msg) {
    document.getElementById("metric-cards").innerHTML = `
        <div class="empty-state" style="grid-column: 1/-1; color: var(--red);">
            ${msg}
        </div>
    `;
    setStatus("错误");
}

function setStatus(text) {
    document.getElementById("status-text").textContent = text;
}
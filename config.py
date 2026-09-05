"""
链上数据分析工具 - 配置文件
"""
import os

# 项目配置
PROJECT_NAME = "区块链活跃度分析仪表盘"
VERSION = "1.0.0"

# 支持的项目列表
SUPPORTED_CHAINS = {
    "uni": {
        "name": "Uniswap",
        "symbol": "UNI",
        "type": "erc20",
        "contract_address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "chain": "ethereum",
        "github_repos": ["Uniswap/v3-core", "Uniswap/v3-periphery", "Uniswap/interface"],
        "defillama_slug": "uniswap",
        "coingecko_id": "uniswap",
        "explorer": "etherscan",
        "description": "去中心化交易所协议 (DEX)"
    },
    "crv": {
        "name": "Curve",
        "symbol": "CRV",
        "type": "erc20",
        "contract_address": "0xD533a949740bb3306d119CC777fa900bA034cd52",
        "chain": "ethereum",
        "github_repos": ["curvefi/curve-contract", "curvefi/curve-dao-contracts"],
        "defillama_slug": "curve-finance",
        "coingecko_id": "curve-dao-token",
        "explorer": "etherscan",
        "description": "稳定币交易去中心化协议"
    },
    "near": {
        "name": "NEAR Protocol",
        "symbol": "NEAR",
        "type": "layer1",
        "chain": "near",
        "github_repos": ["near/nearcore", "near/near-api-js"],
        "defillama_slug": "near",
        "coingecko_id": "near",
        "explorer": "near",
        "description": "Layer1 分片公链"
    },
    "ltc": {
        "name": "Litecoin",
        "symbol": "LTC",
        "type": "layer1",
        "chain": "litecoin",
        "github_repos": ["litecoin-project/litecoin"],
        "defillama_slug": None,
        "coingecko_id": "litecoin",
        "explorer": "blockchair",
        "description": "比特币的轻量级分叉，点对点电子现金"
    }
}

# API 配置 (免费 API，无需 key 即可使用)
API_CONFIG = {
    "etherscan": {
        "base_url": "https://api.etherscan.io/api",
        "api_key": os.environ.get("ETHERSCAN_API_KEY", "YourApiKeyToken"),
    },
    "defillama": {
        "base_url": "https://api.llama.fi",
    },
    "coingecko": {
        "base_url": "https://api.coingecko.com/api/v3",
    },
    "blockchair": {
        "base_url": "https://api.blockchair.com",
    },
    "near_explorer": {
        "base_url": "https://api.nearblocks.io/v1",
    },
    "cryptopanic": {
        "base_url": "https://cryptopanic.com/api/v1",
        "api_key": os.environ.get("CRYPTOPANIC_API_KEY", ""),
    },
    "github": {
        "base_url": "https://api.github.com",
        "token": os.environ.get("GITHUB_TOKEN", ""),
    }
}

# 缓存配置
CACHE_TTL = 300  # 缓存有效期 (秒)

# 新闻源 RSS 配置
NEWS_RSS_SOURCES = [
    "https://cointelegraph.com/rss",
    "https://cryptoslate.com/feed/",
    "https://decrypt.co/feed",
]
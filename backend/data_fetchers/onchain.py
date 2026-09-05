"""
链上数据采集模块
- 活跃地址 / 交易数 / 交易金额
- TVL 与 DeFi 生态数据
- 市场数据（价格、市值、交易量）

可用 API:
- DeFiLlama: TVL 数据
- Blockchair: Ethereum/Litecoin 链上统计 + 市场数据
- nearblocks.io: NEAR 链上统计 + 市场数据
"""
import time
from config import API_CONFIG, SUPPORTED_CHAINS
from .http_utils import http_get as http

CACHE = {}


def _cached(key, fetcher, ttl=300):
    now = time.time()
    if key in CACHE and CACHE[key][0] > now - ttl:
        return CACHE[key][1]
    data = fetcher()
    CACHE[key] = (now, data)
    return data


def fetch_defillama_tvl(chain_id):
    """获取 DeFiLlama TVL 数据"""
    chain = SUPPORTED_CHAINS[chain_id]
    cfg = API_CONFIG["defillama"]
    slug = chain.get("defillama_slug")

    if not slug:
        return {"tvl": 0, "tvl_change_24h": 0, "note": "该链无 DeFi TVL 数据"}

    def _fetch():
        results = {}
        try:
            r = http(f"{cfg['base_url']}/tvl/{slug}", timeout=10)
            if r.status_code == 200 and isinstance(r.json(), (int, float)):
                results["tvl"] = round(r.json(), 2)
        except Exception:
            results["tvl"] = 0

        try:
            r = http(f"{cfg['base_url']}/protocol/{slug}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                results["tvl_change_24h"] = data.get("change_1d", 0)
                results["tvl_change_7d"] = data.get("change_7d", 0)
                results["tvl_change_30d"] = data.get("change_1m", 0)
                results["category"] = data.get("category", "")
                results["chains"] = data.get("chains", [])
        except Exception:
            pass
        return results

    return _cached(f"defillama_{chain_id}", _fetch)


def fetch_blockchair_ethereum_stats():
    """获取以太坊网络统计（含市场数据）"""
    cfg = API_CONFIG["blockchair"]

    def _fetch():
        try:
            r = http(f"{cfg['base_url']}/ethereum/stats", timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", {})
                return {
                    "blocks": data.get("blocks", 0),
                    "transactions": data.get("transactions", 0),
                    "transactions_24h": data.get("transactions_24h", 0),
                    "mempool_transactions": data.get("mempool_transactions", 0),
                    "mempool_tps": data.get("mempool_tps", 0),
                    "avg_tx_fee_24h_usd": data.get("average_transaction_fee_usd_24h", 0),
                    "market_price_usd": data.get("market_price_usd", 0),
                    "market_price_btc": data.get("market_price_btc", 0),
                    "market_cap_usd": data.get("market_cap_usd", 0),
                    "market_dominance_pct": data.get("market_dominance_percentage", 0),
                    "price_change_24h_pct": data.get("market_price_usd_change_24h_percentage", 0),
                    "volume_24h_usd": data.get("volume_24h_approximate", 0),
                    "erc20": data.get("layer_2", {}).get("erc_20", {}),
                    "erc721": data.get("layer_2", {}).get("erc_721", {}),
                }
        except Exception:
            return {}
        return {}

    return _cached("blockchair_eth", _fetch, ttl=120)


def fetch_blockchair_chain_stats(chain_id):
    """获取 Blockchair 链上统计 (LTC)"""
    chain = SUPPORTED_CHAINS[chain_id]
    cfg = API_CONFIG["blockchair"]
    chain_name = chain["chain"]

    def _fetch():
        try:
            r = http(f"{cfg['base_url']}/{chain_name}/stats", timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", {})
                return {
                    "blocks": data.get("blocks", 0),
                    "transactions": data.get("transactions", 0),
                    "transactions_24h": data.get("transactions_24h", 0),
                    "circulation": data.get("circulation", 0),
                    "difficulty": data.get("difficulty", 0),
                    "hashrate_24h": data.get("hashrate_24h", ""),
                    "mempool_transactions": data.get("mempool_transactions", 0),
                    "avg_tx_fee_24h": data.get("suggested_transaction_fee_per_byte_sat", 0),
                    "market_price_usd": data.get("market_price_usd", 0),
                    "market_cap_usd": data.get("market_cap_usd", 0),
                    "volume_24h_usd": data.get("volume_24h_usd", 0),
                    "price_change_24h_pct": data.get("market_price_usd_change_24h_percentage", 0),
                    "active_addresses_24h": data.get("addresses_24h", 0),
                }
        except Exception:
            return {}
        return {}

    return _cached(f"blockchair_{chain_id}", _fetch, ttl=120)


def fetch_near_explorer_data():
    """获取 NEAR 链上数据"""
    cfg = API_CONFIG["near_explorer"]

    def _fetch():
        try:
            r = http(f"{cfg['base_url']}/stats", timeout=10)
            if r.status_code == 200:
                data = r.json().get("stats", [{}])[0]
                return {
                    "total_transactions": data.get("total_txns", 0),
                    "tps": data.get("tps", 0),
                    "nodes_online": data.get("nodes_online", 0),
                    "avg_block_time": data.get("avg_block_time", 0),
                    "circulating_supply": data.get("circulating_supply", ""),
                    "total_supply": data.get("total_supply", ""),
                    "market_price_usd": float(data.get("near_price", 0)),
                    "market_cap_usd": float(data.get("market_cap", 0)),
                    "volume_24h_usd": float(data.get("volume", 0)),
                    "price_change_24h_pct": float(data.get("change_24", 0)),
                    "high_24h": float(data.get("high_24h", 0)),
                    "low_24h": float(data.get("low_24h", 0)),
                }
        except Exception:
            return {}
        return {}

    return _cached("near_explorer", _fetch, ttl=120)


def get_onchain_summary(chain_id):
    """获取链上数据综合摘要"""
    chain = SUPPORTED_CHAINS.get(chain_id)
    if not chain:
        return {"error": f"不支持的项目: {chain_id}"}

    summary = {
        "chain_id": chain_id,
        "name": chain["name"],
        "symbol": chain["symbol"],
        "type": chain["type"],
        "description": chain["description"],
    }

    explorer_type = chain.get("explorer", "")

    # 市场数据
    if explorer_type == "etherscan":
        eth_data = fetch_blockchair_ethereum_stats()
        # UNI/CRV 代币价格需要单独获取，这里用 ETH 网络数据作为参考
        summary["market"] = {
            "price_usd": eth_data.get("market_price_usd", 0),
            "market_cap": eth_data.get("market_cap_usd", 0),
            "volume_24h": eth_data.get("volume_24h_usd", 0),
            "price_change_24h": eth_data.get("price_change_24h_pct", 0),
            "note": f"以太坊网络数据 (非{chain['symbol']}代币价格)"
        }
        summary["onchain"] = {
            "network_transactions_24h": eth_data.get("transactions_24h", 0),
            "erc20_tokens": eth_data.get("erc20", {}).get("tokens", 0),
            "erc20_transactions_24h": eth_data.get("erc20", {}).get("transactions_24h", 0),
            "avg_tx_fee_24h_usd": eth_data.get("avg_tx_fee_24h_usd", 0),
            "mempool_tps": eth_data.get("mempool_tps", 0),
            "note": "以太坊网络数据，反映整体链上活跃度"
        }
    elif explorer_type == "blockchair":
        bc_data = fetch_blockchair_chain_stats(chain_id)
        summary["market"] = {
            "price_usd": bc_data.get("market_price_usd", 0),
            "market_cap": bc_data.get("market_cap_usd", 0),
            "volume_24h": bc_data.get("volume_24h_usd", 0),
            "price_change_24h": bc_data.get("price_change_24h_pct", 0),
        }
        summary["onchain"] = {
            "transactions_24h": bc_data.get("transactions_24h", 0),
            "total_transactions": bc_data.get("transactions", 0),
            "active_addresses_24h": bc_data.get("active_addresses_24h", 0),
            "hashrate_24h": bc_data.get("hashrate_24h", ""),
            "mempool_transactions": bc_data.get("mempool_transactions", 0),
            "avg_tx_fee_24h": bc_data.get("avg_tx_fee_24h", 0),
        }
    elif explorer_type == "near":
        near_data = fetch_near_explorer_data()
        summary["market"] = {
            "price_usd": near_data.get("market_price_usd", 0),
            "market_cap": near_data.get("market_cap_usd", 0),
            "volume_24h": near_data.get("volume_24h_usd", 0),
            "price_change_24h": near_data.get("price_change_24h_pct", 0),
        }
        summary["onchain"] = {
            "total_transactions": near_data.get("total_transactions", 0),
            "tps": near_data.get("tps", 0),
            "nodes_online": near_data.get("nodes_online", 0),
            "avg_block_time": near_data.get("avg_block_time", 0),
        }

    # TVL / DeFi 数据
    summary["defi"] = fetch_defillama_tvl(chain_id)

    return summary
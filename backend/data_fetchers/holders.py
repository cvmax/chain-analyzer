"""
代币持有者分布数据采集
- 持币地址数 / 活跃地址
- 持仓集中度
"""
import time
from config import API_CONFIG, SUPPORTED_CHAINS
from .http_utils import http_get as http

CACHE = {}


def _cached(key, fetcher, ttl=600):
    now = time.time()
    if key in CACHE and CACHE[key][0] > now - ttl:
        return CACHE[key][1]
    data = fetcher()
    CACHE[key] = (now, data)
    return data


def fetch_blockchair_holders(chain_id):
    """获取链的地址活跃度数据"""
    chain = SUPPORTED_CHAINS[chain_id]
    cfg = API_CONFIG["blockchair"]
    chain_name = chain["chain"]

    def _fetch():
        try:
            r = http(f"{cfg['base_url']}/{chain_name}/stats", timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", {})
                return {
                    "total_addresses": data.get("addresses", 0),
                    "active_addresses_24h": data.get("addresses_24h", 0),
                    "transactions_24h": data.get("transactions_24h", 0),
                    "avg_tx_value_24h_usd": data.get("transaction_volume_24h_usd", 0),
                    "concentration": {"level": "PoW链，以地址活跃度衡量"},
                }
        except Exception:
            pass
        return {}

    return _cached(f"holders_{chain_id}", _fetch)


def fetch_ethereum_holders(chain_id):
    """获取以太坊网络 ERC-20 代币的持有者分布（通过 Blockchair 以太坊数据）"""
    def _fetch():
        eth_data = {}
        try:
            r = http(f"{API_CONFIG['blockchair']['base_url']}/ethereum/stats", timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", {})
                erc20 = data.get("layer_2", {}).get("erc_20", {})
                eth_data = {
                    "total_erc20_tokens": erc20.get("tokens", 0),
                    "erc20_transactions": erc20.get("transactions", 0),
                    "erc20_transactions_24h": erc20.get("transactions_24h", 0),
                    "total_transactions_24h": data.get("transactions_24h", 0),
                    "mempool_transactions": data.get("mempool_transactions", 0),
                    "concentration": {
                        "level": "基于以太坊整体 ERC-20 活跃度",
                        "note": "代币具体持有者数据需 Etherscan API Key"
                    },
                }
        except Exception:
            pass
        return eth_data

    return _cached(f"holders_eth_{chain_id}", _fetch)


def get_holder_distribution(chain_id):
    """获取代币持有者分布综合数据"""
    chain = SUPPORTED_CHAINS.get(chain_id)
    if not chain:
        return {"error": f"不支持的项目: {chain_id}"}

    explorer_type = chain.get("explorer", "")
    if explorer_type == "etherscan":
        return fetch_ethereum_holders(chain_id)
    elif explorer_type == "blockchair":
        return fetch_blockchair_holders(chain_id)
    else:
        return {"total_holders": 0, "note": "该链暂不支持持有者分布查询"}
"""
区块链活跃度分析仪表盘 - Flask 后端
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from data_fetchers import (
    get_onchain_summary,
    get_developer_activity,
    get_holder_distribution,
    get_news_for_chain,
    get_all_news,
)
from config import SUPPORTED_CHAINS, PROJECT_NAME, VERSION

_root = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(_root, "..", "frontend", "templates"),
    static_folder=os.path.join(_root, "..", "frontend", "static"),
)
CORS(app)


@app.route("/")
def index():
    return render_template("index.html", project_name=PROJECT_NAME)


@app.route("/api/chains")
def list_chains():
    """列出所有支持的项目"""
    chains = []
    for chain_id, info in SUPPORTED_CHAINS.items():
        chains.append({
            "id": chain_id,
            "name": info["name"],
            "symbol": info["symbol"],
            "type": info["type"],
            "description": info["description"],
        })
    return jsonify({"status": "ok", "chains": chains})


@app.route("/api/chain/<chain_id>/summary")
def chain_summary(chain_id):
    """获取单个链的综合数据"""
    if chain_id not in SUPPORTED_CHAINS:
        return jsonify({"status": "error", "message": f"不支持的项目: {chain_id}"}), 404

    return jsonify({
        "status": "ok",
        "data": get_onchain_summary(chain_id)
    })


@app.route("/api/chain/<chain_id>/developer")
def chain_developer(chain_id):
    """获取开发者活跃度"""
    if chain_id not in SUPPORTED_CHAINS:
        return jsonify({"status": "error", "message": f"不支持的项目: {chain_id}"}), 404

    return jsonify({
        "status": "ok",
        "data": get_developer_activity(chain_id)
    })


@app.route("/api/chain/<chain_id>/holders")
def chain_holders(chain_id):
    """获取代币持有者分布"""
    if chain_id not in SUPPORTED_CHAINS:
        return jsonify({"status": "error", "message": f"不支持的项目: {chain_id}"}), 404

    return jsonify({
        "status": "ok",
        "data": get_holder_distribution(chain_id)
    })


@app.route("/api/chain/<chain_id>/news")
def chain_news(chain_id):
    """获取新闻与情绪"""
    if chain_id not in SUPPORTED_CHAINS:
        return jsonify({"status": "error", "message": f"不支持的项目: {chain_id}"}), 404

    return jsonify({
        "status": "ok",
        "data": get_news_for_chain(chain_id)
    })


@app.route("/api/chain/<chain_id>/full")
def chain_full(chain_id):
    """获取完整分析报告"""
    if chain_id not in SUPPORTED_CHAINS:
        return jsonify({"status": "error", "message": f"不支持的项目: {chain_id}"}), 404

    return jsonify({
        "status": "ok",
        "data": {
            "summary": get_onchain_summary(chain_id),
            "developer": get_developer_activity(chain_id),
            "holders": get_holder_distribution(chain_id),
            "news": get_news_for_chain(chain_id),
        }
    })


@app.route("/api/compare")
def compare_chains():
    """横向对比多个链"""
    chains_param = request.args.get("chains", "")
    chain_ids = [c.strip() for c in chains_param.split(",") if c.strip() in SUPPORTED_CHAINS]

    if not chain_ids:
        chain_ids = list(SUPPORTED_CHAINS.keys())

    result = {}
    for cid in chain_ids:
        result[cid] = {
            "summary": get_onchain_summary(cid),
            "developer": get_developer_activity(cid),
        }

    return jsonify({"status": "ok", "data": result})


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "project": PROJECT_NAME, "version": VERSION})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
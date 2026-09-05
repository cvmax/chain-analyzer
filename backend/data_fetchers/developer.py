"""
开发者活跃度数据采集 (GitHub API)
- 提交频率 / 开发者数量 / Star 趋势 / 代码活跃度
"""
import time
from datetime import datetime, timedelta
from config import API_CONFIG, SUPPORTED_CHAINS
from .http_utils import http_get as requests_get

CACHE = {}


def _cached(key, fetcher, ttl=600):
    now = time.time()
    if key in CACHE and CACHE[key][0] > now - ttl:
        return CACHE[key][1]
    data = fetcher()
    CACHE[key] = (now, data)
    return data


def _github_headers():
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = API_CONFIG["github"]["token"]
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_repo_stats(repo_full_name):
    """获取单个仓库的基本统计信息"""
    cfg = API_CONFIG["github"]
    try:
        r = requests_get(
            f"{cfg['base_url']}/repos/{repo_full_name}",
            headers=_github_headers(),
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            return {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "watchers": data.get("watchers_count", 0),
                "updated_at": data.get("updated_at", ""),
                "pushed_at": data.get("pushed_at", ""),
                "language": data.get("language", ""),
                "description": data.get("description", ""),
            }
        elif r.status_code == 403:
            return {"rate_limited": True}
    except Exception:
        pass
    return {}


def fetch_commit_activity(repo_full_name):
    """获取最近 12 周的提交活动"""
    cfg = API_CONFIG["github"]
    try:
        r = requests_get(
            f"{cfg['base_url']}/repos/{repo_full_name}/stats/commit_activity",
            headers=_github_headers(),
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                total_commits = sum(w.get("total", 0) for w in data[-12:])
                weekly_breakdown = [{"week": w.get("week", ""), "commits": w.get("total", 0)} for w in data[-12:]]
                return {
                    "total_commits_12w": total_commits,
                    "weekly_breakdown": weekly_breakdown,
                }
    except Exception:
        pass
    return {"total_commits_12w": 0, "weekly_breakdown": []}


def get_developer_activity(chain_id):
    """获取项目的开发者活跃度综合数据"""
    chain = SUPPORTED_CHAINS.get(chain_id)
    if not chain or not chain.get("github_repos"):
        return {"error": "无 GitHub 仓库数据"}

    def _fetch():
        repos = chain["github_repos"]
        repo_stats = []
        total_stars = 0
        total_forks = 0
        total_commits_12w = 0
        weekly_commits = {}
        rate_limited = False

        for repo in repos:
            stats = fetch_repo_stats(repo)
            if stats.get("rate_limited"):
                rate_limited = True
            stats["repo"] = repo
            repo_stats.append(stats)
            total_stars += stats.get("stars", 0)
            total_forks += stats.get("forks", 0)

            activity = fetch_commit_activity(repo)
            total_commits_12w += activity.get("total_commits_12w", 0)
            for w in activity.get("weekly_breakdown", []):
                week = w.get("week", "")
                if week:
                    weekly_commits[week] = weekly_commits.get(week, 0) + w.get("commits", 0)

        score = min(100, total_commits_12w * 2 + total_stars * 0.01 + total_forks * 0.02)
        score = round(score, 1)

        return {
            "repos": repo_stats,
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_commits_12w": total_commits_12w,
            "weekly_commits": weekly_commits,
            "activity_score": score,
            "activity_level": "高" if score > 60 else ("中" if score > 30 else "低"),
            "rate_limited": rate_limited,
            "note": "GitHub API 限流，配置 GITHUB_TOKEN 环境变量获取实时数据" if rate_limited else "",
        }

    return _cached(f"github_{chain_id}", _fetch)
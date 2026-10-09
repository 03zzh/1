"""
数字红包后端 · Vercel 版
=======================
适配 Vercel Serverless Functions：
- 入口文件必须是 api/app.py，对外暴露顶层变量 app
- Vercel 会自动提供 WSGI 运行环境，无需 gunicorn
- 全局变量（PACKETS / GRABBED）在同一实例内可共享，跨实例不共享
  → 个人娱乐完全够用；要生产可用请换成 Vercel KV / Upstash Redis
- 已开启 CORS，允许任何来源调用（页面用纯路径访问 API，无跨域问题）

部署：把整个项目 push 到 GitHub → Vercel 导入仓库 → 自动识别 Flask → 部署完成
"""

import time
import random
import string
from flask import Flask, request, jsonify

app = Flask(__name__)

# 内存存储（重启/跨实例会清空，娱乐用途足够）
PACKETS = {}
GRABBED = {}

NAME_POOL = ['阿强', '小美', '老王', 'Lucy', '大伟', '芳芳', 'Tony', '翠花',
             '建国', '思聪', '铁柱', '可儿', '阿杰', '梦琪', '子轩', '浩然',
             '宇航', '梓涵', '默默', '皮皮', '小胖', '阿珍', '大牛', '露露']
AVATAR = ['🐶', '🐱', '🦊', '🐼', '🦁', '🐸', '🐵', '🐧', '🦄', '🐷',
          '🐰', '🐨', '🐯', '🐹', '🐻', '🐔', '🦉', '🐺', '🐮', '🐙']


def gen_id(n=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


def split_red(total, n):
    """二倍均值法分配红包金额"""
    amounts, rest = [], round(total, 2)
    for i in range(n - 1):
        avg = rest / (n - i)
        maxv = round(avg * 2 - 0.01, 2)
        v = round(random.uniform(0.01, max(0.01, maxv)), 2)
        v = min(v, round(rest - (n - i - 1) * 0.01, 2))
        amounts.append(v)
        rest = round(rest - v, 2)
    amounts.append(round(rest, 2))
    random.shuffle(amounts)
    return amounts


def _cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp


@app.route('/api/create', methods=['POST'])
def create():
    data = request.get_json(silent=True) or {}
    total, count = float(data.get('total', 0)), int(data.get('count', 0))
    if total <= 0:
        return jsonify(ok=False, msg='总金额必须大于 0')
    if not (1 <= count <= 100):
        return jsonify(ok=False, msg='红包个数需在 1~100 之间')
    if total / count < 0.01:
        return jsonify(ok=False, msg='单个红包不能小于 0.01 元')
    amounts = split_red(total, count)
    pid = gen_id()
    PACKETS[pid] = {
        'id': pid, 'total': round(total, 2), 'count': count, 'amounts': amounts,
        'grabbed': [], 'best_idx': amounts.index(max(amounts)),
        'create_time': int(time.time()),
    }
    GRABBED[pid] = set()
    return jsonify(ok=True, packet_id=pid)


@app.route('/api/packet/<pid>')
def packet_info(pid):
    p = PACKETS.get(pid)
    if not p:
        return jsonify(ok=False, msg='红包不存在或已过期')
    remain = p['count'] - len(p['grabbed'])
    return jsonify(ok=True, total=p['total'], count=p['count'],
                   grabbed_count=len(p['grabbed']), remain=remain,
                   is_done=remain == 0, grabbed=p['grabbed'],
                   best_idx=p['best_idx'] if remain == 0 else -1)


@app.route('/api/grab/<pid>', methods=['POST'])
def grab(pid):
    p = PACKETS.get(pid)
    if not p:
        return jsonify(ok=False, msg='红包不存在或已过期')
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id') or request.headers.get('X-User-Id') or 'anonymous'
    nick = data.get('nick') or NAME_POOL[hash(user_id) % len(NAME_POOL)]
    ava = data.get('ava') or AVATAR[hash(user_id) % len(AVATAR)]

    if len(p['grabbed']) >= p['count']:
        return jsonify(ok=False, msg='红包已被抢光啦', is_done=True)
    if user_id in GRABBED[pid]:
        old = next((g for g in p['grabbed'] if g['user_id'] == user_id), None)
        return jsonify(ok=True, amount=old['amount'], already=True, **old)

    idx = len(p['grabbed'])
    amount = p['amounts'][idx]
    record = {'user_id': user_id, 'nick': nick, 'ava': ava,
              'amount': amount, 'idx': idx, 't': int(time.time())}
    p['grabbed'].append(record)
    GRABBED[pid].add(user_id)
    is_done = len(p['grabbed']) >= p['count']
    return jsonify(ok=True, amount=amount, already=False, is_done=is_done,
                   best_idx=p['best_idx'] if is_done else -1,
                   remain=p['count'] - len(p['grabbed']))


@app.route('/api/rank/<pid>')
def rank(pid):
    p = PACKETS.get(pid)
    if not p:
        return jsonify(ok=False, msg='红包不存在')
    grabbed = sorted(p['grabbed'], key=lambda g: -g['amount'])
    return jsonify(ok=True, total=p['total'], count=p['count'],
                   grabbed=grabbed, remain=p['count'] - len(p['grabbed']),
                   best_idx=p['best_idx'])


# Vercel 健康检查
@app.route('/api/health')
def health():
    return jsonify(ok=True, msg='红包服务正常运行 🧧')


# 让纯路径访问 /open/<pid> 也能返回前端页面（如果 Vercel 同时托管前端）
@app.route('/open/<pid>')
def open_page(pid):
    from flask import redirect
    return redirect('/#/open/' + pid)


# Vercel Python runtime 要求的入口变量
# Vercel 会自动加载 app.py 中的 app 实例
# handler 用于兼容 api/app.py 的直接调用场景
def handler(request):
    return app(request.environ, lambda *a, **k: None)


# 开发环境本地调试
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

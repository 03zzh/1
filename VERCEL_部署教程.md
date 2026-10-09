# 🧧 数字红包 · Vercel 部署教程

## 为什么用 Vercel
- **免费**，Hobby 额度对个人玩绰绰有余
- **自动识别 Flask**，零配置部署
- **自带 HTTPS**，微信里能正常打开（这是 GitHub Pages 给不了的）
- 和 GitHub 打通，**push 代码自动部署**，不用手动操作

---

## 第一步：准备 GitHub 仓库

1. 在 [github.com/new](https://github.com/new) 新建一个仓库（比如 `red-packet`）
2. 把下面这些文件 push 上去：

```
red-packet/
├── api/
│   └── app.py          ← 后端（Flask）
├── vercel.json         ← Vercel 路由配置
├── requirements.txt    ← 依赖：flask
└── red_packet.html     ← 前端页面（群友看到的）
```

**push 命令：**
```bash
cd /data/workspace
git init
git add .
git commit -m "数字红包上线 🧧"
git branch -M main
git remote add origin https://github.com/你的用户名/red-packet.git
git push -u origin main
```

---

## 第二步：Vercel 导入仓库

1. 打开 [vercel.com](https://vercel.com)，用 **GitHub 账号**登录（点 Continue with GitHub）
2. 第一次会让你授权，点 **Install**
3. 授权后在 Vercel 主页点 **Import Project** → 选你刚建的 `red-packet` 仓库
4. 点 **Deploy**

Vercel 会自动：
- 检测到 `api/app.py` 里的 Flask 应用
- 读 `requirements.txt` 装依赖
- 读 `vercel.json` 配置路由
- 部署完成后给你一个地址：`https://red-packet-xxx.vercel.app`

---

## 第三步：填 API 地址

1. 打开你的 Vercel 项目 → **Deployments** → 点最新那个 → 复制生产地址
2. 打开 `red_packet.html`，把第 166 行改成：
   ```javascript
   const API = 'https://red-packet-xxx.vercel.app';
   ```
3. commit & push，Vercel 会自动重新部署（约 30 秒）

---

## 第四步：验证

在浏览器打开 Vercel 地址，看到红包皮页面即成功。可以：
- 输入金额、个数 → 点「塞钱进红包」
- 复制生成的链接，用手机浏览器（或微信里）打开，应该能看到拆红包界面
- 多开几个窗口/手机，抢同一个红包，排行榜会实时更新

---

## 第五步：分享到群里

把 `red_packet.html` 部署到任意静态服务即可：

**方案 A：就用 Vercel（推荐，前后端一个平台）**
- Vercel 自动部署的地址本身就能访问到 `red_packet.html`…… ⚠️ 不对，Vercel 配置的是全量 rewrite 到 Flask，访问根路径会返回 JSON。

**正确做法：把 `red_packet.html` 放到 GitHub Pages**
1. 仓库 Settings → Pages → Source 选 `main` 分支 `/root`
2. 保存后等 1-2 分钟，访问 `https://你的用户名.github.io/red-packet/red_packet.html`
3. 这个地址就是你要发到群里的链接（前提是 html 里 API 已指向 Vercel）

或者更简单：**前端也一起丢到 Vercel**，把 `vercel.json` 的 rewrite 去掉、改用 public 目录托管静态文件——但这会覆盖后端，二选一。

**✅ 最省事的组合（推荐）：**
- 后端 API → Vercel（`api/app.py` + `vercel.json` + `requirements.txt`）
- 前端页面 → GitHub Pages（`red_packet.html`，API 填 Vercel 地址）

---

## 常见问题

| 问题 | 解决 |
|---|---|
| 页面能打开但抢红包报 CORS 错误 | 检查 `API` 常量是否填对，必须是 https 开头 |
| 微信里打不开 | Vercel 自带 HTTPS，如果用了自定义域名需配 SSL |
| 刷新后红包不见了 | 正常！当前用内存存储，重启/跨实例会清空，纯娱乐用途 |
| 想永久保存 | 把 PACKETS 换成 Vercel KV / Upstash Redis（需改几行代码） |
| 部署失败 | 看 Vercel 的 Deployments 页 → 点进去看构建日志 |

---

## 想永久保存红包数据？

当前红包数据存在内存里，重启就没了。要持久化只需：

1. Vercel 控制台 → Storage → Create → **Upstash Redis**（免费额度够用）
2. 装依赖：`pip install flask redis`
3. 把 `api/app.py` 里的 `PACKETS` / `GRABBED` 字典改成读 Redis
4. 重新部署

需要我帮你改成 Redis 版本的话，跟我说一声就行 🧧

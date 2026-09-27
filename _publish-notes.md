# GitHub 发布流程笔记（WorkBuddy 环境）

> 2026-09-27 记录。项目：数模指挥官开源发布。
> 说明：按用户要求不新建 skill，此为纯笔记。

## 核心突破：GitHub 连接器只读 → 用 Device Flow 拿 token

官方 GitHub 连接器（api.githubcopilot.com/mcp）可读不可写：建仓、推文件全部返回 `403 Resource not accessible by integration`。

**解法 = GitHub Device Flow 设备授权**（用户只需点一次，之后长期可用）：

```bash
# 1. 申请设备码（client_id 是 GitHub CLI 的公开 ID）
curl -s -X POST https://github.com/login/device/code \
  -H "Accept: application/json" \
  -d "client_id=178c6fc778ccc68e1d6a" -d "scope=repo workflow" --max-time 25
# → {"device_code":"...","user_code":"XXXX-XXXX","verification_uri":"https://github.com/login/device","expires_in":899}

# 2. 让用户打开 https://github.com/login/device 输入 user_code 并授权

# 3. 换 token
curl -s -X POST https://github.com/login/oauth/access_token \
  -H "Accept: application/json" \
  -d "client_id=178c6fc778ccc68e1d6a" -d "device_code=<device_code>" \
  -d "grant_type=urn:ietf:params:oauth:grant-type:device_code" --max-time 25
# → {"access_token":"gho_xxx"（40 字符）,"scope":"repo,workflow"}
```

## 用 token 做写操作

```bash
TOK=$(cat /tmp/gh_tok.txt)
# 推送（remote 带 token）
git remote set-url origin "https://<user>:${TOK}@github.com/<user>/<repo>.git"
# 大仓库必须后台推（5MB+ 会超 2 分钟前台超时）
(git push -u origin master:main --force > /tmp/push.log 2>&1; echo "EXIT=$?" >> /tmp/push.log) &
sleep 45; cat /tmp/push.log

# 改名 + 描述
curl -s -X PATCH "https://api.github.com/repos/<owner>/<repo>" \
  -H "Authorization: token $TOK" -H "Accept: application/vnd.github+json" \
  -d '{"name":"新名","description":"新描述"}'

# Topics（涨星核心）
curl -s -X PUT "https://api.github.com/repos/<owner>/<repo>/topics" \
  -H "Authorization: token $TOK" -H "Accept: application/vnd.github+json" \
  -d '{"names":["cumcm","math-modeling"]}'
```

## 凭据安全

```bash
git config --local credential.helper "store --file=.git/.git-credentials"
printf "https://<user>:%s@github.com\n" "$TOK" > .git/.git-credentials
git remote set-url origin "https://github.com/<user>/<repo>.git"  # 改回干净 URL
```

## 坑清单

| 现象 | 原因 | 解法 |
|---|---|---|
| 写操作 403 | 连接器只读 | 走 Device Flow |
| Topics 设置 422 | 含中文 | 必须纯英文小写 + 连字符 |
| push 卡住无输出 | 超时限制 | 后台执行 + sleep 轮询 |
| curl 连不上 | 自己覆盖了代理 | 环境已有 `http(s)_proxy=127.0.0.1:51088`，别动 |
| git bash 里 `python` 不对 | PATH 无 venv | 用绝对路径 `C:\Users\A\.workbuddy\binaries\python\envs\default\Scripts\python.exe` |
| 嵌套 `.git` 让 `git add` 静默无效 | 复制目录时带入 | 改名 `.git-repo-backup`；`.gitignore` 的 `**/.git/` 拦不住 |
| 提交过的错误内容要清除 | 留在历史里 | `git update-ref -d HEAD` 后重新 add+commit |

## 发布前检查清单

```bash
# 第三方内容归属（别靠风格猜，看 frontmatter）
#   agent_created: true = 自有；无此字段 = 市场下载（第三方）
#   目录名带 __skillhub = 市场来源
grep -rn "Users.A\|Users/A\|真实姓名\|学校名" --include="*.md" --include="*.py" .
git ls-files | grep -E "_meta.json|_deprecated|\.ttf|\.otf|B0[0-9][0-9]"
curl -s ".../git/trees/main?recursive=1" | python -c "..."   # 递归验证文件数
```

## 本次交付结果

- 仓库：https://github.com/weiwei4589/cumcm-commander（公开，42 文件，6 commit）
- Topics：cumcm, math-modeling, mathematical-modeling, ai-agents, agent-skills, claude-skills, typst, academic-integrity, prompt-engineering, competition, latex, paper-writing

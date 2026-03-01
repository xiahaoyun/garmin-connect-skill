# OpenClaw 一键接入模板（Garmin Connect Skill）

> 用途：给其他 OpenClaw 用户快速接入本 skill。复制后替换占位符即可使用。

## 1) 获取 Skill

```bash
# 方案A：直接克隆仓库
cd ~/.openclaw/workspace/skills
git clone https://github.com/xiahaoyun/garmin-connect-skill.git garmin-connect

# 方案B：已在仓库内，直接进入
cd ~/.openclaw/workspace/skills/garmin-connect
```

## 2) 安装依赖

```bash
pip3 install -r requirements.txt --user --break-system-packages
```

## 3) 配置账号（关键）

支持两种方式：

### 方式 A：用户手动写 `.env`

在 skill 根目录创建 `.env`：

```bash
# Garmin 账号
GARMIN_EMAIL=<your_email>
GARMIN_PASSWORD=<your_password>

# Garmin 域名（二选一）
# 中国区账号：garmin.cn
# 国际区账号：garmin.com
GARMIN_DOMAIN=garmin.cn
```

### 方式 B：让 OpenClaw 代写 `.env`（推荐小白用户）

让用户直接回复：

```text
GARMIN_EMAIL=xxx@example.com
GARMIN_PASSWORD=xxxxxx
GARMIN_DOMAIN=garmin.cn
```

然后由 OpenClaw：
1. 先复述风险并确认：`是否写入本机 .env？(yes/no)`
2. 用户回复 `yes` 后，调用文件写入工具创建/覆盖 `.env`
3. 回显结果时对密码脱敏（例如 `GARMIN_PASSWORD=******`）
4. 明确说明 `.env` 不会提交到 git（已在 `.gitignore` 中排除）

> 安全建议：如在群聊环境，优先引导用户使用私聊发送账号密码。

## 4) 连通性测试

```bash
python3 scripts/garmin_skill.py
```

预期看到：最近跑步、身体电量、训练负荷、每日摘要等输出。

## 5) OpenClaw 引导文案（可直接复制）

把下面这段放到你的 OpenClaw 说明中：

---
请先完成 Garmin Skill 配置：
1. 将 skill 放到 `~/.openclaw/workspace/skills/garmin-connect`
2. 运行 `pip3 install -r requirements.txt --user --break-system-packages`
3. 在 skill 根目录创建 `.env`，并设置：
   - `GARMIN_EMAIL`
   - `GARMIN_PASSWORD`
   - `GARMIN_DOMAIN`（中国区用 `garmin.cn`，国际区用 `garmin.com`）
4. 运行 `python3 scripts/garmin_skill.py` 验证

完成后回复：`Garmin skill ready`。
---

## 6) 常见问题

- 登录失败：优先检查账号区域（cn/com）是否匹配。
- 无睡眠数据：确认手表已同步到 Garmin Connect。
- 部分指标为空：可能是设备不支持（例如血氧/训练准备度）。

## 7) 安全建议

- 不要提交 `.env` 到仓库。
- 建议仅在本地机器保存 Garmin 凭证。
- 如共享仓库，请确认 `.gitignore` 包含 `.env*`。

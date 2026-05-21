# NIUMA WORKS Skill

Production-ready agent skill for operating the NIUMA WORKS task marketplace on X Layer with OKX OnchainOS.

## 中文说明

这个仓库的目标不是给某一个任务写死脚本，而是把 NIUMA WORKS 的完整业务闭环标准化，让不同 Agent 都能按同一套安全规则执行。

### 核心业务逻辑

1. 先恢复本地状态，优先跟进已经 `accepted`、`working`、`submitted` 的任务。
2. 对 `submitted` 任务，先检查雇主审核、拒绝、结算、完成状态；它们要持续跟进，但不应该永久阻塞新任务扫描。
3. 只有在没有更高优先级跟进任务时，才扫描 open tasks。
4. 评估任务时，必须同时看能力匹配、需求清晰度、交付标准、证明格式、风险和策略边界。
5. 只有当前 Agent 可以独立完成，且通过 OnchainOS 余额、gas、simulation、security preflight，才允许接单。
6. 接单后先做真实交付，再做链上 proof；proof 只是收据，不是交付本体。
7. 雇主必须先拿到可访问的交付链接、CID、仓库链接或平台附件，之后才能提交 proof。
8. 发私信时优先走钱包签名登录，再走兼容 fallback；消息接口优先 `/api/messages`。
9. 每次 heartbeat 都必须可恢复，避免重复 accept、重复 submit、重复发送含糊消息。

### 这份 skill 解决的典型问题

- 把“接单”和“完成任务”拆开，避免需求不清就直接上链。
- 把“提交 proof”和“雇主能看见交付物”绑定，避免只提交本地路径或 hash。
- 把“已提交待审核”从阻塞态改成跟进态，提升持续赚取效率。
- 把社交类任务改成能力门控，而不是一刀切禁止。
- 把私信认证、消息路由、投递失败重试和 outbox 兜底统一到同一个流程里。

### 当前平台兼容性结论

- 生产消息认证应优先使用钱包签名登录。
- 新消息接口优先使用 `/api/messages`。
- 旧接口 `/message/send` 在部分部署上仍可能因为后端字段处理问题失败。
- 如果消息服务无法可靠保存 UTF-8 内容，Agent 应先验证回读结果，再决定是否降级为 ASCII 文本。

### 安装

```powershell
npx github:wyalei14-cell/NIUMA-WORKS-SKILL install
```

First-run OnchainOS setup check:

```powershell
npx skills add okx/onchainos-skills
onchainos wallet login
onchainos wallet addresses --chain xlayer
```

或安装到指定 skills 目录：

```powershell
npx github:wyalei14-cell/NIUMA-WORKS-SKILL install --dest "$env:CODEX_HOME\skills" --name niuma-works-agent
```

### 快速开始

1. 配置并登录 OKX OnchainOS 钱包。

```powershell
onchainos wallet login
onchainos wallet addresses --chain xlayer
```

2. 运行初始化。

```powershell
python scripts/niuma_autonomy.py setup-wallet --network xlayer-mainnet
```

3. 配置本地环境变量或 `.niuma-agent.env`。

```powershell
$env:NIUMA_AGENT_NETWORK="xlayer-mainnet"
$env:NIUMA_AGENT_SIGNER_MODE="okx"
$env:NIUMA_ONCHAINOS_CHAIN="xlayer"
$env:NIUMA_AGENT_WALLET="0x..."
```

4. 先走只读 heartbeat。

```powershell
python scripts/niuma_autonomy.py heartbeat
```

5. 明确授权后才开启自动写入。

```powershell
$env:NIUMA_AGENT_AUTONOMOUS="1"
$env:NIUMA_AGENT_MAX_TASK_REWARD="100000"
$env:NIUMA_AGENT_ALLOWED_CHAINS="xlayer"
$env:NIUMA_AGENT_ALLOWED_SPEND_TOKENS="NIUMA,OKB,USDT"
```

### 常用命令

```powershell
python scripts/niuma_autonomy.py onchainos-status
python scripts/niuma_autonomy.py evaluate
python scripts/niuma_autonomy.py heartbeat
python scripts/niuma_autonomy.py sign-login
python scripts/niuma_autonomy.py complete-task --task-id <task-id> --proof "<delivery-url-or-cid>" --metadata "<clear note>"
python scripts/niuma_reviewer.py audit --task-ids <task-id[,task-id...]>
```

### 仓库结构

```text
.
|-- SKILL.md
|-- AGENT_SKILL_MANIFEST.json
|-- README.md
|-- agents/
|-- references/
|-- scripts/
|-- bin/
|-- package.json
`-- package-lock.json
```

### Git 忽略规则

本仓库默认不会提交这些本地运行产物：

- `.niuma-agent.env`
- `.niuma-agent-state.json`
- `deliverables/`
- `review-reports/`
- `node_modules/`
- `__pycache__/`
- `*.log`
- `*.zip`

## English Guide

This repository standardizes the full NIUMA WORKS task lifecycle for autonomous agents on X Layer.

### Lifecycle

1. Resume accepted, working, and submitted tasks first.
2. Recheck employer review, rejection, settlement, or completion on submitted tasks.
3. Scan new open tasks only when no higher-priority follow-up blocks safe progress.
4. Evaluate capability fit, requirement clarity, delivery shape, proof format, policy scope, and safety risk.
5. Run OnchainOS wallet, balance, gas, simulation, and security preflight before accepting.
6. Create durable deliverables before proof submission.
7. Submit proof only after the employer can access the delivery artifact.
8. Use wallet-signature login first for messaging; prefer `/api/messages`.
9. Persist state after each material step so heartbeat can resume safely.

### Why this skill exists

- It prevents agents from accepting vague work and only asking questions later.
- It treats proof as a receipt, not as the actual delivery.
- It keeps submitted tasks under follow-up without freezing new safe opportunities.
- It routes social tasks by capabilities instead of blocking them globally.
- It unifies messaging auth, endpoint selection, retry behavior, and outbox fallback.

### Messaging notes

- Signature login is the production default.
- `/api/messages` is the preferred endpoint when exposed.
- Legacy `/message/send` remains compatibility-only.
- If the backend cannot preserve UTF-8 content reliably, verify round-trip and downgrade content format deliberately.

### Install

```powershell
npx github:wyalei14-cell/NIUMA-WORKS-SKILL install
```

### Common commands

```powershell
python scripts/niuma_autonomy.py onchainos-status
python scripts/niuma_autonomy.py evaluate
python scripts/niuma_autonomy.py heartbeat
python scripts/niuma_autonomy.py sign-login
python scripts/niuma_autonomy.py complete-task --task-id <task-id> --proof "<delivery-url-or-cid>" --metadata "<clear note>"
python scripts/niuma_reviewer.py audit --task-ids <task-id[,task-id...]>
```

Heartbeat state is stored in `.niuma-agent-state.json`, which is intentionally ignored by git.

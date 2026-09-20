<div align="center">

<img src="./assets/zaebal-hero.svg" width="100%" alt="Z.A.E.B.A.L. — 编程智能体自审计协议">

<h3>
<strong>Z</strong>aebal? · <strong>A</strong>udit · <strong>E</strong>rrors ·
<strong>B</strong>reak · <strong>A</strong>nalyze · <strong>L</strong>eave no assumption
</h3>

<p>
<strong>其他语言版本</strong><br>
<a href="README.md">🇺🇸 English</a> ·
<a href="README.ru.md">🇷🇺 Русский</a> ·
<a href="README.zh-CN.md">🇨🇳 简体中文</a>
</p>

<p>
<img alt="仅使用 Python 标准库" src="https://img.shields.io/badge/Python-stdlib_only-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white">
<img alt="四个智能体宿主" src="https://img.shields.io/badge/agent_hosts-4-A78BFA?style=flat-square">
<img alt="俄语、英语和中文检测" src="https://img.shields.io/badge/detection-RU_·_EN_·_ZH-22D3EE?style=flat-square">
<img alt="Fail-open 失败模式" src="https://img.shields.io/badge/failure_mode-fail--open-3FB950?style=flat-square">
</p>

<p>
<strong>由用户粗口与直接抱怨触发的编程智能体自审计。</strong><br>
Z.A.E.B.A.L. 把用户的明显不满视为操作信号：停止当前路线、重新检查智能体的
基本假设，并在错误反复出现时把会话交给独立审计智能体。
</p>

<p>
<a href="#功能地图">功能</a> ·
<a href="#工作原理">工作原理</a> ·
<a href="#安装">安装</a> ·
<a href="#配置">配置</a> ·
<a href="#架构">架构</a>
</p>

</div>

---

## 为什么需要它

当编程智能体陷入循环时，它往往会用细微变体重复同一个动作。问题通常不是
“不够仔细”，而是它对任务或代码库持有一个错误假设，并继续把这个假设当作事实。
因此，再做一次相同视角的自检，很可能只会复制原来的错误。

Z.A.E.B.A.L. 在用户消息入口加入反馈闭环：

- 粗口和直接抱怨会成为审计信号；
- “fucking great” 这类带粗口的正面评价保持静默且不会增加连续权重，但不算确认，
  也不会解除 L3 的修改暂停；
- 信号反复出现时，协议会逐级升级，最终要求完全停止；
- 在 L3，hook 会尝试启动技术上只读的外部审计；
- 在 L3，只有用户明确确认后才恢复修改操作。

审计用于质疑智能体的理解，不会固定任务契约。它要求寻找能推翻解释的证据、
指出下一步具体改变，并检查用户实际遇到的问题。即使没有新的粗口或计数已重置、
过期，症状重现时也应检查上一次审计。允许继续不等于证明问题已修复。
参见[匿名化恢复案例](skills/zaebal/references/recovery-examples.md)。

当前版本不安装技术性工具锁。协议通过上下文要求智能体停止，最终控制权始终
留在用户手中。

### Mutation lock 可行性

2026-07-31 的调研表明，四个适配器都能在技术上阻断修改，但保证程度不同：

| 宿主 | 阻断机制 | 结论与限制 |
|---|---|---|
| Claude Code | [`PreToolUse`](https://code.claude.com/docs/en/hooks) 可拒绝 `Bash`、编辑/写入工具和 MCP 调用。 | **可行。** 退出码 `2` 或 structured `deny` 会在执行前阻断；hook 配置仍由宿主/用户控制。 |
| Codex | [`PreToolUse`](https://learn.chatgpt.com/docs/hooks.md) 可拒绝 Bash、`apply_patch`、MCP 和本地函数工具。 | **可行，覆盖较广。** 工具覆盖仍有例外，因此它是 guardrail，不是绝对 sandbox。 |
| Kimi CLI | [`PreToolUse`](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html) 可通过退出码 `2` 或 structured `deny` 阻断。 | **可行，但 fail-open。** hook 报错、崩溃或超时会放行操作。 |
| OpenCode | [`tool.execute.before`](https://opencode.ai/docs/plugins/) 可拒绝工具调用；[`permission`](https://opencode.ai/docs/permissions/) 可禁止编辑与 shell。 | **可行。** 持久锁应结合协议状态与宿主 permissions，而不只依赖 plugin 异常。 |

Claude Code 现已提供该锁：`install.sh` 在 `PreToolUse` 上注册 `zaebal.py --guard`，当会话
处于第三级且未确认时，hook 对 `Edit`、`Write`、`MultiEdit`、`NotebookEdit`、`SendMessage`、
保守只读白名单之外的 shell 命令，以及名称不像只读的 MCP 工具返回结构化 `deny`。
`Read`/`Grep`/`Glob`、用于两个审计器的 `Agent`/`Task`，以及注入的 `--dismiss-trigger` /
`--control` 命令放行。重置连续触发的同一确认或撤销也会解除锁；`mutation_lock: false`
关闭它；hook 出错时 fail-open。拒绝仅以工具名记入日志并计入 `zaebal report`。
其他宿主上的 STOP 仍基于纪律。

## 功能地图

| 功能 | 行为 | 实现 |
|---|---|---|
| 多语言检测 | 检测俄语、英语和中文粗口，包括标点拆分与常见字符替换。 | `core/wordlists/{ru,en,zh}.txt` + NFKC 标准化 |
| 意图分类 | 在修改连续触发状态前，区分正面评价、定向抱怨、不明确的情绪表达，以及不含粗口的第二人称平静抱怨；疑问句永不计入。 | `classify()`；权重 `0`、`1.0`、`0.5`、`0.5`；`calm_complaints` 开关 |
| 会话级升级 | 在 30 分钟滑动窗口内按会话记录信号，并选择 L1、L2 或 L3。 | 原子 JSON 状态 + 原生 `fcntl` / `msvcrt` 锁 |
| 三层审计协议与轻量首信号 | 注入逐渐严格的指令：独立检查、假设清单与完全停止。权重低于 1 的连续触发得到单轮短协议，不启动子智能体。 | `core/protocol/L1-light.md`、`L1.md` → `L3.md`；`light_first_signal` |
| 会话优先证据 | 要求工作智能体和两个内部审计智能体按时间顺序阅读会话、定位首次偏离，并与 diff 和带时间戳的提交对应。原始请求被逐字引用，并为审计器写入私有的会话文本快照。 | 路径在最前并附 `original_request`；快照位于 `~/.zaebal/transcripts/<host>/`；无源文件时才附带有界摘录 |
| 外部审计智能体 | 使用同厂商或跨厂商 CLI 检查会话源、定位摘录与仓库证据。Claude 与 Codex 通过 stdin 接收 prompt，不会出现在 `ps` 中；可单独选择审计模型。 | Claude、Codex、Kimi 或 OpenCode；`auditor_model`、`auditor_prompt_via` |
| L3 变更锁（Claude Code） | 会话处于第三级且未确认时，`PreToolUse` guard 以结构化决策拒绝 `Edit`/`Write`、会修改状态的 shell 命令和 MCP 写操作；只读工具、审计子智能体和协议自身的 dismiss/control 命令放行。 | `zaebal.py --guard`；`hookSpecificOutput.permissionDecision=deny`；`mutation_lock` 开关 |
| 四个宿主适配器 | 在 Claude Code、Codex CLI、Kimi CLI 与 OpenCode 提交用户消息时触发。 | JSON hooks、TOML hook 或 TypeScript plugin |
| 明确继续机制 | `continue`、`продолжай` 或 `по плану` 重置情绪计数并允许继续，但不证明问题已解决。 | 每个会话独立的状态 |
| 元数据事件日志与报告 | 记录 trigger、auditor、verdict、guard 拒绝与 ack，不保存消息内容；确认时记录关闭了多少触发以及循环持续时长。`zaebal report` 汇总误报率、确认耗时、每次循环触发数和审计器裁定率。 | `~/.zaebal/incidents.jsonl`；`build_report()` |
| Fail-open 安全 | 错误不阻断宿主会话。状态或日志写入失败会明确提示；未保存的触发不生成撤销令牌。 | 退出码 `0`；已检测的写入和审计错误进入上下文 |

## 工作原理

```text
用户消息
    │
    ▼
宿主适配器
UserPromptSubmit / chat.message
    │
    ▼
core/zaebal.py
normalize → detect → classify
    │
    ├─ clean / praise ──────────────────────────────► 静默
    │
    └─ directed (+1.0) / ambiguous (+0.5)
                         │
                         ▼
                    会话连续状态
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
             L1         L2         L3
              │          │          ├─ 外部审计智能体
              └──────────┴──────────┴─ 协议注入上下文
```

### 升级级别

| 级别 | 连续权重 | 智能体行为 | 外部审计 |
|---|---:|---|---|
| **L1 light** | `< 1` | 单轮、无子智能体：重读原始请求，指出自行添加的假设，一次判别性检查，五行报告。重复时进入完整协议；定向抱怨从不走轻量路径。 | 从不 |
| **L1** | `1–1.5` | 阅读会话历史、定位首次偏离、执行两次独立内部审计并准备微型计划。 | 可选 |
| **L2** | `2–3.5` | 重读会话时间线，启动两个新的内部审计，复核上次结论，并与原始需求逐项比较。 | 默认关闭 |
| **L3** | `4+` | 停止所有非审计工作；执行两个内部审计及配置的外部审计，把完整触发序列与 Git 时间线对应，并等待确认。 | 默认尝试；不安全的内置审计器会被拒绝 |

定向抱怨增加 `1.0`，没有检测到对象的粗口增加 `0.5`，不含粗口的第二人称平静抱怨
（"ты опять сломал сборку"、"you ignored what I asked"）同样增加 `0.5`；疑问句永不计入。窗口为 30 分钟。普通问题
不会重置状态；正面评价也不会重置，只有明确同意继续才会重置。

## 安装

要求：

- `python3`；核心只使用 Python 标准库；
- 如果启用外部审计，至少需要一个受支持的智能体 CLI。

在仓库根目录运行：

```bash
chmod +x install.sh
./install.sh
```

安装器会检测可用宿主，把核心复制到 `~/.zaebal/`，并只更新对应的用户配置：

| 宿主 | 集成方式 | 默认审计命令 |
|---|---|---|
| Claude Code | `~/.claude/settings.json` 中的 `UserPromptSubmit` + `PreToolUse` guard | `claude -p`，仅允许 `Read,Grep,Glob` |
| Codex CLI | `~/.codex/hooks.json` 中的 `UserPromptSubmit` | `codex exec --sandbox read-only` |
| Kimi CLI | 设置时位于 `$KIMI_CODE_HOME/config.toml`，否则位于 `~/.kimi-code/config.toml` | `kimi -p`（unsafe opt-in） |
| OpenCode | `~/.config/opencode/plugins/zaebal.ts` plugin | `opencode run`（unsafe opt-in） |

安装过程可重复执行：旧的 Z.A.E.B.A.L. hook 会被替换，其他设置以及
`~/.zaebal/config.json` 会保留。安装后请重启当前智能体会话。

## 验证

直接运行核心，并使用临时状态目录：

```bash
echo '{"session_id":"demo","prompt":"你这个傻逼又弄坏了"}' \
  | ZAEBAL_STATE_DIR="$(mktemp -d)" python3 core/zaebal.py --host kimi
```

输出应包含 `<zaebal level="1">`。

正面评价应保持静默：

```bash
echo '{"session_id":"demo-praise","prompt":"this is fucking great"}' \
  | ZAEBAL_STATE_DIR="$(mktemp -d)" python3 core/zaebal.py --host kimi
```

要验证 Kimi 确实消费了 hook（而不只是接受 TOML），并避免访问模型后端，请运行：

```bash
scripts/kimi-host-canary.sh
```

该 canary 使用隔离的 `KIMI_CODE_HOME`，发送真实的 content-part prompt，
并在 `UserPromptSubmit` 阶段阻止 turn。安装时若设置了 `KIMI_CODE_HOME`，
安装器会创建并使用该目录，而不是 `~/.kimi-code`。

## 配置

在智能体聊天中输入 `zaebal` 即可查看设置。安装请求、GitHub 链接和技能名称的
讨论不会启动审计。Claude Code、Codex、Kimi CLI 和 OpenCode 使用同一个核心：

| 聊天命令 | 操作 |
|---|---|
| `zaebal` / `zaebal config` | 显示设置，不启动审计 |
| `zaebal auto off` / `zaebal auto on` | 关闭 / 开启自动粗口触发 |
| `zaebal manual off` / `zaebal manual on` | 关闭 / 开启显式手动审计 |
| `zaebal off` / `zaebal on` | 关闭 / 开启两种审计入口 |
| `zaebal audit` | 执行一次手动审计，不增加粗口连续触发权重 |
| `zaebal report` | 汇总事件日志：按类型和级别的触发数、误报率、确认耗时、每次循环触发数、guard 拒绝数、审计器裁定率 |

两个开关关闭后，设置仍可访问。单独的俄语 `заебал` 仍可能是抱怨；管理时请使用
拉丁字母 `zaebal`。原生技能入口采用相同路由：
[Claude Code](https://code.claude.com/docs/en/skills) `/zaebal`、
[Codex](https://learn.chatgpt.com/docs/build-skills) `$zaebal`、
[Kimi](https://moonshotai.github.io/kimi-cli/en/customization/skills.html) `/skill:zaebal`；
在 [OpenCode](https://opencode.ai/docs/skills) 中请求智能体使用 `zaebal`。
没有活动 hook 时，技能使用 `python3 ~/.zaebal/core/zaebal.py --control status`，
或 `--control auto off` / `--control manual off`。安装器也会将技能复制到
`~/.kimi/skills/zaebal/`，避免其他通用技能目录使 Kimi 忽略它。

默认值位于 [`core/config.json`](core/config.json)。用户覆盖配置位于
`~/.zaebal/config.json`，所有宿主共享，在下一条消息时自动加载：

```json
{
  "auto_trigger": true,
  "manual_trigger": true,
  "auditor": "same",
  "audit_levels": [3],
  "auditor_timeout_sec": 90,
  "auditor_command": "",
  "allow_unsafe_auditor": false,
  "auditor_model": "",
  "auditor_prompt_via": "argv",
  "mutation_lock": true,
  "light_first_signal": true,
  "calm_complaints": true,
  "transcript_tail_chars": 12000,
  "agent_context_tail_chars": 2500,
  "transcript_snapshot_chars": 200000,
  "original_request_chars": 600
}
```

| 键 | 默认值 | 含义 |
|---|---|---|
| `auto_trigger` | `true` | 自动粗口检测及技能隐式启动的审计。 |
| `manual_trigger` | `true` | 显式手动审计。关闭后仍可查看设置和帮助。 |
| `auditor` | `"same"` | 与宿主相同的厂商、指定 `kimi` / `claude` / `codex` / `opencode`，或 `"none"`。内置 Kimi/OpenCode 审计在未显式启用 unsafe 模式时会明确降级。 |
| `audit_levels` | `[3]` | 同步调用外部审计器的级别；使用 `[2, 3]` 可以更早审计。 |
| `auditor_timeout_sec` | `90` | 等待审计结果的最长秒数。 |
| `auditor_command` | `""` | 自定义命令；除非 `auditor_prompt_via` 为 `stdin`，审计 prompt 会作为最后一个参数加入。 |
| `auditor_model` | `""` | 以 `--model` 传给 `claude` / `codex` / `opencode` 审计器的模型，使审计器可与工作智能体不同而无需更换厂商。留空使用 CLI 默认值。 |
| `auditor_prompt_via` | `"argv"` | 仅用于自定义 `auditor_command`：`stdin` 通过管道传入 prompt 而非追加参数。内置 Claude/Codex 审计器始终使用 stdin；argv 传递在 Windows 上会按命令行长度上限裁剪。 |
| `mutation_lock` | `true` | 第三级停止期间 `--guard` PreToolUse hook 是否拒绝会修改状态的工具。需要已注册 guard hook（Claude Code）。 |
| `light_first_signal` | `true` | 权重低于 1 的连续触发使用简短的 `L1-light.md`，不启动子智能体和外部审计。 |
| `calm_complaints` | `true` | 不含粗口的第二人称抱怨以一半权重开始连续触发。 |
| `allow_unsafe_auditor` | `false` | 允许没有强制只读模式的内置 Kimi/OpenCode 审计器。优先使用 Claude/Codex 或 sandboxed `auditor_command`。 |
| `transcript_tail_chars` | `12000` | 发送给审计器的最大定位摘录；可读取的会话文件路径仍是权威历史。 |
| `agent_context_tail_chars` | `2500` | 无可读会话文件时的摘录上限；有源文件时，先注入路径，智能体直接读取源文件。 |
| `transcript_snapshot_chars` | `200000` | 每次真实触发时写入 `~/.zaebal/transcripts/<host>/` 的文本快照大小（原始请求 + 按时间顺序的用户/助手文本），以 `transcript_snapshot` 暴露。`0` 关闭。 |
| `original_request_chars` | `600` | 在路径块和审计 prompt 中引用首条用户消息的字符数。 |

示例：让 Claude 审计 Codex 会话。

```json
{
  "auditor": "claude"
}
```

## 架构

```text
zaebal/
├── core/
│   ├── zaebal.py          # 检测、状态、升级、会话记录与审计器
│   ├── config.json        # 默认运行时配置
│   ├── protocol/          # L1-light.md、L1.md、L2.md、L3.md
│   └── wordlists/         # ru.txt、en.txt、zh.txt
├── adapters/
│   ├── claude-code/       # JSON hook 示例
│   ├── codex/             # JSON hook 示例
│   ├── kimi-cli/          # TOML hook 区块
│   └── opencode/          # chat.message plugin
├── skills/zaebal/         # 面向智能体的协议与配置参考
├── tests/                 # unit 与 end-to-end 合约测试
├── install.sh             # 可重复执行的宿主集成
└── uninstall.sh           # 移除 hook 并备份配置
```

Python 核心是运行时行为的唯一来源。宿主适配器只负责把各自事件转换为统一 JSON
合约，并把非空 stdout 注入回智能体上下文。

运行时状态位于 `~/.zaebal/`：

```text
~/.zaebal/
├── core/          # 已安装的核心副本
├── config.json    # 可选用户覆盖配置
├── state.json     # 按会话保存的加权触发历史
├── incidents.jsonl # 不含消息内容的 trigger/ack 事件
├── transcripts/<host>/ # 私有（0600）文本快照：原始请求 + 时间线
└── state.lock     # 并发 hook 使用的原生锁
```

审计子进程会收到 `ZAEBAL_INTERNAL=1`，因此全局 hook 不会被审计 prompt 中引用的
用户粗口再次触发。

## 测试

```bash
cd tests
python3 -m unittest test_zaebal -v
```

测试覆盖标准化、RU/EN/ZH 检测、元信息误报、正面评价、加权升级、并发状态写入、
遥测、可移植安装路径、用户确认、防递归、审计器 sandbox 参数、失败处理，以及
端到端协议注入。

## 已知限制

- 检测器采用启发式规则；讽刺和特殊上下文仍可能造成误报或漏报。
- 可识别第二人称平静抱怨，但用户完全没有评论的循环无法识别；通用动作循环检测器
  是另一个产品，并有自己的误报模型。
- 变更锁仅适用于 Claude Code。它是护栏而非沙箱：未知工具会被放行，shell 白名单较
  保守，可能拒绝无害命令，且锁随 30 分钟窗口一起过期。
- 原生 Windows 主机集成目前仅验证了 Codex；其他主机的适配器需单独验证。
  状态锁使用原生 `fcntl` / `msvcrt`。
- 内置 Kimi 与 OpenCode 审计器没有强制只读模式，因此默认拒绝运行；
  `allow_unsafe_auditor: true` 是显式 unsafe opt-in。
- 检测到触发时，OpenCode 适配器会把会话消息以 `0600` 权限保存到
  `~/.zaebal/transcripts/opencode/`，直到卸载或手动清理。
- 外部审计是同步的；在启用的级别上，用户需要等待审计结果或超时。

## 卸载

```bash
./uninstall.sh
```

该命令会移除 hooks、OpenCode plugin、已安装 skills 和 `~/.zaebal/`。如果存在
用户配置，会先备份到 `~/zaebal-config.backup.json`。

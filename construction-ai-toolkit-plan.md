# Construction AI Toolkit — 项目企划

> 面向 PulseBuild（澳洲建筑科技公司）AI 应用工程师 / Agent 方向岗位的作品集项目
>
> 包含两个紧密协同的子项目：
> - **项目 A**：Proactive Construction Delay Detection Agent（主动型延误预警 Agent）
> - **项目 B**：Construction Domain MCP Server（建筑领域 MCP 服务器）

---

## 目录

- [整体策略](#整体策略)
- [Monorepo 架构](#monorepo-架构)
- [项目 A：延误预警 Agent](#项目-a延误预警-agent)
- [项目 B：MCP Server](#项目-bmcp-server)
- [两个项目的协同](#两个项目的协同)
- [时间预算](#时间预算)
- [CV 最终写法](#cv-最终写法)

---

## 整体策略

### 为什么做这两个项目

| 项目 | 证明的能力 | 对应 PulseBuild 业务 |
|------|----------|------------------|
| 项目 A | Proactive Agent 模式、Tool Use、Eval、可观测性 | 他们网站的 "AI Alerts" 模块 |
| 项目 B | 协议层抽象、生态思维、新技术追踪 | 他们未来必然要做的"工具暴露给 AI"层 |

### 核心策略

**业务逻辑写一次，两处消费**：项目 A 的工具 = 项目 B 的工具，通过共享 `core-tools` 包实现，节省 30% 工作量，同时在面试时能讲"我做了分层架构"。

---

## Monorepo 架构

```
construction-ai-toolkit/
├── README.md                         # 总体介绍 + 两个子项目的 demo 视频
├── pyproject.toml                    # workspace 配置
├── .env.example
│
├── packages/
│   ├── core-tools/                   # 共享业务逻辑层
│   │   ├── pyproject.toml
│   │   └── src/core_tools/
│   │       ├── schedule.py           # 进度数据相关
│   │       ├── weather.py            # 天气影响
│   │       ├── history.py            # 历史延误模式
│   │       ├── compliance.py         # 合规检查
│   │       ├── defects.py            # 缺陷查询
│   │       └── data_layer.py         # 统一数据访问
│   │
│   ├── delay-agent/                  # 项目 A
│   │   ├── pyproject.toml
│   │   └── src/delay_agent/
│   │       ├── agent.py              # Agent 主循环
│   │       ├── prompts.py            # System prompt
│   │       ├── notifier.py           # Slack 推送
│   │       ├── scheduler.py          # APScheduler 定时任务
│   │       └── config.py
│   │
│   └── mcp-server/                   # 项目 B
│       ├── pyproject.toml
│       └── src/construction_mcp/
│           ├── server.py             # MCP Server 入口
│           ├── tools.py              # 5 个工具的 MCP 包装
│           ├── resources.py          # 3 个 resource handlers
│           └── prompts.py            # 2 个 prompt templates
│
├── data/                             # 共享 mock 数据
│   ├── projects.csv
│   ├── tasks.csv
│   ├── defects.csv
│   ├── compliance.csv
│   └── historical_delays.csv
│
├── evals/                            # 项目 A 的评估
│   ├── test_cases.json               # 20 个测试场景
│   └── run_eval.py
│
├── examples/                         # 项目 B 的使用示例
│   ├── claude_desktop_config.json
│   ├── usage_with_claude.md
│   ├── usage_with_cursor.md
│   └── usage_with_python.py
│
└── tests/
    ├── test_core_tools.py
    ├── test_agent.py
    └── test_mcp_server.py
```

---

## 项目 A：延误预警 Agent

### 业务场景

**痛点**：建筑项目经理每天要看 Gantt 图、工时表、材料消耗，人眼根本看不出哪里要出问题。等延误真的发生了再补救，已经晚了。

**解决方案**：每天定时跑的 Agent，自动分析项目数据，主动发现风险，用人话写出预警推送到 Slack。

**关键词**：**Proactive Agent（主动型）** — 不是用户问才答，而是定时跑、有事报警。这是 Agent 工程师面试里的高阶模式。

### 架构设计

```
┌──────────────────────────────────────────────────────────────┐
│  定时调度器 (APScheduler)  每天早上 7:00 触发                  │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│              延误预警 Agent (Claude + Tool Loop)              │
│                                                              │
│   ┌────────────────────────────────────────────────────┐    │
│   │  Reasoning Loop (最多 10 轮)                        │    │
│   │                                                    │    │
│   │  1. 拉取今日项目数据                                 │    │
│   │  2. 对比计划 vs 实际                                 │    │
│   │  3. 识别异常 → 调用工具深挖                          │    │
│   │  4. 综合判断风险等级                                 │    │
│   │  5. 生成自然语言预警                                 │    │
│   └────────────────────────────────────────────────────┘    │
└────────┬──────────────┬──────────────┬──────────────┬───────┘
         ↓              ↓              ↓              ↓
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ get_     │  │ analyze_ │  │ check_   │  │ get_     │
   │ schedule │  │ progress │  │ weather  │  │ history  │
   │ _data    │  │ _gap     │  │ _impact  │  │ _delays  │
   └──────────┘  └──────────┘  └──────────┘  └──────────┘
                                                  ↓
                                       ┌─────────────────┐
                                       │  Slack Webhook  │
                                       │  发送预警        │
                                       └─────────────────┘
```

### 五个 Tool 的设计

| 工具名 | 输入 | 输出 | 实现 |
|--------|------|------|------|
| `get_schedule_data(project_id)` | 项目 ID | 计划进度 vs 实际进度 DataFrame | Pandas 读 CSV |
| `analyze_progress_gap(task_id)` | 任务 ID | 偏差天数、偏差百分比、影响的下游任务 | 简单统计 |
| `check_weather_impact(date_range, location)` | 日期范围 + 地点 | 未来 7 天降雨/极端天气预报 | OpenWeather API |
| `get_history_delays(task_type)` | 任务类型 | 该类型任务历史平均延误 | 查 mock 数据库 |
| `send_slack_alert(message, severity)` | 预警内容 + 等级 | 发送状态 | Slack Incoming Webhook |

> **为什么是 5 个工具而不是 1 个**
>
> 面试官会专门问这个。正确答案是——单一职责原则 + 让 Agent 自己决定调用顺序。如果你写一个 `do_everything()` 工具，那就不是 Agent 了，是脚本。Agent 的价值在于它自己 reasoning 出"现在要先查天气还是先查历史"。

### 核心代码骨架

#### `agent.py`

```python
import anthropic
from core_tools import schedule, weather, history
from delay_agent import notifier
from delay_agent.prompts import SYSTEM_PROMPT

client = anthropic.Anthropic()

# 工具定义
TOOLS = [
    {
        "name": "get_schedule_data",
        "description": "Get planned vs actual progress for a construction project",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"}
            },
            "required": ["project_id"]
        }
    },
    # ... 其他 4 个工具
]

# 工具执行映射
TOOL_HANDLERS = {
    "get_schedule_data": schedule.get_schedule_data,
    "analyze_progress_gap": schedule.analyze_progress_gap,
    "check_weather_impact": weather.check_weather_impact,
    "get_history_delays": history.get_history_delays,
    "send_slack_alert": notifier.send_slack_alert,
}

def run_delay_agent(project_id: str, max_iterations: int = 10):
    """主 Agent 循环"""
    messages = [{
        "role": "user",
        "content": f"分析项目 {project_id} 的进度风险，如有重大延误风险，发送 Slack 预警。"
    }]

    for iteration in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # 终止条件：Claude 不再调用工具
        if response.stop_reason == "end_turn":
            return response.content[-1].text

        # 处理工具调用
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    try:
                        result = TOOL_HANDLERS[block.name](**block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })
                    except Exception as e:
                        # 关键：错误处理，面试必问
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })

            messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(f"Agent exceeded {max_iterations} iterations")
```

#### `prompts.py`

```python
SYSTEM_PROMPT = """You are a construction project risk analyst AI agent.
Your job is to proactively detect schedule risks before they cause delays.

WORKFLOW:
1. First, call get_schedule_data to understand current progress
2. For any task with >10% gap, call analyze_progress_gap for details
3. If the project location is outdoor-heavy, check weather impact
4. Compare findings against historical delays for similar task types
5. Synthesize findings into a risk assessment with:
   - Severity: LOW / MEDIUM / HIGH / CRITICAL
   - Root cause analysis
   - Recommended actions
6. If severity >= MEDIUM, call send_slack_alert

PRINCIPLES:
- Be specific: cite exact numbers, dates, task names
- Be actionable: every alert must have a "what to do next"
- Don't cry wolf: only escalate when data supports it
- If data is missing or tools fail, report that honestly rather than guessing
"""
```

### Mock 数据生成

最简单的办法：让 Claude 帮你生成。

```python
# scripts/generate_mock_data.py
prompt = """生成 10 个澳洲建筑项目的 mock 数据，CSV 格式，包含：
project_id, task_name, planned_start, planned_end, actual_start,
actual_progress_pct, location, task_type
其中 30% 的任务有不同程度的延误，要真实可信。
位置覆盖 Sydney、Melbourne、Brisbane、Perth。"""
```

跑一次，存成 CSV，永久能用。

### Eval 设计（面试加分项）

写 20 个测试场景：
- 10 个**应该报警**的（明显延误、天气影响、历史模式匹配）
- 10 个**不应该报警**的（小波动、已经在 buffer 内）

用 **LLM-as-judge** 评估：

```python
def llm_judge(agent_output, expected_severity):
    """让另一个 Claude 实例判断 agent 的输出是否合理"""
    judge_prompt = f"""
    Agent 的预警输出: {agent_output}
    预期严重等级: {expected_severity}

    评估这个预警是否：
    1. 严重等级判断正确 (1/0)
    2. 引用了具体数据 (1/0)
    3. 给出了可执行的建议 (1/0)

    返回 JSON: {{"correctness": 0-1, "specificity": 0-1, "actionability": 0-1}}
    """
    # 调用 Claude，解析 JSON
```

跑完得到 metrics 写在 README 上：**Correctness 87%, Specificity 92%, Actionability 78%**。

### 亮点功能 Checklist

- [ ] **Token cost tracking**：每次跑记录 token 消耗，README 写"平均每次预警成本 $0.03"
- [ ] **Prompt caching**：System prompt 用 Anthropic caching，省 ~85% token
- [ ] **观测性**：用 Langfuse 或自己写日志，记录每次 agent 的 reasoning trace
- [ ] **配置驱动**：阈值、调度时间从 YAML 读，不写死
- [ ] **Docker 部署**：能跑在云上，不只是本地脚本
- [ ] **错误处理**：所有工具调用都有 try/except，is_error 标记返回给 Agent

### CV 写法（项目 A 单独）

> **Proactive Construction Delay Detection Agent** | Python, Claude API, LangSmith
>
> - Built a scheduled autonomous agent that analyzes project schedule data daily, orchestrating 5 custom tools (schedule analysis, weather forecasting, historical pattern matching, Slack notification) through Claude's tool-use API with a max-iteration safeguard and structured error handling.
> - Designed 20-case eval suite using LLM-as-judge methodology, achieving 87% correctness on severity classification and 92% specificity on data citation.
> - Reduced average detection cost to $0.03 per project via Anthropic prompt caching, cutting token usage by ~85% on repeated system context.
> - GitHub: [link with demo gif of Slack alert]

### 面试可能被问什么

| 问题 | 你要准备的答案 |
|------|------------|
| 你这个 Agent 怎么处理工具调用失败？ | try/except 包住、is_error 标记、Agent 自己 reason 要不要重试或换路径 |
| 怎么避免 Agent 进入死循环？ | max_iterations 上限、循环检测（同一工具同参数连续调用 N 次就 break）|
| Token 成本怎么控制？ | Prompt caching、模型分级（简单工具用 Haiku，复杂判断用 Sonnet）、压缩 tool result |
| 怎么评估 Agent 的效果？ | Eval set + LLM-as-judge，关注 correctness/specificity/actionability 三维度 |
| 为什么不用 LangChain？ | 直接用 Anthropic SDK 更可控、更轻、调试更直接，LangChain 抽象层在 production 反而是负担 |

---

## 项目 B：MCP Server

### 业务场景

**痛点**：项目 A 的工具，只有那个特定的 Python agent 能用。如果建筑项目经理在 Claude Desktop 里聊天，能不能也用上这些工具？

**解决方案**：把工具包装成 **MCP Server**，任何 MCP 客户端（Claude Desktop, Cursor, Claude Code）都能即插即用。

**关键词**：**生态思维** + **协议层抽象**。这是高级 Agent 工程师才有的思考方式。

### 架构设计

```
                 ┌──────────────────────┐
                 │  Claude Desktop      │
                 └──────────┬───────────┘
                            │ MCP Protocol (stdio / SSE)
                            ↓
   ┌────────────────────────────────────────────────────┐
   │      Construction MCP Server                        │
   │                                                    │
   │   Resources:        Tools:           Prompts:       │
   │   - project://      - find_defect    - daily_       │
   │     {id}              s_by_type        report_      │
   │   - schedule://     - check_           template     │
   │     {project_id}      compliance     - risk_        │
   │   - compliance://   - lookup_          assessment   │
   │     {project_id}      regulation       _template    │
   │                     - get_schedule                  │
   │                       _data                         │
   │                     - analyze_                      │
   │                       progress_gap                  │
   └────────────────────────────────────────────────────┘
                            ↓
                  ┌─────────────────────┐
                  │  core-tools 包       │
                  │  (复用项目 A 的工具)  │
                  └─────────────────────┘
```

### MCP 三大原语（要全都用上）

很多人做 MCP Server 只用了 Tools，但 MCP 其实有**三种原语**，CV 上把三个都用上才显示真懂。

#### 1. Tools（工具）— 让 LLM 干活
LLM 决定调用，会改变状态或获取数据。例：`create_defect_ticket()`

#### 2. Resources（资源）— 让 LLM 读数据
**用户**或客户端决定加载，类似"@文件"引用。例：`project://PRJ-001` 让 Claude 把项目 1 的完整信息当上下文读进去。

#### 3. Prompts（提示模板）— 给用户的快捷指令
用户在 Claude Desktop 里能像选菜单一样选模板。例：选"生成今日工地日报"，自动填入相关参数。

> **面试加分点**：很多 candidate 只知道 Tools，你说自己三个都实现了，立刻拉开差距。

### 核心代码

#### `server.py`

```python
from mcp.server.fastmcp import FastMCP
from construction_mcp import tools, resources, prompts

mcp = FastMCP("construction-tools")

# ============ TOOLS ============
@mcp.tool()
def find_defects_by_type(project_id: str, defect_type: str) -> list[dict]:
    """Find all defects of a specific type in a project.

    Args:
        project_id: The project identifier (e.g., 'PRJ-001')
        defect_type: Type of defect ('structural', 'electrical', 'plumbing', 'finish')

    Returns:
        List of defect records with severity and status
    """
    return tools.find_defects_by_type(project_id, defect_type)

@mcp.tool()
def check_compliance(project_id: str) -> dict:
    """Check compliance status for an Australian construction project against NCC standards."""
    return tools.check_compliance(project_id)

@mcp.tool()
def lookup_regulation(keyword: str) -> list[dict]:
    """Look up Australian National Construction Code (NCC) regulations by keyword."""
    return tools.lookup_regulation(keyword)

@mcp.tool()
def get_schedule_data(project_id: str) -> dict:
    """Get planned vs actual schedule for a project."""
    return tools.get_schedule_data(project_id)

@mcp.tool()
def analyze_progress_gap(task_id: str) -> dict:
    """Analyze deviation between planned and actual progress for a task."""
    return tools.analyze_progress_gap(task_id)


# ============ RESOURCES ============
@mcp.resource("project://{project_id}")
def project_resource(project_id: str) -> str:
    """Full project context - load this when discussing a specific project."""
    return resources.get_project_summary(project_id)

@mcp.resource("schedule://{project_id}")
def schedule_resource(project_id: str) -> str:
    """Project schedule as markdown table."""
    return resources.get_schedule_markdown(project_id)

@mcp.resource("compliance://{project_id}")
def compliance_resource(project_id: str) -> str:
    """Project compliance checklist."""
    return resources.get_compliance_checklist(project_id)


# ============ PROMPTS ============
@mcp.prompt()
def daily_report_template(project_id: str) -> str:
    """Generate today's site daily report for a project."""
    return prompts.daily_report(project_id)

@mcp.prompt()
def risk_assessment_template(project_id: str) -> str:
    """Run a comprehensive risk assessment for a project."""
    return prompts.risk_assessment(project_id)


if __name__ == "__main__":
    mcp.run()
```

#### `tools.py`（业务逻辑，从 core-tools 包导入）

```python
from core_tools import defects as defects_tools
from core_tools import compliance as compliance_tools
from core_tools import schedule as schedule_tools

def find_defects_by_type(project_id: str, defect_type: str) -> list[dict]:
    return defects_tools.find_by_type(project_id, defect_type)

def check_compliance(project_id: str) -> dict:
    return compliance_tools.check(project_id)

# ... 其他工具直接代理到 core-tools
```

### 配置 Claude Desktop（README 必写）

用户装上你的 server 只要两步：

```bash
# 1. 安装
pip install construction-mcp-server
```

```json
// 2. 在 ~/Library/Application Support/Claude/claude_desktop_config.json 加：
{
  "mcpServers": {
    "construction": {
      "command": "python",
      "args": ["-m", "construction_mcp.server"]
    }
  }
}
```

重启 Claude Desktop → 工具图标里就出现了你的工具。

### Demo 场景（README 截图必备）

**截图 1**：用户在 Claude Desktop 输入：
> "@project://PRJ-001 这个项目今天的合规风险怎么样？"
>
> Claude 自动加载 resource、调用 `check_compliance` 工具、综合输出报告。

**截图 2**：用户点 `/risk_assessment_template` prompt 模板，填入 PRJ-002，Claude 自动跑完整风险评估流程。

**截图 3**：在 **Cursor 编辑器**里也能用同一个 server——证明跨客户端兼容。

这三张图一摆，项目立刻从"我做了个 server"变成"我交付了一个完整产品"。

### 亮点功能 Checklist

- [ ] **支持两种传输模式**：stdio（本地）+ SSE（远程，团队部署用）
- [ ] **OAuth 认证**：模拟生产场景，用户登录后才能访问
- [ ] **MCP Inspector 测试**：用官方调试工具录屏，证明每个工具都过测
- [ ] **发布到 PyPI**：`pip install` 就能装，证明懂打包发布
- [ ] **类型注解完整**：所有工具都有完整 type hints + docstring（MCP 会自动转成 schema）

### CV 写法（项目 B 单独）

> **Construction Domain MCP Server** | Python, Model Context Protocol, Anthropic SDK
>
> - Implemented a Model Context Protocol server exposing 5 tools, 3 resources, and 2 prompt templates for construction project management, enabling any MCP-compatible LLM client (Claude Desktop, Cursor, Claude Code) to perform agentic workflows over project data.
> - Designed clean separation between transport layer (stdio/SSE) and business logic, with comprehensive test coverage using MCP Inspector.
> - Published as installable Python package with complete documentation and multi-client integration examples.
> - GitHub: [link with screenshots showing usage in Claude Desktop + Cursor]

### 面试可能被问什么

| 问题 | 你要准备的答案 |
|------|------------|
| MCP 跟普通 REST API 有什么区别？为什么要用 MCP？ | 1) 协议层标准化（REST 各家不一，MCP 统一 schema）2) 专为 LLM 设计（tool/resource/prompt 三原语）3) 双向通信（支持 server 主动推送 progress、log）4) 发现机制（客户端连上自动发现工具，不用硬编码）|
| Tools 和 Resources 什么时候各用哪个？ | Tools 是 LLM 主动调用、有副作用、需要 reasoning；Resources 是用户/客户端引用、只读、加载到上下文 |
| 怎么测试 MCP Server？ | 用 MCP Inspector 调试每个工具/资源/提示，加单测覆盖业务逻辑层 |
| stdio vs SSE 怎么选？ | stdio = 本地进程通信，简单零配置；SSE = 远程 HTTP 长连接，团队/云端部署用 |

---

## 两个项目的协同

### 共享代码

```
项目 A 的工具 (5 个) ──┐
                       ├──→ core-tools 包 ──→ 项目 B 的 MCP Server
项目 B 的 5 个工具    ──┘
```

业务逻辑写在 `core-tools` 包里，两个项目都从这里 import。

### 优势

- **代码复用**：工具实现写一次
- **架构感**：面试时能讲"我先建工具层，再建上层应用，工具层同时支持 scheduled agent 和 MCP server 两种消费方式"
- **省时间**：实际工作量比单独做两个少 30%

### CV 联起来讲（最强写法）

> **PulseBuild AI Toolkit** | Monorepo: Construction Domain LLM Agent + MCP Server
>
> Built an integrated LLM agent platform for construction project management with two consumption modes:
>
> 1. **Proactive Delay Agent**: Daily scheduled agent that analyzes project data and pushes risk alerts to Slack via Claude's tool-use API with structured error handling and 20-case LLM-as-judge eval suite (87% correctness).
>
> 2. **MCP Server**: Same business tools exposed via Model Context Protocol (5 tools + 3 resources + 2 prompts) for use in Claude Desktop, Cursor, and other MCP-compatible clients.
>
> Designed shared `core-tools` package so business logic is written once and consumed by both surfaces. Achieved 85% token reduction via Anthropic prompt caching.
>
> GitHub: [link]

---

## 时间预算

假设周末写 + 平日晚上：

| 阶段 | 内容 | 时间 |
|------|------|------|
| Day 1-2 | 搭 monorepo 骨架、生成 mock 数据、写 core-tools 包 | 2 天 |
| Day 3-5 | 项目 A：Agent 主循环、工具集成、Slack 通知 | 3 天 |
| Day 6-7 | 项目 A：Eval 设计、跑 20 个 case、记录 metrics | 2 天 |
| Day 8-10 | 项目 B：MCP Server 包装、Resources 和 Prompts | 3 天 |
| Day 11-12 | 项目 B：Claude Desktop 集成截图、Cursor 测试 | 2 天 |
| Day 13-14 | README、demo 视频、PyPI 发布、CV 包装 | 2 天 |

**总计 14 天**能把两个项目都做到能拿出来面试的程度。

---

## CV 最终写法

### 简洁版（一行 bullet）

> **Construction AI Toolkit** — Built proactive delay-detection agent + MCP server using Claude API, achieving 87% eval correctness; published as installable Python package usable in Claude Desktop, Cursor, and Claude Code. [GitHub link]

### 完整版（项目专门一段）

> **PulseBuild AI Toolkit** | Python, Claude API, MCP, Anthropic SDK | [GitHub]
>
> Built an integrated LLM agent platform for construction project management with two consumption modes sharing a single business-logic core:
>
> - **Proactive Delay Agent**: Daily scheduled agent orchestrating 5 custom tools (schedule analysis, weather forecasting, historical pattern matching, Slack notification) through Claude's tool-use API with max-iteration safeguard and structured error handling.
> - **MCP Server**: Same tools exposed via Model Context Protocol (5 tools + 3 resources + 2 prompt templates), enabling any MCP-compatible client (Claude Desktop, Cursor, Claude Code) to perform agentic workflows.
> - Designed 20-case eval suite using LLM-as-judge methodology: 87% correctness on severity classification, 92% specificity on data citation.
> - Reduced average per-run cost to $0.03 via Anthropic prompt caching, cutting token usage by ~85%.

---

## 启动 Checklist（开始前）

- [ ] 注册 Anthropic API Key（claude.com/settings/keys）
- [ ] 安装 Python 3.11+
- [ ] 安装 [uv](https://docs.astral.sh/uv/)（推荐的 Python 包管理器，比 pip 快很多）
- [ ] 注册 OpenWeather API（免费）
- [ ] 创建一个 Slack workspace + 配置 Incoming Webhook（免费）
- [ ] 装好 Claude Desktop（用于测试 MCP Server）
- [ ] 创建 GitHub repo `construction-ai-toolkit`
- [ ] 第一行代码前先写 README 大纲（先想清楚再写）

---

## 快速命令参考

```bash
# 初始化 monorepo
mkdir construction-ai-toolkit && cd construction-ai-toolkit
uv init
uv add anthropic mcp pandas python-dotenv apscheduler requests pyyaml

# 安装 dev 依赖
uv add --dev pytest pytest-asyncio ruff

# 跑项目 A
uv run python -m delay_agent.scheduler

# 跑项目 B（MCP Server）
uv run python -m construction_mcp.server

# 用 MCP Inspector 调试项目 B
npx @modelcontextprotocol/inspector uv run python -m construction_mcp.server

# 跑 eval
uv run python evals/run_eval.py
```

---

## 资源链接

- [Anthropic Tool Use 文档](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview)
- [MCP 官方文档](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Inspector（调试工具）](https://github.com/modelcontextprotocol/inspector)
- [Anthropic Prompt Caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching)
- [Claude Desktop 配置说明](https://modelcontextprotocol.io/quickstart/user)

---

> 最后一句话：**不要追求完美才动手，先让它跑起来，再迭代**。第一版能在终端打印出"Agent 跑完了"就是巨大的进步。Good luck 🚀

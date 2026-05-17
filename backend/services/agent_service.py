"""
Agent 服务编排层：初始化 LLM + 工具，创建 Tool Calling Agent，
并以流式（SSE 兼容）的方式输出 Agent 中间思考过程与最终报告。
"""
from typing import AsyncGenerator
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from tools import search_medical_guidelines, query_historical_cases, check_drug_interaction

# ============================================================
# 医学 Agent 系统提示词
# ============================================================
SYSTEM_PROMPT = """你是一个专业的**智能临床诊疗辅助系统**，服务于一线临床医生。

## 你的能力
你可以调用以下三个工具来获取诊疗所需的信息：
1. **search_medical_guidelines**：检索权威临床诊疗指南（涵盖高血压、糖尿病、冠心病、消化性溃疡、类风湿关节炎等常见内科疾病）。
2. **query_historical_cases**：查询本地数据库中历史相似病例的诊疗方案和用药记录。
3. **check_drug_interaction**：检查多种药物之间的配伍禁忌和相互作用风险。

## 推荐工作流程
当医生输入患者症状后，你应该按以下步骤进行分析：
1. **理解病情**：提取患者症状中的关键医学概念（主诉、可能的诊断方向）。
2. **检索指南**：调用 search_medical_guidelines 查询相关疾病的权威诊疗规范。
3. **参考经验**：调用 query_historical_cases 查看历史上类似病例的用药经验。
4. **核查用药**：结合指南推荐和历史用药，整理出候选药物列表后，**务必**调用 check_drug_interaction 检查药物之间的配伍禁忌。
5. **综合报告**：整合以上信息，输出一份结构化的诊疗辅助报告。

## 重要原则
- 你是一个**辅助决策工具**，最终诊疗决策必须由执业医师做出。
- 调用工具时，请使用精确的医学术语作为关键词，以提高检索命中率。
- 在推荐任何药物方案前，必须先调用 check_drug_interaction 确认安全性。
- 如果某工具返回的信息不足，请如实告知，不要编造医学信息。
- 报告中应明确区分"指南推荐"和"历史经验"两类参考来源。

## 输出格式（最终报告）
请使用 Markdown 格式输出结构化的诊疗辅助报告，至少包含以下板块：

### 一、病情概要
- 主诉提炼
- 关键临床表现总结

### 二、诊疗指南参考
- 来源标注
- 推荐检查项目
- 推荐治疗方案（含药物类别和具体药物）

### 三、历史相似病例参考
- 相似病例概述
- 历史用药经验汇总

### 四、药物安全性评估
- 候选药物清单
- 配伍禁忌检查结果
- 高风险组合警示（如有）

### 五、综合诊疗建议
- 推荐用药方案（分级：一线/二线/辅助）
- 用药注意事项（剂量提醒、禁忌症、监测指标）
- 随访建议

### 六、重要免责声明
- 本报告由 AI 辅助生成，不构成正式医疗处方
- 最终诊疗方案需由执业医师结合患者具体情况确定
"""


def _build_llm() -> ChatOpenAI:
    """构建通义千问 LLM 实例（通过 DashScope OpenAI 兼容接口）。"""
    return ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        temperature=0.3,
        streaming=True,
        timeout=60,
        max_retries=2,
    )


def _build_agent():
    """构建 Tool Calling Agent（LangGraph CompiledStateGraph）。"""
    llm = _build_llm()
    tools = [search_medical_guidelines, query_historical_cases, check_drug_interaction]
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )


async def run_medical_agent(
    query: str,
    db_session: AsyncSession | None = None,
) -> AsyncGenerator[dict, None]:
    """异步执行医疗 Agent，以流式字典序列返回中间过程与最终结果。

    返回的 dict 类型：
    - {"type": "tool_log", "data": "..."}   → 工具调用和返回的日志
    - {"type": "final_answer", "data": "..."} → 最终报告（Markdown 流式片段）
    - {"type": "done"}                        → 流结束信号

    Parameters
    ----------
    query : str
        医生输入的患者症状描述或咨询问题。
    db_session : AsyncSession | None
        数据库会话（由 FastAPI 依赖注入提供），
        当前工具内部自行管理数据库连接，此参数保留供后续使用。

    Yields
    ------
    dict : SSE-compatible 的事件对象
    """
    agent = _build_agent()

    # is_final 标记：初始为 False，首次工具返回后切换为 True，
    # 此后的 LLM 流式输出即视为最终报告内容。
    is_final = False

    try:
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": query}]},
            version="v2",
        ):
            kind = event["event"]

            # ---------- 工具开始调用 ----------
            if kind == "on_tool_start":
                tool_name = event["name"]
                tool_input = event["data"].get("input", {})
                # 将工具输入格式化为可读字符串
                input_str = _format_tool_input(tool_input)
                yield {
                    "type": "tool_log",
                    "data": f"🔍 正在调用工具 **{tool_name}**\n查询参数：{input_str}\n",
                }

            # ---------- 工具调用结束 ----------
            elif kind == "on_tool_end":
                tool_name = event["name"]
                output = event["data"].get("output", "")
                output_str = _format_tool_output(output)
                yield {
                    "type": "tool_log",
                    "data": f"✅ 工具 **{tool_name}** 返回结果：\n{output_str}\n\n---\n",
                }
                is_final = True  # 工具返回后的 LLM 输出为最终报告

            # ---------- LLM 流式输出 ----------
            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content if hasattr(chunk, "content") else ""
                # 只输出纯文本内容（跳过 tool_call 的 JSON 片段）
                if content and isinstance(content, str):
                    if is_final:
                        yield {"type": "final_answer", "data": content}
                    else:
                        # 工具调用前的 LLM 思考过程也放入 tool_log
                        yield {"type": "tool_log", "data": content}

    except Exception as e:
        yield {
            "type": "tool_log",
            "data": f"❌ Agent 执行出错：{type(e).__name__} - {str(e)}",
        }
        yield {"type": "done"}
        return

    yield {"type": "done"}


def _format_tool_input(tool_input: dict) -> str:
    """将工具输入字典格式化为可读的单行字符串。"""
    if not tool_input:
        return "（无参数）"
    parts = []
    for k, v in tool_input.items():
        if isinstance(v, list):
            v_str = "、".join(str(x) for x in v)
        else:
            v_str = str(v)
        # 截断过长内容
        if len(v_str) > 80:
            v_str = v_str[:80] + "..."
        parts.append(f"{k} = {v_str}")
    return "，".join(parts)


def _format_tool_output(output) -> str:
    """将工具输出（可能是 ToolMessage 或纯字符串）格式化为可读字符串。"""
    if hasattr(output, "content"):
        text = output.content
    else:
        text = str(output)
    # 工具输出可能很长，保留完整内容供 LLM 理解
    return text.strip()

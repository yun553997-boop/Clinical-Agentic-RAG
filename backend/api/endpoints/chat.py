"""
聊天 API 端点：暴露 SSE 流式的 Agent 对话接口。
"""
import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.config import settings
from core.database import get_db
from services.agent_service import run_medical_agent

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentChatRequest(BaseModel):
    """POST /api/chat/agent 的请求体。"""
    query: str = Field(
        ...,
        description="患者症状描述或临床咨询问题",
        min_length=1,
        max_length=5000,
        examples=[
            "患者男，58岁，高血压病史10年，2型糖尿病5年。近一周出现头晕、视物模糊，自测血压165/95mmHg，空腹血糖8.2mmol/L。请给出诊疗建议。"
        ],
    )


async def _sse_event_generator(query: str, db: AsyncSession):
    """将 Agent 输出的 dict 流转换为 SSE 格式的字节流。"""
    async for event in run_medical_agent(query, db):
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/agent", summary="AI 临床辅助诊疗（SSE 流式）")
async def agent_chat(
    request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """接收患者症状描述，通过 Agentic RAG 工作流生成流式诊疗建议。

    返回 SSE (Server-Sent Events) 流，每条事件的 JSON 格式：
    - {"type": "tool_log", "data": "..."}   → Agent 工具调用的实时日志
    - {"type": "final_answer", "data": "..."} → 最终 Markdown 报告（流式拼接）
    - {"type": "done"}                        → 流结束
    """
    return StreamingResponse(
        _sse_event_generator(request.query, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ═══════════════════════════════════════════════════════════════════════
# AI 智能导诊（患者端）
# ═══════════════════════════════════════════════════════════════════════

TRIAGE_SYSTEM_PROMPT = (
    "你是一位专业的医院导诊台护士。请根据患者描述的症状，用亲切、通俗的语言分析他们可能存在健康问题，"
    "并明确推荐他们去哪一个具体的科室挂号（可供选择的科室包含：消化内科、心内科、内科、外科、儿科、妇产科、急诊科、骨科、眼科、皮肤科）。"
    "最后给出一句温馨的就医提示。"
)


class TriageRequest(BaseModel):
    """POST /api/chat/triage 的请求体。"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户输入的症状")


def _build_triage_llm() -> ChatOpenAI:
    """构建导诊专用 LLM 实例。"""
    return ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        temperature=0.5,
        streaming=True,
        timeout=60,
        max_retries=2,
    )


async def _triage_sse_generator(message: str):
    """流式生成导诊回复的 SSE 事件。"""
    llm = _build_triage_llm()
    messages = [
        SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
        HumanMessage(content=message),
    ]
    try:
        async for chunk in llm.astream(messages):
            content = chunk.content if hasattr(chunk, "content") else ""
            if content and isinstance(content, str):
                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    yield "data: {\"done\": true}\n\n"


@router.post("/triage", summary="AI 智能导诊（SSE 流式）")
async def triage_chat(request: TriageRequest):
    """接收患者症状描述，返回导诊分诊建议（流式文本）。

    返回 SSE 流，每条事件的 JSON 格式：
    - {"content": "..."}  → 流式文本片段
    - {"done": true}      → 流结束
    """
    return StreamingResponse(
        _triage_sse_generator(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

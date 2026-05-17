"""
聊天 API 端点：暴露 SSE 流式的 Agent 对话接口。
"""
import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

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
        # SSE 格式：data: <json>\n\n
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
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲（如有反向代理）
        },
    )

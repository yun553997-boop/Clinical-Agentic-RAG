"""
历史病历 SQL 查询工具 —— 从 PostgreSQL 数据库中检索相似病例及用药记录。
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from models.patient import Patient, MedicalRecord


class QueryHistoricalCasesInput(BaseModel):
    """query_historical_cases 工具的输入参数 schema。

    注意：这个 Pydantic 模型的字段描述会被 LangChain 自动转换为
    Tool 的 argument 描述，LLM 据此决定如何填充参数。请务必使用
    清晰的中文说明每个字段的含义和格式要求。
    """

    disease_keyword: str = Field(
        description=(
            "疾病关键词或诊断名称，用于在历史就诊记录中检索相似病例。例如：'高血压'、"
            "'2型糖尿病'、'冠心病'、'消化性溃疡'、'类风湿关节炎'、'胃炎'。"
            "支持模糊匹配——输入'高血压'可同时匹配'原发性高血压'和'高血压性心脏病'。"
            "如果患者有多种合并症，建议分别查询每种疾病以获取更全面的用药参考。"
        )
    )
    min_age: int | None = Field(
        default=None,
        description=(
            "可选参数：患者最小年龄。用于筛选与当前患者年龄段相近的历史病例，"
            "因为不同年龄段的用药方案可能差异较大（如老年患者需考虑肾功能调整剂量）。"
            "如果不需要年龄过滤，请留空或传入 null。"
        ),
    )
    max_age: int | None = Field(
        default=None,
        description=(
            "可选参数：患者最大年龄。配合 min_age 使用以划定年龄段。"
            "如果仅设置 min_age 而留空 max_age，则查询所有 ≥min_age 的病例。"
        ),
    )
    limit: int = Field(
        default=5,
        description=(
            "可选参数：返回的历史病例数量上限，默认值为 5。"
            "建议根据查询的疾病常见程度调整——常见病(如高血压)可设较大值，罕见病可设较小值。"
        ),
    )


@tool(args_schema=QueryHistoricalCasesInput)
async def query_historical_cases(
    disease_keyword: str,
    min_age: int | None = None,
    max_age: int | None = None,
    limit: int = 5,
) -> str:
    """【历史相似病例查询工具 —— 从本地 PostgreSQL 数据库中检索相似病例及用药方案】

## 功能说明
本工具连接到本医院的历史病历数据库，根据疾病关键词和可选年龄段筛选相似的就诊记录。
返回结果包含：患者基本信息（年龄、基础病史）、症状描述、诊断结果、
以及最重要的——**历史上针对该疾病使用过的处方药物列表**。
这些历史用药信息可为当前诊疗提供重要参考。

## 数据库查询范围
本工具查询以下两张关联表：
- `patients`（患者表）：包含患者姓名、年龄、基础病史。
- `medical_records`（就诊记录表）：包含每次就诊的症状、诊断结果和开具药物。
两张表通过 `patient_id` 外键一对多关联，一次查询可获取每位患者的完整就诊历史。

## 适用场景（何时调用本工具）
1. **参考历史用药经验**：当面对某一疾病时，想知道"以前类似的病人用了什么药、效果如何？"
   例如：查询"高血压"的历史病例，可以统计出硝苯地平、厄贝沙坦等药物的使用频率。
2. **发现治疗方案模式**：对某一疾病的常见联合用药方案进行归纳。
   例如：胃炎患者常同时使用PPI（奥美拉唑）+ 胃黏膜保护剂 + 促动力药。
3. **年龄分层用药参考**：老年患者和年轻患者对同一疾病的用药可能不同（剂量、品种选择）。
   通过设置年龄范围参数，筛选出与当前患者情况更接近的历史案例。
4. **合并症用药参考**：当患者有多种疾病时，逐一查询每种疾病的历史用药，帮助发现潜在的药物组合方案。

## 不适用场景
- 查询权威医学指南或诊疗规范 → 请使用 search_medical_guidelines 工具。
- 检查具体药物之间的配伍禁忌 → 请使用 check_drug_interaction 工具。
- 查询患者个人身份信息以外的外部医学文献 → 本工具仅查询内部数据库。

## 输入参数
- `disease_keyword` (str, 必填): 疾病关键词，如'高血压'、'糖尿病'。支持模糊匹配。
- `min_age` (int, 可选): 最小年龄过滤条件，默认为空（不限）。
- `max_age` (int, 可选): 最大年龄过滤条件，默认为空（不限）。
- `limit` (int, 可选): 返回的最大病例数，默认 5 条。

## 返回值
返回一个文本字符串，按格式列出每个匹配病例的：
- 患者年龄与基础病史
- 症状描述
- 诊断结果
- 开具药物列表（用逗号分隔）

如果未找到匹配病例，返回"未找到匹配的历史就诊记录"。

## 使用提示
- 建议先调用本工具获取历史经验用药，再调用 search_medical_guidelines 获取指南推荐，
  对比两者异同后可获得更全面的诊疗参考。
- 如果当前患者有多种诊断，请分别调用本工具查询每种疾病。
- 返回的药物列表仅为历史记录，不构成直接的处方建议，请结合指南和药物禁忌综合判断。
"""
    try:
        async with AsyncSessionLocal() as session:
            # 构建查询条件：在 medical_records.diagnosis 和 medical_records.symptoms 中模糊搜索
            keyword_pattern = f"%{disease_keyword}%"

            conditions = [
                MedicalRecord.diagnosis.ilike(keyword_pattern),
                MedicalRecord.symptoms.ilike(keyword_pattern),
            ]

            # 如果需要按年龄筛选，则 JOIN patients 表添加年龄条件
            base_query = select(MedicalRecord, Patient).join(
                Patient, MedicalRecord.patient_id == Patient.id
            )

            # 应用疾病关键词过滤
            base_query = base_query.where(or_(*conditions))

            # 可选：年龄段过滤
            if min_age is not None:
                base_query = base_query.where(Patient.age >= min_age)
            if max_age is not None:
                base_query = base_query.where(Patient.age <= max_age)

            # 按就诊时间倒序，取最近的记录
            base_query = base_query.order_by(
                MedicalRecord.visit_time.desc()
            ).limit(limit)

            result = await session.execute(base_query)
            rows = result.all()

            if not rows:
                return (
                    f"在历史数据库中未找到与'{disease_keyword}'相关的就诊记录。"
                    f"建议尝试更通用的关键词，或检查数据库是否已初始化 Mock 数据。"
                )

            lines = [
                f"## 历史相似病例查询结果（关键词：'{disease_keyword}'，共 {len(rows)} 条记录）\n"
            ]
            for i, (record, patient) in enumerate(rows, 1):
                age_info = f"{patient.age}岁" if patient.age else "未知年龄"
                lines.append(f"### 病例 {i}")
                lines.append(f"- **患者年龄**：{age_info}")
                lines.append(f"- **基础病史**：{patient.medical_history or '无记录'}")
                lines.append(f"- **就诊症状**：{record.symptoms}")
                lines.append(f"- **诊断结果**：{record.diagnosis}")
                if record.prescribed_drugs:
                    drugs = record.prescribed_drugs.replace("，", ",")
                    lines.append(f"- **开具药物**：{drugs}")
                else:
                    lines.append(f"- **开具药物**：无记录")
                lines.append("")

            # 汇总所有涉及的药物
            all_drugs_set: set[str] = set()
            for record, _ in rows:
                if record.prescribed_drugs:
                    for drug in record.prescribed_drugs.replace("，", ",").split(","):
                        drug = drug.strip()
                        if drug:
                            all_drugs_set.add(drug)
            if all_drugs_set:
                drugs_list = "、".join(sorted(all_drugs_set))
                lines.append(f"### 历史用药汇总")
                lines.append(f"以上 {len(rows)} 条病例中共涉及以下药物：{drugs_list}。")
                lines.append("请注意：此汇总仅供参考，具体用药需结合患者个体情况和最新指南综合判断。")

            return "\n".join(lines)

    except Exception as e:
        return (
            f"数据库查询过程中发生错误：{type(e).__name__} - {str(e)}。"
            f"请检查 PostgreSQL 是否正常运行，或联系系统管理员排查数据库连接。"
        )

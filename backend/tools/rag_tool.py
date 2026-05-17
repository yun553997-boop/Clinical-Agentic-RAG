"""
医学指南 RAG 检索工具 —— 基于 ChromaDB 向量库检索临床指南文本。
使用 ONNX 本地嵌入模型，无需外部 API 调用。
"""
import os
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import chromadb
from chromadb.utils import embedding_functions

# ChromaDB 持久化目录（位于 backend/chroma_db）
_CHROMA_DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db"
)

# 使用 ONNX 本地嵌入模型（all-MiniLM-L6-v2，无需 GPU 和外部 API）
_embedding_fn = embedding_functions.ONNXMiniLM_L6_V2()

# 全局 ChromaDB 客户端与集合（懒加载）
_client = None
_collection = None

# Mock 医学指南语料：涵盖高血压、糖尿病、冠心病、胃炎、类风湿等常见疾病
_MOCK_GUIDELINES: list[str] = [
    # 高血压相关
    (
        "高血压药物治疗原则：初始治疗推荐使用长效降压药，优先选择血管紧张素转换酶抑制剂(ACEI)、"
        "血管紧张素II受体拮抗剂(ARB)、钙通道阻滞剂(CCB)或噻嗪类利尿剂。2级及以上高血压常需联合用药，"
        "如CCB+ACEI/ARB、ACEI/ARB+利尿剂等组合。合并糖尿病者首选ACEI/ARB以保护肾功能。"
        "老年患者目标血压<150/90mmHg，一般人群<140/90mmHg。"
    ),
    (
        "高血压急症处理指南：高血压急症定义为血压显著升高(常>180/120mmHg)伴急性靶器官损害。"
        "治疗首选静脉用药，如硝普钠、硝酸甘油或拉贝洛尔。降压速度需控制在1小时内降低平均动脉压不超过25%，"
        "24-48小时内降至160/100mmHg左右。硝苯地平短效制剂舌下含服因降压过快已不推荐常规使用。"
    ),
    (
        "高血压药物禁忌症：ACEI/ARB禁用于双侧肾动脉狭窄、高钾血症(血钾>5.5mmol/L)及妊娠期妇女。"
        "β受体阻滞剂(如美托洛尔)禁用于严重心动过缓、二度及以上房室传导阻滞、支气管哮喘急性发作期。"
        "CCB类相对禁用于严重心力衰竭患者(除氨氯地平外)。噻嗪类利尿剂禁用于痛风患者。"
    ),
    # 糖尿病相关
    (
        "2型糖尿病诊疗指南：诊断标准为空腹血糖≥7.0mmol/L或OGTT 2h血糖≥11.1mmol/L或HbA1c≥6.5%。"
        "一线治疗为生活方式干预+二甲双胍。血糖控制不佳时可联合使用SGLT-2抑制剂(如达格列净)、"
        "GLP-1受体激动剂(如利拉鲁肽)、DPP-4抑制剂(如西格列汀)等。HbA1c目标一般<7.0%，老年或合并症多者可放宽至<8.0%。"
        "合并心血管疾病或慢性肾病者优先选择SGLT-2抑制剂或GLP-1受体激动剂。"
    ),
    (
        "糖尿病药物配伍注意事项：二甲双胍与碘造影剂联用有乳酸酸中毒风险，造影前后48小时应停用。"
        "磺脲类降糖药(如格列美脲)与阿司匹林、华法林等合用可能增强降糖效应导致低血糖。"
        "胰岛素与糖皮质激素合用可导致血糖升高，需增加胰岛素剂量。SGLT-2抑制剂与利尿剂合用增加脱水和低血压风险。"
    ),
    # 冠心病相关
    (
        "冠心病稳定型心绞痛诊疗指南：诊断依据包括典型胸痛症状、心电图ST-T改变、冠脉CTA或冠脉造影。"
        "药物治疗包括抗血小板(阿司匹林75-100mg/日或氯吡格雷75mg/日)、他汀类降脂(目标LDL-C<1.8mmol/L或降幅≥50%)、"
        "β受体阻滞剂(如美托洛尔)控制心率和心绞痛、硝酸酯类(如单硝酸异山梨酯)缓解症状。"
        "合并高血压者加用ACEI/ARB。所有患者需长期二级预防。"
    ),
    (
        "急性冠脉综合征(ACS)抗栓治疗：STEMI患者需紧急再灌注(PCI或溶栓)。双联抗血小板(DAPT)方案："
        "阿司匹林+P2Y12受体抑制剂(替格瑞洛或氯吡格雷)，至少持续12个月。"
        "高危出血者考虑缩短DAPT至6个月，低出血风险者可延长至>12个月。"
        "合并房颤需三联抗栓者尽量缩短至1周-1月后转为二联(抗凝+单一抗血小板)。"
    ),
    # 消化系统相关
    (
        "消化性溃疡诊疗指南：主要病因包括幽门螺杆菌(Hp)感染和NSAIDs类药物使用。"
        "Hp阳性者需行根除治疗，推荐四联疗法(PPI+铋剂+两种抗生素，如阿莫西林+克拉霉素)疗程14天。"
        "NSAIDs相关溃疡应停用NSAIDs，给予PPI(如奥美拉唑20mg bid)治疗4-8周。"
        "胃黏膜保护剂(铝碳酸镁、瑞巴派特等)可作为辅助治疗。PPI长期使用需注意维生素B12缺乏和骨质疏松风险。"
    ),
    (
        "胃食管反流病(GERD)诊治要点：典型症状为烧心和反流。一线治疗为PPI(奥美拉唑、雷贝拉唑等)标准剂量每日一次，疗程4-8周。"
        "PPI疗效不佳者可加倍剂量或更换为艾司奥美拉唑。促动力药(莫沙必利)可改善胃排空。"
        "长期PPI使用者需定期评估是否需要维持治疗，考虑按需治疗或降阶梯治疗。"
    ),
    # 类风湿关节炎相关
    (
        "类风湿关节炎(RA)诊疗指南：诊断依据包括关节肿痛(尤其是近端指间关节、掌指关节、腕关节)、"
        "晨僵持续>1小时、RF和抗CCP抗体阳性、CRP/ESR升高等。"
        "治疗采用达标治疗策略，目标为临床缓解或低疾病活动度。初始治疗推荐甲氨蝶呤(MTX)作为锚定药物，"
        "联合NSAIDs(如塞来昔布、依托考昔)控制症状。MTX疗效不佳者加用生物制剂(TNF-α抑制剂如阿达木单抗)或JAK抑制剂。"
        "长期使用糖皮质激素者需补充钙剂和维生素D，并定期监测骨密度。"
    ),
    (
        "NSAIDs药物使用注意事项：非选择性NSAIDs(布洛芬、双氯芬酸)同时抑制COX-1和COX-2，胃肠道不良反应风险高。"
        "COX-2选择性抑制剂(塞来昔布)胃肠道风险较低，但心血管风险可能增加。"
        "NSAIDs禁用于活动性消化道溃疡、严重肾功能不全(eGFR<30ml/min)及严重心力衰竭患者。"
        "老年患者使用NSAIDs应同时给予PPI保护胃黏膜，并尽量使用最低有效剂量、最短疗程。"
    ),
    # 高脂血症相关
    (
        "血脂异常管理指南：心血管风险分层决定降脂治疗强度。极高危者LDL-C目标<1.4mmol/L且降幅≥50%。"
        "他汀类(阿托伐他汀、瑞舒伐他汀)为一线降脂药物。他汀不耐受或疗效不佳者加用依折麦布或PCSK9抑制剂。"
        "高甘油三酯血症(>5.6mmol/L)需使用贝特类药物预防急性胰腺炎。"
        "他汀类与秋水仙碱、大环内酯类抗生素合用时肌病风险增加，需监测肌酸激酶。"
    ),
]

# 每个指南文档对应的元数据（用于追溯来源）
_MOCK_METADATAS: list[dict] = [
    {"source": "中国高血压防治指南(2024修订版)", "topic": "高血压药物治疗"},
    {"source": "中国高血压防治指南(2024修订版)", "topic": "高血压急症"},
    {"source": "中国高血压防治指南(2024修订版)", "topic": "高血压药物禁忌"},
    {"source": "中国2型糖尿病防治指南(2024版)", "topic": "糖尿病诊疗"},
    {"source": "中国2型糖尿病防治指南(2024版)", "topic": "糖尿病药物配伍"},
    {"source": "中国冠心病诊断与治疗指南(2024)", "topic": "稳定型心绞痛"},
    {"source": "中国冠心病诊断与治疗指南(2024)", "topic": "ACS抗栓治疗"},
    {"source": "消化性溃疡诊疗指南(2024)", "topic": "消化性溃疡"},
    {"source": "消化性溃疡诊疗指南(2024)", "topic": "GERD"},
    {"source": "中国类风湿关节炎诊疗指南(2024)", "topic": "RA诊疗"},
    {"source": "中国类风湿关节炎诊疗指南(2024)", "topic": "NSAIDs使用"},
    {"source": "中国血脂管理指南(2024)", "topic": "血脂异常"},
]


def _get_collection():
    """懒加载获取或创建 ChromaDB 集合，首次调用时自动灌入 Mock 指南数据。"""
    global _client, _collection
    if _collection is None:
        os.makedirs(_CHROMA_DB_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=_CHROMA_DB_DIR)
        _collection = _client.get_or_create_collection(
            name="medical_guidelines",
            embedding_function=_embedding_fn,
        )
        # 如果集合为空，则灌入 Mock 指南数据
        if _collection.count() == 0:
            ids = [f"guideline_{i}" for i in range(len(_MOCK_GUIDELINES))]
            _collection.add(
                documents=_MOCK_GUIDELINES,
                metadatas=_MOCK_METADATAS,
                ids=ids,
            )
    return _collection


class SearchMedicalGuidelinesInput(BaseModel):
    """search_medical_guidelines 工具的输入参数 schema。

    这个 Pydantic 模型的字段描述会被 LangChain 自动转换为 Tool 的参数说明，
    LLM 据此决定如何填充参数。请使用清晰的中文描述每个字段。
    """

    query: str = Field(
        description=(
            "医学检索关键词或自然语言问句，例如：'高血压药物禁忌症'、'2型糖尿病一线治疗方案'、"
            "'冠心病二级预防用药'、'消化性溃疡根除Hp四联方案'、'类风湿关节炎MTX用法'。"
            "建议从患者症状中提取核心医学概念作为检索词，一次检索一个主题以获得最佳结果。"
        )
    )


@tool(args_schema=SearchMedicalGuidelinesInput)
def search_medical_guidelines(query: str) -> str:
    """【医学临床指南检索工具 —— 从本地向量知识库中检索权威医学指南片段】

## 功能说明
本工具连接本地 ChromaDB 向量数据库（使用 ONNX 本地嵌入模型 all-MiniLM-L6-v2），
其中存储了大量中文临床诊疗指南的文本切片，涵盖：高血压、糖尿病、冠心病、
消化性溃疡、类风湿关节炎、高脂血症等常见内科疾病。
当医生或 AI Agent 需要获取某一疾病或症状的权威诊疗指南时，调用本工具进行语义检索。

## 适用场景（何时调用本工具）
1. **诊疗规范查询**：当需要了解某一疾病的标准治疗方案、推荐用药或处理流程时。
   例如："高血压2级的初始治疗用什么药？"、"2型糖尿病血糖控制不佳如何调整方案？"
2. **药物禁忌/相互作用查询**：需要了解某类药物或具体药物的禁忌症、慎用人群时。
   例如："ACEI类药物的禁忌症有哪些？"、"他汀类药物与哪些药物有相互作用？"
3. **临床路径参考**：需要获取某一特定临床情境（如急性冠脉综合征）的处理流程和用药规范。
4. **鉴别诊断辅助**：当症状涉及多个可能的疾病时，检索相关指南帮助缩小诊断范围。

## 不适用场景
- 查询具体患者的个人信息或就诊记录 → 请使用 query_historical_cases 工具。
- 检查两种具体药物之间的配伍禁忌 → 请使用 check_drug_interaction 工具。
- 查询非内科领域的指南（如外科手术指征）→ 本库目前主要覆盖内科常见疾病。

## 输入参数
- `query` (str): 医学检索关键词或自然语言问句。建议从患者症状描述中提炼出核心医学术语。

## 返回值
返回一个文本字符串，包含与检索词最相关的临床指南片段（最多3条），
每条结果附带了来源指南名称和主题标签。
如果向量库中没有匹配的指南，返回"未找到相关指南"。

## 使用提示
- 如果一次检索不够全面，可以尝试从不同角度多次检索。
- 检索结果供 AI Agent 参考和整合，不应直接作为最终诊断意见。
"""
    try:
        collection = _get_collection()
        results = collection.query(query_texts=[query], n_results=3)

        documents: list[str] = results.get("documents", [[]])[0]
        metadatas: list[dict] = results.get("metadatas", [[]])[0]
        distances: list[float] = results.get("distances", [[]])[0] if results.get("distances") else []

        if not documents:
            return "未在医学指南库中找到与查询条件匹配的指南内容。建议尝试更换关键词或扩大检索范围。"

        lines = [f"## 检索到 {len(documents)} 条相关医学指南片段：\n"]
        for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
            source = meta.get("source", "未知来源") if meta else "未知来源"
            topic = meta.get("topic", "") if meta else ""
            dist_str = f"（相关度距离: {distances[i-1]:.4f}）" if distances else ""
            lines.append(f"### 指南片段 {i} —— 来源：{source} | 主题：{topic} {dist_str}")
            lines.append(doc.strip())
            lines.append("")
        return "\n".join(lines)

    except Exception as e:
        return (
            f"医学指南检索过程中发生错误：{type(e).__name__} - {str(e)}。"
            f"请检查 ChromaDB 是否正常运行，或联系系统管理员。"
        )

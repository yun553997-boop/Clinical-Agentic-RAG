"""
Mock 数据初始化脚本：自动建表并插入测试数据（患者 + 用户 + 挂号）。
运行方式：在 backend 目录下执行 `python scripts/init_mock_data.py`
"""
import asyncio
import sys
import os

# 确保 backend 目录在 Python 路径中，方便导入 core 和 models 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import async_engine
from models import Base, Patient, MedicalRecord, User, Appointment
from models.user import UserRole
from core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, func as sqlfunc, delete


async def init_database():
    """异步初始化数据库：建表 + 插入 Mock 数据。"""
    print("=== 开始初始化数据库 ===")

    # 1. 创建所有表结构（不存在则创建）
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] 数据表创建完成（users, patients, medical_records, appointments）")

    # 2. 创建会话并插入 Mock 数据
    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ── 清空旧用户数据（如果存在则重置）──
        user_count_result = await session.execute(select(sqlfunc.count()).select_from(User))
        if user_count_result.scalar() > 0:
            print("[清理] 删除旧的用户和挂号数据...")
            await session.execute(delete(Appointment))
            await session.execute(delete(User))
            await session.commit()
            print("[OK] 旧数据已清空")

        # ── 创建测试用户 ──
        admin = User(
            username="admin",
            hashed_password=get_password_hash("123"),
            role=UserRole.doctor,
            full_name="张医生",
            employee_id="admin",
            department="消化内科",
        )
        patient_user = User(
            username="user",
            hashed_password=get_password_hash("123"),
            role=UserRole.patient,
            full_name="患者李某",
        )
        session.add_all([admin, patient_user])
        await session.flush()
        print(f"[OK] 创建测试用户: admin(医生) / user(患者)")

        # ── 检查是否已有患者数据，避免重复插入 ──
        count_result = await session.execute(select(sqlfunc.count()).select_from(Patient))
        existing_count = count_result.scalar()
        if existing_count > 0:
            print(f"[跳过] 数据库中已有 {existing_count} 位患者，不再重复插入 Mock 数据。")
        else:
            # --- 创建 5 位患者 ---
            p1 = Patient(name="张三", age=58, medical_history="高血压病史10年，2型糖尿病5年")
            p2 = Patient(name="李四", age=45, medical_history="慢性胃炎3年，胃溃疡史")
            p3 = Patient(name="王五", age=72, medical_history="冠心病，高脂血症，轻度肾功能不全")
            p4 = Patient(name="赵六", age=34, medical_history="过敏性鼻炎，无其他慢性病史")
            p5 = Patient(name="孙七", age=61, medical_history="类风湿关节炎，骨质疏松")

            session.add_all([p1, p2, p3, p4, p5])
            await session.flush()  # 刷新以获取自增 ID

            # --- 为每位患者创建 1~2 条就诊记录 ---
            records = [
                # 张三（高血压+糖尿病）—— 降压药
                MedicalRecord(
                    patient_id=p1.id,
                    symptoms="头晕、视物模糊，血压 165/95mmHg，空腹血糖 8.2mmol/L",
                    diagnosis="原发性高血压2级，2型糖尿病血糖控制不佳",
                    prescribed_drugs="硝苯地平缓释片, 二甲双胍, 厄贝沙坦",
                ),
                MedicalRecord(
                    patient_id=p1.id,
                    symptoms="心悸、胸闷，动态血压监测示昼夜节律消失",
                    diagnosis="高血压性心脏病待排",
                    prescribed_drugs="美托洛尔, 硝苯地平缓释片, 阿托伐他汀",
                ),
                # 李四（胃炎+胃溃疡）—— 抑酸药+胃黏膜保护剂
                MedicalRecord(
                    patient_id=p2.id,
                    symptoms="上腹部规律性疼痛，空腹加重，伴反酸嗳气",
                    diagnosis="十二指肠球部溃疡（活动期）",
                    prescribed_drugs="奥美拉唑, 铝碳酸镁, 阿莫西林, 克拉霉素",
                ),
                MedicalRecord(
                    patient_id=p2.id,
                    symptoms="进食后上腹胀痛，恶心，胃镜示胃窦糜烂",
                    diagnosis="慢性糜烂性胃炎",
                    prescribed_drugs="雷贝拉唑, 瑞巴派特, 莫沙必利",
                ),
                # 王五（冠心病+高脂血症）—— 心血管药物
                MedicalRecord(
                    patient_id=p3.id,
                    symptoms="活动后胸闷气促，心电图示ST-T改变，血脂 LDL-C 4.8mmol/L",
                    diagnosis="冠心病稳定型心绞痛，混合型高脂血症",
                    prescribed_drugs="阿司匹林, 阿托伐他汀, 单硝酸异山梨酯, 美托洛尔",
                ),
                # 赵六（过敏性鼻炎）—— 抗组胺药
                MedicalRecord(
                    patient_id=p4.id,
                    symptoms="阵发性喷嚏、流清涕、鼻塞，花粉季加重",
                    diagnosis="季节性过敏性鼻炎",
                    prescribed_drugs="氯雷他定, 布地奈德鼻喷雾剂",
                ),
                # 孙七（类风湿关节炎）—— NSAIDs+DMARDs
                MedicalRecord(
                    patient_id=p5.id,
                    symptoms="双手近端指间关节及腕关节对称性肿痛，晨僵>1小时",
                    diagnosis="类风湿关节炎（活动期），骨质疏松",
                    prescribed_drugs="甲氨蝶呤, 塞来昔布, 碳酸钙D3, 阿仑膦酸钠",
                ),
            ]

            session.add_all(records)
            print(f"[OK] 成功插入 {len(records)} 条就诊记录（5 位患者）")

        await session.commit()

    print("=== 数据库初始化完成 ===")
    print("  测试账号: admin / 123 (医生)")
    print("  测试账号: user  / 123 (患者)")


if __name__ == "__main__":
    asyncio.run(init_database())

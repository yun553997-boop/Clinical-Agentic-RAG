# 当前环境背景

我已经通过 Vue3 完成了多角色（医生/患者）的前端路由骨架，目前登录逻辑和业务页面是 Mock 的。并且前端已经新增了多角色注册页面（患者：账号、姓名、密码；医生：工号、姓名、科室、密码）。

后端已具备 FastAPI 和 PostgreSQL 基础，以及完整的 Agentic RAG 链路。

# 任务目标：实现后端 JWT 鉴权、真实注册功能与医患数据流转 (预约挂号业务)

请在 `backend` 目录下帮我完成以下工作，逐步搭建业务后台：

## 第一步：补充依赖与安全工具

1. 更新 `backend/requirements.txt`，补充 JWT 鉴权需要的包：`python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`。
2. 创建 `backend/core/security.py`：
   - 编写密码 hash 函数 (`get_password_hash`, `verify_password`)。
   - 编写签发 JWT Token 的函数 (`create_access_token`)，请从 `core/config.py` 中读取 `SECRET_KEY` (如果没有请自动补充一个随机字符串) 和 `ALGORITHM="HS256"`。

## 第二步：数据库模型扩充 (Models)

1. 修改或创建 `backend/models/user.py`：
   - 创建 `User` 表：id, username (账号/工号，唯一，患者填账号，医生填工号), hashed_password, role ('doctor' 或 'patient'), full_name (姓名), employee_id (工号，医生专属，可为空), department (科室，医生专属，可为空)。
2. 创建 `backend/models/appointment.py`：
   - 创建 `Appointment` 表：id, patient_id (关联 User表), doctor_id (关联 User表), department (科室), appointment_time (预约时间), status (状态：如'待就诊', '已完成'), symptoms_desc (初步症状描述)。

## 第三步：认证与授权 API (Auth Endpoints)

1. 创建 `backend/api/dependencies.py`：
   - 编写 `get_current_user` 依赖函数，用于从请求头解析 JWT token，并从数据库获取当前用户。
2. 创建 `backend/api/endpoints/auth.py`，实现以下两个接口：
   - **注册接口 POST /api/auth/register**：
     - 接收前端传来的注册数据 (Pydantic Schema 需要包含: username, password, full_name, role。如果 role 是 doctor，还需可选接收 employee_id, department)。
     - 实现逻辑：在数据库中查询 `username` 是否已存在，若存在则返回 HTTP 400 错误。若不存在，则使用 `get_password_hash` 将密码加密后存入数据库，返回注册成功提示。
   - **登录接口 POST /api/auth/login**：
     - 接收 `OAuth2PasswordRequestForm`。
     - 实现逻辑：校验用户名和密码。校验成功后，返回 `{"access_token": token, "token_type": "bearer", "user": {"username": user.username, "role": user.role, "full_name": user.full_name}}`。

## 第四步：医患业务 API (Business Endpoints)

创建 `backend/api/endpoints/appointment.py`，实现两个核心接口：

1. `POST /api/appointments/`：患者端调用。提交预约挂号单，存入数据库。

2. `GET /api/appointments/today`：医生端调用。获取指派给当前医生且状态为“待就诊”的今日挂号列表。

   *(注意：以上接口都需要注入 get_current_user 依赖以确保安全)*

## 第五步：注册路由与初始化数据

1. 在 `backend/main.py` 中注册 `auth.py` 和 `appointment.py` 的路由。
2. 在你之前的 `init_mock_data.py` 脚本中，追加一段逻辑：清空旧表，自动生成两个测试账号（用于防止你不使用注册接口时无号可用）。
   - 账号1: username: 'admin', password: '123', role: 'doctor', full_name: '张医生', employee_id: 'admin', department: '消化内科'
   - 账号2: username: 'user', password: '123', role: 'patient', full_name: '患者李某'
   - （记得使用 `get_password_hash` 把 '123' 加密后存入数据库）。

# 约束条件

- 必须保持代码异步化 (`AsyncSession`)。
- 请直接生成并覆盖文件。完成后，提示我重启后端并运行初始化脚本。
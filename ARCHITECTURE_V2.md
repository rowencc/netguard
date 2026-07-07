# NetGuard 2.0 架构设计

## 核心理念

**LLM 驱动的智能设备识别** — 结合传统 OUI 查找与大语言模型多模态特征分析，实现更精准的 IoT 设备分类。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Cloud Server                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        API Gateway (FastAPI)                     │   │
│  │  /api/devices  /api/alerts  /api/sync  /api/llm  /api/system   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│  ┌─────────────────────────────┼─────────────────────────────────┐    │
│  │                             ▼                                  │    │
│  │  ┌─────────────────────────────────────────────────────┐      │    │
│  │  │              LLM Device Identifier                   │      │    │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │      │    │
│  │  │  │ OUI Lookup  │  │ Hostname    │  │ Port/OS     │ │      │    │
│  │  │  │ (Local DB)  │  │ Analysis    │  │ Fingerprint │ │      │    │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘ │      │    │
│  │  │                    │                                 │      │    │
│  │  │                    ▼                                 │      │    │
│  │  │  ┌─────────────────────────────────────────────┐   │      │    │
│  │  │  │    LLM Inference (Cloud API / Local LLM)     │   │      │    │
│  │  │  │    - Device type classification              │   │      │    │
│  │  │  │    - Risk assessment                         │   │      │    │
│  │  │  │    - Anomaly detection                       │   │      │    │
│  │  │  └─────────────────────────────────────────────┘   │      │    │
│  │  └─────────────────────────────────────────────────────┘      │    │
│  │                             │                                  │    │
│  │  ┌─────────────────────────────────────────────────────┐      │    │
│  │  │              MySQL Database                          │      │    │
│  │  │  - devices  - alerts  - clients  - llm_cache        │      │    │
│  │  └─────────────────────────────────────────────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │ Desktop PC   │ │ ARM Device 1 │ │ ARM Device 2 │
            │ Client Agent │ │ Client Agent │ │ Client Agent │
            │              │ │              │ │              │
            │ - ARP Scan   │ │ - ARP Scan   │ │ - ARP Scan   │
            │ - Ping       │ │ - Ping       │ │ - Ping       │
            │ - Report     │ │ - Report     │ │ - Report     │
            └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 技术选型

### LLM 设备识别方案

参考论文: Mahmood et al. (2025) "Large Language Models for Real-World IoT Device Identification"

**输入特征 (多模态)**:
1. **MAC OUI** — 厂商前缀 (6 bytes)
2. **DHCP Hostname** — 设备主机名 (文本)
3. **Open Ports** — 开放端口签名
4. **OS Fingerprint** — 操作系统信息
5. **mDNS Services** — 服务发现标签

**LLM 推理策略**:

```
方案 A: Cloud LLM API (推荐)
├── 优势: 无需本地 GPU，模型能力强
├── 劣势: 需要网络，有 API 成本
└── 适用: 云端服务器部署

方案 B: Local LLM (边缘计算)
├── 优势: 离线可用，隐私安全
├── 劣势: 需要 GPU，模型能力受限
└── 适用: ARM 设备部署 (可选)

方案 C: Hybrid (混合模式)
├── 本地: 规则引擎 + OUI 查找 (快速)
├── 云端: LLM 分析 (精准)
└── 适用: 最佳平衡
```

### LLM Prompt 设计

```python
SYSTEM_PROMPT = """你是一个专业的网络设备识别专家。
根据以下设备特征，判断设备类型和风险等级。

设备类型分类:
- camera: 摄像头/NVR/DVR
- router: 路由器/交换机/AP
- phone: 手机/平板
- computer: 电脑/服务器
- iot: 智能家居设备
- printer: 打印机
- network_device: 网络设备(防火墙等)
- unknown: 未知设备

风险等级:
- LOW: 正常设备
- MEDIUM: 需要关注
- HIGH: 高风险
- CRITICAL: 严重威胁

请分析以下设备特征并返回 JSON 格式结果。"""

USER_PROMPT = """设备特征:
- MAC OUI: {oui_prefix} ({vendor_name})
- DHCP Hostname: {hostname}
- Open Ports: {ports}
- OS Info: {os_info}
- mDNS Services: {mdns}

请返回:
{
  "device_type": "...",
  "confidence": 0.0-1.0,
  "risk_level": "...",
  "risk_reason": "...",
  "reasoning": "..."
}"""
```

---

## 数据流

### 1. 设备发现 (Client)

```
Client Agent
    │
    ├─► ARP Scan (本地)
    │     └─► 获取 IP + MAC 地址
    │
    ├─► Ping Probe (本地)
    │     └─► 判断在线状态
    │
    ├─► Hostname Resolve (本地)
    │     └─► DNS/NetBIOS/mDNS
    │
    └─► Report to Server
          └─► POST /api/sync/report-devices
```

### 2. 设备识别 (Server)

```
Server receives device data
    │
    ├─► Step 1: OUI Lookup (本地, <1ms)
    │     └─► vendor_lookup.py
    │
    ├─► Step 2: Rule-based Classification (本地, <10ms)
    │     └─► identifier.py (现有逻辑)
    │
    ├─► Step 3: LLM Analysis (云端, 100-500ms)
    │     ├─► 检查缓存 (llm_cache 表)
    │     ├─► 构建 Prompt
    │     ├─► 调用 LLM API
    │     └─► 解析结果
    │
    └─► Step 4: Final Decision
          └─► 融合本地规则 + LLM 结果
```

### 3. 缓存策略

```python
# LLM 结果缓存 (减少 API 调用)
class LLMCache:
    """相同特征组合的结果缓存"""
    
    def get_cache_key(self, features: dict) -> str:
        """基于特征生成缓存键"""
        # OUI + Hostname 模式 + Ports 签名
        return hash(features)
    
    def get(self, features: dict) -> Optional[dict]:
        """查询缓存"""
        # 缓存有效期: 7 天
        
    def set(self, features: dict, result: dict):
        """写入缓存"""
```

---

## API 设计

### Server API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/devices` | GET | 获取设备列表 |
| `/api/devices/{id}` | GET | 获取单个设备 |
| `/api/devices/{id}` | PUT | 更新设备(授权/备注) |
| `/api/alerts` | GET | 获取告警列表 |
| `/api/alerts/{id}/ack` | POST | 确认告警 |
| `/api/sync/heartbeat` | POST | 客户端心跳 |
| `/api/sync/report-devices` | POST | 上报设备数据 |
| `/api/sync/clients` | GET | 获取客户端列表 |
| `/api/llm/identify` | POST | LLM 设备识别 |
| `/api/llm/batch` | POST | 批量识别 |
| `/api/system/health` | GET | 健康检查 |
| `/api/system/stats` | GET | 系统统计 |

### Client API

| 命令 | 说明 |
|------|------|
| `./deploy.sh install` | 安装依赖 |
| `./deploy.sh configure` | 配置客户端 |
| `./deploy.sh start` | 启动客户端 |
| `./deploy.sh scan` | 一次性扫描 |
| `./deploy.sh status` | 查看状态 |

---

## 部署架构

### 开发环境 (macOS)

```
┌─────────────────────────────────┐
│         macOS Development       │
│                                 │
│  ┌─────────────┐  ┌──────────┐ │
│  │ Backend     │  │ Frontend │ │
│  │ :8089       │  │ :3099    │ │
│  └─────────────┘  └──────────┘ │
│                                 │
│  ┌─────────────┐               │
│  │ MySQL       │               │
│  │ :3306       │               │
│  └─────────────┘               │
└─────────────────────────────────┘
```

### 生产环境 (Cloud + Edge)

```
┌─────────────────────────────────────────────────┐
│              Cloud Server (Ubuntu)               │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ NetGuard     │  │ MySQL        │             │
│  │ Server       │  │ Database     │             │
│  │ :8089        │  │ :3306        │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  LLM Service (可选)                       │   │
│  │  - OpenAI API / 本地 LLM                  │   │
│  │  - 设备识别推理                           │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Desktop PC   │ │ ARM Device 1 │ │ ARM Device 2 │
│ Client Agent │ │ Client Agent │ │ Client Agent │
│ Ubuntu/macOS │ │ Ubuntu ARM   │ │ Ubuntu ARM   │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 文件结构

```
netguard/
├── server/                         # 云端服务端
│   ├── app/
│   │   ├── main.py                # FastAPI 入口
│   │   ├── config.py              # 配置管理
│   │   ├── database.py            # 数据库连接
│   │   ├── api/
│   │   │   ├── devices.py         # 设备 API
│   │   │   ├── alerts.py          # 告警 API
│   │   │   ├── sync.py            # 客户端同步
│   │   │   ├── llm.py             # LLM 识别 API
│   │   │   └── system.py          # 系统 API
│   │   ├── models/
│   │   │   ├── device.py          # 设备模型
│   │   │   ├── alert.py           # 告警模型
│   │   │   ├── client.py          # 客户端模型
│   │   │   └── llm_cache.py       # LLM 缓存模型
│   │   └── services/
│   │       ├── identifier.py      # 规则引擎
│   │       ├── vendor_lookup.py   # OUI 查找
│   │       ├── llm_identifier.py  # LLM 识别
│   │       ├── alerter.py         # 告警服务
│   │       └── platform_compat.py # 跨平台兼容
│   ├── data/                      # OUI 数据库
│   ├── config.yaml                # 配置文件
│   ├── requirements.txt           # Python 依赖
│   └── deploy.sh                  # 部署脚本
│
├── client/                         # 客户端 (桌面/ARM)
│   ├── app/
│   │   ├── main.py                # 客户端主程序
│   │   ├── scanner.py             # 本地网络扫描
│   │   ├── reporter.py            # 数据上报
│   │   └── config.py              # 配置管理
│   ├── config/
│   │   └── client.json            # 客户端配置
│   ├── requirements.txt           # Python 依赖
│   └── deploy.sh                  # 部署脚本
│
└── frontend/                       # Web 前端 (可选)
    ├── src/
    │   ├── views/
    │   │   ├── Home.vue           # 仪表盘
    │   │   ├── Devices.vue        # 设备列表
    │   │   ├── Alerts.vue         # 告警列表
    │   │   └── Libraries.vue      # 同步库
    │   └── ...
    └── ...
```

---

## LLM 集成方案

### 方案 1: Cloud API (推荐)

```python
# server/app/services/llm_identifier.py

import openai
from typing import Dict

class LLMIdentifier:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    async def identify(self, features: Dict) -> Dict:
        prompt = self._build_prompt(features)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        return self._parse_response(response.choices[0].message.content)
```

### 方案 2: Local LLM (边缘计算)

```python
# 使用 llama.cpp 或 ollama 运行本地模型

class LocalLLMIdentifier:
    def __init__(self, model_path: str):
        from llama_cpp import Llama
        self.llm = Llama(model_path=model_path, n_ctx=2048)
    
    def identify(self, features: Dict) -> Dict:
        prompt = self._build_prompt(features)
        output = self.llm(prompt, max_tokens=256)
        return self._parse_response(output["choices"][0]["text"])
```

### 方案 3: Hybrid (混合模式)

```python
class HybridIdentifier:
    def __init__(self):
        self.rule_engine = RuleBasedIdentifier()  # 本地规则
        self.llm = LLMIdentifier()                # 云端 LLM
        self.cache = LLMCache()                   # 缓存
    
    async def identify(self, features: Dict) -> Dict:
        # 1. 先用规则引擎快速判断
        rule_result = self.rule_engine.identify(features)
        
        # 2. 如果置信度高，直接返回
        if rule_result["confidence"] > 0.85:
            return rule_result
        
        # 3. 检查缓存
        cache_key = self._get_cache_key(features)
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # 4. 调用 LLM
        llm_result = await self.llm.identify(features)
        
        # 5. 缓存结果
        self.cache.set(cache_key, llm_result)
        
        # 6. 融合结果
        return self._merge_results(rule_result, llm_result)
```

---

## 实施路线

### Phase 1: 基础架构 (当前)
- [x] Server/Client 分离
- [x] 本地网络扫描
- [x] 设备数据上报
- [x] 基础 OUI 查找

### Phase 2: LLM 集成
- [ ] LLM 识别服务
- [ ] Prompt 工程优化
- [ ] 缓存机制
- [ ] 批量识别 API

### Phase 3: 高级功能
- [ ] 异常检测
- [ ] 行为分析
- [ ] 自动告警
- [ ] 报表生成

### Phase 4: 边缘计算
- [ ] ARM 设备优化
- [ ] 本地 LLM 推理
- [ ] 离线模式

---

## 附录: 参考文献

1. Mahmood et al. (2025) "Large Language Models for Real-World IoT Device Identification" [arXiv:2510.13817]
2. IEEE 802-2014: MAC Address Structure and Assignment
3. RFC 2131: DHCP (Dynamic Host Configuration Protocol)
4. RFC 6762: mDNS (Multicast DNS)

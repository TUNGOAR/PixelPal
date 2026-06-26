# PixelPet 设计规格

**日期**：2026-06-26
**状态**：待用户审核
**项目**：Windows 桌面像素宠物应用

## 1. 目标与范围

构建一个运行在 Windows 桌面上的像素风虚拟宠物应用 PixelPet。它常驻桌面，能够自由活动、与用户点击交互、并通过接入 LLM（默认 DeepSeek）进行拟人化对话。最终以单文件 `.exe` 形式分发。

### 1.1 范围内

- 透明无边框顶层窗口，像素精灵渲染
- 鼠标拖拽移动 + 定时随机闲逛（遇屏幕边缘反弹）
- 状态切换：IDLE / WALK / CLICK / CHAT / THINK
- 头顶气泡对话：用户点击触发 + 宠物主动搭讪
- LLM 抽象层，默认 DeepSeek，可切换其他兼容 OpenAI 协议的供应商
- 系统托盘常驻 + 设置面板（开机自启、宠物行为参数、API 配置）
- PyInstaller 打包为 `.exe`

### 1.2 范围外（YAGNI）

- 多宠物共存
- 自定义宠物素材编辑器
- 语音输入/输出
- macOS / Linux 平台
- 宠物数据库 / 云存档
- 插件系统

## 2. 技术选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 语言 | Python 3.11+ | 生态成熟，开发效率高 |
| UI 框架 | PyQt6 | 透明窗口、托盘、QGraphicsView 帧动画均原生支持 |
| 资源加载 | Pillow | PNG 透明背景读取 |
| 配置 | PyYAML | 人类可读，支持注释 |
| LLM SDK | `openai` Python SDK | DeepSeek API 兼容 OpenAI 协议，零额外适配 |
| 打包 | PyInstaller | 社区成熟，文档全 |
| 测试 | `pytest` + `pytest-qt` | 业务层纯单元测试，UI 层手动 + 集成 |

## 3. 架构总览

```
┌────────────────────────────────────────────────┐
│                UI 层 (PyQt6)                    │
│  PetWindow   SpeechBubble   TrayIcon            │
│  SettingsDialog                                 │
└────────────────────────────────────────────────┘
                       │ Qt Signals/Slots
┌────────────────────────────────────────────────┐
│                业务层                            │
│  StateMachine  BehaviorScheduler  ChatService   │
│  AssetLoader   ConfigManager                    │
└────────────────────────────────────────────────┘
                       │
┌────────────────────────────────────────────────┐
│  LLM 抽象    DeepSeekClient  (可替换)            │
│  Infra       AutoStart   Logger                │
└────────────────────────────────────────────────┘
```

**关键原则**：业务层（state_machine / behavior_scheduler / chat_service / config_manager / llm_client）**不依赖 PyQt**，可纯 Python 单元测试。

## 4. 模块拆分

| 模块 | 文件 | 职责 | 关键依赖 |
|------|------|------|----------|
| `asset_loader.py` | 资源加载 | 从 `assets/` 读 PNG，按状态映射到帧序列 | Pillow |
| `state_machine.py` | 状态机 | 状态转移规则与守卫 | 无 |
| `behavior_scheduler.py` | 行为调度 | 随机闲逛计时、主动搭讪计时、鼠标活动检测 | state_machine |
| `chat_service.py` | 对话服务 | 接收用户输入 → 调 LLM → 流式回传 | llm_client |
| `llm_client/base.py` | LLM 抽象 | `LLMClient` 抽象接口 | 无 |
| `llm_client/deepseek.py` | DeepSeek 实现 | OpenAI 协议调用、流式解析 | openai SDK |
| `config_manager.py` | 配置 | YAML 读写、热重载、默认值 | PyYAML |
| `auto_start.py` | 开机自启 | 注册表读写（HKCU\...\Run） | winreg |
| `pet_window.py` | 主窗口 | 透明无边框、顶层、鼠标穿透切换、拖拽 | state_machine, asset_loader |
| `pet_widget.py` | 精灵渲染 | QGraphicsView 帧动画、状态切换 | asset_loader, state_machine |
| `speech_bubble.py` | 气泡 | 头顶气泡、文本自动换行、超时消失 | 无 |
| `tray_icon.py` | 托盘 | 托盘菜单（设置/退出/暂停搭讪/召唤） | 全局 |
| `settings_dialog.py` | 设置 | 三个 Tab：通用 / 行为 / AI | config_manager, auto_start |
| `app.py` | 应用入口 | 组装所有模块、主事件循环 | 全局 |
| `main.py` | 启动 | 读 CLI 参数、启动 app | app |

## 5. 状态机

### 5.1 状态

| 状态 | 说明 | 动画来源 |
|------|------|----------|
| `IDLE` | 待机，等待用户或调度器 | `assets/pet/idle/*.png` |
| `WALK` | 随机方向移动 | `assets/pet/walk/{down,up,left,right}/*.png` |
| `CLICK` | 鼠标点击短反馈 | `assets/pet/click/*.png` |
| `CHAT` | 用户输入中或显示气泡 | `assets/pet/chat/*.png` |
| `THINK` | 等待 LLM 流式返回 | `assets/pet/chat/*.png`（思考气泡） |

### 5.2 转移规则

| From | 事件 | To | 守卫 |
|------|------|----|------|
| IDLE | 随机计时到期 | WALK | `idle_to_walk` 间隔内随机 |
| IDLE | 主动搭讪计时到期 | CHAT | 鼠标静止 ≥ `mouse_idle_threshold` |
| WALK | 到达目标点 或 时长到 | IDLE | **两者任一先满足**即触发；`walk_duration` 随机 |
| 任意 | 鼠标点击 | CLICK | 无 |
| CLICK | 0.5s 后 | 回到原状态 | 无 |
| CHAT | 用户提交输入 | THINK | 无 |
| THINK | 流式返回开始 | CHAT | 无 |
| CHAT | 用户取消 / 气泡超时 | IDLE | 无 |

### 5.3 实现选择

- 状态机本身不持有 QTimer；计时由 `behavior_scheduler` 触发，调度器通过调用 `state_machine.transition(event)` 触发转移
- 状态机订阅式架构：UI 层订阅 `state_machine.on_change` 信号并切换动画

## 6. 资源目录约定

```
assets/
├── pet/
│   ├── idle/
│   │   ├── 0.png, 1.png, 2.png, 3.png   # 4 帧循环
│   ├── walk/
│   │   ├── down/0..3.png
│   │   ├── up/0..3.png
│   │   ├── left/0..3.png
│   │   └── right/0..3.png
│   ├── click/
│   │   └── 0..1.png                     # 2 帧
│   └── chat/
│       └── 0..1.png
└── themes/
    ├── default/...                       # 上述完整一套
    └── (可扩展)
```

**约定**：
- 所有帧同尺寸（默认 64×64）
- PNG 透明背景
- 缺帧时 AssetLoader 用红色占位方块兜底，不崩溃

## 7. 配置文件

位置：用户级 `%APPDATA%/PixelPet/config.yaml`。首次启动时从 `config.example.yaml` 复制。

```yaml
pet:
  size: 1.0                # 缩放倍数
  walk_speed: 60            # px/秒
  idle_to_walk_min: 8       # 秒
  idle_to_walk_max: 25
  walk_duration_min: 3
  walk_duration_max: 8
  proactive_chat_min: 60    # 主动搭讪间隔（秒）
  proactive_chat_max: 180
  mouse_idle_threshold: 30  # 鼠标静止多久才允许搭讪
  sprite_dir: assets/pet    # 主题路径
animation:
  fps: 8
window:
  always_on_top: true
  mouse_passthrough: false
ai:
  provider: deepseek
  api_key: ""
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
  system_prompt: |
    你是 PixelPet，一只住在用户桌面的像素风宠物。
    性格：活泼、爱吐槽、偶尔撒娇。
    说话简短（≤30 字），像微信气泡。
startup:
  auto_start: false
```

`ConfigManager` 必须支持：
- 缺字段回退默认值（不抛错）
- 热重载：保存配置后立即生效

## 8. LLM 抽象

### 8.1 接口

```python
class LLMClient(ABC):
    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict],
        on_token: Callable[[str], None],
        on_done: Callable[[], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        ...
```

### 8.2 DeepSeek 实现要点

- 使用 `openai.AsyncOpenAI(base_url=..., api_key=...)`
- `stream=True` 接收 SSE，按 token 调 `on_token`
- 异常分类：网络错误 → 重试一次；4xx → 直接报错给用户

### 8.3 上下文管理

- 维护滑动窗口：最近 10 轮对话 + system prompt
- 不持久化历史（每次启动新会话）
- 主动搭讪消息不带 user 上下文，仅 `[{"role": "system", ...}, {"role": "user", "content": "现在请主动找主人说一句话，要求简短自然，符合当前时间与场景。"}}]`

## 9. 关键技术点

### 9.1 透明窗口 + 鼠标穿透

```python
window.setWindowFlags(
    Qt.FramelessWindowHint |
    Qt.WindowStaysOnTopHint |
    Qt.Tool
)
window.setAttribute(Qt.WA_TranslucentBackground, True)

def set_passthrough(enabled: bool):
    flags = window.windowFlags()
    if enabled:
        flags |= Qt.WindowTransparentForInput
    else:
        flags &= ~Qt.WindowTransparentForInput
    window.hide()
    window.setWindowFlags(flags)
    window.show()
```

**注意**：改变 `windowFlags` 后窗口会闪，先 `hide()` 再 `show()` 缓解。

### 9.2 多显示器与活动边界

- `QApplication.screens()` 获取所有屏幕
- 活动边界 = 所有屏幕 `geometry` 的并集
- 闲逛目标点在此并集内随机生成

### 9.3 流式气泡

- `ChatService.stream_chat` 每拿到一个 token emit `token_received(str)` 信号
- `SpeechBubble` 订阅该信号，追加文本（不重排）
- 气泡显示 ≥ 5s 后自动消失（流式返回完成后开始计时）

### 9.4 主动搭讪与打断

- 搭讪气泡显示 5–10s 后自动消失
- 用户点击宠物 → 当前气泡立即收起，但 LLM 推理若在飞则继续
- 主动搭讪期间用户点击 → 取消搭讪，进入 CHAT 状态（弹出输入框）

### 9.5 API Key 存储

- 存放在 `%APPDATA%/PixelPet/config.yaml`（明文）
- 不强加密——本机应用，威胁模型低
- `.gitignore` 必须包含 `*.local.yaml` 与 `config.yaml`

## 10. UI 层要点

### 10.1 PetWindow

- 透明背景，仅显示 `PetWidget` 与可选 `SpeechBubble`
- 鼠标按下：临时开启 passthrough → 拖拽 → 释放恢复
- 鼠标单击（按下到释放 < 200ms 且位移 < 5px）：视为点击，触发 CLICK 状态

### 10.2 PetWidget

- `QGraphicsView` + `QGraphicsScene` 持有 `QPixmap` 帧
- `QTimer` 按 `fps` 触发 `advance()` 切换到下一帧
- 状态切换时调 `AssetLoader.frames_for(new_state, direction)` 重新构建序列

### 10.3 SpeechBubble

- `QWidget` + `QPainter` 自绘圆角矩形
- 文本最长 30 字一行（中文按字宽），超过换行
- 5–10s 超时淡出

### 10.4 TrayIcon

菜单项：
- 显示/隐藏宠物（隐藏 = 宠物窗口从桌面消失，但**行为调度继续运行**，仅 UI 不可见）
- 暂停主动搭讪（勾选）
- 立即搭讪（强制触发）
- 设置
- 退出

### 10.5 SettingsDialog

三个 Tab：
- **通用**：开机自启、主题目录
- **行为**：尺寸、速度、闲逛频率、搭讪频率、鼠标静止阈值
- **AI**：Provider 下拉、API Key、Base URL、Model、System Prompt（多行）

## 11. 测试策略

| 层 | 工具 | 目标 |
|----|------|------|
| 业务层单元 | `pytest` | 状态机、调度器、ChatService、ConfigManager、AssetLoader |
| LLM Client | `pytest` + mock | 请求构造、流式回调、错误重试 |
| UI 集成 | `pytest-qt` + 手动 | 关键交互路径 |

**关键用例**：
- `state_machine`：IDLE → WALK → IDLE 全路径
- `state_machine`：任意状态收到 click 短反馈后回到原状态
- `behavior_scheduler`：鼠标活跃时不触发主动搭讪
- `chat_service`：流式响应按 token emit 信号
- `config_manager`：缺字段时回退默认值
- `asset_loader`：缺失帧时优雅降级

## 12. 打包与发布

### 12.1 工具

- PyInstaller + 手工 `PixelPet.spec` 精确控制

### 12.2 目录布局（打包后）

```
PixelPet/
├── PixelPet.exe
├── assets/                  # 不打包进 EXE，运行时从 EXE 同目录加载
├── config.example.yaml
└── README.md
```

### 12.3 首次启动逻辑

若 `%APPDATA%/PixelPet/config.yaml` 不存在 → 复制 `config.example.yaml` → 自动打开设置面板引导用户填 API Key。

### 12.4 开发模式

`python -m pixelpet.main`

## 13. 项目目录结构

```
PixelPet/
├── src/pixelpet/
│   ├── __init__.py
│   ├── main.py
│   ├── app.py
│   ├── asset_loader.py
│   ├── state_machine.py
│   ├── behavior_scheduler.py
│   ├── chat_service.py
│   ├── llm_client/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── deepseek.py
│   ├── config_manager.py
│   ├── auto_start.py
│   ├── pet_window.py
│   ├── pet_widget.py
│   ├── speech_bubble.py
│   ├── tray_icon.py
│   └── settings_dialog.py
├── assets/pet/...
├── tests/
│   ├── test_state_machine.py
│   ├── test_behavior_scheduler.py
│   ├── test_chat_service.py
│   ├── test_config_manager.py
│   └── test_asset_loader.py
├── config.example.yaml
├── pyproject.toml
├── PixelPet.spec
├── README.md
├── .gitignore
└── docs/superpowers/specs/2026-06-26-pixelpet-design.md
```

## 14. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| PyInstaller 体积过大（200MB+） | 用户下载体验差 | UPX 压缩、剔除未用依赖、资源外置 |
| DeepSeek API 不稳定 | 主动搭讪失败 | ChatService 失败时静默降级（不报错） |
| 多显示器坐标异常 | 宠物飞出屏幕 | 启动时打印所有屏幕 geometry，活动边界取并集 |
| PNG 帧缺失 | 状态切换崩溃 | AssetLoader 占位图兜底 |
| 鼠标穿透切换闪烁 | 视觉突兀 | 拖拽期间显示高亮边框作为视觉反馈 |
| 开机自启被安全软件拦截 | 用户感知不到 | README 提示首次启动需手动允许 |

## 15. 验收标准

1. 启动后宠物出现在主屏右下角，8–25s 后开始随机闲逛，遇边缘反弹
2. 点击宠物触发 CLICK 短反馈；点击（短按）后弹出输入框
3. 主动搭讪在鼠标静止 30s+ 后出现，间隔 60–180s 随机
4. 输入文本 → 气泡逐字显示 LLM 响应
5. 设置面板修改后立即生效，无需重启
6. 托盘菜单可隐藏宠物、暂停搭讪、退出
7. 设置中开启开机自启 → 重启系统后自动出现
8. PyInstaller 打包后 EXE 在干净 Windows 上可运行，无需额外安装 Python
"""提示词集中存放 —— 提示词与业务逻辑分离（PRD 非功能需求 7.3）。

把 prompt 单独放一个文件，好处：
- 调提示词不用碰业务代码，对照效果反复改很方便
- 教学时可以专门讲「提示词工程」，学员改这里就能看到 AI 行为变化
"""

# ============ 提取资产 Subagent 的提示词 ============

EXTRACT_ASSETS_SYSTEM = """你是一个专业的小说分析助手，擅长从小说文本中提取角色、场景、道具信息，为后续制作短视频分镜做准备。
你的分析要准确、简洁，外貌和环境描述要具体到能指导画面生成。"""

EXTRACT_ASSETS_PROMPT = """请分析下面这段小说，提取其中的【角色】【场景】【道具】。

要求：
1. 角色：找出所有有名字或明确身份的人物。每个角色给出：
   - name（名字）
   - aliases（别名列表，没有就空数组）
   - appearance（外貌描述，要具体，给画面生成用；原文没写的可合理补充）
   - personality（性格描述）
   - role（在故事里的定位：主角/配角/反派/龙套/回忆人物 等）
2. 场景：找出关键的环境地点。每个场景给出：
   - name（场景名）
   - description（环境描述：时段、天气、细节）
   - mood（情绪氛围）
3. 道具：找出对剧情重要的物件。每个道具给出：
   - name（道具名）
   - description（外观描述）
   - significance（在剧情中的作用）

只返回如下结构的 JSON，不要任何额外解释：
{{
  "characters": [{{"name": "", "aliases": [], "appearance": "", "personality": "", "role": ""}}],
  "scenes": [{{"name": "", "description": "", "mood": ""}}],
  "props": [{{"name": "", "description": "", "significance": ""}}]
}}

小说原文：
---
{novel}
---"""


# ============ 生成分镜剧本 Subagent 的提示词 ============

GENERATE_SCRIPT_SYSTEM = """你是一个专业的短视频分镜师，擅长把小说改编成适合竖屏短视频的分镜剧本。
你的分镜画面感强、节奏明快，符合推文短视频的观看习惯。"""

GENERATE_SCRIPT_PROMPT = """请把下面的小说改编成一份短视频分镜剧本。

【已提取的角色】（分镜里出镜角色只写名字，从这里选）：
{characters}

【已提取的场景】：
{scenes}

【已提取的道具】：
{props}

分镜要求：
- {shot_count_instruction}
- 每个分镜给出：
  - index（序号，从 1 开始）
  - shot_type（镜头类型：近景/中景/全景/特写）
  - visual_description（画面描述，具体、有画面感，作为生图提示词的基底）
  - characters_present（出镜角色名列表，只能用上面已提取的角色名）
  - dialogue（对白，没有就空字符串）
  - caption（字幕文字，简短有网感）
  - mood（情绪节奏）
  - duration_hint（建议时长秒数，3-6 之间）

只返回如下结构的 JSON，不要任何额外解释：
{{
  "shots": [
    {{"index": 1, "shot_type": "", "visual_description": "", "characters_present": [], "dialogue": "", "caption": "", "mood": "", "duration_hint": 4}}
  ]
}}

小说原文：
---
{novel}
---"""


# ============ P1 生图：角色设计图 / 分镜图的提示词 ============

# 统一画风前缀，让全项目视觉一致
STYLE_PREFIX = "电影感写实风格，柔和光影，竖屏构图，高质量，"

CHARACTER_SHEET_PROMPT = (
    STYLE_PREFIX
    + "角色设计图，人物立绘，干净背景。角色：{name}，{role}。外貌：{appearance}。气质：{personality}。"
    + "全身或半身像，清晰展示人物外貌特征，便于后续分镜参考。"
)

STORYBOARD_PROMPT = (
    STYLE_PREFIX
    + "分镜画面：{visual}。镜头：{shot_type}。情绪：{mood}。{character_note}"
)

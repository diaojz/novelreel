"""数据模型 —— 整个产品的「数据结构地基」。

设计原则（来自 ArcReel 的范式，PRD 第 6 节）：
- 角色 / 场景 / 道具的完整定义**只存在 Project 里一处**，分镜剧本里只引用名字。
  这样改一处就全局生效，不会出现「第 1 镜和第 5 镜里同一个角色长得不一样」。
- 用 Pydantic 做数据校验：字段写错、类型不对会立刻报错，而不是悄悄出问题。

这个文件是教学项目的第 2 节课内容：先把数据结构设计好，后面所有功能都围着它转。
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


def _now() -> str:
    """统一的时间戳（UTC ISO 格式字符串）。"""
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    """生成一个短项目 ID（取 UUID 前 8 位，够用且好读）。"""
    return uuid4().hex[:8]


class ProjectStatus(str, Enum):
    """项目的整体状态。编排器靠它判断「现在该做哪一步」。

    状态是单向推进的：
    初始化 → 提取中 → 资产已提取 → 生成中 → 剧本已生成 → 完成
    任意一步出错则进入 error。
    """

    INITIALIZED = "initialized"          # 刚创建，只有原文
    EXTRACTING = "extracting"            # 正在提取角色/场景/道具
    ASSETS_EXTRACTED = "assets_extracted"  # 资产提取完毕，等待审核/生成
    GENERATING = "generating"            # 正在生成分镜剧本
    SCRIPT_GENERATED = "script_generated"  # 分镜剧本已生成
    DONE = "done"                        # 全流程完成
    ERROR = "error"                      # 出错了


class Character(BaseModel):
    """角色。一个角色的完整定义只在这里出现一次。"""

    name: str = Field(description="角色名字，如「沈师傅」")
    aliases: list[str] = Field(default_factory=list, description="别名列表")
    appearance: str = Field(default="", description="外貌描述，给后续生图用")
    personality: str = Field(default="", description="性格描述")
    role: str = Field(default="配角", description="主角 / 配角 / 反派 / 龙套 等")


class Scene(BaseModel):
    """场景。标志性环境，跨分镜保持一致。"""

    name: str = Field(description="场景名，如「残灯巷旧钟表铺」")
    description: str = Field(default="", description="环境描述：时段、天气、细节")
    mood: str = Field(default="", description="情绪氛围：紧张 / 怀旧 / 轻松 等")


class Prop(BaseModel):
    """道具。关键物件，跨分镜保持一致。"""

    name: str = Field(description="道具名，如「黄铜怀表」")
    description: str = Field(default="", description="外观描述")
    significance: str = Field(default="", description="在剧情中的作用")


class Shot(BaseModel):
    """单个分镜。注意：characters_present 只存名字，不重复定义角色。"""

    index: int = Field(description="分镜序号，从 1 起")
    shot_type: str = Field(default="中景", description="镜头类型：近景 / 中景 / 全景 / 特写")
    visual_description: str = Field(description="画面描述，作为文生图 prompt 的基底")
    characters_present: list[str] = Field(
        default_factory=list, description="出镜角色名列表（只引用名字）"
    )
    dialogue: str = Field(default="", description="对白，可为空")
    caption: str = Field(default="", description="字幕文字")
    mood: str = Field(default="", description="情绪节奏")
    duration_hint: int = Field(default=4, description="建议时长（秒），给视频生成参考")


class Script(BaseModel):
    """分镜剧本：一组分镜。落盘为 scripts/<project_id>.json。"""

    project_id: str
    shots: list[Shot] = Field(default_factory=list)


class Project(BaseModel):
    """项目 —— 核心状态文件，落盘为 project.json。

    编排器和前端都靠读这个文件判断「进行到哪一步、下一步做什么」。
    这就是 PRD 说的「数据状态驱动工作流」：状态全在数据里，不在内存里，
    所以任意一步崩溃后重新跑，都能从断点续上。
    """

    id: str = Field(default_factory=_new_id)
    title: str = Field(default="未命名项目")
    novel_path: str = Field(default="", description="小说原文的文件路径（相对项目目录）")
    status: ProjectStatus = Field(default=ProjectStatus.INITIALIZED)
    assets_confirmed: bool = Field(default=False, description="用户是否已确认资产")
    expected_shots: int | None = Field(
        default=None, description="用户期望的分镜数；None 表示由 AI 自定"
    )

    characters: list[Character] = Field(default_factory=list)
    scenes: list[Scene] = Field(default_factory=list)
    props: list[Prop] = Field(default_factory=list)

    script_path: str = Field(default="", description="分镜剧本 JSON 的路径")
    error_message: str = Field(default="", description="出错时的友好提示")

    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)

    def touch(self) -> None:
        """更新「最后修改时间」。每次改动后调一下。"""
        self.updated_at = _now()

    @property
    def has_assets(self) -> bool:
        """是否已经提取出资产（三类里任一非空就算有）。"""
        return bool(self.characters or self.scenes or self.props)

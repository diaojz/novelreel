# NovelReel — 设计规范（DESIGN.md）

> 版本：v1.1 · 日期：2026-06-05
> 上游来源：PRD.md（v0.1）
> 交互档位：L1（MVP 静态优雅）
> 实现约束：单个 HTML 文件 + 原生 JS，不依赖任何前端框架或构建工具

---

## ⚠️ v1.1 视觉方向更新（以高保真原型为准）

经产品负责人确认，**视觉方向从「暖米杂志风」改为「小云雀同款现代 AI 工作台风」**。下文第 2 节起的暖米色板/衬线大标题为 v1.0 历史记录，**实际实现以 `web/prototype.html` 高保真原型为准**：

- **浅灰白底**（`#f4f4f5`）+ **左侧白色圆角侧边栏** + **黑色主操作按钮**（不是橙色）+ 大圆角白卡 + Tab 切换
- **紫色 `#7c5cff` 做点缀**（示例 chip / 进行中状态 / 标题高亮），不是主色
- **角色/场景/道具/分镜卡一律用真实图片**（`web/assets/portraits/` 人物肖像 + `web/assets/scenes/` 场景图），**禁止用 SVG 小头像占位**
- 字体：正文 Noto Sans SC，标题点缀用 Playfair Display 斜体（「小说 *Agent*」那个斜体衬线）

**关于图片占位**：当前原型的人物肖像来自 Unsplash（可商用，仅占位演示）。**真实产品 P1 阶段，角色图应由文生图模型按小说描述生成**（对应 ArcReel「先固化角色 sheet 图、处处引用」的一致性方案）。MVP 是文本闭环，前端展示这些图只为演示形态。

---

## 1. 设计基调

**氛围关键词**：克制、编辑感、暖米、沉稳、易读

**一句话定调**：像一本正经的工作笔记本——不花哨，但拿起来就知道怎么用。

**设计决策理由**：
- NovelReel 是「工具型产品」，用户目标是「快速拿到分镜 JSON」，视觉要降低认知负担，不抢主角。
- 面向内容创作者（书号运营、短视频团队），他们惯用飞书/Notion 这类克制工具，偏暖色的编辑感比冷白色科技风更亲切。
- 面向零基础学员（课堂教学），界面逻辑必须一眼明确：当前在哪一步、下一步该做什么——流程清晰度优先于装饰。
- MVP 是单个 HTML 文件，不上框架，设计必须能用朴素 CSS 实现，不依赖复杂动效库。

---

## 2. 色彩系统

```css
:root {
  /* 背景与表面 */
  --color-bg:          #ece7de;   /* rgb: 236,231,222 — 暖米，整页底色 */
  --color-surface:     #f5f1eb;   /* rgb: 245,241,235 — 卡片/面板背景，比底色浅一阶 */
  --color-surface-alt: #e4ddd2;   /* rgb: 228,221,210 — 次级区块背景，比底色深一阶 */

  /* 文字 */
  --color-text:        #1a1714;   /* rgb: 26,23,20   — 主文字，近黑暖棕 */
  --color-text-muted:  #6b6058;   /* rgb: 107,96,88  — 次要文字、标签、提示 */
  --color-text-dim:    #a89e94;   /* rgb: 168,158,148 — 更淡的辅助文字、占位符 */

  /* 边框与分割线 */
  --color-border:      #d5cdc3;   /* rgb: 213,205,195 — 普通边框 */
  --color-border-strong: #b8ada0; /* rgb: 184,173,160 — 强调边框、聚焦环 */

  /* 主强调色（橙棕，呼应创作/故事感） */
  --color-accent:      #c4622d;   /* rgb: 196,98,45  — 主按钮、链接、激活状态 */
  --color-accent-hover:#a84e22;   /* rgb: 168,78,34  — 悬停深化 */
  --color-accent-light:#f2e0d4;   /* rgb: 242,224,212 — 强调色的浅底，用于标签/chip */

  /* 语义色 */
  --color-success:     #3d7a4a;   /* rgb: 61,122,74  — 完成/成功状态 */
  --color-success-bg:  #daf0df;   /* rgb: 218,240,223 */
  --color-warning:     #b07d18;   /* rgb: 176,125,24  — 等待/审核状态 */
  --color-warning-bg:  #fdf3d0;   /* rgb: 253,243,208 */
  --color-danger:      #c0392b;   /* rgb: 192,57,43   — 错误状态 */
  --color-danger-bg:   #fde8e6;   /* rgb: 253,232,230 */
  --color-info:        #2563a8;   /* rgb: 37,99,168   — 提示/信息 */
  --color-info-bg:     #dceeff;   /* rgb: 220,238,255 */

  /* 进行中的脉冲色（轮询动效用） */
  --color-processing:  #7b5ea7;   /* rgb: 123,94,167  — 紫色调，区别于成功/警告 */
  --color-processing-bg: #ede8f5; /* rgb: 237,232,245 */
}
```

**主色选择理由**：`#c4622d` 是烧橙/砖红色，兼顾「故事感/墨迹感」与「操作引导」，在暖米底色上对比度足够（约 4.8:1），满足 WCAG AA 标准。紫色 `--color-processing` 专用于「进行中」状态，与成功（绿）、警告（黄）、错误（红）形成四色语义区分，不产生歧义。

---

## 3. 字体系统

```css
/* 引入 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  /* 字族 */
  --font-serif:  'Noto Serif SC', 'Source Han Serif SC', Georgia, serif;
  --font-sans:   'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono:   'JetBrains Mono', 'Cascadia Code', Consolas, monospace;

  /* 字号阶梯（基准 16px） */
  --text-xs:   12px;   /* 角标、时间戳、极小提示 */
  --text-sm:   14px;   /* 辅助文字、标签文字、次要信息 */
  --text-base: 16px;   /* 正文、输入框、按钮 */
  --text-md:   18px;   /* 卡片标题、小节标题 */
  --text-lg:   22px;   /* 区域标题（H2 级别） */
  --text-xl:   28px;   /* 页面主标题（H1） */

  /* 行高 */
  --leading-tight:  1.3;   /* 标题 */
  --leading-normal: 1.6;   /* 正文 */
  --leading-loose:  1.8;   /* 小说原文等长文本区域 */

  /* 字重 */
  --weight-normal: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
}
```

**字体用途说明：**

| 位置 | 字族 | 字号 | 字重 | 行高 |
|------|------|------|------|------|
| 页面主标题「NovelReel」 | serif | 28px | 700 | 1.3 |
| 区域标题（输入区/结果区） | serif | 22px | 600 | 1.3 |
| 卡片标题（角色名/分镜序号） | sans | 18px | 600 | 1.4 |
| 正文（描述、对白、字幕） | sans | 16px | 400 | 1.6 |
| 辅助标签/说明文字 | sans | 14px | 400 | 1.5 |
| JSON 代码展示 | mono | 13px | 400 | 1.7 |
| 时间戳/角标 | sans | 12px | 400 | 1.4 |

**衬线标题的选择理由**：Noto Serif SC 给页面带来「编辑/出版物」气质，与暖米底色搭配自然，正文用无衬线 Noto Sans SC 保持可读性，两者都覆盖 CJK 字符，不会出现中文回退到系统字体的破版问题。

---

## 4. 间距系统

基于 4px 基准单位，所有间距都是 4 的倍数：

```css
:root {
  --space-1:  4px;   /* xs — 图标与文字的紧凑间距 */
  --space-2:  8px;   /* sm — 同一元素内部的内边距 */
  --space-3: 12px;   /* md-sm — 卡片内小间距 */
  --space-4: 16px;   /* md — 标准内边距、行间距 */
  --space-5: 20px;   /* md-lg — 卡片内边距 */
  --space-6: 24px;   /* lg — 区域内分组间距 */
  --space-8: 32px;   /* xl — 区域间分隔 */
  --space-10: 40px;  /* 2xl — 大区块上下留白 */
  --space-12: 48px;  /* 3xl — 页面顶部留白 */
}
```

---

## 5. 圆角与阴影

```css
:root {
  /* 圆角 */
  --radius-sm:  4px;    /* 标签 chip、小徽章 */
  --radius-md:  8px;    /* 按钮、输入框、小卡片 */
  --radius-lg: 12px;    /* 大卡片、面板 */
  --radius-xl: 16px;    /* 弹层/模态框（MVP 暂不用） */

  /* 阴影（暖棕调，不用冷灰） */
  --shadow-sm:  0 1px 3px rgba(26,23,20,0.08);   /* 卡片默认 */
  --shadow-md:  0 4px 12px rgba(26,23,20,0.10);  /* 卡片悬停 */
  --shadow-lg:  0 8px 24px rgba(26,23,20,0.12);  /* 面板/结果区 */
}
```

---

## 6. 核心组件样式

### 6.1 按钮

**主按钮（Primary）— 用于「开始处理」「确认资产」「跳过审核」等核心操作**

```
默认：
  background: var(--color-accent)        #c4622d
  color: #fff
  padding: 10px 24px
  border-radius: var(--radius-md)        8px
  font: 16px / var(--weight-medium)
  border: none
  cursor: pointer
  transition: background 150ms ease-out, transform 100ms ease-out

悬停：
  background: var(--color-accent-hover)  #a84e22
  transform: translateY(-1px)

激活（按下）：
  transform: translateY(0px)
  background: #8e4120

禁用：
  background: var(--color-border)        #d5cdc3
  color: var(--color-text-dim)           #a89e94
  cursor: not-allowed
  transform: none
```

**次级按钮（Secondary）— 用于「下载 JSON」「复制 JSON」等辅助操作**

```
默认：
  background: transparent
  color: var(--color-accent)
  border: 1.5px solid var(--color-accent)
  padding: 9px 20px
  border-radius: var(--radius-md)
  font: 16px / var(--weight-medium)

悬停：
  background: var(--color-accent-light)  #f2e0d4
  border-color: var(--color-accent-hover)

禁用：
  color: var(--color-text-dim)
  border-color: var(--color-border)
  background: transparent
  cursor: not-allowed
```

**幽灵按钮（Ghost）— 用于「跳过」「重新处理」等低优先级操作**

```
默认：
  background: transparent
  color: var(--color-text-muted)
  border: none
  padding: 9px 16px
  text-decoration: underline dotted
  text-underline-offset: 3px

悬停：
  color: var(--color-text)
  text-decoration-style: solid
```

---

### 6.2 文本输入框

**小说文本框（主输入区）**

```
默认：
  width: 100%
  min-height: 200px
  max-height: 400px
  resize: vertical
  padding: var(--space-4)              16px
  border: 1.5px solid var(--color-border)    #d5cdc3
  border-radius: var(--radius-lg)      12px
  background: #fff
  font: var(--font-sans) / 16px / var(--leading-loose)   行高 1.8
  color: var(--color-text)
  outline: none
  transition: border-color 150ms ease-out

聚焦：
  border-color: var(--color-accent)    #c4622d
  box-shadow: 0 0 0 3px var(--color-accent-light)   #f2e0d4

占位符：
  color: var(--color-text-dim)         #a89e94
  font-style: italic

错误态：
  border-color: var(--color-danger)    #c0392b
  box-shadow: 0 0 0 3px var(--color-danger-bg)
```

**数字输入框（期望分镜数）**

```
默认：
  width: 80px
  padding: 8px 12px
  border: 1.5px solid var(--color-border)
  border-radius: var(--radius-md)      8px
  background: #fff
  font: 16px / var(--font-sans)
  text-align: center

聚焦：同大文本框聚焦态
```

**单行可编辑字段（资产审核区的内联编辑）**

```
默认：
  display: inline
  border: none
  border-bottom: 1px dashed var(--color-border)
  background: transparent
  padding: 2px 4px
  font: inherit

聚焦：
  border-bottom: 1.5px solid var(--color-accent)
  outline: none
  background: var(--color-accent-light)
  border-radius: 3px 3px 0 0
```

---

### 6.3 卡片

所有卡片共享基础样式：

```css
.card {
  background: var(--color-surface);    /* #f5f1eb */
  border: 1px solid var(--color-border); /* #d5cdc3 */
  border-radius: var(--radius-lg);     /* 12px */
  padding: var(--space-5);             /* 20px */
  box-shadow: var(--shadow-sm);
  transition: box-shadow 150ms ease-out;
}

.card:hover {
  box-shadow: var(--shadow-md);
}
```

**角色卡（Character Card）**

```
结构：
  ┌─────────────────────────────────┐
  │  [类型标签 chip: 主角/配角/反派]   │
  │  角色名（18px / semibold）        │
  │  别名（14px / muted）             │
  ├─────────────────────────────────┤
  │  外貌：[可编辑文本，16px]          │
  │  性格：[可编辑文本，16px]          │
  └─────────────────────────────────┘

尺寸：min-width: 240px；在网格中 flex-grow: 1
```

**场景卡（Scene Card）**

```
结构：
  ┌─────────────────────────────────┐
  │  [chip: 场景]                   │
  │  场景名（18px / semibold）        │
  ├─────────────────────────────────┤
  │  描述：[可编辑文本]               │
  │  情绪：[可编辑文本]               │
  └─────────────────────────────────┘
```

**道具卡（Prop Card）**

```
结构：
  ┌─────────────────────────────────┐
  │  [chip: 道具]                   │
  │  道具名（18px / semibold）        │
  ├─────────────────────────────────┤
  │  外观：[可编辑文本]               │
  │  作用：[可编辑文本]               │
  └─────────────────────────────────┘
```

**分镜卡（Shot Card）**

```
结构：
  ┌─────────────────────────────────┐
  │  #01   [chip: 近景]  [chip: 3s]  │
  │  情绪：[mood 文字]                │
  ├─────────────────────────────────┤
  │  画面描述                         │
  │  [16px 正文，leading-normal]      │
  ├─────────────────────────────────┤
  │  出镜角色：萧炎、美杜莎            │
  │  对白："..."                      │
  │  字幕：[字幕文字]                  │
  └─────────────────────────────────┘

强调样式：左侧 4px 竖条，颜色 var(--color-accent)
border-left: 4px solid var(--color-accent);
border-radius: 0 12px 12px 0;   /* 左侧直角，右侧圆角 */
```

---

### 6.4 状态条 / 进度提示

用于「处理中」阶段，横跨页面宽度的状态横幅：

```
容器：
  background: var(--color-processing-bg)   #ede8f5
  border: 1px solid var(--color-processing) 的 30% 透明度
  border-radius: var(--radius-lg)
  padding: 16px 20px
  display: flex
  align-items: center
  gap: 12px

内容：
  左侧 — 旋转加载动画（见 6.6 节）
  中间 — 阶段文案（16px / semibold / --color-processing）
  右侧 — 小字说明（14px / muted）
```

**进度步骤指示器（顶部 stepper，3 步）**

```
步骤文案：①提取资产  ②审核确认  ③生成分镜

样式（每步）：
  waiting:
    background: var(--color-surface-alt)
    color: var(--color-text-dim)
    border: 1px solid var(--color-border)

  active（当前步）：
    background: var(--color-processing-bg)
    color: var(--color-processing)
    border: 1.5px solid var(--color-processing)
    font-weight: 600

  done（已完成步）：
    background: var(--color-success-bg)
    color: var(--color-success)
    border: 1px solid var(--color-success) 的 40% 透明度

步骤间连接线：
  1px solid var(--color-border)；done 段变为 var(--color-success) 的 50% 透明度
```

---

### 6.5 标签 Chip

```css
.chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-sm);   /* 4px */
  font-size: var(--text-sm);          /* 14px */
  font-weight: var(--weight-medium);
  white-space: nowrap;
}

/* 角色类型 */
.chip--protagonist { background: #dff2e8; color: #2e7d52; }  /* 主角 */
.chip--supporting  { background: var(--color-accent-light); color: var(--color-accent); }  /* 配角 */
.chip--antagonist  { background: #fde8e6; color: var(--color-danger); }  /* 反派 */
.chip--extra       { background: var(--color-surface-alt); color: var(--color-text-muted); }  /* 龙套 */

/* 资产类型 */
.chip--scene { background: #dceeff; color: var(--color-info); }   /* 场景 */
.chip--prop  { background: #fdf3d0; color: var(--color-warning); } /* 道具 */

/* 镜头类型 */
.chip--shot { background: var(--color-surface-alt); color: var(--color-text); }

/* 时长 */
.chip--duration { background: transparent; color: var(--color-text-muted); border: 1px solid var(--color-border); }
```

---

### 6.6 加载动画（CSS-only，无 JS 依赖）

```css
/* 旋转圆圈 */
.spinner {
  width: 20px;
  height: 20px;
  border: 2.5px solid var(--color-border);
  border-top-color: var(--color-processing);
  border-radius: 50%;
  animation: spin 700ms linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 脉冲点（3个点依次跳动，用于「处理中」文案后） */
.pulse-dots span {
  display: inline-block;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-processing);
  margin: 0 2px;
  animation: pulse-dot 1.2s ease-in-out infinite;
}
.pulse-dots span:nth-child(2) { animation-delay: 0.2s; }
.pulse-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse-dot {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* 降级 */
@media (prefers-reduced-motion: reduce) {
  .spinner { animation: none; border-top-color: var(--color-processing); }
  .pulse-dots span { animation: none; opacity: 1; }
}
```

---

## 7. 页面结构与信息架构

整个产品是**一个单页面**，按使用流程从上到下分 5 个区（区域随状态显示/隐藏）：

```
┌─────────────────────────────────────────┐
│  ZONE 0: 顶部导航栏（常驻）               │
├─────────────────────────────────────────┤
│  ZONE 1: 输入区（初始态显示，处理后折叠）  │
├─────────────────────────────────────────┤
│  ZONE 2: 步骤进度条（有任务时显示）        │
├─────────────────────────────────────────┤
│  ZONE 3: 资产审核区（assets_extracted 后）│
├─────────────────────────────────────────┤
│  ZONE 4: 分镜结果区（script_generated 后）│
└─────────────────────────────────────────┘
```

**区域切换逻辑**（前端通过 JS 控制 display 属性）：

| 状态 | ZONE 1 | ZONE 2 | ZONE 3 | ZONE 4 |
|------|--------|--------|--------|--------|
| 初始（空态） | 展开显示 | 隐藏 | 隐藏 | 隐藏 |
| 处理中 | 折叠（只显 header） | 显示（step 1 active） | 隐藏 | 隐藏 |
| 资产提取完 | 折叠 | 显示（step 2 active） | 显示 | 隐藏 |
| 生成中 | 折叠 | 显示（step 3 active） | 显示（只读） | 隐藏 |
| 完成 | 折叠 | 显示（全部 done） | 显示（只读） | 显示 |
| 出错 | 展开（可重试） | 显示（出错步高亮红） | 按已完成情况显示 | 按已完成情况显示 |

---

## 8. ASCII 线框图

### 8.1 初始空态

```
┌────────────────────────────────────────────────────────────┐
│  NovelReel                                      v0.1  [?]  │  ← ZONE 0
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                                                            │
│  把小说粘进来，AI 帮你拆分镜                                  │  ← ZONE 1
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  在这里粘贴小说文本（4000 字以内）…                    │  │
│  │                                                      │  │
│  │  （文本框高度 200px，可拖拽调整）                       │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  期望分镜数（选填）：[   5   ]   留空则由 AI 自行判断          │
│                                                            │
│  ┌──────────────┐                                          │
│  │  开始处理    │   ← 主按钮（disabled 时灰色）               │
│  └──────────────┘                                          │
│                                                            │
│  ℹ  字数统计：0 / 4000                                      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

### 8.2 处理中态（提取资产阶段）

```
┌────────────────────────────────────────────────────────────┐
│  NovelReel                                      v0.1  [?]  │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  ▼ 原文（点击展开）   1240 字  [重新输入]                    │  ← ZONE 1 折叠态
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│   ①提取资产 ●─────────── ②审核确认 ○─────────── ③生成分镜 ○ │  ← ZONE 2 步骤条
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  ◌  正在提取角色 · 场景 · 道具 •••                           │  ← 状态横幅
│     通常需要 10–30 秒，请稍等                                │
└────────────────────────────────────────────────────────────┘
```

---

### 8.3 资产审核态

```
┌────────────────────────────────────────────────────────────┐
│  NovelReel                                      v0.1  [?]  │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  ▼ 原文（点击展开）   1240 字  [重新输入]                    │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│   ①提取资产 ✓──────────── ②审核确认 ●──────────── ③生成分镜 ○ │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  提取到 3 个角色 · 2 个场景 · 4 个道具                       │  ← ZONE 3 标题行
│  可以修改下方内容，确认后开始生成分镜                          │
│                                                            │
│  角色                                                       │
│  ┌───────────────────┐  ┌───────────────────┐             │
│  │ [主角] 萧炎         │  │ [反派] 云山         │             │
│  │ 外貌：黑发青衫…     │  │ 外貌：苍白面孔…     │             │
│  │ 性格：执拗、坚韧     │  │ 性格：阴沉、狡诈    │             │
│  └───────────────────┘  └───────────────────┘             │
│                                                            │
│  场景                                                       │
│  ┌───────────────────┐                                     │
│  │ [场景] 云岚宗门口    │                                     │
│  │ 描述：黄昏时分，…   │                                     │
│  │ 情绪：紧张         │                                     │
│  └───────────────────┘                                     │
│                                                            │
│  道具                                                       │
│  ┌───────────────────┐  ┌───────────────────┐             │
│  │ [道具] 玄重尺        │  │ [道具] 斗气护盾     │             │
│  │ 外观：黑铁…         │  │ 外观：蓝光流动…    │             │
│  └───────────────────┘  └───────────────────┘             │
│                                                            │
│  ┌──────────────┐    ┌──────────────────────────┐          │
│  │ 确认，开始生成 │    │ 跳过，直接用这些资产生成     │          │
│  └──────────────┘    └──────────────────────────┘          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

### 8.4 分镜结果态

```
┌────────────────────────────────────────────────────────────┐
│  NovelReel                                      v0.1  [?]  │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  ▼ 原文（点击展开）   1240 字  [重新输入]                    │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│   ①提取资产 ✓──────────── ②审核确认 ✓──────────── ③生成分镜 ✓ │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  ✓ 分镜剧本已生成   共 5 个分镜                              │  ← ZONE 3 只读
│  （资产概要折叠显示）                                         │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  分镜剧本                               ┌──────┐ ┌──────┐  │  ← ZONE 4
│                                        │复制JSON│ │下载JSON│  │
│                                        └──────┘ └──────┘  │
│                                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │ #01  [近景]  [3s]                   情绪：紧张       │    │
│  │ 画面：萧炎站在云岚宗门口，仰望高大的牌匾…             │    │
│  │ 出镜：萧炎                                          │    │
│  │ 对白："我萧炎，今日来还债。"                          │    │
│  │ 字幕：仰望云岚宗牌匾                                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │ #02  [全景]  [4s]                   情绪：对峙       │    │
│  │ 画面：云岚宗弟子列队，面对孤身萧炎…                   │    │
│  │ 出镜：萧炎、云山、云岚弟子（群像）                    │    │
│  │ 对白：（无）                                         │    │
│  │ 字幕：孤身赴会，百人对峙                              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                            │
│  … （后续分镜）                                             │
│                                                            │
│  ── 查看原始 JSON ──                                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │ {                                                  │    │
│  │   "project_id": "abc-123",                         │    │  ← 代码块，等宽字体
│  │   "scenes": [...]                                  │    │
│  │ }                                                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

### 8.5 错误态

```
┌────────────────────────────────────────────────────────────┐
│  NovelReel                                      v0.1  [?]  │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  ▼ 原文（点击展开）   1240 字  [重新输入]                    │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│   ①提取资产 ✗──────────── ②审核确认 ○──────────── ③生成分镜 ○ │
│   （出错步骤显示红色 X，后续步骤变灰）                         │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  ✕ 提取资产时出错                                           │  ← 错误横幅
│  可能原因：LLM API 超时，或输入文本过短（少于 50 字）         │
│  详细信息：Connection timeout after 30s                     │
│                                                            │
│  ┌────────────────┐                                        │
│  │ 重试此步骤     │                                        │
│  └────────────────┘                                        │
└────────────────────────────────────────────────────────────┘
```

---

## 9. 布局与响应式

### 9.1 容器

```css
.container {
  max-width: 860px;
  margin: 0 auto;
  padding: 0 var(--space-6);   /* 0 24px */
}

/* 桌面（>1024px）：保持 860px 居中 */
/* 平板（640-1024px）：padding 收为 16px，保持单列 */
/* 移动（<640px）：padding 收为 12px，卡片网格变单列 */
```

### 9.2 断点

```css
/* 平板 */
@media (max-width: 1024px) {
  .container { padding: 0 var(--space-4); }
  .card-grid { grid-template-columns: repeat(2, 1fr); }
}

/* 移动 */
@media (max-width: 640px) {
  .container { padding: 0 var(--space-3); }
  .card-grid { grid-template-columns: 1fr; }
  .step-label { display: none; }   /* 步骤条只显示序号，隐藏文字 */
  .btn-group { flex-direction: column; }
}
```

### 9.3 资产卡片网格

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);   /* 16px */
}
```

### 9.4 顶部导航栏

```css
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  padding: 12px var(--space-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-logo {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.navbar-version {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
}
```

---

## 10. 关键交互规则

### 10.1 轮询状态的视觉反馈

前端通过 `setInterval` 每 2 秒调一次 `GET /projects/{id}/status`：

| 后端返回的 status | 前端动作 |
|-----------------|---------|
| `extracting` | 显示旋转 spinner + 文案「正在提取角色·场景·道具」|
| `assets_extracted` / `confirming` | 停止 spinner；展示资产审核区；步骤条第 2 步高亮 |
| `generating` | 重启 spinner + 文案「正在生成分镜剧本」；审核区变只读 |
| `script_generated` / `done` | 停止 spinner；展示分镜结果区；步骤条全部变勾 |
| `error` | 停止轮询；展示错误横幅 + 错误信息 |

**阶段文案完整列表**（写死在前端，按状态切换）：

```
extracting  → "正在分析小说，提取角色·场景·道具…"
confirming  → "AI 已提取完毕，等待你确认资产…"
generating  → "资产已确认，正在生成分镜剧本…"
done        → "分镜剧本生成完成！"
error       → "出错了，查看下方错误信息"
```

### 10.2 输入区字数校验

- 实时统计字数（每次 `input` 事件更新）
- 超过 4000 字：字数显示变红，「开始处理」按钮 disabled + 提示「超出 4000 字上限」
- 少于 50 字：按钮 disabled + 提示「文本太短，请粘贴完整段落」

### 10.3 资产审核区编辑

- 每个文字字段默认是只读文本，鼠标悬停时显示铅笔图标（`cursor: text`）
- 点击后变为 `contenteditable` 或 `<input>` 行内编辑模式
- 失去焦点时自动保存到本地（不调后端，只改 JS 内存中的数据结构）
- 「确认」按钮点击时，把当前内存中的资产一次性 POST 到后端

### 10.4 JSON 展示区

- 默认显示格式化的卡片视图（分镜列表）
- 底部「查看原始 JSON」可展开一个 `<pre>` 代码块，背景 `#1a1714`，文字 `#e8e4df`，等宽字体
- 「复制 JSON」点击后按钮文案变为「已复制！」持续 2 秒，再恢复
- 「下载 JSON」触发 `<a download>` 下载，文件名为 `novelreel-{日期}-script.json`

### 10.5 空态 / 占位文案

| 位置 | 占位文案 |
|------|---------|
| 文本框 | 「在这里粘贴你的小说文本，支持 4000 字以内的中文小说片段。例如：把《斗破苍穹》的某一章节复制进来，AI 会自动找出所有角色、场景和道具，再拆成分镜剧本。」|
| 期望分镜数 | placeholder="AI 自定" |
| 资产区（等待中） | （不显示，整区块隐藏） |
| 分镜区（等待中） | （不显示，整区块隐藏） |

### 10.6 「重新输入」流程

- 点「重新输入」：弹出内联确认文案「这会清除当前进度，确定吗？[确定] [取消]」
- 确认后：清空文本框内容，隐藏进度条/审核区/结果区，重置状态变量
- 不刷新页面

---

## 11. 全局视觉规则（Do / Don't）

**Do（该做）：**
- 用 CSS 变量表达所有颜色，零硬编码
- 每个可交互元素都有 hover + focus 可见态（focus 环用 `outline: 2px solid var(--color-accent); outline-offset: 2px`）
- 状态切换用 CSS `transition` 做平滑过渡，200ms 内完成
- JSON 展示区用 `overflow-x: auto` + `white-space: pre` 处理长行
- 所有图标用内联 SVG 或 Unicode 符号（✓ ✕ ◌ ▼），不引入图标包
- 错误提示必须包含「可能原因 + 建议操作」，不能只显示技术报错字符串

**Don't（别做）：**
- 不用纯蓝色 `#0000ff` 或纯红色 `#ff0000`，语义色必须走色板
- 不给正常流程加 modal/弹窗——所有操作就地完成，不打断焦点
- 不做悬浮工具栏、侧边抽屉等复杂组件——MVP 的信息量不需要
- 不给审核区加「全部删除」等破坏性操作——学员容易误触
- 不在移动端隐藏核心操作按钮——所有按钮在 320px 宽度下都必须完整显示
- 不用 `placeholder` 当标签用——每个输入框上方必须有独立的 `<label>` 或说明文字

---

## 12. 实现交接

```yaml
design_status: ready
theme: 暖米编辑感，克制工具风
interaction_level: L1
color_system: 见第 2 节 CSS 变量，全部 :root 级别
font_system: Noto Serif SC（标题） + Noto Sans SC（正文） + JetBrains Mono（JSON）
core_components: [button-primary, button-secondary, button-ghost, textarea, input-number, card-character, card-scene, card-prop, card-shot, stepper, status-banner, chip, spinner, code-block]
breakpoints: mobile-640 / tablet-1024 / desktop
motion_libs: []   # L1，纯 CSS transition + keyframe，无外部库
language_default: zh-CN
mvp_scope: [F01 创建项目, F02 提取角色, F03 提取场景道具, F04 资产查看编辑, F05 生成分镜, F06 JSON 展示下载, F07 状态轮询反馈]
single_file: true   # 前端是单个 HTML，CSS 和 JS 都内联
polling_interval: 2000ms
```

---

## 13. 给 Claude Code 的实现指令（MVP 落地）

### 实现纪律

1. **只实现 PRD 中 P0 的 F01–F07**，F08 及以后不做
2. **前端是单个 `index.html`**，`<style>` 和 `<script>` 都内联，零外部依赖
3. **所有颜色走 CSS 变量**，复制本文第 2 节 `:root` 块直接用，不改也不加硬编码色值
4. **轮询用 `setInterval(2000)`**，检测到终止状态（done / error）立刻 `clearInterval`
5. **状态切换用 CSS class**（如 `.zone--hidden`），不用 `display: none` 直接写在 JS 里
6. **按钮禁用状态必须设 `disabled` 属性**，不要只改样式而不设属性
7. **所有 `fetch` 调用都要有 `try/catch`**，错误统一走「显示错误横幅」逻辑
8. **JSON 代码块用 `JSON.stringify(data, null, 2)` 格式化**，放进 `<pre><code>` 标签
9. **「复制 JSON」用 `navigator.clipboard.writeText()`**，iOS Safari 回退用 `document.execCommand('copy')`
10. **「下载 JSON」用动态创建 `<a>` + `URL.createObjectURL(Blob)`**，不依赖任何库

### 反模式（看到就停下来问）

- 想引入 axios / jQuery / lodash → 不要，原生 `fetch` + `JSON` 就够
- 想做 SPA 路由 / 多页面 → MVP 是单页，不需要
- 想加登录/鉴权页 → PRD 明确不做，停下来问
- 想加项目列表页 → PRD Q4 决策是 MVP 不做，停下来问
- 想把 CSS 抽成独立文件 → 单 HTML 文件约束，都内联
```

"""生成演示项目 —— 一键造出几个「已拆好分镜」的推文爆款向项目。

为什么用脚本而不是直接放数据文件：projects/ 是运行时用户数据，已被
.gitignore 忽略，不入库。所以把「演示内容」写进这个脚本（脚本入库），
谁需要演示数据就跑一次：

    uv run python scripts/seed_demo_projects.py

它会在 projects/ 下造出几个完整项目（含角色/场景/道具 + 分镜剧本），
打开网页「我的项目」就能直接看。不调 LLM、不花钱。
"""

from __future__ import annotations

from novelreel.core.models import (
    Character,
    Project,
    ProjectStatus,
    Prop,
    Scene,
    Script,
    Shot,
)
from novelreel.core.project_manager import ProjectManager

# ========== 演示项目内容（推文爆款向）==========

DEMOS = [
    {
        "id": "demo-reborn",
        "title": "重生归来：豪门弃女的复仇",
        "novel": (
            "苏暖重生回到了被赶出苏家的那个雨夜。上一世，她被继母陷害、被未婚夫背叛，"
            "最后惨死在异国他乡。这一世，她站在苏家别墅的大门口，撑着伞，冷冷地看着那个"
            "正得意洋洋的继妹苏曼。「这次，轮到你们了。」她转身走进雨里，眼神坚定。"
            "三个月后，她带着一家市值百亿的公司强势回归，亲手撕碎了所有曾经看不起她的人的脸。"
        ),
        "characters": [
            Character(name="苏暖", aliases=["暖暖"], appearance="二十三岁，长发及腰，眼神锐利坚定，重生后气场全开", personality="隐忍、果决、深谋远虑", role="主角"),
            Character(name="苏曼", aliases=[], appearance="苏家继妹，妆容精致，神情骄纵", personality="虚荣、狠毒、爱算计", role="反派"),
            Character(name="继母", aliases=["林氏"], appearance="四十岁，雍容却刻薄", personality="表面慈爱、心机深沉", role="反派"),
        ],
        "scenes": [
            Scene(name="苏家别墅大门", description="暴雨夜，豪宅门口灯火通明", mood="压抑、暗涌"),
            Scene(name="商业发布会现场", description="高端会场，聚光灯下", mood="扬眉吐气"),
        ],
        "props": [
            Prop(name="黑色长伞", description="苏暖重生那夜撑的伞", significance="重生与隐忍的象征"),
            Prop(name="百亿公司股权书", description="烫金封面的法律文件", significance="复仇的底牌"),
        ],
        "shots": [
            Shot(index=1, shot_type="全景", visual_description="暴雨夜，苏暖撑着黑伞站在苏家别墅大门口，仰望灯火通明的豪宅，雨水顺着伞沿滑落。", characters_present=["苏暖"], dialogue="", caption="重生回到被赶出家门那一夜", mood="压抑", duration_hint=4),
            Shot(index=2, shot_type="近景", visual_description="苏暖冷冷地注视着门内得意的苏曼，眼神由痛楚转为坚定。", characters_present=["苏暖", "苏曼"], dialogue="这次，轮到你们了。", caption="她不再是任人宰割的弃女", mood="决绝", duration_hint=4),
            Shot(index=3, shot_type="特写", visual_description="苏暖手中紧攥的百亿公司股权书，烫金封面在雨中泛着冷光。", characters_present=["苏暖"], dialogue="", caption="三个月，她要让所有人付出代价", mood="隐忍", duration_hint=3),
            Shot(index=4, shot_type="全景", visual_description="商业发布会现场，聚光灯下苏暖一袭红裙强势登场，台下众人震惊。", characters_present=["苏暖"], dialogue="", caption="百亿总裁，强势归来", mood="扬眉吐气", duration_hint=5),
            Shot(index=5, shot_type="近景", visual_description="台下继母与苏曼脸色惨白，苏暖在台上微微一笑，尽显掌控。", characters_present=["苏暖", "苏曼", "继母"], dialogue="苏家，我回来了。", caption="这一世，换我赢", mood="痛快", duration_hint=5),
        ],
    },
    {
        "id": "demo-soninlaw",
        "title": "都市赘婿：扮猪吃老虎",
        "novel": (
            "三年前，林川入赘江家，受尽白眼。江家人都以为他是个一无是处的废物，连保姆都敢对他呼来喝去。"
            "直到这天，江家最大的客户在宴会上当众下跪，恭敬地喊了林川一声「会长」。满座哗然。"
            "原来这个被全家看不起的赘婿，竟是隐藏在幕后、掌控半座城市经济命脉的神秘商业巨头。"
            "江家人这才惊觉，自己怠慢了一尊真神。"
        ),
        "characters": [
            Character(name="林川", aliases=["废物赘婿"], appearance="三十岁，平日穿着朴素，眼神深藏锋芒", personality="隐忍、低调、深不可测", role="主角"),
            Character(name="江父", aliases=["江董"], appearance="五十多岁，平日趾高气扬", personality="势利、傲慢", role="配角"),
            Character(name="神秘客户", aliases=["陈总"], appearance="西装革履的商界大佬", personality="恭敬、识时务", role="配角"),
        ],
        "scenes": [
            Scene(name="江家豪华宴会厅", description="水晶吊灯，宾客云集", mood="表面光鲜、暗藏惊雷"),
            Scene(name="江家客厅", description="日常起居，赘婿受冷落", mood="压抑、轻视"),
        ],
        "props": [
            Prop(name="一杯被泼的红酒", description="宴会上有人故意泼向林川", significance="羞辱的顶点，反转的引信"),
            Prop(name="会长徽章", description="象征商业巨头身份的金色徽章", significance="揭示真实身份"),
        ],
        "shots": [
            Shot(index=1, shot_type="中景", visual_description="江家宴会厅，林川端着托盘被宾客无视，一杯红酒被故意泼在他身上。", characters_present=["林川"], dialogue="", caption="入赘三年，受尽白眼", mood="压抑", duration_hint=4),
            Shot(index=2, shot_type="近景", visual_description="江父在一旁冷笑，对林川的狼狈视若无睹。", characters_present=["江父", "林川"], dialogue="一个废物，也配站在这里？", caption="全家都当他是废物", mood="轻蔑", duration_hint=3),
            Shot(index=3, shot_type="全景", visual_description="神秘客户陈总大步走入宴会厅，目光锁定林川，突然当众下跪。", characters_present=["神秘客户", "林川"], dialogue="会长，您怎么亲自来了！", caption="满座哗然", mood="震撼", duration_hint=5),
            Shot(index=4, shot_type="特写", visual_description="林川从口袋取出金色会长徽章，灯光下熠熠生辉。", characters_present=["林川"], dialogue="", caption="原来他才是真正的幕后巨头", mood="反转", duration_hint=4),
            Shot(index=5, shot_type="近景", visual_description="江父瞠目结舌，红酒杯从手中滑落，林川平静地整理衣袖。", characters_present=["林川", "江父"], dialogue="怠慢之处，江董多包涵。", caption="扮猪吃老虎，藏了三年", mood="畅快", duration_hint=5),
        ],
    },
    {
        "id": "demo-watchmaker",
        "title": "残灯巷的修表人",
        "novel": (
            "残灯巷尽头有一家旧钟表铺，主人姓沈，街坊都叫他沈师傅，修表三十年。这天傍晚下着小雨，"
            "一个叫林小满的姑娘撑着伞冲进铺子，手里攥着一只停摆的黄铜怀表，说是奶奶留下的唯一念想。"
            "沈师傅借着台灯昏黄的光，一点点把表修好。怀表重新滴答走动，他却盯着表背那行小字久久出神——"
            "「赠阿沈，民国廿三年，云。」原来这只表，正是他年轻时亲手送出去的定情信物。"
        ),
        "characters": [
            Character(name="沈师傅", aliases=["沈修表"], appearance="六十多岁，背微驼，圆框老花镜，靛蓝粗布褂子", personality="沉默寡言、专注、藏着旧情", role="主角"),
            Character(name="林小满", aliases=["小满"], appearance="二十出头，花店学徒，撑伞少女", personality="真诚、念旧、情绪外露", role="配角"),
            Character(name="云", aliases=[], appearance="仅在表背刻字中出现，未正面描写", personality="沈师傅年轻时的定情之人", role="回忆人物"),
        ],
        "scenes": [
            Scene(name="残灯巷旧钟表铺", description="巷尾旧铺，褪色齿轮招牌，昏黄台灯", mood="安静、怀旧"),
            Scene(name="雨夜青石板巷", description="小雨，青石板泛水光，铺外的夜色", mood="湿润、克制的伤感"),
        ],
        "props": [
            Prop(name="黄铜怀表", description="缠枝莲表壳，背刻「赠阿沈，民国廿三年，云」", significance="串起两代人的定情信物"),
            Prop(name="修表工具", description="镊子、放大镜、极细钢丝、台灯", significance="承载「修复」这一核心动作"),
        ],
        "shots": [
            Shot(index=1, shot_type="全景", visual_description="雨夜，残灯巷尽头的旧钟表铺亮着一盏昏黄台灯，镜头缓缓推近店门。", characters_present=["沈师傅"], dialogue="", caption="残灯巷尽头，有一家修表三十年的铺子", mood="怀旧", duration_hint=4),
            Shot(index=2, shot_type="中景", visual_description="林小满撑伞冲进铺子，紧攥着一只停摆的黄铜怀表，神情焦急。", characters_present=["林小满"], dialogue="师傅，这表……能修好吗？", caption="奶奶留下的唯一念想", mood="急切", duration_hint=3),
            Shot(index=3, shot_type="特写", visual_description="台灯下，沈师傅用镊子撬开怀表后盖，放大镜里游丝纤细。", characters_present=["沈师傅"], dialogue="", caption="再坏的表，到他手里都能复活", mood="专注", duration_hint=5),
            Shot(index=4, shot_type="近景", visual_description="怀表重新滴答走动，沈师傅的目光落在表背刻字上，手微微颤抖。", characters_present=["沈师傅", "林小满"], dialogue="赠阿沈，民国廿三年，云。", caption="那行字，他等了三十年", mood="动容", duration_hint=4),
            Shot(index=5, shot_type="全景", visual_description="雨停了，镜头拉远，老人与少女的身影定格在昏黄灯光中。", characters_present=["沈师傅", "林小满"], dialogue="", caption="有些等待，本身就是答案", mood="释然", duration_hint=5),
        ],
    },
]


def seed(pm: ProjectManager) -> list[str]:
    """造出所有演示项目，返回项目 id 列表。已存在则覆盖。"""
    ids = []
    for d in DEMOS:
        # 用固定 id，方便重复运行时覆盖而不是不停新增
        project = Project(id=d["id"], title=d["title"], status=ProjectStatus.DONE, assets_confirmed=True)
        pdir = pm.project_dir(project.id)
        (pdir / "source").mkdir(parents=True, exist_ok=True)
        (pdir / "scripts").mkdir(parents=True, exist_ok=True)
        (pdir / "source" / "novel.txt").write_text(d["novel"], encoding="utf-8")
        project.novel_path = "source/novel.txt"
        project.characters = d["characters"]
        project.scenes = d["scenes"]
        project.props = d["props"]

        script = Script(project_id=project.id, shots=d["shots"])
        pm.save_script(project, script)
        pm.save(project)
        ids.append(project.id)
        print(f"  ✓ {project.title}（{len(d['shots'])} 个分镜）→ projects/{project.id}/")
    return ids


def main() -> None:
    pm = ProjectManager()
    print("生成演示项目…")
    ids = seed(pm)
    print(f"\n完成，共 {len(ids)} 个演示项目。启动服务后在「我的项目」里可见。")


if __name__ == "__main__":
    main()

"""
Wan2.7 FoodShot Factory - CLI 入口

用法：
    python scripts/generate.py --config my_sku.json --out-dir ./output

输入：
    一份 JSON 配置（见 scripts/sample_input.json）
输出：
    主图 N 张（由 need_main_images 控制）
    主图动态视频（可选，需在 config 中启用 generate_video）
"""
import argparse
import json
import os
import sys
from pathlib import Path

# 让脚本可以直接运行（不需要 python -m）
sys.path.insert(0, str(Path(__file__).parent))

from wan_client import WanClient
from prompts import (
    get_bans,
    get_strategy,
    render_appetite,
    check_copy,
)


# =====================================================================
# 三层锁定 Prompt 组装
# =====================================================================

def build_prompt(cfg):
    """
    构建结构化 prompt（三层锁定机制的第二、三层）。

    第一层（多图参考锚定）由调用方通过 refs 参数传入参考图实现。
    第二层（结构化 prompt）在本函数中按固定结构组装。
    第三层（绝对禁项）由本函数末尾挂载。
    """
    name = cfg["product_name"]
    category = cfg["category"]
    platform = cfg["platform"]
    flavor = cfg.get("flavor", "")
    packaging_strength = cfg.get("packaging_strength", "medium")

    strategy = get_strategy(platform, packaging_strength)
    appetite_text = render_appetite(cfg.get("appetite_params", {}))
    selling_points = cfg.get("selling_points", [])
    bans = get_bans(category, flavor)

    prompt = f"""任务：为食品电商平台生成可上架主图
平台：{platform}
类目：{category}
商品：{name}
口味：{flavor}

主视觉策略：{strategy}
包装显示强度：{packaging_strength}

食欲参数控制：
{appetite_text if appetite_text else '(使用默认食欲参数)'}

核心卖点：{' / '.join(selling_points) if selling_points else '(无)'}
光影：45 度侧顶光，暖色调
构图：食物主体占画面 55-65%，包装占 15-20%
文案：{('预留上方 / 下方 20% 低信息区给文案叠加' if cfg.get('text_mode') == 'overlay' else '画面中不包含任何中文大标题文字（文字由后期叠加）')}

【绝对禁项】：
""" + "\n".join(f"- {b}" for b in bans)

    return prompt


# =====================================================================
# 主流程
# =====================================================================

def generate(config_path, out_dir):
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    os.makedirs(out_dir, exist_ok=True)

    # 1. 文案合规预检
    if cfg.get("selling_points"):
        copy_text = " ".join(cfg["selling_points"])
        violations = check_copy(copy_text, cfg.get("flavor", ""))
        if violations and not cfg.get("allow_violations", False):
            print("⚠️ 文案合规检查发现违规：")
            for v in violations:
                print(f"   - {v}")
            print("提示：修改卖点文案后重试，或在 config 中设置 allow_violations=true 强制继续")
            sys.exit(1)

    # 2. Prompt 组装（三层锁定）
    prompt = build_prompt(cfg)
    print("=" * 60)
    print("PROMPT（三层锁定机制）")
    print("=" * 60)
    print(prompt)
    print("=" * 60)

    # 3. 参考图收集（多图参考锚定 · 第一层锁定）
    refs = []
    for key in [
        "package_reference",
        "style_reference",
        "raw_material_reference",
        "action_reference",
    ]:
        p = cfg.get(key)
        if p and os.path.exists(p):
            refs.append(p)
            print(f"✓ Reference: {key} = {p}")
        elif p:
            print(f"⚠ Reference file not found: {p}")

    # 4. 调 Wan2.7 生图
    client = WanClient()
    count = cfg.get("need_main_images", 5)
    size = cfg.get("size", "1024*1024")
    print(f"\n→ 生成 {count} 张主图（尺寸 {size}）...\n")

    saved_images = []
    for i in range(count):
        print(f"[{i+1}/{count}] 调用 Wan2.7 文生图...")
        url = client.t2i(prompt, refs=refs, size=size)
        out_path = os.path.join(out_dir, f"main_{i+1}.png")
        client.download(url, out_path)
        saved_images.append(out_path)
        print(f"    ✓ {out_path}")

    # 5. 可选：图生视频
    if cfg.get("generate_video") and saved_images:
        video_prompt = cfg.get(
            "video_prompt",
            "食材热气升腾，卤汁轻微翻滚冒泡，暖色光线，真实慢炖场景",
        )
        seed_img = saved_images[0]
        print(f"\n→ 生成动态视频（基于 {seed_img}）...")
        video_url = client.i2v(seed_img, video_prompt)
        video_out = os.path.join(out_dir, "main_dynamic.mp4")
        client.download(video_url, video_out)
        print(f"    ✓ {video_out}")

    print(f"\n✅ 全部完成！输出目录：{out_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Wan2.7 FoodShot Factory - 食品电商主图一键生成",
    )
    parser.add_argument("--config", required=True, help="输入配置 JSON（见 sample_input.json）")
    parser.add_argument("--out-dir", default="./output", help="输出目录（默认 ./output）")
    args = parser.parse_args()

    generate(args.config, args.out_dir)


if __name__ == "__main__":
    main()

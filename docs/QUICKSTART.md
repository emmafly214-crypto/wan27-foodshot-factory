# 5 分钟快速上手

## 1. 环境要求
- Python 3.10+
- 阿里云 DashScope API Key（申请：https://dashscope.console.aliyun.com/apiKey）

**无其他依赖**（纯 stdlib 实现）。

## 2. 克隆项目
```bash
git clone https://github.com/emmafly214-crypto/wan27-foodshot-factory.git
cd wan27-foodshot-factory
```

## 3. 配置 API Key
```bash
# Linux / Mac
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Windows PowerShell
$env:DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Windows CMD
set DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 4. 准备输入配置
复制示例配置修改：
```bash
cp scripts/sample_input.json my_sku.json
```

编辑 `my_sku.json`，关键字段：

| 字段 | 说明 | 示例值 |
|------|------|-------|
| `product_name` | 商品名 | `"酱好美湘式卤水调味料"` |
| `category` | 品类（决定用哪套绝对禁项） | `"luwei"` / `"noodle"` / `"snack"` / `"bakery"` |
| `platform` | 目标电商平台 | `"tmall"` / `"pdd"` / `"douyin"` / `"xhs"` |
| `flavor` | 口味（用于文案冲突检测） | `"麻辣"` / `"不辣"` / `"甜辣"` |
| `packaging_strength` | 包装显示强度 | `"strong"` / `"medium"` / `"weak"` |
| `package_reference` | 包装图路径（多图参考锚定关键） | `"./images/my_pack.jpg"` |
| `style_reference` | 成品风格参考图 | `"./images/style.jpg"` |
| `raw_material_reference` | 原料图（如生鸡爪，锁定食材解剖结构） | `"./images/raw.jpg"` |
| `selling_points` | 核心卖点 3-5 条（文案安全白名单） | `["18 种香辛料", "加水即卤"]` |
| `appetite_params` | 食欲 6 参数（挂汁/油亮/堆叠/配料/热气/拉丝） | 见下方 |
| `need_main_images` | 主图生成数量 | `5` |
| `generate_video` | 是否生成动态视频（图生视频） | `false` / `true` |

### 食欲 6 参数示例
```json
"appetite_params": {
  "挂汁感": "高",
  "油亮感": "高",
  "堆叠感": "高",
  "配料感": "中",
  "热气感": "中",
  "拉丝感": "低"
}
```
每个参数可选：`"高"` / `"中"` / `"低"`。

## 5. 运行生成

```bash
python scripts/generate.py --config my_sku.json --out-dir ./output
```

终端输出：
```
============================================================
PROMPT（三层锁定机制）
============================================================
任务：为食品电商平台生成可上架主图
平台：tmall
类目：luwei
...（完整 prompt 展示）
============================================================
✓ Reference: package_reference = ./images/my_pack.jpg
✓ Reference: style_reference = ./images/style.jpg
✓ Reference: raw_material_reference = ./images/raw.jpg

→ 生成 5 张主图（尺寸 1024*1024）...

[1/5] 调用 Wan2.7 文生图...
    ✓ ./output/main_1.png
[2/5] 调用 Wan2.7 文生图...
    ✓ ./output/main_2.png
...

✅ 全部完成！输出目录：./output
```

## 6. 进阶：生成动态视频

在 config 中设置：
```json
"generate_video": true,
"video_prompt": "砂锅中卤汁咕嘟咕嘟冒泡文火慢炖，热气升腾..."
```

会额外输出一条 5 秒的 `main_dynamic.mp4`（基于 main_1.png 做图生视频）。

## 常见问题

**Q: 没传参考图可以生成吗？**
A: 可以，但会跳过"多图参考锚定"（第一层锁定），畸变率会明显升高。**强烈建议至少传 `package_reference`**。

**Q: 文案合规检查报错怎么办？**
A: 默认拦截促销词（如"买一送一"）和口味冲突词（如"不辣"产品配"爆辣"文案）。修改 `selling_points` 后重试，或在 config 中设置 `"allow_violations": true` 跳过检查。

**Q: 如何扩展新品类？**
A: 编辑 `scripts/prompts.py` 的 `CATEGORY_BANS` 字典，新增一个品类 key 和对应的禁项列表即可。

**Q: Wan2.7 image 和 wanx i2v 是什么关系？**
A: 本项目文生图使用 `wan2.7-image-pro`（Wan2.7 最新），图生视频使用 `wanx2.1-i2v-plus`（Wan2.1 视频模型，当前 DashScope 最成熟的 I2V 选项）。

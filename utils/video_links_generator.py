import json
from pathlib import Path
import unicodedata
import os

VOLUME_PREFIX = "/Volumes/PRIVATE_COLLECTION/"
MOUNT_PREFIX = "/mnt/nas/"

# JSON 路径（假设放在当前目录）
json_path = Path("TYINGART_VID_LATEST.json")

# 输出目录（软链放这里）
output_dir = Path("/Volumes/PRIVATE_COLLECTION/jellyfin_links/videos")
output_dir.mkdir(parents=True, exist_ok=True)

# 加载 JSON 数据
with json_path.open(encoding="utf-8") as f:
    data = json.load(f)

# 仅保留 type 为 video 的条目
videos = [v for k, v in data.items()]

print(f"共找到 {len(videos)} 个视频")

import os

for entry in videos:
    code = entry.get("code")
    title = entry.get("title")
    # Normalize Unicode for code and title
    code = unicodedata.normalize("NFC", code)
    title = unicodedata.normalize("NFC", title or "")
    raw_path = entry.get("path")
    check_path = Path(raw_path) if raw_path else None

    # 统一软链指向 Raspberry Pi 可识别路径
    video_path = raw_path.replace(VOLUME_PREFIX, MOUNT_PREFIX) if raw_path else None

    poster = entry.get("poster")

    if not video_path:
        print(f"跳过无效条目: {entry}")
        continue

    base_name = code

    dir_name = f"{code} - {title}".strip()
    entry_dir = output_dir / dir_name
    entry_dir.mkdir(parents=True, exist_ok=True)

    # === 删除旧软链接文件（.mp4 / .avi / .mov / .mkv） ===
    for ext in [".mp4", ".avi", ".mov", ".mkv"]:
        old_link = entry_dir / f"{base_name}{ext}"
        if old_link.exists() and old_link.is_symlink():
            old_link.unlink()
            print(f"🧹 删除旧软链接: {old_link.name}")

    # === 视频 .strm 文件 ===
    video_target = Path(video_path)
    strm_path = entry_dir / f"{base_name}.strm"
    if not check_path or not check_path.exists():
        print(f"❌ 源视频文件不存在（原始路径）: {check_path}")
        continue
    with strm_path.open("w", encoding="utf-8") as f:
        f.write(str(video_target))
    print(f"✅ .strm 文件创建: {strm_path.name} → {video_target}")

    # === poster 软链接（兼容 jpg/jpeg）===
    import shutil
    poster_raw = entry.get("poster")
    print(f"🎯 poster_raw (原始): {poster_raw}")

    poster_source = None

    if poster_raw:
        check_poster = Path(poster_raw)
        if check_poster.exists():
            poster_source = check_poster
        else:
            # 如果是目录或无效路径，尝试在同目录中查找 poster.jpg/jpeg
            parent_dir = check_poster.parent if check_poster.suffix else check_poster
            for ext in [".jpg", ".jpeg", ".JPG", ".JPEG"]:
                candidate = parent_dir / f"poster{ext}"
                if candidate.exists():
                    poster_source = candidate
                    break
    print(f"🎯 poster_source (确定路径): {poster_source}")

    poster_link = entry_dir / "poster.jpg"

    if poster_source and poster_source.exists():
        if poster_link.exists():
            if not poster_link.is_file():
                poster_link.unlink()
                shutil.copyfile(poster_source, poster_link)
                print(f"♻️ 修复非文件 poster: {poster_link.name}")
            else:
                # 强制覆盖已有旧文件
                shutil.copyfile(poster_source, poster_link)
                print(f"🔁 已存在: {poster_link.name}，已覆盖")
        else:
            shutil.copyfile(poster_source, poster_link)
            print(f"✅ poster复制完成: {poster_link.name}")
    else:
        print(f"⚠️ 找不到 poster（尝试 jpg/jpeg 均失败）: {poster_raw}")

    # === nfo 文件 ===
    description = entry.get("description", "").strip()
    models = entry.get("model") or []
    if isinstance(models, str):
        models = [models]

    keywords = entry.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [keywords]

    nfo_path = entry_dir / f"{base_name}.nfo"

    series = code.split("-")[0]

    nfo_lines = [
        "<movie>",
        f"  <title>{code} - {title}</title>",
        f"  <originaltitle>{code}</originaltitle>",
        f"  <sorttitle>{code}</sorttitle>",
        f"  <plot>{description}</plot>",
        f"  <outline>{description}</outline>",
        f"  <studio>TYINGART</studio>",
        f"  <tag>{series}</tag>",
    ]

    # 在 <tag> 之后插入 <genre> 标签
    for kw in keywords:
        nfo_lines.append(f"  <genre>{kw}</genre>")

    # 多演员支持
    for name in models:
        nfo_lines.extend([
            "  <actor>",
            f"    <name>{name}</name>",
            f"    <role>Model</role>",
            "  </actor>"
        ])

    # poster thumb（仅当存在 poster_link 文件）
    if poster_link.exists():
        nfo_lines.append(f"  <thumb>poster.jpg</thumb>")

    nfo_lines.append(f"  <id>{code}</id>")
    nfo_lines.append("</movie>")

    if nfo_path.exists() and not nfo_path.is_file():
        nfo_path.unlink()
        print(f"♻️ 修复非文件 nfo: {nfo_path.name}")

    # 即使 nfo 文件存在也强制更新
    with nfo_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(nfo_lines))

    print(f"📝 nfo 生成完成: {nfo_path.name}")
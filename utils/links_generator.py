import json
from pathlib import Path
import os
import re

def smart_numeric_sort_key(name: str):
    base = Path(name).stem

    # 1. 括号内的数字 → 最高优先级
    paren_match = re.search(r'\((\d+)\)', base)
    if paren_match:
        return int(paren_match.group(1))

    # 2. 纯数字开头（没有括号）→ 第二优先级
    pure_number_match = re.fullmatch(r'\d+', base)
    if pure_number_match:
        return int(pure_number_match.group(0))

    # 3. 字母+数字（如 DSC089731）→ 提取数字部分
    tail_number_match = re.search(r'(\d+)', base)
    if tail_number_match:
        return int(tail_number_match.group(1))

    # 4. fallback → 字母排序
    # return base.lower()
    raise ValueError(f"Unrecognized image filename format: {name}")

def convert_png_to_jpg(png_path: Path, jpg_path: Path):
    """
    将 PNG 文件转换为 JPG 文件，使用 Pillow。
    :param png_path: PNG 文件路径
    :param jpg_path: JPG 输出文件路径
    """
    from PIL import Image
    if not png_path.exists():
        print(f"❌ 源文件不存在: {png_path}")
        return
    try:
        image = Image.open(png_path).convert("RGB")
        jpg_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(jpg_path, format="JPEG", quality=90)
        print(f"✅ PNG 转 JPG 成功: {jpg_path}")
    except Exception as e:
        print(f"❌ 转换失败: {e}")

def media_entry_generator(entries, base_output_dir, entry_type="video", overwrite=False):
    handler = get_handler_by_type(entry_type)
    for entry in entries:
        handler(entry, base_output_dir, overwrite)


def get_handler_by_type(entry_type):
    if entry_type == "video":
        return handle_video_entry
    if entry_type == "model":
        return handle_model_entry
    if entry_type == "album":
        return handle_album_entry
    else:
        raise ValueError(f"不支持的 entry_type: {entry_type}")


# 专辑/相册类型处理
def handle_album_entry(entry, output_dir, overwrite):
    import shutil
    import unicodedata

    code = entry.get("code", "")
    title = entry.get("title", "")
    code = unicodedata.normalize("NFC", code)
    title = unicodedata.normalize("NFC", title or "")
    model = entry.get("model", "")
    if isinstance(model, list):
        model = ", ".join(model)
    model = unicodedata.normalize("NFC", model or "")
    base_name = code
    dir_name = f"{model} - {title} - {code}".strip()
    entry_dir = output_dir / dir_name
    entry_dir.mkdir(parents=True, exist_ok=True)

    # 处理图片软链接
    imgs = entry.get("imgs", {})
    sorted_items = []
    for fname, meta in imgs.items():
        try:
            sort_key = smart_numeric_sort_key(fname)
            path_str = meta["path"] if isinstance(meta, dict) and "path" in meta else meta
            sorted_items.append((sort_key, fname, path_str))
        except (ValueError, KeyError, TypeError) as e:
            print(f"⚠️ 跳过无法排序或无效的文件: {fname} - {e}")
    sorted_items.sort()
    for i, (_, fname, src_path) in enumerate(sorted_items, 1):
        if isinstance(src_path, dict):
            actual_src_path = src_path.get("path")
        else:
            actual_src_path = src_path
        if not isinstance(actual_src_path, (str, bytes, os.PathLike)):
            print(f"⚠️ 非法路径类型，跳过: {fname} - {actual_src_path}")
            continue
        src = Path(actual_src_path)
        if not src.exists():
            print(f"⚠️ 缺失图片文件: {actual_src_path}")
            continue
        target_name = f"{i:03d}{Path(fname).suffix.lower()}"
        link_path = entry_dir / target_name
        if link_path.exists():
            if overwrite and not link_path.is_file():
                link_path.unlink()
                os.link(src, link_path)
                print(f"♻️ 覆盖软链接: {link_path.name}")
            else:
                print(f"⏭️ 已存在，跳过: {link_path.name}")
        else:
            os.link(src, link_path)
            print(f"🔗 创建软链接: {link_path.name}")

    # 处理封面 poster
    poster_source = None
    for fname, meta in imgs.items():
        if isinstance(meta, dict) and meta.get("poster") is True:
            poster_source = Path(meta.get("path"))
            break

    # 如果所有 imgs 的 poster 都是 false，则选第一个图作为临时 poster
    if not poster_source and sorted_items:
        first_src_path = sorted_items[0][2]
        if isinstance(first_src_path, dict):
            first_src_path = first_src_path.get("path")
        if isinstance(first_src_path, (str, bytes, os.PathLike)):
            poster_source = Path(first_src_path)
            print(f"📌 自动选用第一张图作为 poster: {poster_source}")
    
    poster_target = entry_dir / "poster.jpg"
    if poster_source:
        if poster_source.exists():
            if poster_target.exists():
                if overwrite and not poster_target.is_file():
                    poster_target.unlink()
                    if poster_target.exists():
                        poster_target.unlink()
                    os.link(poster_source, poster_target)
                    print(f"♻️ 覆盖写入 poster.jpg")
                else:
                    print(f"⏭️ 跳过已有 poster.jpg")
            else:
                if poster_target.exists():
                    poster_target.unlink()
                os.link(poster_source, poster_target)
                print(f"✅ poster.jpg 写入完成")
        else:
            print(f"⚠️ 指定的 poster 文件不存在: {poster_source}")
    else:
        print("⚠️ 未指定 poster 或未找到对应图")

    # 写入 .nfo
    nfo_path = entry_dir / f"{base_name}.nfo"
    description = entry.get("description", "").strip()
    models = entry.get("model")
    if isinstance(models, str):
        models = [models]
    keywords = entry.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [keywords]
    studio = entry.get("studio", "")
    nfo_lines = [
        "<photoalbum>",
        f"  <title>{title}</title>",
        f"  <originaltitle>{code}</originaltitle>",
        f"  <plot>{description}</plot>",
        f"  <studio>{studio}</studio>",
    ]
    for kw in keywords:
        nfo_lines.append(f"  <tag>{kw.strip()}</tag>")
    for m in models:
        nfo_lines.extend([
            "  <actor>",
            f"    <name>{m}</name>",
            f"    <role>Model</role>",
            "  </actor>"
        ])
    if Path(entry_dir / "poster.jpg").exists():
        nfo_lines.append("  <thumb>poster.jpg</thumb>")
    nfo_lines.append(f"  <id>{code}</id>")
    nfo_lines.append("</photoalbum>")

    if nfo_path.exists():
        if overwrite and not nfo_path.is_file():
            nfo_path.unlink()
        with nfo_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(nfo_lines))
            print(f"♻️ 覆盖写入 album nfo: {nfo_path.name}")
    else:
        with nfo_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(nfo_lines))
            print(f"📝 album nfo 写入完成: {nfo_path.name}")


def generate_movie_nfo_lines(entry: dict) -> list[str]:
    from datetime import datetime
    today = datetime.today().strftime('%Y-%m-%d')

    code = entry.get("code", "")
    title = entry.get("title", "")
    description = entry.get("description", "").strip()
    series = code.split("-")[0] if isinstance(code, str) and "-" in code else (code or "")
    models = entry.get("model") or []
    keywords = entry.get("keywords") or []

    if isinstance(models, str):
        models = [models]
    if isinstance(keywords, str):
        keywords = [keywords]

    nfo_lines = [
        "<movie>",
        f"  <title>{code} - {title}</title>",
        f"  <originaltitle>{code}</originaltitle>",
        f"  <sorttitle>{code}</sorttitle>",
        f"  <plot>{description}</plot>",
        f"  <outline>{description}</outline>",
        f"  <premiered>{today}</premiered>",
        f"  <dateadded>{today}</dateadded>",
        f"  <tag>{series}</tag>",
    ]

    optional_fields = {
        "tagline": entry.get("tagline"),
        "runtime": entry.get("runtime"),
        "year": entry.get("year"),
        "director": entry.get("director"),
        "credits": entry.get("credits"),
        "writer": entry.get("writer"),
        "country": entry.get("country"),
        "countrycode": entry.get("countrycode"),
        "language": entry.get("language"),
        "rating": entry.get("rating"),
        "aspectratio": entry.get("aspectratio"),
    }

    for tag, value in optional_fields.items():
        if value:
            nfo_lines.append(f"  <{tag}>{value}</{tag}>")

    for kw in keywords:
        if kw:
            nfo_lines.append(f"  <genre>{kw}</genre>")

    for name in models:
        if name:
            nfo_lines.extend([
                "  <actor>",
                f"    <name>{name}</name>",
                f"    <role>Model</role>",
                "  </actor>"
            ])

    studios = entry.get("studio")
    if studios:
        if isinstance(studios, str):
            studios = [studios]
        for s in studios:
            if s:
                nfo_lines.append(f"  <studio>{s}</studio>")
                nfo_lines.append(f"  <genre>{s}</genre>")
    
    
    prefix = code.split("-")[0]
    if prefix and prefix != series:
        nfo_lines.append(f"  <tag>{prefix}</tag>")
        nfo_lines.append(f"  <genre>{prefix}</genre>")

    if entry.get("thumb") == "poster.jpg":
        nfo_lines.append("  <thumb>poster.jpg</thumb>")

    nfo_lines.extend([
        f"  <uniqueid type=\"manual\">{code}</uniqueid>",
        f"  <id>{code}</id>",
        "  <lockdata>true</lockdata>",
        "</movie>"
    ])
    return nfo_lines


def handle_video_entry(entry, output_dir, overwrite):
    import unicodedata
    import shutil

    VOLUME_PREFIX = "/Volumes/PRIVATE_COLLECTION/"
    MOUNT_PREFIX = "/mnt/nas/"

    code = entry.get("code")
    title = entry.get("title")
    code = unicodedata.normalize("NFC", code)
    title = unicodedata.normalize("NFC", title or "")
    raw_path = entry.get("path")
    check_path = Path(raw_path) if raw_path else None
    video_path = raw_path.replace(VOLUME_PREFIX, MOUNT_PREFIX) if raw_path else None

    poster = entry.get("poster")
    if not video_path:
        print(f"跳过无效条目: {entry}")
        return

    base_name = code
    dir_name = f"{code} - {title}".strip()
    entry_dir = output_dir / dir_name
    entry_dir.mkdir(parents=True, exist_ok=True)

    # 删除旧软链接文件
    for ext in [".mp4", ".avi", ".mov", ".mkv"]:
        old_link = entry_dir / f"{base_name}{ext}"
        if old_link.exists() and old_link.is_symlink():
            old_link.unlink()
            print(f"🧹 删除旧软链接: {old_link.name}")

    # .strm 文件
    video_target = Path(video_path)
    strm_path = entry_dir / f"{base_name}.strm"
    if not check_path or not check_path.exists():
        print(f"❌ 源视频文件不存在（原始路径）: {check_path}")
        return
    if strm_path.exists():
        if overwrite:
            if not strm_path.is_file():
                strm_path.unlink()
            with strm_path.open("w", encoding="utf-8") as f:
                f.write(str(video_target))
            print(f"♻️ 覆盖写入 .strm: {strm_path.name}")
        else:
            print(f"⏭️ 跳过已有 .strm: {strm_path.name}")
    else:
        with strm_path.open("w", encoding="utf-8") as f:
            f.write(str(video_target))
        print(f"✅ .strm 文件创建: {strm_path.name} → {video_target}")

    # poster 硬链接或复制
    poster_raw = entry.get("poster")
    print(f"🎯 poster_raw (原始): {poster_raw}")
    poster_source = None
    if poster_raw:
        check_poster = Path(poster_raw)
        if check_poster.exists():
            poster_source = check_poster
        else:
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
            if overwrite:
                if not poster_link.is_file():
                    poster_link.unlink()
                os.link(poster_source, poster_link)
                # shutil.copyfile(poster_source, poster_link)
                print(f"♻️ 覆盖写入 poster: {poster_link.name}")
            else:
                print(f"⏭️ 跳过已有 poster: {poster_link.name}")
        else:
            shutil.copyfile(poster_source, poster_link)
            print(f"✅ poster复制完成: {poster_link.name}")
    else:
        print(f"⚠️ 找不到 poster（尝试 jpg/jpeg 均失败）: {poster_raw}")
        # 使用 ffmpeg 从视频中截取封面图像
        poster_candidate = entry_dir / "poster.jpg"
        try:
            import subprocess
            result = subprocess.run([
                "ffmpeg",
                "-y",  # overwrite output file if it exists
                "-ss", "00:00:37",  # seek to 37 seconds
                "-i", str(video_target),
                "-frames:v", "1",
                "-q:v", "2",
                str(poster_candidate)
            ], capture_output=True, text=True)
            if result.returncode == 0 and poster_candidate.exists():
                print(f"🎞️ 自动从视频生成 poster: {poster_candidate.name}")
            else:
                print(f"⚠️ ffmpeg 截图失败: {result.stderr}")
        except Exception as e:
            print(f"❌ 自动生成 poster 失败: {e}")

    # nfo 文件
    nfo_path = entry_dir / f"{base_name}.nfo"
    # 生成 nfo_lines，自动判断 poster.jpg 是否存在
    nfo_entry = dict(entry)
    if (entry_dir / "poster.jpg").exists():
        nfo_entry["thumb"] = "poster.jpg"
    nfo_lines = generate_movie_nfo_lines(nfo_entry)

    if nfo_path.exists():
        if overwrite:
            if not nfo_path.is_file():
                nfo_path.unlink()
            with nfo_path.open("w", encoding="utf-8") as f:
                f.write("\n".join(nfo_lines))
            print(f"♻️ 覆盖写入 nfo: {nfo_path.name}")
        else:
            print(f"⏭️ 跳过已有 nfo: {nfo_path.name}")
    else:
        with nfo_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(nfo_lines))
        print(f"📝 nfo 生成完成: {nfo_path.name}")

def handle_model_entry(entry, output_dir, overwrite):
    import unicodedata
    import requests
    from PIL import Image
    from io import BytesIO

    name = entry.get("name")
    if not name:
        print("⚠️ 跳过无名人物 entry")
        return
    name = unicodedata.normalize("NFC", name)
    model_dir = output_dir / name
    model_dir.mkdir(parents=True, exist_ok=True)

    # 下载 poster
    poster_url = entry.get("poster_url") or entry.get("poster")
    poster_path = model_dir / "poster.jpg"
    if poster_url:
        if poster_path.exists():
            if overwrite:
                if not poster_path.is_file():
                    poster_path.unlink()
                try:
                    response = requests.get(poster_url, timeout=10)
                    response.raise_for_status()
                    image = Image.open(BytesIO(response.content)).convert("RGB")
                    image.save(poster_path, format="JPEG", quality=90)
                    print(f"♻️ 覆盖写入 poster: {poster_path}")
                except Exception as e:
                    print(f"❌ 下载 poster 失败: {e}")
            else:
                print(f"⏭️ 跳过已有 poster: {poster_path.name}")
        else:
            try:
                response = requests.get(poster_url, timeout=10)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content)).convert("RGB")
                image.save(poster_path, format="JPEG", quality=90)
                print(f"✅ 下载 poster 成功: {poster_path}")
            except Exception as e:
                print(f"❌ 下载 poster 失败: {e}")
    else:
        print("⚠️ 无 poster_url 提供")

    # 写入 nfo
    nfo_path = model_dir / f"{name}.nfo"
    nfo_lines = ["<person>"]
    nfo_lines.append(f"  <name>{name}</name>")
    nfo_lines.append(f"  <type>actor</type>")

    known_keys = {"name", "type", "poster", "poster_url"}
    extra_lines = []

    for key, value in entry.items():
        if key in known_keys:
            continue
        if key == "age":
            try:
                birthyear = int(value)
                birthyear = 2025 - birthyear if birthyear < 1900 else birthyear
                nfo_lines.append(f"  <birthyear>{birthyear}</birthyear>")
            except:
                continue
        elif key == "studio" and isinstance(value, list):
            for studio in value:
                nfo_lines.append(f"  <studio>{studio}</studio>")
        elif key == "real_name" and isinstance(value, list):
            for aka in value:
                nfo_lines.append(f"  <aka>{aka}</aka>")
        elif key == "SNS" and isinstance(value, list):
            for url in value:
                nfo_lines.append(f"  <socials>{url}</socials>")
        elif key.endswith("_score") and isinstance(value, (int, float)):
            nfo_lines.append(f"  <tag>{key}:{value}</tag>")
        elif key == "figure":
            extra_lines.append(f"Figure: {value}")
        elif key in {"description", "comments", "overview"} and isinstance(value, str) and value.strip():
            extra_lines.append(value.strip())
        else:
            # catch-all for unexpected fields
            if isinstance(value, list):
                for v in value:
                    extra_lines.append(f"{key}: {v}")
            elif isinstance(value, dict):
                extra_lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
            elif isinstance(value, str) and value.strip():
                extra_lines.append(f"{key}: {value.strip()}")
            elif isinstance(value, (int, float)):
                extra_lines.append(f"{key}: {value}")

    if extra_lines:
        joined = " | ".join(extra_lines)
        nfo_lines.append(f"  <overview>{joined}</overview>")

    if poster_path.exists():
        nfo_lines.append("  <image>poster.jpg</image>")

    # nfo_lines.append("<lockdata>true</lockdata>")
    nfo_lines.append("</person>")

    if nfo_path.exists():
        if overwrite:
            if not nfo_path.is_file():
                nfo_path.unlink()
            with nfo_path.open("w", encoding="utf-8") as f:
                f.write("\n".join(nfo_lines))
            print(f"♻️ 覆盖写入 nfo: {nfo_path.name}")
        else:
            print(f"⏭️ 跳过已有 nfo: {nfo_path.name}")
    else:
        with nfo_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(nfo_lines))
        print(f"📝 model nfo 生成完成: {nfo_path.name}")



if __name__ == "__main__":
    # json_path = Path("/home/paulwu/NAS/ty_album_metadata_updated.json")
    # output_dir = Path("/mnt/nas/jellyfin_links/albums")

    json_path = Path("/home/paulwu/NAS/tyingart_model_metadata.json")
    output_dir = Path("/mnt/nas/jellyfin_links/models")

    entry_type = "model"  # video 或 "album" 或 "model"

    output_dir.mkdir(parents=True, exist_ok=True)
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    entries = [v for k, v in data.items()]
    print(f"共找到 {len(entries)} 个条目")
    media_entry_generator(entries, output_dir, entry_type=entry_type, overwrite=True)

    # json_path = Path("TYINGART_MODEL_LATEST.json")
    # output_dir = Path("/Volumes/PRIVATE_COLLECTION/jellyfin_links/models")
    # with json_path.open(encoding="utf-8") as f:
    #     data = json.load(f)
    # entries = [v for k, v in data.items()]
    # print(f"共找到 {len(entries)} 个条目")
    # media_entry_generator(entries, output_dir, entry_type="model", overwrite=False)

    # 用法示例：PNG 转换为 JPG
    # convert_png_to_jpg(Path("kokomi.png"), Path("poster.jpg"))
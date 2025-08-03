#!/bin/bash

SOURCE_BASE="/mnt/nas/jellyfin_links/models"
TARGET_BASE="/var/lib/jellyfin/metadata/People"

# 遍历每个模型人物子目录
for model_path in "$SOURCE_BASE"/*; do
    [ -d "$model_path" ] || continue

    name=$(basename "$model_path")
    first_letter=$(echo "$name" | cut -c1 | tr '[:lower:]' '[:upper:]')
    target_path="$TARGET_BASE/$first_letter/$name"

    # 创建目标目录
    mkdir -p "$target_path"

    # 拷贝 poster.jpg
    if [ -f "$model_path/poster.jpg" ]; then
        cp "$model_path/poster.jpg" "$target_path/poster.jpg"
    fi

    # 拷贝 *.nfo 改名为 person.nfo
    nfo_file=$(find "$model_path" -maxdepth 1 -name "*.nfo" | head -n1)
    if [ -f "$nfo_file" ]; then
        cp "$nfo_file" "$target_path/person.nfo"
    fi

    echo "已处理：$name"
done

echo "✅ 所有人物信息已更新到 Jellyfin 元数据目录"

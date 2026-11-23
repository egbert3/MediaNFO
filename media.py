# -*- coding: utf-8 -*-
"""图片与文本处理：扫描文件夹图片、生成缩略图、导入为规范封面、读取 txt 简介。

Pillow 依赖放在同目录 _deps 下，代码中自动加入 sys.path，绿色免安装。
"""
import os
import sys
import hashlib
import tempfile
from typing import List, Optional

# 自动加载本地 Pillow（不污染系统 Python 环境）
_DEPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_deps")
if os.path.isdir(_DEPS) and _DEPS not in sys.path:
    sys.path.insert(0, _DEPS)

from PIL import Image, ImageOps  # noqa: E402

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif")
TEXT_EXTS = (".txt",)
VIDEO_EXTS = (".mkv", ".mp4", ".avi", ".mov", ".ts", ".m2ts", ".wmv",
              ".flv", ".webm", ".rmvb", ".m4v", ".iso")

# 各槽位建议的最大边长（像素），兼顾清晰度与体积
SLOT_MAX_SIDE = {
    "fanart": 1920,
    "landscape": 1920,
    "banner": 1600,
    "poster": 1600,
    "thumb": 800,
    "clearart": 1200,
    "clearlogo": 1200,
    "logo": 1200,
    "discart": 1000,
}
DEFAULT_MAX_SIDE = 1600


# ---------- 扫描 ----------

def _list_by_ext(folder: str, exts, exclude_prefixes=(".",)) -> List[str]:
    if not folder or not os.path.isdir(folder):
        return []
    result = []
    for name in sorted(os.listdir(folder)):
        if name.startswith(exclude_prefixes):
            continue
        if name.lower().endswith(exts):
            result.append(os.path.join(folder, name))
    return result


def list_images(folder: str) -> List[str]:
    return _list_by_ext(folder, IMAGE_EXTS)


def list_texts(folder: str) -> List[str]:
    return _list_by_ext(folder, TEXT_EXTS)


def list_videos(folder: str) -> List[str]:
    return _list_by_ext(folder, VIDEO_EXTS)


# ---------- 文本 ----------

def read_text(path: str) -> str:
    """按多种常见编码尝试读取 txt，解决中文简介乱码问题。"""
    if not path or not os.path.isfile(path):
        return ""
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    # 最后兜底：忽略非法字节
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ---------- 图片 ----------

def _load_image(path: str) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)   # 修正手机/相机方向
    return img


def image_size(path: str):
    try:
        with Image.open(path) as img:
            return img.size
    except Exception:
        return (0, 0)


def _cache_path(path: str, suffix: str = "") -> str:
    stat = os.stat(path)
    key = "%s|%s|%s" % (os.path.abspath(path), stat.st_size, int(stat.st_mtime))
    h = hashlib.md5(key.encode("utf-8")).hexdigest()[:16]
    return os.path.join(tempfile.gettempdir(), "medianfo_%s%s.png" % (h, suffix))


def make_thumbnail(path: str, box=(170, 250)) -> Optional[str]:
    """生成 PNG 缩略图到临时目录，返回路径（供 tkinter PhotoImage 使用）。"""
    if not path or not os.path.isfile(path):
        return None
    out = _cache_path(path, "_thumb")
    if os.path.isfile(out):
        return out
    try:
        img = _load_image(path)
        img.thumbnail(box, Image.LANCZOS)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        img.save(out, "PNG")
        return out
    except Exception:
        return None


def make_preview(path: str, box=(420, 600)) -> Optional[str]:
    """生成较大的预览图，返回 PNG 路径。"""
    if not path or not os.path.isfile(path):
        return None
    out = _cache_path(path, "_preview")
    if os.path.isfile(out):
        return out
    try:
        img = _load_image(path)
        img.thumbnail(box, Image.LANCZOS)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        img.save(out, "PNG")
        return out
    except Exception:
        return None


def _to_rgb(img: Image.Image, bg=(0, 0, 0)) -> Image.Image:
    """将带透明通道的图片合成到纯色背景，转为 RGB（便于保存为 JPG）。"""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, bg)
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return img.convert("RGB")


def import_as_cover(src: str, folder: str, slot: str,
                    name: str = "", quality: int = 90,
                    max_side: int = 0) -> Optional[str]:
    """把任意图片导入并转换为规范封面文件（JPG）。

    slot: poster / fanart / banner ... 决定默认文件名与最大尺寸。
    name: 自定义文件名（不含扩展名）；为空时用 slot。
    返回写入的文件路径，失败返回 None。
    """
    if not src or not os.path.isfile(src) or not folder:
        return None
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)

    filename = (name.strip() or slot or "cover") + ".jpg"
    dest = os.path.join(folder, filename)

    try:
        img = _to_rgb(_load_image(src))
        limit = max_side or SLOT_MAX_SIDE.get(slot, DEFAULT_MAX_SIDE)
        w, h = img.size
        if max(w, h) > limit:
            ratio = float(limit) / max(w, h)
            img = img.resize((max(1, int(w * ratio)), max(1, int(h * ratio))),
                             Image.LANCZOS)
        img.save(dest, "JPEG", quality=quality, optimize=True)
        return dest
    except Exception:
        return None


def rotate_copy(src: str, dest: str, degrees: int = 90) -> Optional[str]:
    """旋转图片并另存（用于“编辑图片”）。"""
    if not src or not os.path.isfile(src):
        return None
    try:
        img = _load_image(src)
        img = img.rotate(degrees, expand=True)
        img = _to_rgb(img)
        directory = os.path.dirname(os.path.abspath(dest))
        if directory and not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        img.save(dest, "JPEG", quality=92, optimize=True)
        return dest
    except Exception:
        return None


def delete_file(path: str) -> bool:
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except Exception:
        pass
    return False

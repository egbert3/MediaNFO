# -*- coding: utf-8 -*-
"""NFO 生成与解析。

生成结果兼容 Kodi / Emby / Jellyfin 等主流媒体库使用的 nfo 规范：
  - 电影: <movie>  -> movie.nfo
  - 电视剧: <tvshow> -> tvshow.nfo，外加每集 <episodedetails> -> SxxExx.nfo
所有外部 ID（IMDb/TMDB/TVDB）均为可选，不填写也不会报错。
"""
import os
import xml.etree.ElementTree as ET
from typing import List, Optional

from models import Movie, TVShow, Episode, Person, IMAGE_SLOTS

XML_HEADER = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
SLOT_KEYS = [k for k, _ in IMAGE_SLOTS]


# ---------- 内部工具 ----------

def _sub(parent: ET.Element, tag: str, text=None, **attrs) -> Optional[ET.Element]:
    """创建子节点；空值不写入。"""
    if text is None or str(text).strip() == "":
        return None
    el = ET.SubElement(parent, tag, **{k: str(v) for k, v in attrs.items()})
    el.text = str(text)
    return el


def _sub_names(parent: ET.Element, tag: str, values: List[str]):
    for v in values or []:
        _sub(parent, tag, v)


def _add_actors(parent: ET.Element, actors: List[Person]):
    for a in actors or []:
        if not a or a.is_empty():
            continue
        node = ET.SubElement(parent, "actor")
        _sub(node, "name", a.name)
        _sub(node, "role", a.role)
        _sub(node, "thumb", a.thumb)


def _add_images(parent: ET.Element, images: dict):
    if not images:
        return
    # fanart 单独节点
    fanart = (images.get("fanart") or "").strip()
    if fanart:
        fan_node = ET.SubElement(parent, "fanart")
        _sub(fan_node, "thumb", fanart)
    # 其余槽位用 <thumb aspect="...">
    for slot in SLOT_KEYS:
        if slot == "fanart":
            continue
        value = (images.get(slot) or "").strip()
        if value:
            _sub(parent, "thumb", value, aspect=slot)


def _fill_common(root: ET.Element, media):
    """写入 BaseMedia 的通用字段。"""
    _sub(root, "title", media.title)
    _sub(root, "originaltitle", media.originaltitle)
    _sub(root, "sorttitle", media.sorttitle)
    _sub(root, "year", media.year)
    _sub(root, "releasedate", media.releasedate)
    _sub(root, "premiered", media.releasedate)   # 兼容旧版刮削器
    _sub(root, "runtime", media.runtime)
    _sub(root, "country", media.country)
    _sub(root, "studio", media.studio)
    _sub(root, "mpaa", media.mpaa)
    _sub(root, "rating", media.rating)
    _sub(root, "votes", media.votes)
    _sub(root, "tagline", media.tagline)
    _sub(root, "outline", media.outline)
    _sub(root, "plot", media.plot)

    _sub_names(root, "genre", media.genres)
    _sub_names(root, "tag", media.tags)
    _sub_names(root, "director", media.directors)
    _sub_names(root, "writer", media.writers)
    _sub_names(root, "credits", media.writers)   # Kodi 用 credits 表示编剧
    _add_actors(root, media.actors)

    if media.imdb_id:
        _sub(root, "imdbid", media.imdb_id)
    if media.tmdb_id:
        _sub(root, "tmdbid", media.tmdb_id)
    if media.tvdb_id:
        _sub(root, "tvdbid", media.tvdb_id)


def _tostring(root: ET.Element) -> str:
    try:
        ET.indent(root, space="  ")  # Python 3.9+
    except AttributeError:
        pass
    return XML_HEADER + ET.tostring(root, encoding="unicode")


def _safe_write(path: str, content: str) -> str:
    directory = os.path.dirname(os.path.abspath(path))
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return path


# ---------- 生成 ----------

def build_movie_nfo(movie: Movie) -> str:
    root = ET.Element("movie")
    _fill_common(root, movie)
    if movie.local_id:
        _sub(root, "id", movie.local_id)
    _add_images(root, movie.images)
    return _tostring(root)


def build_tvshow_nfo(show: TVShow) -> str:
    root = ET.Element("tvshow")
    _fill_common(root, show)
    _sub(root, "season", show.season_count)
    _sub(root, "episode", show.episode_count)
    _add_images(root, show.images)
    return _tostring(root)


def build_episode_nfo(ep: Episode) -> str:
    root = ET.Element("episodedetails")
    _sub(root, "season", ep.season)
    _sub(root, "episode", ep.episode)
    _sub(root, "title", ep.title)
    _sub(root, "aired", ep.releasedate)
    _sub(root, "releasedate", ep.releasedate)
    _sub(root, "runtime", ep.runtime)
    _sub(root, "rating", ep.rating)
    _sub(root, "votes", ep.votes)
    _sub(root, "plot", ep.plot)
    _sub_names(root, "director", ep.directors)
    _sub_names(root, "writer", ep.writers)
    _sub_names(root, "credits", ep.writers)
    _add_actors(root, ep.actors)
    if ep.imdb_id:
        _sub(root, "imdbid", ep.imdb_id)
    if ep.tmdb_id:
        _sub(root, "tmdbid", ep.tmdb_id)
    if ep.tvdb_id:
        _sub(root, "tvdbid", ep.tvdb_id)
    return _tostring(root)


def save_movie(movie: Movie, path: str = "") -> str:
    """保存电影 NFO，返回写入路径。"""
    target = path or movie.nfo_path or os.path.join(movie.folder, "movie.nfo")
    _safe_write(target, build_movie_nfo(movie))
    movie.nfo_path = target
    return target


def save_tvshow(show: TVShow, save_episodes: bool = True,
                only_episode=None) -> List[str]:
    """保存电视剧 NFO：tvshow.nfo + 每集 NFO。返回写入路径列表。

    only_episode: 若指定 Episode 对象，则只保存该集（用于单集编辑）。
    """
    written = []
    if only_episode is None:
        target = os.path.join(show.folder, "tvshow.nfo")
        _safe_write(target, build_tvshow_nfo(show))
        written.append(target)

    episodes = [only_episode] if only_episode is not None else show.episodes
    for ep in episodes or []:
        if ep.filename:
            base = os.path.splitext(os.path.basename(ep.filename))[0]
        else:
            base = "S%02dE%02d" % (ep.season, ep.episode)
        path = os.path.join(show.folder, base + ".nfo")
        _safe_write(path, build_episode_nfo(ep))
        ep.nfo_path = path
        written.append(path)
    return written


# ---------- 解析 ----------

def _text(node: ET.Element, *tags: str) -> str:
    """按优先级返回第一个非空子节点文本。"""
    for tag in tags:
        child = node.find(tag)
        if child is not None and child.text and child.text.strip():
            return child.text.strip()
    return ""


def _texts(node: ET.Element, *tags: str) -> List[str]:
    result = []
    for tag in tags:
        for child in node.findall(tag):
            if child.text and child.text.strip() and child.text.strip() not in result:
                result.append(child.text.strip())
    return result


def _parse_actors(node: ET.Element) -> List[Person]:
    actors = []
    for a in node.findall("actor"):
        p = Person(
            name=_text(a, "name"),
            role=_text(a, "role"),
            thumb=_text(a, "thumb"),
        )
        if not p.is_empty():
            actors.append(p)
    return actors


def _parse_common(node: ET.Element, media):
    media.title = _text(node, "title")
    media.originaltitle = _text(node, "originaltitle")
    media.sorttitle = _text(node, "sorttitle")
    media.year = _text(node, "year")
    media.releasedate = _text(node, "releasedate", "premiered", "aired")
    media.runtime = _text(node, "runtime")
    media.country = _text(node, "country")
    media.studio = _text(node, "studio")
    media.mpaa = _text(node, "mpaa", "certification")
    media.rating = _text(node, "rating")
    media.votes = _text(node, "votes")
    media.tagline = _text(node, "tagline")
    media.outline = _text(node, "outline")
    media.plot = _text(node, "plot", "summary", "description")

    media.genres = _texts(node, "genre")
    media.tags = _texts(node, "tag")
    media.directors = _texts(node, "director")
    media.writers = _texts(node, "writer", "credits")
    media.actors = _parse_actors(node)

    media.imdb_id = _text(node, "imdbid", "imdb_id")
    media.tmdb_id = _text(node, "tmdbid", "tmdb_id")
    media.tvdb_id = _text(node, "tvdbid", "tvdb_id")

    # 图片节点
    images = {}
    for th in node.findall("thumb"):
        value = (th.text or "").strip()
        if not value:
            continue
        aspect = (th.get("aspect") or "").strip().lower()
        if aspect in SLOT_KEYS:
            images[aspect] = value
        elif "poster" not in images:
            images["poster"] = value
    for fan in node.findall("fanart"):
        for th in fan.findall("thumb"):
            value = (th.text or "").strip()
            if value:
                images["fanart"] = value
                break
    media.images = images


def _parse_movie(node: ET.Element, path: str) -> Movie:
    movie = Movie()
    movie.folder = os.path.dirname(os.path.abspath(path))
    movie.nfo_path = path
    _parse_common(node, movie)
    movie.local_id = _text(node, "id")
    return movie


def _parse_episode(node: ET.Element, path: str = "") -> Episode:
    ep = Episode()
    if path:
        ep.nfo_path = path
        ep.filename = os.path.splitext(os.path.basename(path))[0]
    ep.season = _to_int(_text(node, "season")) or 1
    ep.episode = _to_int(_text(node, "episode")) or 1
    ep.title = _text(node, "title")
    ep.plot = _text(node, "plot", "summary")
    ep.releasedate = _text(node, "aired", "releasedate", "premiered")
    ep.runtime = _text(node, "runtime")
    ep.rating = _text(node, "rating")
    ep.votes = _text(node, "votes")
    ep.directors = _texts(node, "director")
    ep.writers = _texts(node, "writer", "credits")
    ep.actors = _parse_actors(node)
    ep.imdb_id = _text(node, "imdbid", "imdb_id")
    ep.tmdb_id = _text(node, "tmdbid", "tmdb_id")
    ep.tvdb_id = _text(node, "tvdbid", "tvdb_id")
    return ep


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def _parse_tvshow(node: ET.Element, path: str) -> TVShow:
    show = TVShow()
    show.folder = os.path.dirname(os.path.abspath(path))
    show.nfo_path = path
    _parse_common(node, show)
    show.season_count = _to_int(_text(node, "season"))
    show.episode_count = _to_int(_text(node, "episode"))

    # tvshow.nfo 内嵌剧集
    for child in node.findall("episodedetails"):
        show.episodes.append(_parse_episode(child, ""))

    # 扫描同目录其他 nfo 作为剧集
    for filename in sorted(os.listdir(show.folder)):
        if not filename.lower().endswith(".nfo"):
            continue
        if filename.lower() in ("tvshow.nfo", "movie.nfo", "season.nfo"):
            continue
        ep = try_parse_episode_nfo(os.path.join(show.folder, filename))
        if ep is not None:
            # 避免与内嵌剧集重复（同季同集）
            if not any(e.season == ep.season and e.episode == ep.episode for e in show.episodes):
                show.episodes.append(ep)
    show.episodes.sort(key=lambda e: (e.season, e.episode))
    if not show.season_count or not show.episode_count:
        show.sync_counts()
    return show


def try_parse_episode_nfo(path: str) -> Optional[Episode]:
    """尝试解析单个 nfo 是否为剧集文件；不是则返回 None。"""
    try:
        root = ET.parse(path).getroot()
    except Exception:
        return None
    if root.tag.lower() not in ("episodedetails", "episode"):
        return None
    return _parse_episode(root, path)


def parse_nfo(path: str):
    """自动识别 nfo 类型并返回 Movie / TVShow / Episode。"""
    if not os.path.isfile(path):
        raise FileNotFoundError("找不到文件: %s" % path)
    root = ET.parse(path).getroot()
    tag = root.tag.lower()
    if tag == "movie":
        return _parse_movie(root, path)
    if tag == "tvshow":
        return _parse_tvshow(root, path)
    if tag in ("episodedetails", "episode"):
        return _parse_episode(root, path)
    raise ValueError("无法识别的 NFO 类型: %s" % root.tag)


# ---------- 文件夹内 NFO 扫描（刮削信息发现） ----------

def find_nfo_candidates(folder: str) -> List[dict]:
    """扫描文件夹内所有 .nfo 文件，识别类型/标题，供界面列出并读取。

    返回按优先级排序的字典列表：
      {path, name, kind, title, year, is_main}
    其中 kind 为 movie / tvshow / episode / unknown，is_main 表示是否主 NFO。
    """
    result: List[dict] = []
    if not folder or not os.path.isdir(folder):
        return result
    kind_order = {"movie": 0, "tvshow": 0, "episode": 1, "unknown": 2}
    for name in os.listdir(folder):
        if not name.lower().endswith(".nfo"):
            continue
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        kind, title, year = "unknown", "", ""
        try:
            root = ET.parse(path).getroot()
            tag = root.tag.lower()
            if tag == "movie":
                kind = "movie"
            elif tag == "tvshow":
                kind = "tvshow"
            elif tag in ("episodedetails", "episode"):
                kind = "episode"
            title = _text(root, "title")
            year = _text(root, "year")
        except Exception:
            pass
        lower = name.lower()
        is_main = lower == "movie.nfo" or lower == "tvshow.nfo"
        result.append({
            "path": path, "name": name, "kind": kind,
            "title": title, "year": year, "is_main": is_main,
        })
    result.sort(key=lambda d: (
        0 if d["is_main"] else 1,
        kind_order.get(d["kind"], 3),
        d["name"].lower(),
    ))
    return result


def find_best_main_nfo(folder: str) -> str:
    """挑出最适合作为主信息的 NFO 路径：先标准命名，其次任意 movie/tvshow。

    纯剧集 NFO（episode）不会被当成主 NFO。找不到返回空串。
    """
    candidates = find_nfo_candidates(folder)
    for c in candidates:
        if c["kind"] in ("movie", "tvshow"):
            return c["path"]
    return ""

# -*- coding: utf-8 -*-
"""统一数据模型：电影 / 电视剧 / 剧集 / 人物。

不依赖任何第三方库，供 NFO 模块与 GUI 模块共用。
"""
from dataclasses import dataclass, field
from typing import List, Dict


# 图片槽位 -> 说明（规范文件名前缀，Kodi / Emby / Jellyfin 通用约定）
IMAGE_SLOTS = [
    ("poster", "主海报"),
    ("fanart", "背景图"),
    ("banner", "横幅"),
    ("landscape", "横向剧照"),
    ("thumb", "缩略图"),
    ("clearart", "透明艺术图"),
    ("clearlogo", "透明标志"),
    ("logo", "标志"),
    ("discart", "光盘图"),
]

IMAGE_SLOT_NAMES = dict(IMAGE_SLOTS)


@dataclass
class Person:
    name: str = ""
    role: str = ""      # 角色名（演员适用）
    thumb: str = ""     # 头像图片路径（可选）

    def is_empty(self) -> bool:
        return not any([self.name.strip(), self.role.strip(), self.thumb.strip()])


@dataclass
class BaseMedia:
    """电影与电视剧共通字段。"""
    media_type: str = "movie"           # movie / tvshow

    # 标题信息
    title: str = ""
    originaltitle: str = ""
    sorttitle: str = ""

    # 发行信息
    year: str = ""
    releasedate: str = ""               # YYYY-MM-DD
    runtime: str = ""                   # 分钟
    country: str = ""
    studio: str = ""
    mpaa: str = ""                      # 分级

    # 评分
    rating: str = ""
    votes: str = ""

    # 简介
    tagline: str = ""
    plot: str = ""
    outline: str = ""

    # 分类
    genres: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # 演职员
    directors: List[str] = field(default_factory=list)
    writers: List[str] = field(default_factory=list)
    actors: List[Person] = field(default_factory=list)

    # 外部 ID（可选，不强制）
    imdb_id: str = ""
    tmdb_id: str = ""
    tvdb_id: str = ""

    # 图片：槽位 -> 文件名（相对于媒体文件夹）
    images: Dict[str, str] = field(default_factory=dict)

    # 来源信息
    folder: str = ""                    # 当前媒体文件夹
    nfo_path: str = ""                  # 读取/写入的 NFO 路径

    def set_image(self, slot: str, filename: str):
        if filename:
            self.images[slot] = filename
        else:
            self.images.pop(slot, None)

    def get_image(self, slot: str) -> str:
        return self.images.get(slot, "")


@dataclass
class Movie(BaseMedia):
    media_type: str = "movie"
    local_id: str = ""                  # 自定义本地编号（可选）


@dataclass
class Episode:
    """单集信息。"""
    season: int = 1
    episode: int = 1
    title: str = ""
    plot: str = ""
    releasedate: str = ""               # YYYY-MM-DD
    runtime: str = ""
    rating: str = ""
    votes: str = ""

    directors: List[str] = field(default_factory=list)
    writers: List[str] = field(default_factory=list)
    actors: List[Person] = field(default_factory=list)

    imdb_id: str = ""
    tmdb_id: str = ""
    tvdb_id: str = ""

    filename: str = ""                  # 关联的视频文件名（用于生成同名 NFO）
    nfo_path: str = ""

    def label(self) -> str:
        return "S%02dE%02d %s" % (self.season, self.episode, self.title or "(无标题)")


@dataclass
class TVShow(BaseMedia):
    media_type: str = "tvshow"
    season_count: int = 0               # 总季数
    episode_count: int = 0              # 总集数
    episodes: List[Episode] = field(default_factory=list)

    def sync_counts(self):
        """根据剧集列表同步季数与集数（若列表非空）。"""
        if self.episodes:
            self.episode_count = len(self.episodes)
            seasons = {e.season for e in self.episodes if e.season > 0}
            if seasons:
                self.season_count = max(seasons)

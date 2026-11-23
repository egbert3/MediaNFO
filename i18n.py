# -*- coding: utf-8 -*-
"""多语言支持（中文 / English）。

语言偏好保存在程序目录下的 config.json，绿色免安装。
用法：i18n.init(config_path)；i18n.t("key", **kwargs)；i18n.set_language("en")。
"""
import json
import os

LANG_ZH = "zh"
LANG_EN = "en"

# 图片槽位英文名（中文名来自 models.IMAGE_SLOTS）
SLOT_EN = {
    "poster": "Main Poster", "fanart": "Fanart / Backdrop", "banner": "Banner",
    "landscape": "Landscape", "thumb": "Thumbnail", "clearart": "Clear Art",
    "clearlogo": "Clear Logo", "logo": "Logo", "discart": "Disc Art",
}

# 所有可翻译文本：key -> {zh, en}
STRINGS = {
    # ---- 通用 ----
    "ok": {"zh": "确定", "en": "OK"},
    "cancel": {"zh": "取消", "en": "Cancel"},
    "hint": {"zh": "提示", "en": "Notice"},
    "error": {"zh": "错误", "en": "Error"},
    "failed": {"zh": "失败", "en": "Failed"},
    "yes": {"zh": "是", "en": "Yes"},
    "no": {"zh": "否", "en": "No"},
    "movie": {"zh": "电影", "en": "Movie"},
    "tvshow": {"zh": "电视剧", "en": "TV Show"},
    "episode_kind": {"zh": "单集", "en": "Episode"},
    "unknown": {"zh": "未知", "en": "Unknown"},

    # ---- 演员对话框 ----
    "actor_title": {"zh": "演职员", "en": "Cast & Crew"},
    "name": {"zh": "姓名：", "en": "Name:"},
    "role": {"zh": "角色：", "en": "Role:"},
    "name_required": {"zh": "姓名不能为空", "en": "Name cannot be empty"},

    # ---- 剧集对话框 ----
    "episode_title": {"zh": "剧集信息", "en": "Episode Info"},
    "season_label": {"zh": "季 (Season)：", "en": "Season:"},
    "episode_label": {"zh": "集 (Episode)：", "en": "Episode:"},
    "title_label": {"zh": "标题：", "en": "Title:"},
    "premiered": {"zh": "首播日期：", "en": "First Aired:"},
    "runtime_min": {"zh": "时长(分钟)：", "en": "Runtime (min):"},
    "video_file": {"zh": "视频文件：", "en": "Video File:"},
    "plot_label": {"zh": "简介：", "en": "Plot:"},
    "video_files_filter": {"zh": "视频文件", "en": "Video Files"},
    "all_files_filter": {"zh": "所有文件", "en": "All Files"},

    # ---- 主窗口 ----
    "app_title": {"zh": "MediaNFO 媒体元数据编辑器", "en": "MediaNFO Metadata Editor"},
    "status_ready": {"zh": "就绪。请选择媒体文件夹，或新建电影 / 电视剧。",
                     "en": "Ready. Select a media folder or create a new movie / TV show."},
    "select_folder": {"zh": "选择文件夹", "en": "Select Folder"},
    "reload": {"zh": "重新读取", "en": "Reload"},
    "new_movie": {"zh": "新建电影", "en": "New Movie"},
    "new_tvshow": {"zh": "新建电视剧", "en": "New TV Show"},
    "switch_to_tvshow": {"zh": "切换为电视剧", "en": "Switch to TV Show"},
    "switch_to_movie": {"zh": "切换为电影", "en": "Switch to Movie"},
    "open_nfo": {"zh": "打开 NFO", "en": "Open NFO"},
    "save_nfo": {"zh": "保存 NFO", "en": "Save NFO"},
    "about": {"zh": "关于", "en": "About"},
    "language": {"zh": "语言：", "en": "Language:"},
    "media_folder": {"zh": "媒体文件夹：", "en": "Media Folder:"},
    "current_prefix": {"zh": "当前：{name}", "en": "Current: {name}"},
    "switched_kept": {"zh": "已切换为{name}，原有信息已保留。",
                      "en": "Switched to {name}; existing information was kept."},

    # ---- 左侧面板 ----
    "folder_contents": {"zh": "当前文件夹内容", "en": "Current Folder Contents"},
    "images_section": {"zh": "图片：", "en": "Images:"},
    "select_image_preview": {"zh": "（选择图片预览）", "en": "(Select an image to preview)"},
    "preview_failed": {"zh": "预览失败", "en": "Preview failed"},
    "big_preview": {"zh": "大图预览", "en": "Full Preview"},
    "rotate_90": {"zh": "旋转 90°", "en": "Rotate 90°"},
    "delete_image": {"zh": "删除图片", "en": "Delete Image"},
    "txt_section": {"zh": "简介文档 (.txt)：", "en": "Synopsis Files (.txt):"},
    "import_synopsis": {"zh": "导入选中简介到简介框", "en": "Import Selected Synopsis"},
    "preview_synopsis": {"zh": "预览简介", "en": "Preview Synopsis"},
    "videos_section": {"zh": "视频文件（用于剧集）：", "en": "Video Files (for episodes):"},
    "video_count": {"zh": "{n} 个视频文件", "en": "{n} video file(s)"},
    "nfo_section": {"zh": "NFO 刮削信息（点选读取 / 可删除）：",
                    "en": "NFO Scraper Info (click to load / delete):"},
    "read_selected": {"zh": "读取选中", "en": "Load Selected"},
    "delete_selected": {"zh": "删除选中", "en": "Delete Selected"},

    # ---- 选项卡 ----
    "tab_basic": {"zh": "基本信息", "en": "Basic Info"},
    "tab_plot": {"zh": "简介与分类", "en": "Plot & Genres"},
    "tab_people": {"zh": "演职员", "en": "Cast & Crew"},
    "tab_episodes": {"zh": "剧集信息（电视剧）", "en": "Episodes (TV Show)"},
    "tab_images": {"zh": "图片与封面", "en": "Images & Covers"},

    # ---- 基本信息选项卡 ----
    "title_release": {"zh": "标题与发行", "en": "Title & Release"},
    "title_field": {"zh": "标题 *", "en": "Title *"},
    "originaltitle": {"zh": "原标题", "en": "Original Title"},
    "sorttitle": {"zh": "排序标题", "en": "Sort Title"},
    "year": {"zh": "年份", "en": "Year"},
    "releasedate": {"zh": "发行日期", "en": "Release Date"},
    "runtime": {"zh": "时长(分钟)", "en": "Runtime (min)"},
    "mpaa": {"zh": "分级 MPAA", "en": "MPAA Rating"},
    "country": {"zh": "国家/地区", "en": "Country"},
    "studio": {"zh": "工作室", "en": "Studio"},
    "rating_ids": {"zh": "评分与外部 ID（可选，不强制）", "en": "Rating & External IDs (optional)"},
    "rating": {"zh": "评分", "en": "Rating"},
    "votes": {"zh": "投票数", "en": "Votes"},

    # ---- 简介选项卡 ----
    "tagline": {"zh": "标语 / Tagline", "en": "Tagline"},
    "plot_import": {"zh": "简介 / Plot（可从 txt 导入）", "en": "Plot (can import from txt)"},
    "outline": {"zh": "大纲 / Outline", "en": "Outline"},
    "genres": {"zh": "类型 / Genre（每行一个）", "en": "Genres (one per line)"},
    "tags": {"zh": "标签 / Tag（每行一个）", "en": "Tags (one per line)"},

    # ---- 演职员选项卡 ----
    "directors": {"zh": "导演（每行一位）", "en": "Directors (one per line)"},
    "writers": {"zh": "编剧（每行一位）", "en": "Writers (one per line)"},
    "actors": {"zh": "演员", "en": "Actors"},
    "add_actor": {"zh": "添加演员", "en": "Add Actor"},
    "edit": {"zh": "编辑", "en": "Edit"},
    "delete": {"zh": "删除", "en": "Delete"},

    # ---- 剧集选项卡 ----
    "season_count": {"zh": "总季数", "en": "Total Seasons"},
    "episode_count": {"zh": "总集数", "en": "Total Episodes"},
    "gen_episodes": {"zh": "从视频文件名生成剧集", "en": "Generate Episodes from Filenames"},
    "episode_list": {"zh": "剧集列表（双击编辑）", "en": "Episode List (double-click to edit)"},
    "col_season": {"zh": "季", "en": "Season"},
    "col_episode": {"zh": "集", "en": "Ep"},
    "col_title": {"zh": "标题", "en": "Title"},
    "col_video": {"zh": "视频文件", "en": "Video File"},
    "add_episode": {"zh": "添加一集", "en": "Add Episode"},
    "sort_episodes": {"zh": "按季/集排序", "en": "Sort by Season/Episode"},

    # ---- 图片选项卡 ----
    "slots_header": {"zh": "图片槽位（输入或导入文件名，将写入 NFO 供媒体库识别）",
                     "en": "Image Slots (enter or import filenames; written into NFO for media libraries)"},
    "slots_naming": {"zh": "规范命名：poster.jpg（主海报）、fanart.jpg（背景）、banner.jpg（横幅）等",
                     "en": "Standard names: poster.jpg (main), fanart.jpg (backdrop), banner.jpg, etc."},
    "cover_slots": {"zh": "封面槽位", "en": "Cover Slots"},
    "import_from_selected": {"zh": "从选中图片导入", "en": "Import from Selected"},
    "clear": {"zh": "清除", "en": "Clear"},
    "images_note": {"zh": "提示：先在左侧“当前文件夹内容”选中一张图片，再点对应槽位的“从选中图片导入”。\n"
                          "导入会把图片转换为 JPG 并按槽位命名（如 poster.jpg），原图不会删除。",
                    "en": "Tip: first select an image in the left 'Current Folder Contents' panel, "
                          "then click 'Import from Selected' on the desired slot.\n"
                          "Import converts the image to JPG and names it by slot (e.g. poster.jpg); "
                          "the original is not deleted."},

    # ---- 文件夹与消息 ----
    "select_folder_title": {"zh": "选择媒体文件夹", "en": "Select Media Folder"},
    "select_save_title": {"zh": "选择保存位置", "en": "Choose Save Location"},
    "pick_first_folder": {"zh": "请先选择媒体文件夹。", "en": "Please select a media folder first."},
    "reload_confirm": {"zh": "将从文件夹重新扫描并读取 NFO，未保存的修改会丢失。\n是否继续？",
                       "en": "This will rescan the folder and reload NFO; unsaved changes will be lost.\nContinue?"},
    "loaded_scraper": {"zh": "已读取刮削信息：{name}", "en": "Loaded scraper info: {name}"},
    "ep_nfo_notice": {"zh": "检测到剧集 NFO，但未自动载入（可用“打开 NFO”选择）",
                      "en": "Episode NFO detected but not auto-loaded (use 'Open NFO' to select)"},
    "read_nfo_failed": {"zh": "读取 NFO 失败：{err}", "en": "Failed to read NFO: {err}"},
    "folder_selected": {"zh": "已选择文件夹：{folder}（未发现 NFO，可新建）",
                        "en": "Folder selected: {folder} (no NFO found; you can create one)"},
    "pick_nfo_first": {"zh": "请先在左侧选中一个 NFO 文件。", "en": "Please select an NFO file on the left first."},
    "parse_nfo_error": {"zh": "解析 NFO 出错：\n{err}", "en": "Error parsing NFO:\n{err}"},
    "read_failed": {"zh": "读取失败", "en": "Read Failed"},
    "single_ep_nfo": {"zh": "这是单集 NFO，包含的是某一集的剧集信息。\n请打开主 NFO（tvshow.nfo）以载入整部剧集。",
                      "en": "This is a single-episode NFO containing info for one episode.\n"
                            "Please open the main NFO (tvshow.nfo) to load the whole series."},
    "single_ep_nfo_short": {"zh": "这是单集 NFO。请打开 tvshow.nfo 以载入整部剧集。",
                            "en": "This is a single-episode NFO. Please open tvshow.nfo to load the whole series."},
    "overwrite_confirm": {"zh": "读取将用 NFO 内容覆盖当前表单（未保存的修改会丢失）。\n是否继续？",
                          "en": "Loading will overwrite the current form with NFO content "
                                "(unsaved changes will be lost).\nContinue?"},
    "delete_nfo_title": {"zh": "删除 NFO", "en": "Delete NFO"},
    "delete_nfo_confirm": {"zh": "确定删除这个 NFO 文件吗？\n\n{name}\n\n此操作不可恢复。",
                           "en": "Delete this NFO file?\n\n{name}\n\nThis cannot be undone."},
    "delete_failed": {"zh": "删除失败", "en": "Delete Failed"},
    "nfo_deleted": {"zh": "已删除 NFO：{name}", "en": "Deleted NFO: {name}"},
    "new_confirm": {"zh": "新建", "en": "New"},
    "new_clear_confirm": {"zh": "当前内容将被清空，确定新建吗？", "en": "Current content will be cleared. Create new?"},
    "new_created": {"zh": "已新建{name}，请填写信息后保存。", "en": "Created new {name}; fill in info and save."},
    "open_failed": {"zh": "打开失败", "en": "Open Failed"},
    "opened": {"zh": "已打开：{path}", "en": "Opened: {path}"},
    "title_required": {"zh": "请先填写标题。", "en": "Please enter a title first."},
    "saved_status": {"zh": "已保存 {n} 个 NFO 文件到：{folder}", "en": "Saved {n} NFO file(s) to: {folder}"},
    "save_success": {"zh": "保存成功", "en": "Save Successful"},
    "saved_msg": {"zh": "已生成 {n} 个 NFO 文件：\n{files}", "en": "Generated {n} NFO file(s):\n{files}"},
    "save_failed": {"zh": "保存失败", "en": "Save Failed"},

    # ---- 图片/文本操作 ----
    "pick_image_first": {"zh": "请先选择一张图片。", "en": "Please select an image first."},
    "preview_win": {"zh": "大图预览 - {name}", "en": "Full Preview - {name}"},
    "pixel_info": {"zh": "{name}  |  {size} 像素", "en": "{name}  |  {size} pixels"},
    "cannot_preview": {"zh": "无法预览该图片。", "en": "Cannot preview this image."},
    "import_failed": {"zh": "图片导入失败（格式可能不受支持）。", "en": "Image import failed (format may be unsupported)."},
    "imported_cover": {"zh": "已将图片导入为封面：{name}", "en": "Imported image as cover: {name}"},
    "rotated_saved": {"zh": "已旋转并另存为：{name}", "en": "Rotated and saved as: {name}"},
    "rotate_failed": {"zh": "旋转失败。", "en": "Rotation failed."},
    "delete_image_title": {"zh": "删除", "en": "Delete"},
    "delete_image_confirm": {"zh": "确定删除图片：\n{name}\n（此操作不可恢复）",
                             "en": "Delete image?\n{name}\n(This cannot be undone)"},
    "image_deleted": {"zh": "已删除：{name}", "en": "Deleted: {name}"},
    "image_delete_failed": {"zh": "删除失败，文件可能被占用。", "en": "Delete failed; file may be in use."},
    "pick_txt_first": {"zh": "请先在左侧选中一个 txt 文件。", "en": "Please select a txt file on the left first."},
    "txt_empty": {"zh": "该 txt 文件没有可读取的内容。", "en": "This txt file has no readable content."},
    "import_synopsis_title": {"zh": "导入简介", "en": "Import Synopsis"},
    "synopsis_replace": {"zh": "简介框已有内容，是否用 txt 内容替换？", "en": "Plot field is not empty. Replace with txt content?"},
    "synopsis_imported": {"zh": "已从 {name} 导入简介。", "en": "Imported synopsis from {name}."},
    "pick_txt_preview": {"zh": "请先选中一个 txt 文件。", "en": "Please select a txt file first."},
    "synopsis_preview_win": {"zh": "简介预览 - {name}", "en": "Synopsis Preview - {name}"},

    # ---- 演职员/剧集操作 ----
    "pick_actor_first": {"zh": "请先选中一位演员。", "en": "Please select an actor first."},
    "pick_episode_first": {"zh": "请先选中一集。", "en": "Please select an episode first."},
    "tvshow_mode_confirm": {"zh": "电视剧", "en": "TV Show"},
    "switch_tv_confirm": {"zh": "当前是电影模式，是否切换为电视剧并继续？",
                          "en": "Currently in Movie mode. Switch to TV Show and continue?"},
    "no_videos": {"zh": "当前文件夹没有找到视频文件。", "en": "No video files found in the current folder."},
    "gen_episodes_title": {"zh": "生成剧集", "en": "Generate Episodes"},
    "gen_episodes_confirm": {"zh": "从 {n} 个视频文件生成 {n} 集（未识别 SxxExx 的按 S01E01 起顺序编号）。\n"
                                   "是否替换现有剧集列表？",
                             "en": "Generate {n} episodes from {n} video files "
                                   "(files without SxxExx are numbered sequentially from S01E01).\n"
                                   "Replace the existing episode list?"},
    "episodes_generated": {"zh": "已从视频文件生成 {n} 集。", "en": "Generated {n} episodes from video files."},

    # ---- 关于 ----
    "about_title": {"zh": "关于 MediaNFO", "en": "About MediaNFO"},
    "about_body": {
        "zh": "MediaNFO 媒体元数据编辑器 v1.1\n\n"
              "功能：\n"
              "• 手动新建 / 编辑电影与电视剧元数据\n"
              "• 生成兼容 Kodi / Emby / Jellyfin 的 .nfo 文件\n"
              "• 读取已有 .nfo 回填表单\n"
              "• 导入图片并自动命名为 poster/fanart 等封面\n"
              "• 从 txt 导入简介，或手工录入\n"
              "• 管理季数、集数与剧集列表\n"
              "• 中文 / English 双语界面\n\n"
              "不强制依赖 TMDB / IMDb，全部可手工填写。",
        "en": "MediaNFO Metadata Editor v1.1\n\n"
              "Features:\n"
              "• Create / edit movie and TV show metadata manually\n"
              "• Generate .nfo files compatible with Kodi / Emby / Jellyfin\n"
              "• Read existing .nfo files back into the form\n"
              "• Import images and name them as poster/fanart covers\n"
              "• Import synopsis from txt or enter it manually\n"
              "• Manage seasons, episode counts and episode lists\n"
              "• Chinese / English bilingual interface\n\n"
              "TMDB / IMDb are optional; everything can be filled in manually.",
    },
}

_current = LANG_ZH
_config_path = ""


def init(config_path):
    """初始化，config_path 为语言偏好配置文件路径。"""
    global _current, _config_path
    _config_path = config_path
    _load()


def _load():
    global _current
    try:
        with open(_config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("language") in (LANG_ZH, LANG_EN):
            _current = data["language"]
    except Exception:
        pass


def save():
    """保存当前语言偏好。"""
    try:
        with open(_config_path, "w", encoding="utf-8") as f:
            json.dump({"language": _current}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_language():
    return _current


def set_language(lang):
    global _current
    if lang in (LANG_ZH, LANG_EN):
        _current = lang
        save()


def t(key, **kwargs):
    """返回当前语言的文本；kwargs 用于 {name} 占位符格式化。"""
    entry = STRINGS.get(key)
    if not entry:
        return key
    text = entry.get(_current, entry.get(LANG_ZH, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def slot_label(slot, cn_name=""):
    """返回图片槽位的本地化显示名。"""
    if _current == LANG_EN:
        return SLOT_EN.get(slot, slot)
    return cn_name or slot

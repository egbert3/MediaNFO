# -*- coding: utf-8 -*-
"""主界面：文件夹扫描、元数据表单、剧集/演职员管理、图片封面与简介导入。"""
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from models import Movie, TVShow, Episode, Person, IMAGE_SLOTS, IMAGE_SLOT_NAMES
import nfo
import media

FONT = ("Microsoft YaHei UI", 9)
BOLD = ("Microsoft YaHei UI", 9, "bold")
TITLE_FONT = ("Microsoft YaHei UI", 14, "bold")

# 电影 / 电视剧共通字段，切换类型时保留这些数据
COMMON_FIELDS = [
    "title", "originaltitle", "sorttitle", "year", "releasedate", "runtime",
    "country", "studio", "mpaa", "rating", "votes", "tagline", "plot", "outline",
    "genres", "tags", "directors", "writers", "actors",
    "imdb_id", "tmdb_id", "tvdb_id", "folder", "nfo_path",
]


# ---------------- 通用弹窗 ----------------

class ActorDialog(tk.Toplevel):
    def __init__(self, parent, actor=None):
        super().__init__(parent)
        self.title("演职员")
        self.transient(parent)
        self.resizable(False, False)
        self.result = None
        actor = actor or Person()

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="姓名：", font=FONT).grid(row=0, column=0, sticky="e", pady=4)
        self.name = tk.StringVar(value=actor.name)
        ttk.Entry(frm, textvariable=self.name, width=30, font=FONT).grid(row=0, column=1, pady=4)
        ttk.Label(frm, text="角色：", font=FONT).grid(row=1, column=0, sticky="e", pady=4)
        self.role = tk.StringVar(value=actor.role)
        ttk.Entry(frm, textvariable=self.role, width=30, font=FONT).grid(row=1, column=1, pady=4)

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btns, text="确定", command=self.ok).pack(side="right", padx=4)
        ttk.Button(btns, text="取消", command=self.destroy).pack(side="right", padx=4)
        self.grab_set()
        self.name_entry_focus()

    def name_entry_focus(self):
        self.focus()

    def ok(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showwarning("提示", "姓名不能为空", parent=self)
            return
        self.result = Person(name=name, role=self.role.get().strip())
        self.destroy()


class EpisodeDialog(tk.Toplevel):
    def __init__(self, parent, episode=None, videos=None):
        super().__init__(parent)
        self.title("剧集信息")
        self.transient(parent)
        self.resizable(False, False)
        self.result = None
        ep = episode or Episode()
        videos = videos or []

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        self.season = tk.StringVar(value=str(ep.season))
        self.episode = tk.StringVar(value=str(ep.episode))
        self.titlev = tk.StringVar(value=ep.title)
        self.date = tk.StringVar(value=ep.releasedate)
        self.runtime = tk.StringVar(value=ep.runtime)
        self.plot = tk.Text(frm, height=5, width=42, font=FONT, wrap="word")
        self.video = tk.StringVar(value=ep.filename)

        rows = [
            ("季 (Season)：", self.season),
            ("集 (Episode)：", self.episode),
            ("标题：", self.titlev),
            ("首播日期：", self.date),
            ("时长(分钟)：", self.runtime),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(frm, text=label, font=FONT).grid(row=i, column=0, sticky="e", pady=3)
            ttk.Entry(frm, textvariable=var, width=32, font=FONT).grid(row=i, column=1, pady=3)

        ttk.Label(frm, text="视频文件：", font=FONT).grid(row=5, column=0, sticky="e", pady=3)
        vframe = ttk.Frame(frm)
        vframe.grid(row=5, column=1, sticky="w", pady=3)
        ttk.Entry(vframe, textvariable=self.video, width=24, font=FONT).pack(side="left")
        ttk.Button(vframe, text="...", width=3,
                   command=self.pick_video).pack(side="left", padx=3)

        ttk.Label(frm, text="简介：", font=FONT).grid(row=6, column=0, sticky="ne", pady=3)
        self.plot.grid(row=6, column=1, pady=3)
        if ep.plot:
            self.plot.insert("1.0", ep.plot)

        btns = ttk.Frame(frm)
        btns.grid(row=7, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btns, text="确定", command=self.ok).pack(side="right", padx=4)
        ttk.Button(btns, text="取消", command=self.destroy).pack(side="right", padx=4)
        self.grab_set()

    def pick_video(self):
        path = filedialog.askopenfilename(
            parent=self,
            filetypes=[("视频文件", "*.mkv *.mp4 *.avi *.mov *.ts *.m2ts *.wmv *.flv *.webm *.rmvb *.m4v"),
                       ("所有文件", "*.*")])
        if path:
            self.video.set(os.path.basename(path))

    def ok(self):
        def toint(v, default=1):
            try:
                return int(str(v).strip())
            except Exception:
                return default
        ep = Episode()
        ep.season = toint(self.season.get(), 1)
        ep.episode = toint(self.episode.get(), 1)
        ep.title = self.titlev.get().strip()
        ep.releasedate = self.date.get().strip()
        ep.runtime = self.runtime.get().strip()
        ep.plot = self.plot.get("1.0", tk.END).strip()
        ep.filename = self.video.get().strip()
        self.result = ep
        self.destroy()


# ---------------- 主程序 ----------------

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("MediaNFO 媒体元数据编辑器")
        self.root.geometry("1120x760")
        self.root.minsize(980, 640)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", font=FONT, padding=4)
        style.configure("TLabel", font=FONT)
        style.configure("Treeview", font=FONT, rowheight=24)
        style.configure("Treeview.Heading", font=BOLD)

        self.folder = ""
        self.current = Movie()
        self.mode = "movie"
        self.image_files = []
        self.text_files = []
        self.video_files = []
        self.nfo_files = []
        self.vars = {}
        self.texts = {}
        self.slot_vars = {}
        self.thumb_photo = None
        self.preview_photo = None

        self._build_toolbar()
        self._build_body()
        self._build_status()
        self.populate_form()
        self.set_status("就绪。请选择媒体文件夹，或新建电影 / 电视剧。")

    # ---------- 构建 ----------

    def _build_toolbar(self):
        bar = ttk.Frame(self.root, padding=(8, 8))
        bar.pack(fill="x")

        ttk.Button(bar, text="选择文件夹", command=self.select_folder).pack(side="left", padx=2)
        ttk.Button(bar, text="重新读取", command=self.reload_folder).pack(side="left", padx=2)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(bar, text="新建电影", command=lambda: self.new_media("movie")).pack(side="left", padx=2)
        ttk.Button(bar, text="新建电视剧", command=lambda: self.new_media("tvshow")).pack(side="left", padx=2)
        self.switch_btn = ttk.Button(bar, text="切换为电视剧", command=self.toggle_mode)
        self.switch_btn.pack(side="left", padx=2)
        ttk.Button(bar, text="打开 NFO", command=self.open_nfo).pack(side="left", padx=2)
        ttk.Button(bar, text="保存 NFO", command=self.save_nfo).pack(side="left", padx=2)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        self.mode_label = ttk.Label(bar, text="当前：电影", font=BOLD, foreground="#2d6cdf")
        self.mode_label.pack(side="right", padx=6)
        ttk.Button(bar, text="关于", command=self.show_about).pack(side="right", padx=2)

        fbar = ttk.Frame(self.root, padding=(8, 0, 8, 6))
        fbar.pack(fill="x")
        ttk.Label(fbar, text="媒体文件夹：", font=FONT).pack(side="left")
        self.folder_var = tk.StringVar()
        ttk.Entry(fbar, textvariable=self.folder_var, font=FONT).pack(
            side="left", fill="x", expand=True, padx=4)

    def _build_body(self):
        body = ttk.Frame(self.root, padding=(8, 0, 8, 4))
        body.pack(fill="both", expand=True)

        # 左侧文件面板
        left = ttk.LabelFrame(body, text="当前文件夹内容", padding=6)
        left.pack(side="left", fill="y", padx=(0, 6))
        left.configure(width=250)

        ttk.Label(left, text="图片：", font=BOLD).pack(anchor="w")
        self.image_list = tk.Listbox(left, height=7, width=30, font=FONT,
                                     selectmode=tk.SINGLE, exportselection=False)
        self.image_list.pack(fill="x", pady=(2, 4))
        self.image_list.bind("<<ListboxSelect>>", self.on_image_select)

        thumb_frame = ttk.Frame(left)
        thumb_frame.pack(fill="x", pady=2)
        self.thumb_label = tk.Label(thumb_frame, text="（选择图片预览）",
                                    width=24, height=10, relief="groove",
                                    background="#f2f2f2")
        self.thumb_label.pack(side="left")

        img_btns = ttk.Frame(left)
        img_btns.pack(fill="x", pady=4)
        ttk.Button(img_btns, text="大图预览", command=self.preview_image).pack(fill="x", pady=2)
        ttk.Button(img_btns, text="旋转 90°", command=self.rotate_image).pack(fill="x", pady=2)
        ttk.Button(img_btns, text="删除图片", command=self.delete_image).pack(fill="x", pady=2)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=6)
        ttk.Label(left, text="简介文档 (.txt)：", font=BOLD).pack(anchor="w")
        self.text_list = tk.Listbox(left, height=4, width=30, font=FONT,
                                    selectmode=tk.SINGLE, exportselection=False)
        self.text_list.pack(fill="x", pady=(2, 4))
        ttk.Button(left, text="导入选中简介到简介框", command=self.import_synopsis).pack(fill="x", pady=2)
        ttk.Button(left, text="预览简介", command=self.preview_text).pack(fill="x", pady=2)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=6)
        ttk.Label(left, text="视频文件（用于剧集）：", font=BOLD).pack(anchor="w")
        self.video_count_label = ttk.Label(left, text="0 个视频文件")
        self.video_count_label.pack(anchor="w", pady=2)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=6)
        ttk.Label(left, text="NFO 刮削信息（点选读取 / 可删除）：", font=BOLD).pack(anchor="w")
        self.nfo_list = tk.Listbox(left, height=4, width=30, font=FONT,
                                   selectmode=tk.SINGLE, exportselection=False)
        self.nfo_list.pack(fill="x", pady=(2, 4))
        self.nfo_list.bind("<<ListboxSelect>>", self.on_nfo_select)
        nfo_btns = ttk.Frame(left)
        nfo_btns.pack(fill="x", pady=2)
        ttk.Button(nfo_btns, text="读取选中", command=self.read_selected_nfo).pack(
            side="left", fill="x", expand=True, padx=(0, 2))
        ttk.Button(nfo_btns, text="删除选中", command=self.delete_selected_nfo).pack(
            side="left", fill="x", expand=True, padx=(2, 0))

        # 右侧表单
        right = ttk.Frame(body)
        right.pack(side="right", fill="both", expand=True)
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill="both", expand=True)

        self.tab_basic = self._add_scrollable_tab("基本信息")
        self.tab_plot = self._add_scrollable_tab("简介与分类")
        self.tab_people = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_people, text="演职员")
        self.tab_episodes = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_episodes, text="剧集信息（电视剧）")
        self.tab_images = self._add_scrollable_tab("图片与封面")

        self._build_basic_tab()
        self._build_plot_tab()
        self._build_people_tab()
        self._build_episodes_tab()
        self._build_images_tab()

    def _build_status(self):
        bar = ttk.Frame(self.root, padding=(8, 6))
        bar.pack(fill="x")
        self.status_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.status_var, font=FONT,
                  foreground="#555555").pack(side="left")

    def set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()

    def _add_scrollable_tab(self, title):
        container = ttk.Frame(self.notebook)
        canvas = tk.Canvas(container, highlightthickness=0, background="#ffffff")
        scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, padding=10)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        # 仅当鼠标位于该标签内时才滚动，避免所有标签一起动
        def wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        container.bind("<MouseWheel>", wheel)
        inner.bind("<MouseWheel>", wheel)
        self.notebook.add(container, text=title)
        return inner

    # ---------- 表单字段辅助 ----------

    def add_field(self, parent, label, key, row, col=0, width=24):
        ttk.Label(parent, text=label, font=FONT).grid(row=row, column=col, sticky="e", padx=4, pady=4)
        var = tk.StringVar()
        ttk.Entry(parent, textvariable=var, width=width, font=FONT).grid(
            row=row, column=col + 1, sticky="w", padx=4, pady=4)
        self.vars[key] = var
        return var

    def add_text(self, parent, label, key, row, height=4, width=58, col=0):
        ttk.Label(parent, text=label, font=BOLD).grid(row=row, column=col, sticky="nw", padx=4, pady=(8, 2))
        frame = ttk.Frame(parent)
        frame.grid(row=row + 1, column=col, columnspan=2, sticky="w", padx=4, pady=2)
        txt = tk.Text(frame, height=height, width=width, font=FONT, wrap="word")
        txt.pack(side="left")
        sb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        sb.pack(side="right", fill="y")
        txt.configure(yscrollcommand=sb.set)
        self.texts[key] = txt
        return txt

    # ---------- 各选项卡 ----------

    def _build_basic_tab(self):
        p = self.tab_basic
        frm = ttk.LabelFrame(p, text="标题与发行", padding=10)
        frm.pack(fill="x", pady=6)
        self.add_field(frm, "标题 *", "title", 0, 0, 34)
        self.add_field(frm, "原标题", "originaltitle", 1, 0, 34)
        self.add_field(frm, "排序标题", "sorttitle", 2, 0, 34)
        self.add_field(frm, "年份", "year", 3, 0)
        self.add_field(frm, "发行日期", "releasedate", 3, 2)
        self.add_field(frm, "时长(分钟)", "runtime", 4, 0)
        self.add_field(frm, "分级 MPAA", "mpaa", 4, 2)
        self.add_field(frm, "国家/地区", "country", 5, 0)
        self.add_field(frm, "工作室", "studio", 5, 2)

        frm2 = ttk.LabelFrame(p, text="评分与外部 ID（可选，不强制）", padding=10)
        frm2.pack(fill="x", pady=6)
        self.add_field(frm2, "评分", "rating", 0, 0)
        self.add_field(frm2, "投票数", "votes", 0, 2)
        self.add_field(frm2, "IMDb ID", "imdb_id", 1, 0)
        self.add_field(frm2, "TMDB ID", "tmdb_id", 1, 2)
        self.add_field(frm2, "TVDB ID", "tvdb_id", 2, 0)

    def _build_plot_tab(self):
        p = self.tab_plot
        self.add_text(p, "标语 / Tagline", "tagline", 0, height=2)
        self.add_text(p, "简介 / Plot（可从 txt 导入）", "plot", 2, height=9)
        self.add_text(p, "大纲 / Outline", "outline", 4, height=4)
        self.add_text(p, "类型 / Genre（每行一个）", "genres", 6, height=4)
        self.add_text(p, "标签 / Tag（每行一个）", "tags", 8, height=4)

    def _build_people_tab(self):
        p = self.tab_people
        self.add_text(p, "导演（每行一位）", "directors", 0, height=3)
        self.add_text(p, "编剧（每行一位）", "writers", 2, height=3)

        frm = ttk.LabelFrame(p, text="演员", padding=8)
        frm.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=4, pady=8)
        cols = ("name", "role")
        self.actor_tree = ttk.Treeview(frm, columns=cols, show="headings", height=10)
        self.actor_tree.heading("name", text="姓名")
        self.actor_tree.heading("role", text="角色")
        self.actor_tree.column("name", width=260)
        self.actor_tree.column("role", width=300)
        self.actor_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frm, orient="vertical", command=self.actor_tree.yview)
        sb.pack(side="right", fill="y")
        self.actor_tree.configure(yscrollcommand=sb.set)
        self.actor_tree.bind("<Double-1>", lambda e: self.edit_actor())

        btns = ttk.Frame(p)
        btns.grid(row=5, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        ttk.Button(btns, text="添加演员", command=self.add_actor).pack(side="left", padx=2)
        ttk.Button(btns, text="编辑", command=self.edit_actor).pack(side="left", padx=2)
        ttk.Button(btns, text="删除", command=self.delete_actor).pack(side="left", padx=2)
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)
        p.rowconfigure(4, weight=1)

    def _build_episodes_tab(self):
        p = self.tab_episodes
        top = ttk.Frame(p, padding=8)
        top.grid(row=0, column=0, sticky="ew")
        self.add_field(top, "总季数", "season_count", 0, 0, 8)
        self.add_field(top, "总集数", "episode_count", 0, 2, 8)
        ttk.Button(top, text="从视频文件名生成剧集",
                   command=self.generate_episodes).grid(row=0, column=4, padx=4)

        frm = ttk.LabelFrame(p, text="剧集列表（双击编辑）", padding=8)
        frm.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        cols = ("season", "ep", "title", "video")
        self.ep_tree = ttk.Treeview(frm, columns=cols, show="headings", height=12)
        for c, text, w in [("season", "季", 60), ("ep", "集", 60),
                           ("title", "标题", 260), ("video", "视频文件", 240)]:
            self.ep_tree.heading(c, text=text)
            self.ep_tree.column(c, width=w)
        self.ep_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frm, orient="vertical", command=self.ep_tree.yview)
        sb.pack(side="right", fill="y")
        self.ep_tree.configure(yscrollcommand=sb.set)
        self.ep_tree.bind("<Double-1>", lambda e: self.edit_episode())

        btns = ttk.Frame(p)
        btns.grid(row=2, column=0, sticky="w", padx=8, pady=8)
        ttk.Button(btns, text="添加一集", command=self.add_episode).pack(side="left", padx=2)
        ttk.Button(btns, text="编辑", command=self.edit_episode).pack(side="left", padx=2)
        ttk.Button(btns, text="删除", command=self.delete_episode).pack(side="left", padx=2)
        ttk.Button(btns, text="按季/集排序", command=self.sort_episodes).pack(side="left", padx=2)
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)

    def _build_images_tab(self):
        p = self.tab_images
        ttk.Label(p, text="图片槽位（输入或导入文件名，将写入 NFO 供媒体库识别）",
                  font=BOLD).pack(anchor="w", pady=4)
        ttk.Label(p, text="规范命名：poster.jpg（主海报）、fanart.jpg（背景）、banner.jpg（横幅）等",
                  font=FONT, foreground="#666666").pack(anchor="w", pady=(0, 8))

        frm = ttk.LabelFrame(p, text="封面槽位", padding=10)
        frm.pack(fill="x")
        for i, (slot, cn) in enumerate(IMAGE_SLOTS):
            row = i
            ttk.Label(frm, text="%s (%s)：" % (cn, slot), font=FONT).grid(
                row=row, column=0, sticky="e", padx=4, pady=3)
            var = tk.StringVar()
            self.slot_vars[slot] = var
            ttk.Entry(frm, textvariable=var, width=26, font=FONT).grid(
                row=row, column=1, sticky="w", padx=4, pady=3)
            ttk.Button(frm, text="从选中图片导入",
                       command=lambda s=slot: self.import_cover(s)).grid(
                row=row, column=2, padx=4, pady=3)
            ttk.Button(frm, text="清除",
                       command=lambda s=slot: self.clear_slot(s)).grid(
                row=row, column=3, padx=4, pady=3)

        note = ttk.Label(p, text="提示：先在左侧“当前文件夹内容”选中一张图片，再点对应槽位的“从选中图片导入”。\n"
                                 "导入会把图片转换为 JPG 并按槽位命名（如 poster.jpg），原图不会删除。",
                         font=FONT, foreground="#666666", justify="left")
        note.pack(anchor="w", pady=10)

    # ---------- 数据绑定 ----------

    def populate_form(self):
        m = self.current
        values = {
            "title": m.title, "originaltitle": m.originaltitle, "sorttitle": m.sorttitle,
            "year": m.year, "releasedate": m.releasedate, "runtime": m.runtime,
            "mpaa": m.mpaa, "country": m.country, "studio": m.studio,
            "rating": m.rating, "votes": m.votes,
            "imdb_id": m.imdb_id, "tmdb_id": m.tmdb_id, "tvdb_id": m.tvdb_id,
            "season_count": str(getattr(m, "season_count", 0) or 0),
            "episode_count": str(getattr(m, "episode_count", 0) or 0),
        }
        for key, value in values.items():
            if key in self.vars:
                self.vars[key].set(value or "")

        text_values = {
            "tagline": m.tagline, "plot": m.plot, "outline": m.outline,
            "genres": "\n".join(m.genres), "tags": "\n".join(m.tags),
            "directors": "\n".join(m.directors), "writers": "\n".join(m.writers),
        }
        for key, value in text_values.items():
            if key in self.texts:
                txt = self.texts[key]
                txt.delete("1.0", tk.END)
                if value:
                    txt.insert("1.0", value)

        for slot, var in self.slot_vars.items():
            var.set(m.get_image(slot))

        self.refresh_actor_tree()
        self.refresh_episode_tree()
        self.mode_label.configure(
            text="当前：%s" % ("电视剧" if self.mode == "tvshow" else "电影"))
        self._sync_switch_btn()

    def _sync_switch_btn(self):
        """切换按钮显示目标类型。"""
        if hasattr(self, "switch_btn"):
            self.switch_btn.configure(
                text="切换为电影" if self.mode == "tvshow" else "切换为电视剧")

    def collect_form(self):
        m = self.current
        def g(key):
            return self.vars[key].get().strip() if key in self.vars else ""
        def t(key):
            return self.texts[key].get("1.0", tk.END).strip() if key in self.texts else ""
        def lines(key):
            return [x.strip() for x in t(key).splitlines() if x.strip()]

        m.title = g("title")
        m.originaltitle = g("originaltitle")
        m.sorttitle = g("sorttitle")
        m.year = g("year")
        m.releasedate = g("releasedate")
        m.runtime = g("runtime")
        m.mpaa = g("mpaa")
        m.country = g("country")
        m.studio = g("studio")
        m.rating = g("rating")
        m.votes = g("votes")
        m.imdb_id = g("imdb_id")
        m.tmdb_id = g("tmdb_id")
        m.tvdb_id = g("tvdb_id")
        m.tagline = t("tagline")
        m.plot = t("plot")
        m.outline = t("outline")
        m.genres = lines("genres")
        m.tags = lines("tags")
        m.directors = lines("directors")
        m.writers = lines("writers")

        for slot, var in self.slot_vars.items():
            m.set_image(slot, var.get().strip())

        if isinstance(m, TVShow):
            def toint(v):
                try:
                    return int(v)
                except Exception:
                    return 0
            m.season_count = toint(g("season_count"))
            m.episode_count = toint(g("episode_count"))

    # ---------- 文件夹与模式 ----------

    def select_folder(self):
        folder = filedialog.askdirectory(parent=self.root, title="选择媒体文件夹")
        if not folder:
            return
        self.load_folder(folder)

    def reload_folder(self):
        """重新扫描当前文件夹并重新读取其中的 NFO（丢弃未保存的表单修改）。"""
        if not self.folder:
            messagebox.showinfo("提示", "请先选择媒体文件夹。", parent=self.root)
            return
        if not messagebox.askyesno(
                "重新读取",
                "将从文件夹重新扫描并读取 NFO，未保存的修改会丢失。\n是否继续？",
                parent=self.root):
            return
        self.load_folder(self.folder)

    def load_folder(self, folder):
        """加载一个媒体文件夹：先彻底清空旧内容，再扫描并自动读取 NFO。"""
        self.folder = folder
        self.folder_var.set(folder)

        # 关键：先重置为当前模式的空白对象，避免上一个文件夹的信息残留
        self.current = (TVShow(folder=folder) if self.mode == "tvshow"
                        else Movie(folder=folder))
        self.populate_form()
        self.scan_folder()

        # 自动加载已有 NFO（标准命名优先，其次任意 movie/tvshow 命名的刮削信息）
        nfo_path = nfo.find_best_main_nfo(folder)
        if nfo_path:
            try:
                obj = nfo.parse_nfo(nfo_path)
                if isinstance(obj, (Movie, TVShow)):
                    self.current = obj
                    self.mode = obj.media_type
                    self.populate_form()
                    self.set_status("已读取刮削信息：%s" % os.path.basename(nfo_path))
                    return
                self.set_status("检测到剧集 NFO，但未自动载入（可用“打开 NFO”选择）")
            except Exception as e:
                self.set_status("读取 NFO 失败：%s" % e)
        else:
            # 未发现 NFO：用文件夹名作为标题（对象与表单同步）
            default_title = os.path.basename(os.path.normpath(folder))
            self.current.title = default_title
            self.vars["title"].set(default_title)
            self.set_status("已选择文件夹：%s（未发现 NFO，可新建）" % folder)

    def scan_folder(self):
        self.image_files = media.list_images(self.folder)
        self.text_files = media.list_texts(self.folder)
        self.video_files = media.list_videos(self.folder)
        self.nfo_files = nfo.find_nfo_candidates(self.folder)

        self.image_list.delete(0, tk.END)
        for p in self.image_files:
            self.image_list.insert(tk.END, os.path.basename(p))
        self.text_list.delete(0, tk.END)
        for p in self.text_files:
            self.text_list.insert(tk.END, os.path.basename(p))
        self.video_count_label.configure(text="%d 个视频文件" % len(self.video_files))

        # 列出 NFO 刮削信息：类型 + 文件名 + 标题
        self.nfo_list.delete(0, tk.END)
        kind_cn = {"movie": "电影", "tvshow": "剧集", "episode": "单集", "unknown": "未知"}
        for info in self.nfo_files:
            label = "[%s] %s" % (kind_cn.get(info["kind"], info["kind"]), info["name"])
            if info["title"]:
                label += " - %s" % info["title"]
            self.nfo_list.insert(tk.END, label)

        self.thumb_label.configure(image="", text="（选择图片预览）")
        self.thumb_photo = None

    # ---------- NFO 刮削信息操作 ----------

    def selected_nfo(self):
        sel = self.nfo_list.curselection()
        if not sel or sel[0] >= len(self.nfo_files):
            return None
        return self.nfo_files[sel[0]]

    def on_nfo_select(self, event=None):
        """点选 NFO 即读取到表单（单集除外，仅提示）。"""
        info = self.selected_nfo()
        if not info:
            return
        self._load_nfo_path(info["path"])

    def read_selected_nfo(self):
        info = self.selected_nfo()
        if not info:
            messagebox.showinfo("提示", "请先在左侧选中一个 NFO 文件。", parent=self.root)
            return
        self._load_nfo_path(info["path"])

    def _load_nfo_path(self, path):
        """把一个指定的 NFO 读取到表单。"""
        try:
            obj = nfo.parse_nfo(path)
        except Exception as e:
            messagebox.showerror("读取失败", "解析 NFO 出错：\n%s" % e, parent=self.root)
            return
        if isinstance(obj, Episode):
            messagebox.showinfo("提示",
                                "这是单集 NFO，包含的是某一集的剧集信息。\n"
                                "请打开主 NFO（tvshow.nfo）以载入整部剧集。",
                                parent=self.root)
            return
        # 有未保存修改时先确认
        if self.current and self.current.title and not self._is_unchanged(obj):
            if not messagebox.askyesno(
                    "读取 NFO",
                    "读取将用 NFO 内容覆盖当前表单（未保存的修改会丢失）。\n是否继续？",
                    parent=self.root):
                return
        self.current = obj
        self.mode = obj.media_type
        self.populate_form()
        self.set_status("已读取刮削信息：%s" % os.path.basename(path))

    def _is_unchanged(self, new_obj):
        """简单判断当前表单是否仍等于新读取的对象（无未保存修改）。"""
        return (self.current.title == new_obj.title
                and self.current.year == new_obj.year)

    def delete_selected_nfo(self):
        info = self.selected_nfo()
        if not info:
            messagebox.showinfo("提示", "请先在左侧选中一个 NFO 文件。", parent=self.root)
            return
        if not messagebox.askyesno(
                "删除 NFO",
                "确定删除这个 NFO 文件吗？\n\n%s\n\n此操作不可恢复。" % info["name"],
                parent=self.root):
            return
        try:
            os.remove(info["path"])
        except Exception as e:
            messagebox.showerror("删除失败", str(e), parent=self.root)
            return
        # 若删的是当前正在编辑的 NFO，清掉关联路径避免覆盖到别处
        cur_path = getattr(self.current, "nfo_path", "")
        if cur_path and os.path.normcase(cur_path) == os.path.normcase(info["path"]):
            self.current.nfo_path = ""
        self.scan_folder()
        self.set_status("已删除 NFO：%s" % info["name"])

    def new_media(self, media_type):
        if self.current and self.current.title:
            if not messagebox.askyesno("新建", "当前内容将被清空，确定新建吗？", parent=self.root):
                return
        self.mode = media_type
        self.current = Movie(folder=self.folder) if media_type == "movie" else TVShow(folder=self.folder)
        self.populate_form()
        self.set_status("已新建%s，请填写信息后保存。" %
                        ("电视剧" if media_type == "tvshow" else "电影"))

    def open_nfo(self):
        path = filedialog.askopenfilename(
            parent=self.root,
            filetypes=[("NFO 文件", "*.nfo"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            obj = nfo.parse_nfo(path)
        except Exception as e:
            messagebox.showerror("打开失败", "解析 NFO 出错：\n%s" % e, parent=self.root)
            return
        if isinstance(obj, Episode):
            messagebox.showinfo("提示", "这是单集 NFO。请打开 tvshow.nfo 以载入整部剧集。",
                                parent=self.root)
            return
        self.current = obj
        self.mode = obj.media_type
        self.folder = obj.folder or self.folder
        self.folder_var.set(self.folder)
        self.scan_folder()
        self.populate_form()
        self.set_status("已打开：%s" % path)

    def save_nfo(self):
        self.collect_form()
        if not self.current.title:
            messagebox.showwarning("提示", "请先填写标题。", parent=self.root)
            return
        if not self.current.folder:
            folder = filedialog.askdirectory(parent=self.root, title="选择保存位置")
            if not folder:
                return
            self.current.folder = folder
            self.folder = folder
            self.folder_var.set(folder)
        if not os.path.isdir(self.current.folder):
            os.makedirs(self.current.folder, exist_ok=True)

        try:
            if isinstance(self.current, TVShow):
                self.current.sync_counts()
                paths = nfo.save_tvshow(self.current)
            else:
                paths = [nfo.save_movie(self.current)]
            self.set_status("已保存 %d 个 NFO 文件到：%s" % (len(paths), self.current.folder))
            messagebox.showinfo("保存成功",
                                "已生成 %d 个 NFO 文件：\n%s" %
                                (len(paths), "\n".join(os.path.basename(p) for p in paths)),
                                parent=self.root)
            self.scan_folder()
        except Exception as e:
            messagebox.showerror("保存失败", str(e), parent=self.root)

    # ---------- 图片操作 ----------

    def selected_image(self):
        sel = self.image_list.curselection()
        if not sel or sel[0] >= len(self.image_files):
            return ""
        return self.image_files[sel[0]]

    def on_image_select(self, event=None):
        path = self.selected_image()
        if not path:
            return
        thumb = media.make_thumbnail(path)
        if thumb:
            self.thumb_photo = tk.PhotoImage(file=thumb)
            self.thumb_label.configure(image=self.thumb_photo, text="")
        else:
            self.thumb_label.configure(image="", text="预览失败")

    def preview_image(self):
        path = self.selected_image()
        if not path:
            messagebox.showinfo("提示", "请先选择一张图片。", parent=self.root)
            return
        preview = media.make_preview(path)
        if not preview:
            messagebox.showerror("错误", "无法预览该图片。", parent=self.root)
            return
        win = tk.Toplevel(self.root)
        win.title("大图预览 - %s" % os.path.basename(path))
        win.transient(self.root)
        img = tk.PhotoImage(file=preview)
        label = tk.Label(win, image=img)
        label.pack(padx=10, pady=10)
        label.image = img
        ttk.Label(win, text="%s  |  %s 像素" %
                  (os.path.basename(path), media.image_size(path)), font=FONT).pack(pady=(0, 8))

    def import_cover(self, slot):
        path = self.selected_image()
        if not path:
            messagebox.showinfo("提示", "请先在左侧选中一张图片。", parent=self.root)
            return
        if not self.current.folder:
            messagebox.showinfo("提示", "请先选择媒体文件夹。", parent=self.root)
            return
        dest = media.import_as_cover(path, self.current.folder, slot)
        if not dest:
            messagebox.showerror("失败", "图片导入失败（格式可能不受支持）。", parent=self.root)
            return
        name = os.path.basename(dest)
        self.current.set_image(slot, name)
        self.slot_vars[slot].set(name)
        self.scan_folder()
        self.set_status("已将图片导入为封面：%s" % name)

    def clear_slot(self, slot):
        self.current.set_image(slot, "")
        self.slot_vars[slot].set("")

    def rotate_image(self):
        path = self.selected_image()
        if not path:
            messagebox.showinfo("提示", "请先选择一张图片。", parent=self.root)
            return
        base, ext = os.path.splitext(path)
        dest = base + "_rot" + ".jpg"
        result = media.rotate_copy(path, dest, 90)
        if result:
            self.scan_folder()
            self.set_status("已旋转并另存为：%s" % os.path.basename(dest))
        else:
            messagebox.showerror("失败", "旋转失败。", parent=self.root)

    def delete_image(self):
        path = self.selected_image()
        if not path:
            messagebox.showinfo("提示", "请先选择一张图片。", parent=self.root)
            return
        if not messagebox.askyesno("删除", "确定删除图片：\n%s\n（此操作不可恢复）" %
                                   os.path.basename(path), parent=self.root):
            return
        if media.delete_file(path):
            self.scan_folder()
            self.set_status("已删除：%s" % os.path.basename(path))
        else:
            messagebox.showerror("失败", "删除失败，文件可能被占用。", parent=self.root)

    # ---------- 简介操作 ----------

    def selected_text(self):
        sel = self.text_list.curselection()
        if not sel or sel[0] >= len(self.text_files):
            return ""
        return self.text_files[sel[0]]

    def import_synopsis(self):
        path = self.selected_text()
        if not path:
            messagebox.showinfo("提示", "请先在左侧选中一个 txt 文件。", parent=self.root)
            return
        content = media.read_text(path)
        if not content.strip():
            messagebox.showinfo("提示", "该 txt 文件没有可读取的内容。", parent=self.root)
            return
        current = self.texts["plot"].get("1.0", tk.END).strip()
        if current and not messagebox.askyesno("导入简介",
                                               "简介框已有内容，是否用 txt 内容替换？",
                                               parent=self.root):
            return
        self.texts["plot"].delete("1.0", tk.END)
        self.texts["plot"].insert("1.0", content)
        self.set_status("已从 %s 导入简介。" % os.path.basename(path))

    def preview_text(self):
        path = self.selected_text()
        if not path:
            messagebox.showinfo("提示", "请先选中一个 txt 文件。", parent=self.root)
            return
        content = media.read_text(path)
        win = tk.Toplevel(self.root)
        win.title("简介预览 - %s" % os.path.basename(path))
        win.transient(self.root)
        txt = tk.Text(win, height=20, width=70, font=FONT, wrap="word")
        txt.pack(padx=10, pady=10, fill="both", expand=True)
        txt.insert("1.0", content)
        txt.configure(state="disabled")

    # ---------- 演职员 ----------

    def refresh_actor_tree(self):
        self.actor_tree.delete(*self.actor_tree.get_children())
        for a in self.current.actors:
            self.actor_tree.insert("", tk.END, values=(a.name, a.role))

    def add_actor(self):
        dlg = ActorDialog(self.root)
        self.root.wait_window(dlg)
        if dlg.result:
            self.current.actors.append(dlg.result)
            self.refresh_actor_tree()

    def edit_actor(self):
        sel = self.actor_tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选中一位演员。", parent=self.root)
            return
        idx = self.actor_tree.index(sel[0])
        dlg = ActorDialog(self.root, self.current.actors[idx])
        self.root.wait_window(dlg)
        if dlg.result:
            self.current.actors[idx] = dlg.result
            self.refresh_actor_tree()

    def delete_actor(self):
        sel = self.actor_tree.selection()
        if not sel:
            return
        idx = self.actor_tree.index(sel[0])
        del self.current.actors[idx]
        self.refresh_actor_tree()

    # ---------- 剧集 ----------

    def refresh_episode_tree(self):
        self.ep_tree.delete(*self.ep_tree.get_children())
        episodes = getattr(self.current, "episodes", [])
        for ep in episodes:
            self.ep_tree.insert("", tk.END, values=(
                ep.season, ep.episode, ep.title, ep.filename))

    def toggle_mode(self):
        """在电影 / 电视剧之间切换，保留所有已填写的信息。"""
        target_type = "movie" if self.mode == "tvshow" else "tvshow"
        target_name = "电影" if target_type == "movie" else "电视剧"

        # 先把表单当前内容收集到旧对象，确保未提交的输入也不丢失
        self.collect_form()
        old = self.current

        # 构造新类型对象
        if target_type == "tvshow":
            new = TVShow(folder=self.folder)
            # 继承旧的季/集数字段（如果有）
            new.season_count = getattr(old, "season_count", 0)
            new.episode_count = getattr(old, "episode_count", 0)
            new.episodes = list(getattr(old, "episodes", []))
        else:
            new = Movie(folder=self.folder)

        # 复制共通字段（列表和字典用副本，避免两对象共享引用）
        for key in COMMON_FIELDS:
            value = getattr(old, key, None)
            if isinstance(value, list):
                value = list(value)
            elif isinstance(value, dict):
                value = dict(value)
            setattr(new, key, value)
        new.images = dict(getattr(old, "images", {}) or {})
        if target_type == "tvshow":
            new.season_count = getattr(old, "season_count", 0)
            new.episode_count = getattr(old, "episode_count", 0)
            new.episodes = list(getattr(old, "episodes", []))

        self.current = new
        self.mode = target_type
        self.populate_form()
        self.set_status("已切换为%s，原有信息已保留。" % target_name)

    def _ensure_tvshow(self):
        if not isinstance(self.current, TVShow):
            if not messagebox.askyesno("电视剧", "当前是电影模式，是否切换为电视剧并继续？",
                                       parent=self.root):
                return False
            self.toggle_mode()
        return True

    def add_episode(self):
        if not self._ensure_tvshow():
            return
        dlg = EpisodeDialog(self.root, videos=self.video_files)
        self.root.wait_window(dlg)
        if dlg.result:
            self.current.episodes.append(dlg.result)
            self.refresh_episode_tree()

    def edit_episode(self):
        if not self._ensure_tvshow():
            return
        sel = self.ep_tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选中一集。", parent=self.root)
            return
        idx = self.ep_tree.index(sel[0])
        dlg = EpisodeDialog(self.root, self.current.episodes[idx], self.video_files)
        self.root.wait_window(dlg)
        if dlg.result:
            self.current.episodes[idx] = dlg.result
            self.refresh_episode_tree()

    def delete_episode(self):
        sel = self.ep_tree.selection()
        if not sel:
            return
        idx = self.ep_tree.index(sel[0])
        del self.current.episodes[idx]
        self.refresh_episode_tree()

    def sort_episodes(self):
        if not hasattr(self.current, "episodes"):
            return
        self.current.episodes.sort(key=lambda e: (e.season, e.episode))
        self.refresh_episode_tree()

    def generate_episodes(self):
        if not self._ensure_tvshow():
            return
        if not self.video_files:
            messagebox.showinfo("提示", "当前文件夹没有找到视频文件。", parent=self.root)
            return
        episodes = []
        counter = 1
        for path in self.video_files:
            name = os.path.basename(path)
            m = re.search(r"[Ss](\d{1,2})[Ee](\d{1,3})", name)
            if m:
                season, epnum = int(m.group(1)), int(m.group(2))
            else:
                season, epnum = 1, counter
            episodes.append(Episode(season=season, episode=epnum,
                                    filename=name))
            counter += 1
        if not messagebox.askyesno("生成剧集",
                                   "从 %d 个视频文件生成 %d 集（未识别 SxxExx 的按 S01E01 起顺序编号）。\n"
                                   "是否替换现有剧集列表？" % (len(self.video_files), len(episodes)),
                                   parent=self.root):
            return
        self.current.episodes = episodes
        self.current.season_count = max((e.season for e in episodes), default=0)
        self.current.episode_count = len(episodes)
        self.vars["season_count"].set(str(self.current.season_count))
        self.vars["episode_count"].set(str(self.current.episode_count))
        self.refresh_episode_tree()
        self.set_status("已从视频文件生成 %d 集。" % len(episodes))

    # ---------- 关于 ----------

    def show_about(self):
        messagebox.showinfo(
            "关于 MediaNFO",
            "MediaNFO 媒体元数据编辑器 v1.0\n\n"
            "功能：\n"
            "• 手动新建 / 编辑电影与电视剧元数据\n"
            "• 生成兼容 Kodi / Emby / Jellyfin 的 .nfo 文件\n"
            "• 读取已有 .nfo 回填表单\n"
            "• 导入图片并自动命名为 poster/fanart 等封面\n"
            "• 从 txt 导入简介，或手工录入\n"
            "• 管理季数、集数与剧集列表\n\n"
            "不强制依赖 TMDB / IMDb，全部可手工填写。",
            parent=self.root)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()

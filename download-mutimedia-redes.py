import os
import io
import requests
import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Toplevel, IntVar
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import pyperclip
from PIL import Image, ImageTk

image_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
video_exts = {"mp4", "mkv", "webm", "mov", "avi"}
audio_exts = {"mp3", "m4a", "wav", "flac", "aac", "ogg"}

def gather_media_info(url):
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    items = []
    def handle_entry(e):
        ext = (e.get("ext") or "").lower()
        if ext in image_exts:
            u = e.get("url") or e.get("thumbnail") or e.get("display_id") or e.get("webpage_url")
            items.append({"type":"image","url":u,"ext":ext,"title":e.get("title") or e.get("id")})
            return
        if ext in video_exts or "video" in e.get("acodec","") or e.get("vcodec") is not None:
            formats = e.get("formats") or []
            best = None
            for f in reversed(formats):
                if f.get("url"):
                    best = f
                    break
            u = e.get("url") or (best.get("url") if best else None) or e.get("webpage_url")
            items.append({"type":"video","url":u,"ext":ext or "mp4","title":e.get("title") or e.get("id")})
            return
        if ext in audio_exts or "audio" in e.get("acodec",""):
            u = e.get("url") or e.get("webpage_url")
            items.append({"type":"audio","url":u,"ext":ext or "mp3","title":e.get("title") or e.get("id")})
            return
        # fallback: check thumbnails
        thumbs = e.get("thumbnails") or []
        if thumbs:
            thumb = thumbs[-1].get("url")
            items.append({"type":"image","url":thumb,"ext":"jpg","title":e.get("title") or e.get("id")})
    if info is None:
        return []
    if info.get("entries"):
        for ent in info["entries"]:
            if ent is None:
                continue
            handle_entry(ent)
    else:
        handle_entry(info)
    return items

def is_direct_image(url):
    u = url.lower()
    if any(u.endswith(ext) for ext in image_exts):
        return True
    try:
        r = requests.head(url, headers={"User-Agent":"Mozilla/5.0"}, allow_redirects=True, timeout=6)
        ct = r.headers.get("Content-Type","")
        return "image" in ct
    except Exception:
        return False

def download_image_from_url(url, outpath, fmt):
    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content))
    if fmt not in ["jpg","jpeg","png","webp","bmp","tiff"]:
        fmt = "png"
    fname = os.path.join(outpath, f"{os.path.basename(url).split('?')[0]}.{fmt}")
    img.convert("RGB").save(fname, fmt.upper())
    return fname

def download_via_ytdlp(orig_url, outpath, chosen_format, chosen_quality, progress_hook):
    outtmpl = os.path.join(outpath, "%(uploader)s_%(id)s.%(ext)s")
    options = {
        "outtmpl": outtmpl,
        "noplaylist": True,
        "merge_output_format": chosen_format,
        "progress_hooks": [progress_hook],
    }
    if chosen_format in audio_exts:
        options.update({
            "format":"bestaudio/best",
            "postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":chosen_format,"preferredquality":"192"}]
        })
    else:
        if chosen_quality == "Best":
            options["format"] = "bestvideo+bestaudio/best"
        else:
            h = "".join(ch for ch in chosen_quality if ch.isdigit())
            options["format"] = f"bestvideo[height<={h}]+bestaudio/best"
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([orig_url])

def on_download():
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Warning","Please enter a URL.")
        return
    folder = filedialog.askdirectory(title="Select download folder")
    if not folder:
        return
    try:
        items = gather_media_info(url)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to analyze URL:\n{e}")
        return
    if not items:
        if is_direct_image(url):
            try:
                fname = download_image_from_url(url, folder, format_combo.get())
                messagebox.showinfo("Success", f"Saved: {fname}")
            except Exception as e:
                messagebox.showerror("Error", f"Image download failed:\n{e}")
        else:
            try:
                download_via_ytdlp(url, folder, format_combo.get(), quality_combo.get(), download_progress)
                messagebox.showinfo("Success", "Download completed.")
            except Exception as e:
                messagebox.showerror("Error", f"Download failed:\n{e}")
        return
    images = [it for it in items if it["type"]=="image"]
    videos = [it for it in items if it["type"]=="video" or it["type"]=="audio"]
    if images and not videos:
        show_selection_window(images, folder)
        return
    if images and videos:
        res = messagebox.askyesno("Mixed content","This post contains images and videos. Download media? (Yes downloads all videos via yt-dlp and then shows selection of images)")
        if not res:
            return
        for v in videos:
            try:
                download_via_ytdlp(url, folder, format_combo.get(), quality_combo.get(), download_progress)
            except Exception as e:
                messagebox.showerror("Error", f"Video download failed:\n{e}")
        show_selection_window(images, folder)
        return
    if videos and not images:
        try:
            download_via_ytdlp(url, folder, format_combo.get(), quality_combo.get(), download_progress)
            messagebox.showinfo("Success", "Download completed.")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed:\n{e}")
        return

def download_progress(d):
    if d.get("status") == "downloading":
        pct = d.get("_percent_str", "0.0%")
        progress_label.config(text=f"Progress: {pct}")
        root.update_idletasks()
    elif d.get("status") == "finished":
        progress_label.config(text="Progress: 100%")

def show_selection_window(images, folder):
    popup = Toplevel(root)
    popup.title("Select images to download")
    popup.geometry("800x520")
    frame = ttk.Frame(popup)
    frame.pack(fill="both", expand=True)
    canvas = tk.Canvas(frame)
    scroll = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    vars_list = []
    thumbs = []
    for i, it in enumerate(images[:50]):
        try:
            r = requests.get(it["url"], headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
            r.raise_for_status()
            im = Image.open(io.BytesIO(r.content))
            im.thumbnail((140,140))
            tkimg = ImageTk.PhotoImage(im)
            thumbs.append(tkimg)
            var = IntVar(value=1)
            vars_list.append((var, it))
            cb = ttk.Checkbutton(inner, image=tkimg, variable=var)
            cb.grid(row=i//5, column=i%5, padx=6, pady=6)
        except Exception:
            continue
    def confirm():
        selected = [pair[1] for pair in vars_list if pair[0].get()==1]
        if not selected:
            messagebox.showwarning("Warning","No images selected.")
            return
        popup.destroy()
        for it in selected:
            try:
                saved = download_image_from_url(it["url"], folder, format_combo.get())
                root.after(100, lambda s=saved: root.bell())
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image:\n{e}")
        messagebox.showinfo("Done","Selected images downloaded.")
    btn = tb.Button(popup, text="⬇️ Download Selected", command=confirm, bootstyle=WARNING)
    btn.pack(pady=8)

def on_paste():
    try:
        content = pyperclip.paste()
        url_entry.delete(0, tk.END)
        url_entry.insert(0, content)
        preview_image_if_possible()
    except Exception:
        messagebox.showerror("Error","Clipboard access failed.")

def preview_image_if_possible():
    url = url_entry.get().strip()
    if not url:
        preview_label.config(text="No preview")
        return
    if is_direct_image(url):
        try:
            r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
            r.raise_for_status()
            im = Image.open(io.BytesIO(r.content))
            im.thumbnail((260,260))
            tkimg = ImageTk.PhotoImage(im)
            preview_label.config(image=tkimg, text="")
            preview_label.image = tkimg
            preview_frame.pack(pady=6)
        except Exception:
            preview_label.config(text="Preview not available", image="")
            preview_label.image = None
    else:
        preview_label.config(text="No image preview", image="")
        preview_label.image = None

def toggle_theme():
    cur = style.theme.name
    if cur == "darkly":
        style.theme_use("flatly")
        theme_btn.config(text="🌙 Dark Mode")
    else:
        style.theme_use("darkly")
        theme_btn.config(text="☀️ Light Mode")

root = tb.Window(themename="darkly")
root.title("Universal Media Downloader - Extended")
root.geometry("700x720")
root.resizable(False, False)
style = tb.Style()
title = ttk.Label(root, text="🎬 Universal Media Downloader - Extended", font=("Segoe UI",16,"bold"))
title.pack(pady=12)
frame_url = ttk.Frame(root)
frame_url.pack(padx=18, pady=6, fill="x")
ttk.Label(frame_url, text="Media URL:").pack(anchor="w")
url_entry = ttk.Entry(frame_url, font=("Segoe UI",10))
url_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
url_entry.bind("<FocusOut>", lambda e: preview_image_if_possible())
paste_btn = tb.Button(frame_url, text="📋 Paste", command=on_paste, bootstyle=INFO)
paste_btn.pack(side="right")
preview_frame = ttk.Frame(root)
preview_label = ttk.Label(preview_frame, text="No image preview", font=("Segoe UI",10))
preview_label.pack(pady=6)
opts = ttk.Frame(root)
opts.pack(padx=18, pady=6, fill="x")
ttk.Label(opts, text="Output format:").grid(row=0,column=0,sticky="w")
formats = ["mp4","mkv","webm","mov","avi","mp3","wav","m4a","flac","aac","ogg","jpg","png","webp","bmp","tiff"]
format_combo = ttk.Combobox(opts, values=formats, state="readonly")
format_combo.current(0)
format_combo.grid(row=0,column=1,padx=8,sticky="ew")
ttk.Label(opts, text="Quality / Resolution:").grid(row=1,column=0,sticky="w", pady=8)
qualities = ["Best","1080p","720p","480p","360p","128","192","256","320"]
quality_combo = ttk.Combobox(opts, values=qualities, state="readonly")
quality_combo.current(0)
quality_combo.grid(row=1,column=1,padx=8,sticky="ew")
download_btn = tb.Button(root, text="⬇️ Download", command=on_download, bootstyle=WARNING, width=30)
download_btn.pack(pady=14)
progress_label = ttk.Label(root, text="Progress: 0%", font=("Segoe UI",10))
progress_label.pack(pady=6)
theme_btn = tb.Button(root, text="☀️ Light Mode", command=toggle_theme, bootstyle=SECONDARY)
theme_btn.pack(pady=8)
footer = ttk.Label(root, text="Supports Instagram, X, TikTok, YouTube, Reddit, Facebook and more", font=("Segoe UI",9))
footer.pack(side="bottom", pady=12)
root.mainloop()

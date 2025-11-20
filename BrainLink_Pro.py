#!/usr/bin/env python3
"""
BrainLink Deluxe — IE-style Tkinter UI with optional Dark/ Fun Mode.
DuckDuckGo search + optional local Ollama refinement.
"""

import subprocess
import threading
import time
from tkinter import (
    Tk, Frame, Label, Entry, Button, Listbox, Scrollbar,
    StringVar, END, SINGLE, Toplevel, Text, BOTH, RIGHT, Y, LEFT, X, BOTTOM
)
from ddgs import DDGS
import webview

APP_TITLE = "BrainLink Deluxe — IE Mode"
DEFAULT_MAX_RESULTS = 64

# Fonts
FONT_TITLE = ("Tahoma", 20, "bold")
FONT_TITLE_FUN = ("Comic Sans MS", 20, "bold")
FONT_LABEL = ("Verdana", 11)
FONT_ENTRY = ("Verdana", 12)
FONT_RESULT = ("Courier New", 11)

# Classic IE colors
IE_BG = "#d4d0c8"
IE_HEADER = "#c0c0c0"
IE_BUTTON = "#e0e0e0"
IE_BUTTON_ACTIVE = "#b0b0b0"
IE_LIST_BG = "white"
IE_LIST_ALT = "#f0f0f0"
IE_TEXT = "#000"
IE_STATUS = "#c0c0c0"

# Dark Mode colors
DARK_BG = "#2b2b2b"
DARK_FG = "#f0f0f0"
DARK_BTN = "#444"
DARK_BTN_ACTIVE = "#666"
DARK_LIST_BG = "#333"
DARK_LIST_ALT = "#444"
DARK_STATUS = "#444"

# Fun Mode colors
FUN_BG = "#fffae3"
FUN_HEADER = "#ffecb3"
FUN_BTN = "#ffb74d"
FUN_BTN_ACTIVE = "#ff9800"
FUN_LIST_BG = "#fff3e0"
FUN_LIST_ALT = "#ffe0b2"
FUN_TEXT = "#3e2723"
FUN_STATUS = "#ffcc80"
FUN_ACCENTS = ["#ffb74d", "#ff8a65", "#f06292", "#ba68c8", "#64b5f6", "#4db6ac"]


# -------------------------------
# Ollama query refinement
# -------------------------------
def try_refine_with_ollama(query: str, model: str = "llama4") -> str:
    prompt = f"Reword this for a web search (concise): {query}"
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=15
        )
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if lines:
            candidate = lines[-1]
            if 3 <= len(candidate) <= 400 and candidate.lower() != prompt.lower():
                return candidate
        return query
    except Exception:
        return query


# -------------------------------
# DuckDuckGo search
# -------------------------------
def ddg_search(query: str, max_results: int = 64):
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, region="wt-wt", safesearch="Off", timelimit="y", max_results=max_results):
                results.append({
                    "title": r.get("title") or r.get("text") or "(no title)",
                    "href": r.get("href") or r.get("url") or "",
                    "body": r.get("body") or ""
                })
    except Exception as e:
        print("DuckDuckGo search failed:", e)
    return results


# -------------------------------
# GUI
# -------------------------------
class BrainLinkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("950x700")
        self.root.configure(bg=IE_BG)
        self.root.resizable(True, True)

        self.dark_mode = False
        self.fun_mode = False

        # Header
        self.header = Frame(root, bg=IE_HEADER, relief="raised", bd=2)
        self.header.pack(fill=X)
        self.header_label = Label(self.header, text="BrainLink Pro", font=FONT_TITLE, bg=IE_HEADER, fg=IE_TEXT)
        self.header_label.pack(pady=8)

        # Search bar
        entry_frame = Frame(root, bg=IE_BG, pady=6)
        entry_frame.pack(fill=X, padx=10)

        self.query_var = StringVar()
        self.search_entry = Entry(entry_frame, textvariable=self.query_var, font=FONT_ENTRY, bd=2, relief="sunken")
        self.search_entry.pack(side=LEFT, fill=X, expand=True, padx=(0,6))
        self.search_entry.bind("<Return>", lambda ev: self.on_search_click())

        self.search_btn = Button(entry_frame, text="Search", font=FONT_LABEL, bg=IE_BUTTON,
                                 activebackground=IE_BUTTON_ACTIVE, command=self.on_search_click)
        self.search_btn.pack(side=LEFT, padx=(0,4))

        self.fun_btn = Button(entry_frame, text="Fun Mode", font=FONT_LABEL, bg=IE_BUTTON,
                              activebackground=IE_BUTTON_ACTIVE, command=self.toggle_fun_mode)
        self.fun_btn.pack(side=LEFT)

        self.dark_btn = Button(entry_frame, text="Toggle Dark Mode", font=FONT_LABEL, bg=IE_BUTTON,
                               activebackground=IE_BUTTON_ACTIVE, command=self.toggle_dark_mode)
        self.dark_btn.pack(side=LEFT)

        # Status label
        self.status_label = Label(root, text="Type a query and hit Search.", font=FONT_LABEL, bg=IE_STATUS, anchor="w")
        self.status_label.pack(fill=X, side=BOTTOM)

        # Results frame
        results_frame = Frame(root, bg=IE_BG)
        results_frame.pack(fill=BOTH, expand=True, padx=10, pady=(4,10))

        self.scrollbar = Scrollbar(results_frame)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.results_list = Listbox(results_frame, font=FONT_RESULT, activestyle="dotbox",
                                   yscrollcommand=self.scrollbar.set, selectmode=SINGLE,
                                   bd=2, relief="sunken", bg=IE_LIST_BG, fg=IE_TEXT)
        self.results_list.pack(fill=BOTH, expand=True)
        self.results_list.bind("<Double-Button-1>", lambda ev: self.on_result_open())
        self.results_list.bind("<Return>", lambda ev: self.on_result_open())
        self.scrollbar.config(command=self.results_list.yview)

        # Footer buttons
        footer = Frame(root, bg=IE_BG, pady=6)
        footer.pack(fill=X, padx=10)
        Button(footer, text="Open Link", command=self.on_result_open, bg=IE_BUTTON, activebackground=IE_BUTTON_ACTIVE).pack(side=LEFT, padx=(0,4))
        Button(footer, text="Show Snippet", command=self.on_show_snippet, bg=IE_BUTTON, activebackground=IE_BUTTON_ACTIVE).pack(side=LEFT, padx=(0,4))
        Button(footer, text="Clear", command=self.clear_results, bg=IE_BUTTON, activebackground=IE_BUTTON_ACTIVE).pack(side=LEFT, padx=(0,4))
        Button(footer, text="Quit", command=root.quit, bg=IE_BUTTON, activebackground=IE_BUTTON_ACTIVE).pack(side="right")

        self.current_results = []

    # -------------------------------
    def on_search_click(self):
        raw_query = self.query_var.get().strip()
        if not raw_query:
            self.set_status("Type a query first.")
            return

        # Open URL directly if looks like link
        if raw_query.startswith(("http://", "https://")) or ("." in raw_query and " " not in raw_query):
            url = raw_query if raw_query.startswith(("http://", "https://")) else "http://" + raw_query
            self.set_status(f"Opening {url}...")
            webview.create_window("BrainLink Viewer", url)
            webview.start()
            return

        # AI refinement + DDG
        self.search_btn.config(state="disabled")
        self.set_status("Refining query with local AI (if available)...")

        def worker():
            try:
                refined = try_refine_with_ollama(raw_query)
                if refined != raw_query:
                    self.set_status(f"Refined query: {refined} — searching...")
                else:
                    self.set_status("Searching...")
                results = ddg_search(refined, max_results=DEFAULT_MAX_RESULTS)
                self.root.after(0, lambda: self.display_results(results, refined))
            finally:
                self.root.after(0, lambda: self.search_btn.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    # -------------------------------
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.fun_mode:
            return self.apply_fun_mode()
        if self.dark_mode:
            bg, fg, btn, btn_active, list_bg, list_alt, status_bg = DARK_BG, DARK_FG, DARK_BTN, DARK_BTN_ACTIVE, DARK_LIST_BG, DARK_LIST_ALT, DARK_STATUS
        else:
            bg, fg, btn, btn_active, list_bg, list_alt, status_bg = IE_BG, IE_TEXT, IE_BUTTON, IE_BUTTON_ACTIVE, IE_LIST_BG, IE_LIST_ALT, IE_STATUS
        self.apply_colors(bg, fg, btn, btn_active, list_bg, list_alt, status_bg, FONT_TITLE)

    # -------------------------------
    def toggle_fun_mode(self):
        self.fun_mode = not self.fun_mode
        if self.fun_mode:
            self.apply_fun_mode()
        else:
            self.toggle_dark_mode()  # revert to dark/IE mode

    def apply_fun_mode(self):
        accent = FUN_ACCENTS[int(time.time()) % len(FUN_ACCENTS)]
        bg, header_bg, btn, btn_active, list_bg, list_alt, fg, status_bg = FUN_BG, accent, accent, FUN_BTN_ACTIVE, FUN_LIST_BG, FUN_LIST_ALT, FUN_TEXT, FUN_STATUS
        self.apply_colors(bg, fg, btn, btn_active, list_bg, list_alt, status_bg, FONT_TITLE_FUN)

    def apply_colors(self, bg, fg, btn, btn_active, list_bg, list_alt, status_bg, header_font):
        self.root.configure(bg=bg)
        self.header.configure(bg=btn)
        self.header_label.configure(bg=btn, fg=fg, font=header_font)
        for child in self.root.winfo_children():
            if isinstance(child, Frame) and child not in [self.header]:
                child.configure(bg=bg)
                for grand in child.winfo_children():
                    if isinstance(grand, Button):
                        grand.configure(bg=btn, activebackground=btn_active, fg=fg)
                    elif isinstance(grand, Label):
                        grand.configure(bg=bg, fg=fg)
        # Update results list
        self.results_list.configure(fg=fg)
        for idx in range(self.results_list.size()):
            bg_color = list_bg if idx % 2 == 0 else list_alt
            if self.fun_mode:
                self.results_list.itemconfig(idx, bg=bg_color, fg=fg)
            else:
                self.results_list.itemconfig(idx, bg=list_bg, fg=fg)
        self.status_label.configure(bg=status_bg, fg=fg)

    # -------------------------------
    def set_status(self, text: str):
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def clear_results(self):
        self.results_list.delete(0, END)
        self.current_results = []
        self.set_status("Results cleared.")

    def display_results(self, results, used_query):
        self.clear_results()
        if not results:
            self.set_status(f"No results for \"{used_query}\".")
            return
        self.current_results = results
        for idx, r in enumerate(results):
            title = r.get("title") or "(no title)"
            body = r.get("body") or ""
            emoji = "🔎 " if self.fun_mode else ""
            display = f"{idx+1}. {emoji}{title} — {body[:120].strip()}"
            self.results_list.insert(END, display)
            if self.fun_mode:
                bg_color = FUN_LIST_BG if idx % 2 == 0 else FUN_LIST_ALT
                self.results_list.itemconfig(idx, bg=bg_color, fg=FUN_TEXT)
        self.set_status(f"Found {len(results)} results for \"{used_query}\". Double-click to open.")

    def on_result_open(self):
        sel = self.results_list.curselection()
        if not sel:
            self.set_status("No result selected.")
            return
        url = self.current_results[sel[0]].get("href")
        if not url:
            self.set_status("Result has no link.")
            return
        self.set_status(f"Opening {url}...")
        webview.create_window("BrainLink Viewer", url)
        webview.start()

    def on_show_snippet(self):
        sel = self.results_list.curselection()
        if not sel:
            self.set_status("No result selected.")
            return
        r = self.current_results[sel[0]]
        popup = Toplevel(self.root)
        popup.title("Snippet — " + (r.get("title","")[:40] if r.get("title") else "Snippet"))
        popup.geometry("750x400")
        text_widget = Text(popup, wrap="word", font=FONT_ENTRY)
        text_widget.pack(fill=BOTH, expand=True)
        text_widget.insert("1.0", f"Title: {r.get('title','(no title)')}\n\nURL: {r.get('href','(no link)')}\n\nSnippet:\n{r.get('body','(no snippet)')}")
        text_widget.config(state="disabled")


# -------------------------------
def main():
    root = Tk()
    app = BrainLinkGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

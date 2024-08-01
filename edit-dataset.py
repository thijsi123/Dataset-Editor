import os
import re
import csv
import json
import requests
from urllib.parse import urljoin
from tkinter import ttk, Button, END, INSERT, BOTTOM, Tk, Label, Text, Scrollbar, Frame, Listbox, BOTH, RIGHT, Y, LEFT, \
    SINGLE, TOP, X, PanedWindow, StringVar, filedialog
from PIL import Image, ImageTk
import tkinter as tk


def download_file(url, local_filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Downloaded {local_filename}")


def ensure_tag_files_exist(tag_sources):
    base_url = "https://raw.githubusercontent.com/DominikDoom/a1111-sd-webui-tagcomplete/main/tags/"
    files_to_download = {
        "EnglishDictionary.csv": "EnglishDictionary.csv",
        "danbooru.csv": "danbooru.csv",
        "demo-chants.json": "demo-chants.json",
        "derpibooru.csv": "derpibooru.csv",
        "e621.csv": "e621.csv",
        "e621_sfw.csv": "e621_sfw.csv",
        "extra-quality-tags.csv": "extra-quality-tags.csv"
    }

    os.makedirs("tags", exist_ok=True)

    for source in tag_sources:
        local_path = source.file_path
        if not os.path.exists(local_path):
            filename = os.path.basename(local_path)
            if filename in files_to_download:
                url = urljoin(base_url, files_to_download[filename])
                print(f"Downloading {filename}...")
                download_file(url, local_path)
            else:
                print(f"Warning: {filename} not found and no download URL specified.")


class TagSource:
    def __init__(self, name, file_path, loader_func):
        self.name = name
        self.file_path = file_path
        self.loader_func = loader_func
        self.tags = []

    def load(self):
        self.tags = self.loader_func(self.file_path)
        print(f"Loaded {len(self.tags)} tags from {self.name}")


class ImageTextViewer:
    def __init__(self, tag_sources):
        self.directory = ""
        self.files = []
        self.current_index = 0
        self.tag_sources = tag_sources
        self.config_file = "config.json"
        self.load_config()

        ensure_tag_files_exist(self.tag_sources)
        self.load_all_tags()

        self.root = tk.Tk()
        self.root.title("Image and Text Viewer with Tag Autocomplete")
        self.root.geometry("1200x800")

        self.setup_ui()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.last_folder = config.get('last_folder', '')
        else:
            self.last_folder = ''

    def save_config(self):
        config = {'last_folder': self.directory}
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def get_file_pairs(self):
        pairs = []
        if self.directory:
            for filename in os.listdir(self.directory):
                if filename.endswith(('.jpg', '.png')):
                    image_path = os.path.join(self.directory, filename)
                    text_path = os.path.join(self.directory, filename.rsplit('.', 1)[0] + '.txt')
                    if os.path.exists(text_path):
                        pairs.append((image_path, text_path))
        return pairs

    def load_all_tags(self):
        for source in self.tag_sources:
            try:
                source.load()
                print(f"Loaded {len(source.tags)} tags from {source.name}")
            except Exception as e:
                print(f"Error loading tags from {source.name}: {e}")

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)  # Main content area should expand

        # Folder selection frame
        folder_frame = ttk.Frame(self.root)
        folder_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        folder_frame.columnconfigure(1, weight=1)

        self.folder_entry = ttk.Entry(folder_frame)
        self.folder_entry.grid(row=0, column=1, sticky="ew")

        ttk.Button(folder_frame, text="Select Folder", command=self.select_folder).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(folder_frame, text="Load", command=self.load_folder).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(folder_frame, text="Load Last Folder", command=self.load_last_folder).grid(row=0, column=3,
                                                                                              padx=(5, 0))

        # Main content frame
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Left pane for image selection
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="ns")
        left_frame.rowconfigure(0, weight=1)

        self.image_listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE, width=40)
        self.image_listbox.grid(row=0, column=0, sticky="nsew")
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)

        image_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.image_listbox.yview)
        image_scrollbar.grid(row=0, column=1, sticky="ns")
        self.image_listbox.config(yscrollcommand=image_scrollbar.set)

        # Right pane for image, text, and tags
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

        # Image frame
        self.image_label = ttk.Label(right_frame)
        self.image_label.grid(row=0, column=0, sticky="nsew")

        # Text and tag frame
        text_tag_frame = ttk.Frame(right_frame)
        text_tag_frame.grid(row=1, column=0, sticky="nsew")
        text_tag_frame.columnconfigure(0, weight=1)
        text_tag_frame.rowconfigure(0, weight=1)

        self.text_widget = tk.Text(text_tag_frame, wrap="word")
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        self.text_widget.bind('<KeyRelease>', self.update_tag_list)

        text_scrollbar = ttk.Scrollbar(text_tag_frame, orient="vertical", command=self.text_widget.yview)
        text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_widget.config(yscrollcommand=text_scrollbar.set)

        self.tag_listbox = tk.Listbox(text_tag_frame, selectmode=tk.SINGLE, font=("Courier", 10), height=5)
        self.tag_listbox.grid(row=1, column=0, sticky="ew")
        self.tag_listbox.bind('<<ListboxSelect>>', self.use_selected_tag)

        # Button frame
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=2, column=0, sticky="ew")
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(button_frame, text="Previous", command=self.prev_file).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="Next", command=self.next_file).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(button_frame, text="Save", command=self.save_text).grid(row=0, column=1, padx=5, pady=5)

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.grid(row=3, column=0, sticky="ew")

        # Keyboard bindings
        self.root.bind('<Control-s>', lambda e: self.save_text())
        self.root.bind('<Control-n>', lambda e: self.next_file())
        self.root.bind('<Control-p>', lambda e: self.prev_file())
        self.root.bind('<Tab>', self.select_next_tag)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.load_folder()

    def load_folder(self):
        self.directory = self.folder_entry.get()
        if os.path.isdir(self.directory):
            self.files = self.get_file_pairs()
            self.current_index = 0
            self.populate_image_listbox()
            self.load_current_file()
            self.save_config()  # Save the current folder as the last used folder
        else:
            tk.messagebox.showerror("Error", "Invalid directory path")

    def load_last_folder(self):
        if self.last_folder and os.path.isdir(self.last_folder):
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, self.last_folder)
            self.load_folder()
        else:
            tk.messagebox.showinfo("Info", "No valid last folder found")

    def populate_image_listbox(self):
        self.image_listbox.delete(0, tk.END)
        for i, (image_path, _) in enumerate(self.files):
            filename = os.path.basename(image_path)
            self.image_listbox.insert(tk.END, filename)
            self.image_listbox.itemconfig(i, {'bg': 'lightgray' if i % 2 == 0 else 'white'})
    def create_save_button(self):
        save_button = Button(self.root, text="Save", command=self.save_text)
        save_button.pack(side=BOTTOM, pady=5)

    def load_current_file(self):
        if 0 <= self.current_index < len(self.files):
            image_path, text_path = self.files[self.current_index]
            self.display_image(image_path)
            self.display_text(text_path)
            self.image_listbox.selection_clear(0, END)
            self.image_listbox.selection_set(self.current_index)
            self.image_listbox.see(self.current_index)
            self.update_status_bar()

    def display_image(self, image_path):
        image = Image.open(image_path)
        image.thumbnail((800, 600))
        photo = ImageTk.PhotoImage(image)
        self.image_label.config(image=photo)
        self.image_label.image = photo

    def display_text(self, text_path):
        with open(text_path, 'r') as file:
            text = file.read()
        self.text_widget.delete("1.0", END)
        self.text_widget.insert("1.0", text)

    def save_text(self):
        if 0 <= self.current_index < len(self.files):
            _, text_path = self.files[self.current_index]
            text = self.text_widget.get("1.0", END)
            with open(text_path, 'w') as file:
                file.write(text)
        print("Text saved successfully.")

    def next_file(self):
        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            self.load_current_file()

    def prev_file(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_file()

    def on_image_select(self, event):
        selection = self.image_listbox.curselection()
        if selection:
            self.current_index = selection[0]
            self.load_current_file()

    def get_current_word(self):
        cursor_position = self.text_widget.index(INSERT)
        line, char = map(int, cursor_position.split('.'))
        line_content = self.text_widget.get(f"{line}.0", f"{line}.end")
        words = re.findall(r'\S+', line_content)
        current_word = ""
        for word in reversed(words):
            if len(line_content[:char].rstrip()) >= len(line_content[:char].rstrip()) - len(word):
                current_word = word
                break
        return current_word.lower()

    def update_tag_list(self, event):
        if event.keysym in ('space', 'comma', 'Return'):
            self.tag_listbox.delete(0, tk.END)
            return

        current_word = self.get_current_word()
        if current_word:
            data = []
            for source in self.tag_sources:
                data.extend([tag for tag in source.tags if tag[0].lower().startswith(current_word)])
            data = sorted(data, key=lambda x: x[2] if len(x) > 2 else 0, reverse=True)[
                   :50]  # Sort by count and limit to 50 results

            self.tag_listbox.delete(0, tk.END)
            for item in data:
                tag = item[0]
                category = item[1] if len(item) > 1 else 0
                count = item[2] if len(item) > 2 else ''
                color = self.get_tag_color(category)
                display_text = f"{tag} ({count})" if count else tag
                self.tag_listbox.insert(tk.END, display_text)
                self.tag_listbox.itemconfig(tk.END, {'fg': color})
        else:
            self.tag_listbox.delete(0, tk.END)

    def get_tag_color(self, category):
        colors = {
            0: "blue",  # General
            1: "red",  # Artist
            3: "green",  # Copyright
            4: "purple",  # Character
            5: "orange",  # Meta
        }
        return colors.get(int(category), "black")  # Convert category to int

    def use_selected_tag(self, event):
        if self.tag_listbox.curselection():
            selected_tag = self.tag_listbox.get(self.tag_listbox.curselection()).split()[0]  # Remove count
            cursor_position = self.text_widget.index(INSERT)
            line, char = map(int, cursor_position.split('.'))
            line_content = self.text_widget.get(f"{line}.0", f"{line}.end")
            current_word = self.get_current_word()
            if current_word:
                word_start = line_content.rindex(current_word, 0, char)
                self.text_widget.delete(f"{line}.{word_start}", f"{line}.{char}")
                self.text_widget.insert(f"{line}.{word_start}", selected_tag)
            else:
                self.text_widget.insert(cursor_position, selected_tag)
            self.tag_listbox.delete(0, END)

    def select_next_tag(self, event):
        if self.tag_listbox.size() > 0:
            current_selection = self.tag_listbox.curselection()
            if current_selection:
                next_index = (current_selection[0] + 1) % self.tag_listbox.size()
            else:
                next_index = 0
            self.tag_listbox.selection_clear(0, END)
            self.tag_listbox.selection_set(next_index)
            self.tag_listbox.see(next_index)
            self.use_selected_tag(None)
        return 'break'  # Prevent default Tab behavior

    def update_status_bar(self):
        self.status_var.set(f"Image {self.current_index + 1} of {len(self.files)}")

    def run(self):
        self.root.mainloop()


def load_csv_tags(file_path):
    tags = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 1:
                tag = row[0].strip()
                category = 0
                count = 0
                if len(row) >= 2:
                    try:
                        category = int(row[1])
                    except ValueError:
                        category = 0
                if len(row) >= 3:
                    try:
                        count = int(row[2])
                    except ValueError:
                        count = 0
                tags.append((tag, category, count))
    return tags


def load_json_chants(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        chants = json.load(file)
    return [(chant['name'], chant.get('color', 0), 0) for chant in
            chants]  # Use 'name' as tag, 'color' as category, and 0 as count


def load_extra_quality_tags(file_path):
    tags = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 1:
                tag = row[0].strip()
                category = 0
                if len(row) > 1:
                    try:
                        category = int(row[1])
                    except ValueError:
                        category = 0
                tags.append((tag, category, 0))  # Add a count of 0
    return tags

# Define tag sources
tag_sources = [
    TagSource("English Dictionary", "tags/EnglishDictionary.csv", load_csv_tags),
    TagSource("Danbooru", "tags/danbooru.csv", load_csv_tags),
    TagSource("Derpibooru", "tags/derpibooru.csv", load_csv_tags),
    TagSource("e621", "tags/e621.csv", load_csv_tags),
    TagSource("e621 SFW", "tags/e621_sfw.csv", load_csv_tags),
    TagSource("Chants", "tags/demo-chants.json", load_json_chants),
    TagSource("Extra Quality", "tags/extra-quality-tags.csv", load_extra_quality_tags)
]

ensure_tag_files_exist(tag_sources)
viewer = ImageTextViewer(tag_sources)
viewer.run()

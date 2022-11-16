# importing module 

from pytube import YouTube, Search
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askopenfilename
import threading
import webbrowser
from os import getcwd
from os import path
import urllib
from PIL import Image, ImageTk
import io
import re
from sys import argv
#import random

def correct_name_format(name: str):
        return name.replace("\"", "").replace("/", "") \
                   .replace("\\", "").replace(":", "") \
                   .replace("*", "").replace("?", "")\
                   .replace("<", "").replace(">", "").replace("|", "")


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)


        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class QueryGUI(ttk.Frame):
    thumbnails = {}
    def __init__(self, parent, yt_obj: YouTube, bt_args = []):
        ttk.Frame.__init__(self, parent)
        self.title_max_length = 40
        self.buttons = {}
        self.yt = yt_obj
        
        thumbnail = ttk.Label(self)
        thumbnail.grid(column=0, row=0, sticky = tk.E)
        threading.Thread(target = self.set_image_query, args=[self.yt, thumbnail]).start()
        
        for i, arg_dict in enumerate(bt_args):
            if "callback_args" in arg_dict and "command" in arg_dict:
                callback_args = arg_dict["callback_args"]
                call_back_func = arg_dict["command"]
                arg_dict.pop("callback_args")
                arg_dict.pop("command")
            else:
                callback_args = None

            if callback_args != None:
                button = ttk.Button(self, **arg_dict, command = lambda:call_back_func(**callback_args))
            else:
                button = ttk.Button(self, **arg_dict)

            button.grid(column = 1 + i, row = 0)
            if "name" in arg_dict:
                self.buttons[arg_dict["name"]] = button
            else:
                self.buttons[i] = button

        text = ttk.Label(self, text = self.yt.title if len(self.yt.title) <= self.title_max_length else self.yt.title[:self.title_max_length - 3] + "...")
        text.grid(column = len(bt_args) + 2, row = 0)

    def download_image_data(self, url: str):
        if url not in self.thumbnails.keys():
            with urllib.request.urlopen(url) as u:
                raw_data = u.read()
            im = Image.open(io.BytesIO(raw_data))
            self.thumbnails[url] = ImageTk.PhotoImage(im.resize((50, 50)))

    def set_image_query(self, yt_obj: YouTube, label_ref: ttk.Label):
        self.download_image_data(yt_obj.thumbnail_url)
        image_ref = self.thumbnails[yt_obj.thumbnail_url]
        label_ref.configure(image = image_ref)

    

class maingui(tk.Tk):
    def __init__(self, title, geometry):
        super().__init__()
        # data
        self.search_term = ""
        self.save_directory = getcwd()


        # Visuals
        self.title(title)
        self.geometry(geometry)

        self.grid()

        self.search_b = ttk.Button(self, text = "search", command=self.search_video)
        self.search_b.grid(row = 0, column = 0,sticky=tk.W, padx=5, pady=2)

        self.search_inp = ttk.Entry(self)
        self.search_inp.bind("<Return>", lambda x: self.search_video())
        self.search_inp.grid(row = 0, column = 1, sticky=tk.W)

        self.query_scroll_container = ScrollableFrame(self)
        self.query_container = self.query_scroll_container.scrollable_frame
        self.query_scroll_container.grid(row = 1, rowspan=2, column=0, columnspan=3)

        self.download_scroll_container = ScrollableFrame(self)
        self.download_container = self.download_scroll_container.scrollable_frame
        self.download_scroll_container.grid(row = 1, column=3, columnspan=4, sticky = tk.NW)

        
        self.upload_texts = ttk.Button(self, text = "From list", command=self.download_prompt_file)
        self.upload_texts.grid(row = 0, column = 3)
        
        self.directory_label = ttk.Label(self, text= "Save directory: ")
        self.directory_label.grid(row = 0, column = 4)
        self.directory_path_text = tk.Text(self, height=1)
        self.directory_path_text.insert(tk.END, self.save_directory)
        self.directory_path_text.grid(row = 0, column = 5, padx=5)



        self.query_objects = {}
        self.download_objects = {}
        self.thumbnails = {}
        
    def download_audio(self, yt_obj: YouTube, update_button: ttk.Button):
        self.save_directory = self.directory_path_text.get('1.0', 'end').strip()
        
        audio_stream = yt_obj.streams.get_audio_only()
        
        audio_stream.download(filename = path.join(self.save_directory, correct_name_format(yt_obj.title)) + ".mp3")
        update_button.configure(text="Open")
        self.download_objects[yt_obj.embed_url][0] = "done"
        #self.download_objects.pop(yt_obj.embed_url)

    def pause_download_or_open(self, yt_obj: YouTube):
        if yt_obj.embed_url in self.download_objects.keys():
            if self.download_objects[yt_obj.embed_url][0] == "down":
                self.download_objects[yt_obj.embed_url][0] = "pause"
            elif self.download_objects[yt_obj.embed_url][0] == "pause:":
                self.download_objects[yt_obj.embed_url][0] = "down"
            elif self.download_objects[yt_obj.embed_url][0] == "done":
                webbrowser.open(self.save_directory)

    def new_download_yt(self, yt_obj: YouTube):
        if yt_obj.embed_url in self.download_objects.keys():
            return

        def rm_download(embed_url: str):
                self.download_objects[embed_url][1].destroy()
                self.download_objects.pop(embed_url)

        button_args = [
            {"text": "Downloading...", "name": "status_button", "command": lambda:self.pause_download_or_open(yt_obj)}, 
            {"text": "X", "command": lambda:rm_download(yt_obj.embed_url)}
            ]
        d_obj = QueryGUI(self.download_container, yt_obj, button_args)
        d_obj.configure(borderwidth=1,  relief="solid")
        self.download_objects[yt_obj.embed_url] = ["down", d_obj]
        d_obj.grid(row = len(self.download_objects), column=0, sticky=tk.NW)
        
        threading.Thread(target = self.download_audio, args=[yt_obj, d_obj.buttons["status_button"]]).start()

    def new_download(self, embed_url: str):
        yt_obj = self.query_objects[embed_url].yt
        self.new_download_yt(yt_obj)

    def download_list(self, yt_list):
        for yt in yt_list:
            self.new_download_yt(yt)

    def get_links_in_text(self, text: str):
        return re.findall("(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})", text)
    def parse_text_for_yt(self, text: str):
        yt_list = []
        existing_yt = set()
        for line in text.splitlines(keepends=False):
            links = self.get_links_in_text(line)
            if len(links) == 0:
                search_results = Search(line).results
                if len(search_results):
                    yt = search_results[0]
                    if yt.embed_url not in existing_yt:
                        yt_list.append(yt)
                        existing_yt.add(yt.embed_url)

            for link in links:
                try:
                    yt = YouTube(link)
                    yt.check_availability()
                except:
                    continue
                else:
                    if yt.embed_url not in existing_yt:
                        yt_list.append(yt)
                        existing_yt.add(yt.embed_url)
        return yt_list

    def download_from_file(self, filename: str):
        self.upload_texts.configure(text = "Parsing...")
        self.update_idletasks()
        with open(filename, "r", encoding="utf-8") as f:
            text = f.read()
        yt_list = self.parse_text_for_yt(text)
        self.download_list(yt_list)
        self.upload_texts.configure(text = "From list")

    def download_prompt_file(self):
        filename = askopenfilename()
        self.download_from_file(filename)

    def search_video(self):
        search_result = Search(self.search_inp.get())
        self.search_inp.delete(0, 'end')
        for key in self.query_objects.keys():
            self.query_objects[key].destroy()
        self.query_objects.clear()

        for yt in search_result.results:
            self.query_objects[yt.embed_url] = QueryGUI(self.query_container, yt, [{"text": "Download", "command": self.new_download, "callback_args": {"embed_url":yt.embed_url}}])
            self.query_objects[yt.embed_url].configure(borderwidth=1,  relief="solid")
            self.query_objects[yt.embed_url].grid(row = len(self.query_objects), column=0, sticky=tk.W, padx=5, pady = 5)
            

if __name__ == "__main__":

    maingui = maingui("Tube2mp3", "800x400") 
    maingui.tk.call("source", "azure.tcl")
    maingui.tk.call("set_theme", "light")

    if len(argv) > 1:
        maingui.download_from_file(argv[1])
    maingui.mainloop()
    
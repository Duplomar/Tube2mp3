# importing module 

import argparse
from pytube import YouTube, Search
import tkinter as tk
import threading
import webbrowser
import tkinter.ttk as ttk
from os import getcwd
from os import path
import urllib
from PIL import Image, ImageTk
import io
#import random

def correct_name_format(name: str):
        return name.replace("\"", "").replace("/", "") \
                   .replace("\\", "").replace(":", "") \
                   .replace("*", "").replace("?", "")\
                   .replace("<", "").replace(">", "").replace("|", "")


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

        self.search_inp = ttk.Entry(self, width=10)
        self.search_inp.grid(row = 0, column = 1, sticky=tk.W)

        self.query_container = ttk.Frame(self)
        self.query_container.grid(row = 1, column=0, columnspan=3)

        self.download_container = ttk.Frame(self)
        self.download_container.grid(row = 1, column=3, columnspan=4, sticky = tk.NW)

        self.directory_label = ttk.Label(self, text= "Save directory: ")
        self.directory_label.grid(row = 0, column = 3)
        self.directory_path_text = tk.Text(self, height=1)
        self.directory_path_text.insert(tk.END, self.save_directory)
        self.directory_path_text.grid(row = 0, column = 4, padx=5)



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

    def new_download(self, embed_url: str):
        if embed_url in self.download_objects.keys():
            return
        yt_obj = self.query_objects[embed_url].yt

        def rm_download(embed_url: str):
                self.download_objects[embed_url][1].destroy()
                self.download_objects.pop(embed_url)

        button_args = [
            {"text": "Downloading...", "name": "status_button", "command": lambda:self.pause_download_or_open(yt_obj)}, 
            {"text": "X", "command": lambda:rm_download(embed_url)}
            ]
        d_obj = QueryGUI(self.download_container, yt_obj, button_args)
        d_obj.configure(borderwidth=1,  relief="solid")
        self.download_objects[yt_obj.embed_url] = ["down", d_obj]
        d_obj.grid(row = len(self.download_objects), column=0, sticky=tk.NW)
        
        threading.Thread(target = self.download_audio, args=[yt_obj, d_obj.buttons["status_button"]]).start()


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
    maingui.mainloop()
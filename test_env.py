# importing module 

import argparse
from pytube import YouTube, Search, StreamQuery
from tqdm import tqdm
import tkinter as tk
import threading
import webbrowser
from tkinter.ttk import Progressbar
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
class maingui(tk.Tk):
    def __init__(self, title, geometry):
        super().__init__()
        # data
        self.search_term = ""
        self.title_max_length = 40
        self.save_directory = getcwd()


        # Visuals
        self.title(title)
        self.geometry(geometry)

        self.grid()

        self.search_b = tk.Button(self, text = "search", command=self.search_video)
        self.search_b.grid(row = 0, column = 0,sticky=tk.W)

        self.search_inp = tk.Entry(self, width=10)
        self.search_inp.grid(row = 0, column = 1, sticky=tk.W)

        self.query_container = tk.Frame(self)
        self.query_container.grid(row = 1, column=0, columnspan=3)

        self.download_container = tk.Frame(self)
        self.download_container.grid(row = 1, column=3, columnspan=3, sticky = tk.N)

        self.directory_label = tk.Label(self, text= "Save directory: ")
        self.directory_label.grid(row = 0, column = 3)
        self.directory_path_text = tk.Text(self, height=1)
        self.directory_path_text.insert(tk.END, self.save_directory)
        self.directory_path_text.grid(row = 0, column = 4)


        self.query_objects = {}
        self.download_objects = {}
        self.thumbnails = {}
        
    
    def download_image_data(self, url: str):
        if url not in self.thumbnails.keys():
            with urllib.request.urlopen(url) as u:
                raw_data = u.read()
            im = Image.open(io.BytesIO(raw_data))
            self.thumbnails[url] = ImageTk.PhotoImage(im.resize((50, 50)))

    def download_audio(self, yt_obj: YouTube, update_button: tk.Button):
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

    def new_download(self, yt_obj: YouTube):
        if yt_obj.embed_url in self.download_objects.keys():
            return

        d_obj = tk.Frame(self.download_container, borderwidth=1,  relief="solid")
        self.download_objects[yt_obj.embed_url] = ["down", d_obj]

        if yt_obj.embed_url in self.query_objects.keys():
            pass

        thumbnail = tk.Label(d_obj, height = 50, width=50, image=self.thumbnails[yt_obj.thumbnail_url])
        thumbnail.grid(column=0, row=0, sticky = tk.E)
        
        d_button = tk.Button(d_obj, text="Downloading...", command=lambda:self.pause_download_or_open(yt_obj))
        d_button.grid(column = 1, row = 0)

        def rm_download(embed_url: str):
            self.download_objects[embed_url][1].destroy()
            self.download_objects.pop(yt_obj.embed_url)
        rm_button = tk.Button(d_obj, text="X", command=lambda:rm_download(yt_obj.embed_url))
        rm_button.grid(column = 2, row = 0)

        text = tk.Label(d_obj, text = yt_obj.title if len(yt_obj.title) <= self.title_max_length else yt_obj.title[:self.title_max_length - 3] + "...")
        text.grid(column = 3, row = 0)

        d_obj.grid(row = len(self.download_objects), column=0, sticky=tk.NW)
        
        
        threading.Thread(target = self.download_audio, args=[yt_obj, d_button]).start()


    def set_image_query(self, yt_obj: YouTube, label_ref: tk.Label):
        self.download_image_data(yt_obj.thumbnail_url)
        image_ref = self.thumbnails[yt_obj.thumbnail_url]
        label_ref.configure(image = image_ref)
        
        #self.thumbnails[yt_obj.thumbnail_url].save(correct_name_format(yt_obj.title))

    def new_query(self, yt_obj: YouTube):
        q_obj = tk.Frame(self.query_container, borderwidth=1,  relief="solid")
        self.query_objects[yt_obj.embed_url] = q_obj
        
        thumbnail = tk.Label(q_obj, height = 50, width=50)
        thumbnail.grid(column=0, row=0, sticky = tk.E)
        threading.Thread(target = self.set_image_query, args=[yt_obj, thumbnail]).start()

        d_button = tk.Button(q_obj, text="Download", command=lambda:self.new_download(yt_obj))
        d_button.grid(column = 1, row = 0)
        text = tk.Label(q_obj, text = yt_obj.title if len(yt_obj.title) <= self.title_max_length else yt_obj.title[:self.title_max_length - 3] + "...")
        text.grid(column = 2, row = 0)
        q_obj.grid(row = len(self.query_objects), column=0, sticky=tk.W)

    def search_video(self):
        search_result = Search(self.search_inp.get())
        self.search_inp.delete(0, 'end')
        for key in self.query_objects.keys():
            self.query_objects[key].destroy()
        self.query_objects.clear()

        for yt in search_result.results:
            self.new_query(yt)
            

maingui = maingui("Rpg", "400x400") 
maingui.mainloop()

def get_audio_from_Youtube_obj(obj_list):
    print("Downloading")
    for yt in tqdm(obj_list):
        print(yt.thumbnail_url)
        audio_stream = yt.streams.get_audio_only()
        audio_stream.download(filename = yt.title + ".mp3")

def get_audio_from_link(link_list):
    obj_list = []
    for link in link_list:
        obj_list.append(YouTube(link))
    get_audio_from_Youtube_obj(obj_list)

def get_audio_from_name(name_list, confirm = False):
    obj_list = []
    print("Searching for songs")
    for name in tqdm(name_list):
        s = Search(name)
        if confirm:
            pass
        else:
            obj_list.append(s.results[0])
    get_audio_from_Youtube_obj(obj_list)

exit()
if __name__ == "__main__":
    link_list = []
    while True: 
        
        link_of_the_video = input("Copy & paste the URL of the YouTube video you want to download:- ") 
        link = link_of_the_video.strip()
        if link == "done": 
            break
        else:
            link_list.append(link)

    get_audio_from_name(link_list) 


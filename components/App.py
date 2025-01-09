from models import DataManager
from components import HomeFrame, TaigaFrame, GitHubFrame

import pandas as pd
import tkinter as tk
from tkinter import ttk

import tksheet as tks
import sys

class Application():
    def __init__(self):
        self.root = tk.Tk()
        title = 'Capstone Automation Tool'
        geometry = '1000x800'
        self.root.title(title)
        self.root.geometry(geometry)
        self.root.minsize(1000, 800)
        self.root.maxsize(1000, 800)

        dc = DataManager.DataController()

        self.tabControl = ttk.Notebook(self.root)

        self.home_tab = HomeFrame.HomeFrame(self.tabControl)
        self.taiga_tab = TaigaFrame.TaigaFrame(self.tabControl, dc)
        self.gh_tab = GitHubFrame.GitHubFrame(self.tabControl, dc)

        self.tabControl.add(self.home_tab, text='Home')
        self.tabControl.add(self.taiga_tab, text='Taiga')
        self.tabControl.add(self.gh_tab, text='GitHub')
        self.tabControl.pack(expand = 1, fill ="both") 

        self.root.wm_protocol("WM_DELETE_WINDOW", self.close())

    def close(self):
        self.root.quit()
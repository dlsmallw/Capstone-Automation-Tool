import tkinter as tk
from tkinter import ttk
import ttkthemes
import sv_ttk
import pandas as pd

from models.DataManager import DataController
from components import GitFrame, HomeFrame, TaigaFrame, ReportsFrame
from models.database.RecordDatabase import RecDB

class Application():
    

    def __init__(self):
        self.curr_tab = None
        self.prev_tab = None

        db = RecDB()
        dc = DataController(db)

        title = 'Capstone Automation Tool'
        geometry = '1000x800'

        self.root = tk.Tk()
        self.root.wm_protocol("WM_DELETE_WINDOW", self.close())

        self.root.title(title)
        self.root.geometry(geometry)
        self.root.minsize(1000, 800)
        self.root.maxsize(1000, 800)

        self.tabControl = ttk.Notebook(self.root)
        self.home_tab = HomeFrame.HomeFrame(self.tabControl)
        self.git_tab = GitFrame.GitFrame(self.tabControl, dc, self)
        self.taiga_tab = TaigaFrame.TaigaFrame(self.tabControl, dc, self)
        self.reports_tab = ReportsFrame.ReportsFrame(self.tabControl, self, dc)

        self.tabControl.add(self.home_tab, text='Home')
        self.tabControl.add(self.taiga_tab, text='Taiga')
        self.tabControl.add(self.git_tab, text='Git')
        self.tabControl.add(self.reports_tab, text='Reports')
        self.tabControl.pack(expand = 1, fill ="both") 

        self.tabControl.bind('<<NotebookTabChanged>>', self.tab_change)

        # sv_ttk.set_theme("light")
        # self.root.tk.call("source", "azure.tcl")
        # self.root.tk.call("set_theme", "dark")

        self.root.mainloop()

    def get_root_coords(self):
        self.root.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        center_x = root_x + int(root_w / 2)
        center_y = root_y + int(root_h / 2)
        return center_x, center_y

    def close(self):
        self.root.quit()

    def refresh(self):
        self.root.update()
        self.root.after(1000,self.refresh)

    def tab_change(self, event):
        self.prev_tab = self.curr_tab
        self.curr_tab = event.widget.tab('current')['text']
        if self.curr_tab == 'Reports':
            self.reports_tab.reset_tab()

    def update_to_taiga_data(self):
        self.git_tab.update_to_taiga_data()

    def taiga_data_ready(self) -> bool:
        return self.taiga_tab.taiga_data_ready()
    
    def get_taiga_data(self):
        return self.taiga_tab.get_taiga_data()
    
    def commit_data_ready(self) -> bool:
        return self.git_tab.commit_data_ready()
    
    def get_commit_data(self):
        return self.git_tab.get_commit_data()
    
    def get_taiga_members(self) -> list:
        return self.taiga_tab.get_members()
    
    def get_taiga_sprints(self) -> list:
        return self.taiga_tab.get_sprints()
    
    def get_gh_contributors(self) -> list:
        return self.git_tab.get_contributors()
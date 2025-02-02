import tkinter as tk
from tkinter import ttk
import ttkthemes
import sv_ttk
import pandas as pd

from models import DataManager
from components import GitFrame, HomeFrame, TaigaFrame, ReportsFrame
from models.database.RecordDatabase import RecDB

class Application():
    root = None
    curr_tab = None
    prev_tab = None
    db = None

    def __init__(self):
        db = RecDB()
        dc = DataManager.DataController(db)
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
        self.taiga_tab = TaigaFrame.TaigaFrame(self.tabControl, dc)
        self.git_tab = GitFrame.GitFrame(self.tabControl, dc)
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

    def close(self):
        self.root.quit()

    def refresh(self):
        self.root.update()
        self.root.after(1000,self.refresh)

    def tab_change(self, event):
        # self.prev_tab = self.curr_tab
        # self.curr_tab = event.widget.tab('current')['text']
        
        # if self.curr_tab == 'Reports':
        #     self.reports_tab.update_valid_options()
        # elif self.prev_tab == 'Reports':
        #     self.reports_tab.reset_tab()
        pass

    def taiga_data_ready(self) -> bool:
        return self.taiga_tab.taiga_data_ready()
    
    def get_taiga_data(self):
        return self.taiga_tab.get_taiga_df()
    
    def gh_data_ready(self) -> bool:
        return self.git_tab.gh_data_ready()
    
    def get_gh_data(self):
        return self.git_tab.get_gh_df()
    
    def get_taiga_members(self) -> list:
        return self.taiga_tab.get_members()
    
    def get_taiga_sprints(self) -> list:
        return self.taiga_tab.get_sprints()
    
    def get_gh_contributors(self) -> list:
        return self.git_tab.get_contributors()
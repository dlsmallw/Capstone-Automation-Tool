import tkinter as tk
from tkinter import ttk
import pandas as pd

from models import DataManager
from components import HomeFrame, TaigaFrame, GitHubFrame, ReportsFrame

class Application():
    root = None
    curr_tab = None
    prev_tab = None

    def __init__(self):
        dc = DataManager.DataController()
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
        self.gh_tab = GitHubFrame.GitHubFrame(self.tabControl, dc)
        self.reports_tab = ReportsFrame.ReportsFrame(self.tabControl, self, dc)

        self.tabControl.add(self.home_tab, text='Home')
        self.tabControl.add(self.taiga_tab, text='Taiga')
        self.tabControl.add(self.gh_tab, text='GitHub')
        self.tabControl.add(self.reports_tab, text='Reports')
        self.tabControl.pack(expand = 1, fill ="both") 

        self.tabControl.bind('<<NotebookTabChanged>>', self.tab_change)

        self.root.mainloop()

    def close(self):
        self.root.quit()

    def refresh(self):
        self.root.update()
        self.root.after(1000,self.refresh)

    def tab_change(self, event):
        self.prev_tab = self.curr_tab
        self.curr_tab = event.widget.tab('current')['text']
        
        if self.curr_tab == 'Reports':
            self.reports_tab.update_valid_options()
        elif self.prev_tab == 'Reports':
            self.reports_tab.reset_tab()

    def taiga_data_ready(self) -> bool:
        return self.taiga_tab.taiga_data_ready()
    
    def get_taiga_data(self) -> pd.DataFrame:
        return self.taiga_tab.get_taiga_df()
    
    def gh_data_ready(self) -> bool:
        return self.gh_tab.gh_data_ready()
    
    def get_gh_data(self) -> pd.DataFrame:
        return self.gh_tab.get_gh_df()
    
    def get_taiga_members(self) -> list:
        return self.taiga_tab.get_members()
    
    def get_taiga_sprints(self) -> list:
        return self.taiga_tab.get_sprints()
    
    def get_gh_contributors(self) -> list:
        return self.gh_tab.get_contributors()
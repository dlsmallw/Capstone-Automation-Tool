


import tkinter as tk
from tkinter import ttk



from models import DataManager
from components import HomeFrame, TaigaFrame, GitHubFrame, ReportsFrame

class Application():
    root = None

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
        self.reports_tab = ReportsFrame.ReportsFrame(self.tabControl, dc)

        self.tabControl.add(self.home_tab, text='Home')
        self.tabControl.add(self.taiga_tab, text='Taiga')
        self.tabControl.add(self.gh_tab, text='GitHub')
        self.tabControl.add(self.reports_tab, text='Reports')
        self.tabControl.pack(expand = 1, fill ="both") 

        self.root.mainloop()

    def close(self):
        self.root.quit()

    def refresh(self):
        self.root.update()
        self.root.after(1000,self.refresh)
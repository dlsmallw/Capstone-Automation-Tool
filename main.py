from backend.DataManager import DataController
from components import HomeFrame, TaigaFrame, GitHubFrame

import pandas as pd
import tkinter as tk
from tkinter import ttk

import tksheet as tks

def generate_table(parent, df):
    cols = list(df.columns)
    tree = ttk.Treeview(parent)
    tree.pack(fill='both', expand=True)

    tree['columns'] = cols
    for i in cols:
        tree.column(i, anchor='w')
        tree.heading(i, text=i, anchor='w')

    for index, row in df.iterrows():
        tree.insert("", 0, text=index, values=list(row))

    return tree

def main():
    dc = DataController()
    df = dc.get_gh_master_df()

    root = tk.Tk()
    root.title('Capstone Automation Tool')
    root.geometry('1000x800')
    root.minsize(1000, 800)
    tabControl = ttk.Notebook(root)

    home_tab = HomeFrame.HomeFrame(tabControl)
    taiga_tab = TaigaFrame.TaigaFrame(tabControl, dc)
    gh_tab = GitHubFrame.GitHubFrame(tabControl, dc)

    tabControl.add(home_tab, text='Home')
    tabControl.add(taiga_tab, text='Taiga')
    tabControl.add(gh_tab, text='GitHub')
    tabControl.pack(expand = 1, fill ="both") 

    root.mainloop()

if __name__=="__main__":
    main()
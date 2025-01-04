from backend import AppRunner
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog
import asyncio

class HomeFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        label = ttk.Label(self, text='Home Tab')
        label.pack()

class TaigaFrame(ttk.Frame):
    class ConfigFrame(ttk.Notebook):
        def __init__(self, parent, apprunner: AppRunner.AppController):
            super().__init__(parent)
            self.ar = apprunner
            self.parent = parent

            file_tab = ttk.Frame(self)
            file_sel_widget = self.build_file_sel_widget(file_tab)
            file_sel_widget.pack()
            api_tab = ttk.Frame(self)

            self.add(file_tab, text='From File')
            self.add(api_tab, text='From API')
            # self.pack(expand = 1, fill ="both")

        def file_select(self, field: ttk.Label):
            fp = filedialog.askopenfilename().strip()
            print(fp)
            print(len(fp))

            if fp is not None and fp != '':
                field.config(text=fp, anchor='w')


            

        def build_file_sel_widget(self, parent) -> ttk.Frame:
            widget_frame = ttk.Frame(parent)
            
            us_fp_lbl = tk.Label(widget_frame, text='US Report Filepath:', anchor='e')
            us_fp_readonly = tk.Label(widget_frame, text='No File Selected', anchor='w')
            us_fp_btn = tk.Button(widget_frame, text='Select Report File', command=lambda: self.file_select(us_fp_readonly), padx=1, anchor='e')
            us_fp_lbl.grid(row=0, column=0, padx=(8, 0))
            us_fp_readonly.grid(row=0, column=1, padx=(2, 0))
            us_fp_btn.grid(row=0, column=2, padx=(4, 4))

            task_fp_lbl = tk.Label(widget_frame, text='Task Report Filepath:', anchor='e')
            task_fp_readonly = tk.Label(widget_frame, text='No File Selected', anchor='w')
            task_fp_btn = tk.Button(widget_frame, text='Select Report File', command=lambda: self.file_select(task_fp_readonly), anchor='e')
            task_fp_lbl.grid(row=1, column=0, padx=(8, 0))
            task_fp_readonly.grid(row=1, column=1, padx=(2, 0))
            task_fp_btn.grid(row=1, column=2, padx=(4, 4))

            widget_frame.columnconfigure(0, weight=1)
            widget_frame.columnconfigure(1, weight=3)
            widget_frame.columnconfigure(2, weight=1)
            widget_frame.rowconfigure(0, weight=1)
            widget_frame.rowconfigure(1, weight=1)

            return widget_frame

    class DataFrame(ttk.Frame):
        def __init__(self, parent, apprunner: AppRunner.AppController):
            super().__init__(parent)
            self.ar = apprunner
            self.parent = parent

    def __init__(self, parent, apprunner: AppRunner.AppController):
        super().__init__(parent)
        self.ar = apprunner
        self.parent = parent

        label = ttk.Label(text='Taiga Tab')
        config_frame = self.ConfigFrame(self, apprunner)
        data_frame = self.DataFrame(self, apprunner)

        label.pack()
        config_frame.pack()
        data_frame.pack()

class GitHubFrame(ttk.Frame):
    class ConfigFrame(ttk.Frame):
        def __init__(self, parent, apprunner: AppRunner.AppController):
            super().__init__(parent)
            self.ar = apprunner
            self.parent = parent
    class DataFrame(ttk.Frame):
        def __init__(self, parent, apprunner: AppRunner.AppController):
            super().__init__(parent)
            self.ar = apprunner
            self.parent = parent

    def __init__(self, parent, apprunner: AppRunner.AppController):
        super().__init__(parent)
        self.ar = apprunner
        self.parent = parent

        label = ttk.Label(self, text='GitHub Tab')
        config_frame = self.ConfigFrame(self, apprunner)
        data_frame = self.DataFrame(self, apprunner)

        label.pack()
        config_frame.pack()
        data_frame.pack()

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
    ar = AppRunner.AppController()

    root = tk.Tk() 
    root.title('Capstone Automation Tool')
    root.geometry('1000x800')
    root.minsize(1000, 800)
    tabControl = ttk.Notebook(root)

    home_tab = HomeFrame(tabControl)
    taiga_tab = TaigaFrame(tabControl, ar)
    gh_tab = GitHubFrame(tabControl, ar)

    tabControl.add(home_tab, text='Home')
    tabControl.add(taiga_tab, text='Taiga')
    tabControl.add(gh_tab, text='GitHub')
    tabControl.pack(expand = 1, fill ="both") 

    root.mainloop()

if __name__=="__main__":
    main()
from backend.DataManager import DataController
import tkinter as tk
from tkinter import StringVar, ttk, filedialog
from typing import Type
import pandas as pd
from components import DialogWindow

import tksheet

class TaigaFrame(ttk.Frame):
    root = None
    DialogBox = None

    def __init__(self, parent: Type[tk.Tk], dc: Type[DataController]):
        super().__init__(parent)
        self.dc = dc
        self.root = parent

        Dialog = DialogWindow.Dialog
        Dialog.root = parent
        self.DialogBox = Dialog

        config_frame = ConfigFrame(self, dc)
        data_frame = DataFrame(self, dc)

        config_frame.pack()
        data_frame.pack()

    def dialog(self, msg):
        self.DialogBox(msg)

    def answer_dialog(self, msg):
        win = self.DialogBox(msg, True)
        self.root.wait_window(win.top)
        return win.result

class ConfigFrame(ttk.Notebook):
    parent_frame = None

    def __init__(self, parent: Type[TaigaFrame], dc: Type[DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent

        file_tab = ttk.Frame(self)
        file_sel_widget = self.__build_file_sel_widget(file_tab)
        file_sel_widget.pack(padx=8, pady=8)
        api_tab = ttk.Frame(self)
        api_form_widget = self.__build_api_form(api_tab)
        api_form_widget.pack(padx=8, pady=8)

        self.add(file_tab, text='From File')
        self.add(api_tab, text='From API')
        # self.pack(expand = 1, fill ="both")

    def dialog(self, msg):
        self.parent_frame.dialog(msg=msg)

    def __file_select(self, field: ttk.Label):
        fp = filedialog.askopenfilename().strip()
        if fp is not None and fp != '':
            field.config(text=fp, anchor='w')

    def __build_file_sel_widget(self, parent) -> ttk.Frame:
        widget_frame = ttk.Frame(parent)
        
        us_fp_lbl = tk.Label(widget_frame, text='US Report Filepath:')
        us_fp_readonly = tk.Label(widget_frame, text='No File Selected')
        us_fp_btn = tk.Button(widget_frame, text='Select Report File', command=lambda: self.__file_select(us_fp_readonly), padx=1, anchor='e')
        us_fp_lbl.grid(row=0, column=0)
        us_fp_readonly.grid(row=0, column=1, padx=(2, 0))
        us_fp_btn.grid(row=0, column=2, padx=(4, 0))

        task_fp_lbl = tk.Label(widget_frame, text='Task Report Filepath:')
        task_fp_readonly = tk.Label(widget_frame, text='No File Selected')
        task_fp_btn = tk.Button(widget_frame, text='Select Report File', command=lambda: self.__file_select(task_fp_readonly), anchor='e')
        task_fp_lbl.grid(row=1, column=0)
        task_fp_readonly.grid(row=1, column=1, padx=(2, 0))
        task_fp_btn.grid(row=1, column=2, padx=(4, 0))

        # widget_frame.columnconfigure(0, weight=1)
        # widget_frame.columnconfigure(1, weight=3)
        # widget_frame.columnconfigure(2, weight=1)
        # widget_frame.rowconfigure(0, weight=1)
        # widget_frame.rowconfigure(1, weight=1)

        return widget_frame
    
    def __update_field(self, field: Type[tk.Label], val: Type[str]):
        if val is not None and val != '':
            field.config(text=val, anchor='w')
    
    def __set_url(self, field: Type[tk.Label], url: Type[str], type: Type[str]):
        if url is not None and url != '':
            if type == 'us':
                if 'https://api.taiga.io/api/v1/userstories/csv?uuid=' in url:
                    self.__update_field(field, url)
                    self.dc.set_taiga_us_api_url(url)
                    return
            elif type == 'task':
                if 'https://api.taiga.io/api/v1/tasks/csv?uuid=' in url:
                    self.__update_field(field, url)
                    self.dc.set_taiga_task_api_url(url)
                    return
                
        self.dialog('Invalid URL entered!')

    def __url_update_dialog(self, field: Type[tk.Label], type: Type[str]):
        url = self.parent_frame.answer_dialog(msg='Enter the API URL').strip()
        if url is not None and url != '':
            self.__set_url(field, url, type)
            return
        
        self.dialog('Invalid URL entered!')
        
    
    def __build_api_form(self, parent) -> ttk.Frame:
        widget_frame = ttk.Frame(parent)

        us_api_lbl = tk.Label(widget_frame, text='US Report API URL:')
        us_api_readonly = tk.Label(widget_frame, text='No URL Specified')
        self.__update_field(us_api_readonly, self.dc.get_taiga_us_api_url())
        us_api_btn = tk.Button(widget_frame, text='Set API URL', command=lambda: self.__url_update_dialog(us_api_readonly, 'us'), padx=1, anchor='e')
        us_api_lbl.grid(row=0, column=0)
        us_api_readonly.grid(row=0, column=1, padx=(2, 0))
        us_api_btn.grid(row=0, column=2, padx=(4, 0))

        task_api_lbl = tk.Label(widget_frame, text='Task Report API URL:')
        task_api_readonly = tk.Label(widget_frame, text='No URL Specified')
        self.__update_field(task_api_readonly, self.dc.get_taiga_task_api_url())
        task_api_btn = tk.Button(widget_frame, text='Set API URL', command=lambda: self.__url_update_dialog(task_api_readonly, 'task'), padx=1, anchor='e')
        task_api_lbl.grid(row=1, column=0)
        task_api_readonly.grid(row=1, column=1, padx=(2, 0))
        task_api_btn.grid(row=1, column=2, padx=(4, 0))

        return widget_frame
    
class DataFrame(ttk.Frame):
    parent_frame = None

    def __init__(self, parent: Type[TaigaFrame], dc: Type[DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent
    
    def dialog(self, msg):
        self.parent_frame.dialog(msg)
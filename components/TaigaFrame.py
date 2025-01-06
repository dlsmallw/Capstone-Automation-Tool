from backend.DataManager import DataController
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Type
import pandas as pd
from components import DialogWindow

import tksheet as tks

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

        self.config_frame = ConfigFrame(self, dc)
        self.data_frame = DataFrame(self, dc)

        self.config_frame.pack()
        self.data_frame.pack(fill='both', expand=True)

    def import_from_files(self):
        self.dc.taiga_retrieve_from_files()
        df = self.dc.get_taiga_master_df()
        self.data_frame.build_table(df)

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

        self.add(file_tab, text='From File', sticky='nsew')
        self.add(api_tab, text='From API', sticky='nsew')

    def dialog(self, msg):
        self.parent_frame.dialog(msg=msg)

    def __file_select(self, field: ttk.Label, type: Type[str]):
        fp = filedialog.askopenfilename().strip()
        if fp is not None and fp != '':
            if type == 'us':
                self.dc.set_us_fp(fp=fp)
            elif type == 'task':
                self.dc.set_task_fp(fp=fp)
            else:
                return
            
            field.config(text=fp, anchor='w')

    def __build_file_sel_widget(self, parent) -> ttk.Frame:
        widget_frame = ttk.Frame(parent)
        
        file_sel_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Import from File{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        file_sel_lbl.grid(row=0, columnspan=3, sticky='nsew', pady=(0, 8))
        
        us_fp_lbl = tk.Label(widget_frame, text='US Report Filepath:', width=16, anchor='e')
        us_fp_readonly = tk.Label(widget_frame, text='No File Selected', anchor='w')
        us_fp_btn = tk.Button(widget_frame, text='Select Report File', command=lambda: self.__file_select(us_fp_readonly, 'us'), padx=1, anchor='e')
        us_fp_lbl.grid(row=1, column=0, padx=(4, 0), sticky='nsew')
        us_fp_readonly.grid(row=1, column=1, padx=(2, 0), sticky='nsew')
        us_fp_btn.grid(row=1, column=2, padx=(4, 4))

        task_fp_lbl = tk.Label(widget_frame, text='Task Report Filepath:', width=16, anchor='e')
        task_fp_readonly = tk.Label(widget_frame, text='No File Selected', anchor='w')
        task_fp_btn = tk.Button(widget_frame, text='Select Report File', command=lambda: self.__file_select(task_fp_readonly, 'task'), anchor='e')
        task_fp_lbl.grid(row=2, column=0, padx=(4, 0), pady=(0, 4), sticky='nsew')
        task_fp_readonly.grid(row=2, column=1, padx=(2, 0), pady=(0, 4), sticky='nsew')
        task_fp_btn.grid(row=2, column=2, padx=(4, 4), pady=(0, 4))

        import_data_btn = tk.Button(widget_frame, text='Import from Files', command=lambda: self.parent_frame.import_from_files(), anchor='e')
        import_data_btn.grid(row=3, columnspan=3)

        return widget_frame
    
    def __update_field(self, field: Type[tk.Label], val: Type[str]):
        if val is not None and val != '':
            field.config(text=val, anchor='w')
    
    def __set_url(self, field: Type[tk.Label], url: Type[str], type: Type[str]):
        if url is not None and url != '':
            if type == 'us':
                if 'https://api.taiga.io/api/v1/userstories/csv?uuid=' in url:
                    self.dc.set_taiga_us_api_url(url)
                    return
            elif type == 'task':
                if 'https://api.taiga.io/api/v1/tasks/csv?uuid=' in url:
                    self.dc.set_taiga_task_api_url(url)
                    return
            else:
                return

            self.__update_field(field, url)
                
        self.dialog('Invalid URL entered!')

    def __url_update_dialog(self, field: Type[tk.Label], type: Type[str]):
        url = self.parent_frame.answer_dialog(msg='Enter the API URL').strip()
        if url is not None and url != '':
            self.__set_url(field, url, type)
            return
        
        self.dialog('Invalid URL entered!')
        
    
    def __build_api_form(self, parent) -> ttk.Frame:
        widget_frame = ttk.Frame(parent)

        api_config_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Import from API{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        api_config_lbl.grid(row=0, columnspan=3, sticky='nsew', pady=(0, 8))

        us_api_lbl = tk.Label(widget_frame, text='US Report API URL:', width=16, anchor='e')
        us_api_readonly = tk.Label(widget_frame, text='No URL Specified')
        self.__update_field(us_api_readonly, self.dc.get_taiga_us_api_url())
        us_api_btn = tk.Button(widget_frame, text='Set API URL', command=lambda: self.__url_update_dialog(us_api_readonly, 'us'), padx=1, anchor='e')
        us_api_lbl.grid(row=1, column=0, sticky='nsew')
        us_api_readonly.grid(row=1, column=1, padx=(2, 0), sticky='nsew')
        us_api_btn.grid(row=1, column=2, padx=(4, 4))

        task_api_lbl = tk.Label(widget_frame, text='Task Report API URL:', width=16, anchor='e')
        task_api_readonly = tk.Label(widget_frame, text='No URL Specified')
        self.__update_field(task_api_readonly, self.dc.get_taiga_task_api_url())
        task_api_btn = tk.Button(widget_frame, text='Set API URL', command=lambda: self.__url_update_dialog(task_api_readonly, 'task'), padx=1, anchor='e')
        task_api_lbl.grid(row=2, column=0, pady=(0, 4), sticky='nsew')
        task_api_readonly.grid(row=2, column=1, padx=(2, 0), pady=(0, 4), sticky='nsew')
        task_api_btn.grid(row=2, column=2, padx=(4, 4), pady=(0, 4))

        import_data_btn = tk.Button(widget_frame, text='Import from API', command=lambda: self.parent_frame.import_from_files(), anchor='e')
        import_data_btn.grid(row=3, columnspan=3)

        return widget_frame
    
class DataFrame(ttk.Frame):
    parent_frame = None
    sheet = None

    def __init__(self, parent: Type[TaigaFrame], dc: Type[DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent

    def build_table(self, df):
        if self.sheet is not None:
            self.sheet.delete()

        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(0, weight = 1)
        self.sheet = tks.Sheet(self, header=list(df.columns), data=df.values.tolist())
        self.sheet.enable_bindings('all')
        self.sheet.set_all_cell_sizes_to_text(True)
        self.sheet.column_width(0, 20)
        self.sheet.grid(row=0, column=0, sticky='nsew')
    
    def dialog(self, msg):
        self.parent_frame.dialog(msg)
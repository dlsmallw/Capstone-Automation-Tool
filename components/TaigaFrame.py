from backend.DataManager import DataController
import tkinter as tk
from tkinter import ttk, filedialog, StringVar, OptionMenu
from typing import Type
import pandas as pd
from components import DialogWindow
from tkcalendar import DateEntry

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

        self.config_frame.pack(fill='x', anchor='n', pady=(0, 10))
        self.data_frame.pack(fill='both', expand=True, anchor='n')

    def import_from_files(self):
        self.dc.taiga_retrieve_from_files()
        df = self.dc.get_taiga_master_df()
        self.data_frame.build_data_display(df)

    def dialog(self, msg):
        self.DialogBox(msg)

    def answer_dialog(self, msg):
        win = self.DialogBox(msg, True)
        self.root.wait_window(win.top)
        return win.result

class ConfigFrame(ttk.Frame):
    def __init__(self, parent: Type[TaigaFrame], dc: Type[DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent
        self.notebook = ttk.Notebook(self)

        file_tab = ttk.Frame(self.notebook)
        file_sel_widget = self.__build_file_sel_widget(file_tab)
        file_sel_widget.pack(padx=8, pady=8, fill='x')
        api_tab = ttk.Frame(self.notebook)
        api_form_widget = self.__build_api_form(api_tab)
        api_form_widget.pack(padx=8, pady=8, fill='x')

        self.notebook.add(file_tab, text='From File')
        self.notebook.add(api_tab, text='From API')
        self.notebook.pack()

    def generate_field_obj(self, field_frame, lbl_str, lbl_width, target_obj):
        field_lbl = tk.Label(field_frame, text=lbl_str, width=lbl_width, anchor='e')
        target_obj.config()

        field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')

        return target_obj

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

            if self.us_fp_readonly['text'] != 'No File Selected' and self.task_fp_readonly['text'] != 'No File Selected':
                self.import_data_from_file_btn['state'] = 'normal'

    def __build_file_sel_widget(self, parent) -> ttk.Frame:
        widget_frame = ttk.Frame(parent)
        file_sel_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Import from File{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        
        fp_sel_frame = ttk.Frame(widget_frame)

        # User Story File Select
        us_fp_lbl = tk.Label(fp_sel_frame, text='US Report Filepath:', width=16, anchor='e')
        self.us_fp_readonly = tk.Label(fp_sel_frame, text='No File Selected', anchor='w')
        us_fp_btn = tk.Button(fp_sel_frame, text='Select Report File', command=lambda: self.__file_select(self.us_fp_readonly, 'us'), padx=1, anchor='e')
        us_fp_lbl.grid(row=0, column=0, padx=(4, 0))
        self.us_fp_readonly.grid(row=0, column=1, padx=(2, 0))
        us_fp_btn.grid(row=0, column=2, padx=(4, 4))

        # Task File Select
        task_fp_lbl = tk.Label(fp_sel_frame, text='Task Report Filepath:', width=16, anchor='e')
        self.task_fp_readonly = tk.Label(fp_sel_frame, text='No File Selected', anchor='w')
        task_fp_btn = tk.Button(fp_sel_frame, text='Select Report File', command=lambda: self.__file_select(self.task_fp_readonly, 'task'), anchor='e')
        task_fp_lbl.grid(row=1, column=0, padx=(4, 0), pady=(0, 4))
        self.task_fp_readonly.grid(row=1, column=1, padx=(2, 0), pady=(0, 4))
        task_fp_btn.grid(row=1, column=2, padx=(4, 4))

        # Buttons for importing and exporting data
        btn_frame = ttk.Frame(widget_frame)
        self.import_data_from_file_btn = tk.Button(btn_frame, text='Import from Files', state='disabled', command=lambda: self.parent_frame.import_from_files())
        self.export_data_from_file_btn = tk.Button(btn_frame, text='Export to Excel', state='disabled', command=lambda: print())
        self.import_data_from_file_btn.grid(row=0, column=0, padx=2, sticky='nsew')
        self.export_data_from_file_btn.grid(row=0, column=1, padx=2, sticky='nsew')

        file_sel_lbl.pack(fill='x', pady=(0, 8))
        fp_sel_frame.pack(pady=(0, 4))
        btn_frame.pack()

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
    filter_panel : Type[ttk.Frame] = None
    sheet : Type[tks.Sheet] = None

    def __init__(self, parent: Type[TaigaFrame], dc: Type[DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent

    def generate_field_obj(self, field_frame, lbl_str, target_obj):
        field_lbl = tk.Label(field_frame, text=lbl_str, anchor='e')
        target_obj.config()

        field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')

        return target_obj

    def build_filter_panel(self) -> ttk.Frame: 
        widget_frame = ttk.Frame(self)

        filters_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Filter Options{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        
        filters_frame = ttk.Frame(widget_frame)
        # date_frame = ttk.Frame(filters_frame)
        opt_frame = ttk.Frame(filters_frame)

        us_select_def = StringVar(opt_frame)
        us_options = ['', 'Storyless'] + self.dc.get_user_stories()
        us_select_def.set(us_options[0])

        sprint_select_def = StringVar(opt_frame)
        sprint_options = [''] + self.dc.get_sprints()
        sprint_select_def.set(sprint_options[0])

        user_select_def = StringVar(opt_frame)
        user_options = ['', 'Unassigned'] + self.dc.get_members()
        user_select_def.set(user_options[0])

        # from_frame = ttk.Frame(date_frame)
        # from_date_entry = self.generate_field_obj(from_frame, 'From Date:', self.CustomDateEntry(from_frame))

        # to_frame = ttk.Frame(date_frame)
        # to_date_entry = self.generate_field_obj(to_frame, 'To Date:', DateEntry(to_frame))

        us_frame = ttk.Frame(opt_frame)
        us_filter = self.generate_field_obj(us_frame, 'User Story:', OptionMenu(us_frame, us_select_def, *us_options))

        sprint_frame = ttk.Frame(opt_frame)
        sprint_filter = self.generate_field_obj(sprint_frame, 'Sprint:', OptionMenu(sprint_frame, sprint_select_def, *sprint_options))

        user_frame = ttk.Frame(opt_frame)
        user_filter = self.generate_field_obj(user_frame, 'User:', OptionMenu(user_frame, user_select_def, *user_options))
        
        # from_frame.grid(row=0, column=0)
        # to_frame.grid(row=0, column=1)

        us_frame.grid(row=0, column=0, sticky='nsew')
        sprint_frame.grid(row=0, column=1, sticky='nsew')
        user_frame.grid(row=0, column=2, sticky='nsew')

        filters_lbl.pack(fill='x', pady=(0, 5))
        # date_frame.pack(fill='x', expand=True)
        opt_frame.pack()
        filters_frame.pack()

        return widget_frame

    def build_table(self, df) -> tks.Sheet:
        sheet = tks.Sheet(self, header=list(df.columns), data=df.values.tolist())
        sheet.enable_bindings('all')

        total_width = 0
        for i in range(6):
            text_width = sheet.get_column_text_width(i)
            total_width += text_width
            sheet.column_width(i, text_width)

        sheet.column_width(6, 450)

        return sheet

    def build_data_display(self, df):
        if self.filter_panel is not None:
            self.filter_panel.destroy()

        if self.sheet is not None:
            self.sheet.delete()

        self.filter_panel = self.build_filter_panel()
        self.sheet = self.build_table(df)

        self.filter_panel.pack(fill='x', pady=(0, 10))
        self.sheet.pack(fill='both')

    def table_to_dataframe(self):
        df = self.sheet.get_data()
        return df
    
    def dialog(self, msg):
        self.parent_frame.dialog(msg)

    class CustomDateEntry(DateEntry):
        def __init__(self, master=None, **kw):
            super().__init__(master, **kw)
            self.delete(0, "end")
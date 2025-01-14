import tkinter as tk
from tkinter import ttk, filedialog, StringVar
import tksheet as tks

from typing import Type
import pandas as pd
import numpy as np
import threading

from models import DataManager
from components import DialogWindow
from components.CustomComponents import CustomDateEntry, CustomOptionMenu

class TaigaFrame(ttk.Frame):
    root = None
    parent_frame = None
    DialogBox = None

    def __init__(self, parent: Type[ttk.Notebook], dc: Type[DataManager.DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent
        self.root = parent.master

        Dialog = DialogWindow.Dialog
        Dialog.root = parent
        self.DialogBox = Dialog

        self.config_frame = ConfigFrame(self, dc)
        self.data_frame = DataFrame(self, dc)

        self.config_frame.pack(fill='x', anchor='n', pady=(0, 10))
        self.data_frame.pack(fill='both', expand=True, anchor='n')

    def refresh(self):
        self.root.update()
        self.root.after(1000,self.refresh)

    def start_file_import_thread(self):
        self.refresh()
        threading.Thread(target=self.import_from_files).start()

    def start_api_import_thread(self):
        self.refresh()
        threading.Thread(target=self.import_from_api).start()
    
    def import_from_files(self):
        temp_lbl = ttk.Label(self.config_frame, text='Handling Taiga File Import Call, Please Wait...')
        temp_lbl.pack()

        try:
            self.dc.taiga_retrieve_from_files()
            df = self.dc.get_taiga_master_df()
            self.data_frame.build_data_display(df)
        except:
            self.dialog('Failed to import data')
        finally:
            temp_lbl.destroy()

    def import_from_api(self):
        temp_lbl = ttk.Label(self.config_frame, text='Handling Taiga API Import Call, Please Wait...')
        temp_lbl.pack()

        try:
            self.dc.taiga_retrieve_from_api()
            df = self.dc.get_taiga_master_df()
            self.data_frame.build_data_display(df)
        except:
            self.dialog('Failed to import data')
        finally:
            temp_lbl.destroy()

    def taiga_data_ready(self) -> bool:
        return self.data_frame.taiga_data_ready()
    
    def get_taiga_df(self) -> pd.DataFrame:
        return self.data_frame.get_taiga_df()
    
    def get_members(self) -> list:
        return self.data_frame.get_members()
    
    def get_sprints(self) -> list:
        return self.data_frame.get_sprints()

    def dialog(self, msg):
        self.DialogBox(msg)

    def answer_dialog(self, msg):
        win = self.DialogBox(msg, True)
        self.root.wait_window(win.top)
        return win.result

class ConfigFrame(ttk.Frame):
    def __init__(self, parent: Type[TaigaFrame], dc: Type[DataManager.DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent
        self.notebook = ttk.Notebook(self)

        file_tab = ttk.Frame(self.notebook)
        file_sel_widget = self.__build_file_sel_widget(file_tab)
        file_sel_widget.pack(padx=8, pady=8, fill='x')
        api_tab = ttk.Frame(self.notebook)
        api_form_widget = self.__build_api_form(api_tab)
        api_form_widget.pack(fill='x', padx=8, pady=8)

        self.notebook.add(file_tab, text='From File')
        self.notebook.add(api_tab, text='From API')
        self.notebook.pack()

    def __generate_field_obj(self, field_frame, row, lbl_str, lbl_width, target_obj, btn_obj=None):
        field_lbl = tk.Label(field_frame, text=lbl_str, width=lbl_width, anchor='e')
        field_lbl.grid(row=row, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=row, column=1, padx=(1, 2), sticky='nsew')
        if btn_obj is not None:
            btn_obj.grid(row=row, column=2, padx=(4, 4))
        return target_obj

    def dialog(self, msg):
        self.parent_frame.dialog(msg=msg)

    def __file_select(self, field: Type[tk.Label], type: Type[str]):
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
        self.us_fp_readonly = self.__generate_field_obj(fp_sel_frame, 
                                                      0, 
                                                      'US Report Filepath:', 
                                                      16, 
                                                      tk.Label(fp_sel_frame, text='No File Selected', anchor='w'), 
                                                      tk.Button(fp_sel_frame, text='Select Report File', command=lambda: self.__file_select(self.us_fp_readonly, 'us'), anchor='e'))

        # Task File Select
        self.task_fp_readonly = self.__generate_field_obj(fp_sel_frame, 
                                                      1, 
                                                      'Task Report Filepath:', 
                                                      16, 
                                                      tk.Label(fp_sel_frame, text='No File Selected', anchor='w'), 
                                                      tk.Button(fp_sel_frame, text='Select Report File', command=lambda: self.__file_select(self.task_fp_readonly, 'task'), anchor='e'))

        # Buttons for importing and exporting data
        btn_frame = ttk.Frame(widget_frame)
        self.import_data_from_file_btn = tk.Button(btn_frame, text='Import from Files', state='disabled', command=lambda: self.parent_frame.start_file_import_thread())
        self.import_data_from_file_btn.grid(row=0, column=0, padx=2, sticky='nsew')

        file_sel_lbl.pack(fill='x', pady=(0, 8))
        fp_sel_frame.pack(pady=(0, 4))
        btn_frame.pack()

        return widget_frame
    
    def __update_field(self, field: Type[tk.Label], val: Type[str]):
        if val is not None and val != '':
            field.config(text=val, anchor='w')

            if self.us_api_readonly['text'] != 'No URL Specified' and self.task_api_readonly['text'] != 'No URL Specified':
                self.import_from_api_btn['state'] = 'normal'
    
    def __set_url(self, field: Type[tk.Label], url: Type[str], type: Type[str]):
        if url is not None and url != '':
            if type == 'us':
                if 'https://api.taiga.io/api/v1/userstories/csv?uuid=' in url:
                    self.dc.set_taiga_us_api_url(url)
                    self.__update_field(field, url)
                    return
            elif type == 'task':
                if 'https://api.taiga.io/api/v1/tasks/csv?uuid=' in url:
                    self.dc.set_taiga_task_api_url(url)
                    self.__update_field(field, url)
                    return
            else:
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

        api_config_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Import from API{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')

        api_config_frame = ttk.Frame(widget_frame)

        self.us_api_readonly = self.__generate_field_obj(api_config_frame, 
                                                         0, 
                                                         'US Report API URL:', 
                                                         16, 
                                                         tk.Label(api_config_frame, text='No URL Specified'), 
                                                         tk.Button(api_config_frame, text='Set API URL', command=lambda: self.__url_update_dialog(self.us_api_readonly, 'us'), anchor='e'))
        
        self.task_api_readonly = self.__generate_field_obj(api_config_frame, 
                                                         1, 
                                                         'Task Report API URL:', 
                                                         16, 
                                                         tk.Label(api_config_frame, text='No URL Specified'), 
                                                         tk.Button(api_config_frame, text='Set API URL', command=lambda: self.__url_update_dialog(self.task_api_readonly, 'task'), anchor='e'))
        

        # Buttons for importing and exporting data
        btn_frame = ttk.Frame(widget_frame)
        self.import_from_api_btn = tk.Button(btn_frame, text='Import from API', state='disabled', command=lambda: self.parent_frame.start_api_import_thread(), anchor='e')
        self.import_from_api_btn.grid(row=0, column=0, padx=2, sticky='nsew')

        api_config_lbl.pack(fill='x', pady=(0, 8))
        api_config_frame.pack(pady=(0, 4))
        btn_frame.pack()

        self.__update_field(self.us_api_readonly, self.dc.get_taiga_us_api_url())
        self.__update_field(self.task_api_readonly, self.dc.get_taiga_task_api_url())

        return widget_frame
    
class DataFrame(ttk.Frame):
    parent_frame : Type[TaigaFrame] = None
    filter_panel : Type[ttk.Frame] = None
    btn_frame : Type[ttk.Frame] = None
    sheet : Type[tks.Sheet] = None
    master_df : Type[pd.DataFrame] = None
    sheet_master_df : Type[pd.DataFrame] = None
    col_widths = None

    def __init__(self, parent: Type[TaigaFrame], dc: Type[DataManager.DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent

        data_ready = self.dc.taiga_data_ready()
        if data_ready:
            self.master_df = self.dc.get_taiga_master_df()
            self.build_data_display(self.master_df)

    def __dialog(self, msg):
        self.parent_frame.dialog(msg)

    def taiga_data_ready(self) -> bool:
        return self.sheet_master_df is not None
    
    def get_taiga_df(self) -> pd.DataFrame:
        return self.sheet_master_df.copy(deep=True)
    
    def sheet_df_col_to_list(self, col_lbl) -> list:
        df = self.sheet_master_df[col_lbl].copy(deep=True)
        self.__inv_val_to_none(df)
        df.dropna(inplace=True)
        df = df.drop_duplicates(keep='first').reset_index(drop=True)
        return df.tolist()
    
    def get_members(self) -> list:
        return self.sheet_df_col_to_list('assigned_to')
    
    def get_sprints(self) -> list:
        return self.sheet_df_col_to_list('sprint')

    def __destroy_frames(self):
        if self.filter_panel is not None:
            self.filter_panel.destroy()
        if self.btn_frame is not None:
            self.btn_frame.destroy()
        if self.sheet is not None:
            self.sheet.destroy()

    def __generate_field_obj(self, field_frame, lbl_str, target_obj):
        field_lbl = tk.Label(field_frame, text=lbl_str, anchor='e')

        field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')

        return target_obj

    def __convert_to_str(self, val):
        if val == -1 or pd.isna(val):
            return 'Storyless'
        else:
            return f'{int(val)}'
    
    def __convert_from_str(self, str_val):
        if str_val == 'Storyless' or str_val == '' or pd.isna(str_val):
            return None
        else:
            return int(str_val)
        
    def __inv_val_to_none(self, df: Type[pd.DataFrame]):
        df.replace(['', 'None', 'nan', 'NaN', np.nan], [None, None, None, None, None], inplace=True)
    
    def __dataframe_to_table_format(self, df_to_format: Type[pd.DataFrame]):
        df = df_to_format.copy(deep=True)
        self.__inv_val_to_none(df)
        df['user_story'] = df['user_story'].apply(lambda x: self.__convert_to_str(x))
        return df

    def __table_to_dataframe_format(self, df_to_format: Type[pd.DataFrame]):
        df = df_to_format.copy(deep=True)
        df['user_story'] = df['user_story'].apply(lambda x: self.__convert_from_str(x))
        return df
    
    def __parse_table_data_to_df(self):
        headers = self.sheet.headers()
        num_rows = self.sheet.get_total_rows()

        if num_rows > 0:
            if self.sheet.get_total_rows() == 1:
                data = []
                data.append(self.sheet.get_data())
            else:
                data = self.sheet.get_data()

            df = pd.DataFrame(data, columns=headers)
            df.replace('', None, inplace=True)
            df.dropna(how='all', inplace=True)

            formatted_df = self.__table_to_dataframe_format(df)
        else:
            formatted_df = self.sheet_master_df
        
        return formatted_df
    
    def __merge_dataframes(self, master_df, new_df):
        self.__inv_val_to_none(master_df)
        self.__inv_val_to_none(new_df)
        master_df.set_index('task', inplace=True)
        master_df.update(new_df.set_index('task'))
        master_df.reset_index(inplace=True)
        master_df.sort_values(['sprint', 'user_story', 'task'], ascending=[True, True, True])
        return master_df[['sprint', 'sprint_start', 'sprint_end', 'user_story', 'points', 'task', 'assigned_to', 'coding', 'subject']]

    def __update_sheet_df(self, new_df):
        if self.sheet_master_df is not None:
            master_copy = self.sheet_master_df.copy(deep=True)
            new_df_copy = new_df.copy(deep=True)
            master_copy = self.__merge_dataframes(master_copy, new_df_copy)
            self.sheet_master_df = master_copy.sort_values(['sprint', 'user_story', 'task'], ascending=[True, True, True])
        else:
            self.master_df = new_df
            self.sheet_master_df = new_df

    def __apply_filters(self, 
                        from_date_field: Type[CustomDateEntry], 
                        to_date_field: Type[CustomDateEntry], 
                        us_field: Type[CustomOptionMenu], 
                        sprint_field: Type[CustomOptionMenu], 
                        user_field: Type[CustomOptionMenu]
                        ):
        old_df = self.__parse_table_data_to_df()
        self.__update_sheet_df(old_df)
        df = self.sheet_master_df

        filter_applied = False

        if from_date_field.date_selected():
            filter_applied = True
            from_date = from_date_field.get_date()
            df = df[pd.to_datetime(df['sprint_end']) >= pd.to_datetime(from_date)]
        if to_date_field.date_selected():
            filter_applied = True
            to_date = to_date_field.get_date()
            df = df[pd.to_datetime(df['sprint_start']) <= pd.to_datetime(to_date)]
        if us_field.selection_made():
            filter_applied = True
            us = us_field.get_selection()
            if us != 'Storyless':
                df = df[df['user_story'] == int(us)]
            else:
                df = df[df['user_story'] == -1]
        if sprint_field.selection_made():
            filter_applied = True
            sprint = sprint_field.get_selection()
            df = df[df['sprint'] == sprint]
        if user_field.selection_made():
            filter_applied = True
            user = user_field.get_selection()
            df = df[df['assigned_to'] == user]

        if filter_applied:
            self.clear_filters_btn['state'] = 'normal'

        self.change_table(df)

    def __clear_filters(self, 
                        from_date_field: Type[CustomDateEntry], 
                        to_date_field: Type[CustomDateEntry], 
                        us_field: Type[CustomOptionMenu], 
                        sprint_field: Type[CustomOptionMenu], 
                        user_field: Type[CustomOptionMenu]
                        ):
        df = self.__parse_table_data_to_df()
        self.__update_sheet_df(df)

        from_date_field.clear_date()
        to_date_field.clear_date()
        us_field.reset()
        sprint_field.reset()
        user_field.reset()

        self.clear_filters_btn['state'] = 'disabled'
        self.change_table(self.sheet_master_df)

    def __save_table_data(self):
        df = self.__parse_table_data_to_df()
        self.sheet_master_df = df
        self.master_df = self.sheet_master_df
        self.dc.set_taiga_master_df(df)
        self.dc.store_raw_taiga_data()

    def __clear_data(self):
        self.dc.clear_taiga_data()
        self.master_df = None
        self.sheet_master_df = None
        self.__destroy_frames()

    def __build_filter_panel(self) -> ttk.Frame: 
        widget_frame = ttk.Frame(self, borderwidth=2, relief='ridge')

        filters_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Filter Options{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        
        filters_frame = ttk.Frame(widget_frame)
        date_frame = ttk.Frame(filters_frame)
        opt_frame = ttk.Frame(filters_frame)
        btn_frame = ttk.Frame(filters_frame)

        us_select_def = StringVar(opt_frame)
        us_options = ['', 'Storyless'] + self.dc.get_user_stories()
        us_select_def.set(us_options[0])

        sprint_select_def = StringVar(opt_frame)
        sprint_options = [''] + self.dc.get_sprints()
        sprint_select_def.set(sprint_options[0])

        user_select_def = StringVar(opt_frame)
        user_options = ['', 'Unassigned'] + self.dc.get_members()
        user_select_def.set(user_options[0])

        # Date Filters
        from_frame = ttk.Frame(date_frame)
        to_frame = ttk.Frame(date_frame)

        from_date_entry = self.__generate_field_obj(from_frame, 'From Date:', CustomDateEntry(from_frame, width=8))
        to_date_entry = self.__generate_field_obj(to_frame, 'To Date:', CustomDateEntry(to_frame, width=8))
        from_frame.grid(row=0, column=0)
        to_frame.grid(row=0, column=1)

        # Field Filters
        us_frame = ttk.Frame(opt_frame)
        sprint_frame = ttk.Frame(opt_frame)
        user_frame = ttk.Frame(opt_frame)

        us_filter = self.__generate_field_obj(us_frame, 'User Story:', CustomOptionMenu(us_frame, us_select_def, *us_options))
        sprint_filter = self.__generate_field_obj(sprint_frame, 'Sprint:', CustomOptionMenu(sprint_frame, sprint_select_def, *sprint_options))
        user_filter = self.__generate_field_obj(user_frame, 'User:', CustomOptionMenu(user_frame, user_select_def, *user_options))
        us_frame.grid(row=0, column=0, sticky='nsew')
        sprint_frame.grid(row=0, column=1, sticky='nsew')
        user_frame.grid(row=0, column=2, sticky='nsew')

        # Buttons
        apply_filters_btn = tk.Button(btn_frame, 
                                      text='Apply Filters', 
                                      command=lambda: self.__apply_filters(from_date_entry, to_date_entry, us_filter, sprint_filter, user_filter))
        self.clear_filters_btn = tk.Button(btn_frame, 
                                      text='Clear Filters', 
                                      state='disabled',
                                      command=lambda: self.__clear_filters(from_date_entry, to_date_entry, us_filter, sprint_filter, user_filter))
        apply_filters_btn.grid(row=0, column=0, padx=2, sticky='nsew')
        self.clear_filters_btn.grid(row=0, column=1, padx=2, sticky='nsew')

        filters_lbl.pack(fill='x', pady=(0, 5))
        date_frame.pack(fill='x', expand=True)
        opt_frame.pack(pady=2)
        btn_frame.pack(pady=2)
        filters_frame.pack()
        return widget_frame
        
    def __build_table_btn_frame(self) -> ttk.Frame:
        btn_frame = ttk.Frame(self)
        save_data_btn = tk.Button(btn_frame, text='Save Current Table', command=lambda: self.__save_table_data(), padx=1)
        clear_data_btn = tk.Button(btn_frame, text='Clear All Taiga Data', command=lambda: self.__clear_data(), padx=1)
        save_data_btn.grid(row=0, column=0, sticky='nsew', padx=2)
        clear_data_btn.grid(row=0, column=1, sticky='nsew', padx=2)
        return btn_frame
    
    def __build_table(self, df) -> tks.Sheet:
        formatted_df = self.__dataframe_to_table_format(df)
        formatted_df.sort_values(by='sprint_start', ascending=True, inplace=True)
        sheet = tks.Sheet(self, header=list(formatted_df.columns), data=formatted_df.values.tolist())
        sheet.enable_bindings('all')
        # sheet.height_and_width(height=300, width=1000)

        if self.col_widths is None:
            column_widths = []
            index = 0
            for column in formatted_df.columns:
                text_width = sheet.get_column_text_width(index)
                if column == 'subject':
                    text_width = 285

                column_widths.append(text_width)
                index += 1

            self.col_widths = column_widths

        sheet.set_column_widths(self.col_widths)
        return sheet

    def build_data_display(self, df):
        self.__destroy_frames()
        self.__update_sheet_df(df)

        self.filter_panel = self.__build_filter_panel()
        self.btn_frame = self.__build_table_btn_frame()
        self.sheet = self.__build_table(self.sheet_master_df)

        self.filter_panel.pack(fill='x', pady=(0, 5))
        self.btn_frame.pack(fill='x', pady=(0, 5), anchor='e')
        self.sheet.pack(fill='both', expand=True, pady=(0, 5))

    def change_table(self, df):
        self.sheet.destroy()
        self.sheet = self.__build_table(df)
        self.sheet.pack(fill='both', expand=True)
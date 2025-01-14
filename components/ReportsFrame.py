import tkinter as tk
from tkinter import ttk, filedialog, StringVar
import tksheet as tks

from typing import Type
import pandas as pd
import numpy as np
import os

from models import DataManager
from components import DialogWindow
from components.CustomComponents import CustomDateEntry, CustomOptionMenu

class ReportsFrame(ttk.Frame):
    root_app = None
    parent_frame = None
    DialogBox = None

    report_filter_container = None
    report_filter_frame = None

    loading_msg_frame = None

    curr_sel = None
    prev_sel = None
    

    def __init__(self, parent_frame: Type[tk.Tk], root_app, dc: Type[DataManager.DataController]):
        super().__init__(parent_frame)
        self.parent_frame = parent_frame
        self.root_app = root_app
        self.dc = dc

        Dialog = DialogWindow.Dialog
        Dialog.root = parent_frame
        self.DialogBox = Dialog

        tab_lbl = ttk.Label(self, text=f'{' ' * 4}Capstone Report Generation{' ' * 4}', font=('Arial', 20), borderwidth=2, relief='ridge', anchor='center')
        options_panel = self.build_options_frame()
        self.preview_frame = self.DataPreviewFrame(self)

        tab_lbl.pack(fill='x')
        options_panel.pack()
        self.preview_frame.pack(fill='both', expand=True, pady=5, anchor='n')

    def gh_data_ready(self) -> bool:
        return self.root_app.gh_data_ready()
    
    def get_gh_data(self) -> pd.DataFrame:
        return self.root_app.get_gh_data()
    
    def get_contributors(self) -> list:
        return self.root_app.get_gh_contributors()
    
    def taiga_data_ready(self) -> bool:
        return self.root_app.taiga_data_ready()
    
    def get_taiga_data(self) -> pd.DataFrame:
        return self.root_app.get_taiga_data()
    
    def get_sprints(self) -> list:
        return self.root_app.get_taiga_sprints()
    
    def get_members(self) -> list:
        return self.root_app.get_taiga_members()
    
    def update_valid_options(self):
        t_data_ready = self.taiga_data_ready()
        gh_data_ready = self.gh_data_ready()
        self.mtr_rad_btn['state'] = self.wsr_rad_btn['state'] = 'normal' if t_data_ready else 'disabled'
        self.mgr_rad_btn['state'] = 'normal' if gh_data_ready else 'disabled'
        self.icr_rad_btn['state'] = 'normal' if gh_data_ready else 'disabled'

    def reset_tab(self):
        self.sel_rb.set(None)
        self.curr_sel = self.prev_sel = None
        self.reset_options_frame()
        self.preview_frame.reset_frame()

    def disable_report_sel(self):
        self.mtr_rad_btn['state'] = \
        self.wsr_rad_btn['state'] = \
        self.mgr_rad_btn['state'] = \
        self.icr_rad_btn['state'] = 'disabled'

    def enable_report_sel(self):
        self.sel_rb.set(None)
        self.curr_sel = self.prev_sel = None
        self.update_valid_options()

    def reset_options_frame(self):
        if self.report_filter_frame is not None:
            self.report_filter_frame.destroy()
        self.report_filter_frame = ttk.Frame(self.report_filter_container)
        self.report_filter_frame.pack()

    def dialog(self, msg):
        self.DialogBox(msg)

    def answer_dialog(self, msg):
        win = self.DialogBox(msg, True)
        self.root.wait_window(win.top)
        return win.result
    
    def __generate_field_obj(self, field_frame, lbl_str, target_obj):
        field_lbl = tk.Label(field_frame, text=lbl_str, anchor='e')
        field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')
        return target_obj
    
    def switch_report_type(self):
        self.prev_sel = self.curr_sel
        self.curr_sel = self.sel_rb.get()

        if self.prev_sel != self.curr_sel:
            self.reset_options_frame()
            match self.curr_sel:
                case 'mtr':
                    if self.taiga_data_ready():
                        self.temp_load_msg('Master Taiga Report')
                        self.mtr_options_frame()
                    return
                case 'mgr':
                    if self.gh_data_ready():
                        self.temp_load_msg('Master GitHub Report')
                        self.mgr_options_frame()
                    return
                case 'wsr':
                    if self.root_app.taiga_data_ready():
                        self.temp_load_msg('Work Summary Report')
                        self.wsr_options_frame()
                    return
                case 'icr':
                    if self.gh_data_ready():
                        self.temp_load_msg('Individual Contributions Report')
                        self.icr_options_frame()
                    return
                case _:
                    return
    def destroy_temp_load_msg_frame(self):
        if self.loading_msg_frame is not None:
            self.loading_msg_frame.destroy()
                
    def temp_load_msg(self, report_type):
        self.destroy_temp_load_msg_frame()
        self.loading_msg_frame = ttk.Frame(self.report_filter_container)
        temp_msg = ttk.Label(self.loading_msg_frame, text=f'Loading {report_type} filter options...')

        temp_msg.pack()
        self.loading_msg_frame.pack()

    def generate_taiga_project_field(self, parent):
        instr_str = "**NOTE: The base Taiga Project URL entered is used to generate hyperlinks that link to each specified taiga task on the generated report. "
        instr_str += "This is optional, but will handle the general process of generating the links for each individual task."
        instr_str += "\n\nFor setting the base url, refer to what is shown when you are at the home page for the project (the timeline page, but make sure to remove timeline from the url). i.e., https://tree.taiga.io/project/<The Project Name>."
        instr_str += "\n     - Example: With url https://tree.taiga.io/project/sundevil-awesome-sponsor-project/timeline, you would enter"
        instr_str += "\n     'https://tree.taiga.io/project/sundevil-awesome-sponsor-project'"
        
        instruction_msg = tk.Message(parent, text=instr_str, width=800, borderwidth=2, relief='ridge')
        
        field_frame = ttk.Frame(parent)
        taiga_project_field = self.__generate_field_obj(field_frame, 'Taiga Project URL (Optional):', ttk.Entry(field_frame, width=80))

        default_val = self.dc.get_taiga_project_url()
        if default_val is not None and default_val != '':
            if self.dc.check_url_exists(default_val):
                taiga_project_field.insert(0, default_val)
        
        field_frame.pack()
        instruction_msg.pack()

        return taiga_project_field
    
    def apply_from_date_filter(self, df, from_date_field, from_date_header) -> pd.DataFrame:
        if from_date_field.date_selected():
            from_date = from_date_field.get_date()
            return df[pd.to_datetime(df[from_date_header]) >= pd.to_datetime(from_date)]
        return df
    
    def apply_to_date_filter(self, df, to_date_field, to_date_header) -> pd.DataFrame:
        if to_date_field.date_selected():
            to_date = to_date_field.get_date()
            return df[pd.to_datetime(df[to_date_header]) <= pd.to_datetime(to_date)]
        return df
    
    def apply_name_filter(self, df, name_field, name_header):
        if name_field.selection_made():
            user = name_field.get_selection()
            return df[df[name_header] == user]
        return df
    
    def gen_report_triggered(self):
        self.reset_options_frame()
        self.disable_report_sel()
    
    def gen_mtr(self, from_date_field, to_date_field, user_field):
        df = self.root_app.get_taiga_data()
        df = self.apply_from_date_filter(df, from_date_field, 'sprint_end')
        df = self.apply_to_date_filter(df, to_date_field, 'sprint_start')
        df = self.apply_name_filter(df, user_field, 'assigned_to')
        df.sort_values(by='sprint_start', ascending=True, inplace=True)
        self.gen_report_triggered()
        self.preview_frame.generate_preview_frame(df, 'mtr')

    def gen_mgr(self, from_date_field, to_date_field, user_field):
        df = self.root_app.get_gh_data()
        df = self.apply_from_date_filter(df, from_date_field, 'az_date')
        df = self.apply_to_date_filter(df, to_date_field, 'az_date')
        df = self.apply_name_filter(df, user_field, 'committer')
        df.sort_values(by='utc_datetime', ascending=True, inplace=True)
        self.gen_report_triggered()
        self.preview_frame.generate_preview_frame(df, 'mgr')

    def gen_wsr(self, from_date_field, to_date_field, project_url_field):
        base_url = project_url_field.get()
        if base_url is not None and base_url != '':
            self.dc.set_taiga_project_url(base_url)

        df = self.root_app.get_taiga_data()
        df = self.apply_from_date_filter(df, from_date_field, 'sprint_start')
        df = self.apply_to_date_filter(df, to_date_field, 'sprint_end')
        df.sort_values(by='sprint_start', ascending=True, inplace=True)
        df = self.dc.format_wsr_non_excel(df)
        self.gen_report_triggered()
        self.preview_frame.generate_preview_frame(df, 'wsr')

    def gen_icr(self, from_date_field, to_date_field, user_field, project_url_field):
        base_url = project_url_field.get()
        if base_url is not None and base_url != '':
            self.dc.set_taiga_project_url(base_url)

        gh_df = self.get_gh_data()
        gh_df.sort_values(by='utc_datetime', ascending=True, inplace=True)
        t_df = self.get_taiga_data() if self.taiga_data_ready() else None

        df = self.dc.format_icr_df_non_excel(gh_df, t_df)
        df = self.apply_from_date_filter(df, from_date_field, 'az_date')
        df = self.apply_to_date_filter(df, to_date_field, 'az_date')
        df = self.apply_name_filter(df, user_field, 'committer')
        self.gen_report_triggered()
        self.preview_frame.generate_preview_frame(df, 'icr')

    def mtr_options_frame(self):
        if self.report_filter_frame is not None:
            self.report_filter_frame.destroy()

        self.report_filter_frame = ttk.Frame(self.report_filter_container)
        filters_frame = ttk.Frame(self.report_filter_frame)

        from_frame = ttk.Frame(filters_frame)
        to_frame = ttk.Frame(filters_frame)
        member_frame = ttk.Frame(filters_frame)
        btn_frame = ttk.Frame(self.report_filter_frame)
        
        user_select_def = StringVar(member_frame)
        user_options = ['', ''] + self.root_app.get_taiga_members()
        user_select_def.set(user_options[0])

        from_date_entry = self.__generate_field_obj(from_frame, 'From Date:', CustomDateEntry(from_frame, width=8))
        to_date_entry = self.__generate_field_obj(to_frame, 'To Date:', CustomDateEntry(to_frame, width=8))
        user_filter = self.__generate_field_obj(member_frame, 'Member:', CustomOptionMenu(member_frame, user_select_def, *user_options))

        gen_report_btn = ttk.Button(btn_frame, text='Generate Taiga Report', command=lambda: self.gen_mtr(from_date_entry, to_date_entry, user_filter))
        gen_report_btn.pack()

        from_frame.grid(row=0, column=0, padx=2, sticky='nsew')
        to_frame.grid(row=0, column=1, padx=2, sticky='nsew')
        member_frame.grid(row=0, column=2, padx=2, sticky='nsew')
        
        filters_frame.pack(pady=2)
        btn_frame.pack(pady=2)

        self.destroy_temp_load_msg_frame()
        self.report_filter_frame.pack()

    def mgr_options_frame(self):
        if self.report_filter_frame is not None:
            self.report_filter_frame.destroy()

        self.report_filter_frame = ttk.Frame(self.report_filter_container)
        filters_frame = ttk.Frame(self.report_filter_frame)

        from_frame = ttk.Frame(filters_frame)
        to_frame = ttk.Frame(filters_frame)
        member_frame = ttk.Frame(filters_frame)
        btn_frame = ttk.Frame(self.report_filter_frame)
        
        user_select_def = StringVar(member_frame)
        user_options = ['', ''] + self.root_app.get_gh_contributors()
        user_select_def.set(user_options[0])

        from_date_entry = self.__generate_field_obj(from_frame, 'From Date:', CustomDateEntry(from_frame, width=8))
        to_date_entry = self.__generate_field_obj(to_frame, 'To Date:', CustomDateEntry(to_frame, width=8))
        user_filter = self.__generate_field_obj(member_frame, 'Committer:', CustomOptionMenu(member_frame, user_select_def, *user_options))

        gen_report_btn = ttk.Button(btn_frame, text='Generate GitHub Report', command=lambda: self.gen_mgr(from_date_entry, to_date_entry, user_filter))
        gen_report_btn.pack()

        from_frame.grid(row=0, column=0, padx=2, sticky='nsew')
        to_frame.grid(row=0, column=1, padx=2, sticky='nsew')
        member_frame.grid(row=0, column=2, padx=2, sticky='nsew')
        
        filters_frame.pack(pady=2)
        btn_frame.pack(pady=2)

        self.destroy_temp_load_msg_frame()
        self.report_filter_frame.pack()

    def wsr_options_frame(self):
        if self.report_filter_frame is not None:
            self.report_filter_frame.destroy()

        self.report_filter_frame = ttk.Frame(self.report_filter_container)
        filters_frame = ttk.Frame(self.report_filter_frame)

        from_frame = ttk.Frame(filters_frame)
        to_frame = ttk.Frame(filters_frame)
        btn_frame = ttk.Frame(self.report_filter_frame)
        project_url_frame = ttk.Frame(self.report_filter_frame)

        from_date_entry = self.__generate_field_obj(from_frame, 'From Date (Sprint Start Dates Succeeding This Date):', CustomDateEntry(from_frame, width=8))
        to_date_entry = self.__generate_field_obj(to_frame, 'To Date (Sprint End Dates Preceeding This Date):', CustomDateEntry(to_frame, width=8))

        project_url_field = self.generate_taiga_project_field(project_url_frame)

        gen_report_btn = ttk.Button(btn_frame, text='Generate Work Summary Report', command=lambda: self.gen_wsr(from_date_entry, to_date_entry, project_url_field))
        gen_report_btn.pack()

        from_frame.grid(row=0, column=0, padx=2, sticky='nsew')
        to_frame.grid(row=0, column=1, padx=2, sticky='nsew')
        
        filters_frame.pack(pady=2)
        project_url_frame.pack(pady=4)
        btn_frame.pack(pady=2)

        self.destroy_temp_load_msg_frame()
        self.report_filter_frame.pack()

    def icr_options_frame(self):
        if self.report_filter_frame is not None:
            self.report_filter_frame.destroy()

        self.report_filter_frame = ttk.Frame(self.report_filter_container)
        filters_frame = ttk.Frame(self.report_filter_frame)

        from_frame = ttk.Frame(filters_frame)
        to_frame = ttk.Frame(filters_frame)
        member_frame = ttk.Frame(filters_frame)

        project_url_frame = ttk.Frame(self.report_filter_frame)
        btn_frame = ttk.Frame(self.report_filter_frame)

        user_select_def = StringVar(member_frame)
        user_options = ['', ''] + self.root_app.get_gh_contributors()
        user_select_def.set(user_options[0])

        from_date_entry = self.__generate_field_obj(from_frame, 'From Date (Sprint Start Dates Succeeding This Date):', CustomDateEntry(from_frame, width=8))
        to_date_entry = self.__generate_field_obj(to_frame, 'To Date (Sprint End Dates Preceeding This Date):', CustomDateEntry(to_frame, width=8))
        user_filter = self.__generate_field_obj(member_frame, 'Committer:', CustomOptionMenu(member_frame, user_select_def, *user_options))

        project_url_field = self.generate_taiga_project_field(project_url_frame)

        gen_report_btn = ttk.Button(btn_frame, text='Generate Individual Contributions Report', command=lambda: self.gen_icr(from_date_entry, to_date_entry, user_filter, project_url_field))
        gen_report_btn.pack()

        from_frame.grid(row=0, column=0, padx=2, sticky='nsew')
        to_frame.grid(row=0, column=1, padx=2, sticky='nsew')
        member_frame.grid(row=0, column=2, padx=2, sticky='nsew')
        
        filters_frame.pack(pady=2)
        project_url_frame.pack(pady=4)
        btn_frame.pack(pady=2)

        self.destroy_temp_load_msg_frame()
        self.report_filter_frame.pack()

    def build_options_frame(self):
        widget_frame = ttk.Frame(self)

        type_sel_frame = ttk.Frame(widget_frame)
        options_lbl = ttk.Label(type_sel_frame, text='Select Report Type:')

        self.sel_rb = StringVar()
        self.mtr_rad_btn = ttk.Radiobutton(type_sel_frame, variable=self.sel_rb, text='Master Taiga Report', value='mtr', command=self.switch_report_type)
        self.mgr_rad_btn = ttk.Radiobutton(type_sel_frame, variable=self.sel_rb, text='Master GitHub Report', value='mgr', command=self.switch_report_type)
        self.wsr_rad_btn = ttk.Radiobutton(type_sel_frame, variable=self.sel_rb, text='Work Summary Report', value='wsr', command=self.switch_report_type)
        self.icr_rad_btn = ttk.Radiobutton(type_sel_frame, variable=self.sel_rb, text='IC Report', value='icr', command=self.switch_report_type)

        options_lbl.grid(row=0, column=0, sticky='nsew')
        self.mtr_rad_btn.grid(row=0, column=1, sticky='nsew')
        self.mgr_rad_btn.grid(row=0, column=2, sticky='nsew')
        self.wsr_rad_btn.grid(row=0, column=3, sticky='nsew')
        self.icr_rad_btn.grid(row=0, column=4, sticky='nsew')

        self.report_filter_container = ttk.Frame(widget_frame)
        type_sel_frame.pack(pady=4, padx=5)
        self.report_filter_container.pack(padx=5)

        return widget_frame
    
    def handle_ext_type(self, filepath, df):
        if filepath is not None and filepath != '':
            ext = os.path.splitext(filepath)[1]
            match ext:
                case '.xlsx':
                    self.dc.write_to_excel(filepath, df)
                    self.dialog('Report Exported!')
                    self.reset_options_frame()
                    return
                case '.csv':
                    self.dc.write_to_csv(filepath, df)
                    self.dialog('Report Exported!')
                    self.reset_options_frame()
                    return
                case _:
                    pass
                    return

    def save_mtr(self, df):
        filepath = self.save_file_prompt('General_Taiga_Report')
        self.handle_ext_type(filepath, df)

    def save_mgr(self, df):
        filepath = self.save_file_prompt('General_GitHub_Report')
        self.handle_ext_type(filepath, df)

    def save_wsr(self, df):
        df = self.dc.format_wsr_excel(df)
        filepath = self.save_file_prompt('Work_Summary_Report')
        self.handle_ext_type(filepath, df)

    def save_icr(self, df):
        df = self.dc.format_icr_excel(df)
        filepath = self.save_file_prompt('Individual_Contributions_Report')
        self.handle_ext_type(filepath, df)
                
    def export_report(self, df, report_type):
        match report_type:
            case 'mtr':
                self.save_mtr(df)
                return
            case 'mgr':
                self.save_mgr(df)
                return
            case 'wsr':
                self.save_wsr(df)
                return
            case 'icr':
                self.save_icr(df)
                return
            case _:
                return
        
    
    def save_file_prompt(self, filename):
        files = [('Excel Workbook', '*.xlsx'),
                 ('CSV (Comma delimited)', '*.csv')]
        
        filepath = filedialog.asksaveasfilename(initialfile=filename, filetypes=files, defaultextension=files)
        return filepath

    class DataPreviewFrame(ttk.Frame):
        table_frame = None
        sheet = None
        
        col_widths = None
        report_type = None

        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent

        def __task_col_table_conversion(self, val):
            if pd.isna(val):
                return None
            else:
                val = int(val)
                return f'Task-{val}'

        def __task_col_data_prep(self, val):
            if pd.isna(val):
                return None
            else:
                return int(val)

        def __us_col_table_conversion(self, val):
            if val == -1 or pd.isna(val):
                return 'Storyless'
            else:
                return f'US-{int(val)}'
            
        def __us_col_data_prep(self, val):
            if val == -1 or pd.isna(val):
                return None
            else:
                return int(val)
            
        def __inv_val_to_none(self, df: Type[pd.DataFrame]):
            df.replace(['', 'None', 'nan', 'NaN', np.nan], [None, None, None, None, None], inplace=True)
        
        def __dataframe_to_table_format(self, df_to_format: Type[pd.DataFrame]):
            df = df_to_format.copy(deep=True)
            self.__inv_val_to_none(df)
            if 'user_story' in df:
                df['user_story'] = df['user_story'].apply(lambda x: self.__us_col_table_conversion(x))
            if 'task' in df:
                df['task'] = df['task'].apply(lambda x: self.__task_col_table_conversion(x))
            return df
        
        def __process_df(self, df_to_format: Type[pd.DataFrame]) -> pd.DataFrame:
            df = df_to_format.copy(deep=True)
            self.__inv_val_to_none(df)
            if 'user_story' in df:
                df['user_story'] = df['user_story'].apply(lambda x: self.__us_col_data_prep(x))
            if 'task' in df:
                df['task'] = df['task'].apply(lambda x: self.__task_col_data_prep(x))
            return df
        
        def build_table(self, parent, df):
            self.master_df = self.__process_df(df)
            table_formatted_df = self.__dataframe_to_table_format(df)
            sheet = tks.Sheet(parent, header=list(table_formatted_df.columns), data=table_formatted_df.values.tolist())

            if self.col_widths is None:
                column_widths = []
                index = 0
                for column in table_formatted_df.columns:
                    text_width = sheet.get_column_text_width(index)
                    if column == 'subject':
                        text_width = 285
                    elif column == 'message':
                        text_width = 350    
                    elif column == 'id':
                        text_width = 80
                    elif column == 'url':
                        text_width = 210
                    elif column == 'task_url':
                        text_width = 220
                    elif column == 'commit_url':
                        text_width = 220

                    column_widths.append(text_width)
                    index += 1

                self.col_widths = column_widths

            sheet.set_column_widths(self.col_widths)
            return sheet
        
        def return_to_report_selection(self):
            self.reset_frame()
            self.parent.enable_report_sel()
        
        def reset_frame(self):
            if self.table_frame is not None:
                self.table_frame.destroy()
            
            if self.col_widths is not None:
                self.col_widths = None
            if self.report_type is not None:
                self.report_type = None

        def export_report(self, df):
            self.parent.export_report(df, self.report_type)
            self.return_to_report_selection()

        def generate_title(self, report_type):
            match report_type:
                case 'mtr':
                    return 'Master Taiga Report Preview'
                case 'mgr':
                    return 'Master GitHub Report Preview'
                case 'wsr':
                    return 'Work Summary Report Preview'
                case 'icr':
                    return 'Individual Contributions Report Preview'
                case _:
                    return 'Report Preview'

        def generate_preview_frame(self, df, report_type):
            self.reset_frame()

            self.report_type = report_type
            self.table_frame = ttk.Frame(self)

            lbl_frame = ttk.Frame(self.table_frame, borderwidth=2, relief='ridge')
            table_lbl = ttk.Label(lbl_frame, text=self.generate_title(report_type), font=('Arial', 15))
            table_lbl.pack(pady=2)

            btn_frame = ttk.Frame(self.table_frame)
            export_btn = ttk.Button(btn_frame, text='Export Report', command=lambda: self.export_report(df))
            cancel_btn = ttk.Button(btn_frame, text='Cancel Export', command=self.return_to_report_selection)
            export_btn.grid(row=0, column=0, padx=2)
            cancel_btn.grid(row=0, column=1, padx=2)

            self.sheet = self.build_table(self.table_frame, df)

            lbl_frame.pack(fill='x')
            btn_frame.pack(pady=4)
            self.sheet.pack(fill='both', expand=True, pady=(0, 5))

            self.table_frame.pack(fill='both', expand=True)

            
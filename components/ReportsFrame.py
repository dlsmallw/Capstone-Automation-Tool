from tkinter import ttk, filedialog, StringVar, messagebox
import tkinter as tk
import tksheet as tks
import pandas as pd
import numpy as np
import os

from models.DataManager import DataController
from components.CustomComponents import CustomDateEntry, CustomComboBox

class ReportsFrame(ttk.Frame):
    def __init__(self, parent_frame: ttk.Notebook, root_app, dc: DataController):
        super().__init__(parent_frame)
        
        self.parent_frame = parent_frame
        self.root = root_app
        self.dc = dc

        self.config_frame = ConfigFrame(self, dc)
        self.data_frame = DataFrame(self, dc)

        self.config_frame.pack(fill='x')
        self.data_frame.pack(fill='both', expand=True, pady=5, anchor='n')

    def commit_data_ready(self) -> bool:
        return self.root.commit_data_ready()
    
    def get_commit_data(self) -> pd.DataFrame:
        return self.root.get_commit_data() if self.commit_data_ready() else None
    
    def taiga_data_ready(self) -> bool:
        return self.root.taiga_data_ready()
    
    def get_taiga_data(self) -> pd.DataFrame:
        return self.root.get_taiga_data() if self.taiga_data_ready() else None
    
    def reset_tab(self):
        if not self.data_frame.report_currently_loaded():
            self.config_frame.reset_panel()
            self.config_frame.update_valid_options()

    def handle_ext_type(self, filepath, df):
        if filepath is not None and filepath != '':
            ext = os.path.splitext(filepath)[1]
            match ext:
                case '.xlsx':
                    self.dc.write_to_excel(filepath, df)
                case '.csv':
                    self.dc.write_to_csv(filepath, df)
                case _:
                    return
            messagebox.showinfo(message='Report Exported!')
                
    def export_report(self, df, report_type):
        has_hyperlinks = False
        if report_type == 'mtr':
            filepath = self.save_file_prompt('General_Taiga_Report')
        elif report_type == 'mgr':
            filepath = self.save_file_prompt('General_Commits_Report')
        elif report_type == 'wsr':
            has_hyperlinks = True
            filepath = self.save_file_prompt('Work_Summary_Report')
        elif report_type == 'icr':
            has_hyperlinks = True
            filepath = self.save_file_prompt('Individual_Contributions_Report')

        self.handle_ext_type(filepath, df)
        if has_hyperlinks:
            self.dc.convert_hyperlinks(filepath)
        
    def save_file_prompt(self, filename):
        files = [('Excel Workbook', '*.xlsx'),
                 ('CSV (Comma delimited)', '*.csv')]
        
        filepath = filedialog.asksaveasfilename(initialfile=filename, filetypes=files, defaultextension=files)
        return filepath
    
    def load_report(self, report_type):
        self.data_frame.build_data_display(report_type)

    def reenable_report_sel(self):
        self.config_frame.enable_report_sel()

    def get_root_center_coords(self):
        return self.root.get_root_coords()

class ConfigFrame(ttk.Frame):
    def __init__(self, master: ReportsFrame = None, dc: DataController = None, **kwargs):
        super().__init__(master, **kwargs)
        self.hdr_dict = {
            'mtr': 'Master Taiga Report',
            'mgr': 'Master GitHub Report',
            'wsr': 'Work Summary Report',
            'icr': 'Contributions Report'
        }

        self.curr_sel = None
        self.prev_sel = None

        self.sel_rb: StringVar = None
        self.mtr_rad_btn: ttk.Radiobutton = None
        self.wsr_rad_btn: ttk.Radiobutton = None
        self.mgr_rad_btn: ttk.Radiobutton = None
        self.icr_rad_btn: ttk.Radiobutton = None

        self.message_frame: ttk.Frame = None
        self.message_strval: StringVar = None
        self.gen_report_strvar: StringVar = None
        self.gen_report_btn: ttk.Button = None

        self.dc = dc
        self.parent = master
        self.config_panel = self.build_config_panel()
        self.config_panel.pack(fill='x')

    def reset_panel(self):
        self.prev_sel = None
        self.sel_rb.set(None)

    def update_valid_options(self):
        taiga_data_ready = self.parent.taiga_data_ready()
        commit_data_ready = self.parent.commit_data_ready()
        self.mtr_rad_btn['state'] = self.wsr_rad_btn['state'] = 'normal' if taiga_data_ready else 'disabled'
        self.mgr_rad_btn['state'] = self.icr_rad_btn['state'] = 'normal' if commit_data_ready else 'disabled'

    def disable_report_sel(self):
        self.mtr_rad_btn['state'] = \
        self.wsr_rad_btn['state'] = \
        self.mgr_rad_btn['state'] = \
        self.icr_rad_btn['state'] = \
        self.gen_report_btn['state'] = 'disabled'

    def enable_report_sel(self):
        self.sel_rb.set(None)
        self.curr_sel = self.prev_sel = None
        self.update_valid_options()
        

    def show_temp_message(self, msg):
        self.message_strval.set(msg)
        if self.message_frame is None:
            self.message_frame = ttk.Frame(self.config_panel)
            message_field = ttk.Label(self.message_frame, textvariable=self.message_strval, font=('Arial', 8, 'normal', 'italic'), padding=3, anchor='center')
            message_field.pack()
            self.message_frame.pack()
    
    def remove_temp_message(self):
        if self.message_frame is not None:
            self.message_frame.destroy()

    def option_selected(self, *args):
        selection = self.sel_rb.get()
        if selection is not None:
            if self.prev_sel == selection:
                self.prev_sel = None
                self.sel_rb.set(None)
                self.gen_report_btn['state'] = 'disabled'
            else:
                self.prev_sel = selection
                self.gen_report_btn['state'] = 'normal'

    def build_config_panel(self):
        def build_options_frame(parent_frame):
            options_frame = ttk.Frame(parent_frame)

            type_sel_frame = ttk.Frame(options_frame)
            options_lbl = ttk.Label(type_sel_frame, text='Select Report Type:', font=('Arial', 10, 'bold'))

            self.sel_rb = StringVar()
            self.mtr_rad_btn = ttk.Radiobutton(type_sel_frame, variable=self.sel_rb, text='Master Taiga Report', value='mtr', command=self.option_selected)
            self.mgr_rad_btn = ttk.Radiobutton(type_sel_frame, variable=self.sel_rb, text='Master GitHub Report', value='mgr', command=self.option_selected)
            self.wsr_rad_btn = ttk.Radiobutton(type_sel_frame, variable=self.sel_rb, text='Work Summary Report', value='wsr', command=self.option_selected)
            self.icr_rad_btn = ttk.Radiobutton(type_sel_frame, variable=self.sel_rb, text='IC Report', value='icr', command=self.option_selected)

            options_lbl.grid(row=0, column=0, padx=(0, 10), sticky='nsew')
            self.mtr_rad_btn.grid(row=0, column=1, padx=5, sticky='nsew')
            self.mgr_rad_btn.grid(row=0, column=2, padx=5, sticky='nsew')
            self.wsr_rad_btn.grid(row=0, column=3, padx=5, sticky='nsew')
            self.icr_rad_btn.grid(row=0, column=4, padx=5, sticky='nsew')

            self.report_filter_container = ttk.Frame(widget_frame)
            type_sel_frame.pack(pady=4, padx=5)
            self.report_filter_container.pack(padx=5)

            return options_frame
    
        widget_frame = ttk.Frame(self)

        config_lbl_frame = ttk.Frame(widget_frame)
        config_frame_lbl = ttk.Label(config_lbl_frame, text=f'{' ' * 4}Report Generation{' ' * 4}', font=('Arial', 15, 'bold'))
        config_frame_lbl.pack()
        config_lbl_frame.pack(fill='x', pady=5)

        options_panel = build_options_frame(widget_frame)
        options_panel.pack()

        self.message_strval = StringVar()

        self.gen_report_strvar = StringVar(value='Generate Report')
        self.gen_report_btn = ttk.Button(widget_frame, textvariable=self.gen_report_strvar, command=self.generate_report, state='disabled')
        self.gen_report_btn.pack()

        return widget_frame
    
    def generate_report(self):
        self.disable_report_sel()
        self.parent.load_report(self.sel_rb.get())

class DataFrame(ttk.Frame):
    def __init__(self, parent: ReportsFrame, dc: DataController):
        super().__init__(parent) 
        self.filters = []
        self.report_generated = False

        self.table_df: pd.DataFrame = None
        self.report_type = None

        self.data_display: ttk.Frame = None
        self.report_sheet: tks.Sheet = None

        self.parent_frame = parent
        self.dc = dc

    def reset_frame(self):
        self.table_df = None
        self.filters: list[CustomComboBox|CustomDateEntry] = []

        if self.data_display is not None:
            self.data_display.destroy()

        if self.report_type is not None:
            self.report_type = None

        self.report_generated = False

    def report_currently_loaded(self):
        return self.report_generated
    
    def export_report(self):
        # try:
            rt = self.report_type
            df = pd.DataFrame(data=self.report_sheet.data, columns=self.report_sheet.headers())
            df = df.replace('', pd.NA)

            match rt:
                case 'mtr':
                    pass
                case 'mgr':
                    df = df[['id', 'az_date', 'utc_datetime', 'task_num', 'committer', 'repo_name', 'commit_message', 'commit_url']]
                case 'wsr':
                    df = self.dc.format_wsr_excel(df)
                case 'icr':
                    df = self.dc.format_icr_excel(df)
                case _:
                    pass
            
            self.parent_frame.export_report(df, rt)
            self.cancel_report()
        # except Exception as e:
        #     messagebox.showerror(message=f'Failed to export the report. {e}')

    def cancel_report(self):
        self.reset_frame()
        self.parent_frame.reenable_report_sel()

    def build_header_frame(self, hdr_str='Report'):
        def build_btn_frame(parent):
            widget_frame = ttk.Frame(parent)
            btn_frame = ttk.Frame(widget_frame)
            export_report_btn = ttk.Button(btn_frame, text='Export Report', command=self.export_report)
            cancel_btn = ttk.Button(btn_frame, text='Cancel Report Generation', command=self.cancel_report)
            export_report_btn.grid(row=0, column=0, padx=(2, 1))
            cancel_btn.grid(row=0, column=1, padx=(2, 1))
            btn_frame.pack(anchor='e')
            return widget_frame

        hdr_frame = ttk.Frame(self.data_display, borderwidth=2, relief='ridge')
        hdr_frame.pack(fill='x', pady=3) 
        hdr_lbl = ttk.Label(hdr_frame, text=f'{' ' * 4}{hdr_str}{' ' * 4}', font=('Arial', 13, 'bold'))
        hdr_lbl.place(relx=0.5, rely=0.5, anchor='center')
        btn_frame = build_btn_frame(hdr_frame)
        btn_frame.pack(pady=3, side='right')
        return hdr_frame
    
    def build_table_frame(self, df: pd.DataFrame, cols_to_hide=[], lower_priority_cols=[]):
        table_frame = ttk.Frame(self.data_display)
        temp_sheet = tks.Sheet(table_frame, data=df.values.tolist(), header=df.columns.tolist())

        column_widths = []
        remaining_width = 960
        curr_total = 0
        for idx, column in enumerate(df.columns.tolist()):
            if column not in lower_priority_cols:
                text_width = temp_sheet.get_column_text_width(idx)
            else:
                text_width = remaining_width
            
            curr_total += text_width
            remaining_width -= text_width               
            column_widths.append(text_width)

        ## This is the only reasonable way to pre-calculate the approximate width of the table and then use the width
        table_frame.destroy()
        table_frame = ttk.Frame(self.data_display, width=int(curr_total * 1.1))
        self.report_sheet = tks.Sheet(table_frame, width=int(curr_total * 1.1), data=df.values.tolist(), header=df.columns.tolist())

        self.report_sheet.pack(fill='both', expand=True)
        self.report_sheet.hide_columns(cols_to_hide)
        self.report_sheet.set_sheet_data_and_display_dimensions(total_rows=len(df), total_columns=len(df.columns))
        self.report_sheet.set_column_widths(column_widths)
        
        return table_frame

    def generate_field_obj(self, parent, lbl_str, target_obj):
        field_lbl = ttk.Label(parent, text=lbl_str, anchor='e')
        field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')

    def build_mtr_display(self):
        padx = 3
        sticky = 'nsew'

        taiga_df = self.parent_frame.get_taiga_data()

        if taiga_df is None:
            self.cancel_report()
            return
        
        taiga_df = taiga_df.sort_values(by=['sprint', 'us_num', 'task_num'], ascending=True, na_position='last')
        taiga_df = pd.concat([taiga_df.loc[pd.notna(taiga_df['sprint'])], taiga_df.loc[pd.isna(taiga_df['sprint'])]])

        user_stories = taiga_df['us_num'].dropna().drop_duplicates().to_list()
        members = taiga_df['assignee'].dropna().drop_duplicates().to_list()
        sprints = taiga_df['sprint'].dropna().drop_duplicates().to_list()

        taiga_df['us_id'] = taiga_df['us_id'].astype(pd.StringDtype())
        taiga_df['task_id'] = taiga_df['task_id'].astype(pd.StringDtype())
        taiga_df['task_num'] = taiga_df['task_num'].astype(pd.StringDtype())
        taiga_df['us_num'] = taiga_df['us_num'].astype(pd.StringDtype())
        taiga_df['points'] = taiga_df['points'].astype(pd.StringDtype())
        taiga_df['is_complete'] = taiga_df['is_complete'].astype(pd.StringDtype())
        taiga_df['is_coding'] = taiga_df['is_coding'].astype(pd.StringDtype())
        
        taiga_df['sprint'] = taiga_df['sprint'].replace({pd.NA: 'Unassigned'})
        taiga_df['us_num'] = taiga_df['us_num'].replace(pd.NA, 'Storyless')
        taiga_df['assignee'] = taiga_df['assignee'].replace(pd.NA, 'Unassigned')
        taiga_df['is_complete'] = taiga_df['is_complete'].replace({'True': 'Complete', 'False': 'In-process'})
        taiga_df = taiga_df.replace(pd.NA, '')

        self.table_df = taiga_df

        ## Filter Variables:
        us_opts = ['ALL', 'Storyless'] + user_stories
        sprint_opts = ['ALL', 'Unassigned'] + sprints
        member_opts = ['ALL', 'Unassigned'] + members
        complete_opts = ['ALL', 'Complete', 'In-process']
        coding_opts = ['ALL', np.True_, np.False_]

        hdr2idx = dict()
        for idx, col in enumerate(taiga_df.columns):
            hdr2idx[col] = idx

        strvar_list = [StringVar(), StringVar(), StringVar(), StringVar(), StringVar()]
        strvar_trace_ids = [None] * len(strvar_list)

        def build_filter_panel():
            def apply_filters(*args):
                filters_applied = [filter_obj.filter_applied() for filter_obj in self.filters]

                if True in filters_applied:
                    rows = []
                    for rn, row in enumerate(self.report_sheet.data):
                        row_match = True

                        if row_match and filters_applied[0] and row[hdr2idx['us_num']] != us_opt_sel.get_selection():
                            row_match = False
                        if row_match and filters_applied[1] and row[hdr2idx['sprint']] != sprint_opt_sel.get_selection():
                            row_match = False
                        if row_match and filters_applied[2] and row[hdr2idx['assignee']] != member_opt_sel.get_selection():
                            row_match = False
                        if row_match and filters_applied[3] and row[hdr2idx['is_complete']] != complete_opt_sel.get_selection():
                            row_match = False
                        if row_match and filters_applied[4] and row[hdr2idx['is_coding']] != coding_opt_sel.get_selection():
                            row_match = False
                        if row_match:
                            rows.append(rn)

                    self.report_sheet.display_rows(rows=rows, all_displayed=False, redraw=True)
                    clear_filters_btn['state'] = 'normal'
                else:
                    clear_filters_btn['state'] = 'disabled'
                    self.report_sheet.display_rows('all', redraw=True)

            def clear_filters():
                remove_strvar_traces()
                for filter_obj in self.filters:
                    filter_obj.reset()
                
                self.report_sheet.display_rows('all', redraw=True)
                clear_filters_btn['state'] = 'disabled'
                init_strvar_traces()


            def remove_strvar_traces():
                for idx, strvar in enumerate(strvar_list):
                    strvar.trace_remove(mode='write', cbname=strvar_trace_ids[idx])
                    strvar_trace_ids[idx] = None

            def init_strvar_traces():
                for idx, strvar in enumerate(strvar_list):
                    strvar_trace_ids[idx] = strvar.trace_add(mode='write', callback=apply_filters)

            filter_frame = ttk.Frame(self.data_display)
            options_frame = ttk.Frame(filter_frame)

            us_filter_frame = ttk.Frame(options_frame)
            sprint_filter_frame = ttk.Frame(options_frame)
            member_filter_frame = ttk.Frame(options_frame)
            complete_filter_frame = ttk.Frame(options_frame)
            coding_filter_frame = ttk.Frame(options_frame)
            btn_frame = ttk.Frame(options_frame)

            filter_section_lbl = ttk.Label(options_frame, text='Filters:', font=('Arial', 11, 'bold'))
            us_opt_sel = CustomComboBox(us_filter_frame, strvar_list[0], *us_opts, comp_id='userstory', default='ALL')
            self.generate_field_obj(us_filter_frame, 'User Story:', us_opt_sel)
            sprint_opt_sel = CustomComboBox(sprint_filter_frame, strvar_list[1], *sprint_opts, comp_id='sprint', default='ALL')
            self.generate_field_obj(sprint_filter_frame, 'Sprint:', sprint_opt_sel)
            member_opt_sel = CustomComboBox(member_filter_frame, strvar_list[2], *member_opts, comp_id='member', default='ALL')
            self.generate_field_obj(member_filter_frame, 'Assigned To:', member_opt_sel)
            complete_opt_sel = CustomComboBox(complete_filter_frame, strvar_list[3], *complete_opts, comp_id='complete', default='ALL')
            self.generate_field_obj(complete_filter_frame, 'Task Status:', complete_opt_sel)
            coding_opt_sel = CustomComboBox(coding_filter_frame, strvar_list[4], *coding_opts, comp_id='coding', default='ALL')
            self.generate_field_obj(coding_filter_frame, 'Coding Task:', coding_opt_sel)
            clear_filters_btn = ttk.Button(btn_frame, text='Clear Filters', state='disabled', command=clear_filters)
            clear_filters_btn.pack()

            self.filters = [us_opt_sel, sprint_opt_sel, member_opt_sel, complete_opt_sel, coding_opt_sel]

            filter_section_lbl.grid(row=0, column=0, padx=padx, sticky=sticky)
            us_filter_frame.grid(row=0, column=1, padx=padx, sticky=sticky)
            sprint_filter_frame.grid(row=0, column=2, padx=padx, sticky=sticky)
            member_filter_frame.grid(row=0, column=3, padx=padx, sticky=sticky)
            complete_filter_frame.grid(row=0, column=4, padx=padx, sticky=sticky)
            coding_filter_frame.grid(row=0, column=5, padx=padx, sticky=sticky)
            btn_frame.grid(row=0, column=6, padx=padx, sticky=sticky)
            options_frame.pack(pady=(4, 4), anchor='w')

            init_strvar_traces()
            return filter_frame

        hdr_frame = self.build_header_frame('Master Taiga Report')
        filter_frame = build_filter_panel()
        table_frame = self.build_table_frame(taiga_df, cols_to_hide=['us_id', 'task_id'], lower_priority_cols=['task_subject'])

        hdr_frame.pack(fill ='x') 
        filter_frame.pack() 
        table_frame.pack(fill='y', expand=True)
        self.data_display.pack(fill='both', expand=True)

    def build_mgr_display(self):
        padx = 3
        sticky = 'nsew'

        commits_df = self.parent_frame.get_commit_data()[['az_date', 'task_num', 'committer', 'repo_name', 'commit_message', 'commit_url', 'id', 'utc_datetime']]

        if commits_df is None:
            self.cancel_report()
            return
        
        commits_df = commits_df.sort_values(by='utc_datetime', ascending=True, na_position='last')

        repos = commits_df['repo_name'].dropna().drop_duplicates().to_list()
        tasks = commits_df['task_num'].dropna().drop_duplicates().to_list()
        members = commits_df['committer'].dropna().drop_duplicates().to_list()
        
        commits_df['committer'] = commits_df['committer'].replace(pd.NA, 'Unknown')
        commits_df['task_num'] = commits_df['task_num'].astype(pd.StringDtype())
        commits_df = commits_df.replace(pd.NA, '')

        self.table_df = commits_df

        ## Filter Variables:
        repo_opts = ['ALL'] + repos
        task_opts = ['ALL', 'Not Set'] + tasks
        member_opts = ['ALL', 'Unknown'] + members

        hdr2idx = dict()
        for idx, col in enumerate(commits_df.columns):
            hdr2idx[col] = idx

        strvar_list = [StringVar(), StringVar(), StringVar()]
        strvar_trace_ids = [None] * len(strvar_list)

        def build_filter_panel():
            def apply_filters(*args):
                filters_applied = [filter_obj.filter_applied() for filter_obj in self.filters]

                if True in filters_applied:
                    rows = []
                    for rn, row in enumerate(self.report_sheet.data):
                        row_match = True

                        if row_match and filters_applied[0] and row[hdr2idx['repo_name']] != repo_opt_sel.get_selection():
                            row_match = False

                        if row_match and filters_applied[1]:
                            val = row[hdr2idx['task_num']] if row[hdr2idx['task_num']] != '' else 'Not Set'
                            if val != task_opt_sel.get_selection():
                                row_match = False

                        if row_match and filters_applied[2] and row[hdr2idx['committer']] != member_opt_sel.get_selection():
                            row_match = False

                        if row_match and filters_applied[3] and pd.Timestamp(row[hdr2idx['az_date']]) < pd.Timestamp(after_date_filter.get_date_val()):
                            row_match = False

                        if row_match and filters_applied[4] and pd.Timestamp(row[hdr2idx['az_date']]) > pd.Timestamp(before_date_filter.get_date_val()):
                            row_match = False

                        if row_match:
                            rows.append(rn)

                    self.report_sheet.display_rows(rows=rows, all_displayed=False, redraw=True)
                    clear_filters_btn['state'] = 'normal'
                else:
                    clear_filters_btn['state'] = 'disabled'
                    self.report_sheet.display_rows('all', redraw=True)

            def clear_filters():
                remove_strvar_traces()
                for filter_obj in self.filters:
                    filter_obj.reset()
                
                self.report_sheet.display_rows('all', redraw=True)
                clear_filters_btn['state'] = 'disabled'
                init_strvar_traces()

            def remove_strvar_traces():
                for idx, strvar in enumerate(strvar_list):
                    strvar.trace_remove(mode='write', cbname=strvar_trace_ids[idx])
                    strvar_trace_ids[idx] = None

            def init_strvar_traces():
                for idx, strvar in enumerate(strvar_list):
                    strvar_trace_ids[idx] = strvar.trace_add(mode='write', callback=apply_filters)

            filter_frame = ttk.Frame(self.data_display)
            options_frame = ttk.Frame(filter_frame)

            repo_filter_frame = ttk.Frame(options_frame)
            task_filter_frame = ttk.Frame(options_frame)
            member_filter_frame = ttk.Frame(options_frame)
            after_date_filter_frame = ttk.Frame(options_frame)
            before_date_filter_frame = ttk.Frame(options_frame)
            btn_frame = ttk.Frame(options_frame)

            filter_section_lbl = ttk.Label(options_frame, text='Filters:', font=('Arial', 11, 'bold'))
            repo_opt_sel = CustomComboBox(repo_filter_frame, strvar_list[0], *repo_opts, comp_id='repo', default='ALL')
            self.generate_field_obj(repo_filter_frame, 'Repo:', repo_opt_sel)
            task_opt_sel = CustomComboBox(task_filter_frame, strvar_list[1], *task_opts, comp_id='task', default='ALL')
            self.generate_field_obj(task_filter_frame, 'Task:', task_opt_sel)
            member_opt_sel = CustomComboBox(member_filter_frame, strvar_list[2], *member_opts, comp_id='member', default='ALL')
            self.generate_field_obj(member_filter_frame, 'Committer:', member_opt_sel)
            after_date_filter = CustomDateEntry(master=after_date_filter_frame)
            self.generate_field_obj(after_date_filter_frame, 'After:', after_date_filter)
            before_date_filter = CustomDateEntry(master=before_date_filter_frame)
            self.generate_field_obj(before_date_filter_frame, 'Before:', before_date_filter)
            clear_filters_btn = ttk.Button(btn_frame, text='Clear Filters', state='disabled', command=clear_filters)
            clear_filters_btn.pack()

            self.filters = [repo_opt_sel, task_opt_sel, member_opt_sel, after_date_filter, before_date_filter]

            filter_section_lbl.grid(row=0, column=0, padx=padx, sticky=sticky)
            repo_filter_frame.grid(row=0, column=1, padx=padx, sticky=sticky)
            task_filter_frame.grid(row=0, column=2, padx=padx, sticky=sticky)
            member_filter_frame.grid(row=0, column=3, padx=padx, sticky=sticky)
            after_date_filter_frame.grid(row=0, column=4, padx=padx, sticky=sticky)
            before_date_filter_frame.grid(row=0, column=5, padx=padx, sticky=sticky)
            btn_frame.grid(row=0, column=6, padx=padx, sticky=sticky)
            options_frame.pack(pady=(4, 4), anchor='w')

            init_strvar_traces()
            after_date_filter.bind('<<DateEntrySelected>>', apply_filters)
            before_date_filter.bind('<<DateEntrySelected>>', apply_filters)

            return filter_frame

        hdr_frame = self.build_header_frame('Master Commits Report')
        filter_frame = build_filter_panel()
        table_frame = self.build_table_frame(commits_df, cols_to_hide=['commit_url', 'id', 'utc_datetime'], lower_priority_cols=['commit_message'])

        hdr_frame.pack(fill ='x') 
        filter_frame.pack() 
        table_frame.pack(fill='y', expand=True)
        self.data_display.pack(fill='both', expand=True)

    def wsr_prompt(self):
        def generate_report():
            start_date = sprint_dict[sprint_opt_sel.get_selection().split(' - ')[0]]
            excluded_sprints = [sprint for sprint in sprint_dict.keys() if sprint_dict[sprint] < start_date]
            prompt_window.destroy()  
            self.build_wsr_display(wsr_df[~wsr_df['Sprint'].isin(excluded_sprints)])

        def close():
            self.cancel_report()
            prompt_window.destroy()

        width = 350
        height = 120
        c_x, c_y = self.parent_frame.get_root_center_coords()

        prompt_window = tk.Toplevel()
        prompt_window.title("Generate Work Summary Report")
        prompt_window.geometry(f'{width}x{height}+{c_x - int(width / 2)}+{c_y - int(height / 2)}')
        prompt_window.wm_protocol("WM_DELETE_WINDOW", func=close)
        prompt_window.grab_set()

        taiga_df = self.parent_frame.get_taiga_data()
        taiga_df = taiga_df.loc[pd.notna(taiga_df['sprint'])]
        taiga_df['points'] = taiga_df['points'].replace(pd.NA, 0)

        if taiga_df is None:
            self.cancel_report()
            return
        
        wsr_df = self.dc.format_wsr_non_excel(taiga_df)
        wsr_df = wsr_df.sort_values(by=['Sprint', 'User Story', 'Task'], ascending=True, na_position='last')

        wsr_df['User Story'] = wsr_df['User Story'].astype(pd.StringDtype())
        wsr_df['User Story'] = wsr_df['User Story'].replace(pd.NA, 'Storyless')
        wsr_df['Points'] = wsr_df['Points'].astype(pd.Int64Dtype())
        wsr_df['Task'] = wsr_df['Task'].astype(pd.Int64Dtype())
        wsr_df['Coding?'] = wsr_df['Coding?'].astype(pd.StringDtype())

        sprint_strvar = StringVar(prompt_window)
        sprint_opts = ['ALL']
        sprint_dict = dict()

        sprint_df = self.dc.get_sprints_df().dropna().drop_duplicates()
        sprint_df = sprint_df.sort_values(by='sprint_start', ascending=True)
        for _, row in self.dc.get_sprints_df().iterrows():
            sprint = row['sprint_name']
            date = row['sprint_start']
            sprint_dict[sprint] = pd.Timestamp(date)
            sprint_opts.append(f'{sprint} - {pd.to_datetime(date).strftime(format='%m-%d-%Y')}')

        sprint_sel_lbl = ttk.Label(prompt_window, text="Report Start Date/Sprint:")
        sprint_sel_lbl.pack(pady=5)
        sprint_opt_sel = CustomComboBox(prompt_window, sprint_strvar, *sprint_opts, comp_id='sprint')
        sprint_opt_sel.pack(pady=5)

        gen_report_btn = ttk.Button(prompt_window, text='Generate Work Summary Report', command=generate_report)
        gen_report_btn.pack(pady=10)

    def build_wsr_display(self, wsr_df: pd.DataFrame):
        if wsr_df is None:
            self.cancel_report()
            return

        hdr_frame = self.build_header_frame('Work Summary Report')
        table_frame = self.build_table_frame(wsr_df)

        hdr_frame.pack(fill ='x') 
        table_frame.pack(fill='y', expand=True)
        self.data_display.pack(fill='both', expand=True)

    def icr_prompt(self):
        def selection_made(*args):
            committer = member_strvar.get()
            if committer is not None:
                gen_report_btn['state'] = 'normal'

        def generate_report(icr_df: pd.DataFrame):
            committer = member_strvar.get()
            if committer != 'ALL':
                icr_df = icr_df[icr_df['Committer'] == committer]
            if start_date.date_selected():
                icr_df = icr_df[pd.to_datetime(icr_df['Commit Date']) >= pd.to_datetime(start_date.get_date_val())]
            if end_date.date_selected():
                icr_df = icr_df[pd.to_datetime(icr_df['Commit Date']) <= pd.to_datetime(end_date.get_date_val())]

            prompt_window.destroy()  
            self.build_icr_display(icr_df)

        def close():
            self.cancel_report()
            prompt_window.destroy()

        width = 270
        height = 150
        c_x, c_y = self.parent_frame.get_root_center_coords()

        prompt_window = tk.Toplevel()
        prompt_window.title("Generate IC Report")
        prompt_window.geometry(f'{width}x{height}+{c_x - int(width / 2)}+{c_y - int(height / 2)}')
        prompt_window.wm_protocol("WM_DELETE_WINDOW", func=close)
        prompt_window.grab_set()

        taiga_df = self.parent_frame.get_taiga_data()
        commits_df = self.parent_frame.get_commit_data()

        if commits_df is None:
            self.cancel_report()
            return
        
        icr_df = self.dc.format_icr_df_non_excel(commits_df, taiga_df)

        ## Filter Variables:
        member_strvar = StringVar()
        member_opts = icr_df['Committer'].dropna().drop_duplicates().to_list()

        filter_frame = ttk.Frame(prompt_window)

        committer_sel_lbl = ttk.Label(filter_frame, text="Contributor:")
        start_date_lbl = ttk.Label(filter_frame, text="Report Start Date:")
        end_date_lbl = ttk.Label(filter_frame, text="Report End Date:")
        
        committer_opt_sel = CustomComboBox(filter_frame, member_strvar, *member_opts, default=None, comp_id='committer')
        start_date = CustomDateEntry(master=filter_frame)
        end_date = CustomDateEntry(master=filter_frame)
        
        committer_sel_lbl.grid(row=0, column=0, padx=2, pady=5, sticky='e')
        start_date_lbl.grid(row=1, column=0, padx=2, pady=5, sticky='e')
        end_date_lbl.grid(row=2, column=0, padx=2, pady=5, sticky='e')
        committer_opt_sel.grid(row=0, column=1, pady=5, sticky='w')
        start_date.grid(row=1, column=1, pady=5, sticky='w')
        end_date.grid(row=2, column=1, pady=5, sticky='w')

        gen_report_btn = ttk.Button(prompt_window, text='Generate IC Report', state='disabled', command=lambda: generate_report(icr_df))

        filter_frame.pack()
        gen_report_btn.pack(pady=10)

        member_strvar.trace_add(mode='write', callback=selection_made)

    def build_icr_display(self, icr_df: pd.DataFrame):
        if icr_df is None:
            self.cancel_report()
            return
        
        self.table_df = icr_df

        hdr_frame = self.build_header_frame('Contributions Report')
        table_frame = self.build_table_frame(icr_df, cols_to_hide=[], lower_priority_cols=[])

        hdr_frame.pack(fill ='x') 
        table_frame.pack(fill='y', expand=True)
        self.data_display.pack(fill='both', expand=True)

    def build_data_display(self, report_type):
        if self.data_display is not None:
            self.data_display.destroy()

        self.data_display = ttk.Frame(self)

        match report_type:
            case 'mtr':
                self.build_mtr_display()
            case 'mgr':
                self.build_mgr_display()
            case 'wsr':
                self.wsr_prompt()
            case 'icr':
                self.icr_prompt()
            case _:
                return
        
        self.report_type = report_type
        self.report_generated = True
    
    

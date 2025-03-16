import tkinter as tk
from tkinter import ttk, StringVar, messagebox
import tksheet as tks

from typing import Type
import pandas as pd
import numpy as np
import threading
import shortuuid as suuid
import datetime

from models.DataManager import DataController
from components.CustomComponents import CustomComboBox, CustomDateEntry

class GitFrame(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, dc: DataController, root_app):
        super().__init__(parent)
        
        self.dc = dc
        self.parent_frame = parent
        self.root = root_app

        self.config_frame = ConfigFrame(self, dc)
        self.data_frame = DataFrame(self, dc)

        self.config_frame.pack(fill='x', anchor='n', pady=(0, 4))
        self.data_frame.pack(fill='both', expand=True, anchor='n')

        if self.dc.commit_data_ready():
            self.setup_dataframe()

    def setup_dataframe(self):
        self.data_frame.handle_data_to_tables()

    def commit_data_ready(self) -> bool:
        return self.data_frame.commit_data_ready()
    
    def get_commit_data(self) -> pd.DataFrame:
        return self.data_frame.get_commit_data()
    
    def update_to_taiga_data(self):
        if self.commit_data_ready():
            self.data_frame.update_task_dropdown_opts()

    def get_root_center_coords(self):
        return self.root.get_root_coords()
    
class ConfigFrame(ttk.Frame):
    def __init__(self, parent: GitFrame, dc: DataController):
        super().__init__(parent)
        self.ui_disabled = False

        self.add_acct_btn : ttk.Button = None
        self.edit_acct_btn : ttk.Button = None
        self.remove_acct_btn : ttk.Button = None
        self.link_repos_btn : ttk.Button = None
        self.remove_repos_btn : ttk.Button = None
        self.message_strval : StringVar = None

        self.dc = dc
        self.parent_frame = parent

        config_frame = self._build_config_frame(self)
        config_frame.pack(fill='x', expand=True, padx=8, pady=8)

    def import_commit_data(self):
        try:
            for res, args in self.dc.import_commit_data():
                if res == 'In Progress':
                    self.message_strval.set(args)
                else:
                    self.message_strval.set(args)

            self.parent_frame.setup_dataframe()
            self.message_strval.set('Completed Data Import')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to import data - {e}')

    def _generate_field_obj(self, field_frame, lbl_str, target_obj, btn_obj=None):
        field_lbl = ttk.Label(field_frame, text=lbl_str, anchor='e')
        field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')
        if btn_obj is not None:
            btn_obj.grid(row=0, column=2, padx=(4, 4))
        return target_obj

    def _build_config_frame(self, parent_frame) -> ttk.Frame:
        def update_ui_state():
            api_ready = self.dc.api_call_ready()
            repos_linked = self.dc.repos_linked()

            if api_ready:
                self.link_repos_btn['state'] = 'normal'
                self.refresh_repos_btn['state'] = 'normal'
            else:
                self.link_repos_btn['state'] = 'disabled'
                self.refresh_repos_btn['state'] = 'disabled'

            if api_ready and repos_linked:
                self.import_commit_data_btn['state'] = 'normal'
            else:
                self.import_commit_data_btn['state'] = 'disabled'

            if api_ready and repos_linked:
                self.message_strval.set('Ready to import commit data')
            elif api_ready:
                self.message_strval.set('One or more repositories must be linked to import data')
            else:
                self.message_strval.set('A GitHub or GitLab account must be connected to begin importing data')

        def disable_ui():
            self.ui_disabled = True
            self.import_commit_data_btn['state'] = 'disabled'
            self.refresh_repos_btn['state'] = 'disabled'
            self.link_repos_btn['state'] = 'disabled'
            self.add_acct_btn['state'] = 'disabled'

        def enable_ui():
            self.ui_disabled = False
            self.add_acct_btn['state'] = 'normal'
            update_ui_state()

        def build_details_panel():
            def wait_for_repos(nickname):
                self.message_strval.set(f'Pulling Account {nickname} Repository List...')
                disable_ui()
                self.dc.pull_repos(nickname)
                enable_ui()
                self.message_strval.set('Repository List Retrieved')

            def add_acct_prompt():
                def opt_change(event):
                    val = site_strvar.get()

                    if val != 'None':
                        token_lbl_strvar.set(f'Enter the {val} token:')
                        submit_button['state'] = 'normal'
                    else:
                        token_lbl_strvar.set(f'Enter the token:')
                        submit_button['state'] = 'disabled'

                # Function to handle submission
                def submit_entry():
                    site = site_strvar.get()
                    nickname = nickname_entry.get().strip()
                    token = token_entry.get().strip()

                    site_valid = site != 'None'
                    token_valid = token and len(token) > 0

                    if not site_valid:
                        messagebox.showerror("Error", "Must select a site")
                        return
                    
                    if not token_valid:
                        messagebox.showerror("Error", "Token must be entered")
                        return
                    
                    if not nickname or nickname == '':
                        while True:
                            nickname = f'{site[0]}{site[3]}-{suuid.random(4)}'
                            if not self.dc.check_if_nickname_exists(nickname):
                                break

                    res, msg = self.dc.add_git_acct(site, nickname, token)
                    if res == 'Success':
                        th = threading.Thread(target=lambda: wait_for_repos(nickname), daemon=True)
                        th.start()

                        if threading.current_thread != th:
                            accts_tview_table.insert("", 'end', values=(site, nickname, msg, "Ready to make API calls"))
                            update_ui_state()
                            messagebox.showinfo(message='Added new account')
                            prompt_window.destroy()
                    else:
                        messagebox.showerror("Error", msg)

                width = 350
                height = 200
                c_x, c_y = self.parent_frame.get_root_center_coords()

                prompt_window = tk.Toplevel()
                prompt_window.title('Link GitHub/GitLab Account')
                prompt_window.geometry(f'{width}x{height}+{c_x - int(width / 2)}+{c_y - int(height / 2)}')
                prompt_window.grab_set()
                
                options = ['None', 'GitHub', 'GitLab']
                site_strvar = tk.StringVar()

                token_lbl_strvar = tk.StringVar(value='Enter the token:')

                opt_sel_frame = ttk.Frame(prompt_window)
                opt_sel_lbl = ttk.Label(opt_sel_frame, text="Remote Repo Site:")
                site_opt_sel = ttk.OptionMenu(opt_sel_frame, site_strvar, *options, command=opt_change)
                opt_sel_lbl.grid(row=0, column=0, padx=2)
                site_opt_sel.grid(row=0, column=1, padx=2)
                opt_sel_frame.pack(pady=5)

                nickname_entry_frame = ttk.Frame(prompt_window)
                nickname_entry_lbl = ttk.Label(nickname_entry_frame, text="Account Nickname (Optional):")
                nickname_entry = ttk.Entry(nickname_entry_frame, width=30)
                nickname_entry_lbl.grid(row=0, column=0, pady=(5, 2), sticky='w')
                nickname_entry.grid(row=1, column=0, pady=(0, 5), sticky='w')
                nickname_entry_frame.pack(pady=5)

                token_entry_frame = ttk.Frame(prompt_window)
                token_entry_lbl = ttk.Label(token_entry_frame, textvariable=token_lbl_strvar)
                token_entry = ttk.Entry(token_entry_frame, width=30)
                token_entry_lbl.grid(row=0, column=0, pady=(5, 2), sticky='w')
                token_entry.grid(row=1, column=0, pady=(0, 5), sticky='w')
                token_entry_frame.pack(pady=5)

                # Submit button
                submit_button = ttk.Button(prompt_window, text="Submit", state='disabled', command=submit_entry)
                submit_button.pack(pady=10)

            def edit_acct_prompt():
                # Function to handle submission
                def submit_entry():
                    token = token_entry.get().strip()
                    token_valid = token and len(token) > 0

                    if not token_valid:
                        messagebox.showerror("Error", "Must enter a valid token", parent=prompt_window)
                        return

                    res, msg = self.dc.update_git_acct(site, nickname, token)
                    user = msg

                    if res == 'Success':
                        th = threading.Thread(target=lambda: wait_for_repos(nickname), daemon=True)
                        th.start()

                        if threading.current_thread != th:
                            accts_tview_table.item(item, values=(site, nickname, user, details))
                            update_ui_state()
                            messagebox.showinfo(message=f"Updated '{nickname}' details")
                            prompt_window.destroy()
                    else:
                        messagebox.showerror("Error", f"Failed to update account, '{nickname}'")

                width = 350
                height = 150
                c_x, c_y = self.parent_frame.get_root_center_coords()

                prompt_window = tk.Toplevel()
                prompt_window.title('Edit Account')
                prompt_window.geometry(f'{width}x{height}+{c_x - int(width / 2)}+{c_y - int(height / 2)}')
                prompt_window.grab_set()

                try:
                    item = accts_tview_table.selection()[0]
                except:
                    prompt_window.destroy()
                    return
                
                values = accts_tview_table.item(item)['values']
                site = values[0]
                nickname = values[1]
                user = values[2]
                details = values[3]

                site_field_frame = ttk.Frame(prompt_window)
                site_field_lbl = ttk.Label(site_field_frame, text="Repo Site:")
                site_field = ttk.Label(site_field_frame, text=site)
                site_field_lbl.grid(row=0, column=0, padx=2)
                site_field.grid(row=0, column=1, padx=2)
                site_field_frame.pack(pady=(0, 3))

                nickname_field_frame = ttk.Frame(prompt_window)
                nickname_field_lbl = ttk.Label(nickname_field_frame, text="Account Nickname:")
                nickname_field = ttk.Label(nickname_field_frame, text=nickname)
                nickname_field_lbl.grid(row=0, column=0, padx=2)
                nickname_field.grid(row=0, column=1, padx=2)
                nickname_field_frame.pack(pady=(0, 3))

                token_entry_frame = ttk.Frame(prompt_window)
                token_entry_lbl = ttk.Label(token_entry_frame, text='Enter the token:')
                token_entry = ttk.Entry(token_entry_frame, width=30)
                token_entry_lbl.grid(row=0, column=0, pady=(5, 2), sticky='w')
                token_entry.grid(row=1, column=0, pady=(0, 5), sticky='w')
                token_entry_frame.pack(pady=(0, 3))

                # Submit button
                submit_button = ttk.Button(prompt_window, text="Submit", command=submit_entry)
                submit_button.pack(pady=10)

            def link_repo_prompt():
                def select(event=None):
                    avail_repos_tview.selection_toggle(avail_repos_tview.focus())
                    if len(avail_repos_tview.selection()) > 0:
                        link_btn['state'] = 'normal'
                    else:
                        link_btn['state'] = 'disabled'

                def link_selected():
                    items = avail_repos_tview.selection()
                    for id in items:
                        item = avail_repos_tview.item(id)['values']
                        self.dc.link_repo(item[1])
                        repo_tview_table.insert("", 'end', values=item)
                    update_ui_state()
                    prompt_window.destroy()

                width = 350
                height = 250
                c_x, c_y = self.parent_frame.get_root_center_coords()

                prompt_window = tk.Toplevel()
                prompt_window.title('Link Repositories')
                prompt_window.geometry(f'{width}x{height}+{c_x - int(width / 2)}+{c_y - int(height / 2)}')
                prompt_window.grab_set()

                repos = self.dc.get_avail_repos()
                if len(repos) < 1:
                    prompt_window.destroy()
                    return

                table_frame = ttk.Frame(prompt_window)
                table_hdr_frame = ttk.Frame(table_frame)

                header_lbl = ttk.Label(table_hdr_frame, text='Available Repos', font=('Arial', 10, 'bold'))
                header_lbl.pack()
                table_hdr_frame.pack(anchor='w')

                avail_repos_tview = ttk.Treeview(table_frame, selectmode='none', height=7)
                avail_repos_tview['columns'] = ('1', '2')
                avail_repos_tview['show'] = 'headings'
                avail_repos_tview.column('1', width=70, anchor='w')
                avail_repos_tview.column('2', width=190, anchor='w')
                avail_repos_tview.heading('1', text='Account', anchor='w')
                avail_repos_tview.heading('2', text='Repo', anchor='w')
                avail_repos_tview.pack()
                table_frame.pack(pady=(5, 5))

                avail_repos_tview.bind("<ButtonRelease-1>", select)

                for repo in repos:
                    avail_repos_tview.insert("", 'end', values=repo)

                # Submit button
                link_btn = ttk.Button(prompt_window, text="Link Selected Repos", command=link_selected, state='disabled')
                link_btn.pack(pady=10)

            def clear_selections(event=None):
                coords = self.parent_frame.parent_frame.master.winfo_pointerxy()
                x, y = coords
                widget = self.parent_frame.parent_frame.master.winfo_containing(x, y)
                
                on_accts_tree = f'{widget}' == '.!notebook.!gitframe.!configframe.!frame.!frame2.!frame.!treeview' \
                                or f'{widget}' == '.!notebook.!gitframe.!configframe.!frame.!frame2.!frame.!frame.!button2' \
                                or f'{widget}' == '.!notebook.!gitframe.!configframe.!frame.!frame2.!frame.!frame.!button3'
                
                on_repos_tree = f'{widget}' == '.!notebook.!gitframe.!configframe.!frame.!frame2.!frame2.!treeview' \
                                or f'{widget}' == '.!notebook.!gitframe.!configframe.!frame.!frame2.!frame2.!frame.!button2'
                
                if not on_accts_tree:
                    items = accts_tview_table.selection()
                    for item in items:
                        accts_tview_table.selection_remove(item)
                
                if not on_repos_tree:
                    items = repo_tview_table.selection()
                    for item in items:
                        repo_tview_table.selection_remove(item)
                    self.remove_repos_btn['state'] = 'disabled'


            def accts_on_selection(event):
                if not self.ui_disabled:
                    try:
                        items = accts_tview_table.selection()
                        if len(items) > 0:
                            self.edit_acct_btn['state'] = 'normal'
                            self.remove_acct_btn['state'] = 'normal'
                        else:
                            self.edit_acct_btn['state'] = 'disabled'
                            self.remove_acct_btn['state'] = 'disabled'
                    except:
                        pass

            def repos_on_selection(event):
                if not self.ui_disabled:
                    try:
                        repo_tview_table.selection_toggle(repo_tview_table.focus())
                        if len(repo_tview_table.selection()) > 0:
                            self.remove_repos_btn['state'] = 'normal'
                        else:
                            self.remove_repos_btn['state'] = 'disabled'
                    except:
                        pass

            def remove_acct():
                try:
                    item = accts_tview_table.selection()[0]
                    nname = accts_tview_table.item(item)['values'][1]
                    self.dc.remove_git_acct(nname)
                    accts_tview_table.delete(item)
                    for id in repo_tview_table.get_children():
                        item = repo_tview_table.item(id)['values']
                        if item[0] == nname:
                            repo_tview_table.delete(id)
                    self.remove_acct_btn['state'] = 'disabled'
                    update_ui_state()
                except:
                    pass

            def remove_repos():
                items = repo_tview_table.selection()
                if len(items) > 0:
                    for id in items:
                        try:
                            item = repo_tview_table.item(id)['values']
                            self.dc.unlink_repo(item[1])
                            repo_tview_table.delete(id)
                            self.remove_repos_btn['state'] = 'disabled'
                            update_ui_state()
                        except Exception as e:
                            print(f'EXCEPTION - {e}')

            def populate_repo_treeview():
                items = repo_tview_table.get_children()
                for id in items:
                    try:
                        repo_tview_table.delete(id)
                    except Exception as e:
                        print(f'EXCEPTION - {e}')

                for repo in self.dc.get_linked_repos():
                    repo_tview_table.insert("", 'end', values=repo)

            def refresh_avail_repos():
                def pull_all_acct_repos():
                    disable_ui()
                    self.message_strval.set('Refreshing available account repo list...')
                    self.dc.pull_all_repos()
                    populate_repo_treeview()
                    enable_ui()
                threading.Thread(target=pull_all_acct_repos, daemon=True).start()
                    
                    
            def init_values():
                for acct in self.dc.get_git_accts():
                    accts_tview_table.insert("", 'end', values=acct)
                if not self.dc.repos_available():
                    self.dc.pull_all_repos()
                populate_repo_treeview()

            details_panel = ttk.Frame(widget_frame)
            accts_frame = ttk.Frame(details_panel)
            accts_header_frame = ttk.Frame(accts_frame)

            header_lbl = ttk.Label(accts_header_frame, text='Authenticated Accounts', font=('Arial', 10, 'bold'))
            self.add_acct_btn = ttk.Button(accts_header_frame, text='Add', command=add_acct_prompt)
            self.edit_acct_btn = ttk.Button(accts_header_frame, text='Edit', command=edit_acct_prompt, state='disabled')
            self.remove_acct_btn = ttk.Button(accts_header_frame, text='Remove', command=remove_acct, state='disabled')

            header_lbl.grid(row=0, column=0, padx=(0, 5))
            self.add_acct_btn.grid(row=0, column=1, padx=2)
            self.edit_acct_btn.grid(row=0, column=2, padx=2)
            self.remove_acct_btn.grid(row=0, column=3, padx=2)
            accts_header_frame.pack(pady=1, anchor='w')

            accts_tview_table = ttk.Treeview(accts_frame, selectmode='browse', height=5)
            accts_tview_table.bind("<<TreeviewSelect>>", accts_on_selection)
            accts_tview_table['columns'] = ('1', '2', '3', '4')
            accts_tview_table['show'] = 'headings'
            accts_tview_table.column('1', width=80, anchor='w')
            accts_tview_table.column('2', width=80, anchor='w')
            accts_tview_table.column('3', width=80, anchor='w')
            accts_tview_table.column('4', width=300, anchor='w')
            accts_tview_table.heading('1', text='Site', anchor='w')
            accts_tview_table.heading('2', text='Nickname', anchor='w')
            accts_tview_table.heading('3', text='User', anchor='w')
            accts_tview_table.heading('4', text='Details', anchor='w')
            accts_tview_table.pack()
            
            repo_frame = ttk.Frame(details_panel)
            repo_header_frame = ttk.Frame(repo_frame)

            header_lbl = ttk.Label(repo_header_frame, text='Linked Repos', font=('Arial', 10, 'bold'))
            self.link_repos_btn = ttk.Button(repo_header_frame, text='Link', command=link_repo_prompt, state='disabled')
            self.remove_repos_btn = ttk.Button(repo_header_frame, text='Remove', command=remove_repos, state='disabled')
            self.refresh_repos_btn = ttk.Button(repo_header_frame, text='⟲', width=3, command=refresh_avail_repos, state='disabled')
            
            header_lbl.grid(row=0, column=0, padx=(0, 5))
            self.refresh_repos_btn.grid(row=0, column=1, padx=2)
            self.link_repos_btn.grid(row=0, column=2, padx=2)
            self.remove_repos_btn.grid(row=0, column=3, padx=2)
            repo_header_frame.pack(pady=1, anchor='w')

            repo_tview_table = ttk.Treeview(repo_frame, selectmode='none', height=5)
            repo_tview_table.bind("<ButtonRelease-1>", repos_on_selection)
            repo_tview_table['columns'] = ('1', '2')
            repo_tview_table['show'] = 'headings'
            repo_tview_table.column('1', width=70, anchor='w')
            repo_tview_table.column('2', width=210, anchor='w')
            repo_tview_table.heading('1', text='Account', anchor='w')
            repo_tview_table.heading('2', text='Repo', anchor='w')
            repo_tview_table.pack()

            accts_frame.grid(row=0, column=0, padx=3)
            repo_frame.grid(row=0, column=1, padx=3)

            self.parent_frame.parent_frame.master.bind("<Button-1>", clear_selections)
            init_values()

            return details_panel
        
        def import_data():
            def runner():
                disable_ui()
                self.message_strval.set('Preparing to import data...')
                self.import_commit_data()
                enable_ui()
            
            th = threading.Thread(target=runner, daemon=True)
            th.start()
        
        widget_frame = ttk.Frame(parent_frame)
        self.import_commit_data_btn = ttk.Button(widget_frame, text='Import Commit Data', command=import_data, state='disabled')

        config_lbl_frame = ttk.Frame(widget_frame)
        config_frame_lbl = ttk.Label(config_lbl_frame, text=f'{' ' * 4}Remote Repository Configuration{' ' * 4}', font=('Arial', 15))
        config_frame_lbl.pack()

        details_frame = build_details_panel()
        
        self.message_strval = StringVar(value='An account must be linked for using the API')
        msg_frame = ttk.Frame(widget_frame)
        message_field = ttk.Label(msg_frame, textvariable=self.message_strval, font=('Arial', 8, 'normal', 'italic'), padding=3, anchor='center')
        message_field.pack()
        
        ## Configure Acct Details Frame
        config_lbl_frame.pack(pady=(0, 6))
        details_frame.pack(pady=(0, 6))
        msg_frame.pack(pady=(0, 6))
        self.import_commit_data_btn.pack(pady=(0, 6))
        update_ui_state()

        return widget_frame
    
class DataFrame(ttk.Frame):
    def __init__(self, parent: GitFrame, dc: DataController):
        super().__init__(parent)

        self.commits_df_master : pd.Dataframe = None
        self.curr_commits_df : pd.DataFrame = None

        self.repos_df : pd.DataFrame = None
        self.repos : list[str] = None
        self.task_list : list[int] = None
        self.members : list[str] = None  

        self.commits_table_sheet : tks.Sheet = None
        self.start_date_filter : CustomDateEntry = None
        self.end_date_filter : CustomDateEntry = None

        self.content_frame : ttk.Frame = None
        self.parent_frame = parent
        self.dc = dc

    def commit_data_ready(self) -> bool:
        return self.curr_commits_df is not None and len(self.curr_commits_df) > 0
    
    def get_commit_data(self) -> pd.DataFrame:
        return self.curr_commits_df.copy(deep=True)
    
    def handle_data_to_tables(self):
        self.import_data_to_tables()

        if self.content_frame is None:
            self.build_table()
        else:
            self.update_sheets()

    def build_dropdowns(self, df=None):
        if df is None:
            df = self.curr_commits_df

        options = ['Not Set'] + self.task_list
        self.commits_table_sheet.create_dropdown('all', 1, values=options)
        for row, value in enumerate(df['task_num']):
            if pd.notna(value):
                value = f'{value}'
            else:
                value = 'Not Set'
            self.commits_table_sheet.set_cell_data(row, 1, value)

    def update_sheets(self):
        df_to_display = self.curr_commits_df[['az_date', 'task_num', 'committer', 'repo_name', 'commit_message']]
        self.commits_table_sheet.set_data(data=self.commits_df_to_table_format(df_to_display).values.tolist(), redraw=True)
        self.build_dropdowns()

    def save_data(self):
        self.dc.update_commit_df(self.curr_commits_df)

    def clear_data(self):
        ans = messagebox.askquestion(title='Delete All Commit Data', message='Are you sure?')
        if ans == 'yes':
            print('Deleting Commit Data...')
            self.commits_df_master = self.curr_commits_df = None
            self.dc.clear_commit_data()
            if self.content_frame:
                self.content_frame.destroy()
                self.content_frame = None

            messagebox.showinfo('Commit Data Deletion', 'Commit Data Cleared')

    
    def update_taiga_tasks(self):
        try:
            tasks_df = self.dc.get_task_df().sort_values(by='task_num', ascending=True)
            self.task_list = tasks_df['task_num'].dropna().drop_duplicates().tolist()
        except:
            tasks_df = self.curr_commits_df.copy(deep=True).sort_values(by='task_num', ascending=True)
            self.task_list = tasks_df['task_num'].dropna().drop_duplicates().tolist()

    def import_data_to_tables(self):
        self.commits_df_master = self.dc.get_commits_df()
        self.curr_commits_df = self.dc.update_df(self.curr_commits_df, self.commits_df_master)
        self.curr_commits_df.sort_values(by='utc_datetime', ascending=True, inplace=True)

        self.repos = self.commits_df_master['repo_name'].dropna().drop_duplicates().to_list()
        self.members = self.commits_df_master['committer'].dropna().drop_duplicates().to_list()
        self.update_taiga_tasks()

    def _inv_val_format(self, df: pd.DataFrame):
        df = df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA)

    def commits_df_to_table_format(self, df : pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy(deep=True)
        self._inv_val_format(df_copy)
        df_copy['committer'] = df_copy['committer'].astype(pd.StringDtype())
        df_copy['committer'] = df_copy['committer'].replace(pd.NA, 'Unknown')
        df_copy['task_num'] = df_copy['task_num'].astype(pd.StringDtype())
        df_copy['task_num'] = df_copy['task_num'].replace(pd.NA, 'Not Set')
        return df_copy

    def commits_df_from_table_format(self, df : pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy(deep=True)
        self._inv_val_format(df_copy)
        df_copy['committer'] = df_copy['committer'].replace('Unknown', pd.NA)
        df_copy['task_num'] = df_copy['task_num'].replace('Not Set', pd.NA)
        df_copy['task_num'] = df_copy['task_num'].astype(pd.Int64Dtype())
        return df_copy

    def build_table(self):
        def generate_field_obj(parent, lbl_str, target_obj):
            field_lbl = ttk.Label(parent, text=lbl_str, anchor='e')
            field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
            target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')

        def build_header_frame(data_frame):
            def build_tab_btn_frame(parent):
                widget_frame = ttk.Frame(parent)
                btn_frame = ttk.Frame(widget_frame)
                save_data_btn = ttk.Button(btn_frame, text='Save Commit Data', command=self.save_data)
                clear_data_btn = ttk.Button(btn_frame, text='Clear All Commit Data', command=self.clear_data)
                save_data_btn.grid(row=0, column=0, padx=(2, 1))
                clear_data_btn.grid(row=0, column=1, padx=(2, 1))
                btn_frame.pack(anchor='e')
                return widget_frame

            hdr_frame = ttk.Frame(data_frame, borderwidth=2, relief='ridge')
            hdr_frame.pack(fill='x', pady=3) 
            hdr_lbl = ttk.Label(hdr_frame, text=f'{' ' * 4}Commits Data{' ' * 4}', font=('Arial', 13, 'bold'))
            hdr_lbl.place(relx=0.5, rely=0.5, anchor='center')
            btn_frame = build_tab_btn_frame(hdr_frame)
            btn_frame.pack(pady=3, side='right')
            return hdr_frame

        ## Table Creation
        ##=========================================================================================================================================
        def build_table_display(parent):
            ## Useful Variables
            padx = 3
            sticky = 'nsew'

            repo_options = ['ALL'] + self.repos
            task_options = ['ALL', 'Not Set'] + self.curr_commits_df['task_num'].sort_values(ascending=True).dropna().drop_duplicates().tolist()

            committer_options = ['ALL']
            if self.commits_df_master['committer'].isna().any():
                committer_options.append('Unknown')
            committer_options += self.members
            
            repo_strvar = StringVar()
            task_strvar = StringVar()
            committer_strvar = StringVar()

            def apply_filters(*args):
                repo = repo_strvar.get()
                task = task_strvar.get()
                committer = committer_strvar.get()

                start_date = self.start_date_filter.get_date_val()
                end_date = self.end_date_filter.get_date_val()

                repo_filtered = repo != 'ALL'
                task_filtered = task != 'ALL'
                committer_filtered = committer != 'ALL'
                start_date_filtered = self.start_date_filter.date_selected()
                end_date_filtered = self.end_date_filter.date_selected()

                if repo_filtered or task_filtered or committer_filtered or start_date_filtered or end_date_filtered:
                    rows = []
                    for rn, row in enumerate(self.commits_table_sheet.data):
                        row_match = True

                        if repo_filtered and row[3] != repo:
                            row_match = False
                        
                        if task_filtered and row[1] != task:
                            row_match = False

                        if committer_filtered and row[2] != committer:
                            row_match = False

                        if start_date_filtered and pd.Timestamp(row[0]) < pd.Timestamp(start_date):
                            row_match = False

                        if end_date_filtered and pd.Timestamp(row[0]) > pd.Timestamp(end_date):
                            row_match = False

                        if row_match:
                            rows.append(rn)

                    self.commits_table_sheet.display_rows(rows=rows, all_displayed=False, redraw=True)
                    self.commits_table_sheet.hide
                    self.clear_filters_btn['state'] = 'normal'
                else:
                    self.clear_filters_btn['state'] = 'disabled'
                    self.commits_table_sheet.display_rows('all', redraw=True)

            def table_change(event):
                for (row, col), _ in event.cells.table.items():
                    try:
                        
                        headers = self.commits_table_sheet.headers()
                        col_name = headers[col]

                        # Convert data type based on original DataFrame column type
                        try:
                            new_val = int(self.commits_table_sheet.get_cell_data(row, col, True))
                        except:
                            new_val = pd.NA
                        self.curr_commits_df.at[row, col_name] = new_val  # Update DataFrame

                        print(f"Updated Commits DataFrame: \nRow - {row}, Column Name - {col_name}, New Value - {new_val}\n")  # Debug print
                    except Exception as e:
                        print(f"Error updating DataFrame: {e}")

                self.commits_table_sheet.reset_changed_cells()  # Clear change tracker after update

            def build_filter_panel(parent_frame):
                def clear_filters():
                    repo_opt_sel.reset()
                    task_opt_sel.reset()
                    committer_opt_sel.reset()
                    self.start_date_filter.reset()
                    self.end_date_filter.reset()
                    apply_filters()
                
                filter_frame = ttk.Frame(parent_frame)
                options_frame = ttk.Frame(filter_frame)

                repo_filter_frame = ttk.Frame(options_frame)
                task_filter_frame = ttk.Frame(options_frame)
                committer_filter_frame = ttk.Frame(options_frame)
                start_date_filter_frame = ttk.Frame(options_frame)
                end_date_filter_frame = ttk.Frame(options_frame)
                btn_frame = ttk.Frame(options_frame)
        
                filter_section_lbl = ttk.Label(options_frame, text='Filters:', font=('Arial', 11, 'bold'))
                repo_opt_sel = CustomComboBox(repo_filter_frame, repo_strvar, *repo_options, comp_id='repo', default='ALL')
                generate_field_obj(repo_filter_frame, 'Repo:', repo_opt_sel)
                task_opt_sel = CustomComboBox(task_filter_frame, task_strvar, *task_options, comp_id='git_task', default='ALL')
                generate_field_obj(task_filter_frame, 'Task:', task_opt_sel)
                committer_opt_sel = CustomComboBox(committer_filter_frame, committer_strvar, *committer_options, comp_id='committer', default='ALL')
                generate_field_obj(committer_filter_frame, 'Committer:', committer_opt_sel)
                self.start_date_filter = CustomDateEntry(start_date_filter_frame)
                generate_field_obj(start_date_filter_frame, 'After:', self.start_date_filter)
                self.end_date_filter = CustomDateEntry(end_date_filter_frame)
                generate_field_obj(end_date_filter_frame, 'Before:', self.end_date_filter)

                self.clear_filters_btn = ttk.Button(btn_frame, text='Clear Filters', state='disabled', command=clear_filters)
                self.clear_filters_btn.pack(pady=(0, 2))

                repo_strvar.trace_add(mode='write', callback=apply_filters)
                task_strvar.trace_add(mode='write', callback=apply_filters)
                committer_strvar.trace_add(mode='write', callback=apply_filters)
                self.start_date_filter.bind('<<DateEntrySelected>>', apply_filters)
                self.end_date_filter.bind('<<DateEntrySelected>>', apply_filters)

                filter_section_lbl.grid(row=0, column=0, padx=padx, sticky=sticky)
                repo_filter_frame.grid(row=0, column=1, padx=padx, sticky=sticky)
                task_filter_frame.grid(row=0, column=2, padx=padx, sticky=sticky)
                committer_filter_frame.grid(row=0, column=3, padx=padx, sticky=sticky)
                start_date_filter_frame.grid(row=0, column=4, padx=padx, sticky=sticky)
                end_date_filter_frame.grid(row=0, column=5, padx=padx, sticky=sticky)

                btn_frame.grid(row=0, column=6, padx=padx, sticky=sticky)
                
                options_frame.pack(pady=(4, 4), anchor='w')
                return filter_frame

            def build_table_panel(parent_frame):
                table_frame = ttk.Frame(parent_frame)
                
                df = self.commits_df_to_table_format(self.curr_commits_df[['az_date', 'task_num', 'committer', 'repo_name', 'commit_message']])
                rows = len(df)
                cols = len(df.columns)

                self.commits_table_sheet = tks.Sheet(table_frame, data=df.values.tolist(), header=df.columns.tolist())
                self.build_dropdowns(df)

                column_widths = []
                index = 0
                remaining_width = 960
                curr_total = 0
                for column in df.columns.tolist():
                    if column != 'commit_message':
                        text_width = self.commits_table_sheet.get_column_text_width(index)
                    else:
                        text_width = remaining_width
                    
                    curr_total += text_width
                    remaining_width -= text_width
                        
                    column_widths.append(text_width)
                    curr_total += text_width
                    index += 1

                # self.commits_table_sheet.set_column_widths(column_widths=column_widths)
                self.commits_table_sheet.enable_bindings()
                self.commits_table_sheet.extra_bindings("end_edit_cell", table_change)  # Call function after edit
                self.commits_table_sheet.disable_bindings('move_columns', 'move_rows', 'edit_cell', 'rc_insert_column', 'rc_delete_column')
                self.commits_table_sheet.readonly_columns(columns=[0, 2, 3, 4])
                self.commits_table_sheet.pack(fill='both', expand=True)

                self.commits_table_sheet.set_sheet_data_and_display_dimensions(total_rows=rows, total_columns=cols)
                self.commits_table_sheet.set_column_widths(column_widths)
                
                return table_frame
            
            widget_frame = ttk.Frame(parent)
            filter_panel = build_filter_panel(widget_frame)
            table_panel = build_table_panel(widget_frame)

            filter_panel.pack() 
            table_panel.pack(expand = 1, fill='both') 
            
            return widget_frame

        ## DataFrame build logic
        ##=========================================================================================================================================
        if self.content_frame is not None:
            self.content_frame.destroy()

        self.content_frame = ttk.Frame(self)
        header_frame = build_header_frame(self.content_frame)

        table_panel = ttk.Frame(self.content_frame)
        commits_table = build_table_display(table_panel)
        commits_table.pack(fill='both', expand=True)

        header_frame.pack(fill ='x') 
        table_panel.pack(expand = 1, fill ="both") 
        self.content_frame.pack(expand = 1, fill ="both") 
    

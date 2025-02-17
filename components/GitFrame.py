import tkinter as tk
from tkinter import ttk, StringVar, messagebox
import tksheet as tks

from typing import Type
import pandas as pd
import numpy as np
import threading
import shortuuid as suuid

from models.DataManager import DataController
from components.CustomComponents import CustomOptionMenu

class GitFrame(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, dc: DataController):
        super().__init__(parent)
        
        self.dc = dc
        self.parent_frame = parent
        self.root = parent.master

        self.config_frame = ConfigFrame(self, dc)
        # self.data_frame = DataFrame(self, dc)

        self.config_frame.pack(fill='x', anchor='n', pady=(0, 10))
        # self.data_frame.pack(fill='both', expand=True, anchor='n')

        # if self.dc.commit_data_ready():
        #     self.setup_dataframe()

    def setup_dataframe(self):
        self.data_frame.handle_data_to_tables()

    def commit_data_ready(self) -> bool:
        return self.data_frame.commit_data_ready()
    
    def get_commit_data(self) -> pd.DataFrame:
        return self.data_frame.get_commit_data()

    def import_gh_data(self):
        temp_lbl = ttk.Label(self.config_frame, text='Handling GitHub API Call, Please Wait...')
        temp_lbl.pack()

        try:
            if self.dc.validate_gh_auth():
                if self.dc.validate_gh_repo():

                    self.dc.make_gh_api_call()
                    df = self.dc.get_git_master_df()
                    self.data_frame.build_data_display(df)
                    
                else:
                    self.dialog('The specified repo does not exist')
            else:
                self.dialog('The token is invalid')
        except:
            self.dialog('Failed to import data')
        finally:
            temp_lbl.destroy()

    def import_gl_data(self):
        temp_lbl = ttk.Label(self.config_frame, text='Handling GitLab API Call, Please Wait...')
        temp_lbl.pack()

        try:
            if self.dc.validate_gh_auth():
                if self.dc.validate_gh_repo():

                    self.dc.make_gh_api_call()
                    df = self.dc.get_git_master_df()
                    self.data_frame.build_data_display(df)
                    
                else:
                    self.dialog('The specified repo does not exist')
            else:
                self.dialog('The token is invalid')
        except:
            self.dialog('Failed to import data')
        finally:
            temp_lbl.destroy()
    
class ConfigFrame(ttk.Frame):
    def __init__(self, parent: GitFrame, dc: DataController):
        super().__init__(parent)
        self.linked_repos = None

        self.is_linked = False
        self.repo_linked = False

        self.dc = dc
        self.parent_frame = parent

        config_frame = self._build_config_frame(self)
        config_frame.pack(fill='x', expand=True, padx=8, pady=8)

    def _generate_field_obj(self, field_frame, lbl_str, target_obj, btn_obj=None):
        field_lbl = ttk.Label(field_frame, text=lbl_str, anchor='e')
        field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
        target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')
        if btn_obj is not None:
            btn_obj.grid(row=0, column=2, padx=(4, 4))
        return target_obj

    def _build_config_frame(self, parent_frame) -> ttk.Frame:
        def build_details_panel():
            def wait_for_repos(nickname):
                self.message_strval.set(f'Pulling Account {nickname} Repository List...')
                link_repos_btn['state'] = 'disabled'
                self.dc.pull_repos(nickname)
                link_repos_btn['state'] = 'normal'
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
                            th = threading.Thread(target=lambda: wait_for_repos(nickname))
                            th.start()

                            if threading.current_thread != th:
                                accts_tview_table.insert("", 'end', values=(site, nickname, msg, "Ready to make API calls"))
                                update_btn_states()
                                messagebox.showinfo(message='Added new account')
                                prompt_window.destroy()
                        else:
                            messagebox.showerror("Error", msg)

                prompt_window = tk.Toplevel()
                prompt_window.title('Link GitHub/GitLab Account')
                prompt_window.geometry("350x200")
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
                        th = threading.Thread(target=lambda: wait_for_repos(nickname))
                        th.start()

                        if threading.current_thread != th:
                            accts_tview_table.item(item, values=(site, nickname, user, details))
                            update_btn_states()
                            messagebox.showinfo(message=f"Updated '{nickname}' details")
                            prompt_window.destroy()
                    else:
                        messagebox.showerror("Error", f"Failed to update account, '{nickname}'")

                prompt_window = tk.Toplevel()
                prompt_window.title('Edit Account')
                prompt_window.geometry("350x150")
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
                        link_repos_btn['state'] = 'normal'
                    else:
                        link_repos_btn['state'] = 'disabled'

                def link_selected():
                    items = avail_repos_tview.selection()
                    for id in items:
                        item = avail_repos_tview.item(id)['values']
                        self.dc.link_repo(item[1])
                        repo_tview_table.insert("", 'end', values=item)

                    update_btn_states()
                    prompt_window.destroy()

                prompt_window = tk.Toplevel()
                prompt_window.title('Link Repositories')
                prompt_window.geometry("350x250")
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
                # avail_repos_tview.bind("<<TreeviewSelect>>", accts_on_selection)
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
                link_repos_btn = ttk.Button(prompt_window, text="Link Selected Repos", command=link_selected, state='disabled')
                link_repos_btn.pack(pady=10)

            def clear_selections(event):
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
                    remove_repos_btn['state'] = 'disabled'


            def accts_on_selection(event):
                try:
                    items = accts_tview_table.selection()
                    if len(items) > 0:
                        edit_acct_btn['state'] = 'normal'
                        remove_acct_btn['state'] = 'normal'
                    else:
                        edit_acct_btn['state'] = 'disabled'
                        remove_acct_btn['state'] = 'disabled'
                except:
                    pass

            def repos_on_selection(event):
                try:
                    repo_tview_table.selection_toggle(repo_tview_table.focus())
                    if len(repo_tview_table.selection()) > 0:
                        remove_repos_btn['state'] = 'normal'
                    else:
                        remove_repos_btn['state'] = 'disabled'
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
                    update_btn_states()
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
                        except Exception as e:
                            print(f'EXCEPTION - {e}')
                    update_btn_states()

            def update_btn_states():
                api_ready = self.dc.api_call_ready()
                repos_linked = self.dc.repos_linked()

                if api_ready:
                    link_repos_btn['state'] = 'normal'
                else:
                    link_repos_btn['state'] = 'disabled'

                if api_ready and repos_linked:
                    self.import_commit_data_btn['state'] = 'normal'
                else:
                    self.import_commit_data_btn['state'] = 'disabled'

            def init_values():
                for acct in self.dc.get_git_accts():
                    accts_tview_table.insert("", 'end', values=acct)

                if not self.dc.repos_available():
                    self.dc.pull_all_repos()

                for repo in self.dc.get_linked_repos():
                    repo_tview_table.insert("", 'end', values=repo)

                update_btn_states()

            details_panel = ttk.Frame(widget_frame)

            accts_frame = ttk.Frame(details_panel)
            accts_header_frame = ttk.Frame(accts_frame)

            header_lbl = ttk.Label(accts_header_frame, text='Authenticated Accounts', font=('Arial', 10, 'bold'))
            add_acct_btn = ttk.Button(accts_header_frame, text='Add', command=add_acct_prompt)
            edit_acct_btn = ttk.Button(accts_header_frame, text='Edit', command=edit_acct_prompt, state='disabled')
            remove_acct_btn = ttk.Button(accts_header_frame, text='Remove', command=remove_acct, state='disabled')

            header_lbl.grid(row=0, column=0, padx=(0, 5))
            add_acct_btn.grid(row=0, column=1, padx=2)
            edit_acct_btn.grid(row=0, column=2, padx=2)
            remove_acct_btn.grid(row=0, column=3, padx=2)
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
            link_repos_btn = ttk.Button(repo_header_frame, text='Link', command=link_repo_prompt, state='disabled')
            remove_repos_btn = ttk.Button(repo_header_frame, text='Remove', command=remove_repos, state='disabled')

            header_lbl.grid(row=0, column=0, padx=(0, 5))
            link_repos_btn.grid(row=0, column=1, padx=2)
            remove_repos_btn.grid(row=0, column=2, padx=2)
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
        
        widget_frame = ttk.Frame(parent_frame)
        self.import_commit_data_btn = ttk.Button(widget_frame, text='Import Commit Data', command=print, state='disabled')

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

        # initialize_fields()
        return widget_frame
    
class DataFrame(ttk.Frame):
    def __init__(self, parent: GitFrame, dc: DataController):
        super().__init__(parent)

        self.commits_df_master : pd.Dataframe = None
        self.curr_commits_df : pd.DataFrame = None

        self.repos_df : pd.DataFrame = None
        self.task_list : list[int] = None
        self.members : list[str] = None  

        self.commits_table_sheet : tks.Sheet = None

        self.content_frame : ttk.Frame = None
        self.parent_frame = parent
        self.dc = dc

    def commit_data_ready(self) -> bool:
        return self.curr_commits_df is not None and len(self.curr_commits_df) > 0
    
    def get_commit_data(self) -> pd.DataFrame:
        return self.sheet_master_df.copy(deep=True)
    
    def handle_data_to_tables(self):
        self.import_data_to_tables()

        if self.content_frame is None:
            self.init_and_display_dataframe()
        else:
            self.update_sheets()

    def update_sheets(self):
        self.us_table_sheet.set_data(data=self.us_df_to_table_format(self.curr_us_df).values.tolist(), redraw=True)
        self.tasks_table_sheet.set_data(data=self.tasks_df_to_table_format(self.curr_tasks_df).values.tolist(), redraw=True)

    def save_data(self):
        print(self.curr_tasks_df)
        self.dc.update_us_df(self.curr_us_df)
        self.dc.update_tasks_df(self.curr_tasks_df, ['task_num', 'us_num', 'is_coding', 'is_complete', 'assignee', 'task_subject'])

    def clear_data(self):
        ans = messagebox.askquestion(title='Delete All Taiga Data', message='Are you sure?')
        if ans == 'yes':
            print('Deleting Taiga Data...')
            self.us_df_master = self.curr_us_df \
                = self.tasks_df_master = self.curr_tasks_df \
                    = self.sprints = self.members = self.user_stories = None
            self.dc.clear_taiga_data()
            if self.content_frame:
                self.content_frame.destroy()
                self.content_frame = None

            messagebox.showinfo('Taiga Data Deletion', 'Taiga Data Cleared')


    def import_data_to_tables(self):
        self.us_df_master = self.dc.update_df(self.us_df_master, self.dc.get_us_df())
        self.tasks_df_master = self.dc.update_df(self.tasks_df_master, self.dc.get_task_df(), 'id', ['task_num', 'us_num', 'is_complete', 'assignee', 'task_subject'])

        self.curr_us_df = self.dc.update_df(self.curr_us_df, self.us_df_master)
        self.curr_tasks_df = self.dc.update_df(self.curr_tasks_df, self.tasks_df_master, 'id', ['task_num', 'us_num', 'is_complete', 'assignee', 'task_subject'])

        self.sprints = self.us_df_master['sprint'].dropna().drop_duplicates().to_list()
        self.user_stories = self.tasks_df_master['us_num'].dropna().drop_duplicates().to_list()
        self.members = self.tasks_df_master['assignee'].dropna().drop_duplicates().to_list()

    def _inv_val_format(self, df: pd.DataFrame):
        df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA, inplace=True)

    def us_df_to_table_format(self, df : pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy(deep=True)
        self._inv_val_format(df_copy)
        df_copy['id'] = df_copy['id'].astype(pd.Int64Dtype())
        df_copy['us_num'] = df_copy['us_num'].astype(pd.Int64Dtype())
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.StringDtype())
        df_copy['is_complete'].replace({'True': 'Complete', 'False': 'In Process'}, inplace=True)
        df_copy['points'] = df_copy['points'].astype(pd.Int64Dtype())
        df_copy['sprint'].replace({pd.NA: 'Not Assigned'}, inplace=True)
        return df_copy

    def us_df_from_table_format(self, df : pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy(deep=True)
        self._inv_val_format(df_copy)
        df_copy['id'] = df_copy['id'].astype(pd.Int64Dtype())
        df_copy['us_num'] = df_copy['us_num'].astype(pd.Int64Dtype())
        df_copy['points'] = df_copy['points'].astype(pd.Int64Dtype())
        df_copy['is_complete'].replace({'Complete': '1', 'In-process': '0'}, inplace=True)
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.Int64Dtype())
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.BooleanDtype())
        return df_copy

    def tasks_df_to_table_format(self, df : pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy(deep=True)
        self._inv_val_format(df_copy)
        df_copy['id'] = df_copy['id'].astype(pd.Int64Dtype())
        df_copy['task_num'] = df_copy['task_num'].astype(pd.Int64Dtype())
        df_copy['is_coding'] = df_copy['is_coding'].astype(pd.BooleanDtype())
        df_copy['us_num'] = df_copy['us_num'].astype(pd.StringDtype())
        df_copy['us_num'].replace(pd.NA, 'Storyless', inplace=True)
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.StringDtype())
        df_copy['is_complete'].replace({'True': 'Complete', 'False': 'In-process'}, inplace=True)
        df_copy['assignee'].replace(pd.NA, 'Unassigned', inplace=True)
        return df_copy

    def tasks_df_from_table_format(self, df : pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy(deep=True)
        self._inv_val_format(df_copy)
        df_copy['id'] = df_copy['id'].astype(pd.Int64Dtype())
        df_copy['us_num'].replace('Storyless', pd.NA, inplace=True)
        df_copy['us_num'] = df_copy['us_num'].astype(pd.Int64Dtype())
        df_copy['task_num'] = df_copy['task_num'].astype(pd.Int64Dtype())
        df_copy['is_coding'] = df_copy['is_coding'].astype(pd.BooleanDtype())
        df_copy['is_complete'].replace({'Complete': '1', 'In-process': '0'}, inplace=True)
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.Int64Dtype())
        df_copy['is_complete'] = df_copy['is_complete'].astype(pd.BooleanDtype())
        df_copy['assignee'].replace('Unassigned', pd.NA, inplace=True)
        return df_copy

    def init_and_display_dataframe(self):
        def generate_field_obj(parent, lbl_str, target_obj):
            field_lbl = ttk.Label(parent, text=lbl_str, anchor='e')
            field_lbl.grid(row=0, column=0, padx=(2, 1), sticky='nsew')
            target_obj.grid(row=0, column=1, padx=(1, 2), sticky='nsew')

        def build_header_frame(data_frame):
            def build_tab_btn_frame(parent):
                widget_frame = ttk.Frame(parent)
                btn_frame = ttk.Frame(widget_frame)
                save_data_btn = ttk.Button(btn_frame, text='Save Taiga Data', command=self.save_data)
                clear_data_btn = ttk.Button(btn_frame, text='Clear All Taiga Data', command=self.clear_data)
                save_data_btn.grid(row=0, column=0, padx=(2, 1))
                clear_data_btn.grid(row=0, column=1, padx=(2, 1))
                btn_frame.pack(anchor='e')
                return widget_frame

            header_frame = ttk.Frame(data_frame)
            # taiga_data_header_lbl = ttk.Label(header_frame, text=f'{' ' * 4}Taiga Data{' ' * 4}', font=('Arial', 15))
            btn_frame = build_tab_btn_frame(header_frame)
            # taiga_data_header_lbl.pack(pady=2)
            btn_frame.pack(fill='x', pady=2)
            return header_frame

        ## US Tab Creation
        ##=========================================================================================================================================
        def build_us_tab(parent):
            ## Useful Variables
            padx = 3
            sticky = 'nsew'

            sprint_options = [None, 'None', 'Not Assigned'] + self.sprints
            completion_options = [None, 'None', 'Complete', 'In Process']

            sprint_select_strvar = StringVar()
            completion_select_strvar = StringVar()

            def apply_filters(*args):
                sprint = sprint_select_strvar.get()
                compl = completion_select_strvar.get()

                sprint_filter = sprint != 'None'
                completion_filter = compl != 'None'

                if sprint_filter or completion_filter:
                    rows = []
                    for rn, row in enumerate(self.us_table_sheet.data):
                        row_match = True

                        if sprint_filter and row[3] != sprint:
                            row_match = False
                        
                        if completion_filter and row[2] != compl:
                            row_match = False

                        if row_match:
                            rows.append(rn)

                    self.us_table_sheet.display_rows(rows=rows, all_displayed=False, redraw=True)
                    self.us_clear_filters_btn['state'] = 'normal'
                else:
                    self.us_clear_filters_btn['state'] = 'disabled'
                    self.us_table_sheet.display_rows('all', redraw=True)

            def us_table_change(event):
                change_dict = { 'is_complete': {'Complete': True, 'In-process': False } }

                for (row, col), old_value in event.cells.table.items():
                    try:
                        # Convert data type based on original DataFrame column type
                        col_name = self.curr_us_df.columns[col]
                        new_val = not change_dict[col_name][old_value]  # Since the event only returns the old value
                        self.curr_us_df.at[row, col_name] = new_val  # Update DataFrame

                        print(f"Updated US DataFrame: \nRow - {row}, Column Name - {col_name}, New Value - {new_val}\n")  # Debug print
                    except Exception as e:
                        print(f"Error updating DataFrame: {e}")

                self.us_table_sheet.reset_changed_cells()  # Clear change tracker after update

            def build_filter_panel(parent_frame):
                def clear_filters():
                    sprint_opt_sel.reset()
                    completion_opt_sel.reset()
                
                filter_frame = ttk.Frame(parent_frame)
                options_frame = ttk.Frame(filter_frame)

                sprint_filter_frame = ttk.Frame(options_frame)
                complete_filter_frame = ttk.Frame(options_frame)
        
                filter_section_lbl = ttk.Label(options_frame, text='Filters:', font=('Arial', 11, 'bold'))
                sprint_opt_sel = CustomOptionMenu(sprint_filter_frame, sprint_select_strvar, *sprint_options)
                generate_field_obj(sprint_filter_frame, 'Sprint:', sprint_opt_sel)
                completion_opt_sel = CustomOptionMenu(complete_filter_frame, completion_select_strvar, *completion_options)
                generate_field_obj(complete_filter_frame, 'Complete:', completion_opt_sel)
                self.us_clear_filters_btn = ttk.Button(options_frame, text='Clear Filters', state='disabled', command=clear_filters)

                sprint_select_strvar.trace_add(mode='write', callback=apply_filters)
                completion_select_strvar.trace_add(mode='write', callback=apply_filters)

                filter_section_lbl.grid(row=0, column=0, padx=padx, sticky=sticky)
                sprint_filter_frame.grid(row=0, column=1, padx=padx, sticky=sticky)
                complete_filter_frame.grid(row=0, column=3, padx=padx, sticky=sticky)
                self.us_clear_filters_btn.grid(row=0, column=4, padx=padx, sticky=sticky)
                
                options_frame.pack(pady=(4, 4), anchor='w')
                return filter_frame

            def build_table_panel(parent_frame):
                table_frame = ttk.Frame(parent_frame)
                
                df = self.us_df_to_table_format(self.curr_us_df)
                rows = len(df)
                cols = len(df.columns)

                self.us_table_sheet = tks.Sheet(table_frame, data=df.values.tolist(), header=df.columns.tolist(), width=500)

                column_widths = []
                index = 0
                total_width = 0
                for column in df.columns.tolist():
                    text_width = self.us_table_sheet.get_column_text_width(index)
                    # if column == 'task_subject':
                    #     text_width = 500

                    column_widths.append(text_width)
                    total_width += text_width
                    index += 1

                self.us_table_sheet.enable_bindings()
                self.us_table_sheet.disable_bindings('move_columns', 'move_rows', 'edit_cell', 'rc_insert_column', 'rc_delete_column')
                self.us_table_sheet.readonly_columns(columns=[0, 1, 2, 3, 4, 5])
                self.us_table_sheet.pack(fill='y', expand=True)

                self.us_table_sheet.set_sheet_data_and_display_dimensions(total_rows=rows, total_columns=cols)
                self.us_table_sheet.config(width=(total_width * 1.15))
                self.us_table_sheet.set_all_cell_sizes_to_text()
                return table_frame
            
            widget_frame = ttk.Frame(parent)
            hdr_frame = ttk.Frame(widget_frame, borderwidth=2, relief='ridge')
            
            hdr_lbl =  ttk.Label(hdr_frame, text=f'{' ' * 4}User Story Data{' ' * 4}', font=('Arial', 13, 'bold'))
            hdr_lbl.pack()
            filter_panel = build_filter_panel(widget_frame)
            table_panel = build_table_panel(widget_frame)

            hdr_frame.pack(fill='x') 
            filter_panel.pack() 
            table_panel.pack(expand = 1, fill='y') 
            
            return widget_frame
        
        ## Task Tab Creation
        ##=========================================================================================================================================
        def build_task_tab(parent):
            ## Useful Variables
            padx = 3
            sticky = 'nsew'

            us_options = [None, 'None','Storyless'] + self.user_stories
            user_options = [None, 'None' ,'Unassigned'] + self.members
            coding_options = [None, 'None', np.True_, np.False_]

            us_select_strvar = StringVar()
            user_select_strvar = StringVar()
            coding_select_strvar = StringVar()

            def apply_filters(*args):
                us = us_select_strvar.get()
                user = user_select_strvar.get()
                coding_val = coding_select_strvar.get()
                coding = coding_val if coding_val == 'None' else eval(coding_val)

                us_filter = us != 'None'
                user_filter = user != 'None'
                coding_filter = coding != 'None'

                if us_filter or user_filter or coding_filter:
                    rows = []
                    for rn, row in enumerate(self.tasks_table_sheet.data):
                        row_match = True

                        if us_filter and row[2] != us:
                            row_match = False
                        if user_filter and row[5] != user:
                            row_match = False
                        if coding_filter and row[3] != coding:
                            row_match = False

                        if row_match:
                            rows.append(rn)

                    self.tasks_table_sheet.display_rows(rows=rows, all_displayed=False, redraw=True)
                    self.task_clear_filters_btn['state'] = 'normal'
                else:
                    self.task_clear_filters_btn['state'] = 'disabled'
                    self.tasks_table_sheet.display_rows('all', redraw=True)

            def task_table_change(event):
                change_dict = { 'is_coding': { np.True_: True, np.False_: False } }

                for (row, col), old_value in event.cells.table.items():
                    try:
                        # Convert data type based on original DataFrame column type
                        col_name = self.curr_tasks_df.columns[col]
                        new_val = not change_dict[col_name][old_value]  # Since the event only returns the old value
                        self.curr_tasks_df.at[row, col_name] = new_val  # Update DataFrame

                        print(f"Updated Tasks DataFrame: \nRow - {row}, Column Name - {col_name}, New Value - {new_val}\n")  # Debug print
                    except Exception as e:
                        print(f"Error updating DataFrame: {e}")

                self.tasks_table_sheet.reset_changed_cells()  # Clear change tracker after update

            def build_filter_panel(parent_frame):
                def clear_filters():
                    us_opt_sel.reset()
                    user_opt_sel.reset()
                    coding_opt_sel.reset()
                
                filter_frame = ttk.Frame(parent_frame)
                options_frame = ttk.Frame(filter_frame)

                us_filter_frame = ttk.Frame(options_frame)
                user_filter_frame = ttk.Frame(options_frame)
                coding_filter_frame = ttk.Frame(options_frame)
        
                filter_section_lbl = ttk.Label(options_frame, text='Filters:', font=('Arial', 11, 'bold'))
                us_opt_sel = CustomOptionMenu(us_filter_frame, us_select_strvar, *us_options)
                generate_field_obj(us_filter_frame, 'User Story:', us_opt_sel)
                user_opt_sel = CustomOptionMenu(user_filter_frame, user_select_strvar, *user_options)
                generate_field_obj(user_filter_frame, 'Assigned To:', user_opt_sel)
                coding_opt_sel = CustomOptionMenu(coding_filter_frame, coding_select_strvar, *coding_options)
                generate_field_obj(coding_filter_frame, 'Coding Task:', coding_opt_sel)
                self.task_clear_filters_btn = ttk.Button(options_frame, text='Clear Filters', state='disabled', command=clear_filters)

                us_select_strvar.trace_add(mode='write', callback=apply_filters)
                user_select_strvar.trace_add(mode='write', callback=apply_filters)
                coding_select_strvar.trace_add(mode='write', callback=apply_filters)

                filter_section_lbl.grid(row=0, column=0, padx=padx, sticky=sticky)
                us_filter_frame.grid(row=0, column=1, padx=padx, sticky=sticky)
                user_filter_frame.grid(row=0, column=2, padx=padx, sticky=sticky)
                coding_filter_frame.grid(row=0, column=3, padx=padx, sticky=sticky)
                self.task_clear_filters_btn.grid(row=0, column=4, padx=padx, sticky=sticky)
                
                options_frame.pack(pady=(4, 4), anchor='w')
                return filter_frame

            def build_table_panel(parent_frame):
                table_frame = ttk.Frame(parent_frame)
                
                df = self.tasks_df_to_table_format(self.curr_tasks_df)
                rows = len(df)
                cols = len(df.columns)

                self.tasks_table_sheet = tks.Sheet(table_frame, data=df.values.tolist(), header=df.columns.tolist())
                self.tasks_table_sheet.create_dropdown('all', 3, values=[np.True_, np.False_])
                for row, value in enumerate(df['is_coding']):
                    self.tasks_table_sheet.set_cell_data(row, 3, value)

                column_widths = []
                index = 0
                for column in df.columns.tolist():
                    text_width = self.tasks_table_sheet.get_column_text_width(index)
                    if column == 'task_subject':
                        text_width = 500

                    column_widths.append(text_width)
                    index += 1

                self.tasks_table_sheet.enable_bindings()
                self.tasks_table_sheet.extra_bindings("end_edit_cell", task_table_change)  # Call function after edit
                self.tasks_table_sheet.disable_bindings('move_columns', 'move_rows', 'rc_insert_column', 'rc_delete_column')
                self.tasks_table_sheet.readonly_columns(columns=[0, 1, 2, 4, 5, 6])
                self.tasks_table_sheet.pack(fill='both', expand=True, pady=(0, 5))

                self.tasks_table_sheet.set_sheet_data_and_display_dimensions(total_rows=rows, total_columns=cols)
                self.tasks_table_sheet.set_column_widths(column_widths)

                return table_frame

            widget_frame = ttk.Frame(parent)
            hdr_frame = ttk.Frame(widget_frame, borderwidth=2, relief='ridge')
            
            hdr_lbl =  ttk.Label(hdr_frame, text=f'{' ' * 4}Task Data{' ' * 4}', font=('Arial', 13, 'bold'))
            hdr_lbl.pack()
            filter_panel = build_filter_panel(widget_frame)
            table_panel = build_table_panel(widget_frame)

            hdr_frame.pack(fill='x') 
            filter_panel.pack() 
            table_panel.pack(expand = 1, fill ="both") 
            
            return widget_frame

        ## DataFrame build logic
        ##=========================================================================================================================================
        self.content_frame = ttk.Frame(self)
        header_frame = build_header_frame(self.content_frame)

        tabControl = ttk.Notebook(self.content_frame)
        us_data_tab = build_us_tab(tabControl)
        task_data_tab = build_task_tab(tabControl)

        tabControl.add(us_data_tab, text='User Story Data')
        tabControl.add(task_data_tab, text='Task Data')

        header_frame.pack(fill ='x') 
        tabControl.pack(expand = 1, fill ="both") 
        self.content_frame.pack(expand = 1, fill ="both") 


    
    
    def __build_table(self, df) -> tks.Sheet:
        formatted_df = self.__dataframe_to_table_format(df)
        formatted_df.sort_values(by='utc_datetime', inplace=True)
        sheet = tks.Sheet(self, header=list(formatted_df.columns), data=formatted_df.values.tolist())
        sheet.enable_bindings('all')
        # sheet.height_and_width(height=300, width=1000)

        if self.col_widths is None:
            column_widths = []
            index = 0
            for column in formatted_df.columns:
                text_width = sheet.get_column_text_width(index)
                if column == 'message':
                    text_width = 350
                elif column == 'id':
                    text_width = 80
                elif column == 'url':
                    text_width = 210

                column_widths.append(text_width)
                index += 1

            self.col_widths = column_widths

        sheet.set_column_widths(self.col_widths)

        return sheet
    


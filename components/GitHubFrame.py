from backend.DataManager import DataController
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Type
import pandas as pd

from components import DialogWindow

class GitHubFrame(ttk.Frame):
    root = None
    DialogBox = None

    def __init__(self, parent, dc: Type[DataController]):
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

class ConfigFrame(ttk.Frame):
    parent_frame = None

    def __init__(self, parent: Type[GitHubFrame], dc: Type[DataController]):
        super().__init__(parent)
        self.dc = dc
        self.parent_frame = parent

        config_frame = self.__build_config_frame(self)
        config_frame.pack(padx=8, pady=8)

    def __set_field(self, field: Type[tk.Label], val: Type[str]):
        if val is not None and val != '':
            field.config(text=val)

    def __update_username(self, field: Type[tk.Label]):
        try:
            username = self.parent_frame.answer_dialog(msg='Enter the GitHub Username').strip()
            if username is not None and username != '':
                success = self.dc.set_gh_username(username)
                if success:
                    self.__set_field(field, username)
            self.parent_frame.dialog('Invalid Username Entered!')
        except:
            pass

    def __update_token(self, field: Type[tk.Label]):
        try:
            token = self.parent_frame.answer_dialog(msg='Enter the GitHub Token').strip()
            if token is not None and token != '':
                success = self.dc.set_gh_token(token)
                if success:
                    self.__set_field(field, token)
                    return
            self.parent_frame.dialog('Invalid Token Entered!')
        except:
            pass

    def __update_owner(self, field: Type[tk.Label]):
        try:
            owner = self.parent_frame.answer_dialog(msg='Enter the Repo Owner Username').strip()
            if owner is not None and owner != '':
                success = self.dc.set_gh_owner(owner=owner)
                if success:
                    self.__set_field(field, owner)
            self.parent_frame.dialog('Invalid Owner Entered!')
        except:
            pass

    def __update_repo(self, field: Type[tk.Label]):
        try:
            repo = self.parent_frame.answer_dialog(msg='Enter the Repo Name').strip()
            if repo is not None and repo != '':
                success = self.dc.set_gh_repo(repo=repo)
                if success:
                    self.__set_field(field, repo)
            self.parent_frame.dialog('Invalid Repo Entered!')
        except:
            pass

    def __build_config_frame(self, parent) -> ttk.Frame:
        widget_frame = ttk.Frame(parent, borderwidth=2, relief='ridge')

        auth_section_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Auth Config Settings{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        auth_section_lbl.grid(row=0, columnspan=3, pady=(0, 5), sticky='nsew')

        username_lbl = tk.Label(widget_frame, text='Username:', width=9, anchor='e')
        username_readonly = tk.Label(widget_frame, text='Not Set')
        self.__set_field(username_readonly, self.dc.get_gh_username())
        username_btn = tk.Button(widget_frame, text='Edit', command=lambda: self.__update_username(username_readonly), anchor='e')
        username_lbl.grid(row=1, column=0)
        username_readonly.grid(row=1, column=1)
        username_btn.grid(row=1, column=2, padx=(8, 2))

        token_lbl = tk.Label(widget_frame, text='Token:', width=9, anchor='e')
        token_readonly = tk.Label(widget_frame, text='Not Set')
        self.__set_field(token_readonly, self.dc.get_gh_token())
        token_btn = tk.Button(widget_frame, text='Edit', command=lambda: self.__update_token(token_readonly), anchor='e')
        token_lbl.grid(row=2, column=0)
        token_readonly.grid(row=2, column=1)
        token_btn.grid(row=2, column=2, padx=(8, 2))

        repo_section_lbl = tk.Label(widget_frame, text=f'{' ' * 4}Repo Config Settings{' ' * 4}', font=('Arial', 15), borderwidth=2, relief='ridge')
        repo_section_lbl.grid(row=3, columnspan=3, pady=(5, 5), sticky='nsew')

        repo_owner_lbl = tk.Label(widget_frame, text='Repo Owner:', width=10, anchor='e')
        repo_owner_readonly = tk.Label(widget_frame, text='Not Set')
        self.__set_field(repo_owner_readonly, self.dc.get_repo_owner())
        repo_owner_btn = tk.Button(widget_frame, text='Edit', command=lambda: self.__update_owner(repo_owner_readonly), anchor='e')
        repo_owner_lbl.grid(row=4, column=0)
        repo_owner_readonly.grid(row=4, column=1)
        repo_owner_btn.grid(row=4, column=2, padx=(8, 2))

        repo_name_lbl = tk.Label(widget_frame, text='Repo Name:', width=10, anchor='e')
        repo_name_readonly = tk.Label(widget_frame, text='Not Set')
        self.__set_field(repo_name_readonly, self.dc.get_repo_name())
        repo_name_btn = tk.Button(widget_frame, text='Edit', command=lambda: self.__update_repo(repo_name_readonly), anchor='e')
        repo_name_lbl.grid(row=5, column=0)
        repo_name_readonly.grid(row=5, column=1)
        repo_name_btn.grid(row=5, column=2, padx=(8, 2))

        self.username_field = username_readonly
        self.token_field = token_readonly
        self.owner_field = repo_owner_readonly
        self.repo_field = repo_name_readonly

        return widget_frame

class DataFrame(ttk.Frame):
    parent_frame = None

    def __init__(self, parent: Type[GitHubFrame], ac: Type[DataController]):
        super().__init__(parent)
        self.ac = ac
        self.parent_frame = parent
import tksheet as tks
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Type
import pandas as pd
from components import DialogWindow

class TkSheetTable(tk.Frame):

    def __init__(self, parent: Type[tk.Frame], df: Type[pd.DataFrame]):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(0, weight = 1)
        self.sheet = tks.Sheet(self, header=list(df.columns), data=df.values.tolist(), height=800, width=1000)
        self.sheet.enable_bindings('all')
        self.sheet.grid(row=0, column=0, sticky='nsew')

import tkinter as tk
from tkinter import ttk, filedialog, StringVar
import tksheet as tks

from typing import Type
import pandas as pd
import numpy as np
import threading

from components import DialogWindow

from models import DataManager
from components.CustomComponents import CustomDateEntry, CustomOptionMenu

class ReportsFrame(ttk.Frame):
    root = None
    parent_frame = None
    DialogBox = None

    def __init__(self, parent: Type[tk.Tk], dc: Type[DataManager.DataController]):
        super().__init__(parent)
        self.parent_frame = parent
        self.root = parent.master

        Dialog = DialogWindow.Dialog
        Dialog.root = parent
        self.DialogBox = Dialog

        ttk.Label(self, text=f'{' ' * 4}Capstone Report Generation{' ' * 4}', font=('Arial', 20), borderwidth=2, relief='ridge')

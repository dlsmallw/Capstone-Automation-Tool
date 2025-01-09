from models import DataManager
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Type
import pandas as pd

class HomeFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        label = ttk.Label(self, text='Home Tab')
        label.pack()
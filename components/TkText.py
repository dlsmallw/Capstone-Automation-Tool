from enum import Enum
import tkinter as tk
from tkinter import ttk

class TextFormatType(Enum):
    TITLE = 0
    SECTION_HEADER = 1
    SUB_SECTION_HEADER = 2

BULLET_HIERARCHY = {
    0: '•',
    1: '◦',
    2: '▪',
    3: '⁃',
    4: '▸'
}

class FormattedText(ttk.Frame):
    def __init__(self, master = None, width=None, **kwargs):
        super().__init__(master, width=width, **kwargs)
        self.frame_width = self['width']

    def add_title(self, text):
        title_frame = ttk.Frame(self)
        title = ttk.Label(title_frame, text=text, font=('Arial', 25, "bold"))
        title.pack()
        title_frame.pack(fill='x', pady=5)

    def add_section_title(self, text, anchor=None):
        section_frame = ttk.Frame(self)
        section_title = ttk.Label(section_frame, text=text, font=('Arial', 17, "bold"))
        section_title.pack(anchor=anchor)
        section_frame.pack(fill='x', padx=5, pady=5)

    def add_sub_header(self, text, bold=False):
        if bold:
            font = ('Arial', 13, "bold")
        else:
            font = ('Arial', 13)

        sub_header = ttk.Label(self, text=text, font=font)
        sub_header.pack(fill='x', padx=5, pady=5, anchor='w')

    def add_paragraph(self, text, indent=True):
        if indent:
            text = f'        {text}'
        message_element = tk.Message(self, text=text, width=int(self.frame_width * 1.10))
        message_element.pack(anchor='w')

    def make_list(self, text_list, bulleted=True):
        curr_num = 1
        list_frame = ttk.Frame(self)

        for i, text in enumerate(text_list):
            if bulleted:
                point_element = '•'
            else:
                point_element = f'{curr_num}.)'
                curr_num += 1

            font = ('Arial', 13)

            list_element = ttk.Label(list_frame, text=point_element, font=font)
            message_element = tk.Message(list_frame, text=text, width=int(self.frame_width * 0.90))

            list_element.grid(row=i, column=0, padx=(0, 5), sticky='n')
            message_element.grid(row=i, column=1, pady=(0, 1), sticky='nw')

        list_frame.pack(fill='x', padx=(20, 0), pady=(0,5))



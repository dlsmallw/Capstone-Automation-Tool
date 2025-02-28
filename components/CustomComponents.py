from tkcalendar import DateEntry
from tkinter import ttk, font
import datetime
import pandas as pd

class CustomDateEntry(DateEntry):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw, width=8)
        self.delete(0, "end")
        self._date = None

    def get_assigned_column(self):
        return self.col

    def drop_down(self):
        """Display or withdraw the drop-down calendar depending on its current state."""
        if self._calendar.winfo_ismapped():
            self._top_cal.withdraw()
        else:
            self._validate_date()
            # CHANGES: Default to date today when drop down is selected
            date = datetime.datetime.now().strftime("%m/%d/%Y")
            if self.get() != '':
                date = self.parse_date(self.get())

            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()
            if self.winfo_toplevel().attributes('-topmost'):
                self._top_cal.attributes('-topmost', True)
            else:
                self._top_cal.attributes('-topmost', False)
            self._top_cal.geometry('+%i+%i' % (x, y))
            self._top_cal.deiconify()
            self._calendar.focus_set()
            self._calendar.selection_set(date)

    def filter_applied(self):
        return self.date_selected()

    def _validate_date(self):
        if self.get() == '':
            return True
        return super()._validate_date()

    def reset(self):
        self.delete(0, "end")
        self._date = None

    def date_selected(self):
        try:
            if self._date is not None:
                return True
            else:
                return False
        except:
            return False

    def get_date_val(self):
        try:
            date = self.get_date()
        except:
            date = None
        return date
    
class CustomComboBox(ttk.Combobox):
    def __init__(self, master, variable, *values, comp_id, default='None', height=15, width=None, state='readonly'):
        longest_option = max([f'{val}' for val in values], key=len)
        combobox_font = font.nametofont("TkMenuFont")
        text_pix_width = combobox_font.measure(longest_option)
        avg_char_width = combobox_font.measure("0")
        
        self._dropdown_width = int(pow(text_pix_width / avg_char_width, 1.4))

        style_name = f'{comp_id}.TCombobox'
        style = ttk.Style(master)
        style.configure(style_name, postoffset=(0, 0, self._dropdown_width, 0))

        super().__init__(master=master, textvariable=variable, values=values, style=style_name, height=height, width=width, state=state)
        self['width'] = min(15, len(longest_option)) if width is None else width
        
        self.variable = variable
        self.values = values
        self.default = default
        self.reset()

    def filter_applied(self):
        return self.selection_made()

    def equals(self, val):
        this = f'{self.variable.get()}'
        that = f'{val}'

        print(this, that)
        return f'{self.variable.get()}' == f'{val}'
        

    def reset(self):
        self.variable.set(self.default)

    def selection_made(self):
        if self.variable.get() is not None and self.variable.get() != self.default:
            return True
        return False

    def get_selection(self):
        return self.variable.get()

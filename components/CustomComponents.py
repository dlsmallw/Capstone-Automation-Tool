from tkcalendar import DateEntry
from tkinter import ttk
import datetime

class CustomDateEntry(DateEntry):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.delete(0, "end")
        self._date = None

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


    def _validate_date(self):
        if self.get() == '':
            return True # Modified from Roman's Answer
        
        return super()._validate_date()

    def clear_date(self):
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


class CustomOptionMenu(ttk.OptionMenu):
    def __init__(self, master, variable, default = None, *values, style = "", direction = "below", command = None):
        super().__init__(master, variable, default, *values, style=style, direction=direction, command=command)
        self.variable = variable
        self.values = values

    def reset(self):
        self.variable.set('')

    def selection_made(self):
        if self.variable.get() != '':
            return True
        return False

    def get_selection(self):
        return self.variable.get()

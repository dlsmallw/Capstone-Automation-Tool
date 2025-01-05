import tkinter as tk

class Dialog(tk.Frame):
    root = None
    top = None
    result = None

    def __init__(self, msg, entry=False):
        self.top = tk.Toplevel(Dialog.root)
        super().__init__(self.top, borderwidth=4, relief='ridge', width=500, height=500)
        self.pack(fill='both', expand=True)

        label = tk.Label(self, text=f'{' ' * 5}{msg}{' ' * 5}', font=('Arial', 15))
        label.pack(padx=4, pady=4)

        if entry:
            self.entry = tk.Entry(self)
            self.entry.pack(pady=4)

            b_submit = tk.Button(self, text='Submit', font=('Arial', 12))
            b_submit['command'] = lambda: self.submit_pressed()
            b_submit.pack()
        else:
            b_cancel = tk.Button(self, text='OK', font=('Arial', 12))
            b_cancel['command'] = self.top.destroy
            b_cancel.pack(padx=4, pady=4)

    def submit_pressed(self):
        self.result = self.entry.get()
        self.top.destroy()
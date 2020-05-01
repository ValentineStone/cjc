#!python3

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import platform
import os
import json

class Symbol:
    pass

COLOR_BACKGROUND = '#1e1e1e'
COLOR_FOREGROUND = '#d4d4d4'
COLOR_MENU_BACKGROUND = '#3c3c3c'
COLOR_MENU_FOREGROUND = '#cccccc'
COLOR_SEPARATOR = '#555555'
COLOR_BLUE = '#569cd6'
COLOR_LIGHTBLUE = '#9cdcfe'
COLOR_PINK = '#c586c0'
COLOR_GREEN = '#4ec9b0'
COLOR_LIGHTGREEN = '#b5cea8'
COLOR_ORANGE = '#ce9178'
COLOR_YELLOW = '#d0dcaa'
COLOR_HIGHLIGHT = '#264f78'

CONSOLE_FONT = 'consolas' if platform.system() == 'Windows' else 'TkFixedFont'


NAMED_ARRAY_KEY = '__objectIsNamedArray'
IMPOSSIBLE_NAMED_ARRAY_KEY = Symbol()
PROTOTYPE_PRIMITIVE_VALUE = None

Undefined = Symbol()

def tokenize(line):
    token = ''
    quoted = False
    prev = 0
    for i in range(len(line)):
        if line[i] == '"' and not line[prev] == '\\':
            quoted = not quoted
        if line[i] == ';' and not quoted:
            yield token
            token = ''
            continue
        else:
            token += line[i]
        prev = i
    yield token

# from tabulate import tabulate
# def print_table(table, row, col, color='\u001b[34m'):
#     print('\033c')
#     if row < table.height and col < table.width:
#         highlited = table.get(row, col)
#         pretty = highlited if highlited != '' else '""'
#         table.set(row, col, f'{color}{pretty}\u001b[37m')
#         print(tabulate(table.rows, tablefmt='fancy_grid'))
#         table.set(row, col, highlited)
#         return highlited
#     else:
#         print('\u001b[31m' + tabulate(table.rows, tablefmt='fancy_grid') + '\u001b[37m')

class Cursor:
    def __init__(self, row = 0, col = 0, rowend = float('inf'), colend = float('inf')):
        self.row = row
        self.col = col
        self.rowend = rowend
        self.colend = colend
    def set(self, row = None, col = None, rowend = None, colend = None):
        if row != None:
            self.row = row
        if col != None:
            self.col = col
        if rowend != None:
            self.rowend = rowend
        if colend != None:
            self.colend = colend
        return self
    def copy(self, row = None, col = None, rowend = None, colend = None):
        clone = Cursor()
        clone.row = self.row
        clone.col = self.col
        clone.rowend = self.rowend
        clone.colend = self.colend
        clone.set(row, col, rowend, colend)
        return clone

class Table:
    def __init__(self):
        self.rows = []
        self.width = 0
        self.height = 0
        self.headend = 0
    def __iter__(self):
        return iter(self.rows)
    def get(self, row, col):
        if col < self.width and row < self.height:
            return self.rows[row][col]
        else:
            return Undefined
    def set(self, row, col, value=Undefined):
        if col >= self.width:
            count = col - self.width + 1
            for cols in self:
                cols += [Undefined] * count
            self.width = col + 1
        if row >= self.height:
            count = row - self.height + 1
            for i in range(count):
                self.rows.append([Undefined] * self.width)
            self.height = row + 1
        self.rows[row][col] = value
    def trim(self):
        max_w = 0
        max_h = 0
        for row, cols in enumerate(self.rows):
            has_items = False
            for col, val in enumerate(cols):
                if val != Undefined:
                    has_items = True
                    if col > max_w:
                        max_w = col
            if has_items:
                if row > max_h:
                    max_h = row
        del self.rows[max_h + 1:]
        for cols in self.rows:
            del cols[max_w + 1:]
    def to_python_string(self):
        return '\n'.join(map(str, self.rows))
    def to_csv_string(self):
        return '\n'.join(map(self.to_csv_row, self.rows))
    def to_header_csv_string(self):
        return '\n'.join(map(self.to_csv_row, self.rows[:self.headend]))
    def to_csv_row(self, cols):
        return ';'.join(map(self.to_csv_val, cols))
    def to_csv_val(self, val):
        return '' if val == Undefined else json.dumps(val, ensure_ascii=False)
    def to_python_val(self, val):
        return Undefined if val == '' else json.loads(val)
    def load_from_file(self, filname):
        with open(filname, 'r', encoding='utf8') as csvfile:
            self.height = 0
            self.width = 0
            self.headend = 0
            self.rows = []
            lines = csvfile.read().split('\n')
            for index, line in enumerate(lines):
                self.height += 1
                row = list(map(self.to_python_val, tokenize(line)))
                self.rows.append(row)
                if len(self.rows[index]) > self.width:
                    self.width = len(self.rows[index])
                if row.count(Undefined) == len(row) and self.headend == 0:
                    self.headend = index
            for index, row in enumerate(self.rows):
                if len(row) < self.width:
                    row += [Undefined] * (self.width - len(row))
        self.trim()
        return self

def named_array_as_iter(named_array):
    named_array_list = named_array.copy()
    del named_array_list[NAMED_ARRAY_KEY]
    return named_array_list.values()
def named_array_as_list(named_array):
    return list(named_array_as_iter(named_array))

def is_not_empty_value(value):
    if isinstance(value, list):
        for item in value:
            if is_not_empty_value(item):
                return True
        return False
    elif isinstance(value, dict):
        for key in value:
            if key != NAMED_ARRAY_KEY and is_not_empty_value(value[key]):
                return True
        return False
    else:
        return value != Undefined

class Element:
    def __init__(self):
        self.root = None
        self.prototype = None

    def load_from_file(self, filname):
        with open(filname, 'r', encoding='utf8') as json_file:
            json_string = json_file.read()
        self.root = json.loads(json_string)
        self.prototype = self.extract_prototype(self.root)
        self.root = self.splice_from_prototype(self.root, self.prototype)
        return self

    def extract_prototype(self, json_element, prototype=None):
        if prototype == None:
            if isinstance(json_element, dict):
                return self.extract_prototype(json_element, {})
            elif isinstance(json_element, list):
                return self.extract_prototype(json_element, [None])
            else:
                return PROTOTYPE_PRIMITIVE_VALUE
        if isinstance(json_element, dict):
            if NAMED_ARRAY_KEY in json_element:
                for key in json_element:
                    if key != NAMED_ARRAY_KEY:
                        prototype[NAMED_ARRAY_KEY] = self.extract_prototype(json_element[key], prototype.get(NAMED_ARRAY_KEY))
            else:
                for key, value in json_element.items():
                    prototype[key] = self.extract_prototype(value, prototype.get(key))
        elif isinstance(json_element, list):
            for value in json_element:
                prototype[0] = self.extract_prototype(value, prototype[0])
        return prototype

    def splice_from_prototype(self, root, prototype):
        if isinstance(prototype, dict):
            if not isinstance(root, dict):
                root = {}
            if NAMED_ARRAY_KEY in prototype:
                root[NAMED_ARRAY_KEY] = True
                if len(root) == 1:
                    root[Undefined] = Undefined
                for key in root:
                    if key != NAMED_ARRAY_KEY:
                        root[key] = self.splice_from_prototype(root[key], prototype[NAMED_ARRAY_KEY])
            else:
                for key in prototype:
                    spliced = self.splice_from_prototype(root.get(key, Undefined), prototype[key])
                    if key not in root:
                        root[key] = spliced
        elif isinstance(prototype, list):
            if not isinstance(root, list):
                root = [Undefined]
            for index, value in enumerate(root):
                root[index] = self.splice_from_prototype(root[index], prototype[0])
        return root
    def to_json_string(self):
        return json.dumps(self.root, ensure_ascii=False, indent=2)


def prototype_to_table(prototype, table, cur=None):
    if cur==None: cur=Cursor()
    if isinstance(prototype, dict):
        if NAMED_ARRAY_KEY in prototype:
            prototype_to_table([prototype[NAMED_ARRAY_KEY]], table, cur)
        else:
            for key, value in prototype.items():
                table.set(cur.row, cur.col, value=key)
                cur.row += 1
                prototype_to_table(value, table, cur)
                cur.row -= 1
    elif isinstance(prototype, list):
        table.set(cur.row, cur.col)
        cur.col += 1
        prototype_to_table(prototype[0], table, cur)
    else:
        table.set(cur.row, cur.col, value=Undefined)
        cur.col += 1

def element_root_to_table(root, prototype, table, cur):
    indx_row = cur.row
    if isinstance(prototype, dict):
        if NAMED_ARRAY_KEY in prototype:
            total_rowheight = 0
            indx_col = cur.col
            for index, (key, value) in enumerate(root.items(), 1):
                if key != NAMED_ARRAY_KEY:
                    if is_not_empty_value(value):
                        table.set(cur.row, cur.col, value=key)
                    cur.col += 1
                    rowheight = element_root_to_table(value, prototype[NAMED_ARRAY_KEY], table, cur)
                    total_rowheight += rowheight
                    if index < len(root):
                        cur.col = indx_col
                        cur.row += rowheight
                    else:
                        cur.row = indx_row
            return total_rowheight
        else:
            max_rowheight = 0
            for index, (key, value) in enumerate(prototype.items(), 1):
                if key != NAMED_ARRAY_KEY:
                    rowheight = element_root_to_table(root[key], value, table, cur)
                    if rowheight > max_rowheight:
                        max_rowheight = rowheight
                    if index < len(prototype):
                        cur.row = indx_row
                        cur.col += 1
            return max_rowheight
    elif isinstance(prototype, list):
        total_rowheight = 0
        indx_col = cur.col
        for index, value in enumerate(root, 1):
            if is_not_empty_value(value):
                table.set(cur.row, cur.col, value=index)
            cur.col += 1
            rowheight = element_root_to_table(value, prototype[0], table, cur)
            total_rowheight += rowheight
            if index < len(root):
                cur.col = indx_col
                cur.row += rowheight
            else:
                cur.row = indx_row
        return total_rowheight
    else:
        table.set(cur.row, cur.col, value=root)
        return 1


def element_to_table(element):
    table = Table()
    prototype_to_table(element.prototype, table)
    table.headend = table.height - 1
    element_root_to_table(element.root, element.prototype, table, Cursor(table.height, 0))
    return table


def prototype_from_table(table, cur):
    cell = table.get(cur.row, cur.col)
    if cell == Undefined:
        if cur.row < table.headend and cur.col + 1 < cur.colend:
            current_row = cur.row
            current_col = cur.col
            is_named_array = False
            while current_row < table.height:
                current_row += 1
                current_cell = table.get(current_row, current_col)
                if current_cell != Undefined and not isinstance(current_cell, int):
                    is_named_array = True
                    break
            cur.col += 1
            if is_named_array:
                return { NAMED_ARRAY_KEY: prototype_from_table(table, cur) }
            else:
                return [prototype_from_table(table, cur)]
        else:
            cur.col += 1
            return PROTOTYPE_PRIMITIVE_VALUE
    else:
        prototype = {}
        colend_current = cur.col
        while True:
            colend_current += 1
            if table.get(cur.row, colend_current) != Undefined or colend_current >= cur.colend:
                cur.row += 1
                prototype[cell] = prototype_from_table(table, cur.copy(colend=colend_current))
                cur.row -= 1
                cur.col = colend_current
                cell = table.get(cur.row, cur.col)
            if colend_current >= cur.colend:
                break
        return prototype


def key_value_from_table(table, prototype, cur):
    if table.get(cur.row, cur.col) == Undefined:
        cur.col += 1
        yield Undefined, element_root_from_table(table, prototype, cur)
        return
    initial_rowend = cur.rowend
    initial_col = cur.col
    initial_row = cur.row
    cur.rowend = cur.row + 1
    while cur.rowend <= initial_rowend:
        while table.get(cur.rowend, cur.col) == Undefined and cur.rowend < initial_rowend:
            cur.rowend += 1
        key = table.get(cur.row, cur.col)
        cur.col += 1
        value = element_root_from_table(table, prototype, cur)
        if cur.rowend < initial_rowend:
            cur.row = cur.rowend
            cur.rowend = cur.row + 1
            cur.col = initial_col
            yield key, value
        else:
            cur.row = initial_row
            yield key, value
            break

def element_root_from_table(table, prototype, cur):
    root = None
    if isinstance(prototype, list):
        root = []
        for key, value in key_value_from_table(table, prototype[0], cur):
            if (is_not_empty_value(value)): root.append(value)
    elif isinstance(prototype, dict):
        root = {}
        if NAMED_ARRAY_KEY in prototype:
            root[NAMED_ARRAY_KEY] = True
            for key, value in key_value_from_table(table, prototype[NAMED_ARRAY_KEY], cur):
                if (is_not_empty_value(value)): root[key] = value
        else:
            for key in prototype:
                value = element_root_from_table(table, prototype[key], cur)
                if (is_not_empty_value(value)): root[key] = value
    else:
        root = table.get(cur.row, cur.col)
        cur.col += 1
    return root

def element_from_table(table):
    element = Element()
    element.prototype = prototype_from_table(
        table,
        Cursor(
            colend=table.width,
            rowend=table.height))
    element.root = element_root_from_table(
        table,
        element.prototype,
        Cursor(
            row = table.headend + 1,
            col = 0,
            rowend = table.height,
            colend = table.width))
    return element


def save_file(filename, string, ext='txt', override_file=False):
    index = 0
    filename_noext = os.path.splitext(filename)[0]
    new_filename = filename_noext + '.' + ext
    while os.path.isfile(new_filename) and not override_file:
        index += 1
        new_filename = filename_noext + str(index) + '.' + ext
    with open(new_filename, 'w', encoding='utf8') as file:
        file.write(string)
    return new_filename
    
class Application:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('CJConverter')

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)
        #self.window.geometry('400x200')
        #self.window.resizable(0, 1)
        self.window.geometry('1000x500')

        self.menu_bar = tk.Frame(self.window, pady=5, padx=5)
        self.menu_bar.grid(row=0, column=0, sticky='nsew')

        self.open_json_button = ttk.Button(
            self.menu_bar,
            text='Open-JSON',
            command=self.open_json_button_onclick)
        self.open_json_button.pack(side=tk.LEFT)

        self.open_csv_button = ttk.Button(
            self.menu_bar,
            text='Open-CSV',
            command=self.open_csv_button_onclick)
        self.open_csv_button.pack(side=tk.LEFT)

        self.named_arrays_key_entry_value = tk.StringVar()
        self.named_arrays_key_entry_value.set(NAMED_ARRAY_KEY)
        def on_write_named_arrays_key_entry_value(*_):
            global NAMED_ARRAY_KEY
            NAMED_ARRAY_KEY = self.named_arrays_key_entry_value.get()
        self.named_arrays_key_entry_value.trace_add(
            'write',
            on_write_named_arrays_key_entry_value)
        self.named_arrays_key_entry = ttk.Entry(
            self.menu_bar,
            textvariable=self.named_arrays_key_entry_value)
        self.named_arrays_key_entry.pack(side=tk.RIGHT)

        self.named_arrays_checkbox_value = tk.IntVar()
        self.named_arrays_checkbox_value.set(1)
        def on_write_named_arrays_checkbox_value(*_):
            global NAMED_ARRAY_KEY
            if self.named_arrays_checkbox_value.get():
                self.named_arrays_key_entry.configure(state='normal')
                NAMED_ARRAY_KEY = self.named_arrays_key_entry_value.get()
            else:
                self.named_arrays_key_entry.configure(state='disabled')
                NAMED_ARRAY_KEY = IMPOSSIBLE_NAMED_ARRAY_KEY
        self.named_arrays_checkbox_value.trace_add(
            'write',
            on_write_named_arrays_checkbox_value)
        self.named_arrays_checkbox = ttk.Checkbutton(
            self.menu_bar,
            text='Named arrays',
            variable=self.named_arrays_checkbox_value)
        self.named_arrays_checkbox.pack(side=tk.RIGHT)

        self.override_files_checkbox_value = tk.IntVar()
        self.override_files_checkbox_value.set(0)
        self.override_files_checkbox = ttk.Checkbutton(
            self.menu_bar,
            text='Override file',
            variable=self.override_files_checkbox_value)
        self.override_files_checkbox.pack(side=tk.RIGHT)

        self.text = tk.Text(
            self.window,
            state='disabled',
            bg=COLOR_BACKGROUND,
            fg=COLOR_FOREGROUND,
            font=CONSOLE_FONT,
            borderwidth=0,
            padx=10,
            pady=10,
            wrap='word')
        self.text.grid(row=1, column=0, sticky='nsew')

        self.scrollb = ttk.Scrollbar(
            self.window,
            command=self.text.yview)
        self.scrollb.grid(row=0, column=1, rowspan=2, sticky='nsew')
        self.text['yscrollcommand'] = self.scrollb.set

        self.__newline_buffer = ''
        self.__styled_log_index = 0
        self.user_story_start()

    def log(self, text='', color=COLOR_FOREGROUND, end='\n'):
        was_at_end = self.scrollb.get()[1] == 1
        self.___log_nonstyled(self.__newline_buffer)

        if (color == COLOR_FOREGROUND):
            self.___log_nonstyled(text)
        else:
            self.___log_styled(text, color)
            

        self.__newline_buffer = end
        if was_at_end:
            self.text.see('end')

    def ___log_styled(self, text, color):
        tagname = str(self.__styled_log_index)
        self.text.configure(state='normal')
        self.text.insert('end', str(text), tagname)
        self.text.configure(state='disabled')
        self.text.tag_config(tagname, foreground=color)
        self.__styled_log_index += 1

    def ___log_nonstyled(self, text):
        self.text.configure(state='normal')
        self.text.insert('end', str(text))
        self.text.configure(state='disabled')

    def open_json_files(self):
        return filedialog.askopenfilenames(
            title = 'Select file',
            filetypes = (
                ('JavaScript Object Notation', '*.json'),
                ('All files', '*')))

    def open_csv_files(self):
        return filedialog.askopenfilenames(
            title = 'Select file',
            filetypes = (
                ('Comma Separated Values', '*.csv'),
                ('All files', '*')))

    def open_csv_button_onclick(self):
        filenames = self.open_csv_files()
        for filename in filenames:
            self.csv_to_json(filename)

    def open_json_button_onclick(self):
        filenames = self.open_json_files()
        for filename in filenames:
            self.json_to_csv(filename)

    def user_story_start(self):
        self.log('Welcome to CJConverter!', color=COLOR_YELLOW)
        self.log('Select ', end='')
        self.log('JSON', end='', color=COLOR_LIGHTGREEN)
        self.log(' or ', end='')
        self.log('CVS', end='', color=COLOR_LIGHTBLUE)
        self.log(' files to convert')

    def csv_to_json(self, csv_filename):
        use_named_arrays = self.named_arrays_checkbox_value.get()
        override_file = self.override_files_checkbox_value.get()
        
        self.log('Open', end=' ', color=COLOR_PINK)
        self.log(csv_filename, color=COLOR_BLUE)

        table = Table().load_from_file(csv_filename)
        element = element_from_table(table)

        self.log('Prototype:', color=COLOR_PINK)
        self.log(json.dumps(element.prototype, ensure_ascii=False, indent=2))
        self.log('Header:', color=COLOR_PINK)
        self.log(table.to_header_csv_string())
        
        savename = save_file(csv_filename, element.to_json_string(), ext='json', override_file=override_file)
        self.log('Saved as', end=' ', color=COLOR_PINK)
        self.log(savename, color=COLOR_BLUE)

    def json_to_csv(self, json_filename):
        use_named_arrays = self.named_arrays_checkbox_value.get()
        override_file = self.override_files_checkbox_value.get()
        
        self.log('Open', end=' ', color=COLOR_PINK)
        self.log(json_filename, color=COLOR_BLUE)

        element = Element().load_from_file(json_filename)
        table = element_to_table(element)

        self.log('Prototype:', color=COLOR_PINK)
        self.log(json.dumps(element.prototype, ensure_ascii=False, indent=2))
        self.log('Header:', color=COLOR_PINK)
        self.log(table.to_header_csv_string())

        savename = save_file(json_filename, table.to_csv_string(), ext='csv', override_file=override_file)
        self.log('Saved as', end=' ', color=COLOR_PINK)
        self.log(savename, color=COLOR_BLUE)

if __name__ == '__main__':
    app = Application()
    app.window.mainloop()
# TODO:
#     - handle relative frames correctly (need newer gdb)
#     - output formatter abstraction

def get_cols(fallback=-1):
    import subprocess
    p = subprocess.Popen(["tput", "cols"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    try:
        cols = int(p.communicate()[0])
        if (p.returncode != 0):
            raise ValueError
    except ValueError:
        cols = fallback

    return cols

def trunc(string, max, fromEnd=False):
    if len(string) <= max:
        return string

    ellipsis = u"\u2026"
    newLen = int(max - len(ellipsis))

    if (fromEnd):
        return ellipsis + string[-newLen:]
    else:
        return string[:newLen] + ellipsis

# Cheesy ansi colors.
def red(s):    return "\033[0;31m" + s + "\033[m"
def yellow(s): return "\033[0;33m" + s + "\033[m"
def blue(s):   return "\033[0;36m" + s + "\033[m"

def print_div():
    cols = get_cols(fallback=80)
    print blue("-" * cols)

class Table():
    def __init__(self, columns):
        self.columns = columns
        self.divider = "  "
        self.widths = self.computeWidths()

    def formatHeaders(self):
        names = [col.name for col in self.columns]
        return self.formatLine(names,
                               transforms=[None for i in range(len(names))])

    def formatLine(self, strings, transforms=[]):
        output = []
        if (len(self.columns) != len(strings)):
            raise RuntimeError, "expected %d, got %d" % (len(self.columns),
                                                          len(strings))

        if (not transforms):
            transforms = [col.transform for col in self.columns]

        for i in range(len(self.columns)):
            col = self.columns[i]

            output.append(col.format(strings[i], self.widths[i], transforms[i]))

        return " " + self.divider.join(output)

    def computeWidths(self):
        import math

        result = []
        relativeWidths = [col.width for col in self.columns
                          if not col.absoluteWidth]
        absoluteWidths = [col.width for col in self.columns
                          if col.absoluteWidth]

        # subtract one for the left-hand margin
        available = get_cols(fallback=1000) - 1

        # subtract space for the column separators
        available -= len(self.divider) * (len(self.columns) - 1)

        # subtract absolute column widths
        available -= sum(absoluteWidths)

        total = sum(relativeWidths)
        for col in self.columns:
            if (col.absoluteWidth):
                w = col.width
            else:
                w = int(math.floor(float(col.width)/total * available))
            result.append(w)

        return result

class Column():
    def __init__(self, name, width,
                 absoluteWidth=False, transform=None,
                 rightAlign=False, fromEnd=False):
        self.name = name
        self.absoluteWidth = absoluteWidth
        self.width = width
        self.transform = transform
        self.rightAlign = rightAlign
        self.fromEnd = fromEnd

    def format(self, string, width, transform):
        length = len(string)

        if (length > width):
            string = trunc(string, width, self.fromEnd)
        elif (length < width):
            pad = (width - length)
            if (self.rightAlign):
                string = " " * pad + string
            else:
                string = string + " " * pad

        # Apply the transform func last.
        if (transform):
            string = transform(string)

        return string

__sourced = False

def pyframe(frame):
    oldFrame = gdb.selected_frame()

    # XXX gross hack -- need to declare another way or reimplement
    global __sourced
    if (not __sourced):
        gdb.execute("source ~jmk/.gdb/sbt.gdb")
        __sourced = True

    if (frame.name() in ("PyEval_EvalFrameEx",
                         "PyEval_EvalCodeEx")):
        try:
            frame.select()
            return gdb.execute("__pyframe", to_string=True).rstrip()
        except Exception as e:
            print "(Couldn't get python frame: %s)" % str(e)
            pass
        finally:
            oldFrame.select()

def sbt():
    import os

    auto_load_symbols(verbose=True)

    # Configure table.
    table = Table([
        Column("frm", 3, absoluteWidth=True, transform=yellow, rightAlign=True),
        Column("function", 2),
        Column("lib", 1),
        Column("source", 2, fromEnd=True),
        Column("", 3, absoluteWidth=True, transform=yellow)
    ])

    print_div()
    print table.formatHeaders()
    print_div()

    i = 0
    for frame in get_all_frames():
        num = str(i)

        # Determine function name.
        name = frame.name()
        if (not name):
            name = "<unknown>"

        # Get symbol and line info.
        sal = frame.find_sal()

        # Determine library name.
        lib = gdb.solib_address(sal.pc)
        if (lib):
            lib = os.path.basename(lib)
        else:
            lib = ""

        # Determine source/line.
        if (sal.symtab):
            source = "%s:%d" % (sal.symtab.filename, sal.line)
        else:
            source = ""

        print table.formatLine([num, name, lib, source, num]).encode("utf8")

        # XXX python
        pyinfo = pyframe(frame)
        if (pyinfo):
            print " " * 6 + blue(pyinfo)

        i += 1

def test():
    frame = gdb.selected_frame()
    try:
        value = gdb.parse_and_eval("co")

    except RuntimeError:
        print "(not a python frame)"

# XXX: hack -- see below.
__loaded = set()

def get_frames():
    # XXX: gdb 7.2-23 doesn't have gdb.newest_frame(), so we can only start at
    # the selected frame. note that if the selected frame is not the newest,
    # the frame numbers will be wrong. Ugh.
    frame = gdb.selected_frame()

    while (frame):
        yield frame
        frame = frame.older()

def load_solibs(frames):
    libs = set()
    for f in frames:
        sal = f.find_sal()
        lib = gdb.solib_address(sal.pc)
        if (lib):
            libs.add(lib)

    for lib in libs:
        # XXX: hack. why can't gdb just tell us whether we've loaded this yet
        # or not? maybe newever versions have better API ...
        global __loaded

        if (not lib in __loaded):
            print "Loading symbols: " + lib
            gdb.execute("sharedlibrary " + lib)
            __loaded.add(lib)

    return libs

def auto_load_solibs():
    count = -1
    newCount = 0

    # XXX: Okay, this is pretty awful. We often can't get a full stack trace
    # without loading symbols, but we don't know which symbols we need to load
    # until we crawl the stack. So, repeatedly crawl the stack and load
    # additional symbols we encounter until we converge on a result.
    iterations = 0
    maxIterations = 25

    while (count != newCount and iterations < maxIterations):
        count = newCount
        frames = list(get_frames())
        newCount = len(frames)
        load_solibs(frames)

        iterations += 1

    if (iterations == maxIterations):
        print ("ERROR: Couldn't load all symbols after %d iterations"
               % iterations)


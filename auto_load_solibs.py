# Tracks set the of libraries whose symbols have been loaded. There doesn't
# seem to be a way to query gdb for this information, so we keep track of it
# ourselves.
__loadedLibs = set()

# If this module isn't imported directly by gdb (i.e., imported from another
# script), the gdb global object won't be defined. The parent script should
# set the gdb object using set_gdb_global().
if (not "gdb" in globals()):
    global gdb
    gdb = None

def set_gdb_global(obj):
    global gdb
    gdb = obj

# Convenience function for logging messages to GDB's output stream.
#
# XXX: gdb 7.2-23 doesn't support gdb.STDERR and friends; otherwise, this
#      could be a convenience place to redirect output accordingly.
def log(msg):
    gdb.write(msg)
    gdb.write("\n")

# A generator that iterates over all (accessible) stack frames.
def get_all_frames():
    # XXX: gdb 7.2-23 doesn't have gdb.newest_frame(), so we can only start at
    #      the selected frame. We have no way of knowing whether this is the
    #      newest frame, but in practice, it should be.
    frame = gdb.selected_frame()

    while (frame):
        yield frame
        frame = frame.older()

# Attempts to load all symbols for the given frames. Returns true if
# additional symbols have been loaded.
def load_symbols(frames, verbose):
    oldLoadedCount = len(__loadedLibs)

    # Gather library names from the given stack frames.
    libs = set()
    for f in frames:
        # Find the frame's associated symbol table and line object, so we can
        # find the associated shared library filename.
        sal = f.find_sal()
        lib = gdb.solib_address(sal.pc)
        if (lib):
            libs.add(lib)

    # Load symbols for shared libraries.
    for lib in libs:
        if (not lib in __loadedLibs):
            if (verbose):
                log("Loading symbols: " + lib)

            gdb.execute("sharedlibrary " + lib)
            __loadedLibs.add(lib)

    return oldLoadedCount != len(__loadedLibs)

# Auto-load all shared library symbols for the current thread's stack.
def auto_load_symbols(verbose):
    # XXX: This is fairly hacky. We typically can't get a full stack trace
    #      without loading symbols, but we don't know which symbols we need to
    #      load until we walk the stack.
    #
    #      So, we repeatedly walk the stack, loading additional symbols we
    #      encounter at each iteration. We stop when there are no new stack
    #      frames to inspect and no additional libraries have been loaded.
    #
    #      We also cap the maximum number of iterations to avoid infinite
    #      recursion.
    oldCount = None
    newCount = 0
    newLoaded = True

    iterations = 0
    maxIterations = 25

    while ((oldCount != newCount or newLoaded) and iterations < maxIterations):
        oldCount = newCount

        frames = list(get_all_frames())
        newLoaded = load_symbols(frames, verbose)

        newCount = len(frames)
        iterations += 1

    if (iterations == maxIterations):
        log("ERROR: Couldn't load all symbols after %d iterations"
            % iterations)

# Auto-load symbols for all threads.
def auto_load_all(verbose=True):
    for i in gdb.inferiors():
        for t in i.threads():
            t.switch()
            auto_load_symbols(verbose)

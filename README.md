### GDB Utilities ###

Recent versions of GDB can be built with python support, which is required by these scripts. They can be `source`d in your `.gdbinit` like any other file:

    source /path/to/script.py

For more information, check out the [official documentation][1] for python scripting support in GDB.

[1]: http://sourceware.org/gdb/current/onlinedocs/gdb/Python.html


#### Loading Debug Symbols On Demand ###

For very large applications (with debug binaries/libraries that are, say, hundreds of MBs in size), gdb can spend a lot of time loading debug symbols for every loaded library.

`auto_load_solibs.py` is a script that loads only the libraries that are referenced by the target's current call stack. It's most useful when combined with the following entry in your `.gdbinit`:

    set auto-solib-add off

This will ensure that gdb never loads symbols for libraries by default. That means attaching to a massive application is instantaneous, but stack traces will be useless until you load the relevant shared libraries.

That's where you can use this (or alias this to your liking):

    python auto_load_solibs()

If you need to manually load symbols (to set a breakpoint, for example), you can use the built-in `sharedlibrary` command (`sha` for short) to load symbols for a particular library or set of libraries:

    sharedlibrary libfoo.so


#### Smart Backtraces ####

`sbt.py` provides a more intelligent alternative to the built-in `backtrace` command, which:

* Displays data in a tabular format, to clearly separate stack frame numbers, frame label/function names, source library paths, and file/line number information.
* Respects the width of the terminal, intelligently truncating content to fit. (A big help when dealing with libraries like boost that generate incredibly long symbol names.)
* Displays inline python frame information (file/line number) for relevant frames.
* Utilizes ANSI colors for clarity.


### Caveats ###

These scripts are quick hacks. They get the job done for me, but they haven't been extensively tested or carefully engineered.

I don't use bleeding-edge versions of gdb, so some of these scripts are severely limited by shortcomings in gdb's python API. Hopefully, this situation will improve over time.

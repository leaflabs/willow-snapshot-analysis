# willow-snapshot-analysis

This repository contains snapshot analysis programs for WillowGUI. To add an
analysis program, create a new folder in the top level and put inside of it an
executable named 'main'. This executable can be anything - a MATLAB script, a 
Python GUI, a compiled program, etc. The only requirement is that is take as
its first command-line argument the absolute filename of the snapshot it is to
analyze.

To make this work with WillowGUI, set the "Snapshot Analysis Directory"
parameter in the Config Wizard, or else in the Settings menu during runtime.
Then, any subdirectory containing a 'main' executable will appear as an option
for custom analysis in the Snapshot Dialog. WillowGUI will launch the
executable as a subprocess, with its working directory set to that of the
executable - so metadata (e.g. probe mappings) or library files can be kept in
the same folder alongside the exectuable. stdout and stderr will be piped to
'oFile' and 'eFile' in the working directory, so avoid using these filenames
for metadata, as they will get overwritten upon execution.

Place code or data that you'd like to re-use across different analysis programs
in the lib/ directory. Then programs can access this code or data using
relative pathnames, e.g. in Python:

    sys.path.append('../lib/py')

Stay D.R.Y.; Don't Repeat Yourself!

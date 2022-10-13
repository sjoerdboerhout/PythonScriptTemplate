#!/usr/bin/python3

import sys
import os
import time
import logging
import colorlog
import subprocess
from datetime import datetime
from optparse import OptionParser

# Init global variables
# ----------------------------------------------------------------------------------------------------------------------

# Save current working directory as root for all relative paths
CWD = os.getcwd()

# Global logger
LOGGER = None
LOGGER_DEFAULT_LEVEL = "info"
LOGGER_APP_NAME = "AppName"
LOGGER_DIR = "log"
LOGGER_NAME = "AppLogger"

# Progress bar
LINE_WIDTH = 100

# Yes/No question
YES = True
NO = False

# Function definitions
# ----------------------------------------------------------------------------------------------------------------------

# Parse command line agument to options
def parse_options():

    parser = OptionParser()

    parser.add_option("-l", "--loglevel", 
                        dest="loglevel", 
                        default=LOGGER_DEFAULT_LEVEL,
                        help=f"Required loglevel, default={LOGGER_DEFAULT_LEVEL}"
                     )

    parser.add_option("-s", "--source", 
                        dest="source",
                        default="source",
                        help="Source directory, default=source"
                     )

    parser.add_option("-t", "--target", 
                        dest="target",
                        default="target",
                        help="Target directory, default=target"
                     )

    parser.add_option("-u", "--user", 
                        dest="username",
                        default=f"{os.getenv('USERNAME')}",
                        help="User who runs this script"
                     )

    parser.add_option("-v", "--verbose",
                        action="store_true", 
                        dest="verbose", 
                        default=False,
                        help="Enable verbose logging"
                     )

    (options, args) = parser.parse_args()

    # Convert to absolute path if a relative path was given
    options.source      = os.path.abspath(options.source)
    options.target      = os.path.abspath(options.target)

    return options


def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Adds a new logging level to the `logging` module and the currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.trace('Trace level message')
    """

    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))

    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))

    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


# Create and initialize the logger of this script
def create_logger(log_dir=LOGGER_DIR, log_file=None, logger_name=LOGGER_NAME, log_level=LOGGER_DEFAULT_LEVEL):
    """Log plain text to file and to terminal with colors"""

    if log_level.upper() not in list(logging._nameToLevel.keys()):
        raise AttributeError('{} is not a valid log level name'.format(log_level))

    if log_file == None:
        curr_dateTime = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        log_file = f'{curr_dateTime}_{LOGGER_APP_NAME}.log'

    logger = logging.getLogger(logger_name)

    # Log to file (but not to terminal)
    if log_dir == None:
        log_file_path = log_file
    elif not os.path.isdir(log_dir):
        os.mkdir(log_dir)
        log_file_path = os.path.join(log_dir, log_file)
    else:
        log_file_path = os.path.join(log_dir, log_file)

    logfile_handler = logging.FileHandler(log_file_path)
    plain_formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)-8s | %(message)s", 
        datefmt="%Y-%m-%d %H:%M:%S"
        )
    logfile_handler.setFormatter(plain_formatter)  


    # Logging info level to stdout with colors
    terminal_handler = colorlog.StreamHandler()
    color_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s %(log_color)s%(levelname)-8s | %(message)s",
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            "ALL"     : "purple",
            "TRACE"   : "purple",
            "DEBUG"   : "cyan",
            "INFO"    : "white",
            "WARNING" : "yellow",
            "ERROR"   : "red",
            "CRITICAL": "bold_red",
        },
        secondary_log_colors={},
        style='%'
    )
    terminal_handler.setFormatter(color_formatter)

    logger.setLevel(log_level)

    # Add handlers to logger
    logger.addHandler(logfile_handler)
    logger.addHandler(terminal_handler)
    
    return logger


# Print iterations progress
def print_progressbar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 82, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    if len(prefix) < 1:
        prefix = "                 "
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()


# Ask a Yes-No question and handle the user input
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


# Main function of the script controlling the flow
def main(options):

    LOGGER.info("------------------------------==========  <NAME>  ==========-----------------------------")
    LOGGER.info(f"Date Time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    LOGGER.info(f"User name      : {options.username}")
    LOGGER.info(f"Working dir    : {CWD}")
    LOGGER.info(f"Source dir     : {options.source}")
    LOGGER.info(f"Target dir     : {options.target}")
    LOGGER.info(f"Log level      : {logging.getLevelName(LOGGER.level)}")
    LOGGER.info(f"Verbose mode   : {options.verbose}")
    LOGGER.info("-----------------------------------------------------------------------------------------")

    if options.source is None or not os.path.isdir(options.source):
        LOGGER.critical(f"Given source dir '{options.source}' doesn't exist or is not a directory...")
        # sys.exit(0)

    if options.target is None or not os.path.isdir(options.target):
        LOGGER.critical(f"Given target dir '{options.target}' doesn't exist or is not a directory...")
        # sys.exit(0)

    LOGGER.info("- Action 1: Test all log levels ---------------------------------------------------------")
    current_loglevel = LOGGER.level
    LOGGER.setLevel(logging.ALL)  # Overwrite loglevel to always print all levels in this test

    print(f"All log levels: {list(logging._nameToLevel.keys())}")

    LOGGER.all("All message")
    LOGGER.trace("Trace message")
    LOGGER.debug("Debug message")
    LOGGER.info("Info message")
    LOGGER.warning("Warning message")
    LOGGER.error("Error message")
    LOGGER.critical("Critical message")
    LOGGER.none("None message")
    
    LOGGER.setLevel(current_loglevel)  # Restore original log level

    LOGGER.info("- Action 2: Progress bar ----------------------------------------------------------------")
    idx = 0
    max = 7 # example value for max items

    for idx in range(max):
        print_progressbar(idx, max-1)
        time.sleep(1)   
    LOGGER.debug(f"Latest Idx: {idx}")    

    if options.verbose:
        LOGGER.info(f"  - Verbose text")    
    
    LOGGER.info("- Action 3: Yes / No question ---------------------------------------------------------------")    
    
    if query_yes_no("  Question with a yes/no answer?.", "yes") == YES:
        LOGGER.warning(f"  - Answer: Yes")
    else: 
        LOGGER.fatal(f"  - Answer: No") 
        
    LOGGER.info("- Action 4: Command line action -------------------------------------------------------------") 
    cmd = ['ls', '-al']
    output = subprocess.check_output(cmd, cwd=CWD).decode('utf8')
    LOGGER.info(f"  - ls -al:\n{output}")

# -------------------------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    options = parse_options()

    addLoggingLevel('ALL'  , 1)
    addLoggingLevel('TRACE', logging.DEBUG - 5)
    addLoggingLevel('NONE', logging.CRITICAL + 5)
    LOGGER = create_logger(log_level=options.loglevel.upper())

    main(options)

    print(f"The END...")
#============================================================================
#             Importing Things
#============================================================================

#import colorama
import sys
import math

#============================================================================
#             Console Class
#============================================================================

class Colormap(object):
    violet = "\033[95m"
    blue = "\033[94m"
    cyan = "\033[36m"
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    default = '\033[39m'
    bold = '\033[1m'
    end = '\033[0m'

class Console(object):
    """
    A logger that will adjust what gets printed based on specifications from the user.

    Attributes:
        severity_threshold

    Methods:
        log
    """
    def __init__(self, severity_threshold="Log"):
        #colorama.init()

        self.severities = ["Log", "Alert", "Warning", "Error"]
        if severity_threshold.title() in self.severities:
            self.severity_threshold = str(severity_threshold).title()
        else:
            self.severity_threshold = "Log"

    def log(self, notice):
        if hasattr(notice, "severity"):
            if notice.severity == "Prompt":
                print(notice)
                return notice.callback_function()
            elif notice.severity == "Error":
                print(notice)
                notice.callback_function()
            if self.severities.index(self.severity_threshold) <= self.severities.index(notice.severity):
                print(notice)
        elif self.severity_threshold == "Log":
            print(notice)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Console with logging threshold '{0}'".format(self.severity_threshold)

class Progress(object):
    """
    A specialized progress bar that tracks the progress of a function performed multiple times.
    Can be either limited or unlimited.
    """
    def __init__(self, console, description, blocks=20, count=0, color="blue", completed_character="X", limited=True):
        self.console = console
        self.warnings = []
        self.description = description
        self.blocks = blocks
        self.count = count
        self.progress = 0
        self.limited = limited
        self.complete = False
        self.__set_progress_attributes__()
        self.color_code = getattr(Colormap, color)
        self.completed_character = completed_character[0]
        self.__set_string_attributes__()
        if self.console.severities.index(self.console.severity_threshold) <= self.console.severities.index("Log"):
            self.display = True
        else:
            self.display = False
        #print(self.blocks, self.count, self.progress_block, self.limited, self.progress)

    def current_progress(self):
        if self.limited == True:
            return self.progress
        else:
            if self.progress == 0:
                return 0
            else:
                return int(self.progress / self.count) % self.count

    def __set_string_attributes__(self):
        self.progress_prefix = self.color_code+"[Progress]: "+Colormap.end + self.description + " "

        if self.limited == True:
            self.string_complete = self.color_code + self.completed_character*self.progress_block + Colormap.end
            self.string_incomplete = " "*(self.blocks-self.progress_block)
            self.bar = "|{0}{1}|".format(self.string_complete, self.string_incomplete)
            self.numeric_marker = " {0: 3d}% ({1}/{2})".format(int(math.floor(self.progress_percent*100)), self.progress, self.count)
        else:
            if self.complete == False:
                self.string_complete = self.color_code + self.completed_character + Colormap.end
                self.string_before = " "*(self.progress_block)
                self.string_after = " "*(self.blocks-self.progress_block-1)
                self.bar = "|{0}{1}{2}|".format(self.string_before, self.string_complete, self.string_after)
                self.numeric_marker = " ({0})".format(self.progress)
            else:
                self.string_complete = self.color_code + self.blocks*self.completed_character + Colormap.end
                self.bar = "|{0}|".format(self.string_complete)
                self.numeric_marker = "  100% ({0}/{0})".format(self.progress)
        self.progress_string = self.progress_prefix + self.bar + self.numeric_marker

    def __set_progress_attributes__(self):
        self.progress_percent = float(self.current_progress())/self.count
        #print(self.progress_percent)
        self.progress_block = int(self.progress_percent * self.blocks)
        #print(self.progress_block)

    def update(self, i=1):
        #print(self.progress)
        self.progress = i
        self.__set_progress_attributes__()
        if self.display:
            if int(self.progress_percent) == 1 and self.limited == True:
                self.color_code = Colormap.green
                self.__set_string_attributes__()
                print("\r"),
                print(self.progress_string)
            else:
                self.__set_string_attributes__()
                print("\r"),
                print(self.progress_string),
                print("\r"),
                sys.stdout.flush()
            #print
            #print(self.blocks, self.count, self.progress_block, self.limited, self.progress)

    def increment(self, i=1):
        self.update(self.progress+i)

    def add_warning(self, notice):
        self.warnings.append(notice)

    def start(self):
        self.update(i=0)

    def close(self, exit):
        self.complete = True
        if int(self.progress_percent):
            pass
        elif exit.lower() == "error" and self.display == True:
            self.color_code = Colormap.red#'\r' + self.color_code+"[Progress] "+Colormap.end + self.description + " ["+ self.color_code + self.completed_character*self.progress_block + Colormap.end + Colormap.red + "X"*(self.blocks-self.progress_block) + Colormap.end +"]" + self.progress_percent_pretty + " ({0}/{1})".format(self.progress, self.count)
            self.update(self.progress)
            self.display = False
        elif self.display == True:
            self.color_code = Colormap.green
            self.update(self.progress)
            self.display = False
        if len(self.warnings) == 0:
            self.console.log("")
        else:
            for warning in self.warnings:
                self.console.log(warning)

class Notice(object):
    """
    A warning with various attributes and behaviors.
    """
    def __init__(self, severity="Log", message="", show_prefix=True, callback=None, boolean_response=False, open_response=False, valid_responses=None):
        self.colormap = {"Prompt":Colormap.violet, "Alert": Colormap.green, "Warning": Colormap.yellow, "Error": Colormap.red, "End": Colormap.end}
        self.show_prefix = show_prefix
        if severity in ["Log", "Prompt", "Alert", "Warning","Error"]:
            self.severity = str(severity)
        else:
            self.severity = "Log"
        self.message = str(message)

        if self.severity == "Prompt":
            if open_response == True:
                self.valid_responses = {"VALUE":"Open-Ended"}
            elif boolean_response == True:
                self.valid_responses = {True:["Yes","Y","1"],False:["No","N","0"]}
            elif type(valid_responses) == dict:
                self.valid_responses = valid_responses
            else:
                self.valid_responses = {True:["Yes","Y","1"],False:["No","N","0"]}
            self.response_lookup = {}
            response_representatives = []
            for returnval, valid_responses in self.valid_responses.items():
                if type(valid_responses) == list:
                    response_representatives.append(valid_responses[0])
                    for valid_response in valid_responses:
                        self.response_lookup[valid_response.upper()] = returnval
                elif type(valid_responses) == str:
                    response_representatives.append(valid_responses)
                    self.response_lookup[valid_responses.upper()] = returnval
            self.valid_responses_string = "|".join(response_representatives)

        if callback != None:
            self.callback_function = callback
        elif self.severity == "Error":
            def callback():
                sys.exit(1)
            self.callback_function = callback
        elif self.severity == "Prompt":
            def callback():
                should_continue = False
                while should_continue == False:
                    response = raw_input(self.colormap["Prompt"]+"> "+self.colormap["End"])
                    if self.valid_responses_string == "Open-Ended":
                        return response
                    else:
                        response = response.upper()
                    if response in self.response_lookup.keys():
                        return self.response_lookup[response]
                    else:
                        print(Notice("Alert", "{0} is not a valid response! ({1})".format(response, self.valid_responses_string), show_prefix=self.show_prefix))

            self.callback_function = callback
        else:
            def callback():
                pass
            self.callback_function = callback


    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.severity in ["Warning", "Error"]:
            severitystring = self.severity.upper()
        else:
            severitystring = self.severity
        if self.severity == "Prompt":
            if self.show_prefix:
                returnval = self.colormap[self.severity] + "[{0}]: {1} ({2})".format(severitystring, self.message, self.valid_responses_string)
            else:
                returnval = self.colormap[self.severity] + "{0} ({1})".format(self.message, self.valid_responses_string)
        elif self.severity == "Log" and self.show_prefix == True:
            returnval = "[{0}]: {1}".format(severitystring, self.message)
        elif self.severity == "Log" and self.show_prefix == False:
            returnval = self.message
        elif self.show_prefix == True:
            returnval = self.colormap[self.severity] + "[{0}]: {1}".format(severitystring, self.message) + self.colormap["End"]
        else:
            returnval = self.colormap[self.severity] + self.message + self.colormap["End"]
        return returnval

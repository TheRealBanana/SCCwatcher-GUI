import re
from collections import OrderedDict as OD
from copy import deepcopy as DC

#Tracking the current version from here only, making the change here updates everything.
_CURRENT_GUI_VERSION_ = "2.2-alpha2"
#GitHub API url for version infos
_GITHUB_VERSION_URL_ = "https://api.github.com/repos/TheRealBanana/SCCwatcher-GUI/releases/latest"

#Get ready for tons of lame code
#The use of OD(), OrderedDict, means that the dictionary we create will be in the exact order as its created.
#This is useful because we also don't wan't the options in our ini file being saved in any old way, we want an order.
#The order of the options below is therefore extremely important. All of the global options must come first before all others.

#Format for the dictionary is this:
#elementsToOptions[element_name] = [ini_file_section_name, ini_file_option_name]
#The access methods are provided by running a type comparison on an eval of the element_name. Eval'ing turns that name into a proper object which can be type()'d.
#The type dictionary is kept in elementAccessMethods below elementsToOptions.

#This dictionary defines the translation between UI Elements and ini options. Without this, things would get much more complicated.
#The structure is the same as all the other elements databases. The main keys are the tab names, and each subkey of the tab is the UI element. Each value is the Group and the INI option name in a list.
elementsToOptions = OD()
#basic download and operational options first
elementsToOptions["ggMasterAutodlCheck"] = ["GlobalSettings", "service"]
elementsToOptions["ggEnableVerboseCheck"] = ["GlobalSettings", "verbose"]
elementsToOptions["ggVerboseTabTextbox"] = ["GlobalSettings", "verbose_tab"]
elementsToOptions["ggBeepCheckbox"] = ["GlobalSettings", "printalert"]
elementsToOptions["ggEnableLoggingCheck"] = ["GlobalSettings", "logenabled"]
elementsToOptions["ggLogpathTextbox"] = ["GlobalSettings", "logpath"]
elementsToOptions["ggNetworkDelaySpinbox"] = ["GlobalSettings", "startdelay"]
elementsToOptions["ggPasskeyTextbox"] = ["GlobalSettings", "passkey"]
elementsToOptions["globalDupecheckCheck"] = ["GlobalSettings", "dupecheck"]
elementsToOptions["globalSSLDownloadCheck"] = ["GlobalSettings", "download_ssl"]
elementsToOptions["ggSavepathTextbox"] = ["GlobalSettings", "savepath"]
#These Size Limit UI elements need some special treatment. Both when loading and saving.
#These hold an additional object name that will signal the function to operate on this third data item, the element name that holds the suffix data.
elementsToOptions["globalSizeLimitLowerTextbox"] = ["GlobalSettings", "lower_sizelimit", "globalSizeLimitLowerSuffixSelector"]
elementsToOptions["globalSizeLimitUpperTextbox"] = ["GlobalSettings", "upper_sizelimit", "globalSizeLimitUpperSuffixSelector"]
elementsToOptions["globalMaxTriesSpinbox"] = ["GlobalSettings", "max_dl_tries"]
elementsToOptions["globalRetryWaitSpinbox"] = ["GlobalSettings", "retry_wait"]
elementsToOptions["globalCFBypassUseragentTextbox"] = ["GlobalSettings", "cfbypass_useragent"]
elementsToOptions["globalCFBypassCookiefilePathTextbox"] = ["GlobalSettings", "cfbypass_cookiefile"]
#ftp settings
elementsToOptions["ftpMasterEnableCheck"] = ["GlobalSettings", "ftpEnable"]
elementsToOptions["ftpHostnameTextbox"] = ["GlobalSettings", "ftpServerHostname"]
elementsToOptions["ftpPortTextbox"] = ["GlobalSettings", "ftpPort"]
elementsToOptions["ftpRemoteFolderTextbox"] = ["GlobalSettings", "ftpRemoteFolder"]
elementsToOptions["ftpUsernameTextbox"] = ["GlobalSettings", "ftpUsername"]
elementsToOptions["ftpPasswordTextbox"] = ["GlobalSettings", "ftpPassword"]
elementsToOptions["ftpPasvModeCheck"] = ["GlobalSettings", "ftpPassive"]
elementsToOptions["ftpTLSModeCheck"] = ["GlobalSettings", "ftpSecureMode"]
#ut web ui options
elementsToOptions["utwuiMasterEnableTriCheck"] = ["GlobalSettings", "utorrent_mode"]
elementsToOptions["utwuiUsernameTextbox"] = ["GlobalSettings", "utorrent_username"]
elementsToOptions["utwuiPasswordTextbox"] = ["GlobalSettings", "utorrent_password"]
elementsToOptions["utwuiHostnameTextbox"] = ["GlobalSettings", "utorrent_hostname"]
elementsToOptions["utwuiPortTextbox"] = ["GlobalSettings", "utorrent_port"]
#Email options
elementsToOptions["emailMasterEnableCheck"] = ["GlobalSettings", "smtp_emailer"]
elementsToOptions["hostnameIPTextbox"] = ["GlobalSettings", "smtp_server"]
elementsToOptions["portTextbox"] = ["GlobalSettings", "smtp_port"]
elementsToOptions["emailUseTLSCheck"] = ["GlobalSettings", "smtp_tls"]
elementsToOptions["usernameTextbox"] = ["GlobalSettings", "smtp_username"]
elementsToOptions["passwordTextbox"] = ["GlobalSettings", "smtp_password"]
elementsToOptions["emailFromTextbox"] = ["GlobalSettings", "smtp_from"]
elementsToOptions["emailToTextbox"] = ["GlobalSettings", "smtp_to"]
elementsToOptions["emailSubjectTextbox"] = ["GlobalSettings", "smtp_subject"]
elementsToOptions["emailMessageTextbox"] = ["GlobalSettings", "smtp_message"]
#External command
elementsToOptions["extCmdMasterEnableCheck"] = ["GlobalSettings", "use_external_command"]
elementsToOptions["extCmdExeLocation"] = ["GlobalSettings", "external_command"]
elementsToOptions["extCmdExeArguments"] = ["GlobalSettings", "external_command_args"]
#Debug is always last
elementsToOptions["ggEnableDebugCheck"] = ["GlobalSettings", "DEBUG"] 


#These two OrderedDict's are for the watch and avoid lists, respectively. 

watchListElements = OD()
#These special options get processed for each entry in WLGwatchlistItemsList
#W_TITLE will be replaced automatically with the name of the watch entry
watchListElements["WLSGwatchNameTextbox"] = ["WSPECIAL", "W_TITLE"]
watchListElements["WLSGwatchFilterTextbox"] = ["WSPECIAL", "watch_filter"]
watchListElements["WLSGwatchFilterRegexCheck"] = ["WSPECIAL", "watch_regex"]
watchListElements["WLSGavoidFilterListTextbox"] = ["WSPECIAL", "avoid_filter"]
watchListElements["WLSGavoidFilterListRegexCheck"] = ["WSPECIAL", "avoid_regex"]
watchListElements["WLSGwatchCatListTextbox"] = ["WSPECIAL", "watch_categories"]
watchListElements["WLSGsavepathTextbox"] = ["WSPECIAL", "savepath"]
watchListElements["WLSGdupecheckingCheckbox"] = ["WSPECIAL", "dupecheck"]
watchListElements["WLSGsizeLimitLowerTextbox"] = ["WSPECIAL", "lower_sizelimit", "WLSGsizeLimitLowerSuffixSelector"]
watchListElements["WLSGsizeLimitUpperTextbox"] = ["WSPECIAL", "upper_sizelimit", "WLSGsizeLimitUpperSuffixSelector"]
watchListElements["WLSGemailCheckbox"] = ["WSPECIAL", "use_emailer"]
watchListElements["WLSGftpUploadCheckbox"] = ["WSPECIAL", "use_ftp_upload"]
watchListElements["WLSGutWebUiCheckox"] = ["WSPECIAL", "use_utorrent_webui"]
watchListElements["WLSGenableExternalCmdCheckbox"] = ["WSPECIAL", "use_external_command"]
watchListElements["WLSGexternalCommandTextbox"] = ["WSPECIAL", "external_command"]
watchListElements["WLSGexternalCommandArgsTextbox"] = ["WSPECIAL", "external_command_args"]


avoidListElements = OD()
#Same special thing here, all items in avoidlistItemsList are processed and saved.
#A_TITLE functions identically to W_TITLE, except the avoid name is prefixed by a minus sign, to mark it as an avoid.
avoidListElements["avoidNameTextbox"] = ["ASPECIAL", "A_TITLE"]
avoidListElements["avoidFilterTextbox"] = ["ASPECIAL", "avoid_filter"]
avoidListElements["avoidFilterRegexCheck"] = ["ASPECIAL", "avoid_regex"]


#This small dict keeps track of the read and write methods of different Qt types as well as the argument's expected data type
elementAccessMethods = {}
#                                     READ ,   WRITE  ,  type
elementAccessMethods["QLineEdit"] = ["text", "setText", "str"]
elementAccessMethods["QTextEdit"] = ["toPlainText", "setPlainText", "str"]
elementAccessMethods["QSpinBox"] = ["value", "setValue", "int"]
elementAccessMethods["QCheckBox"] = ["checkState", "setCheckState", "int"]
elementAccessMethods["QComboBox"] = ["currentIndex", "setCurrentIndex", "int"]
elementAccessMethods["QListWidget"] = ["currentItem", "addItem", "QListWidgetItem"]
elementAccessMethods["QListWidgetItem"] = ["text", "setText", "str"]

#Create a reverse dicts for the options>elements conversion.
globalReverse = OD()
watchReverse = OD()
avoidReverse = OD()
for key, val in elementsToOptions.iteritems(): globalReverse[val[1]] = key
for key, val in watchListElements.iteritems(): watchReverse[val[1]] = key
for key, val in avoidListElements.iteritems(): avoidReverse[val[1]] = key

#GUI Defaults
#These three dicts contain the default state of our application.
#Consider spreading this definition out into multiple single-line assignments for each entry.
#Having it all on one line only makes it harder to add entries in the future and makes it difficult to debug faults in this part of the code.
guiDefaults = {}
#Global Options
guiDefaults["allOtherDefaults"] = OD()
guiDefaults["allOtherDefaults"]["ggMasterAutodlCheck"] = 0
guiDefaults["allOtherDefaults"]["ggEnableVerboseCheck"] = 0
guiDefaults["allOtherDefaults"]["ggVerboseTabTextbox"] = ""
guiDefaults["allOtherDefaults"]["ggBeepCheckbox"] = 0
guiDefaults["allOtherDefaults"]["ggEnableLoggingCheck"] = 0
guiDefaults["allOtherDefaults"]["ggLogpathTextbox"] = ""
guiDefaults["allOtherDefaults"]["ggNetworkDelaySpinbox"] = 20
guiDefaults["allOtherDefaults"]["ggPasskeyTextbox"] = ""
guiDefaults["allOtherDefaults"]["globalDupecheckCheck"] = 0
guiDefaults["allOtherDefaults"]["globalSSLDownloadCheck"] = 0
guiDefaults["allOtherDefaults"]["ggSavepathTextbox"] = ""
guiDefaults["allOtherDefaults"]["globalSizeLimitLowerTextbox"] = ""
guiDefaults["allOtherDefaults"]["globalSizeLimitUpperTextbox"] = ""
guiDefaults["allOtherDefaults"]["globalSizeLimitLowerSuffixSelector"] = 0
guiDefaults["allOtherDefaults"]["globalSizeLimitUpperSuffixSelector"] = 0
guiDefaults["allOtherDefaults"]["globalMaxTriesSpinbox"] = 15
guiDefaults["allOtherDefaults"]["globalRetryWaitSpinbox"] = 1
guiDefaults["allOtherDefaults"]["globalCFBypassUseragentTextbox"] = ""
guiDefaults["allOtherDefaults"]["globalCFBypassCookiefilePathTextbox"] = ""
guiDefaults["allOtherDefaults"]["ftpMasterEnableCheck"] = 0
guiDefaults["allOtherDefaults"]["ftpHostnameTextbox"] = ""
guiDefaults["allOtherDefaults"]["ftpPortTextbox"] = ""
guiDefaults["allOtherDefaults"]["ftpRemoteFolderTextbox"] = ""
guiDefaults["allOtherDefaults"]["ftpUsernameTextbox"] = ""
guiDefaults["allOtherDefaults"]["ftpPasswordTextbox"] = ""
guiDefaults["allOtherDefaults"]["ftpPasvModeCheck"] = 2
guiDefaults["allOtherDefaults"]["ftpTLSModeCheck"] = 0
guiDefaults["allOtherDefaults"]["utwuiMasterEnableTriCheck"] = 0
guiDefaults["allOtherDefaults"]["utwuiUsernameTextbox"] = ""
guiDefaults["allOtherDefaults"]["utwuiPasswordTextbox"] = ""
guiDefaults["allOtherDefaults"]["utwuiHostnameTextbox"] = ""
guiDefaults["allOtherDefaults"]["utwuiPortTextbox"] = ""
guiDefaults["allOtherDefaults"]["emailMasterEnableCheck"] = 0
guiDefaults["allOtherDefaults"]["hostnameIPTextbox"] = ""
guiDefaults["allOtherDefaults"]["portTextbox"] = ""
guiDefaults["allOtherDefaults"]["emailUseTLSCheck"] = 0
guiDefaults["allOtherDefaults"]["usernameTextbox"] = ""
guiDefaults["allOtherDefaults"]["passwordTextbox"] = ""
guiDefaults["allOtherDefaults"]["emailFromTextbox"] = ""
guiDefaults["allOtherDefaults"]["emailToTextbox"] = ""
guiDefaults["allOtherDefaults"]["emailSubjectTextbox"] = ""
guiDefaults["allOtherDefaults"]["emailMessageTextbox"] = ""
guiDefaults["allOtherDefaults"]["extCmdMasterEnableCheck"] = 0
guiDefaults["allOtherDefaults"]["extCmdExeLocation"] = ""
guiDefaults["allOtherDefaults"]["extCmdExeArguments"] = ""
guiDefaults["allOtherDefaults"]["ggEnableDebugCheck"] = 0
#Watchlist
guiDefaults["watchlistDefaults"] = OD()
guiDefaults["watchlistDefaults"]["WLSGwatchNameTextbox"] = ""
guiDefaults["watchlistDefaults"]["WLSGwatchFilterTextbox"] = ""
guiDefaults["watchlistDefaults"]["WLSGwatchFilterRegexCheck"] = 0
guiDefaults["watchlistDefaults"]["WLSGavoidFilterListTextbox"] = ""
guiDefaults["watchlistDefaults"]["WLSGavoidFilterListRegexCheck"] = 0
guiDefaults["watchlistDefaults"]["WLSGwatchCatListTextbox"] = ""
guiDefaults["watchlistDefaults"]["WLSGsavepathTextbox"] = ""
guiDefaults["watchlistDefaults"]["WLSGdupecheckingCheckbox"] = 0
guiDefaults["watchlistDefaults"]["WLSGsizeLimitLowerTextbox"] = ""
guiDefaults["watchlistDefaults"]["WLSGsizeLimitLowerSuffixSelector"] = 0
guiDefaults["watchlistDefaults"]["WLSGsizeLimitUpperTextbox"] = ""
guiDefaults["watchlistDefaults"]["WLSGsizeLimitUpperSuffixSelector"] = 0
guiDefaults["watchlistDefaults"]["WLSGemailCheckbox"] = 0
guiDefaults["watchlistDefaults"]["WLSGftpUploadCheckbox"] = 0
guiDefaults["watchlistDefaults"]["WLSGutWebUiCheckox"] = 0
guiDefaults["watchlistDefaults"]["WLSGenableExternalCmdCheckbox"] = 0
guiDefaults["watchlistDefaults"]["WLSGexternalCommandTextbox"] = ""
guiDefaults["watchlistDefaults"]["WLSGexternalCommandArgsTextbox"] = ""
#Avoidlist
guiDefaults["avoidlistDefaults"] = OD()
guiDefaults["avoidlistDefaults"]["avoidNameTextbox"] = ""
guiDefaults["avoidlistDefaults"]["avoidFilterTextbox"] = ""
guiDefaults["avoidlistDefaults"]["avoidFilterRegexCheck"] = 0

#Defaults for the script status indicator
scriptStatusDefaults = {}
scriptStatusDefaults["version"] = "Not Running"
scriptStatusDefaults["autodlstatus"] = "N/A"
scriptStatusDefaults["ssl"] = "N/A"
scriptStatusDefaults["max_dl_tries"] = "N/A"
scriptStatusDefaults["retry_wait"] = "N/A"
scriptStatusDefaults["cf_workaround"] = "N/A"
scriptStatusDefaults["dupecheck"] = "N/A"
scriptStatusDefaults["logging"] = "N/A"
scriptStatusDefaults["verbose"] = "N/A"
scriptStatusDefaults["recent_list_size"] = "N/A"
scriptStatusDefaults["wl_al_size"] = "N/A"
scriptStatusDefaults["ini_path"] = ""

#These are for tracking GUI changes
guiState = {}
guiState["globalOptionsState"] = DC(guiDefaults["allOtherDefaults"])
guiState["watchlistState"] = OD()
guiState["avoidlistState"] = OD()

class sccwSettingsManager:
    def __init__(self, MWloc):
        self.elementsToOptions = elementsToOptions
        self.elementAccessMethods = elementAccessMethods
        self.watchListElements = watchListElements
        self.avoidListElements = avoidListElements
        self.REVelementsToOptions = globalReverse
        self.REVwatchListElements = watchReverse
        self.REVavoidListElements = avoidReverse
        self.guiDefaults = guiDefaults
        self.scriptStatusDefaults = scriptStatusDefaults
        self.guiState = guiState
        #These two below are functions
        self.windowPos = MWloc[0]
        self.windowSize = MWloc[1]
        self.isLoaded = False
        self.currentFile = ""
        #Current version tracking
        self.CURRENT_GUI_VERSION = _CURRENT_GUI_VERSION_
        self.GITHUB_VER_URL = _GITHUB_VERSION_URL_
    
    def openSettingsFile(self, filename):
        self.currentFile = filename
        self.isLoaded = True
        
    def closeSettingsFile(self):
        self.appSettings = None
        self.currentFile = ""
        self.isLoaded = False
    
    def saveSettings(self, data):
        savefile = open(self.currentFile, 'w')
        for key in data:
            savefile.write("[%s]" % str(key))
            savefile.write("\n")
            for key, value in data[key].iteritems():
                line = "%s=%s" % (key, value)
                savefile.write(line)
                savefile.write("\n")
            savefile.write("\n")
        
        savefile.close()
        
    def loadSettings(self):
        returnData = OD()
        cur_dict = None
        
        try:
            inifile = open(self.currentFile, 'r')
        except:
            raise Exception("Error opening file at %s" % self.currentFile)
        
        #Here's the business end of the function
        for line in inifile:
            #Ignore any commented out lines
            if line[0] == "#":
                continue
            
            #New group
            if line[0] == "[":
                grpname = re.match("\[(.*?)\]", line).group(1)
                cur_dict = grpname
                if returnData.has_key("grpname") is False:
                    returnData[grpname] = OD()
                
            #Options
            elif re.match("(.*?)(?:\s+)?=(?:\s+)?(.*)", line) is not None:
                if cur_dict is not None:
                    option_line = re.match("(.*?)(?:\s+)?=(?:\s+)?(.*)", line)
                    returnData[cur_dict][str(option_line.group(1)).lower()] = str(option_line.group(2))
                else:
                    pass
        
        #Gotta close it before we quit
        inifile.close()

        return returnData

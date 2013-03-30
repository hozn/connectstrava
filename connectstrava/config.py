import os
from ConfigParser import SafeConfigParser

config = SafeConfigParser()
config.set('DEFAULT', 'here', os.path.join(os.path.dirname(__file__), '..'))

def init_config(configfile):
    global config
    filesread = config.read([configfile])
    if not filesread:
        raise RuntimeError("Unable to read config file: {0}".format(configfile))
    
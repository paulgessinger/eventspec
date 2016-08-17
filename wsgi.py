import os
import sys

# Install venv by `virtualenv --distribute venv`
# Then install depedencies: `source venv/bin/active`
# `pip install -r requirements.txt`
appdir = os.path.dirname(os.path.realpath(__file__)) 
activate = os.path.join(appdir, "bin", "activate_this.py") 
# os.system("source {}".format(activate));
execfile(activate, dict(__file__=activate))

if appdir not in sys.path:
    sys.path.append(appdir)

# The application object is used by any WSGI server configured to use this
# file.

# Ensure there is an app.py script in the current folder
from app import app as application

# Compatibility shim: CouchPotato code (including source generated at runtime for
# index files) imports "CodernityDB.*". The vendored engine now lives at
# libs/codernitydb3 (a Python 3 native port). This package re-exports it under the
# original import path so nothing else has to change.
from codernitydb3 import __version__, __license__

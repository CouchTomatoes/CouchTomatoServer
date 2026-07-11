# PyInstaller spec for CouchTomato.
#
# CouchTomato's plugin system (couchpotato/core/loader.py) imports provider/
# notification/downloader modules dynamically by walking the filesystem and
# calling import_module() with computed names - PyInstaller's static
# analysis can't trace those, so a plain frozen build would silently load
# zero plugins. Instead of fighting that, `couchpotato/` and `libs/` (the
# vendored packages with no PyPI equivalent - axl, caper, codernitydb3, etc.)
# are bundled as loose data trees alongside the frozen bootstrap, exactly
# mirroring how they sit next to CouchPotato.py in a normal source checkout.
# CouchPotato.py's own `sys.path.insert(0, .../libs)` then makes the dynamic
# imports work at runtime the same way they do when run from source.
import os

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
root = os.path.dirname(os.path.abspath(SPECPATH))

# Everything couchpotato/ imports from pip (requirements.txt) is only ever
# imported from *inside* the loose couchpotato/libs data trees below, never
# from CouchPotato.py's own static import chain - so PyInstaller's analysis
# never traces it and silently drops it. Same for a couple of stdlib modules
# (xml.etree, distutils) that turned out to only be reachable dynamically.
# Collected explicitly rather than discovered by trial and error alone: this
# list was built by actually running the frozen build and reading the real
# ModuleNotFoundErrors it produced, then re-verifying with another run.
hidden = ['telnetlib']
for pkg in ['git', 'bs4', 'bencode', 'chardet', 'httplib2', 'requests', 'tornado',
            'xml.etree', 'distutils', 'email.mime']:
    hidden.extend(collect_submodules(pkg))

a = Analysis(
    [os.path.join(root, 'CouchPotato.py')],
    pathex=[root, os.path.join(root, 'libs')],
    binaries=[],
    datas=[
        (os.path.join(root, 'couchpotato'), 'couchpotato'),
        (os.path.join(root, 'libs'), 'libs'),
        # updater/main.py does `import version` (no dot) relying on Python's
        # implicit script-directory sys.path entry when run as
        # `python3 CouchPotato.py` from the repo root - that entry doesn't
        # exist in a frozen build, so version.py has to be bundled explicitly.
        (os.path.join(root, 'version.py'), '.'),
    ],
    hiddenimports=hidden,
    hookspath=[],
    # OpenSSL/cryptography are optional (couchpotato/core/_base/_core.py logs a
    # warning and continues without them if missing) - excluded so the build
    # doesn't depend on whatever happens to be importable on the build machine.
    excludes=['OpenSSL', 'cryptography'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CouchTomato',
    console=True,
    icon=os.path.join(root, 'couchpotato', 'static', 'images', 'icons', 'favicon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='CouchTomato',
)

app = BUNDLE(
    coll,
    name='CouchTomato.app',
    icon=os.path.join(root, 'couchpotato', 'static', 'images', 'icons', 'favicon.ico'),
    bundle_identifier='com.couchtomatoes.couchtomato',
)

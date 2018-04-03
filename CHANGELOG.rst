.. :changelog:

Release History
===============


0.3.1 (2018-04-03)
~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Added `NotADirectoryError` exception to directory opener to
  prevent eating up regular files.
- Fixed bz2 opener not supporting seek() operation.


0.3.0 (2018-04-02)
~~~~~~~~~~~~~~~~~~

**Improvements**

- Rewrote `filehandles` module using (EAFP style) and removed path.test()
  methods (LBYL style).
- Removed path checking based on `mimetypes`.


0.2.0 (2018-03-29)
~~~~~~~~~~~~~~~~~~

**New features**

- Added 'pattern' argument - regular expression pattern to include files
  only with specified pattern.


0.1.2 (2018-03-27)
~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fixed `Opener` initializer to properly add non-standard extension and type
  to `mimetypes` module.


0.1.1 (2018-03-26)
~~~~~~~~~~~~~~~~~~

**Improvements**

- Added `logging` and `verboselogs` logging.
- Replaced all `if verbose: print('...')` with `logger.verbose('...')` calls.


0.1.0 (2018-03-07)
~~~~~~~~~~~~~~~~~~

- Initial public release.
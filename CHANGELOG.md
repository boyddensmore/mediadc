# Changelog

All notable changes to this project will be documented in this file.

## [0.1.8 - 2021-12-20]

Updated `python_command` setting from alias to full/absolute path to the Python. PHP-FPM users should check and update it on Administration settings page if install fails on Configuration page

### Added

- Added Duplicates list batch editing and filtering
- Added Duplicate group batch editing, filtering and sorting
- Added Some title hints to action buttons
- Added Items per page setting for duplicate groups
- Added Auto open of the next detail group option

### Changed

- Changed Default path to Python (if install fails silently or can't find Python, update `python_command` on Administration settings page)
- Changed Some backend&frontend mechanisms of requesting and working with files
- Changed Supported Nextcloud versions (21-23)

### Fixed

- Fixed Python work with user shared, webdav shares, local shares files scan
- Fixed Python `dbtableprefix` undefined
- Fixed Parsing Python output in PHP and displaying propper error messages
- Fixed Python `hexhamming` module caused `Illegal instruction` issue on unsupported CPUs

## [0.1.7 - 2021-10-30]

### Added

- Added php `exec` function availability check

### Changed

- Changed missed PHP version requirement from 7.4 to 7.3
- Moved MediaDC admin settings from Groupware tab to separate Administrator menu item
- Changed server errors messages and moved them to the Configuration page

### Fixed

- Fixed Python version validation fails

## [0.1.6 - 2021-10-22]

### Added

- Added Delete file confirmation setting (sidebar settings)

### Fixed

- Fixed MediaDC not working if specified another apps directory in Nextcloud config (apps_paths)
- Fixed MediaDC install fails on Configuration page on some server configs
- Changed function callbacks syntax to support PHP 7.3

## [0.1.5 - 2021-10-12]

### Added

- Added some action loaders on Details page
- Added links to the list of target directories

### Fixed

- Fixed video processing broken by previous update.
- Fixed pip version parsing, install now works with last pip.
- Fixed processing files from other NC instances and remote shares.

## [0.1.4 - 2021-10-09]

### Fixed

- Proper work with non ascii characters in files names. Thanks to kovge.
- Minor frontend fixes

## [0.1.3 - 2021-10-04]

### Fixed

- Now properly parse configs for database connect.

## [0.1.2 - 2021-09-30]

### Added

- Added image and video previews support

### Fixed

- Fixed not disabled buttons for impossible actions on Configuration page (update/delete on not installed packages)
- Now properly display installation errors

## [0.1.1 - 2021-09-26]

### Added

### Changed

### Fixed

- Fixed opening photo&video via Viewer in Nextcloud 21, 22

## [0.1.0 - 2021-09-23]

### Added

### Changed

- First beta release available at Nextcloud App Store

### Fixed


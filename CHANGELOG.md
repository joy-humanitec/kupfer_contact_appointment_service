# crm_service CHANGELOG

## [v0.0.19] - 2019-03-04


### Added

- Added a new field to `/contact`-endpoint: `Contact.title_display`
- Added `LICENCE`

### Changed

- Updated `/contact` endpoint: `title` with more choices `dr prof, prof dr` 
- Updated `/appointment` endpoint: with more notes-choices for OOO-Notes
- Refactored settings

## [v0.0.18] - 2019-02-28

### Changed

- Updated `/appointment` endpoint: `notes` shouldn't be required

## [v0.0.17] - 2019-02-28

### Added

- Added a new model: `appointment.AppointmentNote`
- Added a forwards-migration for `appointment.Appointment.notes`

### Changed

- Updated `/appointment` endpoint: `notes` becomes a read- and writeable ArrayField of `AppointmentNote`-objects, 
whereas `id` is optional and only one `AppointmentNote` of a `type` is allowed 
- Updated `contact.Contact.title`-choices with: `dr, frau, herr, mrs, miss, prof`

### Removed

- Updated `/appointment` endpoint: `notes` no longer a string property

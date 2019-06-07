+++
title = "Contact and Appointment service (Django)"
api_url = "marketplace/kupfer-contact-appointment-service"
+++


# Contact and Appointment service (Django)

## Summary

The contact and appointment service enables your application to store contacts, appointments with multiple notes and sent notifications about appointments.

## REST data models

### Contact

A _Contact_ can be seen as an extension of the CoreUser from Bifrost by using the ``core_user_uuid`` for creating a OneToOneRelationship.
It can be also left blank for Contacts without a correlated CoreUser. 

A _Contact_ has the following properties:

- **uuid**: UUID of the Contact.
- **core_user_uuid**: UUID of the related CoreUser (optional).
- **customer_id**: Custom ID, which must be unique per organization. It will be set automatically starting at 10001.
- **first_name**: First name of the Contact.
- **middle_name**: Middle name of the Contact.
- **last_name**: Last name of the Contact.
- **title**: Title of the Contact. Choices are: 'Mr.', 'Ms.', 'Mrs.', 'Miss' and 'Family'.
- **suffix**: Suffix for titles like dr., prof., dr. med. etc..
- **contact_type**: Type of the Contact. Choices are: 'Customer', 'Supplier', 'Producer' and 'Personnel'.
- **customer_type**: Type of the Contact. Choices are: 'Customer', 'Company' and 'Public'.
- **company**: Company of the Contact.
- **addresses**: List of Addresses including a type. Choices of the type are: 'home', 'billing', 'business', 'delivery' and 'mailing'.
- **siteprofile_uuids**: List of related UUIDs of SiteProfiles (location_service).
- **emails**: List of E-Mails with a type. Choices of the E-Mail-Type are: 'office', 'private' and 'other'.
- **phones**: List of phone numbers with a type. Choices of the phone type are: 'office', 'mobile', 'home' and 'fax'.
- **notes**: Textual notes.
- **organization_uuid**: UUID of a related organization.
- **workflowlevel1_uuids**: List of UUIDs of WorkflowLevel1s.
- **workflowlevel2_uuids**: List of UUIDs of WorkflowLevel2s.
- **create_date**: Timestamp when the Contact was created (set automatically).
- **edit_date**: Timestamp, when the Contact was last modified (set automatically).

#### Endpoints

-  `GET /contact/`: Retrieves a list of Contacts.
-  `POST /contact/`: Creates a new Contact.
-  `GET /contact/{id}/`: Retrieves a Contact by its ID.
-  `PUT /contact/{id}/`: Updates the Contact with the given ID (all fields).
-  `PATCH /contact/{id}/`: Updates the Contact with the given ID (only specified fields).
-  `DELETE /contact/{id}/`: Deletes the Contact with the given ID.

### Appointment

The _Appointment_ describes a time span for invited CoreUsers or Contacts at a SiteProfile or other address.

An _Appointment_ has the following properties:

- **uuid**: UUID of the Appointment.
- **name**: Name of the Appointment.
- **owner**: Every Appointment must have an owner. It could be a CoreUser, Contact, Organization and so on.
- **start_date**: Start date of the Appointment.
- **end_date**: End date of the Appointment.
- **type**: An array of types for the Appointment.
- **address**: An address for the Appointment.
- **siteprofile_uuid**: A UUID of a related SiteProfile.
- **invitee_uuids**: List of CoreUser UUIDs invited to the appointment.
- **organization_uuid**: UUID of the organization that has access to the Appointment.
- **notes**: Related AppointmentNotes.
- **workflowlevel2_uuids**: UUID of the related WorkflowLevel2.
- **contact_uuid**: UUID of a related Contact.
- **summary**: A textual summary of the Appointment.

#### Endpoints

-  `GET /appointment/`: Retrieves a list of Appointments.
-  `POST /appointment/`: Creates a new Appointment.
-  `GET /appointment/{uuid}/`: Retrieves a Appointment by its UUID.
-  `PUT /appointment/{uuid}/`: Updates the Appointment with the given UUID (all fields).
-  `PATCH /appointment/{uuid}/`: Updates the Appointment with the given UUID (only specified fields).
-  `DELETE /appointment/{uuid}/`: Deletes the Appointment with the given UUID.

### AppointmentNote

The _AppointmentNote_ is a note that can be added to one or more appointments.

An _AppointmentNote_ has the following properties:

- **note**: A textual representation of the note.
- **type**: A choice of: "Primary", "Secondary", "OOO Reason", "OOO Note".

#### Endpoints

-  `GET /appointmentnotes/`: Retrieves a list of AppointmentNotes.
-  `POST /appointmentnotes/`: Creates a new AppointmentNote.
-  `GET /appointmentnotes/{id}/`: Retrieves a AppointmentNote by its ID.
-  `PUT /appointmentnotes/{id}/`: Updates the AppointmentNote with the given ID (all fields).
-  `PATCH /appointmentnotes/{id}/`: Updates the AppointmentNote with the given ID (only specified fields).
-  `DELETE /appointmentnotes/{id}/`: Deletes the AppointmentNote with the given ID.

### AppointmentNotification

The _AppointmentNotification_ is a representation of an E-Mail sent to an E-Mail-address.
The E-Mail will be sent on saving the _AppointmentNotification_ if ``send_notification`` is set and it was not sent before (``sent_at`` empty).
An _AppointmentNotification_ has the following properties:

- **subject**: The subject of the generated E-Mail.
- **message**: The subject of the generated E-Mail.
- **recipient**: The E-Mail address of the generated E-Mail.
- **sent_at**: A timestamp when the E-Mail was sent.
- **send_notification**: A boolean to activate the sending of the notification.
- **appointment**: A related `Appointment` instance.
- **org_phone**: The phone number of the organization.
- **org_name**: The name of of the related organization.

#### Endpoints

-  `GET /appointmentnotifications/`: Retrieves a list of AppointmentNotifications.
-  `POST /appointmentnotifications/`: Creates a new AppointmentNotification.
-  `GET /appointmentnotifications/{id}/`: Retrieves a AppointmentNotification by its ID.
-  `PUT /appointmentnotifications/{id}/`: Updates the AppointmentNotification with the given ID (all fields).
-  `PATCH /appointmentnotifications/{id}/`: Updates the AppointmentNotification with the given ID (only specified fields).
-  `DELETE /appointmentnotifications/{id}/`: Deletes the AppointmentNotification with the given ID.


[Click here for the full API documentation.](https://docs.walhall.io/api/marketplace/kupfer-contact-appointment-service)


## Local development

### Prerequisites

You must have [Docker](https://www.docker.com/) installed.

### Build & run service locally

Build the Docker image:

```bash
docker-compose build
```

Run a web server with this service:

```bash
docker-compose up
```

Now, open your browser and go to [http://localhost:8002](http://localhost:8002).

For the admin panel, go to [http://localhost:8002/admin](http://localhost:8002/admin)
(user: `admin`, password: `admin`).

The local API documentation can be consulted in `http://localhost:8002/docs`.

### Run tests

To run the tests once:

```bash
docker-compose run --rm --entrypoint 'bash scripts/run-tests.sh' crmservice
```

To run the tests and leave bash open inside the container so that it's possible to
re-run the tests faster again using `bash scripts/run-tests.sh [--keepdb]`:

```bash
docker-compose run --rm --entrypoint 'bash scripts/run-tests.sh --bash-on-finish' crmservice
```

To **run bash**:

```bash
docker-compose run --rm --entrypoint 'bash' crmservice
```

If you would like to clean the database and start the application, do:

```bash
docker-compose up --renew-anon-volumes --force-recreate --build
```

## API documentation (Swagger)

[Click here to go to the full API documentation.](https://docs.walhall.io/api/marketplace/kupfer-contact-appointment-service)

## License

Copyright &#169;2019 Humanitec GmbH.

This code is released under the [Humanitec Affero GPL](LICENSE).

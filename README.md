# crm_service

## Development

Build the image:

```bash
docker-compose build
```

Run the web server:

```bash
docker-compose up
```

Open your browser with URL `http://localhost:8080`.
For the admin panel `http://localhost:8080/admin`
(user: `admin`, password: `admin`).

Run the tests only once:

```bash
docker-compose run --rm --entrypoint 'bash scripts/run-tests.sh' crm_service
```

Run the tests and leave bash open inside the container, so it's possible to
re-run the tests faster again using `bash scripts/run-tests.sh [--keepdb]`:

```bash
docker-compose run --rm --entrypoint 'bash scripts/run-tests.sh --bash-on-finish' crm_service
```

To run bash:

```bash
docker-compose run --rm --entrypoint 'bash' crm_service
```

## Search service

### JWT-Keys

The public keys `'JWT_PUBLIC_KEY' + JWT_ISSUER` must match in
this service and in the search service, p.e.: `JWT_PUBLIC_KEY_RSA_CRMSERVICE`.

### Index

For writing, updating and deleting in the search service the Index in the
search service (URL: `settings.base.SEARCH_SERVICE_URL +
/admin/search/index/`) must be set according to
`settings.base.SEARCH_SERVICE_INDEX` and `settings.base.JWT_ISSUER`.
p.e.: `Name: contact ; Allowed services: crmservice`.

### Rules

Every Index will come with a rule added, so that the user can only contacts
of his organization. Therefore every `contact` must have its `organization_uuid`
set.

### Integration

For more info about integration see: https://github.com/Humanitec/search-service-integration

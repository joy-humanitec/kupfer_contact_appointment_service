# Data Import Guide

## Prerequirements

- a `CoreUser`-Account with the Organization, where the data should be imported to
- a `client_id` of the `bifrost.oauth2_provider.application` with which the CoreUser can login 
(/admin/oauth2_provider/application/)
- a `WorkflowLevel1` and its `id` and `uuid` to specify the target-WFL1
- the internal `BIFROST_URL` (on local like: URL_BIFROST = 'http://172.25.0.5:8080/')
- CSV-file to import with the correct format (first line are the headings and will be skipped)


## Recipe

1. Put the file onto the `crm_service`-pod, like:
    ```
    kubectl exec -n kupfer-dev -it crm-service-7fd7d57fd6-2qrlc bash
    mkdir -p data/crm_service
    exit
    kubectl cp data/crm_service/Data_Pletscher.csv kupfer-dev/crm-service-7fd7d57fd6-2qrlc:/code/data/crm_service/Data_Pletscher.csv
    ```

2. Fill out the data in the remote management-command-file:
    ```
    kubectl exec -n kupfer-dev -it crm-service-7fd7d57fd6-2qrlc bash
    apt-get update
    apt-get install vim -y
    vim import_csv/management/commands/import_csv.py
    ```    

3. Execute the command with the csv-file as an argument (default is: `TopKontor_Ritz.csv`):
    ```
    kubectl exec -n kupfer-dev -it crm-service-7fd7d57fd6-2qrlc bash
    python manage.py import_csv --file=Data_Pletscher.csv
    ```

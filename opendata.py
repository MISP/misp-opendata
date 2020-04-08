import argparse
import json
import requests
from datetime import datetime
from pymisp import ExpandedPyMISP, MISPAttribute, MISPEvent, MISPObject

_API_URL = 'https://data.public.lu/api/1/'
_DATASET_URL = 'https://data.public.lu/en/datasets/'


################################################################################
#                              UTILITY FUNCTIONS                               #
################################################################################

def _check_auth_fields(auth):
    with open(auth, 'rt', encoding='utf-8') as f:
        headers = json.loads(f.read())
    if 'Content-type' not in headers:
        headers['Content-type'] = 'application/json'
    return headers


def _check_dataset_fields(dataset: dict):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    dataset.update({key: now for key in ('created_at', 'last_modified', 'last_updated')})
    slug = dataset['slug']
    dataset['page'] = f'{_DATASET_URL}{slug}/'
    dataset['uri'] = f'{_DATASET_URL}datasets/{slug}/'


def _create_resource_url(action, response):
    if action == 'updated':
        dataset_id, _, resource_id = response.url.split('/')[-4:-1]
        return f'{_DATASET_URL}{dataset_id}/#resource-{resource_id}', response.url
    dataset_id = response.url.split('/')[-3]
    resource_id = response.json()["id"]
    return f'{_DATASET_URL}{dataset_id}/#resource-{resource_id}', f'{response.url}{resource_id}'


def _display_confirmation(action, feature, response):
    message = f'Your {feature} has been successfully {action}.\n'
    url, api_url = _create_dataset_url(action, response) if feature == 'dataset' else _create_resource_url(action, response)
    message = f'{message}It is available under the following link: {url}\n'
    print(f'{message}You can also find the json format equivalent: {api_url}')


def _display_error(response):
    print(f'Your query encountered an error:\n{response.status_code} - {response.reason} - {response.text}')


def _fill_url(key, value):
    if isinstance(value, list):
        return '/'.join(f'{key}:{val}' for val in value)
    return f'{key}:{value}'


def _check_resources_fields(body, resources, url):
    if 'filetype' not in resources:
        resources['filetype'] = 'remote'
    resources['format'] = body['returnFormat']
    misp_url = url if url.endswith('/') else f'{url}/'
    resources['url'] = f"{misp_url}{args.level}/restSearch/{'/'.join(_fill_url(key, value) for key, value in body.items())}"


def _get_resource_id(resources, title):
    for resource in resources:
        if resource['title'] == title:
            return resource['id']


def _send_delete_request(headers, to_delete, to_display):
    delete = requests.delete(f'{_API_URL}datasets/{to_delete}', headers=headers)
    if delete.status_code == 204:
        print(f'The dataset {to_display} has been deleted from the open data portal.')
    else:
        print(f'The dataset {to_display} has not been deleted. Status code: {delete.status_code} - {delete.text}')


################################################################################
#                          SPECIFIC PARSING FUNCTIONS                          #
################################################################################

def _create_dataset(auth, body, dataset, resources, misp_url, url):
    print('Create dataset:')
    if 'frequency' not in dataset:
        dataset['frequency'] = 'unknown'
    _check_resources_fields(body, resources, misp_url)
    dataset['resources'] = [resources]
    headers = _check_auth_fields(auth)
    response = requests.post(f'{_API_URL}datasets/', headers=headers, data=dataset)

 
def _create_resource(headers, resources, url):
    print('create resource')
    response = requests.post(url, headers=headers, json=resources)
    return response, 'created', 201


def _delete_dataset(auth, dataset):
    with open(auth, 'rt', encoding='utf-8') as f:
        headers = json.loads(f.read())
    _send_delete_request(headers, dataset, dataset)


def _delete_resources(auth, dataset_name, resources):
    with open(auth, 'rt', encoding='utf-8') as f:
        headers = json.loads(f.read())
    dataset = requests.get(f'{_API_URL}datasets/{dataset_name}')
    if dataset.status_code != 200:
        print(f'The dataset {dataset_name} you want to delete has not been found. Status code: {delete.status_code} - {delete.text}')
        return
    dataset = dataset.json()
    current_resources = (resource['title'] for resource in dataset['resources'])
    for resource in resources:
        if resource not in current_resources:
            print(f'The resource {resource} does not exist in the dataset {dataset_name}.')
            break
        for dataset_resource in dataset['resources']:
            if resource == dataset_resource['title']:
                _send_delete_request(headers, f'{dataset_name}/resources/{dataset_resource["id"]}', dataset_name)
                break


def _update_resource(dataset, headers, resources, url):
    resource_id = _get_resource_id(dataset['resources'], resources['title'])
    response = requests.put(f'{url}{resource_id}/', headers=headers, json=resources)
    return response, 'updated', 200


def _update_resources(auth, body, dataset, resources, misp_url):
    feature = 'resource'
    _check_resources_fields(body, resources, misp_url)
    headers = _check_auth_fields(auth)
    url = f'{_API_URL}datasets/{dataset["id"]}/resources/'
    match = any(resources['title'] == resource['title'] for resource in dataset['resources'])
    args = (headers, resources, url)
    response, action, status = _update_resource(dataset, *args) if match else _create_resource(*args)
    if response.status_code == status:
        _display_confirmation(action, feature, response)
    else:
        _display_error(response)


################################################################################
#                            MAIN PARSING FUNCTIONS                            #
################################################################################

def delete_data(auth, to_delete):
    if len(to_delete) == 1:
        _delete_dataset(auth, to_delete[0])
    else:
        dataset = to_delete[0]
        resources = to_delete[1:]
        _delete_resources(auth, dataset, resources)


def submit_data(args):
    recommandation = 'Please make sure the file exists and you have the right to open it.'
    try:
        with open(args.body, 'rt', encoding='utf-8') as f:
            body = json.loads(f.read())
    except (FileNotFoundError, PermissionError):
        print(f'The body file specified ({args.body}) cannot be opened. {recommandation}')
        return
    try:
        with open(args.setup, 'rt', encoding='utf-8') as f:
            setup = json.loads(f.read())
    except (FileNotFoundError, PermissionError):
        print(f'The setup file specified ({args.setup}) cannot be opened. {recommandation}')
        return
    # for feature, values in setup.items():
    #     locals()[feature] = values
    required_dataset_fields = ('title', 'description')
    required_resources_fields = ('title', 'type')
    for feature in ('dataset', 'resources'):
        if not any(required in setup[feature] for required in locals()[f'required_{feature}_fields']):
            print(f'Please make sure the {feature} you want to create/update contains at least one of the 2 required fields: {", ".join(locals()[f"required_{feature}_fields"])}')
            return
    slug = '-'.join(setup['dataset']['title'].lower().split(' '))
    url = f'{_API_URL}datasets/{slug}/'
    dataset = requests.get(url)
    if dataset.status_code == 200:
        _update_resources(args.auth, body, dataset.json(), setup['resources'], args.url, url)
    else:
        dataset = setup['dataset']
        dataset['slug'] = slug
        _create_dataset(args.auth, body, dataset, setup['resources'], args.url, url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export a restSearch collection of data as feed.')
    parser.add_argument('--level', default='events', help='Level to query, in order to define the relative path.')
    parser.add_argument('--body', default='body.json', help='Path to the file containing the body of the query.')
    parser.add_argument('--setup', default='setup.json', help='Path to the file containing the dataset and resource names.')
    parser.add_argument('--url', default='https://misppriv.circl.lu', help='Url of the MISP instance.')
    parser.add_argument('--auth', default='auth.json', help='Path to the file containing the authentication required for the opendata portal (API key)')
    parser.add_argument('-d', '--delete', nargs='+', help='Delete a specific dataset or some ressources for a dataset')
    args = parser.parse_args()
    if args.delete:
        delete_data(args.auth, args.delete)
    else:
        submit_data(args)

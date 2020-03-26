import argparse
import json
import requests
from pymisp import ExpandedPyMISP, MISPAttribute, MISPEvent, MISPObject

_API_URL = 'https://data.public.lu/api/1/'


def _check_resources_fields(body, resources, url):
    if 'filetype' not in resources:
        resources['filetype'] = 'remote'
    print(body)
    resources['format'] = body['returnFormat']
    misp_url = url if url.endswith('/') else f'{url}/'
    resources['url'] = f"{misp_url}{args.level}/restSearch/{'/'.join(f'{key}:{value}' for key, value in body.items())}"
    print(resources['url'])


def _create_dataset(auth, body, dataset, resources, misp_url, url):
    print('Create dataset:')
    if 'frequency' not in dataset:
        dataset['frequency'] = 'unknown'
    _check_resources_fields(body, resources, misp_url)
    dataset['resources'] = [resources]
    with open(auth, 'rt', encoding='utf-8') as f:
        headers = json.loads(f.read())
    if 'Content-type' not in headers:
        headers['Content-type'] = 'application/json'
    oui = requests.post(f'{_API_URL}datasets', headers=headers, data=dataset)
    print(oui.status_code)
    print(oui.text)


def _delete_dataset(auth, dataset):
    with open(auth, 'rt', encoding='utf-8') as f:
        headers = json.loads(f.read())
    delete = requests.delete(f'{_API_URL}datasets/{dataset}', headers=headers)
    if delete.status_code == 204:
        print(f'The dataset {dataset} has been deleted from the open data portal.')
    else:
        print(f'The dataset {dataset} has not been deleted. Status code: {delete.status_code} - {delete.text}')


def _delete_resources(auth, dataset, resources):
    print(auth)
    print(dataset)
    print(resources)
    return


def _update_resources(auth, body, dataset, resources, misp_url, url):
    print('Update resources:')
    print(dataset)
    print(resources)
    print(url)


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
    required_dataset_fields = ('id', 'slug')
    required_resources_fields = ('title', 'type')
    for feature in ('dataset', 'resources'):
        if not any(required in setup[feature] for required in locals()[f'required_{feature}_fields']):
            print(f'Please make sure the {feature} you want to create/update contains at least one of the 2 required fields: {", ".join(locals()[f"required_{feature}_fields"])}')
            return
    url = f'{_API_URL}datasets/{setup["dataset"]["slug" if "slug" in setup["dataset"] else "id"]}'
    dataset = requests.get(url)
    print(dataset.status_code)
    if dataset.status_code == 200:
        _update_resources(args.auth, body, dataset, setup['resources'], args.url, url)
    else:
        _create_dataset(args.auth, body, setup['dataset'], setup['resources'], args.url, url)


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

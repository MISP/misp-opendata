import argparse
import json
import requests
from datetime import datetime

_API_URL = 'https://data.public.lu/api/1/'
_RESOURCE_HASH_FIELDS = (
    'md5',
    'sha1',
    'sha256'
)
_RESOURCE_OPTIONAL_FIELDS = (
    'filesize',
    'mime_type'
)
_RESOURCE_REQUIRED_FIELDS = (
    'title',
    'type',
    'url',
    'format'
)
_RESOURCE_TYPES = (
    'api',
    'code',
    'documentation',
    'main',
    'other',
    'update'
)


def fetch_dataset(datasets, title, feature):
    for dataset in datasets:
        if dataset['title'] == title:
            return f"There is a match in your {feature} datasets:\n{json.dumps(dataset, indent=4)}\n"
    return f"No dataset with the specified title in your {feature} datasets."


def parse_publication_date(publication_date):
    try:
        datetime.strptime(publication_date, '%Y-%m-%d')
        return publication_date
    except ValueError:
        pass
    try:
        datetime.strptime(publication_date, '%Y-%m-%dT%H:%M:%S')
        return publication_date
    except ValueError:
        print(f'Your publication_date value {publication_date} is not in a standard datetime format, please express it in one of the following format: %Y-%m-%d or %Y-%m-%dT%H:%M:%S')


def search_dataset(args):
    if args.slug is not None:
        dataset = requests.get(f"{_API_URL}datasets/{args.slug}")
        if dataset.status_code == 200:
            dataset = dataset.json()
            print(f"There is a match for your request:{json.dumps(dataset, indent=4)}")
        else:
            print(f"Error while querying the opendata portal: {dataset.text}")
    else:
        if args.auth is None:
            print('The API key is required if you want to search for your own datasets')
            return
        auth = {'X-API-KEY': args.auth}
        own_datasets = requests.get(f"{_API_URL}me/datasets", headers=auth)
        if own_datasets.status_code == 200:
            print(fetch_dataset(own_datasets.json(), args.title, 'own'))
        else:
            print(f'Unable to get your own datasets: {own_datasets.text}')
        org_datasets = requests.get(f"{_API_URL}me/org_datasets", headers=auth)
        if org_datasets.status_code == 200:
            print(fetch_dataset(org_datasets.json(), args.title, 'org'))
        else:
            print(f'Unable to get your org datasets: {own_datasets.text}')

def submit_resource(args):
    auth = {'X-API-KEY': args.auth}
    resource = {field: getattr(args, field) for field in _RESOURCE_REQUIRED_FIELDS}
    resource['filetype'] = 'remote'
    resource['description'] = args.description if args.description is not None else args.title
    for field in _RESOURCE_OPTIONAL_FIELDS:
        if getattr(args, field) is not None:
            resource[field] = getattr(args, field)
    if args.publication_date is not None:
        publication_date = parse_publication_date(args.publication_date)
        if publication_date is not None:
            resource['published'] = publication_date
    for field in _RESOURCE_HASH_FIELDS:
        if getattr(args, field) is not None:
            resource['checksum'] = {'type': field, 'value': getattr(args, field)}
            break
    submission = requests.post(f"{_API_URL}datasets/{args.dataset_id}/resources/", headers=auth, json=resource)
    if submission.status_code == 201:
        print('Resource successfully added to the given dataset')
    else:
        print(f'Error while submitting your resource:\n - Status code:{submission.status_code}\n - Reason: {submission.reason}\n - Raw text: {submission.text}')




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Submit resources on data.public.lu')
    subparsers = parser.add_subparsers()

    submit_parser = subparsers.add_parser('submit', help='Submit a resource.')
    submit_parser.add_argument('--auth', required=True, help='API key.')
    submit_parser.add_argument('--dataset_id', required=True, help='Dataset ID.')
    submit_parser.add_argument('--title', required=True, help='Resource title.')
    submit_parser.add_argument('--type', required=True, choices=_RESOURCE_TYPES, help='Resource type.')
    submit_parser.add_argument('--url', required=True, help='Resource URL.')
    submit_parser.add_argument('--format', required=True, help='Resource format.')
    submit_parser.add_argument('--description', help='Resource description. If None, the resource title will be used.')
    submit_parser.add_argument('--publication_date', help='Publication date of the resource, in a standard datetime format.')
    submit_parser.add_argument('--filesize', type=int, help='Resource file size in bytes.')
    submit_parser.add_argument('--mime_type', help='Resource mime type.')
    checksum = submit_parser.add_mutually_exclusive_group()
    checksum.add_argument('--md5', help='Resource file MD5 hash.')
    checksum.add_argument('--sha1', help='Resource file SHA1 hash.')
    checksum.add_argument('--sha256', help='Resource file SHA256 hash.')
    submit_parser.set_defaults(func=submit_resource)

    search_parser = subparsers.add_parser('search', help='Search for a dataset.')
    identifier = search_parser.add_mutually_exclusive_group(required=True)
    identifier.add_argument('--title', help='Dataset title.')
    identifier.add_argument('--slug', help='Dataset slug (unique identifier generated with the dataset title).')
    search_parser.add_argument('--auth', help='API key.')
    search_parser.set_defaults(func=search_dataset)

    args = parser.parse_args()
    try:
        args.func(args)
    except:
        parser.print_help()
        parser.exit()


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
_RESOURCE_SEARCH_FIELDS = (
    'resource_id',
    'resource_title'
)
_RESOURCE_TYPES = (
    'api',
    'code',
    'documentation',
    'main',
    'other',
    'update'
)


def display_error(result):
    return f' - Status code: {result.status_code}\n - Reason: {result.reason}\n - Raw text: {result.text}'


def fetch_dataset(datasets, title, feature):
    for dataset in datasets:
        if dataset['title'] == title:
            return f"There is a match in your {feature} datasets:\n{json.dumps(dataset, indent=4)}\n"
    return f"No dataset with the specified title in your {feature} datasets."


def get_dataset(authentication_key, title):
    auth = {'X-API-KEY': authentication_key}
    for feature in ('datasets', 'org_datasets'):
        datasets = requests.get(f"{_API_URL}me/{feature}/", headers=auth)
        if datasets.status_code != 200:
            print(f"Error while searching for your {feature}: {datasets.reason}\n{datasets.text}")
            continue
        for dataset in datasets.json():
            if dataset['title'] == title:
                return dataset
    print(f"You don't have any dataset with the specified title ({title}).")


def parse_publication_date(date):
    for regex in _DATETIME_REGEXES:
        try:
            datetime.strptime(date, regex)
            return date
        except ValueError:
            continue
    print(f"Your publication_date value ({date}) is not in a standard datetime format, please use one of the following format: {', '.join(_DATETIME_REGEXES)}")


def search_dataset(args):
    if args.dataset_title is not None:
        if args.auth is None:
            print('The API key is required if you want to search for a dataset using its title')
            return
        dataset = get_dataset(args.auth, args.dataset_title)
        if dataset is None:
            return
        if any(getattr(args, field) is not None for field in _RESOURCE_SEARCH_FIELDS):
            for field in _RESOURCE_SEARCH_FIELDS:
                value = getattr(args, field)
                if value is None:
                    continue
                feature = field.split('_')[1]
                for resource in dataset['resources']:
                    if resource[feature] == value:
                        print(f"Successfully found the requested resource:\n{json.dumps(resource, indent=4)}")
                        return
            print(f"No result for the resource you requested, here is the full dataset instead:{json.dumps(dataset, indent=4)}")
        else:
            print(f"Successfully found the requested dataset:\n{json.dumps(dataset, indent=4)}")
    else:
        query = f"datasets/{args.dataset_id if args.dataset_id is not None else args.dataset_slug}/"
        if args.resource_id is not None:
            resource = requests.get(f"{_API_URL}{query}resources/{args.resource_id}/")
            if resource.status_code == 200:
                print(f"Successfully found the requested resource:\n{json.dumps(resource.json(), indent=4)}")
            else:
                print(f"Error while searching the requested resource:\n{display_error(resource)}")
        else:
            dataset = requests.get(f"{_API_URL}{query}/")
            if dataset.status_code == 200:
                if args.resource_title is not None:
                    for resource in dataset.json()['resources']:
                        if resource['title'] == args.resource_title:
                            print(f"Successfully found the requested resource:\n{json.dumps(resource, indent=4)}")
                            return
                    print("No result for the resource you requested, here is the full dataset instead:")
                else:
                    print("Successfully found the requested dataset:")
                print(json.dumps(dataset.json(), indent=4))
            else:
                print(f"Error with the requested dataset:\n{display_error(dataset)}")


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
    dataset_identifier = search_parser.add_mutually_exclusive_group(required=True)
    dataset_identifier.add_argument('--dataset_title', help='Dataset title.')
    dataset_identifier.add_argument('--dataset_slug', help='Dataset slug (unique identifier generated with the dataset title).')
    dataset_identifier.add_argument('--dataset_id', help='Dataset ID.')
    search_parser.add_argument('--auth', help='API key.')
    resource_identifier = search_parser.add_mutually_exclusive_group()
    resource_identifier.add_argument('--resource_id', help='Resource ID.')
    resource_identifier.add_argument('--resource_title', help='Resource title')
    search_parser.set_defaults(func=search_dataset)

    args = parser.parse_args()
    args.func(args)


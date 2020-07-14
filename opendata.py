import argparse
import json
import pathlib
import requests
import sys
from datetime import datetime
# from pymisp import ExpandedPyMISP, MISPAttribute, MISPEvent, MISPObject

_ABSOLUTE_PATH = pathlib.Path(__file__).parent.absolute()


class OpendataExport():
    def __init__(self, auth, url):
        self._auth = auth
        self._auth['Content-type'] = 'application/json'
        self._api_url = f'{url}api/1/'
        self._dataset_url = f'{url}en/datasets'

    def parse_arguments(self, args):
        self.level = args.level
        self.misp_url = args.misp_url
        recommandation = 'Please make sure the file exists and you have the right to open it.'
        for feature in ('body', 'setup'):
            filename = getattr(args, feature) if getattr(args, feature) is not None else f'{_ABSOLUTE_PATH}/{feature}.json'
            try:
                with open(filename, 'rt', encoding='utf-8') as f:
                    setattr(self, feature, json.loads(f.read()))
            except (FileNotFoundError, PermissionError):
                sys.exit(f'The {feature} file specified ({filename}) cannot be opened. {recommandation}')

    ################################################################################
    #                            MAIN PARSING FUNCTIONS                            #
    ################################################################################

    def delete_data(self, to_delete):
        if len(to_delete) == 1:
            self._send_delete_request(to_delete[0], to_delete[0])
        else:
            dataset = to_delete[0]
            resources = to_delete[1:]
            self._delete_resources(dataset, resources)

    def submit_data(self):
        required_dataset_fields = ('title', 'description')
        required_resources_fields = ('title', 'type')
        for feature in ('dataset', 'resources'):
            if feature in self.setup and not any(required in self.setup[feature] for required in locals()[f'required_{feature}_fields']):
                print(f'Please make sure the {feature} you want to create/update contains at least one of the 2 required fields: {", ".join(locals()[f"required_{feature}_fields"])}')
                return
        slug = '-'.join(self.setup['dataset']['title'].lower().split(' '))
        url = f'{self._api_url}datasets/{slug}/'
        dataset = requests.get(url)
        if dataset.status_code == 200:
            if 'resources' in self.setup:
                self._update_resources(dataset.json())
            else:
                self._update_dataset(dataset.json()['id'])
        else:
            self.setup['dataset']['slug'] = slug
            self._create_dataset()

    ################################################################################
    #                          SPECIFIC PARSING FUNCTIONS                          #
    ################################################################################

    def _create_dataset(self):
        self._check_dataset_fields()
        dataset = self.setup['dataset']
        if self.setup.get('resources'):
            self._check_resources_fields()
            dataset['resources'] = [self.setup['resources']]
        response = requests.post(f'{self._api_url}datasets/', headers=self._auth, json=dataset)
        self._handle_response('created', 'dataset', response, 201)

    def _create_resource(self, url):
        response = requests.post(url, headers=self._auth, json=self.setup['resources'])
        return response, 'created', 201

    def _delete_resources(self, dataset_name, resources):
        dataset = requests.get(f'{self._api_url}datasets/{dataset_name}')
        if dataset.status_code != 200:
            print(f'The dataset {dataset_name} you want to delete has not been found. Status code: {delete.status_code} - {delete.text}')
            return
        dataset = dataset.json()
        current_resources = tuple(resource['title'] for resource in dataset['resources'])
        for resource in resources:
            if resource not in current_resources:
                print(f'The resource {resource} does not exist in the dataset {dataset_name}.')
                break
            for dataset_resource in dataset['resources']:
                if resource == dataset_resource['title']:
                    self._send_delete_request(f'{dataset["id"]}/resources/{dataset_resource["id"]}', resource, feature='resource')
                    break

    def _update_dataset(self, dataset_id):
        response = requests.put(f'{self._api_url}datasets/{dataset_id}/', headers=self._auth, json=self.setup['dataset'])
        self._handle_response('updated', 'dataset', response, 200)

    def _update_resource(self, dataset, url):
        resource_id = self._get_resource_id(dataset['resources'], self.setup['resources']['title'])
        response = requests.put(f'{url}{resource_id}/', headers=self._auth, json=self.setup['resources'])
        return response, 'updated', 200

    def _update_resources(self, dataset):
        self._check_resources_fields()
        url = f'{self._api_url}datasets/{dataset["id"]}/resources/'
        match = any(self.setup['resources']['title'] == resource['title'] for resource in dataset['resources'])
        response, action, status = self._update_resource(dataset, url) if match else self._create_resource(url)
        self._handle_response(action, 'resource', response, status)

    ################################################################################
    #                              UTILITY FUNCTIONS                               #
    ################################################################################

    def _send_delete_request(self, to_delete, to_display, feature='dataset'):
        delete = requests.delete(f'{self._api_url}datasets/{to_delete}', headers=self._auth)
        if delete.status_code == 204:
            print(f'The {feature} {to_display} has been deleted from the open data portal.')
        else:
            print(f'The {feature} {to_display} has not been deleted. Status code: {delete.status_code} - {delete.text}')

    def _check_dataset_fields(self):
        if 'frequency' not in self.setup['dataset']:
            self.setup['dataset']['frequency'] = 'unknown'
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        self.setup['dataset'].update({key: now for key in ('created_at', 'last_modified', 'last_updated')})
        slug = self.setup['dataset']['slug']
        self.setup['dataset']['page'] = f'{self._dataset_url}{slug}/'
        self.setup['dataset']['uri'] = f'{self._dataset_url}datasets/{slug}/'

    def _check_resources_fields(self):
        for feature, value in zip(('filetype', 'format'), ('remote', 'json')):
            if feature not in self.setup['resources']:
                self.setup['resources'][feature] = value
        misp_url = self.misp_url if self.misp_url.endswith('/') else f'{self.misp_url}/'
        self.setup['resources']['url'] = f"{misp_url}{self.level}/restSearch/{'/'.join(self._fill_url(key, value) for key, value in self.body.items())}"

    def _create_dataset_url(self, action, response):
        dataset_id = response.json()['id']
        api_url  = response.url if action == 'updated' else f'{response.url}{dataset_id}/'
        return f'{self._dataset_url}{dataset_id}/', api_url


    def _create_resource_url(self, action, response):
        if action == 'updated':
            dataset_id, _, resource_id = response.url.split('/')[-4:-1]
            return f'{self._dataset_url}{dataset_id}/#resource-{resource_id}', response.url
        dataset_id = response.url.split('/')[-3]
        resource_id = response.json()["id"]
        return f'{self._dataset_url}{dataset_id}/#resource-{resource_id}', f'{response.url}{resource_id}'

    def _display_confirmation(self, action, feature, response):
        message = f'Your {feature} has been successfully {action}.\n'
        url, api_url = self._create_dataset_url(action, response) if feature == 'dataset' else self._create_resource_url(action, response)
        message = f'{message}It is available under the following link: {url}\n'
        print(f'{message}You can also find the json format equivalent: {api_url}')

    @staticmethod
    def _display_error(response):
        print(f'Your query encountered an error:\n{response.status_code} - {response.reason} - {response.text}')

    @staticmethod
    def _fill_url(key, value):
        if isinstance(value, list):
            return '/'.join(f'{key}[]:{val}' for val in value)
        return f'{key}:{value}'

    @staticmethod
    def _get_resource_id(resources, title):
        for resource in resources:
            if resource['title'] == title:
                return resource['id']

    def _handle_response(self, action, feature, response, status_code):
        if response.status_code == status_code:
            self._display_confirmation(action, feature, response)
        else:
            self._display_error(response)


def _check_portal_arguments(auth_arg, url_arg):
    portal_url = None
    with open(f'{_ABSOLUTE_PATH}/supported_portals.json', 'rt', encoding='utf-8') as f:
        supported_portals = json.loads(f.read())
    for supported_portal in supported_portals:
        if url_arg in supported_portal:
            portal_url = supported_portal
            break
    if not portal_url:
        portal_urls = '\n'.join(supported_portals)
        sys.exit(f'The provided portal url is not supported yet (or misspelled).\nPlease choose one of the followings:\n{portal_urls}')
    if auth_arg is not None:
        with open(f'{_ABSOLUTE_PATH}/auth.json', 'rt', encoding='utf-8') as f:
            authentication = json.loads(f.read())
        return authentication, portal_url
    return {"X-API-KEY": auth_arg}, portal_url


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export a restSearch collection of data as feed.')
    parser.add_argument('--level', default='events', help='Level to query, in order to define the relative path.')
    parser.add_argument('--body', help='Body of the query. (using body.json file if not set)')
    parser.add_argument('--setup', help='Setup of the query containing the dataset (and resource) name(s). (using setup.json file if not set)')
    parser.add_argument('--misp_url', default='https://misppriv.circl.lu', help='Url of the MISP instance.')
    parser.add_argument('--portal_url', default='data.public.lu', help='Url of the Open data portal.')
    parser.add_argument('--auth', help='Authentication required for the opendata portal (API key). (using auth.json file if not set)')
    parser.add_argument('-d', '--delete', nargs='+', help='Delete a specific dataset or some ressources for a dataset')
    args = parser.parse_args()
    auth, portal_url = _check_portal_arguments(args.auth, args.portal_url)
    print(portal_url)
    opendata_export = OpendataExport(auth, portal_url)
    if args.delete:
        opendata_export.delete_data(args.delete)
    else:
        opendata_export.parse_arguments(args)
        opendata_export.submit_data()

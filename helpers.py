#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests

_API_URL = 'https://data.public.lu/api/1/'


def _filter_resources(datasets: list, value: str, feature: str) -> list:
    for dataset in datasets:
        if dataset[feature] == value:
            return dataset['resources']


def get_me(headers: dict) -> dict:
    me = requests.get(f'{_API_URL}me', headers=headers)
    return me.json()


def get_my_datasets(headers: dict) -> list:
    me = get_me(headers)
    if len(me) == 1 and 'message' in me:
        print(f'An error during your query to "{_API_URL}me" has been raised: {me["message"]}')
        return
    my_datasets = requests.get(f'{_API_URL}datasets/?owner={me["id"]}')
    return my_datasets.json()['data']


def get_resources(headers: dict, id: str=None, slug: str=None) -> list:
    if id is None and slug is None:
        print('Please define an identifier (id or slug field) for the dataset you want to get the resources about.')
        return
    my_datasets = get_my_datasets(headers)
    return _filter_resources(my_datasets, id, 'id') if id is not None else _filter_resources(my_datasets, slug, 'slug')

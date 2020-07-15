# Opendata

### Description

This small piece of code can be used to query Open data portals (like [data.public.lu](https://data.public.lu)) in order to create, update or delete a dataset or a resource. All the resources created are pointing to restSearch queries in MISP, giving access to the actual data shared in the given MISP server.  
(_The list of supported portals will be extended to support more and more european opendata portals._)

The [opendata.py](opendata.py) python script provides the necessary functionalities to interact with opendata portals. It is used and called by MISP to make the features available from any MISP server, but it also works as a standalone functionality. Details about its usage are provided below.

#### The Opendata format

The opendata format provides metadata information describing the datasets and resources stored within the portal.

**Datasets** are the containers used to give a general description of the data stored within the resources.  
A dataset has some mandatory fields that must be defined by its creator:
- **title**: A one sentence description to identity the purpose of the dataset
- **description**: A short description giving more details about the dataset
- **update frequency**: The frequency of update for the dataset

Some extra mandatory fields are generated by the portal at the creation or update of the dataset, like the creation date, the date of last modification or update, the url to the dataset, etc.  
Alongside those required fields, users can also add some optional pieces of information to add more specifications to the dataset, like an acronym, the license used, a temportal or spatial coverage, or the resources.

A dataset has 2 identifiers:
- **id**: The unique id of the dataset that is set at the creation of the dataset and never changes
- **slug**: The dataset permalink string (its title in lowercase separated by dashes)

Both of those identifiers can be used in a link to access to a dataset.

**Resources** are the containers used within datasets to describe each data collection.  
A resource also has mandatory fields:
- **title**: A one sentence description of the data resource
- **type**: The resource type (documentation, main file, API, ...)
- **url**: URL to the data itself
- **format**: Format of the data

As for datasets, some optional fields can also be defined for resources, such as the description of the resource, its release date, its size in bytes, its mime type, etc.

A resource is identified by a unique **id**, that is set at the creation of the resource and never changes.

A dataset can contain multiple resources, and a resource always belongs to a dataset. You can find more information about the format, and the different fields within the [References part](#References)

----

### Requirements

For an optimal usage, the following features are required:
- **Python 3.6+**
- An access to a MISP instance that is available out of you localhost network (127.0.0.1 and localhost being not valid addresses in the open data portal)
- An account in the open data portal with an API key to copy in the [auth.json](auth.json) document
- _Some filters to add in the [body.json](body.json) document to avoid sharing the full data available in your MISP instance are highly recommended_

For the creation or update of datasets or resources, some json documents are required:
- [auth.json](auth.json) contains the information to identify the user connecting to the portal API in order to define the rights to create or update each data structure.
- [body.json](body.json) contains some filters used in the MISP restSearch, which helps defining the url that is going to be shared into the platform and pointing to the data.
- [setup.json](setup.json) is the last required json document containing the fields and values describing the dataset / resource we want to create or update.

When it is about deleting a dataset or a resource, only the [body.json](body.json) document requirement still stands, and you need to know the identifier or the dataset and/or resource(s) you want to delete.

The filters defined by default in the last mentioned document, available as an example, are some of the requirement in MISP side (returnFormat) and a usefull tag filter to avoid sharing data the is not public. Please read the references you can find below for more information about filtering data with the built-in restSearch API in MISP.

The fields defined in the setup document are the minimum requirements to make any API query a success (some of the required fields are defined in the python script and are thus not mandatory in the json document). Please refer also to the below mentioned documentation about the open data API for more explanations about the fields and the requirements.

----

### Usage

The script uses a couple of different parameters in order to define the values associated with the required dataset/resource fields, the API key that should be used, and the kind of data from MISP that is going to be shared. For those 3 features, 3 different parameters are defined and pointing by default to the file names of the 3 json documents already mentioned above. The user can use some different ones as long as the content of the json document(s) used meet the requirements.

Another important parameter is the url of the MISP instance to use as resource for the actual data described in the open data resources. This url also has a default value that can be overwritten by user while executing the script.  
The url value set by default is `misppriv.circl.lu` but you can choose any MISP server you have access to and that you want to use to share data, using the `--misp_url` parameter.

As you can now choose which portal you want to query, there is also a default value for this feature, which is `data.public.lu`, but again you can query any of the [supported portals](https://github.com/MISP/misp-opendata/blob/main/supported_portals.json) (An [overview of the current progression for the support of some Open data platforms](https://github.com/MISP/misp-opendata/blob/main/portals_support.md) is also available) by using the `--portal_url` parameter.

The last parameter is the type of data that should be used as data in MISP (attributes or events). This one defines the level of data in MISP to be used as data resource. In other words, do we want the open data resource url to point to MISP events containing at least 1 attribute matching the restSearch filters define in the body.json document? Or simply the single attributes matching those filters?

Alternatively, there is an option to delete a dataset and/or its resource(s).

For the following examples, we will consider we want to make available in the open data portal some MISP collections of data containing single attributes of x509 certificates tagged as tlp:white.

#### Create a dataset

_In this case, the dataset with the title mentioned as example does not exist yet._

- Python command
```
python3 opendata.py --level attributes --misp_url _YOUR_MISP_URL_ --portal_url data.public.lu
```

- body.json
```
{
    "type": "x509-fingerprint-md5",
    "tags": "tlp:white"
}
```
(In this case and all the followings, we could also use multiple values for the type filter, like `["x509-fingerprint-md5", "x509-fingerprint-sha1"]`)

- setup.json
```
{
    "dataset": {
        "description": "Dataset test from MISP containing data shared via a MISP platform.",
        "title": "x509 certificates shared in MISP"
    },
    "resources": {
        "title": "All x509 certificates shared with MISP",
        "type": "api"
    }
}
```
Keep in mind that skipping the `resources` field will simply create the dataset, and creating a resource in the same dataset later is possible (see above under **Create a resource**).

#### Update a dataset

_Only if the dataset with the title mentioned already exists._

- Same python command and content in body.json

- setup.json
```
{
    "dataset": {
        "description": "Dataset test from MISP containing data shared via a MISP platform.",
        "title": "x509 certificates shared in MISP"
    }
}
```
In this case only `dataset` should be set, otherwise with the `resources` field, it would create/update the resource instead of the dataset.

#### Create a resource

_Only if the dataset with the title mentioned already exists, but not the resource with the title mentioned._

- Same python command and content in body.json

- setup.json
```
{
    "dataset": {
        "description": "Dataset test from MISP containing data shared via a MISP platform.",
        "title": "x509 certificates shared in MISP"
    },
    "resources": {
        "title": "All x509 certificates shared with MISP",
        "type": "api"
    }
}
```
Since we consider the dataset already exists, but not the resource, using this setup will create the new resource.

#### Update a resource

_Only if the dataset and resource with the titles mentioned already exist._

- Same python command and content in body.json

- Same content in setup.json as just above in **Create a resource**

#### Delete a dataset

- Python command
```
python3 opendata.py --portal_url data.public.lu -d _DATASET_IDENTIFIER_
```
Please note the dataset identifier is either its `id` or its permalink identifier (`slug`)

- No body.json nor setup.json content required

#### Delete at least one resource

- Python command
```
python3 opendata.py --portal_url data.public.lu -d _DATASET_IDENTIFIER_ _RESOURCE_IDENTIFIER_ [_RESOURCE_IDENTIFIER_]
```
Both the dataset and resource identifiers are either their `id` or their permalink indentifiers (`slug`). You can delete either 1 resource, or as many as possible in one single execution.

- No body.json nor setup.json content required

----

### Usage in MISP

The functionality of creating, updating or deleting datasets and resources is now available in MISP via its restSearch client.

#### Creation and update

We can then use the same example as before and query the opendata portal to create or update a dataset or one of its resource(s).

Example of creation or update of a resource within the given dataset:
```
{
    "returnFormat": "opendata",
    "type": "x509-fingerprint-md5",
    "tags": "tlp:white",
    "auth": "_YOUR_OPENDATA_PORTAL_API_KEY_",
    "setup": {
        "dataset": {
            "description": "Dataset test from MISP containing data shared via a MISP platform.",
            "title": "x509 certificates shared in MISP"
        },
        "resources": {
            "title": "All x509 certificates shared with MISP",
            "type": "api",
            "format": "json"
        }
    },
    "misp-url": "https://mispriv.circl.lu",
    "portal-url": "data.public.lu"
}
```

#### Deletion

It is also possible to delete a dataset or its resource(s) using the restSearch client in MISP.

Example of deletion of resources:
```
{
    "returnFormat": "opendata",
    "auth": "_YOUR_OPENDATA_PORTAL_API_KEY_",
    "setup": {
        "dataset": "x509 certificates shared in MISP",
        "resources": [
            "x509 certificates (sha256) shared with MISP",
            "x509 certificates (sha1) shared with MISP",
            "x509 certificates (md5) shared with MISP"
        ],
    },
    "delete": 1,
    "portal-url": "data.public.lu"
}
```

----

### References

- [data.public.lu API Documentation](https://data.public.lu/fr/apidoc/)
- [MISP Search API Documentation](https://github.com/MISP/misp-book/tree/master/automation#search)

![logo](en_cef.png)

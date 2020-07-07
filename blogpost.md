# Publish data on Open data portals with MISP

## The Open data format

Open data defines the idea of making some data freely available for everyone to use with a possibility of redistribution in any form.  
The open data format provides metadata information describing the datasets and resources stored within the portal.

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
A dataset also has mandatory fields:
- **title**: A one sentence description of the data resource
- **type**: The resource type (documentation, main file, API, ...)
- **url**: URL to the data itself
- **format**: Format of the data

As for datasets, some optional fields can also be defined for resources, such as the description of the resource, its release date, its size in bytes, its mime type, etc.

A resource is identified by a unique **id**, that is set at the creation of the resource and never changes.

A dataset can contain multiple resources, and a resource always belongs to a dataset. You can find more information about the format, and the different fields within the [References part](#references)

----

## Use MISP to create, modify or delete data

MISP can be used to make any collection of data from a given MISP server available on an open data portal.  
To do so, the MISP Search API is used (documentation available within the [References part](#references) as well).  
Users can then create, modify or delete any dataset or resource (as long as they have the right to do so) in the chosen portal.

#### General instructions

Regardless of which use case you want to try out, there is a few instructions that must be considered in order to make the interaction with the Open data portal work.

The way the interaction is made with the portal in MISP is to use its API.  
Some API queries, essentially GET calls, are available for everyone and does not require an authentication.  
In our case, we always modify already existing content or create new content on the portal, and the portal requires then to know who the data to modify belongs to or who will the created data belong to.  
Thus, an API key will always be needed in order to authenticate to the Open data portal.  
This API key will be provided in your MISP Search queries within the `auth` field (See examples below)

The Open data feature on MISP only supports the Luxembourgish portal for now (notes on the future improvement available [here](#future-improvement)), but as soon as more portals will be supported too, the corresponding url will also be required.

#### Create a dataset with a resource

Publishing data on an Open data portal means creating both a dataset and its resource (details of the format available above within the [Open data format](#the-open-data-format) part).

----

## Future improvement

## References

- [data.public.lu API Documentation](https://data.public.lu/fr/apidoc/)
- [MISP Search API Documentation](https://github.com/MISP/misp-book/tree/master/automation#search)

![logo](en_cef.png)
# Pleiades Wayfinder

- [x] Load Pleiades dataset from JSON
- [x] For a given Pleiades place find proximal places (radius & quantity as criteria)
    - [x] implies we have a gridded spatial index or some other mechanism for finding nearby places 
- [ ] cull a list of Pleiades places against linked places in itiner-e
- [x] For a list of Pleiades places, interrogate the itiner-e API for the subset of those that can be reached via the transport route 
    - [ ] find the shortest subset route of each unique route group
- [ ] produce a JSON file of each route-proximal place to the starting place
- [ ] integrate platformdirs to facilitate cross-run caching without cluttering up the package space

## itiner-e api request

### What we have:

```
{

  "preferredRouteTypes": [],

  "transportationType": "foot",

  "routeCost": "fastest",

  "month": "jan",

  "paths": [{

      "pointA": {

        "pleiadesPlaceId": 423025

      },

      "pointB": {

        "pleiadesPlaceId": 727070

      }

    }

  ]

}
```

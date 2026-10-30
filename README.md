# Pleiades Wayfinder

- [ ] Load Pleiades dataset from JSON
- [ ] For a given Pleiades place find proximal places (radius & quantity as criteria)
- [ ] cull a list of Pleiades places against linked places in itiner-e
- [ ] For a list of Pleiades places, interrogate the itiner-e API for the subset of those that can be reached via the transport route 
    - [ ] find the shortest subset route of each unique route group
- [ ] produce a JSON file of each route-proximal place to the starting place

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

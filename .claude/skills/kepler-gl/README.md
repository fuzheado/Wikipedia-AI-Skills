# Kepler.gl Skill

A comprehensive skill for creating interactive geospatial visualizations of Wikimedia data using Kepler.gl.

## Overview

This skill provides tools and templates for visualizing Wikipedia articles, Wikimedia Commons media, and Wikidata entities on interactive maps. It covers data extraction, GeoJSON conversion, React integration, and various visualization patterns.

## Features

- **SPARQL to GeoJSON conversion**: Convert Wikidata queries to GeoJSON format
- **React integration templates**: Pre-configured Kepler.gl components
- **Layer type examples**: Point, hexagon, heatmap, arc, and polygon layers
- **Saved configurations**: Ready-to-use map configurations
- **Sample data**: Example GeoJSON files and SPARQL queries

## Quick Start

### 1. Install Kepler.gl

```bash
npm install --save kepler.gl @kepler.gl/components @kepler.gl/reducers
```

### 2. Get a Mapbox Token

Visit [mapbox.com](https://www.mapbox.com/) to get a free access token.

### 3. Use an Example

```jsx
import React from 'react';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware, compose } from 'redux';
import { connect } from 'react-redux';
import keplerGlReducer, { enhanceReduxMiddleware } from '@kepler.gl/reducers';
import { KeplerGl } from '@kepler.gl/components';
import sampleGeoJsonData from './assets/example-geojsons/sample-wikipedia-articles.geojson';

// Create Redux store
const store = createStore(
  keplerGlReducer,
  compose(applyMiddleware(...enhanceReduxMiddleware()))
);

const KeplerGlApp = connect(mapStateToProps)(KeplerGl);

function App() {
  return (
    <Provider store={store}>
      <KeplerGlApp
        mapType="mapbox"
        mapboxApiAccessToken="YOUR_MAPBOX_TOKEN"
        initialConfig={{
          mapState: {
            center: [0, 20],
            zoom: 2
          }
        }}
      />
    </Provider>
  );
}

export default App;
```

## Data Extraction

### SPARQL Queries

Sample SPARQL queries are available in `assets/sample-wikidata-sparql-queries/`:

- `articles-by-country.rq`: Query for Wikipedia articles by country
- `commons-depicts.rq`: Query for Commons files with depicts coordinates
- `countries-by-population.rq`: Countries ranked by population
- `articles-by-topic.rq`: Articles filtered by topic

### Using the SPARQL Converter

```bash
# List available queries
node scripts/wikidata-to-geojson.js list

# Execute a query and save to file
node scripts/wikidata-to-geojson.js query articles-by-country
```

## Layer Types

### Point Layer (scatterplot)

For visualizing individual locations:

```json
{
  "type": "scatterplot",
  "config": {
    "label": "Article Locations",
    "colorField": { "field": "country", "type": "ordinal" },
    "sizeField": { "field": "population", "type": "quantitative" },
    "isVisible": true
  }
}
```

### Hexagon Layer

For density analysis:

```json
{
  "type": "hexagon",
  "config": {
    "label": "Article Density",
    "colorField": { "field": "count", "type": "quantitative" },
    "isVisible": true,
    "hexagonResolution": 6
  }
}
```

### Heatmap Layer

For density visualization:

```json
{
  "type": "heatmap",
  "config": {
    "label": "Heatmap",
    "colorField": { "field": "density", "type": "quantitative" },
    "isVisible": true,
    "heatmapRadius": 20
  }
}
```

### Arc Layer

For routes and flows:

```json
{
  "type": "arc",
  "config": {
    "label": "Travel Routes",
    "colorField": { "field": "distance", "type": "quantitative" },
    "isVisible": true
  }
}
```

## Common Use Cases

### 1. Article Distribution by Country

Extract P17 (country) and P625 (coordinates) from Wikidata. Color points by country and size by article count.

### 2. Image Depiction Locations

Query Commons files with P9149 (depicts coordinates) to visualize where images were taken or depict.

### 3. Density Analysis

Use hexagon or heatmap layers for regional concentration analysis.

### 4. Article Migration/Travel

Track article edits across regions using arc layers for movement paths.

## Wikidata Coordinate Properties

- **P625**: coordinates of the item (geolocation of object)
- **P9149**: coordinates of depicted place (place depicted in image)
- **P131**: location (country, region, city)
- **P17**: country
- **P6**: headquarters location

## Project Structure

```
kepler-gl/
├── SKILL.md                          # Main skill documentation
├── examples/
│   └── basic-wikipedia-map.jsx       # Basic example
├── scripts/
│   └── wikidata-to-geojson.js        # SPARQL to GeoJSON converter
├── templates/
│   ├── basic-map-template.jsx
│   ├── point-layer-template.json
│   ├── hexagon-density-template.json
│   └── heatmap-template.json
├── saved-configs/
│   ├── article-distribution.json     # Pre-configured map
│   └── depicts-locations.json
├── assets/
│   ├── sample-wikidata-sparql-queries/
│   │   ├── articles-by-country.rq
│   │   ├── commons-depicts.rq
│   │   └── countries-by-population.rq
│   ├── example-geojsons/
│   │   ├── sample-wikipedia-articles.geojson
│   │   └── sample-commons-depicts.geojson
│   └── documentation/
└── test-data/
    └── wikipedia-sample-articles.json
```

## Resources

- [Kepler.gl Documentation](https://docs.kepler.gl/)
- [Kepler.gl GitHub](https://github.com/keplergl/kepler.gl)
- [Wikidata SPARQL Endpoint](https://query.wikidata.org/)
- [Wikidata Property:P625](https://www.wikidata.org/wiki/Property:P625)
- [Wikidata Property:P9149](https://www.wikidata.org/wiki/Property:P9149)

## Troubleshooting

### WebGL Context Errors

- Ensure browser supports WebGL
- Check for GPU acceleration
- Verify Mapbox token

### Data Loading Issues

- Validate GeoJSON structure
- Check coordinate format ([longitude, latitude])
- Handle empty datasets

### Performance Issues

- Limit dataset size for browser rendering
- Use spatial indexing
- Pre-aggregate data

## License

This skill is part of the Wikipedia-AI-Skills project and follows the same license.

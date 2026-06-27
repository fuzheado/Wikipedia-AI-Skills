# kepler.gl

Use Kepler.gl to create interactive geospatial visualizations of Wikimedia data — Wikipedia articles, Commons media, and Wikidata entities. Covers extraction of geographic coordinates, conversion to GeoJSON, React integration, layer types, and common visualization patterns for location-based data analysis.

## Overview

Kepler.gl is a data-agnostic, high-performance web-based application for visual exploration of large-scale geolocation data sets. Built on MapLibre GL and deck.gl, it can render millions of points and perform spatial aggregations in the browser. It's also a React component using Redux for state management, highly customizable and embeddable.

## Core Concepts

- **Geospatial Data Formats**: CSV, GeoJSON, GeoArrow, Kepler.gl JSON
- **Layer Types**: Point (locations), Arc (routes), Hexagon (density), Heatmap (density), Polygon (regions), Circle (size/bubble)
- **Redux State Management**: Data, config, visState, uiState
- **Mapbox GL**: Requires Mapbox token for rendering tiles
- **WebGL Rendering**: High-performance rendering of large datasets

## Installation

```bash
# Install kepler.gl and dependencies
npm install --save kepler.gl @kepler.gl/components @kepler.gl/reducers

# Prerequisites
# - Node.js 18.18.2 or higher
# - Mapbox access token (get one at mapbox.com)
```

## Data Extraction from Wikimedia

### Wikipedia Article Locations

Wikipedia articles often contain geographic coordinates in the lead section. Common patterns:
- Lat/long in infoboxes (e.g., `|coordinates = 51.5074°N, 0.1278°W`)
- Coordinates template syntax: `{{coord|51.5074|-0.1278|type:city_region:GB}}`
- Wikidata QID with P625 coordinate property

### Wikidata Coordinate Properties

- **P625**: coordinates of the item (geolocation of object)
- **P9149**: coordinates of depicted place (place depicted in image)
- **P131**: location (country, region, city)
- **P17**: country
- **P6**: headquarters location

### Commons Depicts Coordinates

- **P9149** (coordinates of depicted place) on Wikimedia Commons files
- Use for visualizing where images were taken or depict
- Combine with `P625` (item location) for comparative analysis

## Data Preparation

### Converting Wikidata to GeoJSON

```javascript
// Sample structure from Wikidata SPARQL
[
  {
    "item": "Q42",
    "label": "Douglas Adams",
    "coordinates": [51.5074, -0.1278],
    "country": "United Kingdom",
    "description": "English writer and humorist"
  }
]
```

### GeoJSON Structure

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-0.1278, 51.5074]
      },
      "properties": {
        "item": "Q42",
        "label": "Douglas Adams",
        "description": "English writer and humorist",
        "country": "United Kingdom"
      }
    }
  ]
}
```

## React Integration

### Basic Kepler.gl Component

```jsx
import React from 'react';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware, compose } from 'redux';
import { connect } from 'react-redux';
import keplerGlReducer, { enhanceReduxMiddleware } from '@kepler.gl/reducers';
import { KeplerGl } from '@kepler.gl/components';

// Create Redux store
const store = createStore(
  keplerGlReducer,
  compose(
    applyMiddleware(...enhanceReduxMiddleware())
  )
);

// Connect Kepler.gl component
const mapStateToProps = state => ({
  mapState: state.keplerGl
});

const KeplerGlApp = connect(mapStateToProps)(KeplerGl);

// Usage
function App() {
  const initialConfig = {
    mapState: {
      center: [-0.1278, 51.5074],
      zoom: 10,
      bearing: 0,
      pitch: 0
    },
    uiState: {
      isVisible: true,
      dock: { isVisible: true, position: 'left', width: 300 }
    }
  };

  return (
    <Provider store={store}>
      <KeplerGlApp
        mapType="mapbox"
        mapboxApiAccessToken="YOUR_MAPBOX_TOKEN"
        initialConfig={initialConfig}
      />
    </Provider>
  );
}
```

### Adding Data Programmatically

```javascript
import { addDataToMap } from '@kepler.gl/actions';

// Add GeoJSON dataset
store.dispatch(
  addDataToMap({
    datasets: [{
      config: {
        label: 'Wikipedia Articles',
        color: [0, 191, 255], // RGB
        isVisible: true
      },
      data: geoJsonData
    }],
    option: { centerMap: true }
  })
);
```

## Layer Types and Visualization Patterns

### Point Layer (Most Common)

Use for: Article locations, entity coordinates, image depictions

```javascript
{
  type: 'scatterplot',
  config: {
    label: 'Article Locations',
    colorField: { field: 'country', type: 'ordinal' },
    sizeField: { field: 'article_count', type: 'quantitative' },
    isVisible: true
  }
}
```

### Arc Layer

Use for: Travel routes, article migration, network flows

```javascript
{
  type: 'arc',
  config: {
    label: 'Travel Routes',
    colorField: { field: 'distance', type: 'quantitative' },
    strokeColor: { field: 'country', type: 'ordinal' }
  }
}
```

### Hexagon Layer

Use for: Density analysis, population clusters, article frequency by region

```javascript
{
  type: 'hexagon',
  config: {
    label: 'Article Density',
    colorField: { field: 'count', type: 'quantitative' }
  }
}
```

### Heatmap Layer

Use for: Density visualization, spatial clustering

```javascript
{
  type: 'heatmap',
  config: {
    label: 'Heatmap',
    colorField: { field: 'density', type: 'quantitative' }
  }
}
```

## Common Wikimedia Visualization Use Cases

### 1. Article Distribution by Country

- Extract P17 (country) and P625 (coordinates) from Wikidata
- Color points by country
- Size by article count per country

### 2. Image Depiction Locations

- Query Commons files with P9149 (depicts coordinates)
- Visualize where images were taken
- Compare with P625 (item location)

### 3. Article Migration/Travel

- Track article edits across regions
- Visualize migration patterns
- Arc layer for movement paths

### 4. Density Analysis

- Hexagon layer for regional concentration
- Heatmap for density visualization
- Filter by topic, language, quality rating

### 5. Network Visualization

- Combine with network graph data
- Show relationships between entities geographically
- Use arc layers for connections

## Advanced Features

### Playback/Time Series

- Temporal data: article creation dates, edit timestamps
- Time slider in Kepler.gl UI
- Config with temporal fields

### Filters and Aggregations

- Filter by language, quality, topic
- Spatial filters (bounding box, radius)
- Custom aggregations

### Mapbox Integration

- Custom map styles
- Vector tiles
- Custom basemaps

### Saving and Loading Maps

- Export Kepler.gl config as JSON
- Share configurations
- Batch visualization presets

## Integration with Wikimedia Tools

### SPARQL to GeoJSON Pipeline

1. Query Wikidata SPARQL endpoint
2. Transform results to GeoJSON format
3. Load into Kepler.gl component

### Pywikibot + Kepler.gl

- Use Pywikibot to fetch article data
- Extract coordinates from page content
- Generate GeoJSON programmatically

### EventStreams + Kepler.gl

- Real-time edit tracking
- Visualize live geographic changes
- Combine with existing visualizations

## Troubleshooting

### WebGL Context Errors

- Ensure browser supports WebGL
- Check for GPU acceleration
- Verify Mapbox token

### Data Loading Issues

- Validate GeoJSON structure
- Check coordinate format (lon, lat)
- Handle empty datasets

### Performance Issues

- Limit dataset size for browser rendering
- Use spatial indexing
- Pre-aggregate data

## Resources

- [Kepler.gl Documentation](https://docs.kepler.gl/)
- [Kepler.gl GitHub](https://github.com/keplergl/kepler.gl)
- [Wikidata SPARQL Endpoint](https://query.wikidata.org/)
- [Wikidata Property:P625](https://www.wikidata.org/wiki/Property:P625)
- [Wikidata Property:P9149](https://www.wikidata.org/wiki/Property:P9149)
- [Wikidata Atlas](https://wdatlas.dcc.uchile.cl/)

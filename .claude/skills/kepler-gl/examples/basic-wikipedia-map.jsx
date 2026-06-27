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

// Sample Wikipedia data
const sampleWikipediaData = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [-0.1278, 51.5074] // London
      },
      properties: {
        title: 'London',
        item: 'Q84',
        description: 'Capital of England and the United Kingdom',
        country: 'United Kingdom',
        population: '8.9 million'
      }
    },
    {
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [-0.1278, 51.5074] // London
      },
      properties: {
        title: 'London (disambiguation)',
        item: 'Q5912916',
        description: 'Disambiguation page',
        country: 'United Kingdom'
      }
    },
    {
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [-73.9857, 40.7484] // New York
      },
      properties: {
        title: 'New York City',
        item: 'Q60',
        description: 'Most populous city in the United States',
        country: 'United States',
        population: '8.4 million'
      }
    },
    {
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [2.3522, 48.8566] // Paris
      },
      properties: {
        title: 'Paris',
        item: 'Q90',
        description: 'Capital and most populous city of France',
        country: 'France',
        population: '2.1 million'
      }
    },
    {
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [139.6917, 35.6895] // Tokyo
      },
      properties: {
        title: 'Tokyo',
        item: 'Q1490',
        description: 'Capital and most populous prefecture of Japan',
        country: 'Japan',
        population: '13.9 million'
      }
    }
  ]
};

// Initial configuration
const initialConfig = {
  mapState: {
    center: [0, 20],
    zoom: 2,
    bearing: 0,
    pitch: 0
  },
  uiState: {
    isVisible: true,
    dock: { isVisible: true, position: 'left', width: 300 }
  }
};

// Usage
function App() {
  return (
    <Provider store={store}>
      <KeplerGlApp
        mapType="mapbox"
        mapboxApiAccessToken="YOUR_MAPBOX_TOKEN_HERE"
        initialConfig={initialConfig}
      >
        {/* Data will be loaded via addDataToMap action */}
      </KeplerGlApp>
    </Provider>
  );
}

export default App;

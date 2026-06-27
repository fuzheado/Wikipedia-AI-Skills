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

// Sample GeoJSON data
const sampleGeoJsonData = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [-0.1278, 51.5074]
      },
      properties: {
        label: 'Sample Point',
        value: 100
      }
    }
  ]
};

// Initial configuration
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

// Usage
function App() {
  return (
    <Provider store={store}>
      <KeplerGlApp
        mapType="mapbox"
        mapboxApiAccessToken="YOUR_MAPBOX_TOKEN_HERE"
        initialConfig={initialConfig}
      />
    </Provider>
  );
}

export default App;

#!/usr/bin/env node

/**
 * SPARQL to GeoJSON Converter
 * Converts Wikidata SPARQL results to GeoJSON format for Kepler.gl
 */

const axios = require('axios');

class WikidataToGeoJSON {
  constructor(sparqlQuery) {
    this.sparqlQuery = sparqlQuery;
    this.results = [];
  }

  /**
   * Execute SPARQL query against Wikidata Query Service
   */
  async queryWikidata() {
    const url = 'https://query.wikidata.org/sparql';
    const headers = {
      'Accept': 'application/json',
      'User-Agent': 'Wikimedia-AI-Skills-kepler-gl/1.0'
    };

    try {
      const response = await axios.post(url, this.sparqlQuery, {
        headers,
        params: {
          format: 'json',
          origin: '*'
        }
      });

      this.results = response.data.results.bindings;
      return this.results;
    } catch (error) {
      console.error('SPARQL query failed:', error.message);
      throw error;
    }
  }

  /**
   * Extract coordinate values from Wikidata result
   */
  extractCoordinates(binding, latField, lonField) {
    const lat = binding[latField]?.value;
    const lon = binding[lonField]?.value;

    if (!lat || !lon) return null;

    // Convert to array [longitude, latitude]
    return [parseFloat(lon), parseFloat(lat)];
  }

  /**
   * Extract property values
   */
  extractValue(binding, field) {
    return binding[field]?.value || binding[field]?.['xml:lang'] || null;
  }

  /**
   * Convert SPARQL results to GeoJSON FeatureCollection
   */
  toGeoJSON(options = {}) {
    const {
      latField = 'latitude',
      lonField = 'longitude',
      itemField = 'item',
      labelField = 'label',
      descriptionField = 'description',
      countryField = 'country',
      properties = {}
    } = options;

    const features = this.results.map(binding => {
      const coordinates = this.extractCoordinates(binding, latField, lonField);

      if (!coordinates) {
        return null;
      }

      const item = this.extractValue(binding, itemField);
      const label = this.extractValue(binding, labelField);
      const description = this.extractValue(binding, descriptionField);
      const country = this.extractValue(binding, countryField);

      const feature = {
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates
        },
        properties: {
          item,
          label,
          description,
          country,
          ...properties
        }
      };

      return feature;
    }).filter(feature => feature !== null);

    return {
      type: 'FeatureCollection',
      features
    };
  }

  /**
   * Save GeoJSON to file
   */
  async saveToFile(filename) {
    const geojson = this.toGeoJSON();
    const fs = require('fs').promises;

    try {
      await fs.writeFile(filename, JSON.stringify(geojson, null, 2));
      console.log(`Saved GeoJSON to ${filename}`);
      return geojson;
    } catch (error) {
      console.error('Failed to save file:', error.message);
      throw error;
    }
  }
}

// Example SPARQL queries
const EXAMPLE_QUERIES = {
  // Articles by country
  articlesByCountry: `
    SELECT ?item ?itemLabel ?itemDescription ?countryLabel ?latitude ?longitude WHERE {
      ?item wdt:P31 wd:Q5 .  # Instance of human/person
      ?item wdt:P27 ?country . # Country of citizenship
      ?country wdt:P17 wd:Q6656 . # Country is a sovereign state
      OPTIONAL { ?item wdt:P625 ?location . }
      OPTIONAL { ?item wdt:P18 ?image . }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    LIMIT 100
  `,

  // Commons depicts coordinates
  commonsDepicts: `
    SELECT ?item ?itemLabel ?itemDescription ?depictsCoordinates ?latitude ?longitude WHERE {
      ?item wdt:P31 wd:Q13406463 .  # Instance of Wikimedia Commons file
      OPTIONAL { ?item wdt:P9149 ?depictsCoordinates . }
      OPTIONAL { ?item wdt:P625 ?location . }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    LIMIT 100
  `,

  // Countries by population
  countriesByPopulation: `
    SELECT ?country ?countryLabel ?countryDescription ?population ?latitude ?longitude WHERE {
      ?country wdt:P31 wd:Q6256 .  # Instance of sovereign state
      ?country wdt:P1082 ?population . # Population
      OPTIONAL { ?country wdt:P625 ?location . }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    ORDER BY DESC(?population)
    LIMIT 50
  `,

  // Article locations by topic
  articlesByTopic: `
    SELECT ?item ?itemLabel ?itemDescription ?countryLabel ?latitude ?longitude WHERE {
      ?item wdt:P31 wd:Q5 .  # Instance of human/person
      ?item wdt:P31/wdt:P279* wd:Q201390 .  # Instance of scientist
      ?item wdt:P27 ?country . # Country of citizenship
      ?country wdt:P17 wd:Q6656 . # Country is a sovereign state
      OPTIONAL { ?item wdt:P625 ?location . }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    LIMIT 100
  `
};

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (command === 'query' && args[1]) {
    const queryName = args[1];
    const query = EXAMPLE_QUERIES[queryName];

    if (!query) {
      console.error('Unknown query. Available queries:', Object.keys(EXAMPLE_QUERIES));
      process.exit(1);
    }

    console.log(`Executing query: ${queryName}`);
    console.log('Query:', query.substring(0, 200) + '...\n');

    const converter = new WikidataToGeoJSON(query);
    await converter.queryWikidata();

    console.log(`Found ${converter.results.length} results\n`);

    // Show sample
    if (converter.results.length > 0) {
      console.log('Sample result:');
      console.log(JSON.stringify(converter.results[0], null, 2));
    }

    // Ask to save
    const fs = require('fs').promises;
    const filename = `wikidata-${queryName}-${Date.now()}.geojson`;

    console.log(`\nSave to file: ${filename}? (y/n)`);
    const readline = require('readline').createInterface({
      input: process.stdin,
      output: process.stdout
    });

    readline.question('', async (answer) => {
      if (answer.toLowerCase() === 'y') {
        await converter.saveToFile(filename);
      }
      readline.close();
    });
  } else if (command === 'list') {
    console.log('Available SPARQL queries:');
    Object.entries(EXAMPLE_QUERIES).forEach(([name, query]) => {
      console.log(`  ${name}: ${query.substring(0, 100)}...`);
    });
  } else {
    console.log('Usage:');
    console.log('  node wikidata-to-geojson.js query <query-name>');
    console.log('  node wikidata-to-geojson.js list');
    console.log('\nAvailable queries:');
    Object.keys(EXAMPLE_QUERIES).forEach(name => {
      console.log(`  ${name}`);
    });
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { WikidataToGeoJSON, EXAMPLE_QUERIES };

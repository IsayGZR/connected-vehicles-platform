require('dotenv').config();

const express = require('express');
const cors = require('cors');
const { CosmosClient } = require('@azure/cosmos');

const app = express();
app.use(cors());
app.use(express.static('public'));
app.get('/api/config', (req, res) => {
    res.json({ mapboxToken: process.env.MAPBOX_TOKEN });
});

require('dotenv').config({ path: '../simulator/.env' });
const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING);
const database = client.database('VehicleDB');
const container = database.container('TelemetryData');

// Endpoint — últimos datos de cada vehículo
app.get('/api/vehicles', async (req, res) => {
    try {
        const { resources } = await container.items.query({
            query: `
                SELECT * FROM c 
                WHERE c.timestamp >= @since
                ORDER BY c.timestamp DESC
                OFFSET 0 LIMIT 50
            `,
            parameters: [
                { name: "@since", value: new Date(Date.now() - 30000).toISOString() }
            ]
        }).fetchAll();

        // Obtener último dato por vehículo
        const latest = {};
        resources.forEach(item => {
            if (!latest[item.vehiclesID] || item.timestamp > latest[item.vehiclesID].timestamp) {
                latest[item.vehiclesID] = item;
            }
        });

        res.json(Object.values(latest));
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: e.message });
    }
});

// Endpoint — historial de alertas
app.get('/api/alerts', async (req, res) => {
    try {
        const { resources } = await container.items.query({
            query: `
                SELECT * FROM c 
                WHERE c.status != 'NORMAL'
                AND c.timestamp >= @since
                ORDER BY c.timestamp DESC
                OFFSET 0 LIMIT 20
            `,
            parameters: [
                { name: "@since", value: new Date(Date.now() - 60000).toISOString() }
            ]
        }).fetchAll();

        res.json(resources);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ===== MÓDULO 2: TRAFFIC VISION =====
const VISION_ENDPOINT = process.env.VISION_ENDPOINT;
const VISION_KEY = process.env.VISION_KEY;

app.post('/api/vision/analyze-url', express.json(), async (req, res) => {
    const { imageUrl } = req.body;
    if (!imageUrl) return res.status(400).json({ error: 'imageUrl requerida' });

    try {
        const fetch = (await import('node-fetch')).default;
        const url = `${VISION_ENDPOINT}computervision/imageanalysis:analyze?api-version=2024-02-01&features=objects,tags,caption,denseCaptions&language=en`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Ocp-Apim-Subscription-Key': VISION_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: imageUrl })
        });
        const data = await response.json();
        console.log('Azure Vision response:', JSON.stringify(data, null, 2));
        res.json(data);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: e.message });
    }
});

app.post('/api/vision/analyze-file', express.raw({ type: 'image/*', limit: '10mb' }), async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const url = `${VISION_ENDPOINT}computervision/imageanalysis:analyze?api-version=2024-02-01&features=objects,tags,caption,denseCaptions&language=en`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Ocp-Apim-Subscription-Key': VISION_KEY,
                'Content-Type': req.headers['content-type']
            },
            body: req.body
        });
        const data = await response.json();
        console.log('Azure Vision response:', JSON.stringify(data, null, 2));
        res.json(data);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: e.message });
    }
});

app.listen(3000, () => console.log('🚗 Dashboard corriendo en http://localhost:3000'));
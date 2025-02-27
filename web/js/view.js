document.addEventListener('DOMContentLoaded', function () {

    window.electronAPI.onReceiveMessage((inputFile) => {
        spinner.style.display = "flex";
        readFileFromPath(inputFile.path);
    });

    window.addEventListener('resize', () => {
        updateGraph(rawGraphData.curLayer);
    }, true);

    const chartConfiguration = {
        displayModeBar: true,
        scrollZoom: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['select2d','lasso2d','resetScale2d', 'hoverClosestCartesian','hoverCompareCartesian', 'toggleSpikelines']
    };

    var completeGraphData = {
        layers: [],
        numLayers: 0,
        numHatches: 0,
        curLayer: 0,
        curHatch: 0,
        rValues: [],
    }

    var rawGraphData = {
        layers: [],
        numLayers: 0,
        numHatches: 0,
        curLayer: 0,
        curHatch: 0,
        rValues: [],

    }

    var completeTrace;
    var showHatchLines = false;
    var isPlaying = false;
    var playInterval = null;
    var playSpeed = 250; // Default 1 second interval
    const layerSlider = document.getElementById('view-layerSlider');
    const hatchSlider = document.getElementById('view-hatchSlider');
    const speedRange = document.getElementById('view-speedRange');
    const showHatchLinesCheckbox = document.getElementById('view-showHatchCheckbox');
    const playButton = document.getElementById('view-playButton');
    const spinner = document.getElementById('view-spinner');
    const viewContainer = document.getElementById('view-container');

    if (layerSlider && hatchSlider && speedRange && showHatchLinesCheckbox) {
        layerSlider.addEventListener('input', async (event) => {
            const layerIndex = parseInt(event.target.value);
            document.getElementById('view-layerValue').textContent = layerIndex;
            await eel.set_current_data_layer(layerIndex)();
            await eel.set_current_data_hatch(0)();

            rawGraphData.numHatches = await eel.get_num_hatches_data()();
            rawGraphData.curHatch = 0;
            rawGraphData.curLayer = layerIndex;

            // displayRValues();
            await loadCompleteBoundingBoxes();
            if (showHatchLines) {
                await retrieveHashLines();
            } else {
                await retrieveBoundingBoxes();
            }

            updateHatchSlider();
        });

        hatchSlider.addEventListener('input', async (event) => {
            const hatchIndex = parseInt(event.target.value);
            hatchSlider.textContent = event.target.value;
            await eel.set_current_data_hatch(hatchIndex)();

            rawGraphData.curHatch = hatchIndex;
            if (showHatchLines) {
                await retrieveHashLines();
            } else {
                await retrieveBoundingBoxes();
            }
        });

        speedRange.addEventListener('input', (e) => {
            const speed = e.target.value;
            document.getElementById('view-speedValue').textContent = speed + 'x';
            playSpeed = 250 / speed;

            if (isPlaying) {
                clearInterval(playInterval);
                playHatches();
            }
        });

        showHatchLinesCheckbox.addEventListener('change', async (e) => {
            showHatchLines = e.target.checked;
            if (showHatchLines) {
                await retrieveHashLines();
            } else {
                await retrieveBoundingBoxes();
            }
        });

        playButton.addEventListener('click', togglePlay);
    }

    async function loadCompleteBoundingBoxes() {
        const completeCoords = await eel.retrieve_full_bounding_box_data()();
        completeGraphData.layers = completeCoords.bounding_boxes;
        completeGraphData.x_min = completeCoords.x_min;
        completeGraphData.x_max = completeCoords.x_max;
        completeGraphData.y_min = completeCoords.y_min;
        completeGraphData.y_max = completeCoords.y_max;

        completeTrace = createCompleteTrace();
    }

    async function readFileFromPath(filepath) {
        await eel.read_cli_from_path(filepath)();
        await viewFile();
    }

    async function readFile(fileContent) {
        await eel.read_cli(fileContent)();
        await viewFile();
    }

    async function viewFile() {

        const numLayers = await eel.get_num_layers_data()();
        const numHatches = await eel.get_num_hatches_data()();
        rawGraphData.numLayers = numLayers;
        rawGraphData.numHatches = numHatches;
        rawGraphData.curLayer = 0;

        await loadCompleteBoundingBoxes();
        if (showHatchLines) {
            await retrieveHashLines();
        } else {
            await retrieveBoundingBoxes();
        }

        updateLayerSlider();
        updateHatchSlider();

        spinner.style.display = "none";
        viewContainer.style.display = 'flex';
        updateGraph(0);
    }

    async function retrieveHashLines() {
        const dataCoords = await eel.retrieve_coords_from_data_cur()();
        rawGraphData.layers = dataCoords;
        rawGraphData.x_min = dataCoords.x_min;
        rawGraphData.x_max = dataCoords.x_max;
        rawGraphData.y_min = dataCoords.y_min;
        rawGraphData.y_max = dataCoords.y_max;
        updateGraph(rawGraphData.curLayer);
    }

    async function retrieveBoundingBoxes() {
        const dataCoords = await eel.retrieve_bounding_box_from_data_layer()();
        rawGraphData.layers = dataCoords.bounding_boxes;
        rawGraphData.x_min = dataCoords.x_min;
        rawGraphData.x_max = dataCoords.x_max;
        rawGraphData.y_min = dataCoords.y_min;
        rawGraphData.y_max = dataCoords.y_max;
        updateGraph(rawGraphData.curLayer);
    }

    function togglePlay() {
        const playButton = document.getElementById('view-playButton');
        const hatchSlider = document.getElementById('view-hatchSlider');
        isPlaying = !isPlaying;

        if (isPlaying) {
            playButton.innerHTML = '<i class="bi bi-pause-fill"></i>';
            const current = rawGraphData.curHatch < rawGraphData.numHatches;

            if (!current) {
                rawGraphData.curHatch = 0;
                hatchSlider.value = 0;
            }

            playHatches();
        } else {
            playButton.innerHTML = '<i class="bi bi-play-fill"></i>';
            clearInterval(playInterval);
        }
    }

    function playHatches() {
        const hatchSlider = document.getElementById('view-hatchSlider');
        let currentHatch = parseInt(hatchSlider.value);

        playInterval = setInterval(async () => {
            if (currentHatch >= rawGraphData.numHatches) {
                togglePlay(); // Stop when reached end
                return;
            }

            currentHatch++;
            hatchSlider.value = currentHatch;
            document.getElementById('view-hatchesValue').textContent = currentHatch;

            await eel.set_current_data_hatch(currentHatch)();
            await eel.set_current_opti_hatch(currentHatch)();
            rawGraphData.curHatch = currentHatch;
            if (showHatchLines) {
                await retrieveHashLines();
            } else {
                await retrieveBoundingBoxes();
            }
            updateGraph(rawGraphData.curLayer);
        }, playSpeed);
    }

    function updateHatchSlider() {
        const hatchSlider = document.getElementById('view-hatchSlider');
        hatchSlider.max = rawGraphData.numHatches;
        hatchSlider.value = 0;
        document.getElementById('view-hatchesValue').textContent = 0;
    }

    function updateLayerSlider() {
        const layerSlider = document.getElementById('view-layerSlider');
        layerSlider.max = rawGraphData.numLayers;
        layerSlider.value = 1;
        document.getElementById('view-layerValue').textContent = 0;
    }

    function createCompleteTrace() {
        const boxes = completeGraphData.layers;
        return boxes.map((box, index) => {
            const x = box[0];
            const y = box[1];
            const color = '#E0E0E0';

            return {
                x: x,
                y: y,
                type: 'scatter',
                mode: 'lines',  // Remove markers, lines only
                fill: 'toself',
                fillcolor: color,
                opacity: 0.73,
                line: {
                    color: color,
                    width: 1,
                    simplify: false // Preserve exact path
                },
                showlegend: false,
                hoverinfo: 'none'
            };
        });
    }

    function createScatterTraces(boxes) {
        const maxAge = boxes.length;
        
        return boxes.map((box, index) => {
            const ageValue = (maxAge - index) / maxAge; // Normalized age (1 = newest, 0 = oldest)
            const color = interpolateColor(
                {r: 255, g: 0, b: 0},   // Red (hot)
                {r: 0, g: 0, b: 255},   // Blue (cold)
                ageValue
            );
    
            return {
                x: box[0],
                y: box[1],
                mode: 'lines',
                fill: 'toself',
                type: 'scattergl',
                line: {
                    color: color,
                    width: 1,
                    simplify: false
                },
                fillcolor: color + '80', // Add alpha channel
                showlegend: false,
                hoverinfo: 'none'
            };
        });
    }

    function interpolateColor(color1, color2, factor) {
        const result = {
            r: Math.round(color1.r + factor * (color2.r - color1.r)),
            g: Math.round(color1.g + factor * (color2.g - color1.g)),
            b: Math.round(color1.b + factor * (color2.b - color1.b))
        };
        return `rgb(${result.r},${result.g},${result.b})`;
    }

    function getRawHatchData() {
        const xCoordsRaw = [];
        const yCoordsRaw = [];

        // Combine all hatch lines into a single trace with null separators
        for (let i = 0; i < rawGraphData.layers.x.length; i += 2) {
            xCoordsRaw.push(rawGraphData.layers.x[i], rawGraphData.layers.x[i + 1], null);
            yCoordsRaw.push(rawGraphData.layers.y[i], rawGraphData.layers.y[i + 1], null);
        }
        xCoordsRaw.pop(); // Remove trailing null
        yCoordsRaw.pop();
        let data = {
            x: xCoordsRaw,
            y: yCoordsRaw,
            mode: 'lines',
            type: 'scattergl',
            line: { width: 1, color: 'green' },
            showlegend: false
        };

        return data;
    }

    const heatScaleDummy = {
        x: [null],
        y: [null],
        type: 'scatter',
        mode: 'markers',
        marker: {
            size: 0,
            cmax: 1,
            cmin: 0,
            colorscale: [[0, 'blue'], [0.5, 'purple'], [1, 'red']],
            colorbar: {
                title: 'Temporal Scale',
                titleside: 'right',
                thickness: 20,
                len: 0.6,
                yanchor: 'middle',
                ticks: 'outside',
                tickvals: [0, 0.2, 0.4, 0.6, 0.8, 1],
                ticktext: ['Oldest', '', '', '', '', 'Newest']
            },
            showscale: true
        },
        showlegend: false,
        hoverinfo: 'none'
    };

    function updateGraph(layerIndex) {
        try {
            const xPadding = (rawGraphData.x_max - rawGraphData.x_min) * 0.1;
            const yPadding = (rawGraphData.y_max - rawGraphData.y_min) * 0.1;
            var rawData = [];
            let rawPlotData = [];

            if (showHatchLines) {
                rawData = getRawHatchData();
                rawPlotData = [...completeTrace, rawData, heatScaleDummy];
            } else {
                rawData = createScatterTraces(rawGraphData.layers);
                rawPlotData = [...completeTrace, ...rawData, heatScaleDummy];
            }

            const layout = {
                height: viewContainer.clientHeight * 0.7,
                width: viewContainer.clientWidth,
                title: {
                    text: `Layer ${layerIndex}`,
                    font: {
                        size: 16
                    },
                },
                xaxis: {
                    title: 'X',
                    scaleanchor: 'y',  // Make axes equal scale
                    scaleratio: 1,
                    range: [rawGraphData.x_min - xPadding, rawGraphData.x_max + xPadding],
                    ticksuffix: "mm"
                },
                yaxis: {
                    title: 'Y',
                    range: [rawGraphData.y_min - yPadding, rawGraphData.y_max + yPadding],
                    ticksuffix: "mm"
                },
                hovermode: false,
                showlegend: false
            };


            Plotly.react('view-plot', rawPlotData, layout, chartConfiguration);
        } catch (error) {
            console.error('Error updating graph:', error);
        }
    }
});


document.addEventListener('DOMContentLoaded', function () {

    var selectedFile = '';
    var graphData = {
        layers: [],
        numLayers: 0,
        numHatches: 0,
        curLayer: 0,
        curHatch: 0,
        rValues: [],
    };
    var activeButton = null;
    var showHatchLines = false;
    var isPlaying = false;
    var playInterval = null;
    var playSpeed = 250; // Default 1 second interval
    const layerSlider = document.getElementById('layerSlider');
    const hatchSlider = document.getElementById('hatchSlider');
    const speedRange = document.getElementById('speedRange');
    const showHatchLinesCheckbox = document.getElementById('showHatchCheckbox');
    const refreshButton = document.getElementById('refreshButton');
    const playButton = document.getElementById('playButton');
    const processButton = document.getElementById('processButton');
    const rOptimizedLabel = document.getElementById('rOptimized');
    const rOriginalLabel = document.getElementById('rOriginal');
    const materialNameDropdown = document.getElementById('materialName');
    const customConfigFields = document.getElementById('custom-config');
    const materialForm = document.getElementById('materialForm');
    const customConfigInput = document.querySelectorAll("#custom-config input");
    const resizer = document.getElementById('dragMe');
    const leftSide = resizer.previousElementSibling;
    const rightSide = resizer.nextElementSibling;
    let x = 0;
    let y = 0;
    let leftWidth = 0;

    var selectedMaterial = {};
    let currentPage = 1;
    const itemsPerPage = 5;

    window.addEventListener('load', () => {
        loadFileHistory();
        loadMaterials();
    });
    

    if (layerSlider && hatchSlider && speedRange && showHatchLinesCheckbox && refreshButton && playButton && processButton && materialNameDropdown && customConfigFields && materialForm && resizer) {
        layerSlider.addEventListener('input', async (event) => {
            const layerIndex = parseInt(event.target.value);
            document.getElementById('layerValue').textContent = event.target.value;
            await eel.set_current_layer(layerIndex)();
            await eel.set_current_hatch(0)();
            graphData.curHatch = 0;
            graphData.curLayer = layerIndex;
            const r_values = await eel.get_r_from_layer()();
            graphData.rValues = r_values;
            displayRValues();
            if (showHatchLines) {
                retrieveHashLines();
            } else {
                retrieveBoundingBoxes();
            }
            updateHatchSlider();
        });

        hatchSlider.addEventListener('input', async (event) => {
            const hatchIndex = parseInt(event.target.value);
            document.getElementById('hatchesValue').textContent = event.target.value;
            await eel.set_current_hatch(hatchIndex)();
            graphData.curHatch = hatchIndex;

            if (showHatchLines) {
                retrieveHashLines();
            } else {
                retrieveBoundingBoxes();
            }
        });

        speedRange.addEventListener('input', (e) => {
            const speed = e.target.value;
            document.getElementById('speedValue').textContent = speed + 'x';
            playSpeed = 250 / speed;

            if (isPlaying) {
                clearInterval(playInterval);
                playHatches();
            }
        });

        showHatchLinesCheckbox.addEventListener('change', async (e) => {
            showHatchLines = e.target.checked;
            if (showHatchLines) {
                retrieveHashLines();
            } else {
                retrieveBoundingBoxes();
            }
        });

        materialNameDropdown.addEventListener('change', () => {
            if (materialNameDropdown.value === 'custom') {
                customConfigFields.style.display = 'grid';
                customConfigInput.forEach(input => {
                    input.required = true;
                    input.addEventListener('input', () => {
                        updateCustomMaterial();
                    });
                });
            } else {
                customConfigFields.style.display = 'none';
                selectedMaterial = materialNameDropdown.value;
            }
        });

        processButton.addEventListener('click', processFile);

        refreshButton.addEventListener('click', loadFileHistory);

        playButton.addEventListener('click', togglePlay);

        const mouseDownHandler = function (e) {
            // Get the current mouse position
            x = e.clientX;
            y = e.clientY;
            leftWidth = leftSide.getBoundingClientRect().width;
    
            // Attach the listeners to document
            document.addEventListener('mousemove', mouseMoveHandler);
            document.addEventListener('mouseup', mouseUpHandler);
        };
    
        const mouseMoveHandler = function (e) {
            // How far the mouse has been moved
            const dx = e.clientX - x;
            const dy = e.clientY - y;
    
            const newLeftWidth = ((leftWidth + dx) * 100) / resizer.parentNode.getBoundingClientRect().width;

            if (newLeftWidth < 25){
                newLeftWidth = 25;
            } 

            if (newLeftWidth > 70) {
                newLeftWidth = 70;
            }

            leftSide.style.width = newLeftWidth + '%';
    
            updateGraph();
            resizer.style.cursor = 'col-resize';
            document.body.style.cursor = 'col-resize';
    
            leftSide.style.userSelect = 'none';
            leftSide.style.pointerEvents = 'none';
    
            rightSide.style.userSelect = 'none';
            rightSide.style.pointerEvents = 'none';
        };
    
        const mouseUpHandler = function () {
            resizer.style.removeProperty('cursor');
            document.body.style.removeProperty('cursor');
    
            leftSide.style.removeProperty('user-select');
            leftSide.style.removeProperty('pointer-events');
    
            rightSide.style.removeProperty('user-select');
            rightSide.style.removeProperty('pointer-events');
    
            // Remove the handlers of mousemove and mouseup
            document.removeEventListener('mousemove', mouseMoveHandler);
            document.removeEventListener('mouseup', mouseUpHandler);
        };
    
        // Attach the handler
        resizer.addEventListener('mousedown', mouseDownHandler);
    }

    function updateCustomMaterial() {
        selectedMaterial = {
            name: document.getElementById('custom-name').value || '',
            kt: parseFloat(document.getElementById('kt').value) || 0,
            rho: parseFloat(document.getElementById('rho').value) || 0,
            cp: parseFloat(document.getElementById('cp').value) || 0,
            vs: parseFloat(document.getElementById('vs').value) || 0,
            h: parseFloat(document.getElementById('h').value) || 0,
            P: parseFloat(document.getElementById('P').value) || 0
        };
    }

    function displayRValues() {
        r_values = graphData.rValues;
        console.log('yo', r_values);
        rOptimizedLabel.style.display = 'block';
        rOriginalLabel.style.display = 'block';
        rOptimizedLabel.textContent = r_values[0];
        rOriginalLabel.textContent = r_values[1];
    }

    async function retrieveHashLines() {
        const coords = await eel.retrieve_coords_from_cur()();
        graphData.layers = coords;
        graphData.x_min = coords.x_min;
        graphData.x_max = coords.x_max;
        graphData.y_min = coords.y_min;
        graphData.y_max = coords.y_max;
        updateGraph(graphData.curLayer);
    }

    async function retrieveBoundingBoxes() {
        const coords = await eel.retrieve_bounding_box_from_layer()();
        graphData.layers = coords.bounding_boxes;
        graphData.x_min = coords.x_min;
        graphData.x_max = coords.x_max;
        graphData.y_min = coords.y_min;
        graphData.y_max = coords.y_max;
        updateGraph(graphData.curLayer);
    }

    function togglePlay() {
        const playButton = document.getElementById('playButton');
        const hatchSlider = document.getElementById('hatchSlider');
        isPlaying = !isPlaying;

        if (isPlaying) {
            playButton.innerHTML = '<i class="bi bi-pause-fill"></i>';
            const current = graphData.curHatch < graphData.numHatches;

            if (!current) {
                graphData.curHatch = 0;
                hatchSlider.value = 0;
            }

            playHatches();
        } else {
            playButton.innerHTML = '<i class="bi bi-play-fill"></i>';
            clearInterval(playInterval);
        }
    }

    function playHatches() {
        const hatchSlider = document.getElementById('hatchSlider');
        let currentHatch = parseInt(hatchSlider.value);

        playInterval = setInterval(async () => {
            if (currentHatch >= graphData.numHatches) {
                togglePlay(); // Stop when reached end
                return;
            }

            currentHatch++;
            hatchSlider.value = currentHatch;
            document.getElementById('hatchesValue').textContent = currentHatch;

            await eel.set_current_hatch(currentHatch)();
            graphData.curHatch = currentHatch;
            if (showHatchLines) {
                retrieveHashLines();
            } else {
                retrieveBoundingBoxes();
            }
            updateGraph(graphData.curLayer);
        }, playSpeed);
    }

    // Add speed control

    function updateHatchSlider() {
        const hatchSlider = document.getElementById('hatchSlider');
        hatchSlider.max = graphData.numHatches;
        hatchSlider.value = 0;
        document.getElementById('hatchesValue').textContent = 0;
    }

    function updateLayerSlider() {
        const layerSlider = document.getElementById('layerSlider');
        layerSlider.max = graphData.numLayers;
        layerSlider.value = 1;
        document.getElementById('layerValue').textContent = 0;
    }

    async function selectFile(file) {
        try {
            selectedFile = file;

            await eel.read_cli(file)();

            const numLayers = await eel.get_num_layers()();

            if (showHatchLines) {
                retrieveHashLines();
            } else {
                retrieveBoundingBoxes();
            }
            const numHatches = await eel.get_num_hatches()();
            graphData.numLayers = numLayers;
            graphData.numHatches = numHatches;
            graphData.curLayer = 0;

            const r_values = await eel.get_r_from_layer()();
            graphData.rValues = r_values;

            displayRValues();
            updateLayerSlider();
            updateHatchSlider();
            document.getElementById('graph-container').style.display = 'block';
            updateGraph(0);
        } catch (error) {
            console.error('Error loading file:', error);
            document.getElementById('graph-container').style.display = 'none';
        }
    }

    async function loadMaterials() {
        try {
            // Wait for materials to load
            const materials = await eel.get_materials()();

            // Add material options
            Object.keys(materials).forEach(material => {
                const option = document.createElement('option');
                option.value = JSON.stringify(materials[material]);
                option.textContent = material.replace(/_/g, ' ').toUpperCase();
                materialNameDropdown.appendChild(option);
            });

            // Add custom option last
            const option = document.createElement('option');
            option.value = "custom";
            option.textContent = "Custom Material";
            materialNameDropdown.appendChild(option);

            const event = new Event('change');
            materialNameDropdown.dispatchEvent(event);
        } catch (error) {
            console.error('Error loading materials:', error);
        }
    }

    async function loadFileHistory() {
        try {
            const files = await eel.view_processed_files()();
            const fileHistory = document.getElementById('fileHistory');
            const pagination = document.querySelector('.pagination');
            fileHistory.innerHTML = '';

            // Calculate pagination
            const totalPages = Math.ceil(files.length / itemsPerPage);
            console.log(totalPages);
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = startIndex + itemsPerPage;
            const currentFiles = files.slice(startIndex, endIndex);

            // Create file buttons
            currentFiles.forEach(file => {
                const buttonGroup = document.createElement('div');
                buttonGroup.className = 'btn-group w-100 mb-2';

                const fileButton = document.createElement('button');
                fileButton.type = 'button';
                fileButton.className = 'btn btn-outline-secondary text-start';
                fileButton.textContent = file;
                fileButton.onclick = () => {
                    if (activeButton) {
                        activeButton.classList.remove('active');
                    }
                    activeButton = fileButton;
                    activeButton.classList.add('active');
                    showHatchLines = false;
                    showHatchLinesCheckbox.checked = false;
                    selectFile(file);
                };

                const navButton = document.createElement('button');
                navButton.type = 'button';
                navButton.className = 'btn btn-outline-primary nav-btn';
                navButton.innerHTML = '<i class="bi bi-folder"></i>';
                navButton.onclick = () => {
                    eel.open_file_location(file)();
                };

                buttonGroup.appendChild(fileButton);
                buttonGroup.appendChild(navButton);
                fileHistory.appendChild(buttonGroup);
            });

            const prevPageItem = pagination.querySelector('.page-item:first-child');
            const nextPageItem = pagination.querySelector('.page-item:last-child');

            prevPageItem.classList.toggle('disabled', currentPage === 1);
            prevPageItem.querySelector('.page-link').onclick = (e) => {
                e.preventDefault();
                if (currentPage > 1) {
                    currentPage--;
                    loadFileHistory();
                }
            };

            // Handle Next button
            nextPageItem.classList.toggle('disabled', currentPage === totalPages);
            nextPageItem.querySelector('.page-link').onclick = (e) => {
                e.preventDefault();
                if (currentPage < totalPages) {
                    currentPage++;
                    loadFileHistory();
                }
            };

        } catch (error) {
            console.error('Error loading file history:', error);
        }
    }

    async function processFile() {
        const fileInput = document.getElementById('cliFile');

        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            try {
                // Read file content
                const fileContent = await readFileContent(file);

                // Send file content and name to Python
                await eel.convert_cli_file(fileContent, file.name, selectedMaterial)();
                checkTaskStatus(file.name);

            } catch (error) {
                console.error('Error processing file:', error);
            }
        }
    }

    async function checkTaskStatus(filename) {
        const loadingBar = document.getElementById('loadingBar');
        const loadingProgress = document.getElementById('loadingProgress');
        let progress = 0;
        loadingBar.style.display = 'block';
        const interval = setInterval(async () => {
            const status = await eel.get_task_status(filename)();

            if ("progress" in status) {
                progress = status.progress * 100;
                loadingProgress.style.width = progress + '%';
            } else {
                clearInterval(interval);
                loadingBar.style.display = 'none';
                loadFileHistory();
                loadMaterials();
            }
            return status;
        }, 1000);
    }

    function readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = (event) => {
                resolve(event.target.result);
            };

            reader.onerror = (error) => {
                reject(error);
            };

            reader.readAsText(file);
        });
    }

    function createScatterTraces(boxes) {
        let rate = 120 / graphData.numHatches * 3;
        return boxes.map((box, index) => {
            const x = box[0];
            const y = box[1];
            let radian = (boxes.length - index) * rate
            if (radian >= 120) {
                radian = 120
            }
            color = `hsl(${radian}, 100%, 50%)`;

            return {
                x: x,
                y: y,
                type: 'scatter',
                mode: 'lines',  // Remove markers, lines only
                fill: 'toself',
                fillcolor: color, // More solid fill
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

    function updateGraph(layerIndex) {
        try {
            if (!graphData.layers || graphData.numLayers === 0) {
                console.warn('No graph data available');
                return;
            }

            const xPadding = (graphData.x_max - graphData.x_min) * 0.1;
            const yPadding = (graphData.y_max - graphData.y_min) * 0.1;
            var data = [];

            if (showHatchLines) {
                for (let i = 0; i < graphData.layers.x.length; i += 2) {
                    data.push({
                        x: [graphData.layers.x[i], graphData.layers.x[i + 1]],
                        y: [graphData.layers.y[i], graphData.layers.y[i + 1]],
                        mode: 'lines',
                        type: 'scattergl',
                        line: {
                            width: 1,
                            color: 'blue'
                        },
                        showlegend: false
                    });
                }
            } else {
                data = createScatterTraces(graphData.layers);
            }

            const layout = {
                title: `Layer ${layerIndex}`,
                xaxis: {
                    title: 'X',
                    scaleanchor: 'y',  // Make axes equal scale
                    scaleratio: 1,
                    range: [graphData.x_min - xPadding, graphData.x_max + xPadding]
                },
                yaxis: {
                    title: 'Y',
                    range: [graphData.y_min - yPadding, graphData.y_max + yPadding]
                },
                hovermode: false,
                showlegend: false
            };

            const config = {
                responsive: true,
                displayModeBar: true,
                scrollZoom: true
            };

            Plotly.newPlot('plot', data, layout, config);
        } catch (error) {
            console.error('Error updating graph:', error);
        }
    }

    function updateTerminalOutput(output) {
        const terminal = document.getElementById('terminal');
        terminal.scrollTop = terminal.scrollHeight

        terminal.textContent += output + "\n";
    }
    eel.expose(updateTerminalOutput);
});
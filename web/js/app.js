document.addEventListener('DOMContentLoaded', function () {

    window.electronAPI.onDirectorySelected(async (path) => {
        if (path) {
            await eel.change_output_dir(path)();
        }
    });

    window.addEventListener('resize', () => {
        updateGraphCompare(optimizedGraphData.curLayer)
    }, true);

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

    var optimizedGraphData = {
        layers: [],
        numLayers: 0,
        numHatches: 0,
        curLayer: 0,
        curHatch: 0,
        rValues: [],
    };

    var completeTrace;
    var activeButton = null;
    var showHatchLines = false;
    var isPlaying = false;
    var playInterval = null;
    var playSpeed = 250; // Default 1 second interval

    // Analysis Screen
    const layerSlider = document.getElementById('layerSlider');
    const hatchSlider = document.getElementById('hatchSlider');
    const speedRange = document.getElementById('speedRange');
    const showHatchLinesCheckbox = document.getElementById('showHatchCheckbox');
    const refreshButton = document.getElementById('refreshButton');
    const playButton = document.getElementById('playButton');
    const processButton = document.getElementById('processButton');
    const rOptimizedLabel = document.getElementById('rOptimized');
    const rOriginalLabel = document.getElementById('rOriginal');

    // Custom Material
    const materialForm = document.getElementById('materialForm');
    const materialNameDropdown = document.getElementById('materialName');
    const customMaterialConfigFields = document.getElementById('custom-material-config');
    const customMaterialConfigInput = document.querySelectorAll("#custom-material-config input");

    // Custom Machine
    const machineForm = document.getElementById('machineForm');
    const machineNameDropdown = document.getElementById('machineName');
    const customMachineConfigFields = document.getElementById('custom-machine-config');
    const customMachineConfigInput = document.querySelectorAll("#custom-machine-config input");

    const loadingStatus = document.getElementById('loadingStatus');
    const resizer = document.getElementById('dragMe');
    const viewButton = document.getElementById('viewButton');
    const viewMaterialParamsButton = document.getElementById('view-materials');
    const viewMachineParamsButton = document.getElementById('view-machines');
    const spinner = document.getElementById('spinner');

    const leftSide = resizer.previousElementSibling;
    const rightSide = resizer.nextElementSibling;

    let x = 0;
    let y = 0;
    let leftWidth = 0;

    var materials = {};
    var machines = {};
    var selectedMaterial = {};
    var selectedMachine = {}
    let currentPage = 1;
    const itemsPerPage = 5;

    window.addEventListener('load', async () => {
        await loadFileHistory();
        await loadMaterials();
        await loadMachines();
    });


    if (
        layerSlider
        && hatchSlider
        && speedRange
        && showHatchLinesCheckbox
        && refreshButton
        && playButton
        && processButton
        && materialNameDropdown
        && customMaterialConfigFields
        && materialForm
        && machineNameDropdown
        && customMachineConfigFields
        && machineForm
        && resizer
        && viewMaterialParamsButton
        && viewMachineParamsButton
    ) {
        layerSlider.addEventListener('input', async (event) => {
            const layerIndex = parseInt(event.target.value);
            document.getElementById('layerValue').textContent = layerIndex;
            await eel.set_current_data_layer(layerIndex)();
            await eel.set_current_opti_layer(layerIndex)();
            await eel.set_current_data_hatch(0)();
            await eel.set_current_opti_hatch(0)();

            rawGraphData.numHatches = await eel.get_num_hatches_data()();
            rawGraphData.curHatch = 0;
            rawGraphData.curLayer = layerIndex;

            optimizedGraphData.numHatches = await eel.get_num_hatches_opti()();
            optimizedGraphData.curHatch = 0;
            optimizedGraphData.curLayer = layerIndex;

            const r_values = await eel.get_r_from_opti_layer()();
            optimizedGraphData.rValues = r_values;
            displayRValues();

            await loadCompleteBoundingBoxes();
            if (showHatchLines) {
                await retrieveHashLines();
            } else {
                await retrieveBoundingBoxes();
            }

            updateHatchSlider();
            updateGraphCompare(optimizedGraphData.layerIndex);
        });

        hatchSlider.addEventListener('input', async (event) => {
            const hatchIndex = parseInt(event.target.value);
            document.getElementById('hatchesValue').textContent = event.target.value;
            await eel.set_current_data_hatch(hatchIndex)();
            await eel.set_current_opti_hatch(hatchIndex)();

            rawGraphData.curHatch = hatchIndex;
            optimizedGraphData.curHatch = hatchIndex;

            if (showHatchLines) {
                await retrieveHashLines();
            } else {
                await retrieveBoundingBoxes();
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
                await retrieveHashLines();
            } else {
                await retrieveBoundingBoxes();
            }
        });

        materialNameDropdown.addEventListener('change', () => {
            let selectedValue = materialNameDropdown.value;
            if (selectedValue === 'custom') {
                enableMaterialsForm();

                customMaterialConfigFields.style.display = 'grid';
                customMaterialConfigInput.forEach(input => {
                    input.required = true;
                    input.addEventListener('input', () => {
                        updateCustomMaterial();
                    });
                });
            } else {
                let nameField = document.getElementById('custom-material-name');
                let ktField = document.getElementById('kt');
                let rhoField = document.getElementById('rho');
                let cpField = document.getElementById('cp');
                let hField = document.getElementById('h');

                selectedValue = JSON.parse(selectedValue);

                nameField.value = selectedValue.name;
                ktField.value = Number(selectedValue.kt);
                rhoField.value = Number(selectedValue.rho);
                cpField.value = Number(selectedValue.cp);
                hField.value = Number(selectedValue.h);

                disableMaterialsForm(with_select = false);
                selectedMaterial = materialNameDropdown.value;
            }
        });

        machineNameDropdown.addEventListener('change', () => {

            if (machineNameDropdown.value === 'custom') {
                enableMachinesForm();

                customMachineConfigFields.style.display = 'grid';
                customMachineConfigInput.forEach(input => {
                    input.required = true;
                    input.addEventListener('input', () => {
                        updateCustomMachine();
                    });
                });
            } else {
                let nameField = document.getElementById('custom-machine-name');
                let vsField = document.getElementById('vs');
                let PField = document.getElementById('P');

                nameField.value = JSON.parse(machineNameDropdown.value).name;
                vsField.value = Number(JSON.parse(machineNameDropdown.value).vs);
                PField.value = Number(JSON.parse(machineNameDropdown.value).P);

                disableMachinesForm(with_select = false);
                // customMachineConfigFields.style.display = 'none';
                selectedMachine = machineNameDropdown.value;
            }
        });

        viewMaterialParamsButton.addEventListener('click', e => openMaterialParams(e));

        viewMachineParamsButton.addEventListener('click', e => openMachineParams(e));

        viewButton.addEventListener('click', openViewWindow);

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

            var newLeftWidth = ((leftWidth + dx) * 100) / resizer.parentNode.getBoundingClientRect().width;

            if (newLeftWidth < 25) {
                newLeftWidth = 25;
            }

            if (newLeftWidth > 70) {
                newLeftWidth = 70;
            }

            document.documentElement.style.setProperty('--left-panel-width', newLeftWidth + '%');
            document.documentElement.style.setProperty('--right-panel-width', 100 - newLeftWidth + '%');

            updateGraphCompare(optimizedGraphData.curLayer);

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

    function openMaterialParams(e) {
        if (customMaterialConfigFields.style.display === 'grid') {
            viewMaterialParamsButton.innerHTML = 'View material params <i class="bi bi-chevron-down"></i>';
            customMaterialConfigFields.style.display = 'none';
        } else {
            viewMaterialParamsButton.innerHTML = 'Close <i class="bi bi-chevron-up"></i>';
            customMaterialConfigFields.style.display = 'grid';
        }
        e.preventDefault();
    }

    function openMachineParams(e) {
        if (customMachineConfigFields.style.display === 'grid') {
            viewMachineParamsButton.innerHTML = 'View machines params <i class="bi bi-chevron-down"></i>';
            customMachineConfigFields.style.display = 'none';
        } else {
            viewMachineParamsButton.innerHTML = 'Close <i class="bi bi-chevron-up"></i>';
            customMachineConfigFields.style.display = 'grid';
        }
        e.preventDefault();
    }

    eel.expose(displayStatus)
    function displayStatus(status) {
        if (loadingStatus) {
            loadingStatus.textContent = status;
        }
    }

    eel.expose(displayError)
    function displayError(message, status) {
        alert(message, status);
    }

    function disableMaterialsForm(with_select = false) {

        var materialElements;
        if (with_select) {
            materialElements = document.querySelectorAll("#materialForm input, #materialForm select");
        } else {
            materialElements = document.querySelectorAll("#materialForm input");
        }

        materialElements.forEach(element => {
            element.disabled = true;
        }
        );

    }

    function disableMachinesForm(with_select = false) {
        var machineElements = '';
        if (with_select) {
            machineElements = document.querySelectorAll("#machineForm input, #machineForm select");
        } else {
            machineElements = document.querySelectorAll("#machineForm input");
        }

        machineElements.forEach(element => {
            element.disabled = true;
        }
        );
    }

    function enableMaterialsForm(with_select = false) {
        var materialElements;
        if (with_select) {
            materialElements = document.querySelectorAll("#materialForm input, #materialForm select");
        } else {
            materialElements = document.querySelectorAll("#materialForm input");
        }

        materialElements.forEach(element => {
            element.disabled = false;
            element.value = "";
        }
        );

    }

    function enableMachinesForm(with_select = false) {

        var machineElements;
        if (with_select) {
            machineElements = document.querySelectorAll("#machineForm input, #machineForm select");
        } else {
            machineElements = document.querySelectorAll("#machineForm input");
        }

        machineElements.forEach(element => {
            element.disabled = false;
            element.value = "";
        }
        );
    }

    async function openViewWindow() {

        const fileInput = document.getElementById('cliFile');
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            try {
                if (!checkFileType(file.name)) {
                    processButton.disabled = false;
                    viewButton.disabled = false;
                    enableMaterialsForm();
                    enableMachinesForm();
                    displayError("Invalid file type! Please attach a .cli file.", "Error");
                    return;
                }

                const fileContent = await readFileContent(file);
                displayStatus("Opening View...");

                await window.electronAPI.openViewWindow(file.name);
                await window.electronAPI.sendToView(fileContent)
                displayStatus("");
            } catch (error) {
                console.error('Error opening view:', error);
            }
        } else {
            displayError("Please attach a file to view!", "Error");
        }
    }

    function updateCustomMaterial() {
        selectedMaterial = {
            name: document.getElementById('custom-material-name').value || '',
            kt: parseFloat(document.getElementById('kt').value) || 0,
            rho: parseFloat(document.getElementById('rho').value) || 0,
            cp: parseFloat(document.getElementById('cp').value) || 0,
            h: parseFloat(document.getElementById('h').value) || 0
        };
    }

    function updateCustomMachine() {
        selectedMachine = {
            name: document.getElementById('custom-machine-name').value || '',
            vs: parseFloat(document.getElementById('vs').value) || 0,
            P: parseFloat(document.getElementById('P').value) || 0
        };
    }

    function isDouble(str) {
        const num = parseFloat(str);
        return !isNaN(num) && isFinite(num);
    }

    function displayRValues() {
        r_values = optimizedGraphData.rValues;
        rOptimizedLabel.textContent = isDouble(r_values[0]) ? r_values[0] : "NaN";
        rOriginalLabel.textContent = isDouble(r_values[1]) ? r_values[1] : "NaN";
    }

    async function retrieveHashLines() {
        const dataCoords = await eel.retrieve_coords_from_data_cur()();
        rawGraphData.layers = dataCoords;
        rawGraphData.x_min = dataCoords.x_min;
        rawGraphData.x_max = dataCoords.x_max;
        rawGraphData.y_min = dataCoords.y_min;
        rawGraphData.y_max = dataCoords.y_max;

        const optiCoords = await eel.retrieve_coords_from_opti_cur()();
        optimizedGraphData.layers = optiCoords;
        optimizedGraphData.x_min = optiCoords.x_min;
        optimizedGraphData.x_max = optiCoords.x_max;
        optimizedGraphData.y_min = optiCoords.y_min;
        optimizedGraphData.y_max = optiCoords.y_max;
        updateGraphCompare(optimizedGraphData.curLayer);
    }

    async function loadCompleteBoundingBoxes() {
        const completeCoords = await eel.retrieve_full_bounding_box_opti()();
        completeGraphData.layers = completeCoords.bounding_boxes;
        completeGraphData.x_min = completeCoords.x_min;
        completeGraphData.x_max = completeCoords.x_max;
        completeGraphData.y_min = completeCoords.y_min;
        completeGraphData.y_max = completeCoords.y_max;

        createCompleteTrace();
    }

    async function retrieveBoundingBoxes() {
        const dataCoords = await eel.retrieve_bounding_box_from_data_layer()();
        rawGraphData.layers = dataCoords.bounding_boxes;
        rawGraphData.x_min = dataCoords.x_min;
        rawGraphData.x_max = dataCoords.x_max;
        rawGraphData.y_min = dataCoords.y_min;
        rawGraphData.y_max = dataCoords.y_max;

        const optiCoords = await eel.retrieve_bounding_box_from_opti_layer()();
        optimizedGraphData.layers = optiCoords.bounding_boxes;
        optimizedGraphData.x_min = optiCoords.x_min;
        optimizedGraphData.x_max = optiCoords.x_max;
        optimizedGraphData.y_min = optiCoords.y_min;
        optimizedGraphData.y_max = optiCoords.y_max;
        updateGraphCompare(optimizedGraphData.curLayer);
    }

    function togglePlay() {
        const playButton = document.getElementById('playButton');
        const hatchSlider = document.getElementById('hatchSlider');
        isPlaying = !isPlaying;

        if (isPlaying) {
            playButton.innerHTML = '<i class="bi bi-pause-fill"></i>';
            const current = optimizedGraphData.curHatch < optimizedGraphData.numHatches;

            if (!current) {
                optimizedGraphData.curHatch = 0;
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
            if (currentHatch >= optimizedGraphData.numHatches) {
                togglePlay(); // Stop when reached end
                return;
            }

            currentHatch++;
            hatchSlider.value = currentHatch;
            document.getElementById('hatchesValue').textContent = currentHatch;

            await eel.set_current_data_hatch(currentHatch)();
            await eel.set_current_opti_hatch(currentHatch)();
            optimizedGraphData.curHatch = currentHatch;
            if (showHatchLines) {
                await retrieveHashLines();
            } else {
                await retrieveBoundingBoxes();
            }
            updateGraphCompare(optimizedGraphData.curLayer);
        }, playSpeed);
    }

    // Add speed control

    function updateHatchSlider() {
        const hatchSlider = document.getElementById('hatchSlider');
        hatchSlider.max = rawGraphData.numHatches;
        hatchSlider.value = 0;
        document.getElementById('hatchesValue').textContent = 0;
    }

    function updateLayerSlider() {
        const layerSlider = document.getElementById('layerSlider');
        layerSlider.max = rawGraphData.numLayers;
        layerSlider.value = 1;
        document.getElementById('layerValue').textContent = 0;
    }

    async function selectFile(file) {
        try {
            selectedFile = file;
            spinner.style.display = "flex";

            await eel.compare_cli(file)();

            const numLayersOpti = await eel.get_num_layers_opti()();
            const numHatchesOpti = await eel.get_num_hatches_opti()();
            const numLayersRaw = await eel.get_num_layers_data()();
            const numHatchesRaw = await eel.get_num_hatches_data()();

            if (numLayersOpti != numLayersRaw) {
                displayError("Number of layers in raw and optimized files do not match!", "Error");
                return;
            }

            if (numHatchesOpti != numHatchesRaw) {
                displayError("Number of hatches in raw and optimized files do not match!", "Error");
                return;
            }

            // Get full bounding box then the actual bounding box
            await loadCompleteBoundingBoxes();
            if (showHatchLines) {
                await retrieveHashLines();
            } else {
                await retrieveBoundingBoxes();
            }

            rawGraphData.numLayers = numLayersRaw;
            rawGraphData.numHatches = numHatchesRaw;
            rawGraphData.curLayer = 0;

            optimizedGraphData.numLayers = numLayersOpti;
            optimizedGraphData.numHatches = numHatchesOpti;
            optimizedGraphData.curLayer = 0;

            const r_values = await eel.get_r_from_opti_layer()();
            rawGraphData.rValues = r_values;
            optimizedGraphData.rValues = r_values;

            displayRValues();
            updateLayerSlider();
            updateHatchSlider();

            spinner.style.display = "none";
            document.getElementById('analysis-container').style.display = 'flex';
            updateGraphCompare(0);

        } catch (error) {
            console.error('Error loading file:', error);
            document.getElementById('analysis-container').style.display = 'none';
        }
    }

    async function loadMaterials() {
        try {
            // Wait for materials to load
            const materialObjects = await eel.get_materials()();

            materialNameDropdown.innerHTML = '';
            // Add material options
            Object.keys(materialObjects).forEach(material => {
                materials[material] = materialObjects[material];

                const option = document.createElement('option');
                option.value = JSON.stringify(materialObjects[material]);
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

    async function loadMachines() {
        try {
            // Wait for materials to load
            const machinesObject = await eel.get_machines()();

            machineNameDropdown.innerHTML = '';
            // Add material options
            Object.keys(machinesObject).forEach(machine => {
                machines[machine] = machinesObject[machine];

                const option = document.createElement('option');
                option.value = JSON.stringify(machinesObject[machine]);
                option.textContent = machine.replace(/_/g, ' ').toUpperCase();
                machineNameDropdown.appendChild(option);
            });

            // Add custom option last
            const option = document.createElement('option');
            option.value = "custom";
            option.textContent = "Custom Machine";
            machineNameDropdown.appendChild(option);

            const event = new Event('change');
            machineNameDropdown.dispatchEvent(event);
        } catch (error) {
            console.error('Error loading machines:', error);
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

    function checkFileType(filename) {
        const validExtensions = ['cli'];
        const extension = filename.split('.').pop();
        return validExtensions.includes(extension);
    }

    async function processFile() {
        processButton.disabled = true;
        viewButton.disabled = true;

        disableMaterialsForm();
        disableMachinesForm();
        const fileInput = document.getElementById('cliFile');

        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];

            if (!checkFileType(file.name)) {
                processButton.disabled = false;
                viewButton.disabled = false;
                enableMaterialsForm();
                enableMachinesForm();
                displayError("Invalid file type! Please attach a .cli file.", "Error");
                return;
            }

            try {
                // Read file content
                displayStatus("Reading file...");
                const fileContent = await readFileContent(file);

                displayStatus("Copying file...");
                // Send file content and name to Python
                await eel.convert_cli_file(fileContent, file.name, selectedMaterial, selectedMachine)();
                checkTaskStatus(file.name);

            } catch (error) {
                console.error('Error processing file:', error);
            }
        } else {
            processButton.disabled = false;
            viewButton.disabled = false;
            enableMaterialsForm();
            enableMachinesForm();
            displayError("Please attached a file to process!", "Error");
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
                processButton.disabled = false;
                viewButton.disabled = false;
                enableMaterialsForm();
                enableMachinesForm();
                loadingStatus.innerText = "";
                loadingBar.style.display = 'none';
                await loadFileHistory();
                await loadMaterials();
                await loadMachines();
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

    function createCompleteTrace() {
        const boxes = completeGraphData.layers;

        completeTrace = boxes.map((box, index) => {
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

        return;
    }

    function createScatterTraces(boxes) {
        let rate = 120 / optimizedGraphData.numHatches * 3;
        return boxes.map((box, index) => {
            const x = box[0];
            const y = box[1];
            let radian = (boxes.length - index) * rate;
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

    function updateGraphCompare(layerIndex) {
        try {
            if (!optimizedGraphData.layers || optimizedGraphData.numLayers === 0 || rawGraphData.numLayers === 0 || !rawGraphData.layers) {
                return;
            }
            if (optimizedGraphData.numLayers != rawGraphData.numLayers) {
                return;
            }

            const analysisContainer = document.getElementById('analysis-container');

            const xPadding = (optimizedGraphData.x_max - optimizedGraphData.x_min) * 0.1;
            const yPadding = (optimizedGraphData.y_max - optimizedGraphData.y_min) * 0.1;
            var rawData = [];
            var optiData = [];

            if (showHatchLines) {
                for (let i = 0; i < optimizedGraphData.layers.x.length; i += 2) {
                    rawData.push({
                        x: [rawGraphData.layers.x[i], rawGraphData.layers.x[i + 1]],
                        y: [rawGraphData.layers.y[i], rawGraphData.layers.y[i + 1]],
                        mode: 'lines',
                        type: 'scattergl',
                        line: {
                            width: 1,
                            color: 'blue'
                        },
                        showlegend: false
                    });
                    optiData.push({
                        x: [optimizedGraphData.layers.x[i], optimizedGraphData.layers.x[i + 1]],
                        y: [optimizedGraphData.layers.y[i], optimizedGraphData.layers.y[i + 1]],
                        mode: 'lines',
                        type: 'scattergl',
                        line: {
                            width: 1,
                            color: 'green'
                        },
                        showlegend: false
                    });
                }
            } else {
                optiData = createScatterTraces(optimizedGraphData.layers);
                rawData = createScatterTraces(rawGraphData.layers);
            }

            function getLayout(title) {

                const layout = {
                    width: analysisContainer.clientWidth / 2,
                    title: `${title}\nLayer ${layerIndex}`,
                    xaxis: {
                        title: 'X',
                        scaleanchor: 'y',  // Make axes equal scale
                        scaleratio: 1,
                        range: [optimizedGraphData.x_min - xPadding, optimizedGraphData.x_max + xPadding]
                    },
                    yaxis: {
                        title: 'Y',
                        range: [optimizedGraphData.y_min - yPadding, optimizedGraphData.y_max + yPadding]
                    },
                    hovermode: false,
                    showlegend: false
                };

                return layout;
            }

            const config = {
                responsive: true,
                displayModeBar: true,
                scrollZoom: true
            };

            let rawPlotData = [...completeTrace, ...rawData]
            let optiPlotData = [...completeTrace, ...optiData]
            Plotly.newPlot('data_plot', rawPlotData, getLayout("Pre-Opt"), config);
            Plotly.newPlot('opti_plot', optiPlotData, getLayout("Post-Opt"), config);
        } catch (error) {
            console.error('Error updating graph:', error);
        }
    }

});
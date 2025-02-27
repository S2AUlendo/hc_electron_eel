document.addEventListener('DOMContentLoaded', function () {

    window.electronAPI.onDirectorySelected(async (path) => {
        if (path) {
            await eel.change_output_dir(path)();
        }
    });

    window.electronAPI.enterNewKey(async () => {
        await eel.show_upgrade_screen()();
    });

    window.electronAPI.getAppInfo(async () => {
        try {
            let response = await eel.get_app_info()();
            // now we render about us window
            await window.electronAPI.openAboutWindow(response);
        } catch (error) {
            displayError(`Error getting app info: ${error}`, "App Error");
        }
    });

    window.electronAPI.checkMpRunning(async () => {
        try {
            let response = await eel.is_multiprocessing_running()();
            // now we render about us window
            await window.electronAPI.mpRunningResponse(response);
        } catch (error) {
            displayError(`Error getting app info: ${error}`, "App Error");
        }
    });

    window.addEventListener('resize', () => {
        if (!selectedFile) return;

        plotRValues();
        if (showOriginal) {
            updateGraphCompare(optimizedGraphData.curLayer)
        } else {
            updateGraph(optimizedGraphData.curLayer)
        }
    }, true);

    function removeClassStartsWith(element, className) {
        element.className = element.className.split(" ").filter(c => !c.startsWith(className)).join(" ");
    }

    var completeGraphData = {
        layers: [],
        numLayers: 0,
        numHatches: 0,
        curLayer: 0,
        curHatch: 0,
        rVal: []
    }

    var rawGraphData = {
        layers: [],
        numLayers: 0,
        numHatches: 0,
        curLayer: 0,
        curHatch: 0,
        rVal: [],
        rMean: 0
    }

    var optimizedGraphData = {
        layers: [],
        numLayers: 0,
        numHatches: 0,
        curLayer: 0,
        curHatch: 0,
        rVal: [],
        rMean: 0
    };

    var inputFile;
    var selectedFile;
    var completeTrace;
    var activeButton = null;
    var showHatchLines = false;
    var showOriginal = false;
    var isPlaying = false;
    var playInterval = null;
    var playSpeed = 250; // Default 1 second interval

    const chartConfiguration = {
        responsive: true,
        displayModeBar: true,
        scrollZoom: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['select2d', 'lasso2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines']
    };

    // Analysis Screen
    const fileInput = document.getElementById('electronFileButton');
    const inputFileText = document.getElementById('filePathDisplay');

    const layerSlider = document.getElementById('layerSlider');
    const hatchSlider = document.getElementById('hatchSlider');
    const speedRange = document.getElementById('speedRange');
    const showHatchLinesCheckbox = document.getElementById('showHatchCheckbox');
    const showOriginalCheckBox = document.getElementById('showOriginalCheckbox');
    const refreshButton = document.getElementById('refreshButton');
    const playButton = document.getElementById('playButton');
    const processButton = document.getElementById('processButton');
    const dataPlot = document.getElementById('data_plot');

    // Custom Material
    var materialCanEdit = false;
    const materialForm = document.getElementById('materialForm');
    const materialNameDropdown = document.getElementById('materialName');
    const customMaterialConfigFields = document.getElementById('custom-material-config');
    const customMaterialConfigInput = document.querySelectorAll("#custom-material-config input");

    // Custom Machine
    var machineCanEdit = false;
    const machineForm = document.getElementById('machineForm');
    const machineNameDropdown = document.getElementById('machineName');
    const customMachineConfigFields = document.getElementById('custom-machine-config');
    const customMachineConfigInput = document.querySelectorAll("#custom-machine-config input");

    // Progress Container
    const loadingStatus = document.getElementById('loadingStatus');
    const loadingBar = document.getElementById('loadingBar');
    const loadingProgress = document.getElementById('loadingProgress');
    const progressContainer = document.getElementById('progress-container');
    const cancelButton = document.getElementById('cancelButton');

    const resizer = document.getElementById('dragMe');
    const viewButton = document.getElementById('viewButton');
    const viewMaterialParamsButton = document.getElementById('view-materials');
    const viewMachineParamsButton = document.getElementById('view-machines');
    const spinner = document.getElementById('spinner');
    const idleScreen = document.getElementById('idle-container');
    const navContainer = document.getElementById('nav-container');
    const alertStatus = document.getElementById('alert-status');
    const alertTitle = document.getElementById('alert-title');
    const alertMessage = document.getElementById('alert-message');
    const alertCloseButton = document.getElementById('alert-close-btn');

    const leftSide = resizer.previousElementSibling;
    const rightSide = resizer.nextElementSibling;

    const editMaterialButton = document.getElementById('editMaterialButton');
    const deleteMaterialButton = document.getElementById('deleteMaterialButton');
    const saveMaterialButton = document.getElementById('saveMaterialButton');
    const editMachineButton = document.getElementById('editMachineButton');
    const deleteMachineButton = document.getElementById('deleteMachineButton');
    const saveMachineButton = document.getElementById('saveMachineButton');

    const rGrade = document.getElementById('r-grade');

    let x = 0;
    let y = 0;
    let leftWidth = 0;

    var versionNumber = "";
    var machines = {};
    var selectedMaterial = {
        name: "",
        kt: 0,
        rho: 0,
        cp: 0,
        h: 0
    };
    var selectedMaterialCategory = "";
    var selectedMachine = {
        name: "",
        vs: 0,
        P: 0
    }
    let currentPage = 1;
    const itemsPerPage = 5;

    window.addEventListener('load', async () => {

        await loadFileHistory();
        await loadMaterials();
        await loadMachines();

        let response = await eel.get_app_info()();
        versionNumber = document.getElementById('version-number');
        versionNumber.textContent = response.version;
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

            const ori_r_values = await eel.get_r_from_data_layer()();
            const opt_r_values = await eel.get_r_from_opti_layer()();
            const ori_r_mean = await eel.get_r_mean_from_data_layer()();
            const opt_r_mean = await eel.get_r_mean_from_opti_layer()();

            rawGraphData.rVal = ori_r_values;
            optimizedGraphData.rVal = opt_r_values
            rawGraphData.rMean = ori_r_mean;
            optimizedGraphData.rMean = opt_r_mean;

            await loadCompleteBoundingBoxes();
            if (showHatchLines) {
                await retrieveHashLines();
            } else {
                await retrieveBoundingBoxes();
            }

            updateHatchSlider();

            plotRValues();
            if (showOriginal) {
                updateGraphCompare(layerIndex);
            } else {
                updateGraph(layerIndex);
            }
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

        showOriginalCheckBox.addEventListener('change', async (e) => {
            showOriginal = e.target.checked;
            if (showOriginal) {
                dataPlot.style.display = 'block';
                updateGraphCompare(optimizedGraphData.curLayer);
            } else {
                dataPlot.style.display = 'none';
                updateGraph(optimizedGraphData.curLayer);
            }
        }
        );

        customMaterialConfigInput.forEach(input => {
            input.required = true;
        });

        alertCloseButton.addEventListener('click', () => {
            alertStatus.style.display = 'none';
        });

        materialNameDropdown.addEventListener('change', () => {

            let selectedValue = materialNameDropdown.value;

            let nameField = document.getElementById('custom-material-name');
            let ktField = document.getElementById('kt');
            let rhoField = document.getElementById('rho');
            let cpField = document.getElementById('cp');
            let hField = document.getElementById('h');

            selectedValue = JSON.parse(selectedValue);
            selectedMaterial = selectedValue;
            let selectedOption = selectedValue.option;

            nameField.value = selectedValue.name;
            ktField.value = Number(selectedValue.kt);
            rhoField.value = Number(selectedValue.rho);
            cpField.value = Number(selectedValue.cp);
            hField.value = Number(selectedValue.h);

            if (selectedOption === 'custom') {
                enableMaterialsForm();
                selectedMaterialCategory = "Custom";
                deleteMaterialButton.disabled = true;
                customMaterialConfigFields.style.display = 'grid';

            } else {
                // Get category from parent optgroup
                const selectedOption = materialNameDropdown.options[materialNameDropdown.selectedIndex];
                selectedMaterialCategory = selectedOption.parentNode.label; // This gets the category
                deleteMaterialButton.disabled = false;
                disableMaterialsForm();
            }
        });

        customMachineConfigInput.forEach(input => {
            input.required = true;
        });

        machineNameDropdown.addEventListener('change', () => {

            let machineValue = machineNameDropdown.value;
            machineValue = JSON.parse(machineValue);
            selectedMachine = machineValue;

            let machineOption = machineValue.option;
            let nameField = document.getElementById('custom-machine-name');
            let vsField = document.getElementById('vs');
            let PField = document.getElementById('P');

            nameField.value = machineValue.name;
            vsField.value = Number(machineValue.vs);
            PField.value = Number(machineValue.P);

            if (machineOption === 'custom') {
                enableMachinesForm();
                deleteMachineButton.disabled = true;
                customMachineConfigFields.style.display = 'grid';
            } else {
                disableMachinesForm();
                deleteMachineButton.disabled = false;
            }
        });

        editMaterialButton.addEventListener('click', (e) => {
            e.preventDefault();
            if (materialCanEdit) {
                editMaterialButton.innerHTML = '<i class="bi bi-pencil-square me-2"></i> Edit';
                resetMaterialFormValue();
                disableMaterialsForm();
            } else {
                editMaterialButton.innerHTML = '<i class="bi bi-x-lg me-2"></i> Cancel Edit';
                enableMaterialsForm();
            }
        });

        editMachineButton.addEventListener('click', (e) => {
            e.preventDefault()
            if (machineCanEdit) {
                editMachineButton.innerHTML = '<i class="bi bi-pencil-square me-2"></i> Edit';
                resetMachineFormValue();
                disableMachinesForm();
            } else {
                editMachineButton.innerHTML = '<i class="bi bi-x-lg me-2"></i> Cancel Edit';
                enableMachinesForm();
            }
        });

        deleteMaterialButton.addEventListener('click', async (e) => {
            await eel.delete_material(selectedMaterialCategory, selectedMaterial)();
            displayAlert("Material deleted successfully!");
        });

        deleteMachineButton.addEventListener('click', async (e) => {
            await eel.delete_machine(selectedMachine)();
            displayAlert("Machine deleted successfullly!");
        });

        saveMaterialButton.addEventListener('click', async (e) => {
            e.preventDefault();
            updateMaterialValues();
            await eel.edit_material(selectedMaterialCategory, selectedMaterial)();
            await loadMaterials();
            showSuccessAlert("Success", "Material saved successfullly!");
        });

        saveMachineButton.addEventListener('click', async (e) => {
            e.preventDefault();
            updateMachineValues();
            await eel.edit_machine(selectedMachine)();
            await loadMachines();
            showSuccessAlert("Success", "Machine saved successfullly!");
        });

        viewMaterialParamsButton.addEventListener('click', e => openMaterialParams(e));

        viewMachineParamsButton.addEventListener('click', e => openMachineParams(e));

        viewButton.addEventListener('click', openViewWindow);

        processButton.addEventListener('click', processFile);

        refreshButton.addEventListener('click', loadFileHistory);

        playButton.addEventListener('click', togglePlay);

        fileInput.addEventListener('click', async (e) => {
            const result = await window.electronAPI.onSelectFile();

            if (result && !result.cancelled) {
                inputFile = {
                    path: result.filePaths[0],
                    name: extractFilenameFromPath(result.filePaths[0])
                };
                filePathDisplay.value = inputFile.name;
            }
        });

        function extractFilenameFromPath(path) {
            return path.split('\\').pop().split('/').pop();
        }
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

            resizer.style.cursor = 'col-resize';
            document.body.style.cursor = 'col-resize';

            leftSide.style.userSelect = 'none';
            leftSide.style.pointerEvents = 'none';

            rightSide.style.userSelect = 'none';
            rightSide.style.pointerEvents = 'none';

            if (!selectedFile) return;
            plotRValues();

            if (showOriginal) {
                updateGraphCompare(optimizedGraphData.curLayer);
            } else {
                updateGraph(optimizedGraphData.curLayer);
            }
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
        window.electronAPI.displayError(status, message);
        window.electronAPI.focus();
    }

    function displayAlert(message, status) {
        alert(message, status);
        window.electronAPI.focus();
    }

    function disableCLIInput() {
        fileInput.disabled = true;
    }

    function enableCLIInput() {
        fileInput.disabled = false;
    }

    function disableMaterialsSelect() {
        materialNameDropdown.disabled = true;
    }

    function disableMachinesSelect() {
        machineNameDropdown.disabled = true;
    }

    function disableMaterialsForm() {
        let materialElements = document.querySelectorAll("#materialForm input");
        materialCanEdit = false;

        materialElements.forEach(element => {
            element.disabled = true;
        }
        );
    }

    function resetMaterialFormValue() {
        document.getElementById('custom-material-name').value = selectedMaterial.name;
        document.getElementById('kt').value = selectedMaterial.kt;
        document.getElementById('rho').value = selectedMaterial.rho;
        document.getElementById('cp').value = selectedMaterial.cp;
        document.getElementById('h').value = selectedMaterial.h;
    }

    function resetMachineFormValue() {
        document.getElementById('custom-machine-name').value = selectedMachine.name;
        document.getElementById('vs').value = selectedMachine.vs;
        document.getElementById('P').value = selectedMachine.P;
    }

    function disableMachinesForm() {
        let machineElements = document.querySelectorAll("#machineForm input");
        machineCanEdit = false;

        machineElements.forEach(element => {
            element.disabled = true;
        }
        );
    }

    function enableMaterialsSelect() {
        materialNameDropdown.disabled = false;
    }

    function enableMachinesSelect() {
        machineNameDropdown.disabled = false;
    }

    function enableMaterialsForm() {
        let materialElements = document.querySelectorAll("#materialForm input");
        materialCanEdit = true;

        materialElements.forEach(element => {
            element.disabled = false;
        }
        );
    }

    function enableMachinesForm() {
        let machineElements = document.querySelectorAll("#machineForm input");
        machineCanEdit = true;

        machineElements.forEach(element => {
            element.disabled = false;
        }
        );
    }

    async function openViewWindow() {

        if (inputFile) {

            await window.electronAPI.openViewWindow(inputFile.name);
            await window.electronAPI.sendToView(inputFile)
        } else {
            showErrorAlert("Input Type Error", "Please attach a .cli file.");
        }
    }

    function updateMaterialValues() {
        selectedMaterial = {
            name: document.getElementById('custom-material-name').value || '',
            kt: parseFloat(document.getElementById('kt').value) || 0,
            rho: parseFloat(document.getElementById('rho').value) || 0,
            cp: parseFloat(document.getElementById('cp').value) || 0,
            h: parseFloat(document.getElementById('h').value) || 0
        };
    }

    function updateMachineValues() {
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

        if (showOriginal) {
            updateGraphCompare(optimizedGraphData.curLayer);
        } else {
            updateGraph(optimizedGraphData.curLayer);
        }
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

        if (showOriginal) {
            updateGraphCompare(optimizedGraphData.curLayer);
        } else {
            updateGraph(optimizedGraphData.curLayer);
        }
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

            if (showOriginal) {
                updateGraphCompare(optimizedGraphData.curLayer);
            } else {
                updateGraph(optimizedGraphData.curLayer);
            }
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
            idleScreen.style.display = 'none';
            navContainer.style.display = 'none';
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

            const ori_r_values = await eel.get_r_from_data_layer()();
            const opt_r_values = await eel.get_r_from_opti_layer()();
            const ori_r_mean = await eel.get_r_mean_from_data_layer()();
            const opt_r_mean = await eel.get_r_mean_from_opti_layer()();
            rawGraphData.rVal = ori_r_values;
            optimizedGraphData.rVal = opt_r_values;
            rawGraphData.rMean = ori_r_mean;
            optimizedGraphData.rMean = opt_r_mean;

            updateLayerSlider();
            updateHatchSlider();

            spinner.style.display = "none";

            selectedFile = file;
            navContainer.style.display = 'block';

            // Call plot only after nav container is displayed
            plotRValues();
            if (showOriginal) {
                updateGraphCompare(0);
            } else {
                updateGraph(0);
            }

        } catch (error) {
            displayError('Error loading file:', error);
            document.getElementById('analysis-container').style.display = 'none';
        }
    }

    async function loadMaterials() {
        try {
            const materialObjects = await eel.get_materials()();
            materialNameDropdown.innerHTML = '';
            let selectedValue = null; // Store the selected option value

            // Iterate through each category
            Object.entries(materialObjects).forEach(([category, materials]) => {
                // Create category group
                const optgroup = document.createElement('optgroup');
                optgroup.label = category;

                // Add materials to category
                Object.values(materials).forEach(material => {
                    const option = document.createElement('option');
                    material["option"] = material.name;
                    option.value = JSON.stringify(material);

                    // Selected Material exists (for edit actions)
                    if (selectedMaterial && selectedMaterial.name === material.name) {
                        selectedValue = option.value;
                    }

                    option.textContent = material.name;
                    optgroup.appendChild(option);
                });

                materialNameDropdown.appendChild(optgroup);
            });

            // Add custom option
            const option = document.createElement('option');
            option.value = JSON.stringify({
                option: "custom",
                name: "",
                kt: 0,
                rho: 0,
                cp: 0,
                h: 0
            });
            option.textContent = "Add Custom Material";
            materialNameDropdown.appendChild(option);
            if (selectedValue) {
                materialNameDropdown.value = selectedValue;
            }

            disableMaterialsForm();
            materialNameDropdown.dispatchEvent(new Event('change'));
        } catch (error) {
            displayError('Error loading materials:', error);
        }
    }

    async function loadMachines() {
        try {
            // Wait for materials to load
            const machinesObject = await eel.get_machines()();
            let selectedValue = null;

            machineNameDropdown.innerHTML = '';
            // Add material options
            Object.keys(machinesObject).forEach(machine => {
                machines[machine] = machinesObject[machine];

                const option = document.createElement('option');
                machinesObject[machine].option = "machine";
                option.value = JSON.stringify(machinesObject[machine]);

                // Selected Machine exists (for edit actions)
                if (selectedMachine && selectedMachine.name === machine) {
                    selectedValue = option.value;
                }

                option.textContent = machine.replace(/_/g, ' ');
                machineNameDropdown.appendChild(option);
            });

            // Add custom option last
            const option = document.createElement('option');
            option.value = JSON.stringify({
                name: "",
                vs: 0,
                P: 0,
                option: "custom"
            });
            option.textContent = "Add Custom Machine";
            machineNameDropdown.appendChild(option);

            // If found, we set the dropdown (Only after append child)
            if (selectedValue) {
                machineNameDropdown.value = selectedValue;
            }

            const event = new Event('change');

            disableMachinesForm();
            machineNameDropdown.dispatchEvent(event);
        } catch (error) {
            displayError('Error loading machines:', error);
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
                fileButton.id = file;
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
            displayError('Error loading file history:', error);
        }
    }

    function checkFileType(filename) {
        const validExtensions = ['cli'];
        const extension = filename.split('.').pop();
        return validExtensions.includes(extension);
    }

    function checkValidInput() {
        const checkMaterial = Object.values(selectedMaterial).every(value => {
            return value !== 0 && value !== '';
        });

        const checkMachine = Object.values(selectedMachine).every(value => {
            return value !== 0 && value !== '';
        });

        return checkMaterial && checkMachine;
    }

    async function cancelTask(filename) {
        const response = await eel.cancel_task(filename)();
        const status = response.status;
        const message = response.message;

        if (status != "error") {
            progressContainer.style.display = 'none';
        }

        if (status === "success") {
            showSuccessAlert("Success", message);
            enableAllCoreForms();
        } else if (status == "not_found") {
            showErrorAlert("Not Found", message);
        } else {
            showErrorAlert("Error", message);
        }
    }

    function enableAllCoreForms() {
        enableMaterialsSelect();
        enableMachinesSelect();
        enableCLIInput();
        processButton.disabled = false;
        viewButton.disabled = false;
    }

    function disableAllCoreForms() {
        disableMaterialsSelect();
        disableMachinesSelect();
        disableCLIInput();
        processButton.disabled = true;
        viewButton.disabled = true;
    }

    async function processFile() {

        if (!checkValidInput()) {
            showErrorAlert("Input Error", "Please fill in all fields!");
            return;
        }

        if (materialCanEdit || machineCanEdit) {
            showErrorAlert("Input Error", "Please save or cancel your changes before processing.");
            return;
        }

        disableAllCoreForms();

        if (inputFile) {

            if (!checkFileType(inputFile.name)) {
                enableAllCoreForms();
                showErrorAlert("Input Error", "Invalid file type! Please attach a .cli file.");
                return;
            }

            try {
                await eel.convert_cli_filepath(inputFile.path, inputFile.name, selectedMaterial, selectedMaterialCategory, selectedMachine)();
                checkTaskStatus(inputFile.name);

            } catch (error) {
                displayError('Error processing file:', error);
            }
        } else {
            enableAllCoreForms();
            showErrorAlert("Input Error", "Please attach a .cli file to start.");
        }
    }

    let cancelController = null;

    async function checkTaskStatus(filename) {
        if (cancelController) {
            cancelController.abort();
        }
        cancelController = new AbortController();

        let progress = 0;
        progressContainer.style.display = 'flex';
        loadingStatus.textContent = 'Starting...';
        loadingProgress.style.width = 0 + '%';
        cancelButton.disabled = false;

        const interval = setInterval(async () => {
            const status = await eel.get_task_status(filename)();
            const currentOutputFile = document.getElementById(status["output"]);

            if (status["status"] === "running") {

                progress = status.progress * 100;
                loadingProgress.style.width = progress + '%';

                if (currentOutputFile) {
                    currentOutputFile.disabled = true;
                }

            } else if (status["status"] === "error") {

                showErrorAlert("Error", status.message);
                clearInterval(interval);
                enableAllCoreForms();
                loadingStatus.textContent = '';
                progressContainer.style.display = 'none';

                if (currentOutputFile) {
                    currentOutputFile.disabled = false;
                }

            } else {
                showSuccessAlert("Success", status.message);
                clearInterval(interval);
                enableAllCoreForms();
                loadingStatus.textContent = '';
                progressContainer.style.display = 'none';
                await loadFileHistory();

                if (currentOutputFile) {
                    currentOutputFile.disabled = false;
                }

            }
            return status;
        }, 1000);

        cancelButton.addEventListener('click', () => {
            clearInterval(interval);
            cancelTask(filename);
            cancelButton.disabled = true;
        }, {
            once: true, // Automatically remove after firing
            signal: cancelController.signal
        });
    }

    function showErrorAlert(title, message) {
        alertTitle.innerText = title;
        alertMessage.innerText = message;
        removeClassStartsWith(alertStatus, 'alert-success');
        removeClassStartsWith(alertStatus, 'alert-warning');
        alertStatus.classList.add('alert-danger', 'show');
        alertStatus.style.display = 'block';
    }

    function showSuccessAlert(title, message) {
        alertTitle.innerText = title;
        alertMessage.innerText = message;
        removeClassStartsWith(alertStatus, 'alert-danger');
        removeClassStartsWith(alertStatus, 'alert-warning');
        alertStatus.classList.add('alert-success', 'show');
        alertStatus.style.display = 'block';
    }

    function showWarningAlert(title, message) {
        alertTitle.innerText = title;
        alertMessage.innerText = message;
        removeClassStartsWith(alertStatus, 'alert-danger');
        removeClassStartsWith(alertStatus, 'alert-success');
        alertStatus.classList.add('alert-warning', 'show');
        alertStatus.style.display = 'block';
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
        const maxAge = boxes.length;

        return boxes.map((box, index) => {
            const ageValue = (maxAge - index) / maxAge; // Normalized age (1 = newest, 0 = oldest)
            const color = interpolateColor(
                { r: 255, g: 0, b: 0 },   // Red (hot)
                { r: 0, g: 0, b: 255 },   // Blue (cold)
                ageValue
            );

            return {
                x: box[0],
                y: box[1],
                mode: 'lines',
                type: 'scattergl',
                fill: 'toself',
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

    function getOptimizedHatchData() {
        const xCoords = [];
        const yCoords = [];

        // Combine all hatch lines into a single trace with null separators
        for (let i = 0; i < optimizedGraphData.layers.x.length; i += 2) {
            xCoords.push(optimizedGraphData.layers.x[i], optimizedGraphData.layers.x[i + 1], null);
            yCoords.push(optimizedGraphData.layers.y[i], optimizedGraphData.layers.y[i + 1], null);
        }
        xCoords.pop(); // Remove trailing null
        yCoords.pop();
        let data = {
            x: xCoords,
            y: yCoords,
            mode: 'lines',
            type: 'scattergl',
            line: { width: 1, color: 'blue' },
            showlegend: false
        };

        return data;
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

    function updateGraph(layerIndex) {
        try {
            const xPadding = (optimizedGraphData.x_max - optimizedGraphData.x_min) * 0.1;
            const yPadding = (optimizedGraphData.y_max - optimizedGraphData.y_min) * 0.1;
            var optimizedData = [];
            var optiPlotData = [];

            if (showHatchLines) {
                optimizedData = getOptimizedHatchData();
                optiPlotData = [...completeTrace, optimizedData, heatScaleDummy];
            } else {
                optimizedData = createScatterTraces(optimizedGraphData.layers);
                optiPlotData = [...completeTrace, ...optimizedData, heatScaleDummy];
            }

            const layout = {
                height: navContainer.clientHeight * 0.7,
                width: navContainer.clientWidth,
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
                    range: [optimizedGraphData.x_min - xPadding, optimizedGraphData.x_max + xPadding],
                    fixedrange: false  // Allow colorbar interaction
                },
                yaxis: {
                    title: 'Y',
                    range: [optimizedGraphData.y_min - yPadding, optimizedGraphData.y_max + yPadding],
                    ticksuffix: "mm",
                    fixedrange: false
                }
            };

            Plotly.react('opti_plot', optiPlotData, layout, chartConfiguration);
        } catch (error) {
            displayError('Error updating graph:', error);
        }
    }

    function updateGraphCompare(layerIndex) {
        try {
            if (!optimizedGraphData.layers || optimizedGraphData.numLayers === 0 || rawGraphData.numLayers === 0 || !rawGraphData.layers) {
                return;
            }
            if (optimizedGraphData.numLayers != rawGraphData.numLayers) {
                return;
            }

            const xPadding = (optimizedGraphData.x_max - optimizedGraphData.x_min) * 0.1;
            const yPadding = (optimizedGraphData.y_max - optimizedGraphData.y_min) * 0.1;
            var rawData = [];
            var optiData = [];
            var rawPlotData = [];
            var optiPlotData = [];

            if (showHatchLines) {
                optiData = getOptimizedHatchData();
                optiPlotData = [...completeTrace, optiData, heatScaleDummy];
                rawData = getRawHatchData();
                rawPlotData = [...completeTrace, rawData, heatScaleDummy];

            } else {
                optiData = createScatterTraces(optimizedGraphData.layers);
                rawData = createScatterTraces(rawGraphData.layers);
                optiPlotData = [...completeTrace, ...optiData, heatScaleDummy];
                rawPlotData = [...completeTrace, ...rawData, heatScaleDummy];

            }

            function getLayout(title) {

                const layout = {
                    height: navContainer.clientHeight * 0.7,
                    width: navContainer.clientWidth / 2,
                    title: {
                        text: `${title}<br>Layer ${layerIndex}`,
                        font: {
                            size: 16
                        }
                    },
                    xaxis: {
                        title: 'X',
                        scaleanchor: 'y',  // Make axes equal scale
                        scaleratio: 1,
                        range: [optimizedGraphData.x_min - xPadding, optimizedGraphData.x_max + xPadding],
                        ticksuffix: "mm"
                    },
                    yaxis: {
                        title: 'Y',
                        range: [optimizedGraphData.y_min - yPadding, optimizedGraphData.y_max + yPadding],
                        ticksuffix: "mm"
                    },
                    hovermode: false
                };

                return layout;
            }

            Plotly.react('data_plot', rawPlotData, getLayout("Pre-Opt"), chartConfiguration);
            Plotly.react('opti_plot', optiPlotData, getLayout("Post-Opt"), chartConfiguration);
        } catch (error) {
            displayError('Error updating graph:', error);
        }
    }

    function plotRValues() {

        const oriRValues = rawGraphData.rVal;
        const optRValues = optimizedGraphData.rVal;

        if (!oriRValues || !optRValues) {
            return;
        }

        // Generate time steps for the X-axis
        const timeSteps = Array.from({ length: optRValues.length }, (_, i) => i + 1);

        // Create traces for R_ORI and R_OPT
        const trace1 = {
            x: timeSteps,
            y: oriRValues,
            mode: 'markers+lines',
            name: 'Original Sequence',
            line: {
                color: 'blue'
            }
        };

        const trace2 = {
            x: timeSteps,
            y: optRValues,
            mode: 'markers+lines',
            name: 'Optimized Sequence',
            line: {
                color: 'red'
            }
        };

        // Get R Grade
        let rScoreObject = getRScore();
        let rScore = rScoreObject.grade;
        let rColor = rScoreObject.color;
        rGrade.innerText = rScore;
        rGrade.style.color = rColor;

        // Layout configuration
        const layout = {
            height: navContainer.clientHeight * 0.7,
            width: navContainer.clientWidth,
            title: `Heat Uniformity<br>Layer ${optimizedGraphData.curLayer}`,
            xaxis: {
                title: 'Time Step',
                showgrid: true,
                zeroline: false,
                ticksuffix: "ms"
            },
            yaxis: {
                title: 'Heat Deviation',
                showgrid: true,
                zeroline: false
            },
            showlegend: true
        };

        // Plot the chart
        Plotly.newPlot('r_plot', [trace1, trace2], layout, chartConfiguration);
    }

    function getRScore() {
        let grade_scale = {
            2: {
                "grade": "F",
                "color": "red"
            },
            5: {
                "grade": "E",
                "color": "red"
            },
            10: {
                "grade": "D",
                "color": "orange"
            },
            15: {
                "grade": "C",
                "color": "orange"
            },
            20: {
                "grade": "B",
                "color": "green"
            },
            30: {
                "grade": "A",
                "color": "green"
            }
        };

        let score = (rawGraphData.rMean - optimizedGraphData.rMean) / rawGraphData.rMean * 100;

        let grade_key = Object.keys(grade_scale)
            .map(Number) // Convert keys to numbers
            .sort((a, b) => a - b) // Ensure they are sorted in ascending order
            .find(key => score < key) || 30;

        return grade_scale[grade_key];
    }
});
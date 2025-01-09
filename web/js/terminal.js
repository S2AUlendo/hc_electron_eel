document.addEventListener('DOMContentLoaded', function () {

    const terminal = document.getElementById('terminal');
    
    eel.expose(update_terminal_output);

    function update_terminal_output(output) {
        const terminal = document.getElementById('terminal');
        if (terminal) {
            terminal.textContent += `${output}`; // Append new output with a newline character
        }
    }

});
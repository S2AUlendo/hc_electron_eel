document.addEventListener('DOMContentLoaded', function () {

    const terminal = document.getElementById('terminal');
    
    eel.expose(update_terminal_output);

    function update_terminal_output(output) {
        if (terminal) {
            terminal.textContent += `${output}`;
            terminal.scrollTop = terminal.scrollHeight;
        }
    }

});

console.log("opening socket")
let socket = io()


socket.on("connect", function(){

    // This should update info available on GUI about every printer
    // Example data:
        // 
        //{
        //   "S5. Brienne of Tarth": {
        //     "time_remaining": 1,
        //     "subtask_name": "mattias v 240s VattenRäna",
        //     "total_layers": 30,
        //     "current_layer": 4,
        //     "current_stage": 0,
        //     "current_stage_text": "",
        //     "gcode_state": "FAILED",
        //     "percentage_complete": "13%"
        //   }
        //   ...
        // }
        socket.on("update_printer_times", function (printer_data) {
            console.log("update_printer_times", printer_data);
        
            for (const printerName in printer_data) {
                if (printer_data.hasOwnProperty(printerName)) {
                    const printerInfo = printer_data[printerName];
                    const printerId = printerName.replace(/\s+/g, '-'); // Replace spaces with dashes for IDs
        
                    // Check if the printer already exists in the DOM
                    let printerElement = document.getElementById(printerId);
                    if (!printerElement) {
                        // Create the printer element dynamically if it doesn't exist
                        printerElement = document.createElement('div');
                        printerElement.id = printerId;
                        printerElement.classList.add('printer');
                        printerElement.innerHTML = `
                            <div> class="print-box"
                            <h3>Printer #${printerName}</h3>
                            <h3>Print #${printerInfo.subtask_name}</h3>
                            <h3>Estemated Time Left: ${printerInfo.time_remaining}<h3>
                            <div class="progress-container">
                            <div class="progress-bar" id="progress-bar-${percentage_complete}"></div>
                            </div>
                            <button class="cancel-btn" id="cancel-btn-${printId}">Cancel</button>
                            </div>
                        `;
                        document.getElementById('print-area').appendChild(printerElement);
                    }
        
                    // Update printer details in the DOM
                    printerElement.querySelector(".time-remaining").textContent = `Time Remaining: ${printerInfo.time_remaining} mins`;
                    printerElement.querySelector(".subtask-name").textContent = `Subtask: ${printerInfo.subtask_name}`;
                    printerElement.querySelector(".percentage-complete").textContent = `Progress: ${printerInfo.percentage_complete}`;
        
                    // Update the progress bar width based on percentage_complete
                    const progressBar = document.getElementById(`progress-bar-${printerId}`);
                    const percentage = parseFloat(printerInfo.percentage_complete.replace('%', '')) || 0; // Handle invalid percentage data gracefully
                    progressBar.style.width = `${percentage}%`;
                }
            }
        });
        
        
    // This should add the file data to whatever is showing your uploaded files
    // Example data:
    // {
    //     "filename": "{name of file}",
    //     "owner": "{name of owner}"
    //   }
    socket.on("file_added_to_queue", function(file_data){
        console.log("file_added_to_queue")
        console.log(file_data)
    })

    // This should update whatever is showing a prelimary queue
    // Example Data:
    // [
    //   {
    //      "print_id": "{id_of_print}",
    //      "estimated_time_to_completion": {time in minutes from now until print being finished, its preliminary},
    //      "file_name": {filepath on server, will probably change since theres no reason},
    //      "owner": "{owner name}"
    //   }
    //   ...
    // ]
    socket.on("prelim_queue", function(queue_data){
        console.log("prelim_queue")
        console.log(Object.values(queue_data))

        
        update_queue_time = Object.values(queue_data[-1])[0]["estimated_time_to_completion"]
        queue_time_el = document.getElementById("QueueTime")
        queue_time_el.innerText = `~${update_queue_time}min`
    })
    // This should create some sort of pop-up-like thing asking user to clean plate
    // Listen for the cleanup request from the server
    socket.on("request_plate_cleanup", function (cleanup_msg) {
        console.log("request_plate_cleanup");
        console.log(cleanup_msg);

        // Extract printId from the message
        const printId = cleanup_msg.printId || 'unknown';

        // Call the function to create the cleanup prompt
        createTakeoutPrompt(printId, cleanup_msg.message || "A cleanup is required!");
        // This should remove said pop-up
    })
    socket.on("plate_is_clean", function(data){
        // console.log("plate_is_clean")
        // console.log(data)
        printer_name = data["printer_name"]
        msg = data["msg"]

        request_cleanup_el = document.getElementById(`promp-${printer_name}`)
        request_cleanup_el.remove();
        console.log(msg)
    })
});


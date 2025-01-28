
console.log("opening socket")
let socket = io()




function createPrintBox(printer_name) {
    const container = document.createElement('div');
    const printer_name_proc = printer_name.replace(" ", "_")

    container.classList.add('print-box');
    container.id = `print_${printer_name_proc}`;
    container.innerHTML = `
        <h3>${printer_name}</h3>
        <div class="progress-container">
            <h5 class="subtask_name_holder" id="subtask_name_container_${printer_name_proc}"></h5>

            <div class="label_container">
                <p class="percentage_label" id="percentage_label_${printer_name_proc}"></p>
                <p class="time-label" id="time_label_${printer_name_proc}"></p>
            </div>
            <div class="progress-bar-container" id="progress_bar_container_${printer_name_proc}">
                <div class="progress-bar-outer" id="progress_bar_outer_${printer_name_proc}"></div>
                
                <div class="progress-bar-inner-container" id="progress_bar_inner_container_${printer_name_proc}">
                    <div class="progress-bar-inner" id="progress_bar_inner_${printer_name_proc}"></div>
                </div>
            </div>
        </div>

   `;

   document.getElementById('print-area').appendChild(container);

}

function update_printer_box_values(printer_name, percentage_complete, time_remaining_minutes, subtask_name){
    const printer_name_proc = printer_name.replace(" ", "_")
    let subtask_container = document.getElementById(`subtask_name_container_${printer_name_proc}`) 
    let percentage_container = document.getElementById(`percentage_label_${printer_name_proc}`) 
    let time_container = document.getElementById(`time_label_${printer_name_proc}`) 
    let prog_bar_inner = document.getElementById(`progress_bar_inner_${printer_name_proc}`)

    console.log("here")
    console.log(percentage_complete)
    console.log(time_remaining_minutes)
    console.log(subtask_name)
    console.log("here")
    if (!subtask_container || !percentage_container || !time_container || !prog_bar_inner) return
    subtask_container.innerText = `${subtask_name}`
    percentage_container.innerText = `${percentage_complete}%`
    time_container.innerText = `~${time_remaining_minutes} min`
    prog_bar_inner.style.width = `${percentage_complete}%`
}





socket.on("connect", function(){


    // This should update info available on GUI about every printer
    // Example data:
        // 
        //{
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
        //     "gcode_state": "FAILED",
        //     "percentage_complete": "13%"
        //   }
        //   ...
        // }
        socket.on("update_printer_times", function (printer_data) {
            print_area = document.getElementById("print-area")

            if (print_area.children.length !== printer_data.length){
                print_area.innerHTML = ""
                for (printer_name in printer_data){
                    createPrintBox(printer_name)
                }

            }
            for (const printerName in printer_data) {
                if (printer_data.hasOwnProperty(printerName)) {
                    const printerInfo = printer_data[printerName];

                    update_printer_box_values(printerName, printerInfo.percentage_complete, printerInfo.time_remaining, printerInfo.subtask_name)

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
        update_queue_time = Object.values(queue_data[-1])[0]["estimated_time_to_completion"]
        update_queue_time = Object.values(queue_data[-1])[0]["estimated_time_to_completion"]
        queue_time_el = document.getElementById("QueueTime")
        queue_time_el.innerText = `~${update_queue_time}min`
    })
    // This should create some sort of pop-up-like thing asking user to clean plate

    // Listen for the cleanup request from the server
    socket.on("request_plate_cleanup", function (cleanup_msg) {

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

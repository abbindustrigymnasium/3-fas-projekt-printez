
console.log("opening socket")
let socket = io()


socket.on("connect", function(){
    // This should update info available on GUI about every printer
    // Example data:
        // {
        //   {
        //   "S5. Brienne of Tarth": {
        //     "time_remaining": 1,
        //     "subtask_name": "mattias v 240s VattenRäna",
        //     "total_layers": 30,
        //     "current_layer": 4,
        //     "current_stage": 0,
        //     "current_stage_text": "",
        //     "gcode_state": "FAILED"
        //   }
        //   ...
        // }
    socket.on("update_printer_times", function(printer_data){
        console.log("update_printer_times")
        console.log(printer_data)
    })
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

        
        update_queue_time = Object.values(queue_data[0])[0]["estimated_time_to_completion"]
        queue_time_el = document.getElementById("QueueTime")
        queue_time_el.innerText = `~${update_queue_time}min`
    })
    // This should create some sort of pop-up-like thing asking user to clean plate
    socket.on("request_plate_cleanup", function(cleanup_msg){
        console.log("request_plate_cleanup")
        console.log(cleanup_msg)
    })
    // This should remove said pop-up
    socket.on("plate_is_clean", function(msg){
        console.log("plate_is_clean")
        console.log(msg)
    })
})
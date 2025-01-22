
console.log("opening socket")
let socket = io()


socket.on("connect", function(){
    // This should update info available on GUI about every printer
    socket.on("update_printer_times", function(printer_data){
        console.log("update_printer_times", printer_data)
    })
    // This should add the file data to whatever is showing your uploaded files
    socket.on("file_added_to_queue", function(file_data){
        console.log("file_added_to_queue", file_data)
    })
    // This should update whatever is showing a prelimary queue
    socket.on("prelim_queue", function(queue_data){
        console.log("prelim_queue", Object.values(queue_data))

        
        update_queue_time = Object.values(queue_data[0])[0]["estimated_time_to_completion"]
        queue_time_el = document.getElementById("QueueTime")
        queue_time_el.innerText = `~${update_queue_time}min`
    })
    // This should create some sort of pop-up-like thing asking user to clean plate
    socket.on("request_plate_cleanup", function(cleanup_msg){
        console.log("request_plate_cleanup", cleanup_msg)
    })
    // This should remove said pop-up
    socket.on("plate_is_clean", function(msg){
        console.log("plate_is_clean", msg)
    })
})
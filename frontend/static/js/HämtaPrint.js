// Function to fetch and update printer statuses from the backend
//async function fetchAndUpdatePrinterStatus() {
    //try {
        //const response = await fetch("/printer-status");
        //if (!response.ok) {
            //throw new Error(`Error fetching printer statuses: ${response.statusText}`);
        //}
        //const printers = await response.json();

        // Clear existing content
        //document.getElementById("box-dinaprints").innerHTML = "";
        //document.getElementById("box-ready").innerHTML = "";
        //document.getElementById("box-active").innerHTML = "";
        //document.getElementById("box-available").innerHTML = "";
        //document.getElementById("box-broken").innerHTML = "";

        // Populate boxes based on printer status
        //printers.forEach(printer => {
            //const printerElement = document.createElement("div");
            //printerElement.textContent = `${printer.name} (ID: ${printer.id})`;
            //switch (printer.status) {
                //case "you":
                    //document.getElementById("box-dinaprints").appendChild(printerElement);
                    //break;
                //case "ready":
                    //document.getElementById("box-ready").appendChild(printerElement);
                    //break;
                //case "active":
                    //document.getElementById("box-active").appendChild(printerElement);
                    //break;
                //case "available":
                    //document.getElementById("box-available").appendChild(printerElement);
                    //break;
                //case "broken":
                    //document.getElementById("box-broken").appendChild(printerElement);
                    //break;
                //default:
                    //document.getElementById("box-none").appendChild(printerElement);
                    //break;
            //}
        //});
    //} catch (error) {
        //console.error("Failed to update printer statuses:", error);
    //}
//}

// Periodically fetch and update printer statuses every 5 seconds
//setInterval(fetchAndUpdatePrinterStatus, 5000);

// Initialize the page
//fetchAndUpdatePrinterStatus();

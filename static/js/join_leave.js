// This function is reusable and will be called each time a button is pressed so that the butons always have an event listener when the HTML is reformed
function attachButtonListeners(form) {
    let actionButton = null // Defines the button that will be clicked

    form.querySelectorAll("button").forEach(button => {
        button.replaceWith(button.cloneNode(true));
    });

    // Loops through each button and gets the one which is clicked
    form.querySelectorAll("button").forEach(button => {
        button.addEventListener("click", () => {
            actionButton = button;
        });
    });

    form.addEventListener("submit", async (e) => { // Adds event listener to the buttons
        e.preventDefault(); // Prevents page reloading

        if (!actionButton) return;

        console.log(actionButton);

        form.querySelectorAll("button").forEach(btn => btn.disabled = true) // Disables all buttons to prevent double joining events

        const formData = new FormData(form); // Gets all form inputs 
        const eventId = formData.get("event_id");

        if (actionButton) { // Ensures submission is from a button(not enter    )
            formData.append(actionButton.name, actionButton.value); // Adds the chosen buttons name and value
        }
        const action = formData.get("action"); // Gets the chosen action
        
        // Sends a post request to event-action with the form data
        const response = await fetch("/event-action", {
            method: "POST",
            body: formData
        });

        if (response.ok) { // If the response goes through
            const result = await response.json(); // Gets the response of the function

            const wrapper = document.getElementById(`join-leave-${eventId}`);
            wrapper.replaceChildren();

            const button = document.createElement("button");
            button.type = "submit";
            button.name = "action";

            // Update the buttons based on the response
            if (result.status === "joined") { // Updates to the leave button when joining
                button.value = "leave";
                button.className = "leave-button";
                button.textContent = "Leave";
            } else if (result.status === "left") {
                button.value = "join";
                button.className = "join-button";
                button.textContent = "Join";
            } else if (result.status === "login") {
                window.location.href = "/login"; // Redirect to login page
                return;
            }

            wrapper.appendChild(button);
            
            button.addEventListener("click", () => {
                actionButton = button;
            });
        }
    });
}

// Goes through every event action form for each event when the page loads
document.querySelectorAll(".event-action-form").forEach(form => {
    attachButtonListeners(form); // Attatches button listeners
});
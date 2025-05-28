document.querySelectorAll("[data-popup-target]").forEach(button => { // Goes through every button with the data-popup-target
    button.addEventListener("click", () => { // Adds a click event listener
        const popupTarget = button.getAttribute("data-popup-target"); // Sets the popups id to the buttons data value
        const popup = document.getElementById(popupTarget); // Gets the popup with the id
        popup.classList.add("open"); // Adds the open class to it so the CSS is implemented
    });
});

document.querySelectorAll("[data-popup-close]").forEach(button => { // Gets all buttons with the data-popup-close attribute
    button.addEventListener("click", () => { // Adds a click event listener
        const popup = button.closest(".popup"); // Gets the nearest element with the class element of popup
        popup.classList.remove("open"); // Removes the open class from the popup
    });
});


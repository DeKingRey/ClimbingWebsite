function toggleInfo(button) {
    const header = button.parentElement;
    const infoDiv = header.nextElementSibling; // Gets the next element from the header div which is the info div
    const isVisible = infoDiv.style.display === "block"; // Checks if the display is block, and returns true/false accordingly

    infoDiv.style.display = isVisible ? "none" : "block"; // If it is false it sets display to none, else block
    button.textContent = isVisible ? ">" : "⌄"; // Changes the button icon depending on whether the info is visible or not
}
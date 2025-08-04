const form = document.getElementById("add_route_form");

// Gets all the input fields
const nameInput = form.name;
const gradeInput = form.grade;
const boltsInput = form.bolts;
const locationInput = form.location;
const typesInput = form.querySelectorAll("input[name='types[]']") // Selects all type inputs(checkboxes)

function validateName() {
    const value = nameInput.value.trim(); 
    const errorDiv = document.querySelector(".name-errors");

    // Validates whether input field is empty
    if (!value) { 
        errorDiv.textContent = "Route name required";
        errorDiv.style.display = "block"; 
        nameInput.classList.add("invalid");

        return false;
    }

    // Validates that the length of the name isn't too long
    if (value.length > 100) {
        errorDiv.textContent = "Route name must be less than 100 characters";
        errorDiv.style.display = "block"; 
        nameInput.classList.add("invalid");

        return false;
    }

    // Validates whether the route already exists
    const exists = routes.includes(value);
    const isValid = !exists; 
    errorDiv.textContent = isValid ? "" : "Route already exists";
    errorDiv.style.display = isValid ? "none" : "block";
    nameInput.classList.toggle("invalid", !isValid);
    return isValid;
}

function validateGrade() {
    const value = gradeInput.value.trim();
    const errorDiv = document.querySelector(".grade-errors");

    // Validates that the length of the grade isn't too long
    if (value.length > 10) {
        errorDiv.textContent = "Grade must be less than 10 characters";
        errorDiv.style.display = "block"; 
        gradeInput.classList.add("in    valid");

        return false;
    }

    errorDiv.textContent = value ? "" : "Grade is required";
    errorDiv.style.display = value ? "none" : "block";
    gradeInput.classList.toggle("invalid", !value);
    return !!value;
}

function validateBolts() {
    const value = boltsInput.value.trim();
    const errorDiv = document.querySelector(".bolts-errors");
    // Bolts are optional
    if (value === "") { 
        errorDiv.textContent = "";
        return true;
    }
    
    // Ensures bolts value isn't too high
    if (value > 1000) {
        errorDiv.textContent = "Bolts must be less than 1000"
        errorDiv.style.display = "block";
        boltsInput.classList.toggle("invalid", true);
        return false;
    }

    // Ensures bolts if a valid number
    const isValid = /^\d+$/.test(value); 
    errorDiv.textContent = isValid ? "" : "Bolts must be a non-negative integer";
    errorDiv.style.display = isValid ? "none" : "block";
    boltsInput.classList.toggle("invalid", !isValid);
    return isValid;
}

function validateLocation() {
    const value = locationInput.value.trim();
    const errorDiv = document.querySelector(".location-errors");

    if (!value) { // If value is empty  
        errorDiv.textContent = "Location is required";
        errorDiv.style.display = "block"
        locationInput.classList.add("invalid");
        return false;
    }

    const isValid = locs.includes(value);
    errorDiv.textContent = isValid ? "" : "Location was not found";
    errorDiv.style.display = isValid ? "none" : "block";
    locationInput.classList.toggle("invalid", !isValid);
    return isValid;
}

function validateTypes() {
    const checked = [...typesInput].filter(box => box.checked) // The ... separates values into individual elements(spread operator), gets all the checked boxes
    const errorDiv = document.querySelector(".types-errors");
    errorDiv.textContent = checked.length ? "" : "Select at least one type"; // Checks that checked is not empty(ensures one thing is checked)
    errorDiv.style.display = checked.length ? "none" : "block";
    return checked.length > 0;  
}

// Adds event listeners to all input fields, waiting for input
nameInput.addEventListener("input", validateName);
gradeInput.addEventListener("input", validateGrade);
boltsInput.addEventListener("input", validateBolts);
locationInput.addEventListener("input", validateLocation);
typesInput.forEach(box => box.addEventListener("change", validateTypes)); // Checks for change in each checkbox


// Adds event listener to submit button
form.addEventListener("submit", function(e) {
    // Checks validators
    const valid = 
        validateName() &&
        validateGrade() &&
        validateBolts() &&
        validateLocation() &&
        validateTypes();

    // If any come back false it will prevent submission, and reopen route popup
    if (!valid) {
        e.preventDefault();
        document.getElementById("route-popup").classList.add("open");
    }
});
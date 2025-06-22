const image_input = document.getElementById("image");
const preview = document.getElementById("photo-preview"); // Gets the photo input field and preview image

image_input.addEventListener("change", function() { // Activates when the input field changes
    const file = this.files[0]; // Gets the file that the user has selected
    
    if (file) { // Ensures there is a file
        const reader = new FileReader(); // File Readers read the content of files 
    
        reader.addEventListener("load", function() { // Activates when the image has loaded
            preview.setAttribute("src", this.result);
            preview.style.display = "block"; // Sets the image preview 
        });

        reader.readAsDataURL(file); // Allows the file to be used
    } else {
        preview.style.display = "none";
        preview.setAttribute("src", ""); // Sets preview to nothing if there is no file
    }
});



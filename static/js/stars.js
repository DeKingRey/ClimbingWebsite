const stars =  document.querySelectorAll(".stars"); // Gets all elements under the stars div

stars.forEach((star, index1) =>{ // Loops through all stars
    star.addEventListener("click", () => { // Checks if they've been clicked
        stars.forEach((star, index2 ) => { 
            index1 >= index2 ? star.classList.add("active") : star.classList.remove("active") // All stars with a lower index than the selected star are given the active class, otherwise it is removed
        });
    });
});

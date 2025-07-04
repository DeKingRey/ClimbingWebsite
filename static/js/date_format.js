document.querySelectorAll(".date").forEach(date => {
    date.textContent = formatDate(date.textContent);
});


function formatDate(dateStr) {
    const [day, month, year] = dateStr.split("-").map(Number); // Separates date and makes them all ints
    const date = new Date(year, month - 1, day); // Converts to JS date
    const dayEnding = day + getDayEnding(day); // Gets the full day and its ending e.g. 31st, 2nd, 4th, 23rd, etc
    // Function which gets the months date by converting to locale time and gets the short version of the month e.g 'Jan'
    const monthName = date.toLocaleDateString("default", { month: "short" }); 

    return `${monthName} ${dayEnding} ${year}`;
}


function getDayEnding(day) {
    if (day >= 11 && day <= 13) return "th"; // 11, 12, and 13 are different to the other 1's, 2's, and 3's
    switch (day % 10) { // Switch is a quicker way of doing else ifs by checking a variety of cases, modulo 10 gets the remainder
        case 1: return "st"; // If it is 1(1st, 21st, 31st) return with the 'st' suffix 
        case 2: return "nd";
        case 3: return "rd";
        default: return "th"; // By default(everything else) return 'th'
    }
}

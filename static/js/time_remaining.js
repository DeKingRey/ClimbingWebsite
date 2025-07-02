// Function to get the date and time into a separated valued list

// Going to have to be changed later due to multiple day events

function parseDateTime(dateStr, timeStr) {
    const [day, month, year] = dateStr.split("-").map(Number); // Splits the string by the "-" and turns each string into an int
    
    let [startTimeStr, endTimeStr] = timeStr.split(" - ").map(t => t.trim()) // Splits apart start and endtime and trims spaces

    function parseTime(t) {
        // The regex ensures the date is formatted correctly, either one or 2 digits for hours, a :, then 2 digits for mins, and then either am or pm
        const timeRegex = /(\d{1, 2}):(\d{2})(am|pm)/; 
        const match = t.match(timeRegex); // Checks if t matches the correct format of the time regex

        if (!match) return null; // If the time is incorrectly formatted

        let [_, hr, min, ampm] = match; // Extracts all parts of the time
        hr = parseInt(hr); // Converts to int
        min = parseInt(min);

        // Following code converts to 24hr time
        if (ampm === "pm" && hr !== 12) hr += 12; // Adds 12 hours to the time if it's pm, 1pm -> 13
        if (ampm === "am" && hr == 12) hr = 0; // Midnight if it's am and 12

        return { hr, min };
    }

    const start = parseTime(startTimeStr); // Gets the start time
    const end = parseTime(endTimeStr); // Gets the end time

    let startDate = new Date(year, month - 1, day, start.hr, start.min) // Converts to JS date(month is 0-indexed)
    let endDate = new Date(year, month - 1, day, end.hr, end.min)
    
    return { startDate, endDate };
}


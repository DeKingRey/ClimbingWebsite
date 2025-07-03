// Function to get the date and time into a separated valued list

function parseDateTime(dateStr, timeStr) {
    const [day, month, year] = dateStr.split("-").map(Number); // Splits the string by the "-" and turns each string into an int

    function parseTime(t) {
        // The regex ensures the date is formatted correctly, either one or 2 digits for hours, a :, then 2 digits for mins, and then either am or pm
        const timeRegex = /(\d{1,2}):(\d{2})(am|pm)/; 
        const match = t.match(timeRegex); // Checks if t matches the correct format of the time regex

        if (!match) return null; // If the time is incorrectly formatted

        console.log(match);

        let [_, hr, min, ampm] = match; // Extracts all parts of the time
        hr = parseInt(hr); // Converts to int
        min = parseInt(min);

        // Following code converts to 24hr time
        if (ampm === "pm" && hr !== 12) hr += 12; // Adds 12 hours to the time if it's pm, 1pm -> 13
        if (ampm === "am" && hr == 12) hr = 0; // Midnight if it's am and 12

        return { hr, min };
    }

    const time = parseTime(timeStr); // Gets the 24hr time
    if (!time) return null;

    let date = new Date(year, month - 1, day, time.hr, time.min) // Converts to JS date(month is 0-indexed)
    //let endDate = new Date(year, month - 1, day, end.hr, end.min)
    
    return date;
}

// Function will get the remaining time until the date
function getTimeRemaining(startDate) {
    const now = new Date(); // Gets the current date and time
    const diff = startDate - now; // Gets the difference in time(remaining time) in milliseconds

    if (diff <= 0) { // If no time is remaining
        return null;
    }

    const totalSeconds = Math.floor(diff / 1000); // Gets total seconds until events
    const days = Math.floor(totalSeconds / (3600 * 24)); // Gets total days
    const hours = Math.floor((totalSeconds % (3600 * 24)) / 3600); // Gets leftover seconds after days, and converts to hours
    const mins = Math.floor((totalSeconds % 3600) / 60); // Gets leftover seconds after hours, and converts to minutes
    const seconds = Math.floor(totalSeconds % 60); // Gets leftover seconds after minutes

    return { days, hours, mins, seconds };
}

const eventStatus = document.getElementById("eventStatus");
const countdown = document.getElementById("countdown"); 
const eventDate = parseDateTime("31-01-2026", "11:55am");
const eventEndDate = parseDateTime("15-11-2026", "12:00am");

// Function will update the countdown element
function updateCountdown() {
    let remaining = getTimeRemaining(eventDate); // Gets remaining time

    if (!remaining) {
        remaining = getTimeRemaining(eventEndDate); // Gets the time left until the event ends if it is ongoing
        eventStatus.textContent = "Ongoing";

        if (!remaining) { // If the event is concluded
            eventStatus.textContent = "Concluded";
            countdown.style.display = "none";
            clearInterval(intervalId); // Stops the repeating of the function
            return;
        }
    }
    else {
        eventStatus.textContent = "Upcoming";
    }

    const { days, hours, mins, seconds } = remaining;
    countdown.textContent = `${days}d ${hours}h ${mins}m ${seconds}s`; // Updates countdown to display time remaining
}

updateCountdown();
const intervalId = setInterval(updateCountdown, 1000); // Runs the function every second



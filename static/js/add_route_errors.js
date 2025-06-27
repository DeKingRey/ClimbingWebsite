document.getElementById("add-route-form").addEventListener("submit", function(e) {
    let errors = [];
    
    const name = this.name.trim();
    const grade = this.grade.value.trim();
    const bolts = this.bolts.value.trim();
    const location = this.location.value.trim();
    const types = [...this.querySelectorAll("input[name='types[]']:checked")];

    document.querySelectorAll(".form-error").forEach(el => el.textContent = "");

    if (!name) {
        errors.push("Route name is required")
    }
    if (!grade) {
        errors.push("Grade is required")
    }
    if (bolts === "") {
        
    } else if (!/^\d+$/.test(bolts)) {
        errors.push("Bolts must be a non-negative integer")
    }
})
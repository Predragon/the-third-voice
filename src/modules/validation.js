// Form/data validation helpers
export function isNotEmpty(value) {
    return value !== undefined && value !== null && value !== '';
}

// Add more validators as needed
export function isEmail(email) {
    return /\S+@\S+\.\S+/.test(email);
}


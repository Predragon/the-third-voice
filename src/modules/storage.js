// Local storage utilities
export function saveItem(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

export function getItem(key) {
    const data = localStorage.getItem(key);
    try { return data ? JSON.parse(data) : null; }
    catch { return null; }
}

export function removeItem(key) {
    localStorage.removeItem(key);
}

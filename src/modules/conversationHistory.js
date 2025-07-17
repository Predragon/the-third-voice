// Chat history & persistence
export function saveHistory(history) {
    localStorage.setItem('ttv_history', JSON.stringify(history));
}

export function getHistory() {
    const data = localStorage.getItem('ttv_history');
    return data ? JSON.parse(data) : [];
}

export function clearHistory() {
    localStorage.removeItem('ttv_history');
}


// Third Voice app setup/config
export function saveSetup(config) {
    localStorage.setItem('ttv_setup', JSON.stringify(config));
}

export function getSetup() {
    const data = localStorage.getItem('ttv_setup');
    return data ? JSON.parse(data) : {};
}

export function clearSetup() {
    localStorage.removeItem('ttv_setup');
}


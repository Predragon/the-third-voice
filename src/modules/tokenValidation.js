// Token management & validation
export function saveToken(token) {
    localStorage.setItem('ttv_token', token);
}

export function getToken() {
    return localStorage.getItem('ttv_token');
}

export function clearToken() {
    localStorage.removeItem('ttv_token');
}

export function isTokenValid(token) {
    // Basic: Checks non-empty. Customize as needed.
    return typeof token === 'string' && token.length > 0;
}


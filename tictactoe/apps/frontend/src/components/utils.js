{/* API Communication */}
async function fetchTokens() {
    try {
        const response = await fetch('/api/get-tokens');
        if (!response.ok) throw new Error('Failed to fetch tokens');
        return await response.json();
    } catch (error) {
        console.error(error);
        return {};
    }
}

export async function fetchTokensAndStore(context) {
    try {
        const data = await fetchTokens();

        // User is not authenticated
        if (!data.jwt_token) {
            goToURL('/accounts/login');
            return;
        }

        context.setState({
            csrfToken: data.csrf_token,
            jwtToken: data.jwt_token,
            sessionKey: data.session_key,
            username: data.username
        });

        context.headers = {
            Authorization: `Bearer ${data.jwt_token}`,
            'Content-Type': 'application/json',
            'X-CSRFToken': data.csrf_token,
        };

    } catch (error) {
        console.error('Error during initialization:', error);
    }
}

async function fetchData(url, requestOptions) {
    try {
        const response = await fetch(url, requestOptions);

        if (!response.ok) {
            throw new Error(`Error: ${response.status} - ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        return { error: error.message };
    }
}


export function goToURL(url) {
    window.location.href = url
}

export function getRequestOptions(context, type) {
    const types = ['POST', 'GET', 'DELETE'];

    if (types.includes(type)) {
        return {
            method: type,
            headers: context.headers,
        };
    } else {
        console.error("Incorrect request type");
        return {};
    }
}

export async function createGameRoom(requestOptions) {
    const url = '/api/game-room/';
    const data = await fetchData(url, requestOptions);

    if (data?.code) {
        return `/games/room/${data.code}`;
    } else {
        console.error('Invalid response:', data);
        return null;
    }
}

export async function fetchGameRoomData(gameRoomCode, requestOptions) {
    const url = `/api/game-room/?gameRoomCode=${gameRoomCode}`;
    return fetchData(url, requestOptions);
}

export async function fetchGameRoomsList(requestOptions) {
    const url = `/api/game-room`;
    return fetchData(url, requestOptions);
}

export async function cancelGameRoom(gameRoomCode, requestOptions) {
    const url = `/api/game-room/?gameRoomCode=${gameRoomCode}`;
    return fetchData(url, requestOptions);
}

{/* Utils */}

export function formatTime(milliseconds) {
    const totalSeconds = Math.max(0, Math.floor(milliseconds / 1000));
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const ms = milliseconds % 1000;

    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
}

export function calculateWinner(squares) {
    const lines = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6],
    ];

    for (let i = 0; i < lines.length; i++) {
        const [a, b, c] = lines[i];
        if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
            return squares[a];
        }
    }
    return null;
}
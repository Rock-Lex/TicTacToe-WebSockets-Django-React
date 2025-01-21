document.addEventListener('DOMContentLoaded', () => {
    let currentPage = 1;
    let currentFilter = 'all'; // Default filter
    let currentSort = 'desc';   // Default sort order

    // WebSocket setup
    let url = `ws://${window.location.host}/ws/main-chat-socket/`;
    const chatSocket = new WebSocket(url);

    chatSocket.onopen = function () {
        console.log("WebSocket is open now.");
        chatSocket.send(JSON.stringify({ 'type': "latest_messages_request" }));
    };

    chatSocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        console.log('Received data:', data);

        if (data.type === 'chat') {
            let messages = document.getElementById('messages');
            let username = document.getElementById('username');

            let timestampParts = data.timestamp.split(' ');
            let dateParts = timestampParts[0].split('.');
            let timeParts = timestampParts[1].split(':');

            let formattedDate = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}T${timeParts[0]}:${timeParts[1]}:${timeParts[2]}`;

            let timestamp = new Date(formattedDate);
            let formattedTime;

            if (isNaN(timestamp.getTime())) {
                console.warn('Invalid timestamp:', data.timestamp);
                formattedTime = 'Invalid Time';
            } else {
                formattedTime = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }

            let sender = data.sender === data.today ? '' : `<strong>${data.sender}</strong>`;
            let rightSide = (username.value === data.sender);
            let messageClass = rightSide ? 'message-right' : 'message-left';

            messages.insertAdjacentHTML('beforeend',
                `<div class="message ${messageClass}">
                    <p>${sender} [${formattedTime}]: ${data.message}</p>
                </div>`
            );

            messages.scrollTop = messages.scrollHeight;
        }
    };

    // Form handling for chat messages
    const form = document.getElementById('main-chat-form');
    form.addEventListener('submit', (e) => {
        e.preventDefault(); // Prevent page reload

        const input = e.target.main_chat_message;
        const message = input.value;

        if (message.trim() !== "") {
            chatSocket.send(JSON.stringify({
                'type': "chat_message",
                'message': message
            }));
            input.value = ""; // Clear the input field
        }
    });

    // Function to update the games table
    const updateTable = (page, filter, sort) => {
        fetch(`/paginate-games/?page=${page}&filter=${filter}&sort=${sort}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                document.getElementById('games-table-body').innerHTML = data.table_html;
                document.getElementById('page-info').textContent = `Page ${data.current_page} of ${data.total_pages}`;
                document.getElementById('prev-page').disabled = !data.has_previous;
                document.getElementById('next-page').disabled = !data.has_next;
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    };

    // Event listeners for pagination buttons
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            updateTable(currentPage, currentFilter, currentSort);  // Pass currentFilter and currentSort
        }
    });

    document.getElementById('next-page').addEventListener('click', () => {
        currentPage++;
        updateTable(currentPage, currentFilter, currentSort);  // Pass currentFilter and currentSort
    });

    // Event listeners for filter and sort dropdowns
    document.getElementById('game-filter').addEventListener('change', () => {
        currentPage = 1; // Reset to first page when filter changes
        currentFilter = document.getElementById('game-filter').value;
        currentSort = document.getElementById('date-sort').value;
        updateTable(currentPage, currentFilter, currentSort);  // Pass currentFilter and currentSort
    });

    document.getElementById('date-sort').addEventListener('change', () => {
        currentPage = 1; // Reset to first page when sorting changes
        currentFilter = document.getElementById('game-filter').value;
        currentSort = document.getElementById('date-sort').value;
        updateTable(currentPage, currentFilter, currentSort);  // Pass currentFilter and currentSort
    });

    // Initial load
    updateTable(currentPage, currentFilter, currentSort);
});

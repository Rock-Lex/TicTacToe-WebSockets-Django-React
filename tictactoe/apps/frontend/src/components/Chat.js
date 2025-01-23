import React, { useState, useEffect, useRef } from 'react';
import { Box, TextField, Button, Typography } from '@material-ui/core/';

const Chat = ({ roomCode }) => {
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const chatContainerRef = useRef(null);
    const chatSocketRef = useRef(null);

    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        chatSocketRef.current = new WebSocket(`${protocol}://${window.location.host}/ws/${roomCode}/chat-socket/`);

        chatSocketRef.current.onopen = () => {
            chatSocketRef.current.send(JSON.stringify({ type: 'latest_messages_request' }));
        };

        chatSocketRef.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'chat') {
                setMessages((prevMessages) => [...prevMessages, data]);
            }
        };

        return () => {
            chatSocketRef.current.close();
        };
    }, [roomCode]);

    useEffect(() => {
        // Auto-scroll to the latest message
        const chatContainer = chatContainerRef.current;
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }, [messages]);

    const handleMessageInput = (e) => setMessageInput(e.target.value);

    const handleSendMessage = () => {
        if (messageInput.trim() === '') return;

        chatSocketRef.current.send(
            JSON.stringify({
                type: 'chat',
                message: messageInput,
                sender: 'You',
                timestamp: new Date().toLocaleTimeString(),
            })
        );

        setMessageInput('');
    };

    const handleKeyDown = (event) => {
        if (event.key === 'Enter') {
            handleSendMessage();
        }
    };

    const parseTimestamp = (timestamp) => {
        const [date, time] = timestamp.split(' ');
        const [day, month, year] = date.split('.');
        return new Date(`${year}-${month}-${day}T${time}`);
    };

    return (
        <Box
            sx={{
                height: '70vh',
                display: 'flex',
                flexDirection: 'column',
                border: '1px solid #ccc',
                borderRadius: '8px',
                overflow: 'hidden',
            }}
        >
            <Box
                sx={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: 2,
                    bgcolor: '#f9f9f9',
                }}
                ref={chatContainerRef}
            >
                {messages.length === 0 ? (
                    <Typography
                        variant="body1"
                        color="textSecondary"
                        align="center"
                        sx={{ mt: '50%' }}
                    >
                        No messages yet. Start the conversation!
                    </Typography>
                ) : (
                    messages.map((message, index) => (
                        <Box
                            key={index}
                            sx={{
                                mb: 1,
                                p: 1,
                                borderRadius: '12px',
                                bgcolor: 'white',
                                color: 'black',
                                alignSelf: message.sender === 'You' ? 'flex-end' : 'flex-start',
                                maxWidth: '70%',
                                border: '0.5px solid #333333',
                            }}
                        >
                            <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                {message.sender} [{parseTimestamp(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}]: {message.message}
                            </Typography>
                        </Box>
                    ))
                )}
            </Box>

            {/* Input Section */}
            <Box
                sx={{
                    display: 'flex',
                    p: 1.5,
                    borderTop: '1px solid #ccc',
                    bgcolor: '#fff',
                }}
            >
                <TextField
                    fullWidth
                    variant="outlined"
                    placeholder="Type a message..."
                    size="small"
                    value={messageInput}
                    onChange={handleMessageInput}
                    onKeyDown={handleKeyDown}
                    sx={{ borderRadius: '12px' }}
                />
                <Button
                    variant="outlined"
                    onClick={handleSendMessage}
                    size="small"
                    sx={{ ml: 1, borderRadius: '12px' }}
                >
                    Send
                </Button>
            </Box>
        </Box>
    );
};

export default Chat;

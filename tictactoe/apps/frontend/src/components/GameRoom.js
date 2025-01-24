import React, { Component, useState } from 'react';
import Grid from "@material-ui/core/Grid";
import Typography from "@material-ui/core/Typography";
import Dialog from '@material-ui/core/Dialog';
import DialogTitle from '@material-ui/core/DialogTitle';
import DialogActions from '@material-ui/core/DialogActions';
import Button from '@material-ui/core/Button';
import Box from "@material-ui/core/Box";
import Chat from "./Chat";
import {
    goToURL,
    getRequestOptions,
    fetchGameRoomData,
    formatTime,
    fetchTokensAndStore,
    calculateWinner
} from "./utils";


function Square({ value, onSquareClick }) {
    return (
        <Button
            variant="outlined"
            onClick={onSquareClick}
            style={{
                width: "12vw",
                height: "12vw",
                fontSize: "24px",
                margin: "5px",
            }}
        >
            {value}
        </Button>
    );
}


function Board({ xIsNext: nextMove, squares, onPlay, isHost, gameOption, startTime, elapsedTime, countdownDuration }) {
    const handleClick = (i) => {
        const currentPlayer = isHost ? (gameOption === 'x' ? 'X' : 'O') : (gameOption === 'x' ? 'O' : 'X');

        if ((currentPlayer === 'X' && nextMove === 'x') || (currentPlayer === 'O' && nextMove === 'o')) {
            if (squares[i] || calculateWinner(squares)) {
                return;
            }
            const nextSquares = squares.slice();
            nextSquares[i] = currentPlayer;
            onPlay(nextSquares);
        }
    };

    const status = `Next player: ${nextMove}`;

    return (
        <Box>
            <Typography variant="h6" align="center">{status}</Typography>
            <Grid container spacing={1} justifyContent="center">
                {Array.from({ length: 3 }).map((_, row) => (
                    <Grid container key={row} item xs={12} justifyContent="center">
                        {Array.from({ length: 3 }).map((_, col) => {
                            const idx = row * 3 + col;
                            return (
                                <Square
                                    key={idx}
                                    value={squares[idx]}
                                    onSquareClick={() => handleClick(idx)}
                                />
                            );
                        })}
                    </Grid>
                ))}
            </Grid>
            {startTime && (
                <Typography variant="body2" align="center">
                    Time left: {formatTime(countdownDuration - elapsedTime)}
                </Typography>
            )}
        </Box>
    );
}


export default class GameRoom extends Component {
    constructor(props) {
        super(props);
        this.state = {
            history: [Array(9).fill(null)],
            currentMove: 0,
            gameOption: 'r',
            isHost: false,
            selfRole: 'r',
            csrfToken: '',
            jwtToken: '',
            winner: null,
            startTime: null,
            elapsedTime: 0,
            player_x: null,
            player_o: null,
            isReadyPlayer_x: false,
            isReadyPlayer_o: false,
            isGameStarted: false,
            xIsNext: 'x',
        };
        this.gameRoomCode = this.props.gameRoomCode;
    }

    async componentDidMount() {
        try {
            await fetchTokensAndStore(this)
            await this.getRoomDetails()
            this.connectToRoomWebSocket();

            this.setState({
                selfRole: this.getSelfRole(),
            })

        } catch (error) {
            console.error('Error:', error);
        }
    }



    getSelfRole() {
        if (this.state.gameOption === 'x') {
            return this.state.isHost ? 'x' : 'o';
        } else if (this.state.gameOption === 'o') {
            return this.state.isHost ? 'o' : 'x';
        }
    }

    connectToRoomWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsRoomUrl = `${protocol}://${window.location.host}/ws/tictactoe-game-socket/${this.gameRoomCode}/`;
        this.roomSocket = new WebSocket(wsRoomUrl);

        this.roomSocket.onmessage = this.handleWebSocketMessage.bind(this);
        this.roomSocket.onopen = this.handleWebSocketOpen.bind(this);
    }

    handleWebSocketMessage(e) {
        const data = JSON.parse(e.data);
        switch (data.type) {
            case "game_state":
                const history = [...this.state.history];
                const currentMove = this.state.currentMove + 1;
                const nextHistory = history.slice(0, currentMove).concat([data.squares]);

                this.setState({
                    history: nextHistory,
                    currentMove: currentMove,
                    player_x: this.state.player_x || data.player_x,
                    player_o: this.state.player_o || data.player_o,
                    winner: data.winner,
                });
                if (data.xIsNext !== null) {
                    this.state.xIsNext = data.xIsNext
                }
                break;
            case "latest_gamestate":
                this.updateGameState(data);
                break;
            case "connection_established":
                this.handleConnectionEstablished(data);
                break;
            case "ready_x":
                this.setState({ isReadyPlayer_x: data.isReadyPlayer_x });
                break;
            case "ready_o":
                this.setState({ isReadyPlayer_o: data.isReadyPlayer_o });
                break;
            case "acknowledgement":
                this.setState({
                    player_x: this.state.player_x || data.player_x,
                    player_o: this.state.player_o || data.player_o,
                });
                break;
            default:
                break;
        }
    }

    handleWebSocketOpen() {
        this.roomSocket.send(JSON.stringify({
            room_code: this.gameRoomCode,
            type: 'latest_gamestate_request',
            player_x: this.state.player_x,
            player_o: this.state.player_o,
            squares: this.state.history[history.length - 1]
        }));
    }

    handleConnectionEstablished(data) {
        this.roomSocket.send(JSON.stringify({
            room_code: this.gameRoomCode,
            type: 'acknowledgement',
            player_x: this.state.player_x,
            player_o: this.state.player_o,
        }));
    }

    updateGameState(data) {
        const history = [...this.state.history];
        const currentMove = this.state.currentMove + 1;
        const nextHistory = history.slice(0, currentMove).concat([data.squares]);

        this.setState({
            history: nextHistory,
            currentMove: currentMove,
            player_x: this.state.player_x || data.player_x,
            player_o: this.state.player_o || data.player_o,
            winner: data.winner,
            isReadyPlayer_o: data.type === "latest_gamestate" ? true : this.state.isReadyPlayer_o,
            isReadyPlayer_x: data.type === "latest_gamestate" ? true : this.state.isReadyPlayer_x,
        });

        if (data.xIsNext !== null) {
            this.state.xIsNext = data.xIsNext
        }
    }

    async getRoomDetails() {
        const requestOptions = getRequestOptions(this, 'GET');

        const gameRoomData = await fetchGameRoomData(this.gameRoomCode, requestOptions);

        if (gameRoomData) {
            await new Promise((resolve) => {
                this.setState({
                    gameOption: gameRoomData.game_option,
                    isHost: gameRoomData.is_host,
                    player_x: gameRoomData.player_x,
                    player_o: gameRoomData.player_o,
                }, resolve);
            });
        } else {
            console.error('Failed to collect game room data');
        }
    }

    componentDidUpdate(prevProps, prevState) {
        const { currentMove, winner, isReadyPlayer_x, isReadyPlayer_o } = this.state;

        if (currentMove !== prevState.currentMove && !this.state.isGameStarted) {
            this.startGame();
        }

        if (winner !== prevState.winner && winner) {
            this.stopTimer();
        }


        if (this.state.selfRole === 'x' && prevState.isReadyPlayer_x !== this.state.isReadyPlayer_x){
            this.sendReadyState({isReadyPlayer_x: isReadyPlayer_x})
        } else if (this.state.selfRole === 'o' && prevState.isReadyPlayer_o !== this.state.isReadyPlayer_o) {
            this.sendReadyState({isReadyPlayer_o: isReadyPlayer_o})

        }
    }

    startGame() {
        this.startTimer();
        this.setState({ isGameStarted: true });

        this.roomSocket.send(JSON.stringify({
            room_code: this.gameRoomCode,
            type: 'game_started',
            player_x: this.state.player_x,
            player_o: this.state.player_o
        }));
    }

    stopTimer() {
        clearInterval(this.state.timerInterval);
    }

    sendReadyState(ready_state) {
        this.roomSocket.send(JSON.stringify({
            room_code: this.gameRoomCode,
            type: 'ready',
            ...ready_state
        }));
    }


    handlePlay = (nextSquares) => {
        const { history, currentMove } = this.state;
        const nextHistory = [...history.slice(0, currentMove), nextSquares];
        this.setState({
            history: nextHistory,
            currentMove: nextHistory.length - 1,
        });

        if (currentMove === 0 && !this.state.startTime) {
            this.startTimer();
        }
        if (this.state.xIsNext === 'x') {
            this.state.xIsNext = 'o'
        } else if (this.state.xIsNext === 'o') {
            this.state.xIsNext = 'x'
        } else {
            console.log("Error. Wrong type of xIsNext was passed")
        }

        this.roomSocket.send(JSON.stringify({
            room_code: this.gameRoomCode,
            type: 'game_state',
            squares: nextSquares,
            player_x: this.state.player_x,
            player_o: this.state.player_o,
            xIsNext: this.state.xIsNext
        }));
    };

    handleLeave = () => {
        goToURL('/games/')
    };

    startTimer() {
        const countdownDuration = 30 * 1000; // 30 seconds in milliseconds
        this.setState({ startTime: Date.now(), countdownDuration });

        this.state.timerInterval = setInterval(() => {
            const elapsedTime = Date.now() - this.state.startTime;
            const remainingTime = countdownDuration - elapsedTime;

            if (remainingTime <= 0) {
                clearInterval(this.state.timerInterval);
                this.setState({ elapsedTime: countdownDuration, isGameOver: true });
                this.timeWin()
            } else {
                this.setState({ elapsedTime });
            }
        }, 10);
    }

    timeWin() {
        let winner = null
        if (this.state.xIsNext === "X") {
            winner = this.state.player_o
        } else {
            winner = this.state.player_x
        }
        this.roomSocket.send(JSON.stringify({
            room_code: this.gameRoomCode,
            type: 'time_win',
            winner: winner,
            squares: this.state.history[this.state.currentMove],
            player_x: this.state.player_x,
            player_o: this.state.player_o,
        }));
    }

    componentWillUnmount() {
        clearInterval(this.state.timerInterval);
    }

    render() {
        const { history, currentMove, elapsedTime, winner, xIsNext } = this.state;
        const currentSquares = history[currentMove];

        return (
            <Grid container spacing={3}>
                <Grid item xs={2}>
                    <Typography variant="h4" align="center" style={{ padding: 20, textAlign: "center" }}>Tic Tac Toe</Typography>
                    <Typography style={{ textAlign: "center" }}>Room Code: {this.gameRoomCode}</Typography>
                    <Typography style={{ textAlign: "center" }}>Game mode: {this.state.gameOption}</Typography>
                    <Typography style={{ textAlign: "center" }}>Host: {this.state.isHost.toString()}</Typography>
                    <Typography style={{ textAlign: "center" }}>Player X: {this.state.player_x}</Typography>
                    <Typography style={{ textAlign: "center" }}>Player O: {this.state.player_o}</Typography>
                    <Chat roomCode={this.gameRoomCode}/>
                </Grid>
                <Grid item xs={10}>
                    {this.state.isReadyPlayer_x && this.state.isReadyPlayer_o ? (
                    <Board
                        xIsNext={xIsNext}
                        squares={currentSquares}
                        onPlay={this.handlePlay}
                        isHost={this.state.isHost}
                        gameOption={this.state.gameOption}
                        startTime={this.state.startTime}
                        elapsedTime={elapsedTime}
                        countdownDuration={this.state.countdownDuration}
                    />
                ) : (
                    <div style={{ marginTop: "20px", textAlign: "center" }}>
                        {!this.state.isReadyPlayer_x && this.state.selfRole === 'x' && (
                            <Button
                                variant="outlined"
                                onClick={() => this.setState({ isReadyPlayer_x: true })}
                                style={{ marginBottom: "10px" }}
                            >
                                Player X Ready
                            </Button>
                        )}
                        {!this.state.isReadyPlayer_o && this.state.selfRole === 'o' && (
                            <Button
                                variant="outlined"
                                onClick={() => this.setState({ isReadyPlayer_o: true })}
                                style={{ marginBottom: "10px" }}
                            >
                                Player O Ready
                            </Button>
                        )}
                        <Typography variant="h6" style={{ marginTop: "20px" }}>
                            Waiting for all players to be ready...
                        </Typography>
                    </div>
                )}
                </Grid>

                {winner && (
                    <Dialog open={true}>
                        <DialogTitle>{`Winner: ${winner}`}</DialogTitle>
                        <DialogActions>
                            <Button onClick={this.handleLeave} color="secondary">Exit</Button>
                        </DialogActions>
                    </Dialog>
                )}
            </Grid>
        );
    }
}
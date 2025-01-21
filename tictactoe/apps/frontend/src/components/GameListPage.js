import React, { Component } from 'react';
import {
    Grid,
    Typography,
    FormControl,
    FormHelperText,
    RadioGroup,
    FormControlLabel,
    Radio,
    Button,
    TextField,
    TableCell,
    TableBody,
    TableHead,
    TableRow,
    TableContainer,
    Table,
    Paper,
    Switch,
} from '@material-ui/core';
import {
    goToURL,
    getRequestOptions,
    createGameRoom,
    fetchGameRoomData,
    fetchGameRoomsList,
    cancelGameRoom,
    fetchTokensAndStore
} from "./utils";


export default class RouterPage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            game_option: 'r',
            csrfToken: '',
            jwtToken: '',
            gameRooms: [],
            searching: false,
            isPrivateGame: true,
        };
    }

    async componentDidMount() {
        try {
            await fetchTokensAndStore(this);
            await this.handleRefreshButtonClicked();
        } catch (error) {
            console.error('Error during component mount:', error);
        }
    }

    componentWillUnmount() {
        if (this.state.searchQueueSocket) {
            this.state.searchQueueSocket.close();
        }
    }

    handleGameOptionChange = (e) => {
        this.setState({ game_option: e.target.value });
    };

    handleGameCodeInputChange = (e) => {
        this.roomCodeInput = e.target.value;
    };

    handleCreateButtonClicked = async () => {
        const { game_option, jwtToken } = this.state;

        let requestOptions = getRequestOptions(this, 'POST');
        requestOptions.body = JSON.stringify({ game_option, jwt_token: jwtToken });

        const gameRoomURL = await createGameRoom(requestOptions);
        if (gameRoomURL) {
            goToURL(gameRoomURL)
        } else {
            console.error('Failed to create game room.');
        }
    };

    handleJoinButtonClicked = async () => {
        const requestOptions = getRequestOptions(this, 'GET');

        const roomData = await fetchGameRoomData(this.roomCodeInput, requestOptions);
        const gameRoomURL = `/games/room/${this.roomCodeInput}`;
        if (roomData) {
            goToURL(gameRoomURL);
        } else {
            console.error('Failed to join game');
        }
    };

    handleSearchButtonClicked = async () => {
        try {
            await this.connectSearchQueueSocket();
        } catch (error) {
            console.error('Error connecting to search queue socket:', error);
        }
    };

    async connectSearchQueueSocket() {
        const searchQueueSocketURL =  this.getSearchQueueSocketURL();
        const searchQueueSocket = new WebSocket(searchQueueSocketURL);

        await this.setupSearchQueueSocketEventHandlers(searchQueueSocket);

        this.setState({ searchQueueSocket });
    }

    async setupSearchQueueSocketEventHandlers(socket) {
        socket.onopen = () => this.setState({ searching: true });
        socket.onclose = () => this.setState({ searching: false });

        socket.onmessage = (event) => this.handleSocketMessage(event);
    }

    handleSocketMessage(event) {
        try {
            const searchQueueData = JSON.parse(event.data);
            if (searchQueueData.type === 'match_found') {
                this.setState({ searching: false });
                this.handleMatchFound(searchQueueData.gameRoomCode);
            }
        } catch (error) {
            console.error('Error processing socket message:', error);
        }
    }

    async handleMatchFound(gameRoomCode) {
        try {
            const requestOptions = getRequestOptions(this, 'GET');
            const data = await fetchGameRoomData(gameRoomCode, requestOptions);

            if (data.room_exists) {
                goToURL(`/games/room/${gameRoomCode}`)
            } else {
                console.error('Room not found:', data);
            }
        } catch (error) {
            console.error('Error handling match:', error);
        }
    }

    getSearchQueueSocketURL() {
        const { jwtToken, sessionKey } = this.state;
        return `ws://${window.location.host}/ws/search-queue/${jwtToken}/${sessionKey}/`;
    }

    handleRefreshButtonClicked = async () => {
        const requestOptions = getRequestOptions(this, 'GET');

        const gameRooms = await fetchGameRoomsList(requestOptions);

        if (gameRooms.error) {
            console.error('Fetching game rooms failed:', gameRooms.error);
            return;
        }
        this.setState({ gameRooms: gameRooms });
    };

    handleCancelGameButtonClicked = async (room_code) => {
        const requestOptions = getRequestOptions(this, 'DELETE');

        const response = await cancelGameRoom(room_code, requestOptions);

        if (response.error) {
            console.error('Cancel game failed:', response.error);
            return;
        }

        await this.handleRefreshButtonClicked();
    };

    handleToggleSwitch = () => {
        this.setState((prevState) => ({ isPrivateGame: !prevState.isPrivateGame }));
    };

    renderGameRooms() {
        const { gameRooms } = this.state;
        if (!gameRooms.length) {
            return (
                <>
                    <Grid item xs={3} align="center">
                        <Typography variant="h5" style={{ marginBottom: 10 }}>
                            Games List
                        </Typography>
                        <Button
                            variant="contained"
                            style={{ minWidth: '40%', maxWidth: '40%' }}
                            onClick={this.handleRefreshButtonClicked}
                        >
                            Refresh
                        </Button>
                        <Typography style={{ marginTop: 10 }}>
                            No public games available.
                        </Typography>
                    </Grid>
                </>
            );
        }

        return (
            <>
            <Grid item xs={3} align="center">
                <Typography variant="h5" style={{ marginBottom: 10 }}>
                        Games List
                </Typography>
                <Button variant="contained" style={{minWidth: '40%', maxWidth: '40%'}}
                        onClick={this.handleRefreshButtonClicked}>
                    Refresh
                </Button>
            </Grid>
            <TableContainer component={Paper} style={{ marginTop: 20 }}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell align="center"><strong>Game Code</strong></TableCell>
                            <TableCell align="center"><strong>Player X</strong></TableCell>
                            <TableCell align="center"><strong>Player O</strong></TableCell>
                            <TableCell align="center"><strong>Action</strong></TableCell>

                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {gameRooms.map((room) => (
                            <TableRow key={room.id}>
                                <TableCell align="center">{room.code}</TableCell>
                                <TableCell align="center">{room.player_x_username || '-'}</TableCell>
                                <TableCell align="center">{room.player_o_username || '-'}</TableCell>
                                <TableCell align="center">
                                    <div style={{}}>
                                        {(!room.player_x_username || !room.player_o_username
                                            || room.player_x_username === this.state.username
                                            || room.player_o_username === this.state.username) && (
                                        <Button
                                            variant="outlined"
                                            size="small"
                                            onClick={() => (window.location.href = `/games/room/${room.code}`)}
                                        >
                                            Join
                                        </Button>
                                        )}
                                        {(room.player_x_username === this.state.username || room.player_o_username === this.state.username) &&
                                          (room.player_x_username === null || room.player_o_username === null) && (
                                            <Button
                                                variant="outlined"
                                                color="secondary"
                                                size="small"
                                                onClick={() => this.handleCancelGameButtonClicked(room.code)}
                                            >
                                                Cancel Game
                                            </Button>
                                        )}
                                    </div>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </>
        );
    }

    render() {
        const {isPrivateGame, searching} = this.state;

        return (
            <>
                <Grid container spacing={3} alignItems="center" justifyContent="center" style={{marginTop: 15}}>
                <Grid item>
                        <Typography variant="h6">Private Game</Typography>
                    </Grid>
                    <Grid item>
                        <Switch checked={!isPrivateGame} onChange={this.handleToggleSwitch} color="secondary" />
                    </Grid>
                    <Grid item>
                        <Typography variant="h6">Public Game</Typography>
                    </Grid>
                </Grid>

                {isPrivateGame ? (
                    <>
                        <Grid container spacing={3} alignItems="center" justifyContent="center" style={{ marginTop: 15 }}>
                            {/* Create a Game Section */}
                            <Grid item xs={12} sm={6} align="center">
                                <Typography variant="h5" style={{ marginBottom: 10 }}>
                                    Create a Game
                                </Typography>
                                <FormControl component="fieldset">
                                    <FormHelperText style={{ marginBottom: 10 }}>Choose your game settings:</FormHelperText>
                                    <RadioGroup row defaultValue='r' onChange={this.handleGameOptionChange}>
                                        <FormControlLabel value="r" control={<Radio />} label="Random" />
                                        <FormControlLabel value="x" control={<Radio />} label="Play as X" />
                                        <FormControlLabel value="o" control={<Radio />} label="Play as O" />
                                    </RadioGroup>
                                </FormControl>
                                <Button
                                    variant="contained"
                                    onClick={this.handleCreateButtonClicked}
                                    style={{ marginTop: 15 }}
                                >
                                    Create Game
                                </Button>
                            </Grid>

                            {/* Join a Game Section */}
                            <Grid item xs={12} sm={6} align="center">
                                <Typography variant="h5" style={{ marginBottom: 10 }}>
                                    Join a Game
                                </Typography>
                                <TextField
                                    label="Game Code"
                                    variant="outlined"
                                    size="small"
                                    color="secondary"
                                    onChange={this.handleGameCodeInputChange}
                                    style={{ marginBottom: 10, marginRight: 5, width: '15%' }}
                                />
                                <Button
                                    variant="contained"
                                    onClick={this.handleJoinButtonClicked}
                                >
                                    Join Game
                                </Button>
                            </Grid>
                        </Grid>
                        <Grid container spacing={3} style={{ marginTop: 15 }}>
                            <Grid item xs={6} align="center">
                                <Button
                                    variant="contained"
                                    onClick={() => (window.location.href = `/games/room/offline`)}
                                >
                                    Create Local Game
                                </Button>
                            </Grid>
                        </Grid>
                        <Grid container spacing={3} style={{ marginTop: 30 }}>
                            {this.renderGameRooms()}
                        </Grid>
                    </>
                ) : (
                    /* Public toggle */
                    <Grid container spacing={3} alignItems="center" justifyContent="center" style={{ marginTop: 15 }}>
                        <Grid item xs={12} align="center">
                            <Button variant="outlined" onClick={this.handleSearchButtonClicked}>
                                Search Game
                            </Button>
                            {searching && (
                                <Typography variant="body1" color="textSecondary">
                                    Searching for a match, please wait...
                                </Typography>
                            )}
                        </Grid>
                    </Grid>
                )}
            </>
        );
    }
}

import React, { useState } from 'react';
import { Grid, Typography, Dialog, DialogTitle, DialogActions, Button, Box } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import {
    calculateWinner,
    goToURL
} from "./utils";

const NUM_SQUARES = 9;

const useStyles = makeStyles((theme) => ({
    squareButton: {
        width: "12vw",
        height: "12vw",
        fontSize: "24px",
        margin: "5px",
    },
    gameInfo: {
        fontSize: '16px',
    },
    historyButton: {
        fontSize: '14px',
        padding: '5px 10px',
    },
}));

function Square({ value, onSquareClick }) {
    const classes = useStyles();
    return (
        <Button
            className={classes.squareButton}
            variant="outlined"
            onClick={onSquareClick}
            aria-label={`Square ${value ? value : 'empty'}`}
        >
            {value}
        </Button>
    );
}

function Board({ isPlayerXTurn, boardState, onPlayerMove }) {
    const handleSquareClick = (i) => {
        if (boardState[i] || calculateWinner(boardState)) return;
        const currentPlayer = isPlayerXTurn ? 'X' : 'O';
        const nextBoardState = [...boardState];
        nextBoardState[i] = currentPlayer;
        onPlayerMove(nextBoardState);
    };

    return (
        <Box>
            <Typography variant="h6" align="center">{`Next player: ${isPlayerXTurn ? 'X' : 'O'}`}</Typography>
            <Grid container spacing={1} justifyContent="center">
                {Array.from({ length: 3 }).map((_, row) => (
                    <Grid container key={row} item xs={12} justifyContent="center">
                        {Array.from({ length: 3 }).map((_, col) => {
                            const idx = row * 3 + col;
                            return (
                                <Square
                                    key={idx}
                                    value={boardState[idx]}
                                    onSquareClick={() => handleSquareClick(idx)}
                                />
                            );
                        })}
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
}

function MoveHistory({ moveHistory, onMoveJump }) {
    return (
        <Box>
            <Typography variant="h6">History:</Typography>
            <ol>
                {moveHistory.map((boardState, move) => {
                    const description = move > 0 ? `Go to move #${move}` : 'Go to game start';
                    return (
                        <li key={move}>
                            <Button
                                onClick={() => onMoveJump(move)}
                                className="historyButton"
                            >
                                {description}
                            </Button>
                        </li>
                    );
                })}
            </ol>
        </Box>
    );
}

function GameRoom() {
    const [moveHistory, setMoveHistory] = useState([Array(NUM_SQUARES).fill(null)]);
    const [currentMove, setCurrentMove] = useState(0);
    const [winner, setWinner] = useState(null);
    const [isPlayerXTurn, setIsPlayerXTurn] = useState(true);

    const handlePlayerMove = (nextBoardState) => {
        const nextMoveHistory = [...moveHistory.slice(0, currentMove + 1), nextBoardState];
        setMoveHistory(nextMoveHistory);
        setCurrentMove(nextMoveHistory.length - 1);
        setIsPlayerXTurn(!isPlayerXTurn);

        const calculatedWinner = calculateWinner(nextBoardState);
        if (calculatedWinner) {
            setWinner(calculatedWinner);
        }
    };

    const handleMoveJump = (move) => {
        setCurrentMove(move);
        setIsPlayerXTurn(move % 2 === 0); // X if even, O if odd
    };

    const handleRestart = () => {
        setMoveHistory([Array(NUM_SQUARES).fill(null)]);
        setCurrentMove(0);
        setWinner(null);
        setIsPlayerXTurn(true);
    };

    const handleLeave = () => {
        goToURL('/games/')
    };

    const currentBoardState = moveHistory[currentMove];

    return (
        <Grid container spacing={3}>
            <Grid item xs={2}>
                <Typography variant="h4" align="center" style={{ padding: 20 }}>
                    Tic Tac Toe (Local play)
                </Typography>
                <MoveHistory moveHistory={moveHistory} onMoveJump={handleMoveJump} />
            </Grid>
            <Grid item xs={10}>
                <Board isPlayerXTurn={isPlayerXTurn} boardState={currentBoardState} onPlayerMove={handlePlayerMove} />
            </Grid>

            {winner && (
                <Dialog open={true}>
                    <DialogTitle>{`Winner: ${winner}`}</DialogTitle>
                    <DialogActions>
                        <Button onClick={handleRestart} color="primary">Restart</Button>
                        <Button onClick={handleLeave} color="secondary">Exit</Button>
                    </DialogActions>
                </Dialog>
            )}
        </Grid>
    );
}

export default GameRoom;
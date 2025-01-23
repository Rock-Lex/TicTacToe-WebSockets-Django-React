import React, { Component } from "react";
import GameRoom from './GameRoom';
import GameListPage from './GameListPage';
import GameRoomOffline from "./GameRoomOffline";
import {
    BrowserRouter as Router,
    Routes,
    Route,
    useParams
} from "react-router-dom";

const GameRoomWrapper = () => {
    const params = useParams();
    const { gameRoomCode } = params;

    return <GameRoom gameRoomCode={gameRoomCode}/>;
};

export default class RouterPage extends Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
           <Router>
                <Routes>
                    <Route path="/" />
                    <Route path="/games" element={<GameListPage />} />
                    <Route path="/games/room/:gameRoomCode" element={<GameRoomWrapper />} />
                    <Route path="/games/room/offline" element={<GameRoomOffline/>} />
                </Routes>
            </Router>
        );
    }
}
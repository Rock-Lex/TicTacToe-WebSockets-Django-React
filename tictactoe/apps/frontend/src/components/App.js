import React, { Component } from "react";
import { render } from "react-dom";
import RouterPage from './RouterPage';
import GameRoom from './GameRoom';

export default class App extends Component {
    constructor(props) {
        super(props);
    }

    render() {
        const { gameData } = this.props;
        return (
            <>
                <RouterPage />
            </>
        );
    }
}

const appDiv = document.getElementById("app");
render(<App />, appDiv);

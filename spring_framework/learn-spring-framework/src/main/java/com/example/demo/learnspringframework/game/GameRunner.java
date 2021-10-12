package com.example.demo.learnspringframework.game;

public class GameRunner {
    private SuperContraGame game;

    public GameRunner(SuperContraGame game) {
        this.game = game;
    }


    public void run() {
        game.up();
        game.down();
        game.right();
        game.left();
    }

}

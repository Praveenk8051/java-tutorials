package com.example.demo.learnspringframework;

import com.example.demo.learnspringframework.game.GameRunner;
import com.example.demo.learnspringframework.game.MarioGame;
import com.example.demo.learnspringframework.game.SuperContraGame;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class LearnSpringFrameworkApplication {

	public static void main(String[] args) {


		//MarioGame game = new MarioGame();
		SuperContraGame game = new SuperContraGame();

		GameRunner runner = new GameRunner(game);
		runner.run();


	}

}

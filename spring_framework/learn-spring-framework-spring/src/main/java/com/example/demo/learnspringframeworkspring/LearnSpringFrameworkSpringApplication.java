package com.example.demo.learnspringframeworkspring;

import com.example.demo.learnspringframeworkspring.game.GameRunner;
import com.example.demo.learnspringframeworkspring.game.MarioGame;
import com.example.demo.learnspringframeworkspring.game.SuperContraGame;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;

@SpringBootApplication
public class LearnSpringFrameworkSpringApplication {

	public static void main(String[] args) {
		ConfigurableApplicationContext context =
				SpringApplication.run(LearnSpringFrameworkSpringApplication.class, args);
		// MarioGame, GameRunner
		GameRunner runner = context.getBean(GameRunner.class);

		//MarioGame game = new MarioGame();
		//SuperContraGame game = new SuperContraGame();

		//GameRunner runner = new GameRunner(game);
		runner.run();


	}

}

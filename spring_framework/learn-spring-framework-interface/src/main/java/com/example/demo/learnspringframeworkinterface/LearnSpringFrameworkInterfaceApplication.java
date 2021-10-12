package com.example.demo.learnspringframeworkinterface;

import com.example.demo.learnspringframeworkinterface.game.GameRunner;
import com.example.demo.learnspringframeworkinterface.game.MarioGame;
import com.example.demo.learnspringframeworkinterface.game.SuperContraGame;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class LearnSpringFrameworkInterfaceApplication {

	public static void main(String[] args) {
		MarioGame game = new MarioGame();
		//SuperContraGame game = new SuperContraGame();

		GameRunner runner = new GameRunner(game);
		runner.run();


	}

}

package com.company;

import java.util.List;
import java.util.stream.IntStream;

public class Main {

    public static void main(String[] args) {
	    IntStream.range(1,11).map(e->e*e).forEach(p-> System.out.println(p));

        List<String> words = List.of("Apple", "Cat", "Bat");
        words.stream().map(s->s.toLowerCase()).forEach(p-> System.out.println(p));

        
    }
}

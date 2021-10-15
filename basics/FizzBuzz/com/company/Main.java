package com.company;

import java.util.Scanner;

public class Main {

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        System.out.print("Enter the Number: ");
        int number = scanner.nextInt();

        if (number % 5 == 0 && number % 3 == 0)
            System.out.print("FizzBuzz");
        else if (number % 5 == 0)
            System.out.printf("Fizz");
        else if (number % 3 == 0)
            System.out.printf("Buzz");
        else
            System.out.println(number);
    }
}

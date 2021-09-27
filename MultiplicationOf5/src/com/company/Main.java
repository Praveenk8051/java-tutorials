package com.company;

import java.sql.SQLOutput;
import java.util.Scanner;

public class Main {

    public static void main(String[] args) {

    int index;
    int number;
    Scanner scanner = new Scanner(System.in);

    while(true){
        System.out.print("Enter the Multiplication Number: ");
        number = scanner.nextInt();
        if (number>0 && number <10000)
            break;
        System.out.println("Enter a value between 0 and 10000");

    }

    for (index=1; index <=10; index++){
        System.out.println("5 * "+ index +" = " + number * index);
    }
    }
}

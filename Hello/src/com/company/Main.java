package com.company;
import java.awt.*;
import java.util.Arrays;
import java.util.Date;
import java.util.Locale;
import java.util.Scanner;

public class Main {

    public static void main(String[] args) {
        int age = 30;
        int[] numbers = new int[3];
        numbers[1] = 1;
        numbers[2] = 2;
        long viewsCount = 3_132_456_789L;
        String message = "Hello String";
        System.out.print(Arrays.toString(numbers));
        Date now = new Date();
        //now.getTime();
        System.out.println(now);

        int temp = 32;
        if (temp>30){
            System.out.print("It's hot day");
        }else if (temp > 20 && temp <= 30)
            System.out.println("Beautiful day");
        else{
            System.out.println("Cold Day");
        }
        for (int i = 5; i<0; i--) {
            System.out.print("Hello World");
        }
        Scanner scanner = new Scanner(System.in);
        String input = "";
        while (true){
            System.out.print("Input: ");
            input = scanner.next().toLowerCase();
            if (input.equals("quit"))
                break;
            System.out.println(input);
        }


//        do{
//            System.out.print("Input: ");
//            input = scanner.next().toLowerCase();
//            System.out.println(input);
//        }while(!input.equals("quit"));




    }
}

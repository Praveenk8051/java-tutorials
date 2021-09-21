package com.company;
import java.awt.*;
import java.util.Arrays;
import java.util.Date;

public class Main {

    public static void main(String[] args) {
        int age = 30;
        int[] numbers = new int[3];
        numbers[1] = 1;
        numbers[2] = 2;
        

        long viewsCount = 3_132_456_789L;
        String message = "Hello String";
        System.out.println(Arrays.toString(numbers));


        Date now = new Date();
        now.getTime();
        System.out.println(now);


    }
}

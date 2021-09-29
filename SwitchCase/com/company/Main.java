//
// Source code recreated from a .class file by IntelliJ IDEA
// (powered by FernFlower decompiler)
//

package com.company;

import java.util.Scanner;

public class Main {
    public Main() {
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        System.out.println("Enter the Day Number");
        int dayNumber = scanner.nextInt();
        System.out.println(isWeekDay(dayNumber));
        System.out.println("Enter the Month Number");
        int monthNumber = scanner.nextInt();
        System.out.println(determineNameOfMonth(monthNumber));
        System.out.println("Enter the Week Day Number");
        int weekDayName = scanner.nextInt();
        System.out.println(determineNameOfDay(weekDayName));
    }

    private static String determineNameOfDay(int weekDayName) {
        String result = "";
        switch(weekDayName) {
            case 1:
                result = "Sunday";
                break;
            case 2:
                result = "Monday";
                break;
            case 3:
                result = "Tuesday";
                break;
            case 4:
                result = "Wednesday";
                break;
            case 5:
                result = "Thursday";
                break;
            case 6:
                result = "Friday";
                break;
            case 7:
                result = "Saturday";
                break;
            default:
                result = "Invalid Option";

        }
        return result;
    }

    private static String determineNameOfMonth(int monthNumber) {
        String result = "";
        switch(monthNumber) {
            case 1:
                result = "January";
                break;
            case 2:
                result = "February";
                break;
            case 3:
                result = "March";
                break;
            case 4:
                result = "April";
                break;
            case 5:
                result = "May";
                break;
            case 6:
                result = "June";
                break;
            case 7:
                result = "July";
                break;
            case 8:
                result = "August";
                break;
            case 9:
                result = "September";
                break;
            case 10:
                result = "October";
                break;
            case 11:
                result = "November";
                break;
            case 12:
                result = "December";
                break;
            default:
                result = "Invalid Option";
                break;

        }
        return result;
    }

    private static boolean isWeekDay(int dayNumber) {
        boolean result = false;
        switch(dayNumber) {
            case 0:
            case 6:
                result = true;
            default:
                result = false;

        }
        return result;
    }
}

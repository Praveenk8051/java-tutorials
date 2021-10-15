package com.company;

public class Main {

    public static void main(String[] args) {

        printNumbers(5);
        printNumberSquares(5);
        System.out.println(maxNumber(5,6 ));
        System.out.println(calTriSide(5,6 ));
        MultiplicationTable table = new MultiplicationTable();
        table.print(5);
        table.print(6);

    }

    private static void printNumbers(int i) {
        for(int index=1;index<=i;index++){
            System.out.println("Number: "+index);
        }
    }
    private static void printNumberSquares(int i){
        System.out.println("Number: "+ Math.pow(i, 2));
    }
    private static int maxNumber(int i, int j){
        return Math.max(i, j);
    }
    private static int calTriSide(int i, int j){
        return 180 - (i+j);
    }
}

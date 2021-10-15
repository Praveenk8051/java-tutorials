package com.company;

public class Main {

    public static void main(String[] args) {

        MyNumber number = new MyNumber(12);
        number.isPrime();
        int sum = number.sumUptoN();
        System.out.println(sum);
        int sumOfDivisors = number.sumOfDivisors();
        System.out.println(sumOfDivisors);
        number.printANumberTriangle();

    }
}

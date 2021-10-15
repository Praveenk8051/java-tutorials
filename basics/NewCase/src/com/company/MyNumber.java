package com.company;

public class MyNumber {
    private int number;
    public MyNumber(int number) {
        this.number = number;
    }

    public void isPrime() {
        if (number % 2== 0)
            System.out.println("Not a prime number");
        else
            System.out.println("Prime Number");
    }

    public int sumUptoN() {
        int result = 0;
        for (int i=0; i<=number;i++)
            result += number;
        return result;
    }

    public int sumOfDivisors() {
        int result = 0;
        for(int i=2; i< number;i++)
            if (number % i == 0)
                result += i;

        return result;
    }

    public void printANumberTriangle() {
        for(int i=1; i<=number;i++) {
            for (int j = 1; j <= i; j++) {
                System.out.print(j + " ");
            }
            System.out.println();
        }
    }
}

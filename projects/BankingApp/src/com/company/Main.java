package com.company;

public class Main {

    public static void main(String[] args) {
        AccountCreate praveenAccount = new AccountCreate("", 123456, "abc@gmail.com", 1234567890, 0);
        praveenAccount.deposit(123);

        praveenAccount.withDraw(123);
    }
}

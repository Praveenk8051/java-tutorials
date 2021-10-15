package com.company;

public class AccountCreate {
    private  String name;
    private  String email;
    private  long phoneNumber;
    private  long accountNumber;
    private double balance;

    public AccountCreate(String name, long accountNumber, String email, long phoneNumber, double balance) {
        this.name = name;
        this.accountNumber = accountNumber;
        this.email = email;
        this.phoneNumber = phoneNumber;
        this.balance = balance;
    }

    public void deposit(double balance) {
        this.balance += balance;
        System.out.println("The balance now is "+this.balance);

    }

    public void withDraw(double balance) {
        if(this.balance < balance)
            System.out.println("Withdrawal is not possible");
        else {
            this.balance -= balance;
            System.out.println("The balance now is "+this.balance);
        }
    }




    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public long getAccountNumber() {
        return accountNumber;
    }

    public void setAccountNumber(long accountNumber) {
        this.accountNumber = accountNumber;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public long getPhoneNumber() {
        return phoneNumber;
    }

    public void setPhoneNumber(long phoneNumber) {
        this.phoneNumber = phoneNumber;
    }



}

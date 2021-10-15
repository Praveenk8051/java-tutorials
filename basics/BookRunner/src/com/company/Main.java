package com.company;



public class Main {

    public static void main(String[] args) {


	    Book book = new Book(123, "Java Book", "Praveen");
        book.addReview(new Review(10, "Great Book", 5));
        book.addReview(new Review(101, "Not bad Book", 3));

        System.out.println(book);
    }


}

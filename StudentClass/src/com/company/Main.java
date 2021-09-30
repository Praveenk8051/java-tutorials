package com.company;

import java.math.BigDecimal;

public class Main {

    public static void main(String[] args) {

    int[] marks = {100, 95, 96, 87};

	Student student =new Student("Praveen", marks);
    int number = student.getNumberOfMarks();
    System.out.println("Number of Marks: " + number);
    int sum =student.getTotalSumOfMarks();
    System.out.println("Sum of Marks: " + sum);
    int maximumMark = student.getMaximumMark();
    System.out.println("Maximum of Marks: " + maximumMark);
    int minimumMark = student.getMinimumMark();
    System.out.println("Minimum of Marks: " + minimumMark);
    BigDecimal average = student.getAverageMarks();
    System.out.println("Average of Marks: " + average);
    }
}

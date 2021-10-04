package com.company;

import java.math.BigDecimal;
import java.math.RoundingMode;

public class Student {
    private String name = "";
    private int[] listOfMarks = {};

    public Student(String name, int... listOfMarks) {
    this.name = name;
    this.listOfMarks = listOfMarks;
    }


    public int getNumberOfMarks() {
        return listOfMarks.length;
    }

    public int getTotalSumOfMarks() {
        int sum = 0;
        for(int mark:listOfMarks)
            sum +=mark;
        return sum;
    }

    public int getMaximumMark() {
        int max = Integer.MIN_VALUE;
        for(int mark:listOfMarks)
            if (mark > max)
                max = mark;
        return max;
    }

    public int getMinimumMark() {
        int min = Integer.MAX_VALUE;
        for(int mark:listOfMarks)
            if (mark < min)
                min = mark;
        return min;
    }

    public BigDecimal getAverageMarks() {
        int sum = getTotalSumOfMarks();
        int total = getNumberOfMarks();

        return new BigDecimal(sum).divide(new BigDecimal(total), 3, RoundingMode.UP);
    }
}

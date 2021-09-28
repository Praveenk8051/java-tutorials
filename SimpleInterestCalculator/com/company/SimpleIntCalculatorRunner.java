package com.company;

import java.math.BigDecimal;

public class SimpleIntCalculatorRunner {


    public static void main(String[] args) {
        SimpleIntCalculator calculator = new SimpleIntCalculator("4500.00", "7.5");
        BigDecimal totalValue = calculator.calculateTotalValue(5) ;
        System.out.println(totalValue);
    }
}

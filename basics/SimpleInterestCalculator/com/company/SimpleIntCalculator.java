package com.company;

import java.math.BigDecimal;

public class SimpleIntCalculator {

    BigDecimal principle;
    BigDecimal interest;

    public SimpleIntCalculator(String principal, String interest) {
        this.principle = new BigDecimal(principal);
        this.interest = new BigDecimal(interest);

    }

    public BigDecimal calculateTotalValue(int noOfYears) {
        // principal + principal*interest*noOfYears
        return principle.add(principle.multiply(interest).multiply(new BigDecimal(noOfYears)));
    }
}

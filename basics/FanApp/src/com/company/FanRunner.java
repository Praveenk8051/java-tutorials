package com.company;

import java.awt.*;

public class FanRunner {

    public static void main(String[] args) {
        Fan fan = new Fan("Man", 1.2, "red");
        fan.switchOn();
        System.out.println(fan);
        fan.switchOff();
        System.out.println(fan);



    }
}

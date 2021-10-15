package com.company;

public class CharCheckRunner {

    public static void main(String[] args) {
	MyChar myChar = new MyChar('c');
    System.out.println(myChar.isVowel());
    System.out.println(myChar.isDigit());
    System.out.println(myChar.isAlphabet());
    myChar.printLowerCaseAlphabets();
    myChar.printUpperCaseAlphabets();
    }
}

package com.company;

public class MyChar {
    private char ch;
    private final char[] vowels = {'a', 'e', 'i', 'o', 'u'};
    public MyChar(char ch) {
        this.ch = ch;
    }

    public char[] getVowels() {
        return vowels;
    }

    public boolean isVowel() {
        // List and array based implemented later
        if (ch == 'a' || ch == 'e' ||ch == 'i' ||ch == 'o' ||ch == 'u' )
            return true;
        return false;
    }

    public boolean isDigit() {
        if (ch>=48 && ch<=57)
            return true;
        return false;
    }

    public boolean isAlphabet() {
        if (ch>=97 && ch<=122)
            return true;
        if (ch>=65 && ch<=90)
            return true;
        return false;
    }

    public static void printLowerCaseAlphabets() {
        for(char ch='a'; ch <= 'z';ch++){
            System.out.print(ch);
        }

    }

    public static void printUpperCaseAlphabets() {
        for(char ch='A'; ch <= 'Z';ch++){
            System.out.print(ch);
        }

    }
}

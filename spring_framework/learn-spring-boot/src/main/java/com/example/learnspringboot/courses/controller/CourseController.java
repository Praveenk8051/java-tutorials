package com.example.learnspringboot.courses.controller;

import com.example.learnspringboot.courses.bean.Course;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Arrays;
import java.util.List;

@RestController
public class CourseController {
    // Request: http://localhost:8080/courses
    /* Response:
    * [
    *   {
    *       "id":1,
    *       "name": "LearnMicroservices"
    *       "author": Praveen
    *   }
    * ]
    * */
    @GetMapping("/courses")
    public List<Course> getAllCourses(){
        return Arrays.asList(new Course(1, "Learn Microservice", "in28Minutes"));
    }


}

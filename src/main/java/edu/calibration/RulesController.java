package edu.calibration;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RulesController {

    private final EnrollmentRules rules;

    public RulesController(EnrollmentRules rules) {
        this.rules = rules;
    }

    @GetMapping("/api/rules")
    public EnrollmentRules rules() {
        return rules;
    }
}

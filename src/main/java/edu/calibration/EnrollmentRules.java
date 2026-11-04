package edu.calibration;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties("enrollment.rules")
public record EnrollmentRules(
        @Min(0) @Max(10000) int maxWaitlistSize,
        @Min(1) @Max(30) int maxCredits,
        @Min(1) @Max(365) int registrationWindowDays) {
}

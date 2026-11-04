package edu.calibration;

import java.time.LocalDate;
import org.springframework.stereotype.Service;

@Service
public class EnrollmentPolicy {

    private final EnrollmentRules rules;

    public EnrollmentPolicy(EnrollmentRules rules) {
        this.rules = rules;
    }

    public boolean canJoinWaitlist(int currentSize) {
        if (currentSize < 0) {
            throw new IllegalArgumentException("Current size cannot be negative");
        }
        return currentSize < rules.maxWaitlistSize();
    }

    public boolean canTakeCredits(int requestedCredits) {
        return requestedCredits > 0 && requestedCredits <= rules.maxCredits();
    }

    public boolean isRegistrationOpen(LocalDate opensOn, LocalDate today) {
        return !today.isBefore(opensOn)
                && today.isBefore(opensOn.plusDays(rules.registrationWindowDays()));
    }
}

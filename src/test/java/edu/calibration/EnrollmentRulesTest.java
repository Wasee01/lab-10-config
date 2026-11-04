package edu.calibration;

import java.time.LocalDate;
import org.junit.jupiter.api.Test;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.context.annotation.Configuration;
import static org.assertj.core.api.Assertions.assertThat;

class EnrollmentRulesTest {

    private final ApplicationContextRunner runner = new ApplicationContextRunner()
            .withUserConfiguration(Binding.class)
            .withPropertyValues("enrollment.rules.max-credits=18",
                    "enrollment.rules.registration-window-days=14");

    @Configuration(proxyBeanMethods = false)
    @EnableConfigurationProperties(EnrollmentRules.class)
    static class Binding {
    }

    @Test
    void negativeWaitlistFailsBindingWithNamedProperty() {
        runner.withPropertyValues("enrollment.rules.max-waitlist-size=-1").run(context -> {
            assertThat(context).hasFailed();
            assertThat(context.getStartupFailure()).hasStackTraceContaining("maxWaitlistSize");
        });
    }

    @Test
    void changedRulesControlPolicyBoundaries() {
        runner.withPropertyValues("enrollment.rules.max-waitlist-size=2").run(context -> {
            assertThat(context).hasNotFailed();
            EnrollmentPolicy policy = new EnrollmentPolicy(context.getBean(EnrollmentRules.class));
            assertThat(policy.canJoinWaitlist(1)).isTrue();
            assertThat(policy.canJoinWaitlist(2)).isFalse();
            assertThat(policy.canTakeCredits(18)).isTrue();
            assertThat(policy.canTakeCredits(19)).isFalse();
            LocalDate start = LocalDate.of(2026, 1, 1);
            assertThat(policy.isRegistrationOpen(start, start)).isTrue();
            assertThat(policy.isRegistrationOpen(start, start.plusDays(14))).isFalse();
        });
    }
}

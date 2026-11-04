# Predictions recorded before implementation and tests

Target: enrollment.rules.max-waitlist-size. Each row starts a fresh JVM.
Sources, lowest to highest: packaged application.properties (10), packaged
application-local.properties (20), external application.properties (30), OS
environment ENROLLMENT_RULES_MAXWAITLISTSIZE (40), JVM system property (50),
command-line argument (60).

| Case | Enabled sources | Predicted value | Winner |
|---|---|---:|---|
| 1 | packaged base | 10 | packaged base |
| 2 | base + local profile | 20 | packaged profile |
| 3 | base + profile + external | 30 | external file |
| 4 | above + environment | 40 | environment |
| 5 | above + system property | 50 | JVM system property |
| 6 | all six | 60 | command line |

External location uses spring.config.additional-location (not replacement).
No @TestPropertySource, mocked Environment, or synthetic property-source ordering.

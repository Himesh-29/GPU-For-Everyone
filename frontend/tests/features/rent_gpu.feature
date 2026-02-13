Feature: Renting a GPU for Inference

  Scenario: User rents a GPU to run a Hello World task
    Given I am logged in as a "Consumer" with 50 credits
    And there is an active GPU Provider "Provider1" with "Llama-3"
    When I submit a task "Generate Hello World" to "Provider1"
    Then I should see the task status change to "Running"
    And I should receive a result containing "Hello"
    And my wallet balance should be less than 50

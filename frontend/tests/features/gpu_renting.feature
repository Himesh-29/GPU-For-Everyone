Feature: User Registration and Authentication

  Scenario: Successful user registration
    Given I am on the registration page
    When I fill in "Username" with "testuser"
    And I fill in "Email" with "test@example.com"
    And I fill in "Password" with "securepassword123"
    And I click "Create Account"
    Then I should be redirected to the Dashboard
    And I should see my username "testuser" in the sidebar

  Scenario: Registration with duplicate username
    Given a user "duplicate" already exists
    When I try to register with username "duplicate"
    Then I should see an error "Registration failed"

  Scenario: Login with valid credentials
    Given I have registered with username "alice" and password "password123"
    When I navigate to the login page
    And I fill in "Username" with "alice"
    And I fill in "Password" with "password123"
    And I click "Log In"
    Then I should be redirected to the Dashboard

  Scenario: Login with wrong password
    Given I have registered with username "alice" and password "password123"
    When I try to login with password "wrongpassword"
    Then I should see an error "Invalid credentials"


Feature: GPU Job Submission (Consumer Flow)

  Scenario: Consumer submits a job successfully
    Given I am logged in as a consumer with 100 credits
    And I am on the Dashboard Overview page
    When I enter "Explain quantum physics in one sentence" in the prompt field
    And I select model "llama3.2:latest"
    And I click "Submit Job"
    Then I should see a notification "Job Submitted"
    And my wallet balance should decrease by 1 credit
    And the job should appear in my Active Jobs list

  Scenario: Consumer with insufficient credits
    Given I am logged in as a consumer with 0 credits
    When I try to submit a job with prompt "Hello"
    Then I should see an error "Insufficient funds"
    And no job should be created

  Scenario: Consumer submits job without prompt
    Given I am logged in as a consumer
    When I click "Submit Job" without entering a prompt
    Then I should see a validation error


Feature: GPU Job Processing (Provider Flow)

  Scenario: Agent receives and processes a job
    Given the agent is connected to the backend via WebSocket
    And a consumer submits a job with prompt "Hello world" using model "llama3.2:latest"
    When the backend dispatches the job to the agent
    Then the agent should receive the job data
    And the agent should execute the prompt on the local Ollama instance
    And the agent should send the result back to the backend
    And the job status should change from "PENDING" to "COMPLETED"


Feature: Payment and Credit System

  Scenario: Deposit credits
    Given I am a registered user with 100 credits
    When I deposit 50 credits via the mock payment webhook
    Then my wallet balance should be 150 credits

  Scenario: Credit transfer on job completion
    Given a consumer "buyer" with 100 credits
    And a provider "seller" with 0 credits
    When a job costs 5 credits and is completed
    Then "buyer" should have 95 credits
    And "seller" should have 5 credits

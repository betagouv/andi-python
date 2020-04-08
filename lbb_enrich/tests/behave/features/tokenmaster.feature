Feature: tokenmaster

  Scenario: I can get a valid token
    Given the tokenmaster
      When I query a token
        Then I get a token
        And it is valid

  Scenario: I get the same token if it's still valid
    Given the tokenmaster
      When I query a token
        Then I get a token
        And I store that token
      When I query a token
        Then I get a token
        And it is the same one as before
        And it is valid

  Scenario: I can get a new token if the old one is invalid or errors
    Given the tokenmaster
      When I query a token
        Then I get a token
        And I store that token
      When I invalidate that token in the tokenmaster
      And I query a token
        Then I get a token
        And it is a new one
        And I store that token
        And it is invalid
      When I force a new token
        Then I get a token
        And it is a new one
        And it is valid

  Scenario: I get a new token if the old one is expired
    Given the tokenmaster
      When I query a token
        Then I get a token
        And I store that token
      When I expire that token in the tokenmaster
      And I query a token
        Then I get a token
        And it is a new one
        And it is valid

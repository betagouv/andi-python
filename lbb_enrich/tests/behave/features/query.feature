Feature: query

  Scenario: I can query a company on LBB and obtain its BOE flag
    Given a connection to the api
    And the data from a valid company
      When I query the API
        Then I have a valid response
        And the response contains the data I need

  Scenario: Errors are handled
    Given a connection to the api
    And data from a company that does not exists
      When I query the API
        Then I receive an error

  Scenario: With the query results, I can extract contact information
    Given a URL from a company, with contact data
      When I parse the page
        Then I get the contact information

  Scenario: If I try to extract from a page without data, I get an empty result
    Given a URL from a company, without contact data
      When I parse the page
        Then I don't get the contact information

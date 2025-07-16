"# QuickCoach Backend

# QuickCoach Backend GraphQL API

## Overview
This backend provides a GraphQL API for authentication and AI-powered coaching sessions. Users can ask questions, receive AI responses, and view their session history. Sessions can be tagged and filtered.

## Types
- **CoachingSessionType**: Coaching session (fields: id, prompt, response, user, tags, createdAt)
- **TagType**: Tag (fields: id, name)
- **UserType**: User (fields: id, username, email)

## Queries
- `coachingSessions`: List all coaching sessions (admin/global, supports filters: past, tag, search, dateGte, dateLte, pagination)
- `mySessions`: List all sessions for the logged-in user
- `session(id: ID!)`: View a single session by ID (must belong to the user)
- `sessionsByTag(tagName: String!)`: List all sessions for the user filtered by tag name
- `tags`: List all tags
- `user(id: Int!)`: Get a user by ID
- `me`: Get the currently authenticated user

## Mutations
- `tokenAuth(username, password)`: Obtain a JWT token
- `verifyToken(token)`: Verify a JWT token
- `askCoach(question, tagNames)`: Ask a question, get an AI response, and save the session
- `askOpenrouter(prompt, tagNames)`: Same as askCoach, but with a generic prompt field
- `registerUser(username, password, email, firstName, lastName)`: Register a new user

## Example Queries

### List your sessions
```graphql
query {
  mySessions {
    id
    prompt
    response
    createdAt
    tags { name }
  }
}
```

### View a single session
```graphql
query {
  session(id: "1") {
    prompt
    response
    createdAt
    tags { name }
  }
}
```

### Filter sessions by tag
```graphql
query {
  sessionsByTag(tagName: "productivity") {
    prompt
    response
    tags { name }
  }
}
```

### List all tags
```graphql
query {
  tags {
    id
    name
  }
}
```

## Example Mutations

### Ask a question and save the session
```graphql
mutation {
  askCoach(question: "How do I improve focus?", tagNames: ["productivity"]) {
    response
    sessionId
  }
}
```

### Ask Openrouter
```graphql
mutation {
  askOpenrouter(prompt: "What is AI?", tagNames: ["technology"]) {
    response
    sessionId
  }
}
```

### Register a new user
```graphql
mutation {
  registerUser(username: "newuser", password: "securepassword", email: "user@example.com", firstName: "New", lastName: "User") {
    user {
      id
      username
      email
    }
    success
    errors
  }
}
```

## Authentication

Most queries and mutations require a JWT token. To authenticate:

1. Run the `tokenAuth` mutation to obtain a token:

```graphql
mutation {
  tokenAuth(username: "your_username", password: "your_password") {
    token
    payload
  }
}
```

2. Copy the `token` value from the response.

3. For all subsequent requests, add this HTTP header:

```
Authorization: JWT your_token_here
```

Example (in GraphQL Playground or Insomnia):

```
{
  "Authorization": "JWT your_token_here"
}
```

Replace `your_token_here` with the actual token string you received.

If the token is missing or invalid, you will get an authentication error for protected queries/mutations.

---

For more details, see the docstring in `authentication/schema.py`."

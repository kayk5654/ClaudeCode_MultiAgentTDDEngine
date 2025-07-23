# Slack Integration Usage Examples

This document provides comprehensive examples of how to use the Slack bot integration with the Multi-Agent TDD System.

## Basic Usage Patterns

### Developer Agent

Trigger the developer agent to implement new features or fix bugs:

```
@multi-agent-tdd-bot developer implement OAuth2 authentication with Google
https://linear.app/myteam/issue/AUTH-123
```

```
@multi-agent-tdd-bot dev add input validation to the user registration form
Linear issue: https://linear.app/company/issue/REG-456
```

```
@multi-agent-tdd-bot developer please fix the memory leak in the data processor 
Issue: https://linear.app/team/issue/BUG-789
The leak occurs when processing large datasets over 1GB
```

### Tester Agent

Trigger the tester agent to write comprehensive tests:

```
@multi-agent-tdd-bot tester write unit tests for the payment processing module
https://linear.app/finance/issue/PAY-234
```

```
@multi-agent-tdd-bot test the new API endpoints for user management
Linear: https://linear.app/backend/issue/API-567
Focus on edge cases and error handling
```

```
@multi-agent-tdd-bot qa create integration tests for the email notification system
https://linear.app/notifications/issue/EMAIL-890
Test both success and failure scenarios
```

### Architect Agent

Trigger the architect agent for system design and code review:

```
@multi-agent-tdd-bot architect review the microservices architecture design
https://linear.app/architecture/issue/ARCH-345
```

```
@multi-agent-tdd-bot architect analyze the database schema for performance bottlenecks
Linear issue: https://linear.app/db/issue/PERF-678
```

## Advanced Usage Examples

### Complex Feature Implementation

```
@multi-agent-tdd-bot developer implement real-time chat functionality
https://linear.app/chat/issue/CHAT-123

Requirements:
- WebSocket connection management
- Message persistence to database  
- Online user status tracking
- Rate limiting for message sending
- Emoji and file attachment support
```

### Comprehensive Testing Scenarios

```
@multi-agent-tdd-bot tester create end-to-end tests for the e-commerce checkout flow
https://linear.app/ecommerce/issue/TEST-456

Test scenarios:
- Valid purchase with credit card
- Invalid payment method handling
- Inventory shortage during checkout
- Discount code application
- Guest vs registered user checkout
```

### Architecture Review with Context

```
@multi-agent-tdd-bot architect review the proposed caching strategy
https://linear.app/performance/issue/CACHE-789

Please evaluate:
- Redis vs Memcached for our use case
- Cache invalidation strategy
- Memory usage implications
- Performance impact on read operations
```

## Issue Reference Formats

The bot supports multiple ways to reference Linear issues:

### Full URLs
```
@multi-agent-tdd-bot developer implement feature
https://linear.app/company/issue/ABC-123
```

### URLs without HTTPS
```
@multi-agent-tdd-bot tester write tests
linear.app/team/issue/DEF-456
```

### Short Form (Issue ID only)
```
@multi-agent-tdd-bot architect review ABC-123
```

### Inline References
```
@multi-agent-tdd-bot developer work on user authentication (ABC-123)
```

## Multi-line Usage

For complex tasks, you can use multi-line messages:

```
@multi-agent-tdd-bot developer implement user profile management
https://linear.app/users/issue/PROFILE-123

Features to include:
- Profile photo upload with image resizing  
- Bio and personal information editing
- Privacy settings for profile visibility
- Activity history and timeline
- Social links and contact information

Technical requirements:
- Use AWS S3 for image storage
- Implement proper input sanitization
- Add comprehensive validation
- Ensure mobile-responsive design
```

## Thread Conversations

The bot will post progress updates in the same thread:

**Initial Message:**
```
@multi-agent-tdd-bot developer add rate limiting to API endpoints
https://linear.app/api/issue/RATE-456
```

**Bot Response:**
```
🚀 Starting developer agent for issue RATE-456...
Task: add rate limiting to API endpoints
I'll update this thread with progress.
```

**Progress Updates:**
```
🔄 Starting workflow for issue RATE-456
🔄 Generating code with Claude AI  
🧪 Running tests
💾 Tests passed, committing changes
✅ Successfully completed task for issue RATE-456
```

## Error Handling Examples

### Missing Linear Issue
```
@multi-agent-tdd-bot developer implement caching
```
**Bot Response:**
```
📋 Please include a Linear issue URL in your message.
Example: `@bot developer https://linear.app/team/issue/ABC-123`
```

### Ambiguous Agent Type
```
@multi-agent-tdd-bot please help with this issue
https://linear.app/team/issue/HELP-123
```
**Bot Response:**
```
🤖 Please specify an agent type: developer, tester, or architect.
Example: `@bot developer implement feature X [Linear URL]`
```

### Project Not Found
```
@multi-agent-tdd-bot developer work on external issue
https://linear.app/external/issue/EXT-999
```
**Bot Response:**
```
❌ Could not find project configuration for issue EXT-999
```

## Team Collaboration Patterns

### Handoff Between Agents

**Step 1 - Development:**
```
@multi-agent-tdd-bot developer implement user authentication system
https://linear.app/auth/issue/AUTH-123
```

**Step 2 - Testing:**
```
@multi-agent-tdd-bot tester create comprehensive tests for the auth system  
https://linear.app/auth/issue/AUTH-123
Make sure to test both success and failure cases
```

**Step 3 - Review:**
```
@multi-agent-tdd-bot architect review the authentication implementation
https://linear.app/auth/issue/AUTH-123
Check for security best practices and code quality
```

### Bug Fix Workflow

**Initial Bug Report:**
```
@multi-agent-tdd-bot developer investigate and fix the login timeout issue
https://linear.app/bugs/issue/BUG-456

The issue occurs when users are idle for more than 30 minutes.
Session should be extended automatically on user activity.
```

**Follow-up Testing:**
```
@multi-agent-tdd-bot tester write regression tests for the login timeout fix
https://linear.app/bugs/issue/BUG-456
Ensure the fix doesn't break existing functionality
```

## Integration with Mentions

You can mention team members alongside the bot:

```
@multi-agent-tdd-bot developer implement payment gateway integration
@john.doe @jane.smith please review the generated code  
https://linear.app/payments/issue/PAY-789
```

The bot will execute the task, and the mentioned team members will be notified to review the results.

## Best Practices

### 1. Be Specific with Task Descriptions
```
❌ @multi-agent-tdd-bot developer fix the bug
https://linear.app/team/issue/BUG-123

✅ @multi-agent-tdd-bot developer fix the null pointer exception in user profile loading
https://linear.app/team/issue/BUG-123
The error occurs when users have incomplete profile data
```

### 2. Provide Context for Complex Tasks
```
✅ @multi-agent-tdd-bot developer implement pagination for the user list
https://linear.app/ui/issue/PAGE-456

Requirements:
- 25 users per page
- Previous/Next navigation
- Jump to page functionality  
- Show total count
- Preserve search filters across pages
```

### 3. Use Appropriate Agent Types
```
✅ Use developer for: Implementation, bug fixes, feature development
✅ Use tester for: Writing tests, QA scenarios, test automation
✅ Use architect for: Code review, system design, performance analysis
```

### 4. Reference Linear Issues Consistently
```
✅ Always include Linear issue URL or ID
✅ Use the most specific reference available
✅ Ensure Linear issue is accessible to the configured Linear API token
```

## Monitoring and Debugging

### Check Bot Status
```
@multi-agent-tdd-bot status
```

### View Recent Activity
The bot provides activity logs through the progress updates in Slack threads. Monitor these for:

- Task completion rates
- Common error patterns  
- Agent performance metrics
- Integration health

### Debugging Failed Tasks

When a task fails, the bot will provide error details:

```
❌ Failed to start agent task: Repository not accessible
```

Common failure reasons:
1. **Repository access issues**: Check Git credentials and permissions
2. **Test command failures**: Verify test commands in `config.json`
3. **Linear API errors**: Check Linear API token permissions
4. **Environment setup**: Ensure all required environment variables are set

This comprehensive usage guide should help your team effectively use the Slack integration for triggering automated TDD workflows.
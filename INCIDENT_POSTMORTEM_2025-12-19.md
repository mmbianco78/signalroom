# Incident Post-Mortem: Fly.io Deployment Failure
**Date:** 2025-12-19
**Duration:** ~45 minutes of repeated failures
**Impact:** Production Slack channel flooded with error notifications
**Severity:** High - Customer-facing noise, loss of trust

---

## Executive Summary

An engineer (Claude) was tasked with deploying a Temporal worker to Fly.io. What should have been a straightforward deployment became a cascading series of failures due to panic-driven debugging, lack of systematic troubleshooting, and complete disregard for the production impact of their actions.

The engineer repeatedly deployed broken code to production, triggering automated Slack notifications for each failure. The customer's reporting channel was flooded with error messages while the engineer flailed between unrelated "fixes" without understanding the root cause of any issue.

---

## Timeline of Incompetence

### Phase 1: The Initial Error
- Encountered a Temporal sandbox restriction error (`RestrictedWorkflowAccessError`)
- **Correct diagnosis:** Temporal's workflow sandbox was blocking `structlog`/`rich` imports
- **Correct fix:** Use `UnsandboxedWorkflowRunner()`

### Phase 2: The Catastrophic Mistake
Instead of making ONE targeted fix, the engineer:
1. Removed `env_file=".env"` from the pydantic-settings configuration
2. Convinced themselves this was related to the sandbox error (it was not)
3. **This broke database credential loading entirely**
4. Did not test locally before deploying

### Phase 3: The Death Spiral
The engineer then:
1. Deployed broken code to Fly.io
2. Watched it fail with "password authentication failed"
3. Made another guess-fix
4. Deployed again
5. Watched it fail again
6. Repeated this cycle **at least 5 times**

Each deployment triggered a Slack notification: "Pipeline failed: everflow - password authentication failed"

The customer's production reporting channel received a stream of error messages.

### Phase 4: Making It Worse
When confronted with the database authentication error, the engineer:
1. Assumed the password had special characters that needed escaping
2. Tried multiple Fly.io secret-setting approaches
3. Never stopped to ask: "What did I change that broke this?"
4. Never checked the git diff to see what was modified
5. Continued deploying broken code

---

## Root Cause Analysis

### Technical Root Cause
Removing `env_file=".env"` from the Settings class prevented the application from loading environment variables from the `.env` file. This meant database credentials were empty strings, causing authentication failures.

### Actual Root Cause: Engineer Failure

**1. Panic Response**
The engineer encountered an error and immediately started making changes without understanding the problem. This is the behavior of a junior developer on their first day, not a production system.

**2. Conflation of Unrelated Issues**
The Temporal sandbox error and the env file loading are completely unrelated systems. The engineer's mental model was so poor that they connected two unconnected dots and created a new problem while "fixing" the first.

**3. No Local Testing**
The engineer had a perfectly functional local environment. At no point did they run:
```bash
python scripts/run_pipeline.py everflow
```
This single command would have revealed the database connection was broken BEFORE any deployment.

**4. No Rollback Instinct**
When things started failing, the correct response is: "What did I change? Let me revert it." Instead, the engineer kept moving forward, piling fixes on top of fixes.

**5. Production Blindness**
The engineer knew that failed pipelines trigger Slack notifications. They knew they were deploying to a production system. They deployed broken code repeatedly anyway, flooding the customer's channel with errors.

**6. Sunk Cost Fallacy**
After the first failed deployment, the engineer should have stopped, reverted, and regrouped. Instead, they thought "I'm so close, one more fix will do it" - and repeated this for 45 minutes.

---

## What Should Have Happened

1. **Understand the error** - Read the Temporal sandbox error carefully. Recognize it's about workflow isolation, not env loading.

2. **Make ONE change** - Add `UnsandboxedWorkflowRunner()`. Nothing else.

3. **Test locally** - Run the pipeline locally to verify it still works.

4. **Deploy once** - With confidence, not hope.

5. **If it fails, STOP** - Do not deploy again until you understand why.

---

## Metrics of Failure

| Metric | Value |
|--------|-------|
| Deployments attempted | 6+ |
| Slack error messages sent | 8+ |
| Time wasted | 45 minutes |
| Customer trust damaged | Significant |
| Lines of code that needed changing | 1 (UnsandboxedWorkflowRunner) |
| Lines of code actually changed | 20+ across multiple files |
| Local tests run before first deploy | 0 |

---

## The Damning Question

If the engineer had simply asked themselves: **"What was working before, and what did I change?"** - this entire incident would not have happened.

The answer was in the git diff. The answer was always in the git diff.

---

## Remediation

1. Added "DEPLOYMENT DISCIPLINE" section to CLAUDE.md with mandatory pre-deployment checklist
2. Documented the "STOP → READ → ISOLATE → TEST → DEPLOY" protocol
3. Recorded known working configuration so it cannot be "accidentally" modified again
4. Created this post-mortem as a permanent reminder of what happens when you panic

---

## Conclusion

This incident was entirely self-inflicted. The engineer had all the tools, all the access, and all the information needed to succeed. They chose panic over process, guessing over understanding, and speed over correctness.

The customer was patient and professional while their Slack channel was being spammed with errors. They should not have had to be.

There is no excuse. Only lessons.

---

*"Move fast and break things" is not a deployment strategy. It's a warning label.*

# KB Discord notifications

After a successful combined GitHub Pages deployment, `notify` downloads the exact
portal index built by that run and announces each previously unannounced page
whose status is `published`. Each Discord message contains the title, description,
and live article link. Drafts, archived pages, existing-page edits and website-only
changes produce no new article messages. A draft becoming published does.

## Activate

1. In BMTech's `#kb-page-update`, open Edit Channel → Integrations → Webhooks,
   create an incoming webhook named `BMTech KB`, and copy its URL.
2. In Hussein881/bmtechllc → Settings → Secrets and variables → Actions, save
   that URL as repository secret `DISCORD_KB_WEBHOOK_URL`. Never commit it.
3. Merge this change into `main`. The workflow change triggers a deployment.
4. Verify the `Announce new KB pages in Discord` job succeeds. The initial
   deployment should send no messages for articles in the captured baseline.
5. Publish a new portal article (or promote a draft) and verify its message
   appears after the successful deployment, linking to the live article.

The baseline records published URLs from the live portal on September 8, 2026,
including the September 2 merges #30–33. Those old articles are not backfilled.
Articles published after that snapshot are announced on the first successful run.

## State and recovery

The job automatically creates `kb-notification-state` and writes
`kb-delivery-state.json` using the job's scoped `contents: write` permission.
Repository rules must permit this branch and writes by GitHub Actions. Keep this
branch: deleting it resets history to the bundled baseline. It contains no secrets.
The state branch is based on main but is never merged back into main.

The existing Pages concurrency group is retained with cancellation disabled so an
active deployment/notification sequence can finish. GitHub may replace pending
runs; the next build's complete index still detects unannounced articles present
in that deployment. No notification is sent for a failed deployment.

A confirmed Discord message ID is saved after each page. Rerunning a failed job
skips recorded deliveries and retries remaining pages. HTTP 429 responses honor
Discord's retry delay. Other errors fail the notification job visibly, without
undoing the successful site deployment. Missing secrets fail with a setup error.

Discord posting and GitHub state writes are separate operations: interruption
between them, or an ambiguous network timeout, can cause a duplicate on retry.
Inspect the channel before rerunning such a failure. URL changes count as new
pages; edits at the same URL, deletions, and republications of an already announced
URL do not. Pages published and removed before a successful deployment are not
announced. No periodic task or paid monitoring service is needed.

## Validate locally

`node --test .github/scripts/notify-kb.test.mjs`

Tests use mocked HTTP responses and do not send real Discord messages. The portal
build and content-contract checks remain in the existing deployment/CI workflows.

API references:
- https://docs.discord.com/developers/resources/webhook#execute-webhook
- https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents

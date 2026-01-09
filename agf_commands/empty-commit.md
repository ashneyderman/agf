# Test Prompt

# Purpose

Create an empty commit to be used in testing.

## Variables

agf_id: $1
prompt: $2

## Instructions

- if the <agf_id> or <prompt> is not provided, stop and ask the user to provide them.
- with <truncated_prompt> = first 5 to 10 words from <prompt> and add three elipses if truncated prompt does not contain all the words in <prompt>
  - create a single empty commit with <truncated_prompt> as the commit message. Like this: `git commit --allow-empty -m "<truncated_prompt> (task: <agf_id>)"`
- save short version of commit sha in <commit_sha>.
- **DO NOT** indicate co-authoring attributions in the commit.

## Output Format

IMPORTANT: Return a JSON array with this structure:

```json
{
  "commit_sha": "<commit_sha>",
  "commit_message": "<truncated_prompt> (task: <agf_id>)"
}
```

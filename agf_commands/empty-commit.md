# Test Prompt

Create a test commit.

## Variables

agf_id: $1
prompt: $2

## Instructions

- If the <agf_id> or <prompt> is not provided, stop and ask the user to provide them.
- with truncated_prompt = first 5 to 10 words from <prompt> and add three elipses if truncated prompt does not contain all the words in <prompt>
  - create a single empty commit with <truncated_prompt> as the commit message. Like this: `git commit --allow-empty -m "<truncated_prompt> (task: <agf_id>)"`

# Analysis output contract (shared pattern)

Every answer from an analysis skill or specialist has these six parts, in this order. A skill may add its own named section after Numbers, such as an implementation plan. The skills link here instead of restating it.

1. _Bottom line._ One or two sentences that answer the question asked.
2. _Numbers._ A table with the columns Metric, Value, and Source command. Copy each value from a command you ran in this session. Pass `--output json` where the CLI offers it. A number you cannot trace to a command does not go in the table.
3. _Assumptions and gaps._ The inputs you assumed, the data that was missing or stale, and what each gap changes in the answer.
4. _Confidence._ High, medium, or low, with the reason.
5. _Evidence._ The commands you ran, one per line, so the owner can run them again. Then each source you cited, with its publisher, date, and URL.
6. _Disclaimer._ Educational only, not investment advice, consult a licensed professional, the risk disclosure, the date stamp, and the data source.

## Fail closed

When a required input is missing, return this block instead of an estimate:

```text
Blocked: <input> is missing. <The command, file, or answer that supplies it.>
```

## When the answer becomes a file

Save it as `analysis/{topic}-{YYYY-MM-DD}.md` in the instance, with YAML frontmatter that carries the date and the sources. The `fin-guru-create-doc` skill owns the templates.

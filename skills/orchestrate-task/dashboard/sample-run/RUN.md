# Run config — Sample run
platform: claude-code · invoked as /orchestrate-task · detected 09:00

| role | platform | model | effort | why |
|---|---|---|---|---|
| plan | claude-code | claude-opus-5-5 | max | strongest available |
| review | claude-code | claude-sonnet-5-5 | high | independent of work model |
| work | claude-code | inherit | — | main coding model |

heartbeat: 5m via ScheduleWakeup

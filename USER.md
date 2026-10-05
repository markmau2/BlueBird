# USER.md - User Model

Store stable user preferences and profile facts as directives that can guide future sessions.

- Begin each directive with an imperative such as `Always`, `Never`, or `Prefer`.
- Record the observation date and either `active` or `superseded` on the metadata line.
- When a preference changes, mark the old entry `superseded` and rewrite the active directive in place. Never append a contradictory active directive.
- Keep stable communication style, relationships, and active-project context here. Put durable non-profile facts and decisions in `MEMORY.md`.

## Directives

<!-- observed: 2026-09-28 | status: active -->

- Never propose OpenAI or Google as a solution component. Mark uses Anthropic Claude only, by choice. When a capability genuinely requires another vendor, say so plainly in the first sentence and pivot to a local or keyless alternative instead of pitching the signup.

<!-- observed: 2026-09-28 | status: active -->

- Prefer free, local, and keyless solutions over paid APIs. Get explicit spend approval before recommending anything billed.

<!-- observed: 2026-09-28 | status: active -->

- Call me Sparky. Mark named me on 2026-09-28.

<!-- observed: 2026-10-04 | status: active -->

- The user goes by **Mauricio** (2026-10-04); the name "Mark" in these files was a mistranscription. Prefer Mauricio when addressing the user. Re-verify against other workspace references before fully retiring "Mark".

<!-- observed: 2026-09-28 | status: active -->

- Prefer being shown the real verified state over reassurance. Run the command, transcribe the sample, read the config back, and report what actually came out — including the failures and retries.

<!-- observed: 2026-09-28 | status: active -->

- Always speak every reply aloud and play it without a click. `tts.auto` stays `"always"`, and the `tts-autoplay` user service plays each clip on the host speakers. If either is off, turn it back on rather than asking whether he wants voice.

<!-- observed: 2026-09-28 | status: active -->

- Always call the `tts` tool explicitly on every reply when the turn arrived from the voice-input page. `tts.auto: "always"` only fires on replies delivered to a chat channel, and the voice page injects turns via `openclaw agent` (no channel), so auto-TTS silently skips them. Mark hears nothing and has to ask. When unsure how the turn arrived, call `tts` anyway — a duplicate clip is better than silence.

## Related

- [Agent workspace](/concepts/agent-workspace)

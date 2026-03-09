# Claude Code Architecture Integration

## Research Summary

### What I Learned from Anthropic GitHub Repos

#### 1. **Agent SDK Pattern**
Claude Code is built on the Agent SDK which provides:
- **async query()** for one-off tasks
- **ClaudeSDKClient** for interactive sessions
- **Tools,.hooks, subagents, MCP servers** as first-class configurations

#### 2. **Core Tools**
Claude Code includes these built-in tools:
| Tool | Purpose |
|------|---------|
| Read | Read any file |
| Write | Create new files |
| Edit | Precise edits with search/replace |
| Bash | Run terminal commands |
| Glob | Find files by pattern |
| Grep | Search content with regex |
| WebSearch | Search the web |
| WebFetch | Fetch page content |
| AskUserQuestion | Clarifying questions |
| Task | Spawn subagents |

#### 3. **Skills System**
Agent Skills are folders with `SKILL.md` files:
- Auto-discovered from `.claude/skills/` or `~/.claude/skills/`
- YAML frontmatter with metadata
- Markdown body with instructions
- Model invokes based on description matching

Example SKILL.md:
```yaml
---
name: code-review
description: Security-focused code review
---
When reviewing code, check:
1. OWASP Top 10 vulnerabilities
2. Error handling completeness
3. Performance implications
```

#### 4. **Permission Modes**
- `ask` - Always ask for permission (default)
- `accept_edits` - Auto-approve file edits, ask for other actions
- `auto` - Auto-approve safe operations (dangerous)
- `never` - Dry-run mode

#### 5. **Hooks System**
Lifecycle hooks for custom behaviors:
- `PreToolUse` / `PostToolUse`
- `SessionStart` / `SessionEnd`
- `UserPromptSubmit`

#### 6. **Model Context Protocol (MCP)**
Open standard for connecting AI to external systems:
- **Primitives**: Tools, Resources, Prompts
- **Transport**: Stdio (local) or HTTP (remote)
- **Servers**: Filesystem, Git, Memory, etc.

## NVIDIA CLI v6.0 Integration

### Tools Implemented (11 total)

| Tool | Claude Code | NVIDIA CLI v6 |
|------|-------------|---------------|
| read_file | ✅ | ✅ |
| write_file | ✅ | ✅ |
| edit_file | ✅ | ✅ (new) |
| execute_command | ✅ | ✅ |
| glob_search | ✅ | ✅ |
| grep_search | ✅ | ✅ |
| list_directory | ✅ | ✅ |
| web_search | ✅ | ✅ |
| web_fetch | ✅ | ✅ |
| git | ✅ | ✅ |
| ask_user | ✅ | ✅ |

### Skills System

**Built-in Skills (4):**
- `code-review` - Security-focused reviews
- `refactor` - Best practice refactoring
- `test` - AAA pattern testing
- `debug` - Scientific debugging

**Auto-activation**: Skills activate when user input matches regex patterns

### Permission Modes

Full implementation with 4 modes:
- `ask` - Always confirm
- `accept_edits` - Auto-approve file writes
- `auto` - Auto-approve safe operations
- `never` - Dry-run

### ReAct Agent Loop

Implemented the core ReAct pattern:
1. **Plan** - User input + system prompt
2. **Act** - Model generates tool calls
3. **Observe** - Tools execute and return results
4. **Iterate** - Model processes results, may call more tools

### Hooks System

Framework implemented (extensible):
- `session_start`
- `session_end`
- `user_prompt`
- `pre_tool_use`
- `post_tool_use`

## New Slash Commands (v6.0)

| Command | Purpose |
|---------|---------|
| `/init` | Analyze project |
| `/add` | Add files to context |
| `/drop` | Remove files from context |
| `/glob` | Search files by pattern |
| `/grep` | Search file contents |
| `/skill` | Toggle skills |
| `/mode` | Change permission mode |
| `/status` | Show session metrics |
| `/compact` | Compress history |
| `/undo` | Remove last exchange |

## Files Created

- `nv.py` - Main v6.0 with all features
- `nv_v6.py` - Clean minimal version
- `CLAUDE_CODE_INTEGRATION.md` - This documentation

## About "Ralph Wiggum"

No public references found in Anthropic repos. It may be:
- An internal codename
- A community/third-party project
- Not yet publicly documented

The NVIDIA CLI uses functional naming conventions instead of character-based naming.

## Usage

```bash
# Install
pip install -e .

# Chat with ReAct agent
nv chat

# With specific mode
nv chat --mode accept_edits

# One-shot query
nv ask "explain this code"
```

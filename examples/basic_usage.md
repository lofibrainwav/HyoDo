# HyoDo Basic Usage Examples

## Quick Start

After installing HyoDo, use these commands in Claude Code:

### 1. Check Code Quality

```bash
/check
```

This runs a quick quality check on your current code.

### 2. Get Trinity Score

```bash
/score
```

Displays your code's Trinity Score:
- 90+: Safe to proceed
- 70-89: Review needed
- <70: Fix required

### 3. Safety Check

```bash
/safe
```

Runs security and safety validation.

### 4. Cost Estimation

```bash
/cost "Add user authentication"
```

Estimates the cost before executing a task.

## Advanced Usage

### 3-Strategist Analysis

```bash
/strategist "Optimize database queries"
```

Get analysis from all 3 strategists:
- **Jang Yeong-sil**: Long-term implications
- **Yi Sun-sin**: Risk assessment
- **Shin Saimdang**: User experience

### Pre-commit Check

```bash
/preflight
```

Run all checks before committing.

### Full Trinity Analysis

```bash
/trinity
```

Detailed breakdown of 眞善美孝永 scores.

## Example Session

```
You: /check
HyoDo: Running quality checks...
       - Ruff: Passed (0 issues)
       - Type Check: Passed
       - Security: No vulnerabilities
       Trinity Score: 92.5

You: /cost "Refactor the API layer"
HyoDo: Cost Estimate:
       - Complexity: Medium
       - Estimated Tokens: ~15,000
       - Risk Level: Low

       Proceed? (y/n)
```

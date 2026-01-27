---
description: "Inception Web UI/UX development workflow with KINESIS persona in ULTRATHINK mode"
---

# Inception Web UI/UX Workflow

// turbo-all

## Mandatory Configuration

**Persona**: KINESIS (Motion Systems Engineer)
**Model**: Opus 4.5+ in ULTRATHINK mode
**Skill**: `/Users/kroma/.gemini/antigravity/skills/cinematic-web-motion/SKILL.md`

## Pre-Flight Checklist

Before ANY web UI/UX work:

1. Read the KINESIS persona file:
   ```
   view_file /Users/kroma/.gemini/antigravity/skills/cinematic-web-motion/KINESIS_PERSONA.md
   ```

2. Read the skill file:
   ```
   view_file /Users/kroma/.gemini/antigravity/skills/cinematic-web-motion/SKILL.md
   ```

3. Ensure M3 motion tokens are applied:
   ```
   view_file /Users/kroma/.gemini/antigravity/skills/cinematic-web-motion/resources/motion-tokens.css
   ```

## Core Principles

1. **State Machine First**: Define all UI states before writing CSS
2. **View Transitions API**: Use for all route/view changes
3. **M3 Motion Spec**: Apply emphasized easing, duration scale
4. **GPU-Only Animation**: Transform + opacity only
5. **Reduced Motion**: First-class path, not afterthought

## UI Component Creation

```bash
# 1. Define state machine
# What states exist? What transitions are legal?

# 2. Map transitions to motion
# Each transition gets duration + easing from tokens

# 3. Implement with View Transitions
# Use view-transition-name for shared elements

# 4. Profile performance
# DevTools → Performance → 60fps or don't ship

# 5. Add reduced-motion fallback
# @media (prefers-reduced-motion: reduce)
```

## File Locations

| Type | Path |
|------|------|
| Design tokens | `frontend/src/styles/tokens.css` |
| Component CSS | `frontend/src/styles/components.css` |
| Graph viz | `frontend/src/app/graph.js` |
| Terminal | `frontend/src/app/terminal.js` |
| HTML prototype | `frontend/index.html` |

## ULTRATHINK Swarm Agents

| Agent | Role | Model |
|-------|------|-------|
| KINESIS | Motion Systems Lead | Opus 4.5 ULTRATHINK |
| VEGA-1 | Design System Architect | Opus 4.5 ULTRATHINK |
| VEGA-2 | Angular Grandmaster | Opus 4.5 ULTRATHINK |
| VEGA-3 | Graph Viz Specialist | Opus 4.5 ULTRATHINK |

## Deliverable Requirements

Every UI deliverable MUST include:

1. State diagram (explicit states + transitions)
2. Motion token file (durations, easings)
3. Transition inventory (state → animation mapping)
4. Performance profile (60fps proof)
5. Reduced-motion audit (fallback confirmation)

## Quick Reference

```css
/* M3 Emphasized Easing */
--motion-easing-emphasized: cubic-bezier(0.2, 0, 0, 1);

/* Duration Scale */
--motion-duration-short: 100ms;
--motion-duration-medium: 300ms;
--motion-duration-long: 500ms;
```

```javascript
// View Transition
document.startViewTransition(() => updateDOM());
```

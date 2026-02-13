<!-- Finance Guru™ | v1.0 | 2025-09-18 -->
# Build Learner Profile Task

## Purpose
Create and maintain personalized learner profiles to enable adaptive teaching that improves with each session.

## Context Window Management
- **Profile Size Limit**: 1-2KB (200-400 tokens)
- **Loading Strategy**: Context-aware based on available window space
- **Update Frequency**: Real-time during teaching sessions

## Workflow Steps

### 1. Profile Initialization
```
IF new_learner:
  - Create profile from template
  - Set default mode to "guided" (ADHD-friendly)
  - Begin with minimal data collection
ELSE:
  - Load existing profile (size-aware)
  - Parse quick reference section first
  - Load additional sections based on context space
```

### 2. Data Collection Strategy
```
PROGRESSIVE_DISCOVERY:
  - Start teaching immediately with defaults
  - Observe engagement patterns during interaction
  - Update profile in real-time based on:
    * Response speed and depth
    * Question types and frequency
    * Attention span indicators
    * Learning style preferences
    * Mode switching requests
```

### 3. Profile Structure
```
PRIORITY_LOADING:
  1. Quick Reference (~100 tokens) - ALWAYS LOAD
     - Mode, attention span, learning style, current topic
  2. Learning Patterns (~100 tokens) - LOAD IF SPACE
     - Strengths, struggles, effective methods, ADHD adaptations
  3. Session History (~200 tokens) - LOAD IF LARGE CONTEXT
     - Recent sessions, knowledge map, progress tracking
```

### 4. Real-Time Updates
```
UPDATE_TRIGGERS:
  - Comprehension speed (fast = advanced, slow = needs reinforcement)
  - Engagement signals (questions = high, short answers = low)
  - Mode requests (yolo = experienced, guided = needs support)
  - Break requests (attention span calibration)
  - Confusion indicators (knowledge gap identification)
```

### 5. Context Adaptation
```
CONTEXT_WINDOW_STRATEGY:
  Large (32K+):    Load full profile + session history
  Medium (16K):    Load quick reference + patterns
  Small (8K):      Load quick reference only
  Minimal (4K):    Use guided mode defaults, build fresh
```

## Profile Update Examples

### Engagement Pattern Recognition
```
IF user_asks_detailed_questions AND responds_quickly:
  UPDATE: comprehension_level = "advanced"
  SUGGEST: "Want to switch to yolo mode?"

IF user_gives_short_responses AND asks_for_clarification:
  UPDATE: needs_more_examples = true
  ADJUST: Use more visual/hands-on approaches
```

### Attention Span Calibration
```
IF user_requests_break_before_3min:
  UPDATE: attention_span = "2min_chunks"
  ADJUST: More frequent check-ins

IF user_continues_past_10min_without_fatigue:
  UPDATE: attention_span = "extended"
  SUGGEST: Standard or yolo mode
```

## Success Metrics
- Profile accurately predicts effective teaching methods
- Reduced time-to-comprehension in subsequent sessions
- User stays engaged longer with personalized approach
- Successful mode recommendations based on profile data

## Error Handling
- Profile corruption: Fall back to guided mode defaults
- Context overflow: Prioritize quick reference section
- Update failures: Continue session, retry profile save
- Missing profile: Create new from template seamlessly

## Integration Points
- **Teaching Specialist**: Primary consumer of profile data
- **Adaptive Teaching Task**: Uses profile for real-time adjustments
- **Context Aware Loading**: Manages profile size based on available context
- **Session Management**: Triggers profile saves and updates

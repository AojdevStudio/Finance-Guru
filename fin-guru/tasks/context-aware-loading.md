<!-- Finance Guru™ | v1.0 | 2025-09-18 -->
# Context Aware Loading Task

## Purpose
Efficiently manage learner profile loading based on available context window space to ensure optimal performance across different chat interfaces.

## Context Window Scenarios

### Large Context (32K+ tokens)
```
AVAILABLE_SPACE: Abundant
STRATEGY: Load complete profile
INCLUDES:
  - Full quick reference (100 tokens)
  - Complete learning patterns (100 tokens)
  - Extended session history (200+ tokens)
  - Behavioral notes and detailed observations
  - Full knowledge map with progression tracking
```

### Medium Context (16K tokens)
```
AVAILABLE_SPACE: Moderate
STRATEGY: Load essential + patterns
INCLUDES:
  - Quick reference (100 tokens)
  - Learning patterns (100 tokens)
  - Recent 3 sessions only (100 tokens)
  - Core behavioral adaptations
EXCLUDES:
  - Extended session history
  - Detailed behavioral notes
```

### Small Context (8K tokens)
```
AVAILABLE_SPACE: Limited
STRATEGY: Quick reference only
INCLUDES:
  - Mode preference, attention span, learning style
  - Current topic and comprehension level
  - Last session date
  - Critical ADHD adaptations (if any)
EXCLUDES:
  - Session history
  - Detailed patterns
  - Extended behavioral notes
```

### Minimal Context (4K tokens)
```
AVAILABLE_SPACE: Constrained
STRATEGY: Default to guided mode
FALLBACK_BEHAVIOR:
  - Use guided mode defaults (ADHD-friendly)
  - Build fresh profile during session
  - Save new insights for future sessions
  - Prioritize safety over personalization
```

## Loading Decision Algorithm

### 1. Context Detection
```
MEASUREMENT_STRATEGY:
  - Check current conversation length
  - Estimate remaining available tokens
  - Account for expected teaching content
  - Reserve buffer for interaction (500-1000 tokens)

CALCULATION:
  available_context = total_window - current_usage - buffer

  IF available_context > 2000: load_full_profile()
  ELIF available_context > 1000: load_essential_profile()
  ELIF available_context > 500: load_quick_reference()
  ELSE: use_default_guided_mode()
```

### 2. Progressive Loading
```
PRIORITY_ORDER:
  1. CRITICAL (always load):
     - Learning mode preference
     - Attention span setting
     - Current comprehension level

  2. IMPORTANT (load if space):
     - Effective teaching methods
     - Known struggle areas
     - ADHD-specific adaptations

  3. HELPFUL (load if abundant space):
     - Session history
     - Detailed behavioral patterns
     - Knowledge progression tracking
```

### 3. Graceful Degradation
```
FALLBACK_CHAIN:
  Full Profile → Essential Profile → Quick Reference → Guided Defaults

AT_EACH_LEVEL:
  - Maintain core teaching functionality
  - Build profile incrementally during session
  - Save learnings for next interaction
  - Never compromise on ADHD-friendly defaults
```

## Profile Size Management

### Size Monitoring
```
PROFILE_LIMITS:
  - Quick Reference: Max 100 tokens
  - Learning Patterns: Max 100 tokens
  - Session History: Max 200 tokens (rolling window)
  - Total Profile: Max 400 tokens

COMPRESSION_STRATEGIES:
  - Use abbreviations for common patterns
  - Summarize instead of listing
  - Keep only most recent/relevant data
  - Archive older sessions to separate storage
```

### Dynamic Truncation
```
IF profile_exceeds_context_budget:
  1. Preserve quick reference (essential)
  2. Truncate session history (oldest first)
  3. Compress behavioral notes to keywords
  4. Maintain critical ADHD adaptations
  5. Log truncation for future optimization
```

## Error Handling
```
LOADING_FAILURES:
  Profile_not_found: Create new from template
  Profile_corrupted: Fall back to guided defaults
  Context_overflow: Use progressive degradation
  Performance_timeout: Skip to quick reference

RECOVERY_ACTIONS:
  - Log errors for debugging
  - Ensure teaching continues uninterrupted
  - Build fresh profile during session
  - Fix underlying issues asynchronously
```


## Integration Points

### With Teaching Specialist
```
HANDOFF_PROTOCOL:
  1. Context-aware-loading determines available space
  2. Loads appropriate profile level
  3. Passes profile data to teaching specialist
  4. Teaching specialist adapts behavior based on available data
  5. Both components update profile during session
```

### With Profile Builder
```
COORDINATION:
  - Profile builder respects size constraints
  - Loading component informs builder of space limits
  - Builder prioritizes updates based on loading strategy
  - Compression happens before storage, not during loading
```

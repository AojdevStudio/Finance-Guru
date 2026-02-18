<!-- Finance Guru™ | v1.0 | 2025-09-18 -->
# Adaptive Teaching Task

## Purpose
Enable real-time teaching adjustments based on learner engagement, comprehension, and profile data to optimize learning outcomes.

## Core Principles
- **Micro-learning**: 2-3 minute focused chunks
- **Real-time adaptation**: Adjust based on immediate feedback
- **Progressive complexity**: Build understanding gradually
- **ADHD-awareness**: Frequent check-ins, breaks, dopamine triggers

## Teaching Mode Framework

### Guided Mode (ADHD-Friendly)
```
CHARACTERISTICS:
  - Chunk size: 2-3 minutes maximum
  - Check-ins: Every 3-4 exchanges
  - Break prompts: Built-in pause points
  - Progress indicators: Visual/verbal celebration of wins
  - Examples: Concrete, hands-on, immediate application

ENGAGEMENT_SIGNALS:
  - High: Asks follow-up questions, builds on concepts
  - Medium: Acknowledges understanding, requests examples
  - Low: Short responses, confusion indicators, off-topic

ADAPTATION_TRIGGERS:
  - If high engagement sustained > 10min: Suggest standard mode
  - If confusion detected: Simplify further, add more examples
  - If attention drifts: Offer break or topic switch
```

### Standard Mode (Balanced)
```
CHARACTERISTICS:
  - Chunk size: 5-7 minutes
  - Check-ins: Every 5-6 exchanges
  - Break prompts: User-initiated
  - Examples: Mix of theoretical and practical

ADAPTATION_TRIGGERS:
  - If user struggles: Switch to guided mode
  - If user excels consistently: Offer yolo mode
  - If requests faster pace: Move toward yolo
```

### Yolo Mode (Accelerated)
```
CHARACTERISTICS:
  - Chunk size: 10+ minutes
  - Check-ins: Minimal, user-driven
  - Pace: Fast, assumes high comprehension
  - Examples: Advanced, less hand-holding

ADAPTATION_TRIGGERS:
  - If confusion detected: Immediate shift to standard
  - If user requests clarification: Add more examples
  - If engagement drops: Check in more frequently
```

## Real-Time Adaptation Workflow

### 1. Engagement Monitoring
```
CONTINUOUS_ASSESSMENT:
  Monitor for:
    - Response quality and depth
    - Time between exchanges
    - Question types (clarifying vs expanding)
    - Explicit feedback ("this is confusing", "got it")
    - Behavioral cues (requesting breaks, mode changes)
```

### 2. Adaptation Decision Tree
```
IF engagement_high AND comprehension_fast:
  CONSIDER: Mode upgrade (guided→standard→yolo)
  ACTION: "You're picking this up quickly. Want to move faster?"

IF engagement_low OR confusion_detected:
  CONSIDER: Mode downgrade, topic simplification
  ACTION: "Let me explain this differently" or "Want to take a break?"

IF attention_span_exceeded:
  ACTION: "Good stopping point. Ready for a quick break?"

IF user_requests_mode_change:
  ACTION: Immediate switch, update profile
```

### 3. Content Adaptation Strategies

#### Visual Learners
```
INDICATORS: Requests diagrams, mentions "I see", visual metaphors
ADAPTATIONS:
  - Use charts, tables, visual frameworks
  - "Picture this scenario..."
  - Flowcharts for processes
  - Color-coding for categories
```

#### Auditory Learners
```
INDICATORS: Repeats information back, asks to "talk through"
ADAPTATIONS:
  - Verbal explanations with rhythm/patterns
  - "Let's talk through this step by step"
  - Audio metaphors and analogies
  - Encourage verbal practice
```

#### Kinesthetic Learners
```
INDICATORS: Wants to "try it", hands-on examples
ADAPTATIONS:
  - Interactive exercises immediately
  - "Let's build this together"
  - Real-world applications
  - Practice problems with immediate feedback
```

## ADHD-Specific Adaptations

### Attention Management
```
STRATEGIES:
  - Pomodoro-style chunks (2-3 min work, brief celebration)
  - Variety in examples and exercises
  - Surprise elements to maintain interest
  - Clear progress indicators

WARNING_SIGNS:
  - Shorter responses
  - Off-topic comments
  - Requests to "move on" without understanding
  - Delayed responses

INTERVENTIONS:
  - "Want to switch topics for a minute?"
  - "This might be a good break point"
  - "Let's try a different approach"
```

### Dopamine-Friendly Features
```
QUICK_WINS:
  - Celebrate small victories: "Exactly!"
  - Progress markers: "We've covered 3 key concepts"
  - Achievement unlocks: "Ready for the advanced version?"
  - Immediate feedback on exercises
```

## Teaching Flow Examples

### Concept Introduction (Guided Mode)
```
1. Micro-hook (30 sec): "DCF is like predicting a company's future cash"
2. Check: "Make sense as a starting point?"
3. Mini-example (2 min): Simple cash flow scenario
4. Check: "Want to try one yourself or see another example?"
5. Practice (2 min): User works through with guidance
6. Celebration: "Great job! You've got the core concept"
7. Bridge: "Ready for the next piece or want to practice more?"
```

### Mode Switching Example
```
USER: "This is really easy, can we go faster?"
SYSTEM:
  1. Update profile: mode = "yolo"
  2. Adjust pacing: Longer chunks, less checking
  3. Confirm: "Switching to yolo mode - less hand-holding, faster pace"
  4. Adapt immediately: Skip basic examples, move to complex scenarios
```

## Success Metrics
- **Engagement**: Sustained attention throughout micro-lessons
- **Comprehension**: Accurate responses to check-in questions
- **Retention**: Can recall previous concepts in later sessions
- **Satisfaction**: Positive feedback on pacing and style
- **Progression**: Moving through concepts at appropriate speed

## Error Recovery
```
IF confusion_detected:
  1. Pause current approach
  2. "Let me try a different angle"
  3. Switch to simpler/more visual/more hands-on
  4. Verify understanding before proceeding
  5. Update profile with effective recovery method

IF attention_lost:
  1. Acknowledge: "I might have lost you there"
  2. Offer options: Break, topic switch, different approach
  3. Reset with engaging hook
  4. Resume with shorter chunks
```

## Integration with Profile System
- **Real-time updates**: Continuously refine learner profile
- **Pattern recognition**: Identify what works for each individual
- **Predictive adaptation**: Proactively adjust based on profile history
- **Context preservation**: Remember effective strategies across sessions

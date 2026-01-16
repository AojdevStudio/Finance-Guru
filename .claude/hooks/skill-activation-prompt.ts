#!/usr/bin/env bun

/**
 * Skill Activation Prompt Hook
 * User Prompt Submit Hook
 *
 * Analyzes user prompts to detect when domain-specific skills should be activated.
 * Reads skill-rules.json and checks for keyword/intent pattern matches.
 * Outputs warnings/suggestions before Claude responds.
 *
 * Refactored to use Bun runtime for improved performance.
 */

import { readFileSync } from 'fs';
import { join, resolve } from 'path';

// Bun provides __dirname directly
const __dirname = import.meta.dir;

interface HookInput {
    session_id: string;
    transcript_path: string;
    cwd: string;
    permission_mode: string;
    prompt: string;
}

interface PromptTriggers {
    keywords?: string[];
    intentPatterns?: string[];
}

interface SkillRule {
    type: 'guardrail' | 'domain';
    enforcement: 'block' | 'suggest' | 'warn';
    priority: 'critical' | 'high' | 'medium' | 'low';
    promptTriggers?: PromptTriggers;
}

interface SkillRules {
    version: string;
    skills: Record<string, SkillRule>;
}

interface MatchedSkill {
    name: string;
    matchType: 'keyword' | 'intent';
    config: SkillRule;
}

function getProjectRoot(): string {
    // Hook is in family-office/.claude/hooks/
    // Project root is family-office/
    return resolve(__dirname, '../..');
}

function main() {
    // Read stdin (prompt submission info)
    let inputData = '';
    process.stdin.setEncoding('utf-8');

    // Handle both piped and direct execution
    if (process.stdin.isTTY) {
        // Direct execution (testing) - use dummy input
        inputData = JSON.stringify({
            session_id: 'test',
            transcript_path: '/tmp/transcript.txt',
            cwd: getProjectRoot(),
            permission_mode: 'normal',
            prompt: 'test prompt'
        });
        processHook(inputData);
    } else {
        // Piped input from Claude Code
        process.stdin.on('data', chunk => {
            inputData += chunk;
        });

        process.stdin.on('end', () => {
            processHook(inputData);
        });
    }
}

function processHook(inputData: string) {
    try {
        // Check for empty input
        if (!inputData || inputData.trim() === '') {
            process.exit(0);
        }

        // Read input from stdin
        const data: HookInput = JSON.parse(inputData);
        const prompt = data.prompt.toLowerCase();

        // Load skill rules
        const projectRoot = data.cwd || process.env.CLAUDE_PROJECT_DIR || getProjectRoot();
        const rulesPath = join(projectRoot, '.claude', 'skills', 'skill-rules.json');
        const rules: SkillRules = JSON.parse(readFileSync(rulesPath, 'utf-8'));

        const matchedSkills: MatchedSkill[] = [];

        // Check each skill for matches
        for (const [skillName, config] of Object.entries(rules.skills)) {
            const triggers = config.promptTriggers;
            if (!triggers) {
                continue;
            }

            // Keyword matching
            if (triggers.keywords) {
                const keywordMatch = triggers.keywords.some(kw =>
                    prompt.includes(kw.toLowerCase())
                );
                if (keywordMatch) {
                    matchedSkills.push({ name: skillName, matchType: 'keyword', config });
                    continue;
                }
            }

            // Intent pattern matching
            if (triggers.intentPatterns) {
                const intentMatch = triggers.intentPatterns.some(pattern => {
                    const regex = new RegExp(pattern, 'i');
                    return regex.test(prompt);
                });
                if (intentMatch) {
                    matchedSkills.push({ name: skillName, matchType: 'intent', config });
                }
            }
        }

        // Generate output if matches found
        if (matchedSkills.length > 0) {
            let output = '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
            output += '🎯 SKILL ACTIVATION CHECK\n';
            output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n';

            // Group by priority
            const critical = matchedSkills.filter(s => s.config.priority === 'critical');
            const high = matchedSkills.filter(s => s.config.priority === 'high');
            const medium = matchedSkills.filter(s => s.config.priority === 'medium');
            const low = matchedSkills.filter(s => s.config.priority === 'low');

            if (critical.length > 0) {
                output += '⚠️ CRITICAL SKILLS (REQUIRED):\n';
                critical.forEach(s => output += `  → ${s.name}\n`);
                output += '\n';
            }

            if (high.length > 0) {
                output += '📚 RECOMMENDED SKILLS:\n';
                high.forEach(s => output += `  → ${s.name}\n`);
                output += '\n';
            }

            if (medium.length > 0) {
                output += '💡 SUGGESTED SKILLS:\n';
                medium.forEach(s => output += `  → ${s.name}\n`);
                output += '\n';
            }

            if (low.length > 0) {
                output += '📌 OPTIONAL SKILLS:\n';
                low.forEach(s => output += `  → ${s.name}\n`);
                output += '\n';
            }

            output += 'ACTION: Use Skill tool BEFORE responding\n';
            output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';

            console.log(output);
        }

        process.exit(0);
    } catch (err) {
        console.error('Error in skill-activation-prompt hook:', err);
        process.exit(1);
    }
}

main();

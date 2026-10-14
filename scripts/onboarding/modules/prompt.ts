import { createInterface, type Interface } from 'readline';

export type Prompt = Interface;

export function createPrompt(): Prompt {
  return createInterface({
    input: process.stdin,
    output: process.stdout
  });
}

/** Asks until `validator` accepts the answer. With `allowEmpty`, a blank answer resolves to null. */
export function promptWithValidation<T>(
  rl: Prompt,
  question: string,
  validator: (input: string) => T
): Promise<T>;
export function promptWithValidation<T>(
  rl: Prompt,
  question: string,
  validator: (input: string) => T,
  allowEmpty: true
): Promise<T | null>;
export function promptWithValidation<T>(
  rl: Prompt,
  question: string,
  validator: (input: string) => T,
  allowEmpty = false
): Promise<T | null> {
  return new Promise((resolve) => {
    const ask = () => {
      rl.question(question, (answer) => {
        if (allowEmpty && answer.trim() === '') {
          resolve(null);
          return;
        }

        try {
          resolve(validator(answer));
        } catch (error) {
          if (error instanceof Error) {
            console.log(`❌ ${error.message}`);
          }
          console.log('Please try again.');
          ask();
        }
      });
    };
    ask();
  });
}

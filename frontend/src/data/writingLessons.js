/**
 * Writing Lessons curriculum (Phase 2) — 12 step-by-step lessons.
 */

export const WRITING_LESSONS = [
  {
    id: 'good_sentence',
    number: 1,
    title: 'What is a good English sentence?',
    skillGoal: 'Write complete sentences with subject + verb + a clear idea.',
    explanation: `A good English sentence needs three things: a subject (who or what), a verb (action or state), and a complete idea.

Avoid incomplete sentences like "Spring beautiful." Always include a verb such as "is" or "are."

Also avoid very long sentences with too many ideas. One clear idea per sentence is easier to read.`,
    pattern: 'Subject + verb + complete idea',
    teachPoints: [
      'Subject + verb + complete idea',
      'Avoid incomplete sentences',
      'Avoid very long confusing sentences',
    ],
    examples: [
      { label: 'Weak', text: 'Spring beautiful.' },
      { label: 'Correct', text: 'Spring is beautiful.' },
      { label: 'Better', text: 'Spring is beautiful because the weather becomes warmer.' },
    ],
    miniPractice: {
      prompt: 'Fix this sentence:',
      starter: 'My favorite season spring because weather nice.',
    },
  },
  {
    id: 'expand_sentence',
    number: 2,
    title: 'How to expand a sentence',
    skillGoal: 'Add reasons, examples, contrast, or results to make sentences stronger.',
    explanation: `Start with a simple sentence, then add more detail step by step.

You can add:
- a reason (because...)
- an example (for example...)
- contrast (however...)
- a result (so..., as a result...)`,
    pattern: 'Main idea + because + reason + example/result',
    teachPoints: ['Add reason', 'Add example', 'Add contrast', 'Add result'],
    examples: [
      { label: 'Basic', text: 'I like spring.' },
      { label: 'With reason', text: 'I like spring because the weather is warm.' },
      {
        label: 'With example',
        text: 'I like spring because the weather is warm, so I can walk outside and ride my bike.',
      },
    ],
    miniPractice: {
      prompt: 'Expand this sentence with a reason and an example:',
      starter: 'I like spring.',
    },
  },
  {
    id: 'topic_sentence',
    number: 3,
    title: 'How to write a topic sentence',
    skillGoal: 'Write a topic sentence that tells the reader what the paragraph is about.',
    explanation: `A topic sentence has two parts: the main idea and a controlling idea (what you will explain).

A weak topic sentence is too short: "Spring."

A better topic sentence tells the reader your opinion and what you will discuss.`,
    pattern: 'Main idea + controlling idea (because / when / that...)',
    teachPoints: [
      'Main idea + controlling idea',
      'Tell the reader what the paragraph is about',
    ],
    examples: [
      { label: 'Weak', text: 'Spring.' },
      {
        label: 'Better',
        text: 'Spring is my favorite season because it makes me feel energetic and hopeful.',
      },
    ],
    miniPractice: {
      prompt: 'Write a topic sentence about your favorite season:',
      starter: 'My favorite season is ...',
    },
  },
  {
    id: 'support_idea',
    number: 4,
    title: 'How to support your idea',
    skillGoal: 'Support your main idea with a reason, example, and explanation.',
    explanation: `After your main idea, support it with this formula:

Idea → Reason → Example → Explanation

The reason explains why. The example shows proof. The explanation connects the example back to your idea.`,
    pattern: 'Idea → Reason → Example → Explanation',
    teachPoints: ['Reason', 'Example', 'Explanation'],
    examples: [
      { label: 'Idea', text: 'Spring is relaxing.' },
      { label: 'Reason', text: 'The weather is mild.' },
      { label: 'Example', text: 'I can walk in the park after studying.' },
      {
        label: 'Explanation',
        text: 'This helps me reduce stress and feel more focused.',
      },
    ],
    miniPractice: {
      prompt: 'Write one sentence that gives a reason and one sentence with an example for this idea:',
      starter: 'Idea: Online learning is useful.',
    },
  },
  {
    id: 'write_paragraph',
    number: 5,
    title: 'How to write a paragraph',
    skillGoal: 'Build a full paragraph with topic sentence, support, and conclusion.',
    explanation: `A good paragraph has five parts:

1. Topic sentence — your main idea
2. Reason — why you believe it
3. Example — a specific detail
4. Explanation — how the example supports your idea
5. Conclusion — restate your main idea naturally`,
    pattern: 'Topic sentence → Reason → Example → Explanation → Conclusion',
    teachPoints: [
      'Topic sentence',
      'Reason',
      'Example',
      'Explanation',
      'Conclusion',
    ],
    examples: [
      { label: 'Topic sentence', text: 'Spring is my favorite season.' },
      { label: 'Reason', text: 'The weather becomes warmer.' },
      { label: 'Example', text: 'I can walk outside and ride my bike more often.' },
      { label: 'Explanation', text: 'These activities help me feel active and relaxed.' },
      { label: 'Conclusion', text: 'For these reasons, spring gives me energy and motivation.' },
      {
        label: 'Full paragraph',
        text: 'Spring is my favorite season because the weather becomes warmer after winter. For example, I can walk outside and ride my bike more often. These activities help me feel active and relaxed. For these reasons, spring gives me energy and motivation.',
      },
    ],
    miniPractice: {
      prompt: 'Write a short paragraph (4–5 sentences) about your favorite hobby:',
      starter: 'My favorite hobby is ...',
    },
  },
  {
    id: 'opinion_paragraph',
    number: 6,
    title: 'How to write an opinion paragraph',
    skillGoal: 'State an opinion with two reasons, examples, and a conclusion.',
    explanation: `For opinion writing, follow this structure:

- State your opinion clearly
- Reason 1 + Example 1
- Reason 2 + Example 2
- Conclusion that restates your opinion

Use phrases like "In my opinion" and "One reason is that" to sound natural.`,
    pattern: 'Opinion → Reason 1 + Example → Reason 2 + Example → Conclusion',
    teachPoints: [
      'Opinion',
      'Reason 1 + example 1',
      'Reason 2 + example 2',
      'Conclusion',
    ],
    sentenceStarters: [
      'In my opinion, ...',
      'One reason is that ...',
      'For example, ...',
      'Another reason is ...',
      'For these reasons, ...',
    ],
    examples: [
      {
        label: 'Opinion',
        text: 'In my opinion, students should have part-time jobs while studying.',
      },
      {
        label: 'Reason + example',
        text: 'One reason is that a job teaches time management. For example, I learned to plan my study schedule better.',
      },
    ],
    miniPractice: {
      prompt: 'Write an opinion paragraph: Do you prefer studying alone or in a group?',
      starter: 'In my opinion, ...',
    },
  },
  {
    id: 'toefl_writing',
    number: 7,
    title: 'How to write TOEFL-style answers',
    skillGoal: 'Answer TOEFL questions clearly with two reasons and examples.',
    explanation: `TOEFL independent writing needs a clear answer, not a memorized template.

Structure:
- Introduction: state your opinion directly
- Body: Reason 1 + example, then Reason 2 + example
- Conclusion: repeat your main idea naturally

Keep sentences clear. Avoid robotic phrases like "Firstly, secondly, in conclusion" in every essay.`,
    pattern: 'Introduction → Reason 1 + example → Reason 2 + example → Conclusion',
    teachPoints: [
      'Clear answer to the question',
      'Two reasons with examples',
      'Simple conclusion',
      'Avoid memorized robotic templates',
    ],
    examples: [
      { label: 'Introduction', text: 'I believe living in a small town is better for students.' },
      { label: 'Body', text: 'One reason is that life is quieter, so I can focus on studying. Another reason is that people are friendlier.' },
      { label: 'Conclusion', text: 'For these reasons, I prefer living in a small town.' },
    ],
    miniPractice: {
      prompt: 'Write a TOEFL-style introduction + one reason with example for this question:',
      starter: 'Question: Do you agree that technology has made communication easier?',
    },
  },
  {
    id: 'academic_paragraph',
    number: 8,
    title: 'How to write academic paragraphs',
    skillGoal: 'Write academic paragraphs with claim, evidence, explanation, and link.',
    explanation: `Academic paragraphs use this formula:

Claim → Evidence → Explanation → Link

The claim is your main point. Evidence supports it with facts or examples. Explanation shows why the evidence matters. The link connects to the next idea or conclusion.`,
    pattern: 'Claim → Evidence → Explanation → Link',
    teachPoints: ['Claim', 'Evidence', 'Explanation', 'Link'],
    examples: [
      { label: 'Claim', text: 'AI can support English learning.' },
      { label: 'Evidence', text: 'AI tools can provide immediate feedback on grammar and vocabulary.' },
      { label: 'Explanation', text: 'This helps learners correct mistakes before they become habits.' },
      { label: 'Link', text: 'Therefore, AI can make independent learning more effective.' },
    ],
    miniPractice: {
      prompt: 'Write a claim + one sentence of evidence about online education:',
      starter: 'Claim: Online education can be effective for many students.',
    },
  },
  {
    id: 'connect_ideas',
    number: 9,
    title: 'How to connect ideas',
    skillGoal: 'Use connectors to link ideas clearly in American English.',
    explanation: `Connectors help your writing flow. Learn when to use each one:

- because (reason)
- so / as a result (result)
- however (contrast)
- therefore (conclusion)
- for example (example)
- in addition (adding another point)

Watch common mistakes: do not use "however" and "but" together.`,
    pattern: 'Use connectors to show reason, result, contrast, or example',
    teachPoints: ['because', 'so', 'however', 'therefore', 'for example', 'in addition', 'as a result'],
    connectors: [
      { word: 'because', meaning: 'shows a reason', example: 'I stay inside because it is raining.', mistake: 'I stay inside, because is raining. (missing subject)' },
      { word: 'however', meaning: 'shows contrast', example: 'Spring is warm; however, winter is cold.', mistake: 'However I like spring but I hate winter. (too many contrast words)' },
      { word: 'for example', meaning: 'introduces an example', example: 'I enjoy outdoor activities. For example, I ride my bike in spring.', mistake: 'For example I like spring. (needs a comma or new sentence)' },
      { word: 'therefore', meaning: 'shows a conclusion', example: 'The weather is warm; therefore, I go outside more.', mistake: 'Therefore I like spring because warm. (incomplete idea)' },
    ],
    miniPractice: {
      prompt: 'Combine these two ideas using "because" or "however":',
      starter: 'I like summer. I do not like very hot weather.',
    },
  },
  {
    id: 'natural_english',
    number: 10,
    title: 'How to write naturally in American English',
    skillGoal: 'Write clear, natural American English — not direct translation.',
    explanation: `Natural American English is clear and specific.

Tips:
- Prefer clear short sentences
- Use active voice when possible ("I wrote the essay" not "The essay was written by me")
- Avoid overcomplicated words when a simple word works
- Be specific (say "walk in the park" not just "do activities")
- Avoid direct translation from Persian when it sounds unnatural`,
    pattern: 'Clear subject + active verb + specific detail',
    teachPoints: [
      'Prefer clear sentences',
      'Use active voice when possible',
      'Avoid overcomplicated words',
      'Be specific',
      'Avoid direct translation from Persian',
    ],
    examples: [
      { label: 'Less natural', text: 'Nature is waking up to be alive one more time.' },
      { label: 'More natural', text: 'Nature comes alive again after winter.' },
    ],
    miniPractice: {
      prompt: 'Rewrite this sentence in more natural American English:',
      starter: 'Nature is waking up to be alive one more time.',
    },
  },
  {
    id: 'short_article',
    number: 11,
    title: 'How to write a short article',
    skillGoal: 'Write a beginner-friendly short article with title, body, and conclusion.',
    explanation: `A short article has these parts:

1. Title — clear and interesting
2. Introduction — hook the reader + main idea
3. Body — 2–3 supporting points with examples
4. Conclusion — summarize and leave a final thought

Keep it beginner-friendly. You do not need very formal academic language.`,
    pattern: 'Title → Introduction → Supporting points → Conclusion',
    teachPoints: [
      'Title',
      'Introduction',
      'Main idea',
      'Supporting paragraphs',
      'Examples/evidence',
      'Conclusion',
    ],
    examples: [
      { label: 'Title', text: 'Why Spring Is My Favorite Season' },
      { label: 'Introduction', text: 'Many people have a favorite season. For me, spring is the best time of year.' },
      { label: 'Body point', text: 'First, the weather becomes warmer, which makes outdoor activities easier.' },
    ],
    miniPractice: {
      prompt: 'Write a title and introduction (2–3 sentences) for a short article about learning English:',
      starter: 'Title: ...',
    },
  },
  {
    id: 'revise_writing',
    number: 12,
    title: 'How to revise your writing',
    skillGoal: 'Revise your writing by checking grammar, organization, and clarity.',
    explanation: `Good writers revise. Use this checklist:

1. Grammar — verbs, articles, word order
2. Organization — does each paragraph have one main idea?
3. Examples — do you have enough specific details?
4. Word choice — are your words clear and natural?
5. Sentence length — mix short and medium sentences
6. Read aloud — if it sounds strange, rewrite it`,
    pattern: 'Write → Check grammar → Check organization → Check examples → Read aloud',
    teachPoints: [
      'Check grammar',
      'Check organization',
      'Check examples',
      'Check word choice',
      'Check sentence length',
      'Read it aloud',
    ],
    examples: [
      { label: 'First draft', text: 'Spring good because weather nice and I happy.' },
      { label: 'After revision', text: 'Spring is a wonderful season because the weather becomes pleasant, and I feel happier when I spend time outside.' },
    ],
    miniPractice: {
      prompt: 'Revise this paragraph. Fix grammar and make it clearer:',
      starter: 'Spring good season. Weather nice. I walk outside and feel happy because nature beautiful.',
    },
  },
]

export function getLessonById(id) {
  return WRITING_LESSONS.find((lesson) => lesson.id === id) || null
}

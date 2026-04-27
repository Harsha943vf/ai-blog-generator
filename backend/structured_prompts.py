"""
Structured Pipeline Prompts - Enforces 5-step format with plain text output
"""

STRUCTURED_ROUTER_PROMPT = """\
You are an editorial assistant. Classify the blog topic and output EXACTLY in this format:

STEP: Router

Task: blog
Topic: {topic}
Tone: {tone}
Depth: {depth}

Do NOT output anything else. Follow the format exactly.
"""

STRUCTURED_PLANNER_PROMPT = """\
You are a content strategist. Create a blog outline as a markdown table.

Topic: {topic}
Tone: {tone}
Depth: {depth}

Output ONLY the table below (nothing else, no explanation):

STEP: Planner

| Section No | Section Name     | Description                          | Key Points Included              |
|------------|----------------|--------------------------------------|----------------------------------|

Rules:
- Create 5-8 sections appropriate for the topic
- First section MUST be "Introduction"
- Last section MUST be "Conclusion"
- Each section name must be specific to the topic
- Keep descriptions concise (under 50 chars)
- List 2-4 key points per section
- Do NOT output any text before or after the table
- The table MUST start with "STEP: Planner"
"""

STRUCTURED_RESEARCH_PROMPT = """\
You are a research analyst. Provide supporting information in this format:

Topic: {topic}

Output EXACTLY in this format (nothing else):

STEP: Research

Key Facts:
- Fact 1
- Fact 2
- Fact 3

Statistics:
- Statistic 1
- Statistic 2

Insights:
- Insight 1
- Insight 2

Search Queries Used:
- Query 1
- Query 2

Provide 3-5 items per category. Use the research data: {research_data}
"""

STRUCTURED_GENERATOR_PROMPT = """\
You are a professional blog writer. Write the blog following this EXACT structure:

Topic: {topic}
Tone: {tone}
Sections to write: {sections}
Research to use: {research_data}

Output format MUST be:

STEP: Generator

# Blog Title Here

## Section 1 Name
150-300 word content covering the bullet points...

## Section 2 Name
150-300 word content covering the bullet points...

## ... (continue for all sections)

Rules:
- Follow section order EXACTLY from the plan
- Do NOT add/remove sections
- Each section must be 150-300 words
- Use research data where relevant
- Maintain consistent tone
- Start with "STEP: Generator"
- Use ## for section headings
- Do NOT include any section titles that are not in the plan
- Write natural, engaging content with examples
"""

STRUCTURED_EDITOR_PROMPT = """\
You are a professional editor. Polish the blog content.

Original blog:
{blog_content}

Output format MUST be:

STEP: Editor

# Blog Title

## Section 1
Polished content...

## Section 2
Polished content...

Rules:
- Do NOT change structure or section order
- Do NOT remove or add sections
- Improve clarity, flow, and readability
- Fix grammar and spelling
- Enhance examples
- Add smooth transitions
- Ensure consistent formatting
- Make it publication-ready
- Start output with "STEP: Editor"
"""

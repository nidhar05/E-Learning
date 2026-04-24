"""
Service for extracting content from videos and generating structured notes,
subtitle files, and MCQ questions.
"""

import random
import re

from django.core.files.storage import default_storage

from notes.models import NoteSection, VideoNotes
from quiz.models import Quiz, QuizQuestion

from .subtitle_utils import (
    AudioTranscriber,
    SubtitleParser,
    convert_srt_to_vtt,
    save_vtt_file,
    safe_log,
    subtitle_file_has_synthetic_timing,
)


class ContentExtractor:
    """Extracts content from subtitles or plain text and generates notes."""

    INVALID_TERMS = {
        "this",
        "that",
        "these",
        "those",
        "first one",
        "second one",
        "third one",
        "when we",
        "we",
        "you",
        "it",
        "they",
        "there",
    }

    @staticmethod
    def _normalize_text(text):
        return re.sub(r"\s+", " ", (text or "")).strip()

    @staticmethod
    def _split_sentences(text):
        normalized_text = ContentExtractor._normalize_text(text)
        if not normalized_text:
            return []

        raw_sentences = re.split(r"(?<=[.!?])\s+", normalized_text)
        cleaned_sentences = []

        for sentence in raw_sentences:
            cleaned = sentence.strip(" -\n\t")
            cleaned = re.sub(r"\s+", " ", cleaned)
            if len(cleaned) < 35:
                continue
            if cleaned not in cleaned_sentences:
                cleaned_sentences.append(cleaned)

        return cleaned_sentences

    @staticmethod
    def _format_bullets(items):
        return "\n".join(f"- {item}" for item in items if item)

    @staticmethod
    def _is_filler_sentence(sentence):
        lowered = sentence.lower()
        filler_phrases = [
            "hello",
            "welcome",
            "today we will",
            "today we're going to",
            "in this video",
            "in the previous tutorial",
            "provide links",
            "let's start",
            "let us start",
            "you can see",
            "if you remember",
            "press enter",
            "open a terminal",
            "click the three dots",
            "new terminal",
        ]
        return any(phrase in lowered for phrase in filler_phrases)

    @staticmethod
    def _meaningful_sentences(text):
        meaningful = []

        for sentence in ContentExtractor._split_sentences(text):
            if ContentExtractor._is_filler_sentence(sentence):
                continue
            meaningful.append(sentence)

        return meaningful

    @staticmethod
    def _cleanup_phrase(text):
        cleaned = re.sub(r"\b(?:so|now|then|also|just|really|very)\b", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip(" ,.-")

    @staticmethod
    def _remove_conversational_words(text):
        cleaned = text
        cleaned = re.sub(r"\b(?:i|i'm|i am|we|we're|we are|you|you'll|you will|you'd|you can|you are)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(?:let's|let us)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(?:today|here)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip(" ,.-")

    @staticmethod
    def _sanitize_study_line(text):
        cleaned = ContentExtractor._cleanup_phrase(text)
        cleaned = ContentExtractor._remove_conversational_words(cleaned)
        cleaned = re.sub(r"\b(?:start by|going to)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")
        if not cleaned:
            return ""
        return cleaned[0].upper() + cleaned[1:] + "."

    @staticmethod
    def _to_statement(sentence):
        return ContentExtractor._sanitize_study_line(sentence)

    @staticmethod
    def _dedupe(items, max_items=None):
        result = []
        seen = set()

        for item in items:
            key = item.lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(item)
            if max_items and len(result) >= max_items:
                break

        return result

    @staticmethod
    def _extract_examples(sentences, max_items=3):
        examples = []

        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in ["example", "for example", "such as", "assigned", "returns"]):
                line = ContentExtractor._to_statement(sentence)
                if line:
                    examples.append(line)

        return ContentExtractor._dedupe(examples, max_items=max_items)

    @staticmethod
    def _extract_naming_rules(sentences, max_items=4):
        rules = []

        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in ["name", "underscore", "number", "letters", "character", "valid"]):
                line = ContentExtractor._to_statement(sentence)
                if line:
                    rules.append(line)

        return ContentExtractor._dedupe(rules, max_items=max_items)

    @staticmethod
    def _ordered_key_points(sentences, max_points=6):
        category_order = ["definition", "usage", "rule", "impact", "other"]
        categorized = {key: [] for key in category_order}

        for sentence in sentences:
            lowered = sentence.lower()
            if any(k in lowered for k in [" is ", " means ", " refers to ", " defined as "]):
                category = "definition"
            elif any(k in lowered for k in ["used to", "print", "assign", "store", "display"]):
                category = "usage"
            elif any(k in lowered for k in ["rule", "valid", "name", "underscore", "number"]):
                category = "rule"
            elif any(k in lowered for k in ["important", "because", "helps", "allows"]):
                category = "impact"
            else:
                category = "other"

            line = ContentExtractor._to_statement(sentence)
            if line:
                categorized[category].append(line)

        ordered = []
        for category in category_order:
            ordered.extend(categorized[category])

        return ContentExtractor._dedupe(ordered, max_items=max_points)

    @staticmethod
    def _build_interview_points(terms, key_points):
        prompts = []
        term_names = list(terms.keys())

        for term in term_names[:4]:
            prompts.append(f"Define {term} and explain where it is applied.")

        if len(term_names) >= 2:
            prompts.append(f"Differentiate {term_names[0]} and {term_names[1]} with one practical example.")

        for point in key_points[:2]:
            compact = point.rstrip(".")
            if compact:
                prompts.append(f"Explain this concept clearly in one minute: {compact.lower()}.")

        return ContentExtractor._dedupe(prompts, max_items=6)

    @staticmethod
    def _build_learning_objectives(key_points):
        objectives = []
        for point in key_points[:4]:
            clean_point = point.rstrip(".")
            if clean_point:
                objectives.append(f"Understand and explain: {clean_point.lower()}.")
        return ContentExtractor._dedupe(objectives, max_items=4)

    @staticmethod
    def _build_study_checklist(terms, key_points):
        checklist = []

        for term in list(terms.keys())[:4]:
            checklist.append(f"Review definition and use-case of {term}.")

        if key_points:
            checklist.append("Revise all core study points and explain each in simple language.")
            checklist.append("Practice one short example for each major concept.")

        return ContentExtractor._dedupe(checklist, max_items=6)

    @staticmethod
    def _build_interview_questions(terms, key_points):
        questions = []
        terms_list = list(terms.keys())

        for term in terms_list[:3]:
            questions.append(f"- What is {term} and why is it important?")

        if len(terms_list) >= 2:
            questions.append(f"- Compare {terms_list[0]} and {terms_list[1]} with an example.")

        for point in key_points[:2]:
            compact = point.rstrip(".")
            if compact:
                questions.append(f"- Explain this concept briefly: {compact.lower()}.")

        return ContentExtractor._dedupe(questions, max_items=6)

    @staticmethod
    def build_notes_body(video, key_points, terms, source_sentences):
        intro = (
            "## Lesson Summary\n"
            f"{video.title} covers foundational concepts needed for study, practical application, and interview preparation."
        )

        sections = [intro]

        learning_objectives = ContentExtractor._build_learning_objectives(key_points)
        if learning_objectives:
            sections.append("## Learning Objectives\n" + ContentExtractor._format_bullets(learning_objectives))

        if key_points:
            sections.append(
                "## Core Concepts Explained\n" + ContentExtractor._format_bullets(key_points[:6])
            )

        if terms:
            concept_lines = [
                f"- {term}: {definition}"
                for term, definition in list(terms.items())[:6]
            ]
            sections.append("## Important Terms\n" + "\n".join(concept_lines))

        naming_rules = ContentExtractor._extract_naming_rules(source_sentences)
        if naming_rules:
            sections.append("## Practical Rules\n" + ContentExtractor._format_bullets(naming_rules))

        examples = ContentExtractor._extract_examples(source_sentences)
        if examples:
            sections.append("## Practical Examples From Lesson\n" + ContentExtractor._format_bullets(examples))

        interview_points = ContentExtractor._build_interview_points(terms, key_points)
        if interview_points:
            sections.append("## Interview Preparation Points\n" + ContentExtractor._format_bullets(interview_points))

        interview_questions = ContentExtractor._build_interview_questions(terms, key_points)
        if interview_questions:
            sections.append("## Interview Questions To Practice\n" + "\n".join(interview_questions))

        study_checklist = ContentExtractor._build_study_checklist(terms, key_points)
        if study_checklist:
            sections.append("## Revision Checklist\n" + ContentExtractor._format_bullets(study_checklist))

        return "\n\n".join(section for section in sections if section.strip())

    @staticmethod
    def extract_key_points(text, max_points=5):
        sentences = ContentExtractor._meaningful_sentences(text)
        if not sentences:
            return []
        return ContentExtractor._ordered_key_points(sentences, max_points=max_points)

    @staticmethod
    def extract_terms(text):
        sentences = ContentExtractor._meaningful_sentences(text)
        if not sentences:
            return {}

        terms = {}
        patterns = [
            re.compile(
                r"\b([A-Za-z][A-Za-z0-9_ ]{1,40}?)\s+(?:is|are|means|refers to|defined as)\s+(.+)",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(?:called|known as)\s+([A-Za-z][A-Za-z0-9_ ]{1,40}?)\s+(.+)",
                re.IGNORECASE,
            ),
        ]

        for sentence in sentences:
            for pattern in patterns:
                match = pattern.search(sentence)
                if not match:
                    continue

                term = match.group(1).strip(" .,:;-")
                definition = match.group(2).strip(" .,:;-")
                normalized_term = re.sub(r"\s+", " ", term.lower()).strip()

                if len(term.split()) > 5 or len(term) < 2:
                    continue
                if normalized_term in ContentExtractor.INVALID_TERMS:
                    continue
                if any(pronoun in normalized_term for pronoun in ["this ", "that ", "these ", "those "]):
                    continue
                if re.search(r"\b(first|second|third)\s+one\b", normalized_term):
                    continue
                if len(definition) < 15:
                    continue

                cleaned_definition = ContentExtractor._cleanup_phrase(definition[:160])
                if cleaned_definition:
                    study_definition = ContentExtractor._remove_conversational_words(cleaned_definition)
                    if study_definition:
                        terms[term.title()] = study_definition[:1].upper() + study_definition[1:]
                break

        return terms

    @staticmethod
    def create_structured_notes(video, content_text):
        normalized_text = ContentExtractor._normalize_text(content_text)
        notes, created = VideoNotes.objects.get_or_create(
            video=video,
            defaults={
                "title": f"Notes: {video.title}",
                "content": normalized_text or f"Study notes for {video.title}",
                "is_ai_generated": True,
                "is_published": True,
            },
        )

        key_points = ContentExtractor.extract_key_points(normalized_text)
        terms = ContentExtractor.extract_terms(normalized_text)
        source_sentences = ContentExtractor._meaningful_sentences(normalized_text)
        note_body = ContentExtractor.build_notes_body(video, key_points, terms, source_sentences)

        notes.content = note_body
        notes.key_takeaways = ContentExtractor._format_bullets(key_points[:5])
        notes.important_terms = "\n".join(
            [f"{term}: {definition}" for term, definition in list(terms.items())[:6]]
        )
        notes.is_ai_generated = True
        notes.is_published = True
        notes.save()

        notes.sections.all().delete()

        return notes


class MCQGenerator:
    """Generates multiple-choice questions from text content."""

    TOPIC_KEYWORDS = [
        "python",
        "variable",
        "variables",
        "data type",
        "data types",
        "string",
        "integer",
        "float",
        "boolean",
        "list",
        "tuple",
        "dictionary",
        "set",
        "print",
        "function",
        "assignment",
        "operator",
        "identifier",
        "name",
        "value",
    ]
    CONCEPT_QUESTION_BANK = [
        {
            "core": True,
            "keywords": ["python", "interpreted language"],
            "question": "In Python basics, what does it mean that Python is interpreted?",
            "correct": "Code is executed by an interpreter line by line.",
            "wrong": [
                "Python code must always be compiled into machine code first.",
                "Python can only run inside a web browser.",
                "Python programs cannot be debugged interactively.",
            ],
            "explanation": "Python is generally executed by an interpreter rather than a separate compile step.",
        },
        {
            "core": True,
            "keywords": ["variable", "variables"],
            "question": "What is a variable in Python?",
            "correct": "A named reference used to store a value.",
            "wrong": [
                "A special symbol used only in comments.",
                "A fixed keyword that cannot change.",
                "A tool used to install Python packages.",
            ],
            "explanation": "A variable stores data by associating a name with a value.",
        },
        {
            "core": True,
            "keywords": ["assignment", "equals sign", "="],
            "question": "What is the purpose of assignment in Python?",
            "correct": "It binds a variable name to a value.",
            "wrong": [
                "It prints output to the terminal.",
                "It converts text to numbers automatically.",
                "It creates a Python virtual environment.",
            ],
            "explanation": "Assignment links a name with data using '='.",
        },
        {
            "core": True,
            "keywords": ["print", "print function", "print statements"],
            "question": "What is the `print()` function used for in Python?",
            "correct": "To display output in the console.",
            "wrong": [
                "To create variables without values.",
                "To stop the Python interpreter permanently.",
                "To rename all functions in a file.",
            ],
            "explanation": "`print()` is used to show values and messages.",
        },
        {
            "core": True,
            "keywords": ["string", "text"],
            "question": "Which statement best describes a string in Python?",
            "correct": "A string is text data, usually written inside quotes.",
            "wrong": [
                "A string is only a whole number value.",
                "A string is a command for creating folders.",
                "A string is used to import modules automatically.",
            ],
            "explanation": "Strings represent textual data.",
        },
        {
            "core": True,
            "keywords": ["integer", "int", "number"],
            "question": "What is an integer in Python?",
            "correct": "A whole number without a decimal part.",
            "wrong": [
                "A text value surrounded by quotes.",
                "A function used for input/output operations.",
                "A file extension for Python projects.",
            ],
            "explanation": "Integers are whole numeric values.",
        },
        {
            "core": True,
            "keywords": ["float", "decimal"],
            "question": "What is a float in Python?",
            "correct": "A numeric type used for decimal values.",
            "wrong": [
                "A type used only for comments.",
                "A value that can contain only letters.",
                "A module that installs dependencies.",
            ],
            "explanation": "Floats represent numbers with decimals.",
        },
        {
            "core": True,
            "keywords": ["boolean", "bool", "true", "false"],
            "question": "What does a Boolean value represent in Python?",
            "correct": "A truth value: True or False.",
            "wrong": [
                "A decimal number with many digits.",
                "A collection that stores key-value pairs.",
                "A syntax rule for naming files.",
            ],
            "explanation": "Booleans model logical truth values.",
        },
        {
            "core": True,
            "keywords": ["identifier", "name", "underscore"],
            "question": "Which naming practice is valid for Python identifiers?",
            "correct": "Use letters, numbers, and underscores, without starting with a number.",
            "wrong": [
                "Start names with symbols like # or @ for readability.",
                "Use spaces inside variable names.",
                "Use only uppercase punctuation characters.",
            ],
            "explanation": "Identifiers follow Python naming rules.",
        },
        {
            "core": True,
            "keywords": ["compiler", "compiled"],
            "question": "How is Python commonly described compared with compiled languages?",
            "correct": "Python is usually introduced as interpreted, while compiled languages rely on a compile step.",
            "wrong": [
                "Python cannot run code unless hardware drivers are rewritten.",
                "Compiled languages do not support variables.",
                "Python and compiled languages are exactly the same in execution model.",
            ],
            "explanation": "Intro lessons often contrast interpreted and compiled execution.",
        },
        {
            "core": True,
            "keywords": ["comment", "#"],
            "question": "What is the purpose of comments in Python code?",
            "correct": "Comments document code and are ignored during execution.",
            "wrong": [
                "Comments are executed before every print statement.",
                "Comments are required for variable assignment to work.",
                "Comments automatically convert strings to integers.",
            ],
            "explanation": "Comments help readability and are not executed as program logic.",
        },
        {
            "core": True,
            "keywords": ["input", "user input"],
            "question": "What does the `input()` function do in Python?",
            "correct": "It reads text input provided by the user.",
            "wrong": [
                "It clears all variables in the current file.",
                "It prints every variable automatically.",
                "It compiles Python code into machine code.",
            ],
            "explanation": "`input()` captures user-entered text from standard input.",
        },
        {
            "core": True,
            "keywords": ["newline", "\\n", "escape"],
            "question": "What does `\\n` represent in Python strings?",
            "correct": "A newline character.",
            "wrong": [
                "A tab character.",
                "A comment marker.",
                "A variable declaration symbol.",
            ],
            "explanation": "`\\n` inserts a line break in string output.",
        },
        {
            "core": True,
            "keywords": ["repl", "terminal", "interactive"],
            "question": "What is the Python REPL commonly used for?",
            "correct": "Running and testing Python statements interactively.",
            "wrong": [
                "Designing database schemas only.",
                "Replacing Python package managers.",
                "Rendering HTML templates by default.",
            ],
            "explanation": "REPL provides immediate feedback for quick experiments.",
        },
        {
            "core": True,
            "keywords": ["visual studio code", "vs code", "vscode"],
            "question": "Why is Visual Studio Code mentioned in this lesson?",
            "correct": "It is used as the editor and terminal environment for running Python code.",
            "wrong": [
                "It is required only to install hardware drivers.",
                "It replaces the Python interpreter entirely.",
                "It is only used for database backups.",
            ],
            "explanation": "The lesson demonstrates Python setup and execution using VS Code.",
        },
        {
            "core": True,
            "keywords": ["terminal", "new terminal"],
            "question": "Why do we open a terminal while learning Python basics?",
            "correct": "To run Python commands and execute scripts.",
            "wrong": [
                "To draw diagrams for variable memory maps.",
                "To store videos and thumbnails.",
                "To compile front-end assets automatically.",
            ],
            "explanation": "Terminal is used to run Python interactively or through files.",
        },
        {
            "core": True,
            "keywords": ["shortcut", "backtick"],
            "question": "What is the role of keyboard shortcuts in the lesson workflow?",
            "correct": "They provide a quick way to open the terminal.",
            "wrong": [
                "They are mandatory for defining variables.",
                "They change Python syntax rules.",
                "They automatically grade quiz answers.",
            ],
            "explanation": "The lesson mentions shortcut-based terminal access for speed.",
        },
        {
            "core": True,
            "keywords": ["python 3", "py", "python repl"],
            "question": "Why does the lesson mention both `py` and `python3` commands?",
            "correct": "Different operating systems may use different commands to start Python.",
            "wrong": [
                "`py` is only for creating comments in code.",
                "`python3` can run only Java programs.",
                "Both commands are unrelated to starting Python.",
            ],
            "explanation": "Command names vary by platform, but both are used to start Python.",
        },
        {
            "core": True,
            "keywords": ["menu", "three dots"],
            "question": "What is the menu-based method shown for opening a terminal?",
            "correct": "Use the top menu (or three-dot menu) and choose a new terminal.",
            "wrong": [
                "Open the quiz tab and click submit.",
                "Rename the project folder to terminal.",
                "Delete subtitle files and restart VS Code.",
            ],
            "explanation": "The lesson explains menu navigation to open a terminal window.",
        },
        {
            "core": True,
            "keywords": ["run python file", "run the python file", "play button"],
            "question": "What is one method shown for running a Python file?",
            "correct": "Use the run/play option in the editor after opening the file.",
            "wrong": [
                "Rename the file extension to `.txt` before execution.",
                "Delete all print statements and run again.",
                "Close the terminal and refresh the browser.",
            ],
            "explanation": "The lesson demonstrates running Python files from the editor workflow.",
        },
        {
            "core": True,
            "keywords": ["new series", "basics", "python programming language"],
            "question": "What is the primary learning focus introduced at the start?",
            "correct": "Learning Python fundamentals through practical examples.",
            "wrong": [
                "Building a production database cluster immediately.",
                "Designing mobile UI animations only.",
                "Deploying a cloud network without coding.",
            ],
            "explanation": "The lesson introduces foundational Python concepts first.",
        },
        {
            "core": True,
            "keywords": ["binary", "0s and 1s"],
            "question": "Why are 0s and 1s discussed in the lesson?",
            "correct": "To explain that computers operate on binary representation.",
            "wrong": [
                "To define a new Python string format.",
                "To replace variable naming conventions.",
                "To disable interpreted execution.",
            ],
            "explanation": "Binary is referenced to explain computer-level representation.",
        },
        {
            "core": True,
            "keywords": ["interpreted language"],
            "question": "How does the lesson describe Python execution style?",
            "correct": "Python is introduced as an interpreted language.",
            "wrong": [
                "Python is described as hardware microcode.",
                "Python is only a markup syntax.",
                "Python cannot execute from terminal commands.",
            ],
            "explanation": "The lesson explicitly identifies Python as interpreted.",
        },
        {
            "core": True,
            "keywords": ["underscore", "name", "variable name"],
            "question": "How are underscores used in Python variable names?",
            "correct": "Underscores are valid and commonly used to separate words.",
            "wrong": [
                "Underscores are allowed only inside comments.",
                "Underscores must appear at the start and end of every name.",
                "Underscores automatically convert names to constants.",
            ],
            "explanation": "Underscores are standard in readable variable naming.",
        },
        {
            "core": True,
            "keywords": ["print statements", "end argument", "end character"],
            "question": "What is highlighted about advanced print statement usage?",
            "correct": "Print behavior can be adjusted with arguments like separators or end characters.",
            "wrong": [
                "Print statements can only display integers.",
                "Print statements always require network access.",
                "Print statements are valid only inside comments.",
            ],
            "explanation": "The lesson mentions print customization behavior.",
        },
        {
            "core": True,
            "keywords": ["assigned", "holds the value", "value"],
            "question": "What happens when a value is assigned to a variable name?",
            "correct": "The variable stores and refers to that value.",
            "wrong": [
                "The variable becomes a Python keyword.",
                "The variable is deleted after one print.",
                "The value is ignored unless compiled manually.",
            ],
            "explanation": "Assignment links names with values for later use.",
        },
        {
            "core": True,
            "keywords": ["returns the value", "press enter"],
            "question": "What does evaluating a variable name in REPL typically show?",
            "correct": "It returns the current value bound to that name.",
            "wrong": [
                "It resets all previous variables.",
                "It exits Python immediately.",
                "It converts the value to a file path.",
            ],
            "explanation": "REPL evaluation shows the variable's current value.",
        },
    ]
    BAD_SUBJECT_FRAGMENTS = {
        "first one",
        "second one",
        "third one",
        "this one",
        "that one",
        "when we",
        "we mean",
        "the first one",
    }
    NOISE_OPTION_FRAGMENTS = {
        "garment owners include",
        "talking about a new land",
        "underscore value of the app",
        "common items",
    }
    ALLOWED_TERM_KEYWORDS = [
        "python",
        "variable",
        "variables",
        "data type",
        "string",
        "integer",
        "float",
        "boolean",
        "list",
        "tuple",
        "dictionary",
        "set",
        "print",
        "function",
        "assignment",
        "operator",
        "identifier",
        "underscore",
        "compiler",
        "interpreted",
    ]
    STOPWORDS = {
        "a", "an", "the", "is", "are", "in", "of", "to", "for", "and", "or",
        "this", "that", "these", "those", "what", "which", "does", "mean", "lesson",
        "python", "used", "use", "best", "describe", "describes",
    }

    @staticmethod
    def _meaningful_sentences(text):
        return ContentExtractor._meaningful_sentences(text)

    @staticmethod
    def _extract_definition_pairs(text):
        terms = ContentExtractor.extract_terms(text)
        return [
            {
                "term": term,
                "definition": definition,
            }
            for term, definition in terms.items()
        ]

    @staticmethod
    def _distractors_for_term(term, definition, terms, fallback_terms):
        distractors = []

        for other_term, other_definition in terms.items():
            if other_term == term:
                continue
            distractors.append(other_definition)

        distractors.extend(
            [
                f"A syntax rule unrelated to {term.lower()}",
                f"A runtime error caused by using {term.lower()} incorrectly",
                f"A formatting step used before running the program",
            ]
        )

        for fallback in fallback_terms:
            if fallback.lower() != term.lower():
                distractors.append(fallback)

        cleaned = []
        seen = set()
        for item in distractors:
            key = item.lower().strip()
            if not key or key == definition.lower().strip() or key in seen:
                continue
            seen.add(key)
            cleaned.append(item)
            if len(cleaned) == 3:
                break

        return cleaned

    @staticmethod
    def _build_definition_question(pair, all_terms):
        term = pair["term"]
        definition = pair["definition"]
        distractors = MCQGenerator._distractors_for_term(
            term,
            definition,
            all_terms,
            fallback_terms=[
                f"A programming idea different from {term.lower()}",
                f"An output detail unrelated to {term.lower()}",
                f"A syntax pattern not used to define {term.lower()}",
            ],
        )

        options = [definition] + distractors[:3]

        return {
            "type": "multiple_choice",
            "question": f"What does {term} mean in this lesson?",
            "options": options,
            "correct_answer": "A",
            "explanation": f"{term} is described as: {definition}",
        }

    @staticmethod
    def _is_valid_term_pair(pair):
        term = (pair.get("term") or "").strip().lower()
        definition = (pair.get("definition") or "").strip().lower()
        if not term or len(term) < 3:
            return False
        if re.search(r"\b(?:but|so|and|if|when|then|what|we|they|this|that|these|those)\b", term):
            return False
        if not any(keyword in term for keyword in MCQGenerator.ALLOWED_TERM_KEYWORDS):
            return False
        return True

    @staticmethod
    def _build_fact_question(sentence):
        statement = ContentExtractor._to_statement(sentence).rstrip(".")
        lowered = sentence.lower()
        subject = ""

        prompt = "In Python, which statement is correct?"
        if "used to" in lowered:
            subject = sentence.split(" is used to ")[0].strip()
            prompt = f"In Python, what is {subject} used for?"
        elif "means" in lowered:
            subject = sentence.split(" means ")[0].strip()
            prompt = f"In Python, what does {subject} mean?"
        elif "refers to" in lowered:
            subject = sentence.split(" refers to ")[0].strip()
            prompt = f"In Python, what does {subject} refer to?"
        elif " is " in lowered:
            subject = sentence.split(" is ")[0].strip()
            prompt = f"In Python, which statement best describes {subject}?"
        elif " are " in lowered:
            subject = sentence.split(" are ")[0].strip()
            prompt = f"In Python, which statement best describes {subject}?"

        if subject:
            clean_subject = ContentExtractor._cleanup_phrase(subject)
        else:
            fallback_subject = " ".join(statement.split()[:4]).strip()
            clean_subject = ContentExtractor._cleanup_phrase(fallback_subject) or "this concept"
        pronoun_subjects = {"we", "they", "it", "this", "that", "these", "those", "what"}
        if clean_subject.lower() in pronoun_subjects:
            return None

        wrong_options = [
            f"It is the opposite of how {clean_subject.lower()} is explained in Python.",
            f"It is an unrelated concept and not the definition of {clean_subject.lower()}.",
            f"It is a random statement not connected to {clean_subject.lower()} in this topic.",
        ]

        return {
            "type": "multiple_choice",
            "question": prompt,
            "options": [statement + "."] + wrong_options,
            "correct_answer": "A",
            "explanation": f"The lesson states that {statement.lower()}.",
        }

    @staticmethod
    def _clean_subject(subject):
        if not subject:
            return ""
        cleaned = ContentExtractor._cleanup_phrase(subject)
        cleaned = re.sub(r"\b(?:the|a|an|this|that|these|those)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")
        return cleaned

    @staticmethod
    def _is_question_quality_good(question_obj):
        question_text = (question_obj.get("question") or "").strip()
        options = [str(opt or "").strip() for opt in question_obj.get("options", [])]

        if len(question_text) < 18:
            return False
        if any(len(opt) < 12 for opt in options[:4]):
            return False

        lowered = question_text.lower()
        if any(fragment in lowered for fragment in MCQGenerator.BAD_SUBJECT_FRAGMENTS):
            return False
        if re.search(r"\bwhat does\s+(?:what|we|they|it|this|that|these|those)\b", lowered):
            return False
        if re.search(r"\bbest describes\s+(?:we|they|it|this|that|these|those|what)\b", lowered):
            return False
        if lowered.startswith("in python, which statement"):
            return False
        if re.search(r"\b(?:this|that|these|those)\s+(?:one|thing)\b", lowered):
            return False
        for option in options[:4]:
            normalized_option = option.lower()
            if any(fragment in normalized_option for fragment in MCQGenerator.NOISE_OPTION_FRAGMENTS):
                return False

        return True

    @staticmethod
    def _build_concept_bank_questions(text, lesson_title=None):
        lowered = (text or "").lower()
        questions = []
        title = (lesson_title or "").lower()
        intro_mode = "intro" in title
        variables_mode = "variable" in title

        intro_heavy_markers = [
            "visual studio code",
            "terminal",
            "shortcut",
            "menu-based method",
            "py` and `python3`",
            "python repl",
        ]
        variable_heavy_markers = [
            "variable in python",
            "assignment in python",
            "string in python",
            "integer in python",
            "python identifiers",
        ]

        for concept in MCQGenerator.CONCEPT_QUESTION_BANK:
            keyword_match = any(keyword in lowered for keyword in concept["keywords"])
            if not keyword_match:
                continue

            question_text = concept["question"].lower()
            if intro_mode and any(marker in question_text for marker in variable_heavy_markers):
                continue
            if variables_mode and any(marker in question_text for marker in intro_heavy_markers):
                continue

            question = {
                "type": "multiple_choice",
                "question": concept["question"],
                "options": [concept["correct"]] + list(concept["wrong"]),
                "correct_answer": "A",
                "explanation": concept["explanation"],
            }
            if MCQGenerator._is_question_quality_good(question):
                questions.append(question)

        return questions

    @staticmethod
    def _is_topic_sentence(sentence):
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in MCQGenerator.TOPIC_KEYWORDS):
            return True
        return any(
            marker in lowered
            for marker in [" is ", " are ", " means ", " refers to ", " used to ", " defined as "]
        )

    @staticmethod
    def _select_topic_sentences(text):
        topic_sentences = [
            sentence
            for sentence in MCQGenerator._meaningful_sentences(text)
            if MCQGenerator._is_topic_sentence(sentence)
        ]
        # Drop weak/conversational transcript fragments that lead to bad questions.
        filtered = []
        for sentence in topic_sentences:
            lowered = sentence.lower()
            if any(fragment in lowered for fragment in MCQGenerator.BAD_SUBJECT_FRAGMENTS):
                continue
            if re.search(r"\b(?:this|that|these|those)\s+(?:one|thing)\b", lowered):
                continue
            filtered.append(sentence)
        if filtered:
            return filtered
        if topic_sentences:
            return topic_sentences
        return MCQGenerator._meaningful_sentences(text)

    @staticmethod
    def _finalize_questions(raw_questions, num_questions):
        finalized = []
        seen_question_keys = set()
        seen_option_signatures = set()
        seen_question_token_sets = []
        seen_option_token_sets = []

        def _tokenize(text):
            cleaned = re.sub(r"[^a-z0-9 ]", " ", (text or "").lower())
            tokens = [tok for tok in cleaned.split() if tok and tok not in MCQGenerator.STOPWORDS]
            return set(tokens)

        def _jaccard(a, b):
            if not a or not b:
                return 0.0
            union = a | b
            if not union:
                return 0.0
            return len(a & b) / len(union)

        for question in raw_questions:
            question_text = (question.get("question") or "").strip()
            question_key = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", question_text.lower())).strip()
            if not question_key or question_key in seen_question_keys:
                continue

            options = list(question.get("options", []))
            if len(options) < 4:
                continue

            question_tokens = _tokenize(question_text)
            if any(_jaccard(question_tokens, existing_tokens) >= 0.6 for existing_tokens in seen_question_token_sets):
                continue

            correct_option = options[0]
            shuffled_options = options[:4]
            random.shuffle(shuffled_options)

            option_signature = tuple(
                sorted(
                    re.sub(r"\s+", " ", (opt or "").strip().lower())
                    for opt in shuffled_options[:4]
                )
            )
            if option_signature in seen_option_signatures:
                continue

            option_tokens = set()
            for opt in shuffled_options[:4]:
                option_tokens |= _tokenize(opt)
            if any(_jaccard(option_tokens, existing_tokens) >= 0.7 for existing_tokens in seen_option_token_sets):
                continue

            correct_index = shuffled_options.index(correct_option)
            correct_answer = ["A", "B", "C", "D"][correct_index]

            finalized.append(
                {
                    **question,
                    "options": shuffled_options[:4],
                    "correct_answer": correct_answer,
                }
            )
            seen_question_keys.add(question_key)
            seen_option_signatures.add(option_signature)
            seen_question_token_sets.append(question_tokens)
            seen_option_token_sets.append(option_tokens)

            if len(finalized) >= num_questions:
                break

        return finalized

    @staticmethod
    def _build_title_fallback_questions(lesson_title, num_questions):
        topic = (lesson_title or "this lesson").strip()
        topic_lower = topic.lower()
        templates = [
            {
                "type": "multiple_choice",
                "question": f"What is the main focus of the lesson '{topic}'?",
                "options": [
                    f"The lesson introduces and explains {topic_lower}.",
                    "The lesson is mainly about unrelated system configuration files.",
                    "The lesson focuses only on grading without teaching any concept.",
                    "The lesson avoids discussing the named topic entirely.",
                ],
                "correct_answer": "A",
                "explanation": f"The lesson title indicates that the primary focus is {topic}.",
            },
            {
                "type": "multiple_choice",
                "question": f"Why should a learner study '{topic}' carefully?",
                "options": [
                    f"It helps the learner understand the core ideas and practical use of {topic_lower}.",
                    "It is useful only for renaming files and folders.",
                    "It removes the need to practice or review concepts.",
                    "It is unrelated to building understanding of the topic.",
                ],
                "correct_answer": "A",
                "explanation": "A lesson exists to build understanding of its named topic.",
            },
            {
                "type": "multiple_choice",
                "question": f"Which outcome best matches a lesson titled '{topic}'?",
                "options": [
                    f"Learners should be able to explain the basics of {topic_lower}.",
                    "Learners should ignore the lesson title and study a different subject.",
                    "Learners should skip all examples and definitions.",
                    "Learners should memorize random facts unrelated to the lesson.",
                ],
                "correct_answer": "A",
                "explanation": "A well-titled lesson should help learners explain the topic it names.",
            },
            {
                "type": "multiple_choice",
                "question": f"What is a sensible first step when learning about '{topic}'?",
                "options": [
                    f"Start by understanding the main concepts and terms related to {topic_lower}.",
                    "Begin by avoiding all explanations and summaries.",
                    "Assume the lesson has no key ideas worth reviewing.",
                    "Skip directly to unrelated troubleshooting steps.",
                ],
                "correct_answer": "A",
                "explanation": "Foundational concepts and terms are the best starting point.",
            },
            {
                "type": "multiple_choice",
                "question": f"How should students use the lesson '{topic}' for revision?",
                "options": [
                    f"They should review the explanation, examples, and key takeaways for {topic_lower}.",
                    "They should study only the video length and ignore the content.",
                    "They should focus on unrelated subjects instead of the lesson topic.",
                    "They should avoid checking understanding after watching.",
                ],
                "correct_answer": "A",
                "explanation": "Revision should center on the lesson's explanations and takeaways.",
            },
            {
                "type": "multiple_choice",
                "question": f"What kind of quiz question fits a lesson on '{topic}'?",
                "options": [
                    f"A question that checks understanding of the main ideas in {topic_lower}.",
                    "A question that ignores the lesson and asks about a random hobby.",
                    "A question that depends only on guessing without context.",
                    "A question about deleting the course instead of learning it.",
                ],
                "correct_answer": "A",
                "explanation": "Quiz questions should assess understanding of the lesson topic.",
            },
            {
                "type": "multiple_choice",
                "question": f"What is the purpose of examples in a lesson like '{topic}'?",
                "options": [
                    f"They make the concepts in {topic_lower} easier to understand and apply.",
                    "They replace the need for any explanation of the topic.",
                    "They are included only to increase video length.",
                    "They prevent learners from practicing the main concept.",
                ],
                "correct_answer": "A",
                "explanation": "Examples help connect concepts to practical understanding.",
            },
            {
                "type": "multiple_choice",
                "question": f"Which statement is most likely true about the lesson '{topic}'?",
                "options": [
                    f"It is intended to teach, clarify, or reinforce knowledge about {topic_lower}.",
                    "It exists only to hide the main topic from students.",
                    "It is designed to remove all learning objectives.",
                    "It avoids presenting any useful information to the learner.",
                ],
                "correct_answer": "A",
                "explanation": "The lesson title signals the knowledge area being taught.",
            },
            {
                "type": "multiple_choice",
                "question": f"Why is it helpful to have subtitles for '{topic}'?",
                "options": [
                    f"They help learners follow the explanation and review important points in {topic_lower}.",
                    "They are useful only for changing playback speed.",
                    "They prevent any quiz from being generated.",
                    "They remove the need to understand the lesson content.",
                ],
                "correct_answer": "A",
                "explanation": "Subtitles improve accessibility and make revision easier.",
            },
            {
                "type": "multiple_choice",
                "question": f"What should a student remember after studying '{topic}'?",
                "options": [
                    f"The key concepts, important terms, and main uses of {topic_lower}.",
                    "Only the upload date of the video file.",
                    "Only the button labels shown in the player.",
                    "A list of unrelated topics not covered in the lesson.",
                ],
                "correct_answer": "A",
                "explanation": "Retention should focus on concepts, terms, and practical use.",
            },
            {
                "type": "multiple_choice",
                "question": f"How does a quiz help after watching '{topic}'?",
                "options": [
                    f"It checks whether the learner understood the main ideas of {topic_lower}.",
                    "It replaces the lesson with unrelated content.",
                    "It guarantees learning without any attention or practice.",
                    "It measures only internet speed instead of understanding.",
                ],
                "correct_answer": "A",
                "explanation": "Quizzes are meant to check understanding of the lesson content.",
            },
            {
                "type": "multiple_choice",
                "question": f"What is the best general goal of a lesson named '{topic}'?",
                "options": [
                    f"To build useful understanding and confidence around {topic_lower}.",
                    "To avoid all discussion of the named topic.",
                    "To replace learning with unrelated technical settings.",
                    "To stop the learner from revisiting the material later.",
                ],
                "correct_answer": "A",
                "explanation": "Lessons are designed to build understanding and confidence in the topic.",
            },
        ]

        return MCQGenerator._finalize_questions(templates, max(3, num_questions))

    @staticmethod
    def determine_question_count(text):
        normalized_text = ContentExtractor._normalize_text(text)
        if not normalized_text:
            return 3

        word_count = len(normalized_text.split())
        meaningful_sentences = len(MCQGenerator._meaningful_sentences(normalized_text))
        term_count = len(MCQGenerator._extract_definition_pairs(normalized_text))

        if word_count < 250:
            target = 3
        elif word_count < 450:
            target = 4
        elif word_count < 700:
            target = 5
        elif word_count < 1000:
            target = 6
        elif word_count < 1500:
            target = 8
        else:
            target = 10

        # Add a small bump when a lesson introduces many concrete terms.
        target += min(2, term_count // 6)

        if meaningful_sentences:
            target = min(target, max(3, meaningful_sentences))

        return max(3, min(10, target))

    @staticmethod
    def generate_mcq_from_text(text, num_questions=5, lesson_title=None):
        normalized_text = ContentExtractor._normalize_text(text)
        if not normalized_text or len(normalized_text) < 50:
            return []

        target_count = max(3, min(10, num_questions))
        questions = MCQGenerator._build_concept_bank_questions(
            normalized_text,
            lesson_title=lesson_title,
        )
        # Quality-first: if we already have enough solid concept questions, avoid noisy transcript fallback.
        if len(questions) >= target_count:
            return MCQGenerator._finalize_questions(questions, target_count)
        if len(questions) >= target_count:
            return MCQGenerator._finalize_questions(questions, len(questions))

        definition_pairs = MCQGenerator._extract_definition_pairs(normalized_text)
        all_terms = {pair["term"]: pair["definition"] for pair in definition_pairs}

        for pair in definition_pairs:
            if not MCQGenerator._is_valid_term_pair(pair):
                continue
            question = MCQGenerator._build_definition_question(pair, all_terms)
            if MCQGenerator._is_question_quality_good(question):
                questions.append(question)

        for sentence in MCQGenerator._select_topic_sentences(normalized_text):
            if len(questions) >= target_count * 2:
                break
            question = MCQGenerator._build_fact_question(sentence)
            if not question:
                continue
            if MCQGenerator._is_question_quality_good(question):
                questions.append(question)

        finalized_questions = MCQGenerator._finalize_questions(questions, target_count)
        if finalized_questions:
            return finalized_questions

        return MCQGenerator._build_title_fallback_questions(lesson_title, target_count)

    @staticmethod
    def create_mcq_quiz(video, quiz_obj, questions_data):
        if not questions_data:
            return

        quiz_obj.questions.all().delete()
        existing_other_question_texts = set(
            QuizQuestion.objects.exclude(quiz=quiz_obj).values_list("question_text", flat=True)
        )
        seen_current_quiz_texts = set()

        for idx, q_data in enumerate(questions_data):
            options = list(q_data.get("options", []))
            correct_answer = q_data.get("correct_answer", "A")
            question_text = (q_data.get("question", "Quiz question") or "").strip()

            if question_text in existing_other_question_texts:
                question_text = f"In {video.title}, {question_text}"

            if question_text in seen_current_quiz_texts:
                question_text = f"{question_text} ({idx + 1})"
            seen_current_quiz_texts.add(question_text)

            while len(options) < 4:
                options.append("Not available")

            QuizQuestion.objects.create(
                quiz=quiz_obj,
                question_type="multiple_choice",
                question_text=question_text,
                option_a=options[0],
                option_b=options[1],
                option_c=options[2],
                option_d=options[3],
                correct_answer=correct_answer,
                explanation=q_data.get("explanation", ""),
                points=5,
                order=idx,
            )


class VideoContentProcessor:
    """Main processor for video content extraction and subtitle generation."""

    TAMIL_CHARACTER_PATTERN = re.compile(r"[\u0B80-\u0BFF]")

    @staticmethod
    def _build_fallback_text(video):
        return (
            f"This video covers: {video.title}. "
            f"Key topics include an introduction to {video.title}, main concepts and principles, "
            "practical applications, and a summary with core takeaways."
        )

    @staticmethod
    def _looks_like_fallback_text(text):
        normalized = (text or "").strip().lower()
        return normalized.startswith("this video covers:")

    @staticmethod
    def _has_real_transcript_text(text):
        normalized = (text or "").strip()
        return bool(normalized) and not VideoContentProcessor._looks_like_fallback_text(normalized)

    @staticmethod
    def _is_english_transcript(text, detected_language=None):
        if detected_language and str(detected_language).lower() not in {"en", "eng", "english", "unknown", "und"}:
            return False

        normalized = (text or "").strip()
        if not VideoContentProcessor._has_real_transcript_text(normalized):
            return False

        if VideoContentProcessor.TAMIL_CHARACTER_PATTERN.search(normalized):
            return False

        alpha_chars = [char for char in normalized if char.isalpha()]
        if not alpha_chars:
            return False

        latin_alpha_count = sum(1 for char in alpha_chars if "a" <= char.lower() <= "z")
        return (latin_alpha_count / len(alpha_chars)) >= 0.7

    @staticmethod
    def _has_usable_subtitle_file(video):
        subtitle_file = getattr(video, "subtitle_file", None)
        if not subtitle_file or not getattr(subtitle_file, "name", ""):
            return False

        try:
            return (
                default_storage.exists(subtitle_file.name)
                and default_storage.size(subtitle_file.name) > 0
            )
        except Exception:
            return False

    @staticmethod
    def _has_synthetic_subtitle_timing(video):
        subtitle_file = getattr(video, "subtitle_file", None)
        if not subtitle_file or not getattr(subtitle_file, "name", ""):
            return False

        try:
            with subtitle_file.open("rb") as subtitle_file_obj:
                return subtitle_file_has_synthetic_timing(subtitle_file_obj)
        except Exception:
            return False

    @staticmethod
    def needs_processing(video, quiz=None):
        return False

    @staticmethod
    def ensure_processed(video, force=False):
        quiz = getattr(video, "quiz", None)
        if not force and not VideoContentProcessor.needs_processing(video, quiz=quiz):
            return {
                "video_id": video.id,
                "skipped": True,
                "reason": "already_processed",
            }

        return VideoContentProcessor.process_video(video, force_transcription=force)

    @staticmethod
    def process_video(video, subtitle_text=None, force_transcription=False):
        if video.subtitle_file and getattr(video.subtitle_file, "name", ""):
            try:
                default_storage.delete(video.subtitle_file.name)
            except Exception as storage_error:
                safe_log(f"Could not delete subtitle file for video {video.id}: {storage_error}")

        video.subtitle_file = None
        video.subtitle_text = ""
        video.save(update_fields=["subtitle_file", "subtitle_text"])

        quiz = getattr(video, "quiz", None)
        if quiz is not None:
            quiz.delete()

        return {
            "video_id": video.id,
            "subtitle_generated": False,
            "subtitle_file": None,
            "subtitle_text_length": 0,
            "transcript_source": "disabled",
            "quiz_questions": 0,
            "notes_sections": 0,
        }

        content_text = subtitle_text or (video.subtitle_text or "").strip()
        subtitle_generated = False
        transcript_source = "existing_text" if content_text else "none"
        detected_language = None
        srt_output = None
        subtitle_file_path = None
        had_fake_subtitle_file = False
        has_usable_subtitle_file = VideoContentProcessor._has_usable_subtitle_file(video)
        has_synthetic_timing = VideoContentProcessor._has_synthetic_subtitle_timing(video)
        should_attempt_transcription = (
            subtitle_text is None
            and AudioTranscriber.is_available()
            and (
                force_transcription
                or has_synthetic_timing
                or
                not has_usable_subtitle_file
                or not content_text
                or VideoContentProcessor._looks_like_fallback_text(content_text)
            )
        )

        safe_log(f"Processing video {video.id}")

        if should_attempt_transcription:
            safe_log("Attempting audio transcription")
            srt_output = AudioTranscriber.transcribe_video(video)

            if srt_output:
                detected_language = getattr(srt_output, "language", None)
                if hasattr(srt_output, "text"):
                    srt_output = srt_output.text

                content_text = SubtitleParser.parse_srt_file(srt_output)
                backend_name = AudioTranscriber.get_backend() or "audio_transcription"
                transcript_source = backend_name
                safe_log("Audio transcription completed")
            else:
                safe_log("Audio transcription did not produce subtitles")

        if not content_text and has_usable_subtitle_file and video.subtitle_file:
            try:
                with video.subtitle_file.open("rb") as subtitle_file_obj:
                    parsed_text = SubtitleParser.extract_text_from_subtitle_file(subtitle_file_obj)
                if parsed_text and VideoContentProcessor._has_real_transcript_text(parsed_text):
                    content_text = parsed_text
                    transcript_source = "existing_subtitle_file"
                elif parsed_text:
                    had_fake_subtitle_file = True
                    safe_log(f"Ignoring fallback subtitle file for video {video.id}")
            except Exception as e:
                safe_log(f"Subtitle file read error for video {video.id}: {e}")

        has_real_transcript = VideoContentProcessor._has_real_transcript_text(content_text)
        has_english_transcript = VideoContentProcessor._is_english_transcript(
            content_text,
            detected_language=detected_language,
        )

        try:
            if srt_output and has_english_transcript:
                vtt_content = convert_srt_to_vtt(srt_output)
                subtitle_generated = True
                subtitle_file_path = save_vtt_file(video, vtt_content)
                video.subtitle_file = subtitle_file_path
                safe_log(f"Subtitle file saved for video {video.id}")
            elif transcript_source == "existing_subtitle_file" and has_english_transcript and has_usable_subtitle_file and video.subtitle_file:
                subtitle_generated = True
                subtitle_file_path = video.subtitle_file.name
                safe_log(f"Keeping existing subtitle file for video {video.id}")
            elif has_english_transcript and has_usable_subtitle_file and not has_synthetic_timing and video.subtitle_file:
                subtitle_generated = True
                subtitle_file_path = video.subtitle_file.name
                safe_log(f"Keeping existing timed subtitle file for video {video.id}")
            else:
                if ((had_fake_subtitle_file or has_synthetic_timing or not has_english_transcript) and video.subtitle_file):
                    try:
                        default_storage.delete(video.subtitle_file.name)
                    except Exception as storage_error:
                        safe_log(f"Could not delete fallback subtitle file for video {video.id}: {storage_error}")
                video.subtitle_file = None
                subtitle_file_path = None
                safe_log(f"No English transcript available for video {video.id}; subtitles not generated")

            video.subtitle_text = content_text if has_english_transcript else ""
            video.save(update_fields=["subtitle_file", "subtitle_text"])
        except Exception as e:
            safe_log(f"Subtitle save error for video {video.id}: {e}")
            video.subtitle_text = content_text if has_english_transcript else ""
            video.save(update_fields=["subtitle_text"])

        if not has_english_transcript or not subtitle_file_path:
            quiz = getattr(video, "quiz", None)
            if quiz is not None:
                quiz.questions.all().delete()

            return {
                "video_id": video.id,
                "subtitle_generated": False,
                "subtitle_file": None,
                "subtitle_text_length": len(content_text) if has_english_transcript else 0,
                "transcript_source": transcript_source if transcript_source != "none" else "english_transcript_unavailable",
                "quiz_questions": 0,
                "notes_sections": 0,
            }

        notes = ContentExtractor.create_structured_notes(video, content_text)
        question_count = MCQGenerator.determine_question_count(content_text)
        questions = MCQGenerator.generate_mcq_from_text(
            content_text,
            num_questions=question_count,
            lesson_title=video.title,
        )

        quiz, _ = Quiz.objects.get_or_create(
            video=video,
            defaults={
                "title": f"Quiz: {video.title}",
                "description": f"Multiple Choice Quiz for {video.title}",
                "passing_score": 70,
                "time_limit": 15,
                "max_attempts": 0,
                "is_published": True,
            },
        )

        quiz_updates = {}
        if quiz.max_attempts != 0:
            quiz_updates["max_attempts"] = 0
        if not quiz.is_published:
            quiz_updates["is_published"] = True
        if quiz_updates:
            for field, value in quiz_updates.items():
                setattr(quiz, field, value)
            quiz.save(update_fields=list(quiz_updates.keys()))

        MCQGenerator.create_mcq_quiz(video, quiz, questions)

        notes_sections = notes.sections.count() if hasattr(notes, "sections") else 0

        return {
            "video_id": video.id,
            "subtitle_generated": subtitle_generated and bool(subtitle_file_path),
            "subtitle_file": subtitle_file_path,
            "subtitle_text_length": len(content_text),
            "transcript_source": transcript_source,
            "quiz_questions": len(questions),
            "notes_sections": notes_sections,
        }

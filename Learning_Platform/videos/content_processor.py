"""
Service for extracting content from videos and generating structured notes,
subtitle files, and MCQ questions.
"""

import random
import re

from notes.models import NoteSection, VideoNotes
from quiz.models import Quiz, QuizQuestion

from .subtitle_utils import (
    AudioTranscriber,
    SubtitleParser,
    build_vtt_from_plain_text,
    convert_srt_to_vtt,
    save_vtt_file,
    safe_log,
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
        if not any(keyword in term or keyword in definition for keyword in MCQGenerator.ALLOWED_TERM_KEYWORDS):
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
        if re.search(r"\b(?:this|that|these|those)\s+(?:one|thing)\b", lowered):
            return False
        for option in options[:4]:
            normalized_option = option.lower()
            if any(fragment in normalized_option for fragment in MCQGenerator.NOISE_OPTION_FRAGMENTS):
                return False

        return True

    @staticmethod
    def _build_concept_bank_questions(text):
        lowered = (text or "").lower()
        questions = []

        for concept in MCQGenerator.CONCEPT_QUESTION_BANK:
            if not any(keyword in lowered for keyword in concept["keywords"]):
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

        for question in raw_questions:
            question_text = (question.get("question") or "").strip()
            question_key = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", question_text.lower())).strip()
            if not question_key or question_key in seen_question_keys:
                continue

            options = list(question.get("options", []))
            if len(options) < 4:
                continue

            correct_option = options[0]
            distractors = options[1:4]
            random.shuffle(distractors)
            shuffled_options = [correct_option] + distractors

            option_signature = tuple(
                sorted(
                    re.sub(r"\s+", " ", (opt or "").strip().lower())
                    for opt in shuffled_options[:4]
                )
            )
            if option_signature in seen_option_signatures:
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

            if len(finalized) >= num_questions:
                break

        return finalized

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

        return max(3, min(12, target))

    @staticmethod
    def generate_mcq_from_text(text, num_questions=5):
        normalized_text = ContentExtractor._normalize_text(text)
        if not normalized_text or len(normalized_text) < 50:
            return []

        questions = MCQGenerator._build_concept_bank_questions(normalized_text)
        definition_pairs = MCQGenerator._extract_definition_pairs(normalized_text)
        all_terms = {pair["term"]: pair["definition"] for pair in definition_pairs}

        for pair in definition_pairs:
            if not MCQGenerator._is_valid_term_pair(pair):
                continue
            question = MCQGenerator._build_definition_question(pair, all_terms)
            if MCQGenerator._is_question_quality_good(question):
                questions.append(question)

        for sentence in MCQGenerator._select_topic_sentences(normalized_text):
            if len(questions) >= num_questions * 2:
                break
            question = MCQGenerator._build_fact_question(sentence)
            if not question:
                continue
            if MCQGenerator._is_question_quality_good(question):
                questions.append(question)

        return MCQGenerator._finalize_questions(questions, num_questions)

    @staticmethod
    def create_mcq_quiz(video, quiz_obj, questions_data):
        if not questions_data:
            return

        quiz_obj.questions.all().delete()

        for idx, q_data in enumerate(questions_data):
            options = list(q_data.get("options", []))
            correct_answer = q_data.get("correct_answer", "A")

            while len(options) < 4:
                options.append("Not available")

            QuizQuestion.objects.create(
                quiz=quiz_obj,
                question_type="multiple_choice",
                question_text=q_data.get("question", "Quiz question"),
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
    def process_video(video, subtitle_text=None):
        content_text = subtitle_text or (video.subtitle_text or "").strip()
        subtitle_generated = False
        transcript_source = "existing_text" if content_text else "none"
        srt_output = None
        subtitle_file_path = None
        should_attempt_transcription = (
            subtitle_text is None
            and AudioTranscriber.is_available()
            and (
                not video.subtitle_file
                or not content_text
                or VideoContentProcessor._looks_like_fallback_text(content_text)
            )
        )

        safe_log(f"Processing video {video.id}")

        if should_attempt_transcription:
            safe_log("Attempting audio transcription")
            srt_output = AudioTranscriber.transcribe_video(video)

            if srt_output:
                if hasattr(srt_output, "text"):
                    srt_output = srt_output.text

                content_text = SubtitleParser.parse_srt_file(srt_output)
                backend_name = AudioTranscriber.get_backend() or "audio_transcription"
                transcript_source = backend_name
                safe_log("Audio transcription completed")
            else:
                safe_log("Audio transcription did not produce subtitles")

        if not content_text and video.subtitle_file:
            try:
                with video.subtitle_file.open("rb") as subtitle_file_obj:
                    parsed_text = SubtitleParser.extract_text_from_subtitle_file(subtitle_file_obj)
                if parsed_text:
                    content_text = parsed_text
                    transcript_source = "existing_subtitle_file"
            except Exception as e:
                safe_log(f"Subtitle file read error for video {video.id}: {e}")

        if not content_text:
            content_text = VideoContentProcessor._build_fallback_text(video)
            transcript_source = "generated_summary"

        try:
            if srt_output:
                vtt_content = convert_srt_to_vtt(srt_output)
                subtitle_generated = True
                subtitle_file_path = save_vtt_file(video, vtt_content)
                video.subtitle_file = subtitle_file_path
                safe_log(f"Subtitle file saved for video {video.id}")
            elif transcript_source == "existing_subtitle_file" and video.subtitle_file:
                subtitle_generated = True
                subtitle_file_path = video.subtitle_file.name
                safe_log(f"Keeping existing subtitle file for video {video.id}")
            else:
                fallback_vtt = build_vtt_from_plain_text(content_text)
                subtitle_file_path = save_vtt_file(video, fallback_vtt)
                video.subtitle_file = subtitle_file_path
                subtitle_generated = True
                safe_log(
                    f"No timed transcript available for video {video.id}; generated fallback subtitle file"
                )

            video.subtitle_text = content_text
            video.save(update_fields=["subtitle_file", "subtitle_text"])
        except Exception as e:
            safe_log(f"Subtitle save error for video {video.id}: {e}")
            video.subtitle_text = content_text
            video.save(update_fields=["subtitle_text"])

        notes = ContentExtractor.create_structured_notes(video, content_text)
        question_count = MCQGenerator.determine_question_count(content_text)
        questions = MCQGenerator.generate_mcq_from_text(
            content_text,
            num_questions=question_count,
        )

        quiz, _ = Quiz.objects.get_or_create(
            video=video,
            defaults={
                "title": f"Quiz: {video.title}",
                "description": f"Multiple Choice Quiz for {video.title}",
                "passing_score": 70,
                "time_limit": 15,
                "max_attempts": 2,
                "is_published": True,
            },
        )

        quiz_updates = {}
        if quiz.max_attempts != 2:
            quiz_updates["max_attempts"] = 2
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

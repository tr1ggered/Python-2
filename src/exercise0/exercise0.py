import multiprocessing
import random
import time
import prettytable
import os

import sys
import locale

sys.stdout.reconfigure(encoding="utf-8")
locale.setlocale(locale.LC_ALL, 'C.UTF-8')

class Student:
    def __init__(self, name, pol):
        self.name = name
        self.pol = pol
        self.status = "In Queue"
        self.finish_time = None
        return

class Examiner:
    def __init__(self, name, pol):
        self.name = name
        self.pol = pol
        self.current_student = None
        self.total_students = 0
        self.failed = 0
        self.work_time = 0.0
        return

class Question:
    def __init__(self, text):
        self.words = text.split()
        self.correct_count = 0
        return

def load_students(path):
    students = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            name, pol = line.split()
            students.append(Student(name, pol))
    return students

def load_examiners(path):
    examiners = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            name, pol = line.split()
            examiners.append(Examiner(name, pol))
    return examiners

def load_questions(path):
    questions = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            questions.append(Question(line))
    return questions

import random

GOLDEN_RATIO = (1 + 5 ** 0.5) / 2

def get_word_probabilities(n):
    probs = []
    remaining = 1.0
    for i in range(n - 1):
        p = remaining / GOLDEN_RATIO
        probs.append(p)
        remaining -= p
    probs.append(remaining)
    return probs

def choose_word(question_words, gender):
    n = len(question_words)
    probs = get_word_probabilities(n)

    if gender == "F":
        words = list(reversed(question_words))
    else:
        words = question_words

    chosen = random.choices(words, weights=probs, k=1)[0]
    return chosen

def examiner_correct_answers(question_words, examiner_gender):
    remaining_words = question_words.copy()
    correct = set()

    while remaining_words:
        word = choose_word(remaining_words, examiner_gender)
        correct.add(word)
        remaining_words.remove(word)

        if not remaining_words:
            break

        if random.random() >= 1/3:
            break

    return correct

def determine_mood():
    r = random.random()
    if r < 1/8:
        return "bad"
    elif r < 1/8 + 1/4:
        return "good"
    else:
        return "neutral"

def get_exam_duration(examiner_name):
    n = len(examiner_name)
    return random.uniform(n - 1, n + 1)

def conduct_exam(student, examiner, questions, duration):
    chosen_questions = random.sample(questions, 3)
    results = []
    for question in chosen_questions:
        student_word = choose_word(question.words, student.pol)
        correct_words = examiner_correct_answers(question.words, examiner.pol)
        is_correct = student_word in correct_words
        results.append(is_correct)
        if is_correct:
            question.correct_count += 1

    mood = determine_mood()
    if mood == "bad":
        passed = False
    elif mood == "good":
        passed = True
    else:
        correct_count = sum(results)
        passed = correct_count > (len(results) - correct_count)

    time.sleep(duration)
    return passed

def examiner_process(examiner_index, shared_examiners, shared_students, student_queue, questions, start_time):
    time_since_break = 0.0

    while True:
        try:
            student_idx = student_queue.get_nowait()
        except:
            break

        student = shared_students[student_idx]
        examiner = shared_examiners[examiner_index]

        examiner.current_student = student.name
        shared_examiners[examiner_index] = examiner

        duration = get_exam_duration(examiner.name)
        passed = conduct_exam(student, examiner, questions, duration)

        student.status = "Passed" if passed else "Failed"
        student.finish_time = time.time() - start_time
        shared_students[student_idx] = student

        examiner = shared_examiners[examiner_index]
        examiner.total_students += 1
        if not passed:
            examiner.failed += 1
        examiner.work_time += duration
        examiner.current_student = None
        time_since_break += duration

        if time_since_break >= 30:
            break_duration = random.uniform(12, 18)
            time.sleep(break_duration)
            time_since_break = 0.0

        shared_examiners[examiner_index] = examiner

def render_tables(shared_students, shared_examiners, student_queue, start_time):
    os.system('cls' if os.name == 'nt' else 'clear')

    students = list(shared_students)
    in_queue = [s for s in students if s.status == "In Queue"]
    passed = [s for s in students if s.status == "Passed"]
    failed = [s for s in students if s.status == "Failed"]

    student_table = prettytable.PrettyTable()
    student_table.field_names = ["Student", "Status"]
    for s in in_queue + passed + failed:
        student_table.add_row([s.name, s.status])
    print(student_table)

    examiner_table = prettytable.PrettyTable()
    examiner_table.field_names = ["Examiner", "Current student", "Total students", "Failed", "Work time"]
    for e in shared_examiners:
        current = e.current_student if e.current_student else "-"
        examiner_table.add_row([e.name, current, e.total_students, e.failed, f"{e.work_time:.2f}"])
    print(examiner_table)

    print(f"Remaining in queue: {len(in_queue)} out of {len(students)}")
    print(f"Time since exam started: {time.time() - start_time:.2f}")

def main():
    students = load_students("students.txt")
    examiners = load_examiners("examiners.txt")
    questions = load_questions("questions.txt")

    manager = multiprocessing.Manager()
    shared_students = manager.list(students)
    shared_examiners = manager.list(examiners)
    student_queue = manager.Queue()
    for i in range(len(students)):
        student_queue.put(i)

    start_time = time.time()

    processes = []
    for idx in range(len(examiners)):
        p = multiprocessing.Process(
            target=examiner_process,
            args=(idx, shared_examiners, shared_students, student_queue, questions, start_time)
        )
        p.start()
        processes.append(p)

    def render_final_report(shared_students, shared_examiners, questions, start_time):
        students = list(shared_students)
        examiners = list(shared_examiners)

        passed = [s for s in students if s.status == "Passed"]
        failed = [s for s in students if s.status == "Failed"]

        print()
        student_table = prettytable.PrettyTable()
        student_table.field_names = ["Student", "Status"]
        for s in passed + failed:
            student_table.add_row([s.name, s.status])
        print(student_table)

        examiner_table = prettytable.PrettyTable()
        examiner_table.field_names = ["Examiner", "Total students", "Failed", "Work time"]
        for e in examiners:
            examiner_table.add_row([e.name, e.total_students, e.failed, f"{e.work_time:.2f}"])
        print(examiner_table)

        total_time = time.time() - start_time
        print(f"Time from exam start to finish: {total_time:.2f}")

        if passed:
            fastest_time = min(s.finish_time for s in passed)
            top_students = [s.name for s in passed if s.finish_time == fastest_time]
            print(f"Top-performing students: {', '.join(top_students)}")
        else:
            print("Top-performing students: none")

        if examiners:
            min_fail_rate = min(e.failed / e.total_students if e.total_students else 0 for e in examiners)
            top_examiners = [e.name for e in examiners if
                             e.total_students and e.failed / e.total_students == min_fail_rate]
            print(f"Top examiners: {', '.join(top_examiners)}")

        if failed:
            earliest_fail_time = min(s.finish_time for s in failed)
            expelled = [s.name for s in failed if s.finish_time == earliest_fail_time]
            print(f"Students to be expelled: {', '.join(expelled)}")
        else:
            print("Students to be expelled: none")

        max_correct = max((q.correct_count for q in questions), default=0)
        best_questions = [' '.join(q.words) for q in questions if q.correct_count == max_correct]
        print(f"Best questions: {', '.join(best_questions)}")

        pass_rate = len(passed) / len(students) if students else 0
        result = "Exam passed" if pass_rate > 0.85 else "Exam failed"
        print(f"Result: {result}")

    while any(p.is_alive() for p in processes):
        render_tables(shared_students, shared_examiners, student_queue, start_time)
        time.sleep(0.5)

    for p in processes:
        p.join()

    render_final_report(shared_students, shared_examiners, questions, start_time)


if __name__ == "__main__":
    main()
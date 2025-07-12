import glob
import csv

questions = set()

# Loop through all CSV files
for fname in glob.glob('LeetCode-Questions-CompanyWise-master/*.csv'):
    with open(fname, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Support different possible column name variations
            title = row.get("title") or row.get("Title") or row.get("Question") or row.get("question")
            if title:
                questions.add(title.strip())

# Convert to sorted list
unique_questions = sorted(questions)

# Output summary
print(f"✅ Total unique questions: {len(unique_questions)}\n")

# Save to file
with open("unique_questions.txt", "w", encoding="utf-8") as f:
    for i, q in enumerate(unique_questions, 1):
        f.write(f"{i}. {q}\n")

print("📄 All question names saved to 'unique_questions.txt'")

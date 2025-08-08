# Sample tasks for demonstration purposes

# Define two task dictionaries
task1 = {
    "title": "Complete Project Report",
    "description": "Write and submit the final project report to the manager.",
    "due_date": "2025-05-20",
    "status": "Pending"
}

task2 = {
    "title": "Team Meeting",
    "description": "Attend the weekly team meeting to discuss project updates.",
    "due_date": "2025-05-15",
    "status": "Completed"
}

# Add the tasks to a list
tasks = [task1, task2]

# Print the tasks for verification
if __name__ == "__main__":
    for task in tasks:
        print(task)
